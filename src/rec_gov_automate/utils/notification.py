import importlib.util
import logging
import os
import re
import smtplib
from email.mime.text import MIMEText
from typing import Optional, Union

import requests
from azure.communication.sms import SmsClient, SmsSendResult

__all__ = ["send_email", "send_gmail", "send_sms", "send_pushover"]

# if in development environment, load environment variables from .env file
if importlib.util.find_spec("dotenv"):
    from dotenv import load_dotenv, find_dotenv

    load_dotenv(find_dotenv())


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
    Send simple text messages to email.

    Args:
        smtp_host: SMTP host, such as ``smtp.gmail.com``.
        sender: Email address of the sender.
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
    Send simple text messages to email using GMail.

    .. note::
        If ``sender`` and ``password`` is not provided, this function will attempt to retrieve these values from
        the environment variables ``GMAIL_USERNAME`` and ``GMAIL_PASSWORD``. However, if these are not set in the
        environment variables and not explicitly provided as input arguments, this function will fail.

    Args:
        recipients: List of email addresses to send to.
        body: Simple text to send.
        subject: Subject of the email.
        sender: Gmail address of the sender. By default, retrieved from  the ``GMAIL_USERNAME`` environment variable.
        password: Application password of the sender. By default, retrieved the environment ``GMAIL_PASSWORD`` variable.
    """
    # if explicitly provided, use credentials passed in
    if sender is not None and password is not None:
        logging.debug("Sending GMail using sender and password provided as arguments.")

    # otherwise, try to retrieve credentials from environment variables
    else:
        sender = os.environ.get("GMAIL_USERNAME")
        password = os.environ.get("GMAIL_PASSWORD")

    # ensure some credentials are found
    if sender is None or password is None:
        logging.error(
            "Cannot retrieve GMail credentials from environment variables, and no GMail credentials were "
            "provided, so cannot send email."
        )

    # send email
    send_email(
        smtp_host="smtp.gmail.com",
        sender=sender,
        subject=subject,
        password=password,
        recipients=recipients,
        body=body,
        smtp_port=465,
    )

    return


def _validate_phone_number(phone_number: str) -> str:
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


def send_sms(
    body: str, recipients: Optional[Union[str, list[str]]] = None
) -> list[SmsSendResult]:
    """
    Send simple text messages to phone numbers using
    `Azure Communication Services' SMS SDK<https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/sms/send>`_.

    .. note::

        This requires
        `purchasing ($2/month for toll-free) a phone number<https://learn.microsoft.com/en-us/azure/communication-services/quickstarts/telephony/get-phone-number?tabs=windows&pivots=platform-azp>`_
        in
        `Azure Communication Services<https://azure.microsoft.com/en-us/products/communication-services>`_.

    Args:
        body: Text message to send.
        recipients: Single phone number or list of phone numbers to send to.
    """
    # if recepients not provided, try to read from environment variable
    if recipients is None:
        recipients = os.environ.get("SMS_NUMBER")

    # if still do not have a sms number, cannot send a message
    if recipients is None:
        raise ValueError("Please provide recipient phone number(s).")

    # format the phone numbers to send to
    if isinstance(recipients, str):
        recipients = _validate_phone_number(recipients)
    else:
        recipients = [_validate_phone_number(ph) for ph in recipients]

    # load the SMS connection string from environment variables
    azure_sms_connection_string = os.environ.get("AZURE_SMS_CONNECTION_STRING")

    if azure_sms_connection_string is None:
        raise EnvironmentError(
            "Cannot load Azure SMS connection string from environment variables."
        )

    # get the SMS number used for sending messages
    azure_sms_number = os.environ.get("AZURE_SMS_NUMBER")

    if azure_sms_number is None:
        raise EnvironmentError(
            "Cannot load Azure SMS number from environment variables."
        )

    # format the azure phone number, the number used for sending
    azure_sms_number = _validate_phone_number(azure_sms_number)

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
            logging.debug(f"""SMS Message "{body}" successfully sent to "{resp.to}".""")

    return sms_responses


def send_pushover(
    message: str,
    api_token: Optional[str] = None,
    user_key: Optional[str] = None,
) -> requests.Response:
    """
    Send notifications using `Pushover platform<https://pushover.net>`_.

    .. note::

        This *does* require installing the Pushover application on any devices you wish to receive notifications on,
        but *does not* require applying and getting approved for an SMS notification number. Hence, this frequently
        is an easier route to getting notifications on a mobile device.

    Args:
        message: Text message to send.
        api_token: Pushover API token. If not provided, will try to retrieve from ``PUSHOVER_API_KEY`` environment
          variable.
        user_key: Pushover user key. If not provided, will try to retrieve from ``PUSHOVER_USER_KEY`` environment
          variable.
    """
    # try to retrieve credentials from environment variables
    if user_key is None:
        user_key = os.environ.get("PUSHOVER_USER_KEY")
        logging.debug("Using Pushover user key from environment variables.")
    else:
        logging.debug("Using Pushover user key provided via input parameter.")

    if api_token is None:
        api_token = os.environ.get("PUSHOVER_API_KEY")
        logging.debug(f"Using Pushover API token from environment variables.")
    else:
        logging.debug(f"Using Pushover API token provided via input parameter.")

    # format parameters
    url = "https://api.pushover.net/1/messages.json"
    payload = {
        "token": api_token,
        "user": user_key,
        "message": message,
        "sound": "bugle",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    # make post call to submit message send request
    res = requests.post(url, headers=headers, data=payload)

    # handle response if an error is encountered
    if res.status_code != requests.codes.ok:
        logging.error(
            f"""Pushover API encountered an error, returned status code {res.status_code}: {res.json().get("error")}"""
        )
    else:
        logging.debug("Message successfully sent via Pushover.")

    # provide the response back, which can be handled if necessary
    return res
