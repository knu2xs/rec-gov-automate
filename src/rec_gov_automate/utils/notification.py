import json
import logging
import os
import re
import smtplib
from email.mime.text import MIMEText
from typing import Optional, Union

import requests
from azure.communication.sms import SmsClient, SmsSendResult

from .credentials import (
    get_azure_sms_connection_string,
    get_azure_sms_number,
    get_gmail_credentials,
    get_sms_number,
    get_pushover_credentials,
)

__all__ = ["send_email", "send_gmail", "send_sms", "send_pushover"]


def send_email(
    smtp_host: str,
    sender: str,
    password: str,
    recipients: Union[str, list[str]],
    body: str,
    subject: Optional[str] = None,
    smtp_port: Optional[int] = 465,
) -> None:
    """
    Send simple text messages to email, and phone numbers when using the correct address for the carrier.

    Args:
        smtp_host: SMTP host, such as ``smtp.gmail.com``.
        sender: Gmail address of the sender.
        password: Application password of the sender.
        recipients: List of email addresses to send to.
        body: Simple text to send.
        subject: Subject of the email.
        smtp_port: SMTP port for the SMTP server, defaults to 465.

    Text Message Hosts:

        * Verizon Text: ``3334445555@vtext.com``
    """
    # if recipients is single string, convert to list
    if isinstance(recipients, str):
        recipients = [recipients]

    # Create a MIMEText object with the body of the email.
    msg = MIMEText(body)

    # Set the sender's email.
    msg["From"] = sender

    # if a subject is provided, add it
    if subject is not None:
        msg["Subject"] = subject

    # Join the list of recipients into a single string separated by commas.
    msg["To"] = ", ".join(recipients)

    # Connect to Gmail's SMTP server using SSL.
    with smtplib.SMTP_SSL(smtp_host, smtp_port) as smtp_server:

        # Login to the SMTP server using the sender's credentials.
        smtp_server.login(sender, password)

        # Send the email. The sendmail function requires the sender's email, the list of recipients, and the email
        # message as a string.
        smtp_server.sendmail(sender, recipients, msg.as_string())

    # Print a message to console after successfully sending the email.
    logging.debug(f"Message with text {body} sent to {msg['To']}.")

    return


def send_gmail(
    recipients: Union[str, list[str]],
    body: str,
    subject: Optional[str] = None,
    sender: Optional[str] = None,
    password: Optional[str] = None,
) -> None:
    """
    Send simple text messages to email and phone numbers when using the correct address using GMail.
    Args:
        recipients: List of email addresses to send to.
        body: Simple text to send.
        subject: Subject of the email.
        sender: Gmail address of the sender.
        password: Application password of the sender.
    """
    if sender is None or password is None:
        sender, password = get_gmail_credentials()

    send_email(
        smtp_host="smtp.gmail.com",
        sender=sender,
        subject=subject,
        password=password,
        recipients=recipients,
        body=body,
        smtp_port=465,
    )


def send_sms(
    body: str, recipients: Optional[Union[str, list[str]]] = None
) -> list[SmsSendResult]:
    """
    Send simple text messages to phone numbers.
    Args:
        body: Text message to send.
        recipients: Single phone number or list of phone numbers to send to.
    """
    # if recepients not provided, read from environment variables
    if recipients is None:
        recipients = get_sms_number()

    # format the phone numbers to send to
    if isinstance(recipients, str):
        recipients = validate_phone_number(recipients)
    else:
        recipients = [validate_phone_number(ph) for ph in recipients]

    # load the SMS connection string from environment variables
    azure_sms_connection_string = get_azure_sms_connection_string()
    azure_sms_number = get_azure_sms_number()

    # format the azure phone number, the number used for sending
    azure_sms_number = validate_phone_number(azure_sms_number)

    # create the client to use for sending messages
    sms_client: SmsClient = SmsClient.from_connection_string(
        azure_sms_connection_string
    )

    # use the client to send the message
    sms_responses = sms_client.send(from_=azure_sms_number, to=recipients, message=body)

    # ensure all messages were successful, and notify if not
    for resp in sms_responses:
        if not resp.successful:
            logging.error(
                f"""Encountered error while sending SMS message to "{resp.to}": {resp.error_message}"""
            )
        else:
            logging.debug(f"""SMS Message successfully sent to "{resp.to}".""")

    return sms_responses


def validate_phone_number(phone_number: str) -> str:
    """Ensure and clean up phone number string for sending SMS messages, ``+133344455555``."""
    # pluck out all the numbers
    matches = re.findall(r"\d+", phone_number)

    # combine all the numbers
    if len(matches):
        phone_number = "".join(matches)

    # if the phone number is not 10 to 12 digits, cannot use
    if (len(phone_number) < 10) or (len(phone_number) > 12):
        raise ValueError(
            f"""The phone number provided "{phone_number}", is not between 10 and 12 digits."""
        )

    # if does not include the 1 US country code, add it
    elif len(phone_number) == 10:
        phone_number = "1" + phone_number

    # add the plus prefix
    phone_number = "+" + phone_number

    return phone_number


def send_pushover(
    message: str, user_key: Optional[str] = None, api_token: Optional[str] = None
) -> requests.Response:
    """Send notifications using Pushover application."""
    if api_token is None or user_key is None:
        user_key, api_token = get_pushover_credentials()
        logging.debug("Using Pushover credentials from environment variables.")
    else:
        logging.debug("Using Pushover credentials from input parameters.")

    url = "https://api.pushover.net/1/messages.json"
    payload = {"token": api_token, "user": user_key, "message": message}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    res = requests.post(url, headers=headers, data=payload)

    if res.status_code != requests.codes.ok:
        logging.error(
            f"""Pushover API encountered an error, returned status code {res.status_code}: {res.json().get("error")}"""
        )
    else:
        logging.debug("Message successfully sent via Pushover.")

    return res
