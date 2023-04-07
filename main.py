from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.remote_connection import LOGGER, logging
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from plyer import notification

options = Options()
options.headless = True
options.add_argument("--log-level=3")
LOGGER.setLevel(logging.ERROR)

to_check = "https://www.marktplaats.nl/l/computers-en-software/processors/#sortBy:SORT_INDEX|sortOrder:DECREASING"
keywords = ["5700X", "5700 X"]


def check_for_change(driver, old_ads):
    new_ads = driver.find_elements(By.XPATH, "//UL[contains(@class, 'hz-Listing--list-item')]")

    # check if there are changes
    if old_ads != new_ads:
        print("Changes found")
        set_a = set(old_ads)
        set_b = set(new_ads)
        # if there are changes, then check if the new add contains a word of interest
        print(f"The differences in the list are: {set_b - set_a}")
        for add in set_b - set_a:
            if any([kw in add for kw in keywords]):
                return True

    # if no changes, or the changes did not contain a keyword
    print("No changes found")
    return False


def notify():
    notification_title = 'There might be a new listing!'
    notification_message = to_check

    notification.notify(
        title=notification_title,
        message=notification_message,
        app_icon=None,
        timeout=10,
        toast=False
    )


def main():
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(to_check)
        driver.implicitly_wait(5)
        driver.find_element(By.XPATH, "//BUTTON[contains(@class, 'gdpr-consent-button')]").click()
        old_ads = driver.find_elements(By.XPATH, "//UL[contains(@class, 'hz-Listing--list-item')]")
        while not check_for_change(driver, old_ads):
            sleep(60)
            driver.refresh()
        else:
            notify()
            main()
    except Exception as e:
        print(f"Something went wrong, quitting.. error message:\n{e}")


if __name__ == '__main__':
    main()
