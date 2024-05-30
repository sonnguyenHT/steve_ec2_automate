import boto3
import os
import re
import paramiko
from botocore.exceptions import ClientError

# AWS configuration
AWS_REGION = 'us-west-2'
KEY_NAME = 'work-steve'
LAUNCH_TEMPLATE_ID = 'lt-0d41438011c9d7cc8'

# SSH configuration
SSH_CONFIG_PATH = os.path.expanduser('~/.ssh/config')
HOST_ALIAS = 'ec2'
KEY_FILE_PATH = "/home/work-steve.pem"

def describe_security_groups(client):
    try:
        security_groups = client.describe_security_groups()
        # print("Security groups described successfully:")
        # for sg in security_groups['SecurityGroups']:
        #     #print(f"- {sg['GroupName']} (ID: {sg['GroupId']})")
    except ClientError as e:
        print(f"Failed to describe security groups: {e}")

def create_ec2_instance(client):
    try:
        response = client.run_instances(
            LaunchTemplate={
                'LaunchTemplateId': LAUNCH_TEMPLATE_ID
            },
            MinCount=1,
            MaxCount=1,
            KeyName=KEY_NAME
        )

        instance = response['Instances'][0]
        instance_id = instance['InstanceId']

        print('Waiting for instance to enter running state...')
        waiter = client.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])

        instance_info = client.describe_instances(InstanceIds=[instance_id])
        hostname = instance_info['Reservations'][0]['Instances'][0]['PublicDnsName']

        print(f"Instance created with hostname: {hostname}")
        return hostname

    except ClientError as e:
        print(f"An error occurred: {e}")
        return None

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
        
def main():
    client = boto3.client('ec2', region_name=AWS_REGION)

    # Describe security groups
    describe_security_groups(client)

    # Create EC2 instance
    hostname = create_ec2_instance(client)
    if hostname:
        print(f'Instance created successfully with hostname: {hostname}')
        update_ssh_config(hostname)
        print(f'SSH config updated with hostname: {hostname}')
        connect_via_ssh(hostname)
    else:
        print("Failed to create EC2 instance.")

if __name__ == '__main__':
    main()
