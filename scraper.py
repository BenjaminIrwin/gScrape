import json
import os
import time
from datetime import datetime

import boto3
import requests

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

print('Setting up SQS and SNS services...')


def get_public_ip():
    """ Retrieve the public IP address of the current server. """
    response = requests.get('https://api.ipify.org')
    return response.text


public_ip_address = get_public_ip()

# Set up AWS services
sns_client = boto3.client('sns', region_name='eu-west-2')
sqs_client = boto3.client('sqs', region_name='eu-west-2')
sqs_status_url = 'https://sqs.eu-west-2.amazonaws.com/637423486927/StatusQueue.fifo'

sqs_target_url = os.environ.get('SQS_TARGET_URL')


def get_public_ip():
    """ Retrieve the public IP address of the current server. """
    response = requests.get('https://api.ipify.org')
    return response.text


def listen_for_sqs_change(wait_time = 1):
    response = sqs_client.receive_message(
        QueueUrl=sqs_target_url,
        AttributeNames=['All'],
        MaxNumberOfMessages=10,
        WaitTimeSeconds=wait_time  # Adjust this as needed
    )

    messages = response.get('Messages', [])
    if messages:
        # Get the latest message
        message = messages[-1]
        message_body = json.loads(message['Body'])
        url = message_body.get('Message')
        start_time_str = message_body.get('subject')
        if start_time_str is not 'New URL':
            # Get the current date
            today_date = datetime.now().date()

            # Parse the time
            parsed_time = datetime.strptime('07:56', '%H:%M').time()

            # Combine current date with parsed time
            start_time = datetime.combine(today_date, parsed_time)
        else:
            start_time = None
        # Delete the message
        sqs_client.delete_message(
            QueueUrl=sqs_target_url,
            ReceiptHandle=message['ReceiptHandle']
        )

        return start_time, url


    return None, None




def publish_to_sqs(ip_address, status):
    """ Publish a message to SQS with the status of the page load. """
    message_body = {
        "status": status,
        "instance_ip": ip_address
    }
    sqs_client.send_message(QueueUrl=sqs_status_url,
                            MessageBody=str(message_body),
                            MessageGroupId=str(datetime.now().timestamp()))


print('Setting up chromedriver...')

publish_to_sqs(public_ip_address, 'startup')

# Main flow
driver = uc.Chrome()
url = None

while not url:
    start_time, url = listen_for_sqs_change()

    if start_time:
        # Wait until start_time is reached, given that start_time is GMT
        while start_time.time() > datetime.utcnow().time():
            time.sleep(1)

print('Navigating to:', url)


publish_to_sqs(public_ip_address, 'loading')


driver.get(url)

loaded = False

def holding_page(text):
    return 'until there is a free space on the booking site' in text


# Start a loop that will refresh the page every 2.5 seconds
while True:
    start_time, new_url = listen_for_sqs_change()
    if new_url:
        print('New URL detected:', new_url)
        driver.get(new_url)
        url = new_url
    try:
        print('Refreshing...')
        # Check if the page has loaded by looking for any text or a specific element
        if (driver.find_element(By.TAG_NAME, 'body').text.strip() != '' and not holding_page(driver.find_element(By.TAG_NAME, 'body').text.strip())):
            print("Page has loaded content, exiting the loop.")
            publish_to_sqs(public_ip_address, 'success')
            # Wait indefinitely to keep the browser open
            restart = False
            while not restart:
                start_time, new_url = listen_for_sqs_change()
                if new_url:
                    print('New URL detected:', new_url)
                    driver.get(new_url)
                    publish_to_sqs(public_ip_address, 'loading')
                    url = new_url
                    restart = True
            continue
        # Refresh the page
        driver.refresh()
        # Wait for 2.5 seconds
        time.sleep(2.5)
    except Exception as e:
        publish_to_sqs(public_ip_address, 'failure')


driver.quit()
