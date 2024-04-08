import boto3

# Create an EC2 resource
ec2 = boto3.resource('ec2')

USER_DATA_SCRIPT = """#!/bin/bash

# Update and Upgrade Ubuntu
sudo apt-get update
sudo apt-get -y upgrade

# Install XFCE Desktop, VNC Server, and Google Chrome
sudo apt-get install -y xfce4 xfce4-goodies tightvncserver
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb

# Initial VNC server start to configure it, then kill it to configure xstartup
vncserver :1
vncserver -kill :1

# Configure VNC Server to start XFCE and open Google Chrome
mkdir -p ~/.vnc
echo '#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
# Wait for the desktop to load, then open Google Chrome
(sleep 10; google-chrome --no-sandbox --disable-gpu &' > ~/.vnc/xstartup
chmod +x ~/.vnc/xstartup

# Install noVNC
cd ~
git clone https://github.com/novnc/noVNC.git

# Generate a self-signed SSL certificate for noVNC
cd noVNC
openssl req -new -x509 -days 365 -nodes -out self.pem -keyout self.pem -batch

# Create a startup script for VNC and noVNC, adjusting noVNC to use port 6080
IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "Connect with https://$IP:6080/vnc.html?host=$IP&port=6080"
vncserver :1
./utils/novnc_proxy --vnc localhost:5901 --listen 6080 --cert self.pem
"""

# # delete all instances
# for instance in ec2.instances.all():
#     instance.terminate()
#
# # Delete all security groups
# for sg in ec2.security_groups.all():
#     if sg.group_name != 'default':
#         sg.delete()


def get_latest_ubuntu_ami():
    client = boto3.client('ec2')
    images = client.describe_images(
        Filters=[
            {'Name': 'name', 'Values': ['ubuntu/images/hvm-ssd/ubuntu-*-amd64-server-*']},
            {'Name': 'architecture', 'Values': ['x86_64']},
            {'Name': 'root-device-type', 'Values': ['ebs']},
            {'Name': 'virtualization-type', 'Values': ['hvm']}
        ],
        Owners=['099720109477']  # Ubuntu's owner ID
    )
    images = sorted(images['Images'], key=lambda x: x['CreationDate'], reverse=True)
    return images[0]['ImageId'] if images else None

def create_security_group():
    # Check if VNC_SSH security group already exists
    for sg in ec2.security_groups.all():
        if sg.group_name == 'VNC_SSH':
            return sg.group_id
    sg = ec2.create_security_group(
        GroupName='VNC_SSH',
        Description='Security group for VNC and SSH access'
    )
    sg.authorize_ingress(
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 5900,
             'ToPort': 5901,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 6080,
             'ToPort': 6080,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ]
    )
    return sg.group_id



def create_instance(instance_name):
    sg_id = create_security_group()  # Create a security group for VNC
    ami_id = get_latest_ubuntu_ami()
    if ami_id:
        instances = ec2.create_instances(
            ImageId=ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.small',
            # userData=USER_DATA_SCRIPT,
            SecurityGroupIds=[sg_id],  # Add security group
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': instance_name
                        }
                    ]
                }
            ]
        )
        print(f"Instance {instance_name} created with ID: {instances[0].id}")
    else:
        print("Could not find a suitable AMI")


if __name__ == '__main__':
    instance_name = "test"  # Replace with your desired instance name
    create_instance(instance_name)
