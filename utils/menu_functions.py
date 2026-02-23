import os, bluetooth, re, subprocess, time, curses
import logging as log

from utils.color import color

##########################
# UI Redesign by Lamento #
##########################

def get_target_address():
    print(f"\n What is the target address{color.BLUE}? {color.RESET}Leave blank and we will scan for you{color.BLUE}!{color.RESET}")
    target_address = input(f"\n {color.BLUE}> ")

    if target_address == "":
        devices = scan_for_devices()
        if devices:
            # Check if the returned list is from known devices or scanned devices
            if len(devices) == 1 and isinstance(devices[0], tuple) and len(devices[0]) == 2:
                # A single known device was chosen, no need to ask for selection
                # I think it would be better to ask, as sometimes I do not want to chose this device and actually need solely to scan for actual devices.
                confirm = input(f"\n Would you like to register this device{color.BLUE}:\n{color.RESET}{devices[0][1]} {devices[0][0]}{color.BLUE}? {color.BLUE}({color.RESET}y{color.BLUE}/{color.RESET}n{color.BLUE}) {color.BLUE}").strip().lower()
                if confirm == 'y' or confirm == 'yes':
                    return devices[0][0]
                elif confirm != 'y' or 'yes':
                    return
            else:
                # Show list of scanned devices for user selection
                for idx, (addr, name) in enumerate(devices):
                    print(f"{color.RESET}[{color.BLUE}{idx + 1}{color.RESET}] {color.BLUE}Device Name{color.RESET}: {color.BLUE}{name}, {color.BLUE}Address{color.RESET}: {color.BLUE}{addr}")
                selection = int(input(f"\n{color.RESET}Select a device by number{color.BLUE}: {color.BLUE}")) - 1
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

    # Load known devices
    known_devices = load_known_devices()
    if known_devices:
        print(f"\n{color.RESET}Known devices{color.BLUE}:")
        for idx, (addr, name) in enumerate(known_devices):
            print(f"{color.BLUE}{idx + 1}{color.RESET}: Device Name: {color.BLUE}{name}, Address: {color.BLUE}{addr}")

        use_known_device = input(f"\n{color.RESET}Do you want to use one of these known devices{color.BLUE}? {color.BLUE}({color.RESET}yes{color.BLUE}/{color.RESET}no{color.BLUE}): ")
        if use_known_device.lower() == 'yes':
            device_choice = int(input(f"{color.RESET}Enter the index number of the device to attack{color.BLUE}: "))
            return [known_devices[device_choice - 1]]

    # Normal Bluetooth scan
    print(f"\n{color.RESET}Attempting to scan now{color.BLUE}...")
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True, lookup_class=True)
    device_list = []
    if len(nearby_devices) == 0:
        print(f"\n{color.RESET}[{error}+{color.RESET}] No nearby devices found.")
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
            print(f"{color.RESET}{idx + 1}{color.BLUE}: {color.BLUE}Device Name{color.RESET}: {color.BLUE}{name}{color.RESET}, {color.BLUE}Address{color.RESET}: {color.BLUE}{addr}")
    return device_list

def getterm():
    size = os.get_terminal_size()
    return size.columns


def print_menu():
    title = "BlueDucky - Bluetooth Device Attacker"
    vertext = "Ver 2.1"
    motd1 = f"Remember, you can still attack devices without visibility.."
    motd2 = f"If you have their MAC address.."
    terminal_width = getterm()
    separator = "=" * terminal_width

    print(color.BLUE + separator)  # Blue color for separator
    print(color.RESET + title.center(len(separator)))  # Centered Title in blue
    print(color.BLUE + vertext.center(len(separator)))  # Centered Version
    print(color.BLUE + separator + color.RESET)  # Blue color for separator
    print(motd1.center(len(separator)))# used the same method for centering
    print(motd2.center(len(separator)))# used the same method for centering
    print(color.BLUE + separator + color.RESET)  # Blue color for separator

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

print(color.BLUE + separator)  # Blue color for separator
print(color.RESET + title.center(len(separator)))  # White color for title
print(color.BLUE + vertext.center(len(separator)))  # White blue for version number
print(color.BLUE + separator + color.RESET)  # Blue color for separator
print(f"{color.RESET}Remember, you can still attack devices without visibility{color.BLUE}.." + color.RESET)
print(f"{color.BLUE}If you have their {color.RESET}MAC address{color.BLUE}.." + color.RESET)
print(color.BLUE + separator + color.RESET)  # Blue color for separator
