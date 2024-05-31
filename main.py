import streamlit as st
import boto3
from botocore.exceptions import ClientError
import ec2_template_script
import os
# AWS configuration
#AWS_REGION = 'us-west-2'
AWS_REGION = 'ap-southeast-1'
# Initialize a session using your profile
# AWS_REGION = 'ap-southeast-1'
# #KEY_NAME = 'work-steve'
# KEY_NAME = 'sonnguyen'
# LAUNCH_TEMPLATE_ID = 'lt-064789a5a9e169f89'

# # SSH configuration
# SSH_CONFIG_PATH = os.path.expanduser('~/.ssh/config')
# HOST_ALIAS = 'ec2'
# #KEY_FILE_PATH = "/home/work-steve.pem"
# KEY_FILE_PATH = "/home/son/.ssh/id_rsa"





session = boto3.Session(region_name=AWS_REGION)
ec2_client = session.client('ec2')
ec2_resource = boto3.resource('ec2')

def get_launch_templates():
    templates = []
    try:
        # Describe all launch templates
        response = ec2_client.describe_launch_templates()
        
        # Iterate through the launch templates and store their details
        for template in response['LaunchTemplates']:
            templates.append({
                'LaunchTemplateId': template['LaunchTemplateId'],
                'LaunchTemplateName': template['LaunchTemplateName'],
                'CreatedBy': template['CreatedBy'],
                'DefaultVersionNumber': template['DefaultVersionNumber'],
                'LatestVersionNumber': template['LatestVersionNumber'],
                'CreateTime': template['CreateTime'],
            })
    except ClientError as e:
        st.error(f"Error: {e}")
    return templates

def run_instance(launch_template_id, version, name):
    try:
        response = ec2_client.run_instances(
            LaunchTemplate={
                'LaunchTemplateId': launch_template_id,
                'Version': str(version)
            },
            MaxCount=1,
            MinCount=1,
            TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': name
                },
            ]
        },
    ],
        )
        instance_id = response['Instances'][0]['InstanceId']
        st.session_state['instance_id'] = instance_id
        st.session_state['instance_state'] = 'running'
        st.success(f"Successfully launched EC2 instance with ID: {instance_id}")
    except ClientError as e:
        st.error(f"Error launching instance: {e}")

def stop_instance(instance_id):
    try:
        ec2_client.stop_instances(InstanceIds=[instance_id])
        st.session_state['instance_state'] = 'stopped'
        st.success(f"Successfully stopped EC2 instance with ID: {instance_id}")
    except ClientError as e:
        st.error(f"Error stopping instance: {e}")

def check_instance_state(name):
    state = False
    try:
        response = ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [name]
                }
            ]
        )
        if len(response['Reservations']) > 0:
            instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
            state = response['Reservations'][0]['Instances'][0]['State']['Name']
            st.session_state['instance_id'] = instance_id
            st.session_state['instance_state'] = state
    except ClientError as e:
        st.error(f"Error checking instance state: {e}")
    return state

def run_script(hostname):
    ec2_template_script.update_ssh_config(hostname)
    ec2_template_script.connect_via_ssh(hostname)
    st.write("Script is run success")
    return None
def get_instance_id(name):
    try:
        response = ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:Name',
                    'Values': [name]
                }
            ]
        )
        if len(response['Reservations']) > 0:
            instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
            return instance_id
    except ClientError as e:
        st.error(f"Error checking instance state: {e}")
    return None

def main():
    #init var
    instance_id = ""
    hostname = ""
    
    st.title("AWS EC2 Launch Templates")
    name = st.text_input("", placeholder="Type name to tag instance", key="name_input")
    st.button("Check Instance State", key="check_button")
    check = check_instance_state(name)
    st.write(f"Instance state: {check}, Instance ID: {get_instance_id(name)}")
    # get info of instance

    if check != False:
        instance_id = get_instance_id(name)
        instance_info = ec2_client.describe_instances(InstanceIds=[instance_id])
        hostname = instance_info['Reservations'][0]['Instances'][0]['PublicDnsName']
    st.write(f"Hostname: {hostname}")
    # run script after click button
    if st.button("Run Script", key="run_script_button"):
        if check == 'running':
            run_script(hostname)
            # chech init state of instance
            # ec2_client.describe_instance_status(
            #         Filters=[
            #             {
            #                 'Name': 'string',
            #                 'Values': [
            #                     name,
            #                 ]
            #             },
            #         ],
            # )
        else:
            st.write("Instance is not ready to run script")
    
    if check == 'running':
        print("Instance is running")
        instance_state = ec2_client.describe_instance_status(
            InstanceIds=[
                instance_id,
            ]
        )['InstanceStatuses'][0]['SystemStatus']['Details'][0]['Status']
        if instance_state == 'passed':
            st.write("Instance is ready to run script")
        else:
            st.write("Instance is not ready to run script")
        if st.button("Stop Instance", key="stop_button"):
            stop_instance(st.session_state['instance_id'])
    elif check == "stopped":
        #change instance from 'stopped' to 'running'
        if st.button("Start Instance", key="start_button"):
            ec2_client.start_instances(InstanceIds=[st.session_state['instance_id']])
            st.session_state['instance_state'] = 'running'
            st.success(f"Successfully started EC2 instance with ID: {st.session_state['instance_id']}")
        # run_script(hostname)
    elif check == "stopping":
        st.write("Instance is stopping")
    elif check == "pending":
        st.write("Instance is pending")
    else:
        st.write("Instance is not exist in your account")
        #st.write("Instance is not running or stopped")
        #create a new instance
        templates = get_launch_templates()
        template_names = [template['LaunchTemplateName'] for template in templates]
        selected_template_name = st.selectbox("Select a Launch Template", template_names)
        if selected_template_name:
            template = next(template for template in templates if template['LaunchTemplateName'] == selected_template_name)
            if st.button("Run Instance"):
                run_instance(template['LaunchTemplateId'], template['LatestVersionNumber'], name)
                # instance = ec2_client.Instance(instance_id)
                # instance_id = get_instance_id(name)
                # response = ec2_resource.create_tags(
                #     DryRun= False,
                #     Resources=[
                #         instance_id,
                #     ],
                #     Tags=[
                #         {
                #             'Key': 'Xin chao',
                #             'Value': name
                #         },
                #     ]
                # )
                # st.write(response)
                # add namef for the instance
            if check_instance_state(name) == 'running':
                st.write("Instance is running successfully")
            else:
                st.write("Instance is not running success")
        # run script
        # run_script(hostname)
        

        # hostname = instance_info['Reservations'][0]['Instances'][0]['PublicDnsName']
        # get hostname of the instance with name tag
        # hostname = ec2_template_script.create_ec2_instance(ec2_client, name)

        
    # if 'instance_state' not in st.session_state:
    #     st.session_state['instance_state'] = 'stopped'
    #     st.session_state['instance_id'] = None

    # templates = get_launch_templates()
    # template_names = [template['LaunchTemplateName'] for template in templates]
    
    # col1, col2 = st.columns([3, 1])

    # with col1:
    #     selected_template_name = st.selectbox("Select a Launch Template", template_names)
    
    # with col2:
    #     st.markdown("<br>", unsafe_allow_html=True)  # Add space before the button
    #     if selected_template_name:
    #         template = next(template for template in templates if template['LaunchTemplateName'] == selected_template_name)
    #         if st.session_state['instance_state'] == 'stopped':
    #             if st.button("Run Instance"):
    #                 run_instance(template['LaunchTemplateId'], template['LatestVersionNumber'])
    #         else:
    #             if st.button("Stop Instance"):
    #                 stop_instance(st.session_state['instance_id'])

if __name__ == "__main__":
    main()
