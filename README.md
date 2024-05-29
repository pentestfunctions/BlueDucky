# BlueDucky Version 2.1 (for Android) 🦆
exus. Make sure you come join us on VC !
https://discord.gg/HackNexus

NOTES: I will not be able to run this on a laptop or other device outside of a raspberry pi for testing. Due to this, any issues you have will need to be resolved amonsgt each other as I do not have the spare funds to buy an adapter. 

1. [saad0x1's GitHub](https://github.com/saad0x1)
2. [spicydll's GitHub](https://github.com/spicydll)
3. [lamentomori's GitHub](https://github.com/lamentomori)

<p align="center">
  <img src="./images/duckmenu.png">
</p>

🚨 CVE-2023-45866 - BlueDucky Implementation (Using DuckyScript)

🔓 Unauthenticated Peering Leading to Code Execution (Using HID Keyboard)

[This is an implementation of the CVE discovered by marcnewlin](https://github.com/marcnewlin/hi_my_name_is_keyboard)

<p align="center">
  <img src="./images/BlueDucky.gif">
</p>

## Introduction 📢

BlueDucky is an advanced tool designed to exploit vulnerabilities in Bluetooth devices. By leveraging this script, users can:

1. 📡 Load saved Bluetooth devices that are no longer visible but still have Bluetooth enabled.
2. 📂 Automatically save any scanned devices.
3. 💌 Send messages in DuckyScript format to interact with devices.

This script has been successfully tested on a Raspberry Pi 4 using the default Bluetooth module. It is effective against various phones, with the exception of New Zealand brand, Vodafone.

## Installation and Usage 🛠️

### Setup Instructions for Debian-based Systems

```bash
# Update apt
sudo apt-get update
sudo apt-get -y upgrade

# Install dependencies from apt
sudo apt install -y bluez-tools bluez-hcidump libbluetooth-dev \
                    git gcc python3-pip python3-setuptools \
                    python3-pydbus

# Install pybluez from source
git clone https://github.com/pybluez/pybluez.git
cd pybluez
sudo python3 setup.py install

# Build bdaddr from the bluez source
cd ~/
git clone --depth=1 https://github.com/bluez/bluez.git
gcc -o bdaddr ~/bluez/tools/bdaddr.c ~/bluez/src/oui.c -I ~/bluez -lbluetooth
sudo cp bdaddr /usr/local/bin/
```


### Setup Instructions for Arch-based Systems

```bash
# Update pacman & packages
sudo pacman -Syyu

# Install dependencies
# Note: libbluetooth-dev included in bluez package for Arch-based systems
sudo pacman -S bluez-tools bluez-utils bluez-deprecated-tools \
               python-setuptools python-pydbus python-dbus \
               git gcc python-pip \

# Install pybluez from source
git clone https://github.com/pybluez/pybluez.git
cd pybluez
sudo python3 setup.py install

# Build bdaddr from the bluez source
cd ~/
git clone --depth=1 https://github.com/bluez/bluez.git
gcc -o bdaddr ~/bluez/tools/bdaddr.c ~/bluez/src/oui.c -I ~/bluez -lbluetooth
sudo cp bdaddr /usr/local/bin/
```

## Running BlueDucky

```bash
git clone https://github.com/pentestfunctions/BlueDucky.git
cd BlueDucky
sudo hciconfig hci0 up
python3 BlueDucky.py
```
Alternatively,

```python3
pip3 install -r requirements.txt
```

## Operational Steps 🕹️

1. Upon execution, it prompts for the target MAC address.
2. Pressing nothing triggers an automatic scan for devices.
3. Previously found devices are stored in known_devices.txt.
4. If known_devices.txt exists, it checks this file before scanning.
5. Executes using payload.txt file.
6. Successful execution results in automatic connection and script running.

## DuckyScript 💻

🚧 Work in Progress:
- Suggest ideas for improvement

## Version 2.1 🐛

- Updated UI
- Improved User Experience
- Bluetooth Debugger; Checks your Bluetooth adapters and installed dependencies before granting access to the application to prevent unsupported devices.
- Please Note: Numerous changes have been made; please reference the commit history for specific changes.

## What's Planned for the Next Release?

- Integrated DuckyScript Console for attacks that aim to maintain persistence after a payload has been executed.
- Suggest what should be added next! Join [HackNexus Discord Server](https://discord.gg/HackNexus)

### 📝 Example payload.txt:

```bash
REM Title of the payload
STRING ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()_-=+\|[{]};:'",<.>/?
GUI D
```

```bash
REM Opens a private browser to hackertyper.net
DELAY 200
ESCAPE
GUI d
ALT ESCAPE
GUI b
DELAY 700
REM PRIVATE_BROWSER is equal to CTRL + SHIFT + N
PRIVATE_BROWSER
DELAY 700
CTRL l
DELAY 300
STRING hackertyper.net
DELAY 300
ENTER
DELAY 300
```

## Enjoy experimenting with BlueDucky! 🌟
