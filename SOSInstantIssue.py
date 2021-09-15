import logging
import os
from datetime import date
import time
import json
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from cryptography.fernet import Fernet

try:
    # Logger setup
    InstantIssue_Log = r"F:\Python\SOS Instant Issue\Logs\SOS Instant Issue Logs.txt"
    logging.basicConfig(level=logging.INFO, filename=InstantIssue_Log, filemode='a', format='%(lineno)d - %(asctime)s - %(message)s')

    # retrieving encrypted password
    key = b'9zrSPd6tAfv7xd6hHV6Qmt-kf-9mNMxNlT7SATNKYiw='
    cipher_suite = Fernet(key)

    try:
        with open(r'F:\Python\Credentials\SOSInstantIssue_pw_bytes.bin', 'rb') as file_object:
            for line in file_object:
                encryptedpwd = line
    except Exception as ex:
        logging.exception('File not found')

    decryptedpwd = (cipher_suite.decrypt(encryptedpwd))
    plain_text_encryptedpwd = bytes(decryptedpwd).decode("utf-8")

    email = 'drainwater@bibank.com'
    password = plain_text_encryptedpwd
    wait_time = 15
    downloads_path = r'F:\Downloads'

    # initializing Chrome driver
    chrome_options = webdriver.ChromeOptions()
    prefs = {"download.default_directory" : "F:\Downloads"}
    chrome_options.add_experimental_option("prefs",prefs)
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get('https://cardwizard.bientrust.bankindependent.com/#/login')
    except Exception as ex:
        logging.exception('Driver failed')


    # logging in:
    login_email = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, "loginUserName"))
            )
    login_password = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, "loginPassword"))
            )
    login_submit = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, "loginBtnSubmit"))
            )

    login_email.send_keys(email)
    login_password.send_keys(password)
    login_submit.click()

    # navigating to Reports
    reports = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, "Reports"))
            )
    reports.click()

    inventory_summary = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, "InventorySummary"))
            )
    inventory_summary.click()

    # Selecting all locations and running report
    location = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, "selectPCGroup"))
            )

    reload = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, "btnReload"))
            )
    select_location = Select(location)
    select_location.select_by_index(0)
    reload.submit()

    time.sleep(5)

    # download report
    json_button = WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, "imgJson"))
            )
    json_button.click()

    time.sleep(5)

    # create a list of json files in Downloads folder sorted by date created
    json_list = [os.path.join(downloads_path, files) for files in os.listdir(downloads_path) if files.endswith(".JSON")]

    json_list.sort(reverse = True, key = lambda file: os.stat(file).st_ctime)

    # wait for file to be downloaded and show in the downloads folder
    time_to_wait = wait_time
    time_counter = 0
    while not date.fromtimestamp(os.stat(json_list[0]).st_ctime) == date.today():
        time.sleep(1)
        time_counter += 1
        json_list.sort(reverse = True, key = lambda file: os.stat(file).st_ctime)
        if time_counter > time_to_wait:
            break

    # append json data into operating file and save
    try:
        with open(json_list[0], 'r+') as f_daily:
            data_daily = json.load(f_daily)
    except Exception as ex:
        logging.exception('File not found')

    try:
        with open(r"F:\Power BI\Data Sources\OPERATINGInventorySummary.JSON", 'r+') as f_master:
            data_master = json.load(f_master)
    except Exception as ex:
        logging.exception('File not found')

    try:
        datasets_daily = data_daily['InventorySummaryDataSet']
        datasets_master = data_master['InventorySummaryDataSet']

        branches_daily = datasets_daily['InventorySummaryData']
        branches_master = datasets_master['InventorySummaryData']

        for dict in branches_daily:
            branches_master.append(dict)
    except Exception as ex:
        logging.exception('append error')

    try:
        with open(r"F:\Power BI\Data Sources\OPERATINGInventorySummary.JSON", 'w+') as f_master:
            json.dump(data_master, f_master)
    except Exception as ex:
        logging.exception('File not found')

    time.sleep(5)

finally:
    driver.close()
    driver.quit()
    logging.info('Driver quit')
