import os, bluetooth, re, subprocess, time, curses
import logging as log

##########################
# UI Redesign by Lamento #
##########################

def get_target_address():
    blue = "\033[94m"
    reset = "\033[0m"
    prompt = f"{blue}?{reset} Leave blank and we will scan for you{blue}!{reset}"

    print(f"\nWhat is the target address{prompt}")
    target_address = input(f"\n{blue}> {reset}").strip()

    if not target_address:
        devices = scan_for_devices()
        if not devices:
            return

        if len(devices) == 1 and isinstance(devices[0], tuple) and len(devices[0]) == 2:
            addr, name = devices[0]
            confirm = input(
                f"\nWould you like to register this device{blue}:\n{reset}{name} {addr}{blue}? {reset}(y/n){blue} "
            ).strip().lower()
            if confirm in {'y', 'yes'}:
                return addr
            else:
                return get_target_address()  # Rescan if the user doesn't confirm

        # Show list of scanned devices for user selection
        print("\nAvailable devices:")
        for idx, (addr, name) in enumerate(devices, 1):
            print(f"{reset}[{blue}{idx}{reset}] {blue}Device Name{reset}: {blue}{name}, Address{reset}: {blue}{addr}")

        try:
            selection = int(input(f"\n{reset}Select a device by number{blue}: {reset}")) - 1
            if 0 <= selection < len(devices):
                target_address = devices[selection][0]
            else:
                print(f"\n{reset}Invalid selection. Exiting.")
                return
        except ValueError:
            print(f"\n{reset}Invalid input. Exiting.")
            return
    elif not is_valid_mac_address(target_address):
        print(f"\n{reset}Invalid MAC address format. Please enter a valid MAC address.")
        return get_target_address()  # Prompt again for correct MAC address

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
            device_choice = int(input(f"{reset}Enter the index number of the device to attack{blue}: "))
            return [known_devices[device_choice - 1]]

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
    size = os.get_terminal_size()
    return size.columns


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
