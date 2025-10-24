from netmiko import ConnectHandler
from typing import Optional

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
    }


def gigabit_status(ip: Optional[str] = None) -> str:
    """
    Returns a single-line summary of GigabitEthernet interfaces:
    "<Gi0/0 up, Gi0/1 down, ...> -> X up, Y down, Z administratively down"
    Errors return a user-friendly string.
    """
    err = _require_ip(ip)
    if err:
        return err

    params = _device_params(ip)

    try:
        with ConnectHandler(**params) as ssh:
            up = 0
            down = 0
            admin_down = 0
            result = ssh.send_command("show ip interface brief", use_textfsm=True)

            # TextFSM may return None if template not found; fallback to raw parsing
            if result is None or isinstance(result, str):
                raw = result if isinstance(result, str) else ssh.send_command(
                    "show ip interface brief"
                )
                detail_list = []
                for line in raw.splitlines():
                    # Typical columns: Interface  IP-Address  OK?  Method  Status  Protocol
                    # We only care about Interface (GigabitEthernet*) and Status
                    parts = line.split()
                    if not parts:
                        continue
                    iface = parts[0]
                    if not iface.startswith("GigabitEthernet"):
                        continue
                    # Status may be "administratively down" (two tokens). Try to detect.
                    status_str = ""
                    if "administratively down" in line:
                        status_str = "administratively down"
                    else:
                        # Try last two tokens for status/protocol pairs
                        if len(parts) >= 2:
                            # Commonly, Status at -2, Protocol at -1
                            status_str = parts[-2].lower()
                            if status_str not in ("up", "down"):
                                # fallback: try last token
                                status_str = parts[-1].lower()
                    norm = "down"
                    if status_str == "up":
                        norm = "up"
                        up += 1
                    elif status_str == "down":
                        norm = "down"
                        down += 1
                    elif status_str == "administratively down":
                        norm = "administratively down"
                        admin_down += 1
                    else:
                        # Unknown status -> count as down for safety
                        down += 1
                    detail_list.append(f"{iface} {norm}")

                detail = ", ".join(detail_list)
                summary = f"-> {up} up, {down} down, {admin_down} administratively down"
                return f"{detail} {summary}".strip()

            # If TextFSM returned structured data (list of dicts)
            phase = []
            for entry in result:
                iface = entry.get("interface", "")
                if not iface.startswith("GigabitEthernet"):
                    continue
                status_val = entry.get("status", "").lower()
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
                    # Unknown -> treat as down
                    down += 1
                    norm = "down"
                phase.append(f"{iface} {norm}")

            detail = ", ".join(phase)
            summary = f"-> {up} up, {down} down, {admin_down} administratively down"
            return f"{detail} {summary}".strip()

    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"