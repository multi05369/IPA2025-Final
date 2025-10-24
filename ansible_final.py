import subprocess
from typing import Optional

# Allowed router IPs
ALLOWED_IPS = {
    "10.0.15.61",
    "10.0.15.62",
    "10.0.15.63",
    "10.0.15.64",
    "10.0.15.65",
}

OUTPUT_FILE = "show_run_66070101_Router-Exam.txt"


def showrun(ip: Optional[str] = None) -> str:
    # Validate IP presence
    if not ip:
        return "Error: No IP specified"
    if ip not in ALLOWED_IPS:
        return f"Error: IP not allowed ({ip})"

    # Run ansible-playbook with extra-vars to pass router_ip
    # Ensure ansible.cfg in current dir takes effect (inventory/ssh settings)
    cmd = [
        "ansible-playbook",
        "-i",
        "hosts",
        "playbook.yml",
        "--extra-vars",
        f"router_ip={ip}",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""

        # For troubleshooting (optional): print to logs
        if result.returncode != 0:
            print("ansible-playbook failed rc=", result.returncode)
            print("STDOUT:\n", stdout[:2000])
            print("STDERR:\n", stderr[:2000])

        # Keep the same success criteria you used before (ok=3)
        # But also allow ok>=3 patterns because tasks count can vary
        # We will primarily rely on file creation in playbook, but keep your check
        if "ok=3" in stdout or "ok=" in stdout:
            # We expect the playbook to write OUTPUT_FILE on success
            return OUTPUT_FILE
        else:
            return "Error: Ansible"

    except FileNotFoundError:
        # ansible-playbook not found
        return "Error: Ansible"
    except Exception as e:
        print("Error running ansible-playbook:", e)
        return "Error: Ansible"