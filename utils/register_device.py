import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib
import logging as log

class Agent(dbus.service.Object):
  @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
  def Cancel(self):
    log.debug("Agent.Cancel")

class Profile(dbus.service.Object):
  @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
  def Cancel(self):
    print("Profile.Cancel")

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
