#!/usr/bin/env python3

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
#
from ise_utils import getDriver, iseLogin, iseLogout, isePostLoginPopUps, LOGGER, waitForUrl
#
import argparse
import os

def main():

    # process arguments, failover to environment variables
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default=os.getenv("ISE_HOST", ""), help="Cisco ISE hostname or IP address (env ISE_HOST) (required)")
    parser.add_argument("--username", type=str, default=os.getenv("ISE_USERNAME", ""), help="Cisco ISE username (env ISE_USERNAME) (required)")
    parser.add_argument("--password", type=str, default=os.getenv("ISE_PASSWORD", ""), help="Cisco ISE password (env ISE_PASSWORD) (required)")
    args = parser.parse_args()
    host = args.host
    username = args.username
    password = args.password

    if not host or not username or not password:
        parser.print_help()
        exit(1)
    
    baseUrl = f"https://{host}/admin"
    try:
        driver = getDriver(url=f"{baseUrl}/login.jsp")
        # Login
        iseLogin(driver, username, password, timeout=60)
        isePostLoginPopUps(driver)
        #

        # #######################################################################
        # Disable Administrator password expiration
        # Navigate to Administration > System > Admin Access > Authentication
        waitForUrl(driver, f"{baseUrl}/#administration/administration_system/administration_system_rbac/adminAccess_authentication")
        
        WebDriverWait(driver, 10).until(
            EC.all_of(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Password Policy']")),
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Password Policy']"))
            )
        )
        # Click on Password Policy Tab
        passwordPolicy = driver.find_element(By.XPATH, "//span[text()='Password Policy']")
        passwordPolicy.click()
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "adminAuthSettingsStub.passwordDisableUserAccountChk"))
        )
        passwordExpirationCheckbox = driver.find_element(By.ID, "adminAuthSettingsStub.passwordDisableUserAccountChk")
        # Following code was not working as expected
        # driver.execute_script("arguments[0].scrollIntoView();", passwordExpirationCheckbox) # not needed
        # WebDriverWait(driver, 5).until(
        #     EC.element_to_be_clickable((By.ID, "adminAuthSettingsStub.passwordDisableUserAccountChk"))
        # )
        if passwordExpirationCheckbox.is_selected(): # If checked, uncheck it
            LOGGER.info("Password expiration is enabled. Disabling it...")
            passwordExpirationCheckbox.click()
            LOGGER.info("Waiting for save button to be enabled...")
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "submitAuthBtn"))
            )
            LOGGER.info("Save button enabled.")
            saveButton = driver.find_element(By.ID, "submitAuthBtn")
            LOGGER.info("Saving changes...")
            saveButton.click()
            LOGGER.info("Changes saved.")
        else:
            LOGGER.info("Password expiration is already disabled.")
        # #######################################################################

        # Logout
        iseLogout(driver)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
