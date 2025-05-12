import os
import time
import pandas as pd
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

load_dotenv()

# 2Captcha Proxy Configuration
TWOCAPTCHA_USERNAME = os.getenv('TWOCAPTCHA_USERNAME')
TWOCAPTCHA_PASSWORD = os.getenv('TWOCAPTCHA_PASSWORD')
PROXY_DNS = os.getenv('PROXY_DNS')

print(TWOCAPTCHA_USERNAME)
print(TWOCAPTCHA_PASSWORD)
print(PROXY_DNS)

class MondayMarketPlaceScraper():
    def __init__(self) -> None:
        '''Initializes Selenium WebDriver and sets up proxy'''
        print("[INFO] Initializing WebDriver...")
        self.proxy_url = self.get_proxy()
        self.setup_driver()

    def get_proxy(self):
        """
        Returns a dictionary with proxy credentials formatted for HTTP/S use.
        """
        proxy_url = f"http://{TWOCAPTCHA_USERNAME}:{TWOCAPTCHA_PASSWORD}@{PROXY_DNS}"
        return proxy_url

    def check_ip(self, proxy):
        """
        Prints and returns the current external IP using the configured proxy.
        """
        print("[INFO] Checking proxy IP address...")
        try:
            response = requests.get("http://ip-api.com/json", proxies=proxy, timeout=10)
            ip_data = response.json()
            ip_address = ip_data.get('query', 'Unknown')
            country = ip_data.get('country', 'Unknown')
            print(f"[INFO] Current Proxy IP: {ip_address} ({country})")
            return ip_address
        except requests.exceptions.RequestException:
            print("[WARNING] Failed to fetch IP address. Proxy might be blocked!")
            return "Failed"

    def setup_driver(self):
        '''Configures the Selenium WebDriver (Chrome) with proxy'''
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument(f'--proxy-server={self.proxy_url}')
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.maximize_window()
            print("[INFO] WebDriver initialized successfully with proxy.")
        except Exception as e:
            print(f"[ERROR] Failed to initialize WebDriver: {e}")
            raise

    def scrolling_and_pagination(self, URL):
        '''Automates scrolling and paginating through search results'''
        print(f"[INFO] Navigating to URL: {URL}")
        try:
            self.driver.get(URL)
            print("[INFO] Page loaded. Waiting for main element...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#listing-header-controls > a > button"))
            )
            print("[INFO] Main element located. Scrolling to bottom...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            print("[INFO] Scrolling complete.")
        except TimeoutException:
            print(f"[WARNING] Timeout while loading page or waiting for element at {URL}")
        except Exception as e:
            print(f"[ERROR] Unexpected error during scrolling: {e}")

    def log_visit(self, url, proxy_ip):
        '''Logs the visit to an Excel file with date, time, and IP address only'''
        print("[INFO] Logging visit to Excel file...")
        log_file = "visit_log.xlsx"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = pd.DataFrame([[now, url, proxy_ip]],
                                 columns=["Timestamp", "URL", "IP"])

        try:
            if os.path.exists(log_file):
                old_df = pd.read_excel(log_file)
                updated_df = pd.concat([old_df, new_entry], ignore_index=True)
            else:
                updated_df = new_entry

            updated_df.to_excel(log_file, index=False)
            print("[INFO] Visit logged successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to write to log file: {e}")

if __name__ == "__main__":
    URL = "https://auth.monday.com/marketplace/listing/12/docugen"
    print("[INFO] Script started.")

    scraper = MondayMarketPlaceScraper()
    proxy_ip = scraper.check_ip({"http": scraper.proxy_url, "https": scraper.proxy_url})

    try:
        scraper.scrolling_and_pagination(URL)
        scraper.log_visit(URL, proxy_ip)
    finally:
        scraper.driver.quit()
        print("[INFO] WebDriver closed. Script finished.")