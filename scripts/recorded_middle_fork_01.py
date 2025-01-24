import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.recreation.gov/permits/234623/registration/detailed-availability?date=2025-05-04")
    page.get_by_label("Middle Fork of the Salmon on May 7, 2025 - Available").click()
    page.get_by_role("button", name="Book Now").click()
    page.get_by_label("Email* (Required)").click()
    page.get_by_label("Email* (Required)").fill("knu2xs@gmail.com")
    page.get_by_label("Email* (Required)").press("Tab")
    page.get_by_label("Password* (Required)").click()
    page.get_by_label("Password* (Required)").fill("password")
    page.get_by_label("Password* (Required)").press("Tab")
    page.get_by_label("Password* (Required)").click(click_count=3)
    page.get_by_role("button", name="Show password value").click()
    page.get_by_label("Password* (Required)").click()
    page.get_by_label("Password* (Required)").press("ControlOrMeta+a")
    page.get_by_label("Password* (Required)").fill("xuqdom-rimqiz-4korNo")
    page.get_by_role("button", name="Log In", exact=True).click()
    page.goto("https://www.recreation.gov/permits/234623/registration/317bb3e8-797f-5466-8f1f-b9a55dd6be2c__234623")
    page.get_by_label("Cart - 1 item in cart.").click()
    page.goto("https://www.recreation.gov/permits/234623/registration/317bb3e8-797f-5466-8f1f-b9a55dd6be2c__234623")
    page.get_by_label("Type* (Required)").select_option("10")
    page.get_by_label("Add watercraft").click()
    page.get_by_label("Station Location* (Required)").select_option("2300")
    page.locator("label").filter(has_text="Yes, I have read and agree to").locator("span").first.click()
    page.get_by_label("Launch Location* (Required)").select_option("2100")
    page.get_by_label("Take-out Location* (Required)").select_option("2108")
    page.get_by_role("button", name="Exit Date (Required)").click()
    page.get_by_label("Wednesday, May 14, 2025 -").click()
    page.get_by_role("group", name="Exit Date (Required)").click()
    page.get_by_test_id("OrderDetailsSummary-cart-btn").click()
    page.goto("https://www.recreation.gov/cart")

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
