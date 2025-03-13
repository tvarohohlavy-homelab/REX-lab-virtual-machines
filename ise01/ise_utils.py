#!/usr/bin/env python3

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
#
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
#
from datetime import datetime
from time import sleep
import logging
import sys
import os
#

LOGGER = logging.getLogger("selenium")
LOGGER.setLevel(logging.INFO)
stdoutHandler = logging.StreamHandler(stream=sys.stdout)

# Set the log levels on the handlers
stdoutHandler.setLevel(logging.DEBUG)
fmt = logging.Formatter(
    "%(name)s: %(asctime)s | %(levelname)s | %(filename)s:%(lineno)4s - %(funcName)20s() | %(process)d >>> %(message)s"
)
stdoutHandler.setFormatter(fmt)
LOGGER.addHandler(stdoutHandler)

def waitForReadyState(driver, url=None, clickTarget=None, timeout=30):
    start = datetime.now()
    if url:
        LOGGER.info(f"Waiting for {url} page to load...")
        driver.get(url)
    elif clickTarget:
        LOGGER.info("Waiting for click to be processed...")
        clickTarget.click()
    else:
        LOGGER.info("Waiting for page to load...")
    
    while driver.execute_script("return document.readyState") != "complete":
        if (datetime.now() - start).seconds > timeout:
            LOGGER.error(f"Load timed out at {datetime.now()}")
            raise Exception(f"Load timed out at {datetime.now()}")
        sleep(0.1)
    LOGGER.info(f"Loaded in {datetime.now() - start}")      

def waitForClick(driver, clickTarget, timeout=30):
    waitForReadyState(driver, clickTarget=clickTarget, timeout=timeout)

def waitForUrl(driver, url, timeout=30):
    waitForReadyState(driver, url=url, timeout=timeout)

def getDriver(url=None):
    chrome_options = Options()
    chrome_options.add_argument("--headless")                  # Run Chrome in headless mode (no visible UI)
    chrome_options.add_argument("--no-sandbox")                # Often needed in containerized/CI environments
    chrome_options.add_argument("--disable-dev-shm-usage")     # Bypass /dev/shm issue if it's limited
    chrome_options.add_argument("--disable-gpu")               # Potentially speeds up/avoids some issues on certain environments
    chrome_options.add_argument("--ignore-certificate-errors") # Tells Chrome not to reject self-signed certs
    chrome_options.add_argument("--allow-insecure-localhost")  # Allows navigation to pages on localhost with untrusted certs
    chrome_options.page_load_strategy = "normal"               # Options are: none, eager, normal
    path = os.path.dirname(os.path.abspath(__file__))
    prefs = {
        "download.default_directory": path
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Initialize the ChromeDriver using webdriver_manager
    LOGGER.info("Starting ChromeDriver...")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    LOGGER.info("ChromeDriver started.")
    LOGGER.info("Maximizing window...")
    driver.maximize_window()
    LOGGER.info("Window maximized.")
    if url:
        waitForUrl(driver, url)
    LOGGER.info("Returning driver.")
    return driver

def iseLogin(driver, username=None, password=None, check_mode=False, timeout=30):
    try:
        LOGGER.info("Waiting for ISE login page to load...")
        loginPageReady = WebDriverWait(driver, timeout).until(
            EC.all_of(
                EC.url_contains("admin/login.jsp"),
                EC.presence_of_element_located((By.NAME, "username")),
                EC.element_to_be_clickable((By.NAME, "username")), 
                EC.presence_of_element_located((By.NAME, "password")),
                EC.element_to_be_clickable((By.NAME, "password")),
                EC.presence_of_element_located((By.ID, "loginPage_loginSubmit"))
            )
        )
        LOGGER.info("ISE login page loaded.")
    except (TimeoutException, NoSuchElementException) as e:
        loginPageReady = False

    if check_mode:
        LOGGER.info("Returning loginPageReady status (check_mode).")
        return loginPageReady

    if not loginPageReady:
        LOGGER.error("Failed to load ISE login page at %s", datetime.now())
        raise Exception(f"Failed to load ISE login page at {datetime.now()}")

    if not username or not password:
        LOGGER.error("Username and password are required to login to ISE at %s", datetime.now())
        raise Exception(f"Username and password are required to login to ISE at {datetime.now()}")

    LOGGER.info("Entering username...")
    username_field = driver.find_element(By.NAME, "username")
    username_field.click()
    username_field.send_keys(username)
    LOGGER.info("Username entered.")
    LOGGER.info("Entering password...")
    password_field = driver.find_element(By.NAME, "password")
    password_field.click()
    password_field.send_keys(password)
    LOGGER.info("Password entered.")
    LOGGER.info("Submitting login form...")
    submit_button = driver.find_element(By.ID, "loginPage_loginSubmit")
    waitForClick(driver, submit_button)
    LOGGER.info("Login form submitted.")

def isePostLoginPopUps(driver, timeout=30):
    # while class:xwtAlert is present
    while True:
        try:
            LOGGER.info("Waiting for ISE alert pop-up to appear...")
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME, "xwtAlert"))
            )
            LOGGER.info("ISE alert pop-up found.")
            # find button element within above class div using xpath and click it
            try:
                LOGGER.info("Waiting for alert button to appear and to be clickable...")
                WebDriverWait(driver, timeout).until(
                    EC.all_of(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'xwtAlert')]//button")),
                        EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'xwtAlert')]//button"))
                    )
                )
                LOGGER.info("Alert button found and clickable.")
                alertButton = driver.find_element(By.XPATH, "//div[contains(@class,'xwtAlert')]//button")
                LOGGER.info("Clicking alert button...")
                alertButton.click()
                LOGGER.info("Alert button clicked.")
                timeout = 5
                LOGGER.info("Waiting for ISE UI to reflect changes...")
                sleep(1)
                LOGGER.info("Waiting finished.")
            except (TimeoutException, NoSuchElementException) as e:
                LOGGER.error("Failed to find alert button in ISE pop-up at %s", datetime.now())
                raise Exception(f"Failed to find alert button in ISE pop-up at {datetime.now()}")
        except (TimeoutException, NoSuchElementException) as e:
            LOGGER.info("ISE alert pop-up not found.")
            break                  
    timeout = 5
    # while id:ise-modal is present
    while True:
        try:
            LOGGER.info("Waiting for ISE modal to appear...")
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.ID, "ise-modal"))
            )
            LOGGER.info("ISE modal found.")
            # find id:carousel-next button and click it
            try:
                LOGGER.info("Waiting for next button to appear and to be clickable...")
                WebDriverWait(driver, timeout).until(
                    EC.all_of(
                        EC.presence_of_element_located((By.ID, "carousel-next")),
                        EC.element_to_be_clickable((By.ID, "carousel-next"))
                    )
                )
                LOGGER.info("Next button found and clickable.")
                nextButton = driver.find_element(By.ID, "carousel-next")
                LOGGER.info("Clicking next button...")
                nextButton.click()
                LOGGER.info("Next button clicked.")
                LOGGER.info("Waiting for ISE UI to reflect changes...")
                sleep(1)
                LOGGER.info("Waiting finished.")
            except (TimeoutException, NoSuchElementException) as e:
                LOGGER.error("Failed to find next button in ISE modal at %s", datetime.now())
                raise Exception(f"Failed to find next button in ISE modal at {datetime.now()}")
        except (TimeoutException, NoSuchElementException) as e:
            LOGGER.info("ISE modal not found.")
            break

def iseLogout(driver, timeout=30):
    try:
        LOGGER.info("Waiting for settings dropdown to appear...")
        settingsDropdown = WebDriverWait(driver, timeout).until(
            EC.all_of(
                EC.url_contains("admin"),
                EC.presence_of_element_located((By.CLASS_NAME, "fi-setting")),
                EC.element_to_be_clickable((By.CLASS_NAME, "fi-setting"))
            )
        )
        LOGGER.info("Settings dropdown found.")
    except (TimeoutException, NoSuchElementException) as e:
        settingsDropdown = False
    
    if not settingsDropdown:
        LOGGER.error("Failed to find settings dropdown to logout at %s", datetime.now())
        raise Exception(f"Failed to find settings dropdown to logout at {datetime.now()}")
    
    settingsDropdown = driver.find_element(By.CLASS_NAME, "fi-setting")
    LOGGER.info("Clicking settings dropdown...")
    settingsDropdown.click()
    LOGGER.info("Settings dropdown clicked.")
    LOGGER.info("Waiting for logout link to appear and be clickable...")
    WebDriverWait(driver, timeout).until(
        EC.all_of(
            EC.presence_of_element_located((By.LINK_TEXT, "Logout")),
            EC.element_to_be_clickable((By.LINK_TEXT, "Logout"))
        )
    )
    LOGGER.info("Logout link found.")
    logoutLink = driver.find_element(By.LINK_TEXT, "Logout")
    LOGGER.info("Clicking logout link...")
    waitForClick(driver, logoutLink)
    LOGGER.info("Logout successful.")

def takeScreenshot(driver, prefix= "", suffix="", folder=""):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
    if not folder:
        folder = "./"
    driver.save_screenshot(folder + prefix + timestamp + suffix + ".png")
