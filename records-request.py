from base64 import b64decode
from datetime import datetime
from time import sleep, strftime, strptime

import yaml
from dateutil.relativedelta import relativedelta
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.print_page_options import PrintOptions

with open("info.yml", "r") as file:
    info = yaml.safe_load(file)["services"]


def initialize():
    driver = webdriver.Chrome()
    actions = ActionChains(driver)
    driver.implicitly_wait(10)
    return driver, actions


def login_ta(driver, actions):
    driver.get("https://portal.therapyappointment.com")
    driver.maximize_window()
    actions.send_keys(info["therapyappointment"]["username"])
    actions.send_keys(Keys.TAB)
    actions.send_keys(info["therapyappointment"]["password"])
    actions.send_keys(Keys.ENTER)
    actions.perform()


def go_to_client(firstname, lastname, driver, actions):
    clients_button = driver.find_element(
        By.XPATH, value="//*[contains(text(), 'Clients')]"
    )
    clients_button.click()

    sleep(2)

    actions.send_keys(Keys.ESCAPE)
    actions.perform()

    firstname_label = driver.find_element(By.XPATH, "//label[text()='First Name']")
    firstname_field = firstname_label.find_element(
        By.XPATH, "./following-sibling::input"
    )
    firstname_field.send_keys(firstname)

    lastname_label = driver.find_element(By.XPATH, "//label[text()='Last Name']")
    lastname_field = lastname_label.find_element(By.XPATH, "./following-sibling::input")
    lastname_field.send_keys(lastname)

    search_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Search'")
    search_button.click()

    try:
        driver.find_element(
            By.CSS_SELECTOR, "a[aria-description*='Press Enter to view the profile of"
        ).click()
    except NoSuchElementException:
        return "No client found"


def extract_client_data(driver):
    name = driver.find_element(By.CLASS_NAME, "text-h4").text
    firstname = name.split(" ")[0]
    lastname = name.split(" ")[-1]
    account_number_element = driver.find_element(
        By.XPATH, "//div[contains(normalize-space(text()), 'Account #')]"
    ).text
    account_number = account_number_element.split(" ")[-1]
    birthdate_element = driver.find_element(
        By.XPATH, "//div[contains(normalize-space(text()), 'DOB ')]"
    ).text
    birthdate_str = birthdate_element.split(" ")[-1]
    birthdate = strftime("%Y/%m/%d", strptime(birthdate_str, "%m/%d/%Y"))
    gender_title_element = driver.find_element(
        By.XPATH,
        "//div[contains(normalize-space(text()), 'Gender') and contains(@class, 'v-list-item__title')]",
    )
    gender_element = gender_title_element.find_element(
        By.XPATH, "following-sibling::div"
    )
    sleep(0.5)
    gender = gender_element.text.split(" ")[0]

    age = relativedelta(datetime.now(), datetime.strptime(birthdate, "%Y/%m/%d")).years
    return {
        "firstname": firstname,
        "lastname": lastname,
        "account_number": account_number,
        "birthdate": birthdate,
        "gender": gender,
        "age": age,
    }


def go_docs(driver, actions, client):
    dob = client["birthdate"].split("/")
    year = dob[0]
    month = dob[1]
    day = dob[2]
    docs_button = driver.find_element(By.LINK_TEXT, "Docs & Forms")
    docs_button.click()
    receiving_consent = driver.find_element(
        By.LINK_TEXT, "Receiving Consent to Release of Information"
    )
    receiving_consent.click()
    sleep(5)
    print_options = PrintOptions()
    print_options.orientation = "portrait"
    pdf = driver.print_page(print_options)
    with open(
        f"School Records Requests/{client['firstname']} {client['lastname']} {month}{day}{year} Receiving.pdf",
        "wb",
    ) as file:
        decoded = b64decode(pdf, validate=True)
        file.write(decoded)
    driver.back()
    sending_consent = driver.find_element(
        By.LINK_TEXT, "Sending Consent to Release of Information"
    )
    sending_consent.click()
    sleep(5)
    print_options = PrintOptions()
    print_options.orientation = "portrait"
    pdf = driver.print_page(print_options)
    with open(
        f"School Records Requests/{client['firstname']} {client['lastname']} {month}{day}{year} Sending.pdf",
        "wb",
    ) as file:
        decoded = b64decode(pdf, validate=True)
        file.write(decoded)
    tab_open = driver.find_element(By.CSS_SELECTOR, ".mdi-chevron-double-right")
    tab_open.click()


def download(driver, actions, first, last):
    if go_to_client(first, last, driver, actions) == "No client found":
        return False
    client = extract_client_data(driver)
    go_docs(driver, actions, client)
    return True


def write_file(filename, data):
    data = data.strip("\n")
    empty = False
    with open(filename, "r") as file:
        body = file.read().strip("\n")
        if body == "":
            empty = True
        with open(filename, "w") as file:
            file.write(data if empty else f"{body}, {data}")


def main():
    driver, actions = initialize()
    login_ta(driver, actions)
    with open("records.txt", "r") as file:
        appointments = file.read().split(", ")
    with open("records.txt", "w") as file:
        file.write("")
    for appointment in appointments:
        client = appointment.split(" ")
        firstname = client[0]
        lastname = client[1]
        if not download(driver, actions, firstname, lastname):
            write_file("recordfailures.txt", appointment)
        else:
            write_file("savedrecords.txt", appointment)


main()
