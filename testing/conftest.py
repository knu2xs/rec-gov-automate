from pathlib import Path

from pytest import fixture

from rec_gov_automate.utils import get_recgov_credentials


@fixture(scope="session")
def secrets_path() -> Path:
    dir_prj = Path(__file__).parent.parent
    secrets_pth = dir_prj / "config" / "secrets.ini"
    return secrets_pth


@fixture(scope="session")
def recgov_credentials(secrets_path) -> tuple:
    credentials = get_recgov_credentials(secrets_path)
    return credentials
