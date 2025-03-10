#!/usr/bin/env python3

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
#
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
#
from datetime import datetime
#
import argparse
import os

def getDriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")                  # Run Chrome in headless mode (no visible UI)
    chrome_options.add_argument("--no-sandbox")                # Often needed in containerized/CI environments
    chrome_options.add_argument("--disable-dev-shm-usage")     # Bypass /dev/shm issue if it's limited
    chrome_options.add_argument("--disable-gpu")               # Potentially speeds up/avoids some issues on certain environments
    chrome_options.add_argument("--ignore-certificate-errors") # Tells Chrome not to reject self-signed certs
    chrome_options.add_argument("--allow-insecure-localhost")  # Allows navigation to pages on localhost with untrusted certs

    # Initialize the ChromeDriver using webdriver_manager
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver

def iseLogin(driver, username, password):
    username_field = driver.find_element(By.NAME, "username")
    username_field.click()
    username_field.send_keys(username)
    password_field = driver.find_element(By.NAME, "password")
    password_field.click()
    password_field.send_keys(password)
    submit_button = driver.find_element(By.ID, "loginPage_loginSubmit")
    submit_button.click()

def main():

    # process arguments, failover to environment variables
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default=os.getenv("ISE_HOST", ""), help="Cisco ISE hostname or IP address (env ISE_HOST) (required)")
    parser.add_argument("--username", type=str, default=os.getenv("ISE_USERNAME", ""), help="Cisco ISE username (env ISE_USERNAME) (required)")
    parser.add_argument("--old-password", type=str, default=os.getenv("ISE_OLD_PASSWORD", ""), help="Cisco ISE initial admin password (env ISE_OLD_PASSWORD) (required)")
    parser.add_argument("--new-password", type=str, default=os.getenv("ISE_NEW_PASSWORD", ""), help="Cisco ISE final admin password (env ISE_NEW_PASSWORD) (required)")
    args = parser.parse_args()
    host = args.host
    username = args.username
    old_password = args.old_password
    new_password = args.new_password

    if not host or not username or not old_password or not new_password:
        parser.print_help()
        exit(1)
    
    baseUrl = f"https://{host}/admin/login.jsp"
    driver = getDriver()

    try:
        driver.get(baseUrl)
        driver.set_window_size(1920, 1040)
        # Login
        iseLogin(driver, username, old_password)
        # Initial enforced password change
        try:
            passwordResetURLCheck = WebDriverWait(driver, 10).until(
                expected_conditions.url_contains("resetPassword")
            )
        except TimeoutException:
            passwordResetURLCheck = False
        if passwordResetURLCheck:
            # wait for new password field just to be sure
            WebDriverWait(driver, 20).until(
                expected_conditions.presence_of_element_located((By.ID, "PWD"))
            )
            WebDriverWait(driver, 20).until(
                expected_conditions.element_to_be_clickable((By.ID, "PWD"))
            )
            # enter and save new password
            newPasswordField = driver.find_element(By.ID, "PWD")
            newPasswordField.click()
            newPasswordField.send_keys(new_password)
            confirmPasswordField = driver.find_element(By.ID, "confirmPWD")
            confirmPasswordField.click()
            confirmPasswordField.send_keys(new_password)
            submitButton = driver.find_element(By.ID, "rstBtn")
            submitButton.click()
            # wait for initial login page submit button
            initialLoginPageCheck = WebDriverWait(driver, 10).until(
                expected_conditions.presence_of_element_located((By.ID, "loginPage_loginSubmit"))
            )
            if initialLoginPageCheck:
                print(f"Successfully reset ISE admin password for {username} at {host} at {datetime.now()}")
            else:
                raise Exception(f"Failed to reset ISE admin password for {username} at {host} at {datetime.now()}")
        else:
            raise Exception(f"Expected password reset redirect not found for {username} at {host} at {datetime.now()}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()