import binascii
import bluetooth
import logging as log
import sys
import time
from multiprocessing import Process
from pydbus import SystemBus
from enum import Enum

from utils.menu_functions import (main_menu, read_duckyscript, 
                                  run, restart_bluetooth_daemon, get_target_address)
from utils.register_device import register_hid_profile, agent_loop

child_processes = []

class ConnectionFailureException(Exception):
    pass

class Adapter:
    def __init__(self, iface):
        self.iface = iface
        self.bus = SystemBus()
        self.adapter = self._get_adapter(iface)

    def _get_adapter(self, iface):
        try:
            return self.bus.get("org.bluez", f"/org/bluez/{iface}")
        except KeyError:
            log.error(f"Unable to find adapter '{iface}', aborting.")
            raise ConnectionFailureException("Adapter not found")

    def _run_command(self, command):
        result = run(command)
        if result.returncode != 0:
            raise ConnectionFailureException(f"Failed to execute command: {' '.join(command)}. Error: {result.stderr}")

    def set_property(self, prop, value):
        # Convert value to string if it's not
        value_str = str(value) if not isinstance(value, str) else value
        command = ["sudo", "hciconfig", self.iface, prop, value_str]
        self._run_command(command)

        # Verify if the property is set correctly
        verify_command = ["hciconfig", self.iface, prop]
        verification_result = run(verify_command)
        if value_str not in verification_result.stdout:
            log.error(f"Unable to set adapter {prop}, aborting. Output: {verification_result.stdout}")
            raise ConnectionFailureException(f"Failed to set {prop}")

    def power(self, powered):
        self.adapter.Powered = powered

    def reset(self):
        self.power(False)
        self.power(True)

    def enable_ssp(self):
        try:
            # Command to enable SSP - the actual command might differ
            # This is a placeholder command and should be replaced with the actual one.
            ssp_command = ["sudo", "hciconfig", self.iface, "sspmode", "1"]
            ssp_result = run(ssp_command)
            if ssp_result.returncode != 0:
                log.error(f"Failed to enable SSP: {ssp_result.stderr}")
                raise ConnectionFailureException("Failed to enable SSP")
        except Exception as e:
            log.error(f"Error enabling SSP: {e}")
            raise

class PairingAgent:
    def __init__(self, iface, target_addr):
        self.iface = iface
        self.target_addr = target_addr
        dev_name = "dev_%s" % target_addr.upper().replace(":", "_")
        self.target_path = "/org/bluez/%s/%s" % (iface, dev_name)

    def __enter__(self):
        try:
            log.debug("Starting agent process...")
            self.agent = Process(target=agent_loop, args=(self.target_path,))
            self.agent.start()
            time.sleep(0.25)
            log.debug("Agent process started.")
            return self
        except Exception as e:
            log.error(f"Error starting agent process: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            log.debug("Terminating agent process...")
            self.agent.kill()
            time.sleep(0.25)
            log.debug("Agent process terminated.")
        except Exception as e:
            log.error(f"Error terminating agent process: {e}")
            raise

class L2CAPClient:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.connected = False
        self.sock = None

    def encode_combo_input(*args):
        if not args:
            return bytes([0xA1, 0x01] + [0] * 8)  # Empty report for key release

        # Filter out non-Key_Codes arguments and process
        valid_args = [a for a in args if isinstance(a, Key_Codes)]

        # Properly sum the values of modifiers
        modifiers = sum(a.value for a in valid_args if a in Key_Codes.MODIFIERS)

        keycodes = [a.value for a in valid_args if a not in Key_Codes.MODIFIERS]
        keycodes += [0] * (6 - len(keycodes))
        return bytes([0xA1, 0x01, modifiers, 0x00] + keycodes)

    def encode_keyboard_input(*args):
      keycodes = []
      flags = 0
      for a in args:
        if isinstance(a, Key_Codes):
          keycodes.append(a.value)
        elif isinstance(a, Modifier_Codes):
          flags |= a.value
      assert(len(keycodes) <= 7)
      keycodes += [0] * (7 - len(keycodes))
      report = bytes([0xa1, 0x01, flags, 0x00] + keycodes)
      return report

    def close(self):
        if self.connected:
            self.sock.close()
        self.connected = False
        self.sock = None

    def send(self, data):
        if not self.connected:
            log.error("[TX] Not connected")
            return

        log.debug(f"[TX-{self.port}] Attempting to send data: {binascii.hexlify(data).decode()}")
        if self.attempt_send(data, 0.1):
            log.debug(f"[TX-{self.port}] Data sent successfully")
        else:
            log.error(f"[TX-{self.port}] ERROR! Timed out sending data")

    def attempt_send(self, data, timeout):
        start = time.time()
        while time.time() - start < timeout:
            try:
                self.sock.send(data)
                return True
            except bluetooth.btcommon.BluetoothError as ex:
                if ex.errno != 11:  # no data available
                    raise ex
                time.sleep(0.001)
            except Exception as ex:
                log.error(f"[TX-{self.port}] Exception: {ex}")
                self.connected = False
        return False

    def recv(self, timeout=0):
        start = time.time()
        while True:
            raw = None
            if not self.connected:
                return None
            if self.sock is None:
                return None
            try:
                raw = self.sock.recv(64)
                if len(raw) == 0:
                    self.connected = False
                    return None
                log.debug(f"[RX-{self.port}] Received data: {binascii.hexlify(raw).decode()}")
            except bluetooth.btcommon.BluetoothError as ex:
                if ex.errno != 11:  # no data available
                    raise ex
                else:
                    if (time.time() - start) < timeout:
                        continue
            return raw

    def connect(self, timeout=None):
        log.debug(f"Attempting to connect to {self.addr} on port {self.port}")
        log.debug("connecting to %s on port %d" % (self.addr, self.port))
        sock = bluetooth.BluetoothSocket(bluetooth.L2CAP)
        sock.settimeout(timeout)
        try:
            sock.connect((self.addr, self.port))
            sock.setblocking(0)
            self.sock = sock
            self.connected = True
            log.debug("SUCCESS! connected on port %d" % self.port)
        except Exception as ex:
            self.connected = False
            log.error("ERROR connecting on port %d: %s" % (self.port, ex))
            raise ConnectionFailureException(f"Connection failure on port {self.port}")

        return self.connected

    def send_keyboard_report(self, *args):
        self.send(self.encode_keyboard_input(*args))

    def send_keypress(self, *args, delay=0.05):
        if args:
            log.debug(f"Attempting to send... {args}")
            self.send(self.encode_keyboard_input(*args))
        else:
            # If no arguments, send an empty report to release keys
            self.send(self.encode_keyboard_input())
        time.sleep(delay)

    def send_combination(self, *keys, delay=0.05):
        """
        Send a combination of keys, which can include modifiers and regular keys.
        """
        modifiers = 0
        regular_keys = []

        for key in keys:
            if key in Key_Codes.MODIFIERS:
                modifiers |= key.value
            else:
                regular_keys.append(key.value)

        # Ensure that no more than 6 regular keys are sent
        regular_keys = regular_keys[:6] + [0] * (6 - len(regular_keys))

        # Create the HID report and send it
        report = bytes([0xa1, 0x01, modifiers, 0x00] + regular_keys)
        self.send(report)
        time.sleep(delay)

        # Send an empty report to release the keys
        self.send(self.encode_combo_input())

class L2CAPConnectionManager:
    def __init__(self, target_address):
        self.target_address = target_address
        self.clients = {}

    def create_connection(self, port):
        client = L2CAPClient(self.target_address, port)
        self.clients[port] = client
        return client

    def connect_all(self):
        try:
            return sum(client.connect() for client in self.clients.values())
        except ConnectionFailureException as e:
            log.error(f"Connection failure: {e}")
            raise

    def close_all(self):
        for client in self.clients.values():
            client.close()

def terminate_child_processes():
    for proc in child_processes:
        if proc.is_alive():
            proc.terminate()
            proc.join()

def setup_bluetooth(target_address):
    restart_bluetooth_daemon()
    profile_proc = Process(target=register_hid_profile, args=('hci0', target_address))
    profile_proc.start()
    child_processes.append(profile_proc)
    adapter = Adapter('hci0')
    adapter.set_property("name", "Robot POC")
    adapter.set_property("class", 0x002540)
    adapter.power(True)
    return adapter

# Key codes for modifier keys
class Modifier_Codes(Enum):
    LEFTCONTROL = 0xe0
    LEFTSHIFT = 0xe1
    LEFTALT = 0xe2
    LEFTGUI = 0xe3
    RIGHTCONTROL = 0xe4
    RIGHTSHIFT = 0xe5
    RIGHTALT = 0xe6
    RIGHTGUI = 0xe7

    # Convenience mappings for common names
    CTRL = LEFTCONTROL
    ALT = LEFTALT
    SHIFT = LEFTSHIFT
    GUI = LEFTGUI

# Modifier Key Set for easy checking
MODIFIER_KEYS_SET = {Modifier_Codes.LEFTCONTROL, Modifier_Codes.LEFTSHIFT, Modifier_Codes.LEFTALT, Modifier_Codes.LEFTGUI,
                     Modifier_Codes.RIGHTCONTROL, Modifier_Codes.RIGHTSHIFT, Modifier_Codes.RIGHTALT, Modifier_Codes.RIGHTGUI}

class Key_Codes(Enum):
    NONE = 0x00
    A = 0x04
    B = 0x05
    C = 0x06
    D = 0x07
    E = 0x08
    F = 0x09
    G = 0x0a
    H = 0x0b
    I = 0x0c
    J = 0x0d
    K = 0x0e
    L = 0x0f
    M = 0x10
    N = 0x11
    O = 0x12
    P = 0x13
    Q = 0x14
    R = 0x15
    S = 0x16
    T = 0x17
    U = 0x18
    V = 0x19
    W = 0x1a
    X = 0x1b
    Y = 0x1c
    Z = 0x1d
    _1 = 0x1e
    _2 = 0x1f
    _3 = 0x20
    _4 = 0x21
    _5 = 0x22
    _6 = 0x23
    _7 = 0x24
    _8 = 0x25
    _9 = 0x26
    _0 = 0x27
    ENTER = 0x28
    ESCAPE = 0x29
    BACKSPACE = 0x2a
    TAB = 0x2b
    SPACE = 0x2c
    MINUS = 0x2d
    EQUAL = 0x2e
    LEFTBRACE = 0x2f
    RIGHTBRACE = 0x30
    BACKSLASH = 0x31
    SEMICOLON = 0x33
    QUOTE = 0x34
    BACKTICK = 0x35
    COMMA = 0x36
    DOT = 0x37
    SLASH = 0x38
    CAPSLOCK = 0x39

def process_duckyscript(client, duckyscript):
    client.send_keypress('')  # Send empty report
    time.sleep(0.5)

    for line in duckyscript:
        line = line.strip()
        if not line or line.startswith("REM"):
            continue  # Skip empty lines and comments

        if line.startswith("STRING"):
            text = line[7:]
            for letter in text:
                try:
                    # Use upper() to match the uppercase keys defined in Key_Codes
                    key_code = getattr(Key_Codes, letter.upper()) if letter != " " else Key_Codes.SPACE
                    client.send_keypress(key_code)
                    client.send_keypress()
                    time.sleep(0.05)  # Add a small delay between keypresses
                except AttributeError:
                    log.warning(f"Unsupported character '{letter}' in Duckyscript")

        elif line.startswith("GUI"):
            # Handle combination keys
            components = line.split()
            try:
                # Use Modifier_Codes for modifier keys
                modifier = getattr(Modifier_Codes, components[0].upper())
                for key in components[1:]:
                    # Use Key_Codes for regular keys
                    key_code = getattr(Key_Codes, key.upper(), None)
                    if key_code:
                        client.send_combination(modifier, key_code)
                        client.send_combination()  # Release keys
            except AttributeError:
                log.warning(f"Unsupported key or modifier in line: {line}")

def initialize_pairing(agent_iface, target_address):
    try:
        with PairingAgent(agent_iface, target_address) as agent:
            log.debug("Pairing agent initialized")
    except Exception as e:
        log.error(f"Failed to initialize pairing agent: {e}")
        raise ConnectionFailureException("Pairing agent initialization failed")

def establish_connections(connection_manager):
    if not connection_manager.connect_all():
        raise ConnectionFailureException("Failed to connect to all required ports")

# Main function
def main():
    log.basicConfig(level=log.DEBUG)
    main_menu()
    target_address = get_target_address()
    if not target_address:
        log.info("No target address provided. Exiting.")
        return

    duckyscript = read_duckyscript()
    if not duckyscript:
        log.info("Payload file not found. Exiting.")
        return

    adapter = setup_bluetooth(target_address)
    adapter.enable_ssp()

    try:
        connection_manager = L2CAPConnectionManager(target_address)
        connection_manager.create_connection(1)   # SDP
        connection_manager.create_connection(17)  # HID Control
        connection_manager.create_connection(19)  # HID Interrupt

        initialize_pairing('hci0', target_address)
        establish_connections(connection_manager)
        hid_interrupt_client = connection_manager.clients[19]
        process_duckyscript(hid_interrupt_client, duckyscript)
    except ConnectionFailureException as e:
        log.error(f"Connection failure: {e}")
        terminate_child_processes()
        sys.exit("Exiting script due to connection failure")

if __name__ == "__main__":
    try:
        main()
    finally:
        terminate_child_processes()
