import subprocess

def showrun():
    # read https://www.datacamp.com/tutorial/python-subprocess to learn more about subprocess
    command = ['ansible-playbook', '-i', 'hosts', 'playbook.yml']
    result = subprocess.run(command, capture_output=True, text=True)
    result = result.stdout
    if 'ok=3' in result:
        return 'show_run_66070101_R1-Exam.txt'
    else:
        return 'Error: Ansible'