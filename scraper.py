import time
import boto3
import requests

import undetected_chromedriver as uc

print('Setting up SQS and SNS services...')

# Set up AWS services
sns_client = boto3.client('sns', region_name='eu-west-2')
sqs_client = boto3.client('sqs', region_name='eu-west-2')
sqs_queue_url = 'https://sqs.eu-west-2.amazonaws.com/637423486927/StatusQueue.fifo'

def get_public_ip():
    """ Retrieve the public IP address of the current server. """
    response = requests.get('https://api.ipify.org')
    return response.text

def handle_sns_message():
    # This is a placeholder. In practice, you would set this up to be triggered by an actual SNS message.
    # Here we assume you have the message containing the URL
    message = {'url': 'https://twitter.com/home'}
    return message['url']

def publish_to_sqs(url, ip_address):
    """ Publish a message to SQS with the status of the page load. """
    message_body = {
        "url": url,
        "status": "loaded",
        "link": f"https://{ip_address}:6080/vnc.html?host={ip_address}&port=6080"
    }
    sqs_client.send_message(QueueUrl=sqs_queue_url, MessageBody=str(message_body))

print('Setting up chromedriver...')

# Main flow
driver = uc.Chrome()
url = handle_sns_message()

print('Navigating to:', url)

driver.get(url)

loaded = False

# Start a loop that will refresh the page every 2.5 seconds
while not loaded:
    print('Refreshing...')
    # Check if the page has loaded by looking for any text or a specific element
    # Example: Check if there is any text in the body
    # if driver.find_element_by_tag_name('body').text.strip() != '':
    if driver.find_element('body').text.strip() != '':
        print("Page has loaded content, exiting the loop.")
        break
    # Refresh the page
    driver.refresh()
    # Wait for 2.5 seconds
    time.sleep(2.5)

if loaded:
    public_ip_address = get_public_ip()
    publish_to_sqs(url, public_ip_address)

    # Wait indefinitely to keep the browser open
    while True:
        time.sleep(100)

driver.quit()
