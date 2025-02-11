import os
import importlib.util

__all__ = [
    "load_dotenv",
    "get_recgov_credentials",
    "get_azure_sms_connection_string",
    "get_gmail_credentials",
    "get_notification_credentials",
    "get_pushover_credentials",
]


def load_dotenv():
    """Helper function to load the .env file if using dotenv to test locally."""
    if importlib.util.find_spec("dotenv"):
        from dotenv import load_dotenv, find_dotenv

        load_dotenv(find_dotenv())


def get_recgov_credentials():
    """Try to retrieve the recgov credentials from environment variables."""
    # load local dotenv if present
    load_dotenv()

    # load the variables
    user = os.environ.get("RECGOV_USERNAME")
    pswd = os.environ.get("RECGOV_PASSWORD")

    if user is None or pswd is None:
        raise EnvironmentError(
            "Cannot load recgov credentials from environment variables."
        )

    return user, pswd


def get_azure_sms_connection_string():
    """Try to retrieve the Azure SMS connection string from environment variables."""
    load_dotenv()

    azure_sms_connection_string: str = os.environ.get("AZURE_SMS_CONNECTION_STRING")

    if azure_sms_connection_string is None:
        raise EnvironmentError(
            "Cannot load Azure SMS connection string from environment variables."
        )

    return azure_sms_connection_string


def get_azure_sms_number():
    """Try to retrieve the Azure SMS number from environment variables."""
    load_dotenv()

    azure_sms_number: str = os.environ.get("AZURE_SMS_NUMBER")

    if azure_sms_number is None:
        raise EnvironmentError(
            "Cannot load Azure SMS number from environment variables."
        )

    return azure_sms_number


def get_gmail_credentials():
    """Try to retrieve the gmail credentials from environment variables."""
    load_dotenv()

    user = os.environ.get("GMAIL_USERNAME")
    pswd = os.environ.get("GMAIL_PASSWORD")

    if user is None or pswd is None:
        raise EnvironmentError(
            "Cannot load GMail credentials from environment variables."
        )

    return user, pswd


def get_sms_number():
    """Try to retrieve the SMS number from environment variables."""
    load_dotenv()

    sms_number: str = os.environ.get("SMS_NUMBER")

    if sms_number is None:
        raise EnvironmentError("Cannot load SMS number from environment variables.")

    return sms_number


def get_pushover_credentials():
    """Try to retrieve the pushover credentials from environment variables."""
    load_dotenv()

    user_key: str = os.environ.get("PUSHOVER_USER_KEY")
    app_key: str = os.environ.get("PUSHOVER_APP_TOKEN")

    if user_key is None or app_key is None:
        raise EnvironmentError(
            "Cannot load pushover credentials from environment variables."
        )

    return user_key, app_key
