from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("http://localhost:5000/login")
wait = WebDriverWait(driver, 15)

wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys("admin@eventhub.com")
driver.find_element(By.NAME, "password").send_keys("Admin@12345")
driver.find_element(By.CSS_SELECTOR, "button.btn-gradient").click()

wait.until(EC.url_contains("/admin"))
time.sleep(2)  # give the page time to fully render

print("\n=== PAGE URL ===")
print(driver.current_url)

print("\n=== PAGE TITLE ===")
print(driver.title)

print("\n=== H2 HEADINGS ===")
for h in driver.find_elements(By.TAG_NAME, "h2"):
    print(f"  - {h.text}")

print("\n=== TABLE ROWS ===")
rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
print(f"Total rows: {len(rows)}")
for i, row in enumerate(rows[:5]):
    cells = row.find_elements(By.TAG_NAME, "td")
    print(f"  Row {i+1}: {[c.text for c in cells]}")

print("\n=== PAGE TEXT (first 500 chars) ===")
print(driver.find_element(By.TAG_NAME, "body").text[:500])

time.sleep(3)
driver.quit()