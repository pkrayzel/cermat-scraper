import os
import time
import argparse
import random
import threading
from playwright.sync_api import sync_playwright
from answered import ANSWERED
from questions import CATEGORIES
from common import accept_cookies, click_prijimacky, detect_total_questions, select_category, select_subject, wait_for_subject_selection

# Path to store the updated answered questions in Python format
ANSWERED_PYTHON_FILE = "answered_now.py"

# --------------------------
# Helper Functions
# --------------------------

def get_manually_answered():
    """ Load manually confirmed answered questions from `questions.py`. """
    answered_dict = {}
    for entry in ANSWERED:
        category_name = entry["name"]
        answered_set = set()
        for r in entry["answered"]:
            if isinstance(r, range):
                answered_set.update(range(r.start, r.stop))  # Convert range to set of numbers
            else:
                answered_set.add(r)
        answered_dict[category_name] = answered_set
    return answered_dict

def get_unanswered_questions(category_name, total_questions, manually_answered):
    """ Get a list of unanswered questions for a category. """
    all_questions = set(range(1, total_questions + 1))
    answered_questions = manually_answered.get(category_name, set())
    return list(all_questions - answered_questions)

def find_category(name):
    """ Get category details from `CATEGORIES` list. """
    return next((item for item in CATEGORIES if item["name"] == name), None)

def format_answered(questions):
    """ Convert a set of numbers into a mix of `range()` and single numbers. """
    sorted_questions = sorted(questions)
    if not sorted_questions:
        return "[]"

    ranges = []
    current_range = [sorted_questions[0]]

    for num in sorted_questions[1:]:
        if num == current_range[-1] + 1:
            current_range.append(num)
        else:
            if len(current_range) > 1:
                ranges.append(f"range({current_range[0]}, {current_range[-1] + 1})")
            else:
                ranges.append(str(current_range[0]))
            current_range = [num]

    if len(current_range) > 1:
        ranges.append(f"range({current_range[0]}, {current_range[-1] + 1})")
    else:
        ranges.append(str(current_range[0]))

    return "[" + ", ".join(ranges) + "]"

def save_questions_python(updated_answered):
    """ Saves the answered questions into a Python script format (`questions_now.py`). """
    with open(ANSWERED_PYTHON_FILE, "w", encoding="utf-8") as f:

        f.write("\nANSWERED = [\n")
        
        # Writing the updated ANSWERED dictionary
        for category, questions in updated_answered.items():
            formatted_questions = format_answered(questions)
            f.write(f'    {{"name": "{category}", "answered": {formatted_questions}}},\n')

        f.write("]\n\n")

    print(f"✅ Saved updated answered questions to `{ANSWERED_PYTHON_FILE}`.")

# --------------------------
# Browser Session Per Category
# --------------------------
def start_category_session(category_name, subject, category_radio_id, num_questions, manually_answered, answered_now):
    """
    Starts a **separate browser instance** for a category.
    Each browser instance handles multiple tabs for the category, ensuring an independent session.
    """
    base_test_url = "https://tau.cermat.cz/test-kategorie.php?poradi_ulohy="

    def run_in_thread():
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, args=["--start-maximized"], ignore_default_args=["--enable-automation"])
            context = browser.new_context(no_viewport=True)  # Ensures full maximized window
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

            # Step 6: Detect total questions
            total_questions = detect_total_questions(page)

            # Get list of unanswered questions
            unanswered = get_unanswered_questions(category_name, total_questions, manually_answered)

            if len(unanswered) == 0:
                print(f"No unanswered questions left in {category_name}.")
                return None

            # Select random questions
            selected_questions = random.sample(unanswered, min(num_questions, len(unanswered)))
            print(f"Opening {len(selected_questions)} questions from {category_name}: {selected_questions}")

            # Open first question in current tab
            first_question_url = base_test_url + str(selected_questions[0])
            print(f"Opening first question in current tab: {first_question_url}")
            page.goto(first_question_url)
            page.wait_for_load_state("networkidle")

            # Open remaining questions in separate tabs
            for question in selected_questions[1:]:
                question_url = base_test_url + str(question)
                new_tab = context.new_page()
                print(f"Opening extra question in new tab: {question_url}")
                new_tab.goto(question_url)
                new_tab.wait_for_load_state("networkidle")

            print(f"✅ Session for category '{category_name}' is running in its own browser instance.")

            # **Merge and Save Answered Questions**
            if category_name in answered_now:
                answered_now[category_name].update(selected_questions)
            else:
                answered_now[category_name] = manually_answered.get(category_name, set()).union(selected_questions)

            # Save updated answered log in Python format
            save_questions_python(answered_now)

            # Prevent the browser from closing immediately
            page.wait_for_timeout(9999999)

    # Run each browser session in a new thread
    thread = threading.Thread(target=run_in_thread)
    thread.start()

# --------------------------
# Main Function
# --------------------------
def main(categories, num_questions_per_category):
    """
    Starts a **separate browser instance** for each category.
    Each instance runs an independent session and opens multiple tabs for questions.
    """
    manually_answered = get_manually_answered()  # Load manually confirmed answered questions from `questions.py`
    answered_now = manually_answered.copy()  # Copy existing answers and update them

    for category_name in categories:
        category_info = find_category(category_name)
        if not category_info:
            print(f"Skipping unknown category: {category_name}")
            continue

        subject = category_info["subject"]
        category_radio_id = category_info["category"]

        # Start a separate browser instance for this category
        start_category_session(category_name, subject, category_radio_id, num_questions_per_category, manually_answered, answered_now)

# --------------------------
# Command Line Arguments
# --------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Open multiple random unanswered questions in separate browsers, ensuring independent sessions."
    )
    parser.add_argument("--categories", nargs="+", required=True, help="List of category names.")
    parser.add_argument("--num_questions", type=int, default=5, help="Number of questions per category.")
    args = parser.parse_args()

    main(args.categories, args.num_questions)
