#!/usr/bin/env python3

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
#
from ise_utils import getDriver, iseLogin, iseLogout, isePostLoginPopUps, LOGGER, waitForUrl, waitForClick
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
        # Perform Policy Export to local file
        # Navigate to Administration > System > Backup & Restore > Policy Export
        waitForUrl(driver, f"{baseUrl}/#administration/administration_system/backup_restore/backup_restore_policy_export")
        WebDriverWait(driver, 10).until(
            EC.all_of(
                EC.presence_of_element_located((By.ID, "expNoEncryp")),
                EC.element_to_be_clickable((By.ID, "expNoEncryp")),
                EC.presence_of_element_located((By.ID, "dwnLclComp")),
                EC.element_to_be_clickable((By.ID, "dwnLclComp")),
                EC.presence_of_element_located((By.ID, "exportPolicy")),
                EC.element_to_be_clickable((By.ID, "exportPolicy"))
            )
        )
        # Hide side menu
        driver.find_element(By.CLASS_NAME, "sidenav-toggler").click()
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='sidenav'][@class='toggled']"))
        )
        # Perform Policy Export
        expNoEncryp = driver.find_element(By.ID, "expNoEncryp") # Uncheck Encryption
        driver.execute_script("arguments[0].scrollIntoView();", expNoEncryp) # slide into view
        expNoEncryp.click()
        dwnLclComp = driver.find_element(By.ID, "dwnLclComp") # Check Download to Local Computer
        dwnLclComp.click()
        exportPolicyButton = driver.find_element(By.ID, "exportPolicy") # Export Policy
        LOGGER.info("Exporting Policy to local file...")
        waitForClick(driver, exportPolicyButton)
        LOGGER.info("Policy Exported to local file")
        # #######################################################################

        # Logout
        iseLogout(driver)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
