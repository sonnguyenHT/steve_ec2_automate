import boto3
import os
import re
import paramiko
from botocore.exceptions import ClientError

# AWS configuration
#AWS_REGION = 'us-west-2'
AWS_REGION = 'ap-southeast-1'
#KEY_NAME = 'work-steve'
KEY_NAME = 'sonnguyen'
LAUNCH_TEMPLATE_ID = 'lt-064789a5a9e169f89'

# SSH configuration
SSH_CONFIG_PATH = os.path.expanduser('~/.ssh/config')
HOST_ALIAS = 'ec2'
#KEY_FILE_PATH = "/home/work-steve.pem"
KEY_FILE_PATH = "/home/son/.ssh/id_rsa"

def update_ssh_config(hostname):
    config_entry = f"""
Host {HOST_ALIAS}
    HostName {hostname}
    IdentityFile "{KEY_FILE_PATH}"
    LocalForward 8188 localhost:8188
    User ubuntu
"""
    if os.path.exists(SSH_CONFIG_PATH):
        with open(SSH_CONFIG_PATH, 'r') as file:
            config = file.read()

        if f'Host {HOST_ALIAS}' in config:
            # Replace the existing HostName for the given alias
            new_config = re.sub(
                rf'Host {HOST_ALIAS}.*?HostName .*?\n',
                f'Host {HOST_ALIAS}\n    HostName {hostname}\n',
                config,
                flags=re.S
            )
        else:
            new_config = config + config_entry
    else:
        new_config = config_entry

    with open(SSH_CONFIG_PATH, 'w') as file:
        file.write(new_config)

def connect_via_ssh(hostname):
    key = paramiko.RSAKey.from_private_key_file(KEY_FILE_PATH)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print(f"Connecting to {hostname} via SSH...")
    try:
        client.connect(hostname, username='ubuntu', pkey=key)
        print("Connected successfully!")

        # Execute a test command
        stdin, stdout, stderr = client.exec_command('echo "Hello, World!"')
        print(stdout.read().decode())
        
        # Execute pwd command to print the working directory
        stdin, stdout, stderr = client.exec_command('pwd')
        print("Current working directory:")
        print(stdout.read().decode())
        
        # Run the shell script
        stdin, stdout, stderr = client.exec_command('bash scripts/run_comfyui.sh')
        print(stdout.read().decode())
        print(stderr.read().decode())

        client.close()
    except Exception as e:
        print(f"Failed to connect via SSH: {e}")
        
