import json
import requests

requests.packages.urllib3.disable_warnings()

# Allowed router IPs
ALLOWED_IPS = {
    "10.0.15.61",
    "10.0.15.62",
    "10.0.15.63",
    "10.0.15.64",
    "10.0.15.65",
}

# the RESTCONF HTTP headers, including the Accept and Content-Type
# Two YANG data formats (JSON and XML) work with RESTCONF
headers = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}
basicauth = ("admin", "cisco")

IF_NAME = "Loopback66070101"
IF_PATH = f"ietf-interfaces:interfaces/interface={IF_NAME}"


def _require_ip(ip: str | None):
    if not ip:
        return "Error: No IP specified"
    if ip not in ALLOWED_IPS:
        return f"Error: IP not allowed ({ip})"
    return None


def _api_url(ip: str) -> str:
    return f"https://{ip}/restconf/data/{IF_PATH}"


def create(ip: str | None = None):
    err = _require_ip(ip)
    if err:
        return err

    api_url = _api_url(ip)

    yangConfig = {
        "ietf-interfaces:interface": {
            "name": IF_NAME,
            "type": "iana-if-type:softwareLoopback",
            "description": "Created by 66070101",
            "enabled": True,
            "ietf-ip:ipv4": {
                "address": [{"ip": "172.1.1.1", "netmask": "255.255.255.0"}]
            },
            "ietf-ip:ipv6": {},
        }
    }

    resp = requests.put(
        api_url, data=json.dumps(yangConfig), auth=basicauth, headers=headers, verify=False
    )

    if 200 <= resp.status_code <= 299:
        print("STATUS OK: {}".format(resp.status_code))
        return (
            "Interface loopback 66070101 is created successfully"
            if resp.status_code == 201
            else "Cannot create: Interface loopback 66070101"
        )
    else:
        print("Error. Status Code: {}".format(resp.status_code))
        try:
            print(resp.text)
        except Exception:
            pass
        return "Cannot create: Interface loopback 66070101"


def delete(ip: str | None = None):
    err = _require_ip(ip)
    if err:
        return err

    api_url = _api_url(ip)

    resp = requests.delete(api_url, auth=basicauth, headers=headers, verify=False)

    if 200 <= resp.status_code <= 299:
        print("STATUS OK: {}".format(resp.status_code))
        return "Interface loopback 66070101 is deleted successfully"
    elif resp.status_code == 404:
        print("STATUS NOT FOUND: {}".format(resp.status_code))
        return "Cannot delete: Interface loopback 66070101"
    else:
        print("Error. Status Code: {}".format(resp.status_code))
        try:
            print(resp.text)
        except Exception:
            pass
        return "Cannot delete: Interface loopback 66070101"


def enable(ip: str | None = None):
    err = _require_ip(ip)
    if err:
        return err

    api_url = _api_url(ip)

    # 1) Read current admin state
    state_resp = requests.get(api_url, auth=basicauth, headers=headers, verify=False)

    if state_resp.status_code == 404:
        print("STATUS NOT FOUND: 404")
        return "Cannot enable: Interface loopback 66070101 not found"

    if 200 <= state_resp.status_code <= 299:
        data = {}
        try:
            data = state_resp.json().get("ietf-interfaces:interface", {})
        except Exception:
            pass
        currently_enabled = bool(data.get("enabled", False))

        # 2) If already enabled, report it
        if currently_enabled:
            return "Cannot enable: Interface loopback 66070101"

        # 3) Otherwise, patch to enable
        yangConfig = {"ietf-interfaces:interface": {"enabled": True}}
        resp = requests.patch(
            api_url, data=json.dumps(yangConfig), auth=basicauth, headers=headers, verify=False
        )

        if 200 <= resp.status_code <= 299:
            print("STATUS OK: {}".format(resp.status_code))
            return "Interface loopback 66070101 is enabled successfully"
        else:
            print("Error. Status Code: {}".format(resp.status_code))
            try:
                print(resp.text)
            except Exception:
                pass
            return "Cannot enable: Interface loopback 66070101"
    else:
        print("Error. Status Code (GET): {}".format(state_resp.status_code))
        try:
            print(state_resp.text)
        except Exception:
            pass
        return "Cannot enable: failed to read current state"


def disable(ip: str | None = None):
    err = _require_ip(ip)
    if err:
        return err

    api_url = _api_url(ip)

    # 1) Read current admin state
    state_resp = requests.get(api_url, auth=basicauth, headers=headers, verify=False)

    if state_resp.status_code == 404:
        print("STATUS NOT FOUND: 404")
        return "Cannot disable: Interface loopback 66070101 not found"

    if 200 <= state_resp.status_code <= 299:
        data = {}
        try:
            data = state_resp.json().get("ietf-interfaces:interface", {})
        except Exception:
            pass
        currently_enabled = bool(data.get("enabled", False))

        # 2) If already disabled, report it
        if not currently_enabled:
            return "Cannot shutdown: Interface loopback 66070101"

        # 3) Otherwise, patch to disable
        yangConfig = {"ietf-interfaces:interface": {"enabled": False}}
        resp = requests.patch(
            api_url, data=json.dumps(yangConfig), auth=basicauth, headers=headers, verify=False
        )

        if 200 <= resp.status_code <= 299:
            print("STATUS OK: {}".format(resp.status_code))
            return "Interface loopback 66070101 is shutdowned successfully"
        else:
            print("Error. Status Code: {}".format(resp.status_code))
            try:
                print(resp.text)
            except Exception:
                pass
            return "Cannot shutdown: Interface loopback 66070101"
    else:
        print("Error. Status Code (GET): {}".format(state_resp.status_code))
        try:
            print(state_resp.text)
        except Exception:
            pass
        return "Cannot disable: failed to read current state"


def status(ip: str | None = None):
    err = _require_ip(ip)
    if err:
        return err

    api_url_status = _api_url(ip)

    resp = requests.get(api_url_status, auth=basicauth, headers=headers, verify=False)

    if 200 <= resp.status_code <= 299:
        print("STATUS OK: {}".format(resp.status_code))
        data = {}
        try:
            data = resp.json().get("ietf-interfaces:interface", {})
        except Exception:
            pass

        # admin-status from 'enabled' (True -> up, False -> down)
        admin_status = "up" if data.get("enabled") else "down"
        oper_status = data.get("oper-status", "unknown")

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

    elif resp.status_code == 404:
        print("STATUS NOT FOUND: {}".format(resp.status_code))
        return "No Interface loopback 66070101"
    else:
        print("Error. Status Code: {}".format(resp.status_code))
        try:
            print(resp.text)
        except Exception:
            pass
        return "Cannot read status: Interface loopback 66070101"