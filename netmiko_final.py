from netmiko import ConnectHandler
from pprint import pprint

device_ip = "10.0.15.61"
username = "admin"
password = "cisco"

device_params = {
    "device_type": "cisco_ios",
    "ip": device_ip,
    "username": username,
    "password": password,
}


def gigabit_status():
    ans = ""
    with ConnectHandler(**device_params) as ssh:
        up = 0
        down = 0
        admin_down = 0
        result = ssh.send_command("show ip interface brief", use_textfsm=True)
        phase = []
        for status in result:
            iface = status.get("interface", "")
            if status["interface"].startswith("GigabitEthernet"):
                    if status["status"] == "up":
                        up += 1
                        norm = "up"
                    elif status["status"] == "down":
                        down += 1
                        norm = "down"
                    elif status["status"] == "administratively down":
                        admin_down += 1
                        norm = "administratively down"
                    phase.append(f"{iface} {norm}")
        ans = {
            "up": up,
            "down": down,
            "administratively_down": admin_down
        }
        detail = ", ".join(phase)
        summary = f"-> {up} up, {down} down, {admin_down} administratively down"
        ansText = f"{detail} {summary}"
        print(ansText)
        return ansText

