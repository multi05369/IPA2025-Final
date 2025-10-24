from ncclient import manager
import xmltodict
from typing import Optional

# Allowed router IPs (match your main)
ALLOWED_IPS = {
    "10.0.15.61",
    "10.0.15.62",
    "10.0.15.63",
    "10.0.15.64",
    "10.0.15.65",
}


ROUTER_USER = "admin"
ROUTER_PASS = "cisco"

IF_NAME = "Loopback66070101"

# --------------------------------------------------------------
# Helpers
# --------------------------------------------------------------

def _require_ip(ip: Optional[str]):
    if not ip:
        return "Error: No IP specified"
    if ip not in ALLOWED_IPS:
        return f"Error: IP not allowed ({ip})"
    return None


def _connect(ip: str):
    # Open a NETCONF over SSH session to the specific device
    return manager.connect(
        host=ip,
        port=830,
        username=ROUTER_USER,
        password=ROUTER_PASS,
        hostkey_verify=False,
        allow_agent=False,
        look_for_keys=False,
        timeout=30,
    )


def _netconf_edit_config(mgr, netconf_config: str):
    return mgr.edit_config(target="running", config=netconf_config)


def _netconf_get_config(mgr, netconf_filter: str):
    return mgr.get_config(source="running", filter=netconf_filter)


def _check_interface_exist(mgr) -> bool:
    find_interface = f"""
        <filter>
            <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                <interface><name>{IF_NAME}</name></interface>
            </interfaces>
        </filter>
    """
    try:
        reply_xml = _netconf_get_config(mgr, find_interface).xml
        return IF_NAME in reply_xml
    except Exception:
        return False


# --------------------------------------------------------------
# Core functions (per-command IP)
# --------------------------------------------------------------

def create(ip: Optional[str] = None):
    err = _require_ip(ip)
    if err:
        return err

    netconf_config = f"""
        <config>
            <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                <interface>
                    <name>{IF_NAME}</name>
                    <description>Created by 66070101</description>
                    <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type>
                    <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
                        <address>
                            <ip>172.1.1.1</ip>
                            <netmask>255.255.255.0</netmask>
                        </address>
                    </ipv4>
                </interface>
            </interfaces>
        </config>
    """

    try:
        with _connect(ip) as m:
            if _check_interface_exist(m):
                raise Exception("Interface already exists")

            reply = _netconf_edit_config(m, netconf_config)
            xml_data = reply.xml
            print(xml_data)
            if "<ok/>" in xml_data or "<ok />" in xml_data:
                return "Interface loopback 66070101 is created successfully"
    except Exception as e:
        print("Error!", e)
    return "Cannot create: Interface loopback 66070101"


def delete(ip: Optional[str] = None):
    err = _require_ip(ip)
    if err:
        return err

    netconf_config = f"""
        <config>
            <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                <interface operation="delete">
                    <name>{IF_NAME}</name>
                </interface>
            </interfaces>
        </config>
    """

    try:
        with _connect(ip) as m:
            if not _check_interface_exist(m):
                raise Exception("Interface does not exist")

            reply = _netconf_edit_config(m, netconf_config)
            xml_data = reply.xml
            print(xml_data)
            if "<ok/>" in xml_data or "<ok />" in xml_data:
                return "Interface loopback 66070101 is deleted successfully"
    except Exception as e:
        print("Error!", e)
    return "Cannot delete: Interface loopback 66070101"


def enable(ip: Optional[str] = None):
    err = _require_ip(ip)
    if err:
        return err

    netconf_config = f"""
        <config>
            <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                <interface>
                    <name>{IF_NAME}</name>
                    <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type>
                    <enabled>true</enabled>
                </interface>
            </interfaces>
        </config>
    """

    try:
        with _connect(ip) as m:
            if not _check_interface_exist(m):
                raise Exception("Interface does not exist")

            reply = _netconf_edit_config(m, netconf_config)
            xml_data = reply.xml
            print(xml_data)
            if "<ok/>" in xml_data or "<ok />" in xml_data:
                return "Interface loopback 66070101 is enabled successfully"
    except Exception as e:
        print("Error!", e)
    return "Cannot enable: Interface loopback 66070101"


def disable(ip: Optional[str] = None):
    err = _require_ip(ip)
    if err:
        return err

    netconf_config = f"""
        <config>
            <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                <interface>
                    <name>{IF_NAME}</name>
                    <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type>
                    <enabled>false</enabled>
                </interface>
            </interfaces>
        </config>
    """

    try:
        with _connect(ip) as m:
            if not _check_interface_exist(m):
                raise Exception("Interface does not exist")

            reply = _netconf_edit_config(m, netconf_config)
            xml_data = reply.xml
            print(xml_data)
            if "<ok/>" in xml_data or "<ok />" in xml_data:
                return "Interface loopback 66070101 is shutdowned successfully"
    except Exception as e:
        print("Error!", e)
    return "Cannot shutdown: Interface loopback 66070101"


def status(ip: Optional[str] = None):
    err = _require_ip(ip)
    if err:
        return err

    netconf_filter = f"""
        <filter>
            <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                <interface><name>{IF_NAME}</name></interface>
            </interfaces-state>
        </filter>
    """

    try:
        with _connect(ip) as m:
            netconf_reply = m.get(filter=netconf_filter)
            print(netconf_reply)
            netconf_reply_dict = xmltodict.parse(netconf_reply.xml)

            data = netconf_reply_dict.get("rpc-reply", {}).get("data")
            if data:
                iface = data.get("interfaces-state", {}).get("interface")
                # iface may be a dict or a list; handle dict case
                if isinstance(iface, dict):
                    admin_status = iface.get("admin-status")
                    oper_status = iface.get("oper-status", "unknown")

                    if admin_status == "up" and oper_status == "up":
                        return "Interface loopback 66070101 is enabled"
                    if admin_status == "down" and oper_status == "down":
                        return "Interface loopback 66070101 is disabled"
                    if admin_status == "up" and oper_status == "unknown":
                        return "Interface loopback 66070101 is enabled"
                    if admin_status == "down" and oper_status == "unknown":
                        return "Interface loopback 66070101 is disabled"
                    if admin_status == "down" or oper_status == "down":
                        return "Interface loopback 66070101 is disabled"
                    return "Interface loopback 66070101 is enabled"
                else:
                    # No single interface dict found
                    return "No Interface loopback 66070101"
            else:
                return "No Interface loopback 66070101"
    except Exception as e:
        print("Error!", e)
        return "Cannot read status: Interface loopback 66070101"