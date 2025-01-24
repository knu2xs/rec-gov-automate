from rec_gov_automate.reserve import remove_reservations


def test_remove_reservations(recgov_credentials):
    remove_reservations(*recgov_credentials, headless=False)
