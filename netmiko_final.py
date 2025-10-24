from typing import Optional, List
from netmiko import ConnectHandler

# Allowed router IPs
ALLOWED_IPS = {
    "10.0.15.61",
    "10.0.15.62",
    "10.0.15.63",
    "10.0.15.64",
    "10.0.15.65",
}

USERNAME = "admin"
PASSWORD = "cisco"


def _require_ip(ip: Optional[str]):
    if not ip:
        return "Error: No IP specified"
    if ip not in ALLOWED_IPS:
        return f"Error: IP not allowed ({ip})"
    return None


def _device_params(ip: str):
    return {
        "device_type": "cisco_ios",
        "ip": ip,
        "username": USERNAME,
        "password": PASSWORD,
        "fast_cli": False,
    }


def gigabit_status(ip: Optional[str] = None) -> str:
    """
    Returns a single-line summary of GigabitEthernet interfaces:
    "<Gi0/0 up, Gi0/1 down, ...> -> X up, Y down, Z administratively down"
    """
    err = _require_ip(ip)
    if err:
        return err

    params = _device_params(ip)

    try:
        with ConnectHandler(**params) as ssh:
            ssh.send_command("terminal length 0", expect_string=r"#", strip_prompt=True)

            up = 0
            down = 0
            admin_down = 0

            result = ssh.send_command("show ip interface brief", use_textfsm=True)

            # If TextFSM returned structured data (list of dicts)
            if isinstance(result, list) and result and isinstance(result[0], dict):
                details: List[str] = []
                for entry in result:
                    iface = entry.get("intf", "") or entry.get("interface", "")
                    if not iface or not iface.startswith("GigabitEthernet"):
                        continue
                    # Netmiko templates typically expose 'status' and 'proto'
                    status_val = (entry.get("status") or "").strip().lower()
                    if status_val == "up":
                        up += 1
                        norm = "up"
                    elif status_val == "down":
                        down += 1
                        norm = "down"
                    elif status_val == "administratively down":
                        admin_down += 1
                        norm = "administratively down"
                    else:
                        # unknown -> count as down
                        down += 1
                        norm = "down"
                    details.append(f"{iface} {norm}")

                detail = ", ".join(details)
                summary = f"-> {up} up, {down} down, {admin_down} administratively down"
                return f"{detail} {summary}".strip()

            # Fallback: raw text parsing
            raw = result if isinstance(result, str) else ssh.send_command(
                "show ip interface brief"
            )
            details: List[str] = []
            for line in raw.splitlines():
                parts = line.split()
                if not parts:
                    continue
                iface = parts[0]
                if not iface.startswith("GigabitEthernet"):
                    continue

                # Determine status from the line preserving "administratively down"
                status_str = ""
                if "administratively down" in line:
                    status_str = "administratively down"
                else:
                    # Try second-to-last token for "Status"
                    if len(parts) >= 2:
                        status_str = parts[-2].lower()
                        if status_str not in ("up", "down"):
                            status_str = parts[-1].lower()

                if status_str == "up":
                    up += 1
                    norm = "up"
                elif status_str == "administratively down":
                    admin_down += 1
                    norm = "administratively down"
                else:
                    down += 1
                    norm = "down"

                details.append(f"{iface} {norm}")

            detail = ", ".join(details)
            summary = f"-> {up} up, {down} down, {admin_down} administratively down"
            return f"{detail} {summary}".strip()

    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


def motd_get(ip: Optional[str] = None) -> str:
    """
    Return the MOTD banner text or "Error: No MOTD Configured".
    Uses 'show banner motd' which outputs only the banner text.
    """
    err = _require_ip(ip)
    if err:
        return err

    try:
        with ConnectHandler(**_device_params(ip)) as ssh:
            ssh.send_command("terminal length 0", expect_string=r"#", strip_prompt=True)
            output = ssh.send_command(
                "show banner motd", strip_prompt=True, strip_command=True
            )
            text = (output or "").strip()
            if not text or "not configured" in text.lower():
                return "Error: No MOTD Configured"
            return text
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"
