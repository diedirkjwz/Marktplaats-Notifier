from __future__ import print_function

import base64
import os.path
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.remote_connection import LOGGER, logging
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

options = Options()
options.headless = True
options.add_argument("--log-level=3")
LOGGER.setLevel(logging.ERROR)
SCOPES = ['https://mail.google.com/']  # all permissions


def authenticate():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes=SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())


def notify_via_email(keywords):
    """
    Create and send an email message
    Print the returned  message id
    Returns: Message object, including message id
    """
    print("Sending message..", end="\r", flush=True)
    creds = Credentials.from_authorized_user_file('token.json', scopes=SCOPES)

    try:
        service = build('gmail', 'v1', credentials=creds)
        message = EmailMessage()

        message['To'] = 'olledejong@gmail.com'
        message['From'] = 'mijn.notifier@gmail.com'
        message['Subject'] = 'Potential listing of interest'

        message.set_content(
            f'One of the following keywords was encountered while scraping the Marktplaats page:\n\n {keywords}'
        )

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        service.users().messages().send(userId="me", body=create_message).execute()
        print("Message sent!")

    except HttpError as error:
        print(F'An error occurred while sending the email: {error}')


def check_for_change(driver, old_ads, keywords):
    new_ads = driver.find_elements(By.XPATH, "//UL[contains(@class, 'hz-Listing--list-item')]")

    # check if there are changes
    if old_ads != new_ads:
        print("Changes found")
        return True
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


def get_user_settings():
    keywords = []
    print("Welcome! This script can be run in multiple console instances in order to track multiple pages.")
    url = input("Please paste the Marktplaats link of the page you'd like to check for potential promising listings:\n")
    keyword = 'placeholder'
    print("\nThis program works by looking for words of interest that might appear in a new listing. It will ask you "
          "for these shortly, and you have to provide at least one. When you're done, simply enter the letter: q\n")
    while len(keywords) == 0:
        while not keyword == 'q':
            keyword = input("Enter a keyword of interest: ")
            keywords.append(keyword)

    print("\nThank you! Program will notify you once an advertisement of interest is encountered.")

    return url, keywords


def main():
    url, keywords = get_user_settings()

    try:
        authenticate()
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        driver.implicitly_wait(5)
        driver.find_element(By.XPATH, "//BUTTON[contains(@class, 'gdpr-consent-button')]").click()
        old_ads = driver.find_elements(By.XPATH, "//UL[contains(@class, 'hz-Listing--list-item')]")

        while not check_for_change(driver, old_ads, keywords):
            sleep(60)
            driver.refresh()
        else:
            notify_via_email(keywords)
            main()

    except Exception as e:
        print(f"Something went wrong, quitting.. error message:\n{e}")


if __name__ == '__main__':
    main()
