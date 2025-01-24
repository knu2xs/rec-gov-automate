from configparser import ConfigParser
from pathlib import Path

__all__ = ["get_recgov_credentials"]


def get_recgov_credentials(secrets_path: Path) -> tuple[str, str]:
    """Get the username and password as a tuple for Recreation.gov from the ``secrets.ini`` config file."""
    # ensure the secrets.ini file exists
    if not secrets_path.exists():
        raise FileNotFoundError(
            f"Cannot locate secrets.ini config file at {secrets_path}"
        )

    # read in the secrets file
    with open(secrets_path, "r") as secrets_f:
        secrets_config = ConfigParser()
        secrets_config.read_file(secrets_f)

        # retrieve the username and password
        recgov_username = secrets_config.get("DEFAULT", "RECGOV_USERNAME")
        recgov_password = secrets_config.get("DEFAULT", "RECGOV_PASSWORD")

        if recgov_username is None and recgov_password is None:
            raise ValueError(
                f"Cannot retrieve username and password from {secrets_path}"
            )
        elif recgov_password is None:
            raise ValueError(f"Cannot retrieve password from {secrets_path}.")
        elif recgov_password is None:
            raise ValueError(f"Cannot retrieve username from {secrets_path}.")

    return recgov_username, recgov_password
