import os
import time
import argparse
from playwright.sync_api import sync_playwright

def accept_cookies(page):
    try:
        page.wait_for_selector("body", timeout=10000)
        time.sleep(2)
        page.click("xpath=//button[contains(text(), 'Přijmout všechny soubory cookie')]", timeout=5000)
        print("Accepted cookies.")
    except Exception as e:
        print("Cookie acceptance failed or already done:", e)

def click_prijimacky(page):
    try:
        page.wait_for_selector("a.odkaz.vyber_pr", state="visible", timeout=10000)
        page.get_by_role("link", name="PŘIJÍMAČKY").click(timeout=10000)
        print("Clicked on PŘIJÍMAČKY button.")
    except Exception as e:
        print("Failed to click on PŘIJÍMAČKY button:", e)

def wait_for_subject_selection(page):
    try:
        page.wait_for_url("**/predmet_prijimacky.php", timeout=10000)
        print("Navigated to subject selection page.")
    except Exception as e:
        print("Subject selection page did not load as expected:", e)

def select_subject(page, subject):
    if subject == "ma":
        subject_selector = "a.odkaz[href*='predmet=ma']"
    elif subject == "cj":
        subject_selector = "a.odkaz[href*='predmet=cj']"
    else:
        raise ValueError("Unsupported subject value.")
    try:
        page.click(subject_selector, timeout=10000)
        print(f"Clicked on subject selection link for '{subject}'.")
    except Exception as e:
        print("Failed to click on the subject selection link:", e)

def select_category(page, category_radio_id):
    try:
        # Expand the category selection panel
        page.click("#vyber_ulohy", timeout=10000)
        print("Expanded category selection panel.")
        page.wait_for_selector("#content-ulohy", state="visible", timeout=10000)
    except Exception as e:
        print("Failed to expand category selection:", e)

    try:
        # Select the desired category radio button
        page.click(f"#{category_radio_id}", timeout=10000)
        print(f"Selected the category radio button ({category_radio_id}).")
    except Exception as e:
        print("Failed to select category radio button:", e)

    try:
        # Click the submit button to start the test
        page.click("#submitButton", timeout=10000)
        print("Clicked on the submit button to start the test.")
    except Exception as e:
        print("Failed to click the submit button:", e)

def get_test_folder_name(page):
    """
    Extracts the folder name from the <p class="cesta"> element.
    Example content: "Matematika (5. ročník) / Číslo a početní operace"
    """
    try:
        page.wait_for_selector("p.cesta", timeout=5000)
        folder_name = page.query_selector("p.cesta").inner_text().strip()
        # Sanitize the folder name by replacing "/" with " - "
        folder_name = folder_name.replace("/", " - ")
        print(f"Detected test folder name: {folder_name}")
        return folder_name
    except Exception as e:
        print("Error detecting test folder name:", e)
        return "default_test_folder"

def detect_total_questions(page):
    """
    Looks for a paragraph with class "info_text" and a span with class "pocet_text"
    and returns the total number of questions as an integer.
    """
    try:
        page.wait_for_selector("p.info_text span.pocet_text", timeout=5000)
        total_text = page.query_selector("p.info_text span.pocet_text").inner_text().strip()
        total_questions = int(total_text)
        print(f"Detected total questions: {total_questions}")
        return total_questions
    except Exception as e:
        print("Error detecting total questions:", e)
        return None

def capture_question(page, question_url, question_number, screenshot_dir, html_dir):
    print("Navigating to:", question_url)
    page.goto(question_url)
    page.wait_for_load_state("networkidle")
    time.sleep(2)  # Extra wait if needed

    # Capture screenshot of the .container-test div
    try:
        element = page.query_selector("div.container-test")
        if element:
            screenshot_path = os.path.join(screenshot_dir, f"question_{question_number}.png")
            element.screenshot(path=screenshot_path)
            print(f"Saved screenshot as {screenshot_path}")
        else:
            print(f"Element .container-test not found on question page {question_number}")
    except Exception as e:
        print(f"Error taking screenshot of .container-test on question {question_number}:", e)

    # Save HTML content of the question part only.
    # Here we extract only the parts that contain the question content.
    try:
        # Adjust the selector(s) as needed to capture the question text.
        content = page.locator("div.citace-container, div.vypis_zadani").all_inner_texts()
        html_filename = os.path.join(html_dir, f"question_{question_number}.html")
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write("\n\n".join(content))
        print(f"Saved question HTML to: {html_filename}")
    except Exception as e:
        print(f"Error saving HTML for question {question_number}:", e)

def capture_all_questions(page, base_test_url, subject, category_radio_id,
                          start_question, end_question, screenshot_dir, html_dir, detect_total=False):
    # Step 4: Select subject
    select_subject(page, subject)
    # Step 5: Select category and submit
    select_category(page, category_radio_id)

    # Detect test folder name and update output directories
    test_folder = get_test_folder_name(page)
    new_screenshot_dir = os.path.join(screenshot_dir, test_folder)
    new_html_dir = os.path.join(html_dir, test_folder)
    os.makedirs(new_screenshot_dir, exist_ok=True)
    os.makedirs(new_html_dir, exist_ok=True)

    # Optionally detect total questions from the page
    if detect_total:
        detected_total = detect_total_questions(page)
        if detected_total is not None:
            end_question = detected_total
        else:
            print("Falling back to provided end_question value.")

    print(f"Capturing questions from {start_question} to {end_question}.")
    # Step 6: Loop over questions and capture content
    for i in range(start_question, end_question + 1):
        question_url = base_test_url + str(i)
        capture_question(page, question_url, i, new_screenshot_dir, new_html_dir)
    return test_folder  # Return the folder name for later use

def show_results(page):
    # Click the "ukončit" link
    try:
        page.click("a.odkaz.ukoncit", timeout=10000)
        print("Clicked on 'ukončit' button.")
    except Exception as e:
        print("Failed to click on 'ukončit' button:", e)

    # Wait for the popup to appear
    try:
        page.wait_for_selector("div.vyskakovaci-okno", timeout=10000)
        print("Popup appeared.")
    except Exception as e:
        print("Popup did not appear:", e)

    # Click the "Ano" button within the popup
    try:
        page.click("button.opravit-button", timeout=10000)
        print("Clicked 'Ano' in popup.")
    except Exception as e:
        print("Failed to click 'Ano' button in popup:", e)

    # Wait for the results container to appear
    try:
        page.wait_for_selector("div.shrnuti-width", timeout=10000)
        print("Results container is visible.")
    except Exception as e:
        print("Results container did not appear:", e)

def capture_results(page, output_path):
    """
    Captures a full screenshot of the results container (<div class="shrnuti-width">)
    by temporarily resizing the viewport.
    """
    try:
        element = page.query_selector("div.shrnuti-width")
        if element:
            bounding_box = element.bounding_box()
            if bounding_box:
                # Save the original viewport size.
                original_viewport = page.viewport_size
                new_width = int(bounding_box["width"])
                new_height = int(bounding_box["height"])
                page.set_viewport_size({"width": new_width, "height": new_height})
                
                element.screenshot(path=output_path)
                print(f"Saved full results screenshot as {output_path}")
                
                # Restore the original viewport.
                page.set_viewport_size(original_viewport)
            else:
                print("Could not determine bounding box for results container.")
        else:
            print("Results container not found.")
    except Exception as e:
        print("Error capturing results screenshot:", e)

def main(subject, category_radio_id, start_question, end_question,
         screenshot_dir, html_dir, detect_total):
    base_test_url = "https://tau.cermat.cz/test-kategorie.php?poradi_ulohy="

    with sync_playwright() as p:
        # Launch the browser; set headless=True if you do not need the UI.
        browser = p.chromium.launch(headless=False)
        # Create a browser context with a large viewport (simulating a maximized window)
        context = browser.new_context(viewport={'width': 2000, 'height': 2000})
        page = context.new_page()

        # Step 1: Open Homepage and Accept Cookies
        page.goto("https://tau.cermat.cz/")
        accept_cookies(page)

        # Step 2: Click on the PŘIJÍMAČKY Button
        click_prijimacky(page)

        # Step 3: Wait for subject selection page to load
        wait_for_subject_selection(page)

        # Steps 4-6: Process questions (with optional detection of total questions)
        test_folder = capture_all_questions(page, base_test_url, subject, category_radio_id,
                                            start_question, end_question, screenshot_dir, html_dir, detect_total)

        # Now, show results by clicking through the confirmation popup.
        show_results(page)

        # Capture the full results screenshot in the same test folder as questions.
        results_output = os.path.join(screenshot_dir, test_folder, "results.png")
        capture_results(page, results_output)

        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Automate tau.cermat.cz test session and capture questions and results."
    )
    parser.add_argument("--subject", type=str, default="ma", choices=["ma", "cj"],
                        help="Subject to select ('ma' for matematika, 'cj' for český jazyk a literatura). Default is 'ma'.")
    parser.add_argument("--category", type=str, default="radio_2",
                        help="Category radio button ID (default: radio_2).")
    parser.add_argument("--end_question", type=int, default=10,
                        help="Last question number to capture (default: 10). Ignored if --detect-total is used.")
    parser.add_argument("--detect-total", action="store_true",
                        help="Detect the total number of questions from the page instead of using --end_question.")
    args = parser.parse_args()

    # Configuration
    subject = args.subject
    category_radio_id = args.category
    start_question = 1
    end_question = args.end_question

    # Base output directories
    screenshot_dir = "screenshots"
    html_dir = "html_pages"
    os.makedirs(screenshot_dir, exist_ok=True)
    os.makedirs(html_dir, exist_ok=True)

    main(subject, category_radio_id, start_question, end_question, screenshot_dir, html_dir, args.detect_total)
