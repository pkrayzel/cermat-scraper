import os
import time
import argparse
from playwright.sync_api import sync_playwright
import psutil
from questions import CATEGORIES
from answered import ANSWERED
from common import accept_cookies, click_prijimacky, select_category, select_subject, wait_for_subject_selection

def main(subject, category_radio_id, start_question):
    base_test_url = "https://tau.cermat.cz/test-kategorie.php?poradi_ulohy="

    with sync_playwright() as p:
        # Launch the browser; set headless=True if you do not need the UI.
        browser = p.chromium.launch(headless=False)
        browser = p.chromium.launch(headless=False, args=["--start-maximized"], ignore_default_args=["--enable-automation"])
        context = browser.new_context(no_viewport=True)  # Ensures it uses the full maximized window

        page = context.new_page()

        # Step 1: Open Homepage and Accept Cookies
        page.goto("https://tau.cermat.cz/")
        accept_cookies(page)

        # Step 2: Click on the PŘIJÍMAČKY Button
        click_prijimacky(page)

        # Step 3: Wait for subject selection page to load
        wait_for_subject_selection(page)

        # Step 4: Select subject
        select_subject(page, subject)
        # Step 5: Select category and submit
        select_category(page, category_radio_id)
    
        question_url = base_test_url + str(start_question)

        print("Navigating to:", question_url)
        page.goto(question_url)
        page.wait_for_load_state("networkidle")

        page.wait_for_timeout(9999999)

def find_category(name):
    for item in CATEGORIES:
        if item["name"] == name:
            return item
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automate tau.cermat.cz test session and capture questions and results."
    )
    parser.add_argument("--name", type=str, help="Name of the category.")
    parser.add_argument("--question", type=int, default=1,
                        help="Question number to open (default: 1).")
    args = parser.parse_args()

    # Configuration
    item = find_category(args.name)
    category_radio_id = item["category"]
    subject = item["subject"]
    start_question = args.question

    main(subject, category_radio_id, start_question)
