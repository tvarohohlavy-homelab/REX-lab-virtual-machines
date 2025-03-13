#!/usr/bin/env python3

from selenium.common.exceptions import TimeoutException, NoSuchElementException
#
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
#
from ise_utils import getDriver, iseLogin, waitForClick
#
from datetime import datetime
#
import argparse
import os

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
    
    baseUrl = f"https://{host}/admin"
    try:
        driver = getDriver(url=f"{baseUrl}/login.jsp")
        # Login
        iseLogin(driver, username, old_password, timeout=60)
        # Initial enforced password change
        try:
            passwordResetURLCheck = WebDriverWait(driver, 60).until(
                expected_conditions.all_of(
                    expected_conditions.url_contains("resetPassword"),
                    expected_conditions.presence_of_element_located((By.ID, "PWD")),
                    expected_conditions.element_to_be_clickable((By.ID, "PWD")),
                    expected_conditions.presence_of_element_located((By.ID, "confirmPWD")),
                    expected_conditions.element_to_be_clickable((By.ID, "confirmPWD")),
                    expected_conditions.presence_of_element_located((By.ID, "rstBtn"))
                )
            )
        except (TimeoutException, NoSuchElementException) as e:
            passwordResetURLCheck = False
        
        if not passwordResetURLCheck:
            raise Exception(f"Expected password reset redirect not found for {username} at {host} at {datetime.now()}")
        
        # enter and save new password
        newPasswordField = driver.find_element(By.ID, "PWD")
        newPasswordField.click()
        newPasswordField.send_keys(new_password)
        confirmPasswordField = driver.find_element(By.ID, "confirmPWD")
        confirmPasswordField.click()
        confirmPasswordField.send_keys(new_password)
        submitButton = driver.find_element(By.ID, "rstBtn")
        waitForClick(driver, submitButton)
        
        # wait for login page to load
        if iseLogin(driver, check_mode=True):
            print(f"Successfully reset ISE admin password for {username} at {host} at {datetime.now()}")
        else:
            raise Exception(f"Failed to reset ISE admin password for {username} at {host} at {datetime.now()}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
