import time

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
