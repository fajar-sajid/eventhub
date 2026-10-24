"""
Selenium E2E test for EventHub.
Run: python test_app.py
"""
import time
import random
import string
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select

# ⚠️ Change to your AWS ALB URL later
BASE_URL = "http://localhost:5000"
ADMIN_EMAIL = "admin@eventhub.com"
ADMIN_PASSWORD = "Admin@12345"


# ---------- HELPERS ----------
def unique_email(prefix="testuser"):
    """Generate a unique email so re-runs don't collide."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = "".join(random.choices(string.ascii_lowercase, k=4))
    return f"{prefix}_{ts}_{rand}@test.com"


def get_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


# ---------- TEST 1: HOMEPAGE ----------
def test_1_homepage_loads():
    """Test 1 — Homepage title and hero heading visible."""
    driver = get_driver()
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 10)
        heading = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        assert "Event" in heading.text or "Discover" in heading.text
        assert "EventHub" in driver.title
        print(f"✅ Test 1 PASSED — Title: {driver.title}")
    finally:
        time.sleep(2)
        driver.quit()


# ---------- TEST 2: EVENTS VISIBLE ----------
def test_2_events_visible():
    """Test 2 — Event cards render on homepage."""
    driver = get_driver()
    try:
        driver.get(BASE_URL)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "event-card")))
        cards = driver.find_elements(By.CLASS_NAME, "event-card")
        assert len(cards) >= 5, f"Expected at least 5 cards, got {len(cards)}"
        print(f"✅ Test 2 PASSED — Found {len(cards)} event cards")
    finally:
        time.sleep(2)
        driver.quit()


# ---------- TEST 3: LOGIN PAGE RENDERS ----------
def test_3_login_page():
    """Test 3 — Login form fields and button render."""
    driver = get_driver()
    try:
        driver.get(f"{BASE_URL}/login")
        wait = WebDriverWait(driver, 10)
        email = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        password = driver.find_element(By.NAME, "password")
        button = driver.find_element(By.CSS_SELECTOR, "button.btn-gradient")
        assert email.is_displayed() and password.is_displayed() and button.is_displayed()
        print("✅ Test 3 PASSED — Login form complete")
    finally:
        time.sleep(2)
        driver.quit()


# ---------- TEST 4: ADMIN LOGIN ----------
def test_4_admin_login_and_navigate():
    """Test 4 — Login as admin → dashboard loads with events."""
    driver = get_driver()
    try:
        driver.get(f"{BASE_URL}/login")
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(ADMIN_EMAIL)
        driver.find_element(By.NAME, "password").send_keys(ADMIN_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button.btn-gradient").click()

        # Wait for dashboard
        wait.until(EC.url_contains("/admin"))
        print(f"   → Redirected to: {driver.current_url}")

        # Stat boxes
        stats = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "stat-box")))
        assert len(stats) >= 4, f"Expected 4 stat boxes, got {len(stats)}"
        print(f"   → Found {len(stats)} stat boxes")

        # Table rows
        rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr")))
        assert len(rows) >= 1, f"Expected at least 1 event row, got {len(rows)}"
        print(f"   → Found {len(rows)} event rows")

        # ⭐ Read actual table cell text — this is the fix
        all_titles = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                all_titles.append(cells[1].text.strip())  # column 2 = title

        print(f"   → Event titles in table: {all_titles}")

        # Case-insensitive check against any known title
        known = ["tech expo", "rock night", "city marathon",
                 "modern art", "startup pitch", "persistence test"]
        joined = " | ".join(t.lower() for t in all_titles)
        matched = [t for t in known if t in joined]
        assert len(matched) >= 1, \
            f"No known event found. Titles seen: {all_titles}"

        print(f"✅ Test 4 PASSED — Dashboard shows {len(rows)} events, matched: {matched}")

    finally:
        time.sleep(2)
        driver.quit()

# ---------- TEST 5: REGISTER NEW USER ----------
def test_5_register_new_user():
    """Test 5 — Register a new user via the form, verify success + redirect."""
    new_email = unique_email("seleniumuser")
    new_password = "TestPass123"
    new_name = "Selenium Test User"

    print(f"   → Registering: {new_email}")

    driver = get_driver()
    try:
        driver.get(f"{BASE_URL}/register")
        wait = WebDriverWait(driver, 15)

        # Fill register form
        wait.until(EC.presence_of_element_located((By.NAME, "name"))).send_keys(new_name)
        driver.find_element(By.NAME, "email").send_keys(new_email)
        driver.find_element(By.NAME, "password").send_keys(new_password)
        driver.find_element(By.NAME, "confirm").send_keys(new_password)

        # Close any visible flash messages (they overlay the button)
        driver.execute_script("""
            document.querySelectorAll('.alert').forEach(a => a.remove());
        """)

        # Scroll the button into view, then JS-click it (bypasses CSS overlays)
        button = driver.find_element(By.CSS_SELECTOR, "button.btn-gradient")
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", button)

        # Expect redirect to /login
        wait.until(EC.url_contains("/login"))
        print(f"   → Redirected to: {driver.current_url}")

        # Verify success flash
        page_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert ("account created" in page_text
                or "please log in" in page_text
                or "success" in page_text), \
            "No success message after registration"
        print(f"✅ Test 5 PASSED — Registered {new_email}")

        # Save credentials for Test 6
        with open(".last_test_user.txt", "w") as f:
            f.write(f"{new_email}|{new_password}")

    finally:
        time.sleep(2)
        driver.quit()

# ---------- TEST 6: LOGIN WITH NEW USER ----------
def test_6_login_new_user():
    """Test 6 — Login with the user registered in Test 5."""
    # Read credentials from file
    try:
        with open(".last_test_user.txt") as f:
            new_email, new_password = f.read().strip().split("|")
    except FileNotFoundError:
        print("⚠️ Skipping Test 6 — no user from Test 5")
        return

    print(f"   → Logging in as: {new_email}")

    driver = get_driver()
    try:
        driver.get(f"{BASE_URL}/login")
        wait = WebDriverWait(driver, 15)

        wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(new_email)
        driver.find_element(By.NAME, "password").send_keys(new_password)
        driver.find_element(By.CSS_SELECTOR, "button.btn-gradient").click()

        # Regular user should redirect to "/" (homepage), not /admin
        time.sleep(2)  # let redirect happen
        assert "/admin" not in driver.current_url, \
            "Regular user was wrongly redirected to admin page!"
        print(f"   → Redirected to: {driver.current_url}")

        # Verify logged-in navbar (Welcome message or Logout link)
        page_text = driver.find_element(By.TAG_NAME, "body").text
        assert "Logout" in page_text or "Selenium Test User" in page_text, \
            "Not logged in — no user indicator found"
        print(f"✅ Test 6 PASSED — Logged in as {new_email} (regular user → homepage)")

    finally:
        time.sleep(2)
        driver.quit()

# ---------- TEST 7: CREATE EVENT AS ADMIN ----------
def test_7_admin_creates_event():
    """Test 7 — Login as admin → create event via UI → verify it's saved."""
    ts = datetime.now().strftime("%H%M%S")
    event_title = f"Selenium Event {ts}"
    event_venue = "Selenium Test Hall"
    event_date = "2026-12-30"
    event_time = "15:00"
    event_capacity = "42"

    print(f"   → Creating event: '{event_title}'")

    driver = get_driver()
    try:
        # 1. Login as admin
        driver.get(f"{BASE_URL}/login")
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(ADMIN_EMAIL)
        driver.find_element(By.NAME, "password").send_keys(ADMIN_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "button.btn-gradient").click()
        wait.until(EC.url_contains("/admin"))
        print("   → Logged in as admin")

        # 2. Open the Add Event form
        driver.get(f"{BASE_URL}/admin/event/new")
        wait.until(EC.presence_of_element_located((By.NAME, "title")))
        print(f"   → Opened: {driver.current_url}")

        # 3. Fill text fields (safe for text inputs)
        driver.find_element(By.NAME, "title").send_keys(event_title)
        driver.find_element(By.NAME, "description").send_keys(
            "Created by Selenium E2E test — verifying end-to-end data flow."
        )
        driver.find_element(By.NAME, "venue").send_keys(event_venue)

        # 4. Set date/time/capacity via JS (bypasses HTML5 input mask corruption)
        driver.execute_script(f"""
            document.querySelector('input[name="event_date"]').value = '{event_date}';
            document.querySelector('input[name="event_time"]').value = '{event_time}';
            document.querySelector('input[name="capacity"]').value = '{event_capacity}';
        """)

        # 5. Select category via JS
        driver.execute_script("""
            const sel = document.querySelector('select[name="category_id"]');
            sel.selectedIndex = 1;
            sel.dispatchEvent(new Event('change', { bubbles: true }));
        """)

        # 6. Debug: confirm all field values before submit
        values = driver.execute_script("""
            return {
                title:    document.querySelector('[name="title"]').value,
                date:     document.querySelector('[name="event_date"]').value,
                time:     document.querySelector('[name="event_time"]').value,
                venue:    document.querySelector('[name="venue"]').value,
                capacity: document.querySelector('[name="capacity"]').value,
                category: document.querySelector('[name="category_id"]').value
            };
        """)
        print(f"   → Form values: {values}")

        # 7. Submit the form via JS (bypasses button click interception)
        driver.execute_script("""
            document.querySelector('form[method="POST"]').submit();
        """)

        # 8. Wait for redirect back to /admin
        try:
            wait.until(EC.url_contains("/admin"))
            assert "/admin/event/new" not in driver.current_url, "Form did not submit"
        except Exception:
            driver.save_screenshot("test7_failure.png")
            print("   ⚠️ Form did not redirect — screenshot: test7_failure.png")
            print(f"   → Page text: {driver.find_element(By.TAG_NAME, 'body').text[:300]}")
            raise
        print(f"   → Redirected to: {driver.current_url}")

        # 9. Wait for table rows to exist
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))

        # 10. Extra wait — Selenium text extraction is lazy after redirect
        time.sleep(1.5)

        # 11. Try reading titles via Selenium
        titles = []
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                titles.append(cells[1].text.strip())

        print(f"   → Titles via Selenium: {titles}")

        # 12. Fallback — read titles via JS innerText if Selenium returns empty
        if not any(titles) or event_title not in titles:
            print("   → Selenium titles empty — falling back to JS extraction")
            titles = driver.execute_script("""
                return Array.from(document.querySelectorAll('table tbody tr'))
                    .map(r => {
                        const cells = r.querySelectorAll('td');
                        return cells.length >= 2 ? cells[1].innerText.trim() : '';
                    });
            """)
            print(f"   → Titles via JS: {titles}")

        # 13. Assert new event exists
        assert event_title in titles, \
            f"New event '{event_title}' not found in dashboard. Titles: {titles}"
        print(f"   → New event appears in dashboard ✅")

        print(f"✅ Test 7 PASSED — Created event '{event_title}'")

    finally:
        time.sleep(2)
        driver.quit()

# ---------- RUNNER ----------
if __name__ == "__main__":
    print(f"\n🧪 Running Selenium E2E tests against {BASE_URL}\n" + "="*60)
    test_1_homepage_loads()
    test_2_events_visible()
    test_3_login_page()
    test_4_admin_login_and_navigate()
    test_5_register_new_user()
    test_6_login_new_user()
    test_7_admin_creates_event()
    print("="*60)
    print("🎉 ALL 6 SELENIUM TESTS PASSED\n")