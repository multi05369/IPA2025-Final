import os
import time
import json
import requests
import dotenv
from requests_toolbelt.multipart.encoder import MultipartEncoder
import restconf_final as restconf
import netconf_final as netconf
import netmiko_final as netmiko
import ansible_final as ansible

dotenv.load_dotenv()

# ---------------------------------------
# 1) Config and helpers
# ---------------------------------------
STUDENT_ID = "66070101"

# Allowed routers
ALLOWED_IPS = {
    "10.0.15.61",
    "10.0.15.62",
    "10.0.15.63",
    "10.0.15.64",
    "10.0.15.65",
}

# Methods
METHOD_RESTCONF = "restconf"
METHOD_NETCONF = "netconf"
METHOD_LABEL = {
    METHOD_RESTCONF: "Restconf",
    METHOD_NETCONF: "Netconf",
}

# Maintain selected method across commands
current_method = None  # one of None, "restconf", "netconf"

# Webex
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
if not ACCESS_TOKEN:
    raise RuntimeError("ACCESS_TOKEN is not set in environment variables.")

roomIdToGetMessages = (
    "Y2lzY29zcGFyazovL3VybjpURUFNOnVzLXdlc3QtMl9yL1JPT00vYmQwODczMTAtNmMyNi0xMWYwLWE1MWMtNzkzZDM2ZjZjM2Zm"
)


def post_message_to_webex(room_id: str, message: str):
    r = requests.post(
        "https://webexapis.com/v1/messages",
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        data=json.dumps({"roomId": room_id, "markdown": message}),
    )
    return r


# ---------------------------------------
# 2) Utility checks and formatters
# ---------------------------------------
def set_method(method_str: str):
    global current_method
    if method_str not in (METHOD_RESTCONF, METHOD_NETCONF):
        return "Error: No method specified"
    current_method = method_str
    return f"Ok: {METHOD_LABEL[current_method]}"


def ensure_method_selected():
    if not current_method:
        return "Error: No method specified"
    return None


def ensure_ip_provided(ip: str | None):
    if not ip:
        return "Error: No IP specified"
    if ip not in ALLOWED_IPS:
        return f"Error: IP not allowed ({ip})"
    return None


def _append_method_suffix(base_msg: str, cmd: str, method_key: str) -> str:
    """
    Append method suffix per requirement:
      - create/delete/enable/disable: "... using Restconf/Netconf"
      - status: "... (checked by Restconf/Netconf)"
    Do not duplicate suffix if already present.
    """
    label = METHOD_LABEL.get(method_key, method_key)
    if cmd == "status":
        if "(checked by" not in base_msg:
            return f"{base_msg} (checked by {label})"
        return base_msg
    else:
        if "using " not in base_msg:
            return f"{base_msg} using {label}"
        return base_msg


# ---------------------------------------
# 3) Command handlers
# ---------------------------------------
def handle_part1_command(cmd: str, ip: str | None) -> str:
    """
    Dispatch create/delete/enable/disable/status to restconf/netconf
    based on current_method and append the method suffix.
    """
    err = ensure_method_selected()
    if err:
        return err

    err = ensure_ip_provided(ip)
    if err:
        return err

    try:
        if current_method == METHOD_RESTCONF:
            if cmd == "create":
                msg = restconf.create(ip=ip)
            elif cmd == "delete":
                msg = restconf.delete(ip=ip)
            elif cmd == "enable":
                msg = restconf.enable(ip=ip)
            elif cmd == "disable":
                msg = restconf.disable(ip=ip)
            elif cmd == "status":
                msg = restconf.status(ip=ip)
            else:
                return "Error: No command found."
            return _append_method_suffix(msg, cmd, current_method)

        elif current_method == METHOD_NETCONF:
            if cmd == "create":
                msg = netconf.create(ip=ip)
            elif cmd == "delete":
                msg = netconf.delete(ip=ip)
            elif cmd == "enable":
                msg = netconf.enable(ip=ip)
            elif cmd == "disable":
                msg = netconf.disable(ip=ip)
            elif cmd == "status":
                msg = netconf.status(ip=ip)
            else:
                return "Error: No command found."
            return _append_method_suffix(msg, cmd, current_method)

    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

    return "Error: No command found."


def handle_showrun(ip: str | None):
    """
    Call ansible.showrun(ip) which returns:
      - a filename (string) on success
      - or 'Error: ...'
    If filename, attach it to Webex and return None (since we posted already).
    If Error, return the error string to be posted as text.
    """
    try:
        result = ansible.showrun(ip=ip)
    except Exception as e:
        result = f"Error: {type(e).__name__}: {e}"

    if not result or result.startswith("Error:"):
        return result or "Error: Ansible"

    filename = result
    try:
        with open(filename, "rb") as f:
            m = MultipartEncoder(
                fields={
                    "roomId": roomIdToGetMessages,
                    "text": "show running config",
                    "files": (os.path.basename(filename), f, "text/plain"),
                }
            )
            headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Content-Type": m.content_type,
            }
            r = requests.post(
                "https://webexapis.com/v1/messages",
                data=m,
                headers=headers,
            )
            if r.status_code != 200:
                print("Webex POST failed:", r.status_code, r.text)
                return "Error: Ansible"
    except Exception as e:
        print("Attach file failed:", e)
        return "Error: Ansible"

    return None


def handle_motd_set(ip: str | None, message: str | None) -> str:
    """
    Set MOTD via Ansible:
      returns "Ok: success" or "Error: ..."
    """
    # ansible.motd_set will also validate IP/message
    try:
        result = ansible.motd_set(ip=ip, message=message)
    except Exception as e:
        result = f"Error: {type(e).__name__}: {e}"
    return result


def handle_motd_get(ip: str | None) -> str:
    """
    Get MOTD via Netmiko/TextFSM:
      returns banner text or "Error: No MOTD Configured" or "Error: ..."
    """
    try:
        result = netmiko.motd_get(ip=ip)
    except Exception as e:
        result = f"Error: {type(e).__name__}: {e}"
    return result


# ---------------------------------------
# 4) Parser
# ---------------------------------------
def parse_command(text: str):
    """
    After removing leading '/<student_id> ', parse command.

    Supported:
    - restconf
    - netconf
    - <ip> <action> where action in {create, delete, enable, disable, status}
    - <action>                -> error: missing IP (handled later)
    - <ip> gigabit_status
    - gigabit_status          -> error: missing IP
    - <ip> showrun
    - showrun                 -> error: missing IP
    - <ip> motd <message...>  -> set motd via ansible
    - <ip> motd               -> get motd via netmiko
    - lone IP                 -> "Error: No command found."
    """
    parts = text.strip().split()
    if not parts:
        return {"type": "error", "message": "Error: No command or unknown command"}

    # Method selection
    if parts[0] in (METHOD_RESTCONF, METHOD_NETCONF) and len(parts) == 1:
        return {"type": "set_method", "method": parts[0]}

    # Single IP only -> explicit error per requirement
    if len(parts) == 1 and parts[0] in ALLOWED_IPS:
        return {"type": "error", "message": "Error: No command found."}

    # Showrun requires IP now: "<ip> showrun"
    if len(parts) == 2 and parts[1] == "showrun":
        return {"type": "showrun", "ip": parts[0]}
    if len(parts) == 1 and parts[0] == "showrun":
        return {"type": "showrun", "ip": None}

    # MOTD:
    # "<ip> motd <message...>" => set
    if len(parts) >= 3 and parts[1] == "motd":
        msg = " ".join(parts[2:])
        return {"type": "motd_set", "ip": parts[0], "message": msg}
    # "<ip> motd" => get
    if len(parts) == 2 and parts[1] == "motd":
        return {"type": "motd_get", "ip": parts[0]}

    # Part1 actions
    part1_actions = {"create", "delete", "enable", "disable", "status"}

    # Case: "<ip> <action>"
    if len(parts) == 2 and parts[1] in part1_actions:
        return {"type": "part1", "ip": parts[0], "action": parts[1]}

    # Case: "<action>" (missing IP)
    if len(parts) == 1 and parts[0] in part1_actions:
        return {"type": "part1", "ip": None, "action": parts[0]}

    # Netmiko gigabit_status expects IP: "<ip> gigabit_status"
    if len(parts) == 2 and parts[1] == "gigabit_status":
        return {"type": "gigabit_status", "ip": parts[0]}
    if len(parts) == 1 and parts[0] == "gigabit_status":
        return {"type": "gigabit_status", "ip": None}

    return {"type": "error", "message": "Error: No command or unknown command"}


# ---------------------------------------
# 5) Main loop
# ---------------------------------------
def main():
    while True:
        # Rate-limit polling
        time.sleep(1)

        # GET latest message
        get_params = {"roomId": roomIdToGetMessages, "max": 1}
        get_headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        r = requests.get(
            "https://webexapis.com/v1/messages",
            params=get_params,
            headers=get_headers,
        )
        if r.status_code != 200:
            raise Exception(
                f"Incorrect reply from Webex Teams API. Status code: {r.status_code}"
            )

        json_data = r.json()
        if len(json_data.get("items", [])) == 0:
            raise Exception("There are no messages in the room.")

        messages = json_data["items"]
        message = messages[0].get("text", "")
        print("Received message: " + str(message))

        prefix = f"/{STUDENT_ID} "
        if not message.startswith(prefix):
            continue

        # Extract the command text after "/<id> "
        command_text = message[len(prefix) :]

        parsed = parse_command(command_text)
        response_message = None

        if parsed["type"] == "set_method":
            response_message = set_method(parsed["method"])

        elif parsed["type"] == "part1":
            response_message = handle_part1_command(
                parsed["action"], parsed.get("ip")
            )

        elif parsed["type"] == "gigabit_status":
            try:
                response_message = netmiko.gigabit_status(ip=parsed.get("ip"))
            except Exception as e:
                response_message = f"Error: {type(e).__name__}: {e}"

        elif parsed["type"] == "showrun":
            response_message = handle_showrun(parsed.get("ip"))

        elif parsed["type"] == "motd_set":
            response_message = handle_motd_set(
                parsed.get("ip"), parsed.get("message")
            )

        elif parsed["type"] == "motd_get":
            response_message = handle_motd_get(parsed.get("ip"))

        elif parsed["type"] == "error":
            response_message = parsed["message"]

        else:
            response_message = "Error: No command or unknown command"

        # Post text reply (if any). When showrun succeeds, response_message is None
        if response_message:
            reply = post_message_to_webex(roomIdToGetMessages, response_message)
            if reply.status_code != 200:
                print("Webex POST failed:", reply.status_code, reply.text)


if __name__ == "__main__":
    main()
