import subprocess
from typing import Optional
import json

ALLOWED_IPS = {
    "10.0.15.61",
    "10.0.15.62",
    "10.0.15.63",
    "10.0.15.64",
    "10.0.15.65",
}

def showrun(ip: Optional[str] = None) -> str:
    if not ip:
        return "Error: No IP specified"
    if ip not in ALLOWED_IPS:
        return f"Error: IP not allowed ({ip})"

    cmd = [
        "ansible-playbook",
        "-i",
        "hosts",
        "playbook.yml",
        "--extra-vars",
        f"router_ip={ip}",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        stdout = result.stdout or ""
        stderr = result.stderr or ""

        if result.returncode != 0:
            print("ansible-playbook failed rc=", result.returncode)
            print("STDOUT:\n", stdout[:2000])
            print("STDERR:\n", stderr[:2000])

        if "ok=" in stdout:
            return "show_run_66070101_Router-Exam.txt"
        else:
            return "Error: Ansible"
    except Exception as e:
        print("Error running ansible-playbook:", e)
        return "Error: Ansible"


def motd_set(ip: Optional[str], message: Optional[str]) -> str:
    """
    Configure banner motd on the given router using Ansible playbook_motd.yml.
    Returns "Ok: success" or "Error: <reason>".
    """
    if not ip:
        return "Error: No IP specified"
    if ip not in ALLOWED_IPS:
        return f"Error: IP not allowed ({ip})"
    if not message or not message.strip():
        return "Error: No MOTD message specified"

    # Support "\n" in chat to make multi-line banners
    # Example input: "Authorized Access Only!\nManaged by 66070101"
    motd_text = message.replace("\\n", "\n")

    extra_vars = {
        "router_ip": ip,
        "router_user": "admin",  # override here if needed
        "router_pass": "cisco",  # override here if needed
        "delim": "%",
        "motd_message": motd_text,
    }

    cmd = [
        "ansible-playbook",
        "-i",
        "hosts",
        "playbook_motd.yml",
        "--extra-vars",
        json.dumps(extra_vars),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        stdout = result.stdout or ""

        if result.returncode != 0:
            return "Error: Ansible"

        # Consider success if Ansible ran without failures
        # and made changes or at least executed the task
        if "failed=0" in stdout:
            return "Ok: success"

        return "Error: Ansible"

    except FileNotFoundError:
        return "Error: Ansible (ansible-playbook not found)"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"
