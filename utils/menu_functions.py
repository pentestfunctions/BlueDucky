import os, bluetooth, re, subprocess, time, curses, shutil
import logging as log

##########################
# UI Redesign by Lamento #
##########################

def get_target_address():
    blue = "\033[94m"
    reset = "\033[0m"
    print(f"\n What is the target address{blue}? {reset}Leave blank and we will scan for you{blue}!{reset}")
    target_address = input(f"\n {blue}> ")

    if target_address == "":
        devices = scan_for_devices()
        if devices:
            # Check if the returned list is from known devices or scanned devices
            if len(devices) == 1 and isinstance(devices[0], tuple) and len(devices[0]) == 2:
                # A single known device was chosen, no need to ask for selection
                # I think it would be better to ask, as sometimes I do not want to chose this device and actually need solely to scan for actual devices.
                confirm = input(f"\n Would you like to register this device{blue}:\n{reset}{devices[0][1]} {devices[0][0]}{blue}? {blue}({reset}y{blue}/{reset}n{blue}) {blue}").strip().lower()
                if confirm in ('y', 'yes'):
                    return devices[0][0]
                else:
                    return
            else:
                # Show list of scanned devices for user selection
                for idx, (addr, name) in enumerate(devices):
                    print(f"{reset}[{blue}{idx + 1}{reset}] {blue}Device Name{reset}: {blue}{name}, {blue}Address{reset}: {blue}{addr}")
                raw_selection = input(f"\n{reset}Select a device by number{blue}: {blue}").strip()
                if not raw_selection.isdigit():
                    print("\nInvalid selection. Exiting.")
                    return
                selection = int(raw_selection) - 1
                if 0 <= selection < len(devices):
                    target_address = devices[selection][0]
                else:
                    print("\nInvalid selection. Exiting.")
                    return
        else:
            return
    elif not is_valid_mac_address(target_address):
        print("\nInvalid MAC address format. Please enter a valid MAC address.")
        return

    return target_address

def restart_bluetooth_daemon():
    run(["sudo", "service", "bluetooth", "restart"])
    time.sleep(0.5)

def run(command):
    assert(isinstance(command, list))
    log.info("executing '%s'" % " ".join(command))
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result

def print_fancy_ascii_art():

    ascii_art = """
	⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠤⠄⠒⠒⠒⠒⠒⠒⠂⠠⢄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠴⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠓⢄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠞⠁⠀⠀⠀⠀⣀⡤⠴⠒⠒⠒⠒⠦⠤⣀⠀⠀⠀⠙⢆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⠀⢰⠋⠀⠀⠀⣠⠖⠋⢀⣄⣀⡀⠀⠀⠀⠀⠀⠀⠉⠲⣄⠀⠈⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⢠⠇⠀⠀⢀⡼⠁⠀⣴⣿⡛⠻⣿⣧⡀⠀⠀⠀⠀⠀⠀⠈⠳⡄⡿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⣼⣀⣀⣀⡜⠀⠀⠀⣿⣿⣿⣿⣿⣿⡧⠀⠀⠀⠀⠀⠀⠀⠀⠙⣿⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⣀⡤⠟⠁⠀⠈⠙⡶⣄⡀⠈⠻⢿⣿⡿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠇⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
	⣤⣤⠖⠖⠛⠉⠈⣀⣀⠀⠴⠊⠀⠀⣹⣷⣶⡏⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ ⠀⣀⡀⠀⠀
	⠘⠿⣿⣷⣶⣶⣶⣶⣤⣶⣶⣶⣿⣿⣿⡿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡜⠀⠀⠀⠀⠀⠀⢀⣀⣠⣤⠤⠖⠒⠋⠉⠁⠙⣆⠀
	⠀⠀⠀⠀⠉⠉⠉⠉⠙⠿⣍⣩⠟⠋⠙⢦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣾⣖⣶⣶⢾⠯⠽⠛⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⡄
	⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⠚⠁⠀⠀⠀⠀⠈⠓⠤⠀⠀⠀⠀⠀⠀⠐⠒⠚⠉⠉⠁⠀⠀⠀⠀⠀⠀⢀⣀⣀⠀⣀⢀⠀⠀⠀⠀⠀⠀⠀⣇
	⠀⠀⠀⠀⠀⠀⠀⡴⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⠤⠤⠖⠒⠚⠉⠉⠁⠀⠀⠀⢸⢸⣦⠀⠀⠀⠀⠀⠀⢸
	⠀⠀⠀⠀⠀⢠⠎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⡠⠤⠴⠒⠒⠉⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡏⣸⡏⠇⠀⠀⠀⠀⠀⢸
	⠀⠀⠀⠀⢠⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠞⢠⡿⠀⠀⠀⠀⠀⠀⠀⢸
	⠀⠀⠀⠀⣾⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡠⠊⣠⡟⠀⠀⠀⠀⠀⠀⠀⠀⡏
	⠀⠀⠀⠀⡏⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠢⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡠⠖⠉⢀⣴⠏⠠⠀⠀⠀⠀⠀⠀⠀⣸⠁
	⠀⠀⠀⠀⢹⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠒⠒⠢⠤⠄⠀⠀⠀⠀⠀⠈⠁⠀⣠⣶⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⢠⠃⠀
	⠀⠀⠀⠀⠀⢣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣴⠿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠃⠀⠀
	⠀⠀⠀⠀⠀⠈⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⡶⠿⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠃⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⠳⣄⢀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠤⠖⣪⡵⠋⠀⠀⠀⠀⠀
	⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⠫⠭⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣭⣭⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⡴⠶⠛⠉⠀⠀⠀⠀⠀⠀⠀
"""

    print("\033[94m" + ascii_art + "\033[0m")  # Blue color

def clear_screen():
    os.system('clear')

# Function to save discovered devices to a file
def save_devices_to_file(devices, filename='known_devices.txt'):
    with open(filename, 'w') as file:
        for addr, name in devices:
            file.write(f"{addr},{name}\n")

# Function to scan for devices
def scan_for_devices():
    main_menu()

    blue = "\033[94m"
    error = "\033[91m"
    reset = "\033[0m"

    # Load known devices
    known_devices = load_known_devices()
    if known_devices:
        blue = "\033[94m"
        error = "\033[91m"
        reset = "\033[0m"
        print(f"\n{reset}Known devices{blue}:")
        for idx, (addr, name) in enumerate(known_devices):
            blue = "\033[94m"
            error = "\033[91m"
            reset = "\033[0m"
            print(f"{blue}{idx + 1}{reset}: Device Name: {blue}{name}, Address: {blue}{addr}")

        blue = "\033[94m"
        error = "\033[91m"
        reset = "\033[0m"
        use_known_device = input(f"\n{reset}Do you want to use one of these known devices{blue}? {blue}({reset}yes{blue}/{reset}no{blue}): ")
        if use_known_device.lower() == 'yes':
            raw_choice = input(f"{reset}Enter the index number of the device to attack{blue}: ").strip()
            if not raw_choice.isdigit() or not (1 <= int(raw_choice) <= len(known_devices)):
                print("\nInvalid selection.")
                return []
            return [known_devices[int(raw_choice) - 1]]

    # Normal Bluetooth scan
    blue = "\033[94m"
    error = "\033[91m"
    reset = "\033[0m"
    print(f"\n{reset}Attempting to scan now{blue}...")
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True, lookup_class=True)
    device_list = []
    if len(nearby_devices) == 0:
        print(f"\n{reset}[{error}+{reset}] No nearby devices found.")
    else:
        print("\nFound {} nearby device(s):".format(len(nearby_devices)))
        for idx, (addr, name, _) in enumerate(nearby_devices):
            device_list.append((addr, name))

    # Save the scanned devices only if they are not already in known devices
    new_devices = [device for device in device_list if device not in known_devices]
    if new_devices:
        known_devices += new_devices
        save_devices_to_file(known_devices)
        for idx, (addr, name) in enumerate(new_devices):
            print(f"{reset}{idx + 1}{blue}: {blue}Device Name{reset}: {blue}{name}{reset}, {blue}Address{reset}: {blue}{addr}")
    return device_list

def getterm():
    # Robust to running without a controlling terminal (piped output, cron, or a
    # launcher with no tty): fall back to a sane width instead of raising OSError.
    return shutil.get_terminal_size((80, 24)).columns


def print_menu():
    blue = '\033[94m'
    reset = "\033[0m"
    title = "BlueDucky - Bluetooth Device Attacker"
    vertext = "Ver 2.1"
    motd1 = f"Remember, you can still attack devices without visibility.."
    motd2 = f"If you have their MAC address.."
    terminal_width = getterm()
    separator = "=" * terminal_width

    print(blue + separator)  # Blue color for separator
    print(reset + title.center(len(separator)))  # Centered Title in blue
    print(blue + vertext.center(len(separator)))  # Centered Version
    print(blue + separator + reset)  # Blue color for separator
    print(motd1.center(len(separator)))# used the same method for centering
    print(motd2.center(len(separator)))# used the same method for centering
    print(blue + separator + reset)  # Blue color for separator

def main_menu():
    clear_screen()
    print_fancy_ascii_art()
    print_menu()


def list_adapters():
    """Return available HCI adapter names, e.g. ['hci0', 'hci1'] (sorted)."""
    try:
        return sorted(n for n in os.listdir('/sys/class/bluetooth') if n.startswith('hci'))
    except FileNotFoundError:
        return []

def _adapter_usb_vendor(name):
    """USB vendor id (lowercase hex, e.g. '0a12') for an hci adapter, or None if
    it isn't USB. Read straight from sysfs so the adapter need not be powered up."""
    path = os.path.realpath(f"/sys/class/bluetooth/{name}")
    while path and path != "/":
        vid = os.path.join(path, "idVendor")
        if os.path.isfile(vid):
            try:
                return open(vid).read().strip().lower()
            except Exception:
                return None
        path = os.path.dirname(path)
    return None

def find_ud100(adapters=None):
    """Return the adapter name of a plugged-in Sena UD100 / CSR8510 (USB vendor
    0a12 = Cambridge Silicon Radio), or None. The UD100 is a Class-1 long-range
    dongle, so we prefer it when present. Re-checked every call, so it is fine
    that the dongle is not always plugged in."""
    if adapters is None:
        adapters = list_adapters()
    for name in adapters:
        if _adapter_usb_vendor(name) == "0a12":
            return name
    return None

def select_adapter(default='hci0'):
    """Interactively choose which Bluetooth adapter to use. If a Sena UD100
    (CSR8510) is plugged in, it becomes the default for its longer range.
    Returns the chosen adapter; falls back to `default` on blank/invalid input,
    so it never breaks the non-interactive flow."""
    blue = "\033[94m"
    reset = "\033[0m"
    adapters = list_adapters()
    ud100 = find_ud100(adapters)
    if ud100:
        default = ud100  # auto-prefer the long-range UD100 whenever it is plugged in

    if len(adapters) <= 1:
        only = adapters[0] if adapters else default
        if only == ud100:
            print(f"\n{blue}[i] Using long-range Sena UD100 ({only}).{reset}")
        return only

    print(f"\n{reset}Available Bluetooth adapters{blue}:{reset}")
    for idx, name in enumerate(adapters, 1):
        addr = ""
        try:
            out = subprocess.run(["hciconfig", name], capture_output=True, text=True).stdout
            m = re.search(r"BD Address: ([0-9A-Fa-f:]{17})", out)
            if m:
                addr = f"  ({m.group(1)})"
        except Exception:
            pass
        tag = ""
        if name == ud100:
            tag += f"{blue}  [Sena UD100 - long range]{reset}"
        if name == default:
            tag += f"{blue}  [default]{reset}"
        print(f"{blue}{idx}{reset}: {blue}{name}{reset}{addr}{tag}")
    raw = input(f"\n{reset}Select adapter by number (blank = {default}){blue}: {reset}").strip()
    if raw == "":
        return default
    if raw.isdigit() and 1 <= int(raw) <= len(adapters):
        return adapters[int(raw) - 1]
    print(f"{reset}Invalid selection; using {default}.")
    return default

def is_valid_mac_address(mac_address):
    # Regular expression to match a MAC address in the form XX:XX:XX:XX:XX:XX
    mac_address_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return mac_address_pattern.match(mac_address) is not None

# Function to read DuckyScript from file
def read_duckyscript(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return [line.strip() for line in file.readlines()]
    else:
        log.warning(f"File {filename} not found. Skipping DuckyScript.")
        return None

# Function to load known devices from a file
def load_known_devices(filename='known_devices.txt'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return [tuple(line.strip().split(',')) for line in file]
    else:
        return []


title = "BlueDucky - Bluetooth Device Attacker"
vertext = "Ver 2.1"
terminal_width = getterm()
separator = "=" * terminal_width
blue = "\033[0m"
reset = "\033[0m"

print(blue + separator)  # Blue color for separator
print(reset + title.center(len(separator)))  # White color for title
print(blue + vertext.center(len(separator)))  # White blue for version number
print(blue + separator + reset)  # Blue color for separator
print(f"{reset}Remember, you can still attack devices without visibility{blue}.." + reset)
print(f"{blue}If you have their {reset}MAC address{blue}.." + reset)
print(blue + separator + reset)  # Blue color for separator
