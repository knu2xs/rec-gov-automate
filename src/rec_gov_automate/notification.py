import logging
import smtplib
from email.mime.text import MIMEText
from typing import Union


def send_message(
    sender: str, password: str, recipients: Union[str, list[str]], body: str
):
    """
    Send simple text messages to email, and phone numbers when using the correct address for the carrier.

    Args:
        sender: Gmail address of the sender.
        password: Application password of the sender.
        recipients: List of email addresses to send to.
        body: Simple text to send.

    Verizon: ``3334445555@vtext.com``
    """
    # Create a MIMEText object with the body of the email.
    msg = MIMEText(body)

    # Set the sender's email.
    msg["From"] = sender

    # Join the list of recipients into a single string separated by commas.
    msg["To"] = ", ".join(recipients)

    # Connect to Gmail's SMTP server using SSL.
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:

        # Login to the SMTP server using the sender's credentials.
        smtp_server.login(sender, password)

        # Send the email. The sendmail function requires the sender's email, the list of recipients, and the email message as a string.
        smtp_server.sendmail(sender, recipients, msg.as_string())

    # Print a message to console after successfully sending the email.
    logging.debug(f"Message with text {body} sent to {msg['To']}.")

    return
