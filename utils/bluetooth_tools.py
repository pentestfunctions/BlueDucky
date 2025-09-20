"""
Bluetooth management tools utility module.
Provides compatibility between hciconfig and btmgmt commands.
"""

import subprocess
import logging
from typing import List, Optional, Tuple
from pydbus import SystemBus

log = logging.getLogger(__name__)

class BluetoothTool:
    """Enum-like class for Bluetooth management tools."""
    HCICONFIG = "hciconfig"
    BTMGMT = "btmgmt"

class BluetoothManager:
    """Manages Bluetooth adapter operations using the appropriate tool."""
    
    def __init__(self, iface: str):
        self.iface = iface
        self.tool = self._detect_available_tool()
        log.info(f"Using Bluetooth management tool: {self.tool}")
    
    def _detect_available_tool(self) -> str:
        """Detect which Bluetooth management tool is available."""
        # Check for hciconfig first (legacy)
        try:
            result = subprocess.run(["which", "hciconfig"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return BluetoothTool.HCICONFIG
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Check for btmgmt (modern)
        try:
            result = subprocess.run(["which", "btmgmt"], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return BluetoothTool.BTMGMT
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # If neither is found, default to hciconfig and let the error propagate
        log.warning("Neither hciconfig nor btmgmt found, defaulting to hciconfig")
        return BluetoothTool.HCICONFIG
    
    def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        return subprocess.run(command, capture_output=True, text=True, timeout=30)
    
    def set_property(self, prop: str, value: str) -> Tuple[bool, str]:
        """
        Set a Bluetooth adapter property using the appropriate tool.
        
        Args:
            prop: Property name (e.g., 'up', 'down', 'sspmode')
            value: Property value
            
        Returns:
            Tuple of (success, output_message)
        """
        if self.tool == BluetoothTool.HCICONFIG:
            return self._set_property_hciconfig(prop, value)
        elif self.tool == BluetoothTool.BTMGMT:
            return self._set_property_btmgmt(prop, value)
        else:
            raise ValueError(f"Unknown Bluetooth tool: {self.tool}")
    
    def _set_property_hciconfig(self, prop: str, value: str) -> Tuple[bool, str]:
        """Set property using hciconfig."""
        command = ["sudo", "hciconfig", self.iface, prop, value]
        result = self._run_command(command)
        
        if result.returncode != 0:
            return False, f"Failed to set {prop}: {result.stderr}"
        
        # Verify the property was set
        verify_command = ["hciconfig", self.iface, prop]
        verify_result = self._run_command(verify_command)
        
        if value not in verify_result.stdout:
            return False, f"Property {prop} not set correctly. Output: {verify_result.stdout}"
        
        return True, f"Successfully set {prop} to {value}"
    
    def _set_property_btmgmt(self, prop: str, value: str) -> Tuple[bool, str]:
        """Set property using btmgmt."""
        # Handle special properties that require D-Bus
        if prop == 'name':
            return self._set_adapter_name_dbus(value)
        elif prop == 'class':
            return self._set_adapter_class_dbus(value)
        
        # Map hciconfig properties to btmgmt commands
        btmgmt_commands = {
            'up': ['power', 'on'],
            'down': ['power', 'off'],
            'sspmode': ['ssp', 'on' if value == '1' else 'off']
        }
        
        if prop not in btmgmt_commands:
            return False, f"Property {prop} not supported with btmgmt"
        
        btmgmt_prop, btmgmt_value = btmgmt_commands[prop]
        
        # For btmgmt, we need to use interactive mode or specific commands
        if btmgmt_prop == 'power':
            command = ["sudo", "btmgmt", "-i", self.iface, btmgmt_prop, btmgmt_value]
        elif btmgmt_prop == 'ssp':
            command = ["sudo", "btmgmt", "-i", self.iface, btmgmt_prop, btmgmt_value]
        else:
            return False, f"Unsupported btmgmt property: {btmgmt_prop}"
        
        result = self._run_command(command)
        
        if result.returncode != 0:
            return False, f"Failed to set {prop}: {result.stderr}"
        
        return True, f"Successfully set {prop} to {value} using btmgmt"
    
    def enable_ssp(self) -> Tuple[bool, str]:
        """Enable Secure Simple Pairing (SSP)."""
        if self.tool == BluetoothTool.HCICONFIG:
            return self._enable_ssp_hciconfig()
        elif self.tool == BluetoothTool.BTMGMT:
            return self._enable_ssp_btmgmt()
        else:
            raise ValueError(f"Unknown Bluetooth tool: {self.tool}")
    
    def _enable_ssp_hciconfig(self) -> Tuple[bool, str]:
        """Enable SSP using hciconfig."""
        command = ["sudo", "hciconfig", self.iface, "sspmode", "1"]
        result = self._run_command(command)
        
        if result.returncode != 0:
            return False, f"Failed to enable SSP: {result.stderr}"
        
        return True, "SSP enabled successfully using hciconfig"
    
    def _enable_ssp_btmgmt(self) -> Tuple[bool, str]:
        """Enable SSP using btmgmt."""
        command = ["sudo", "btmgmt", "-i", self.iface, "ssp", "on"]
        result = self._run_command(command)
        
        if result.returncode != 0:
            return False, f"Failed to enable SSP: {result.stderr}"
        
        return True, "SSP enabled successfully using btmgmt"
    
    def _set_adapter_name_dbus(self, name: str) -> Tuple[bool, str]:
        """Set adapter name using D-Bus."""
        try:
            bus = SystemBus()
            adapter_path = f"/org/bluez/{self.iface}"
            adapter = bus.get("org.bluez", adapter_path)
            adapter.Alias = name
            return True, f"Successfully set adapter name to '{name}' using D-Bus"
        except Exception as e:
            return False, f"Failed to set adapter name using D-Bus: {str(e)}"
    
    def _set_adapter_class_dbus(self, class_value: str) -> Tuple[bool, str]:
        """Set adapter class using D-Bus."""
        try:
            bus = SystemBus()
            adapter_path = f"/org/bluez/{self.iface}"
            adapter = bus.get("org.bluez", adapter_path)
            
            # Convert string to integer if needed
            if isinstance(class_value, str):
                if class_value.startswith('0x'):
                    class_int = int(class_value, 16)
                else:
                    class_int = int(class_value)
            else:
                class_int = class_value
            
            # Try different methods to set the Class property
            try:
                # Method 1: Use Set method
                adapter.Set("org.bluez.Adapter1", "Class", class_int)
                return True, f"Successfully set adapter class to {class_int} using D-Bus Set method"
            except Exception as e1:
                try:
                    # Method 2: Direct property assignment
                    adapter.Class = class_int
                    return True, f"Successfully set adapter class to {class_int} using D-Bus direct assignment"
                except Exception as e2:
                    # Method 3: Use Properties interface
                    try:
                        props = bus.get("org.bluez", adapter_path, "org.freedesktop.DBus.Properties")
                        props.Set("org.bluez.Adapter1", "Class", class_int)
                        return True, f"Successfully set adapter class to {class_int} using D-Bus Properties interface"
                    except Exception as e3:
                        # If all methods fail, return a warning but don't treat as critical error
                        return True, f"Warning: Could not set adapter class via D-Bus (Class property may be read-only). Attempted methods failed: Set({str(e1)}), Direct({str(e2)}), Properties({str(e3)})"
                        
        except Exception as e:
            return False, f"Failed to access adapter via D-Bus: {str(e)}"
    
    def get_adapter_info(self) -> str:
        """Get adapter information using the appropriate tool."""
        if self.tool == BluetoothTool.HCICONFIG:
            command = ["hciconfig", self.iface]
        elif self.tool == BluetoothTool.BTMGMT:
            command = ["btmgmt", "-i", self.iface, "info"]
        else:
            raise ValueError(f"Unknown Bluetooth tool: {self.tool}")
        
        result = self._run_command(command)
        return result.stdout if result.returncode == 0 else result.stderr
