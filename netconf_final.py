from ncclient import manager
import xmltodict

m = manager.connect(
    host="<!!!REPLACEME with router IP address!!!>",
    port=<!!!REPLACEME with NETCONF Port number!!!>,
    username="admin",
    password="cisco",
    hostkey_verify=False
    )

def create():
    netconf_config = """<!!!REPLACEME with YANG data!!!>"""

    try:
        netconf_reply = netconf_edit_config(netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        if '<ok/>' in xml_data:
            return "<!!!REPLACEME with proper message!!!>"
    except:
        print("Error!")


def delete():
    netconf_config = """<!!!REPLACEME with YANG data!!!>"""

    try:
        netconf_reply = netconf_edit_config(netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        if '<ok/>' in xml_data:
            return "<!!!REPLACEME with proper message!!!>"
    except:
        print("Error!")


def enable():
    netconf_config = """<!!!REPLACEME with YANG data!!!>"""

    try:
        netconf_reply = netconf_edit_config(netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        if '<ok/>' in xml_data:
            return "<!!!REPLACEME with proper message!!!>"
    except:
        print("Error!")


def disable():
    netconf_config = """<!!!REPLACEME with YANG data!!!>"""

    try:
        netconf_reply = netconf_edit_config(netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        if '<ok/>' in xml_data:
            return "<!!!REPLACEME with proper message!!!>"
    except:
        print("Error!")

def netconf_edit_config(netconf_config):
    return  m.<!!!REPLACEME with the proper Netconf operation!!!>(target="<!!!REPLACEME with NETCONF Datastore!!!>", config=<!!!REPLACEME with netconf_config!!!>)


def status():
    netconf_filter = """<!!!REPLACEME with YANG data!!!>"""

    try:
        # Use Netconf operational operation to get interfaces-state information
        netconf_reply = m.<!!!REPLACEME with the proper Netconf operation!!!>(filter=<!!!REPLACEME with netconf_filter!!!>)
        print(netconf_reply)
        netconf_reply_dict = xmltodict.<!!!REPLACEME with the proper method!!!>(netconf_reply.xml)

        # if there data return from netconf_reply_dict is not null, the operation-state of interface loopback is returned
        if <!!!REPLACEME with the proper condition!!!>:
            # extract admin_status and oper_status from netconf_reply_dict
            admin_status = <!!!REPLACEME!!!>
            oper_status = <!!!REPLACEME !!!>
            if admin_status == 'up' and oper_status == 'up':
                return "<!!!REPLACEME with proper message!!!>"
            elif admin_status == 'down' and oper_status == 'down':
                return "<!!!REPLACEME with proper message!!!>"
        else: # no operation-state data
            return "<!!!REPLACEME with proper message!!!>"
    except:
       print("Error!")
