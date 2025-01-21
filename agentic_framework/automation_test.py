from playwright.sync_api import sync_playwright
from googleapiclient.discovery import build
import yaml
import re
import base64
from bs4 import BeautifulSoup

import sys
parent_dir = ".."
sys.path.append(parent_dir)
import utility
import google_ai_studio_services

class Automation:
    def __init__(self):
        with open("/app/config.yaml") as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)
        self.logger = utility.logger_helper()

        # Authenticate with GOOGLE API
        creds = utility.authenticate(self.cfg)
        self.gmail_service = build("gmail", "v1", credentials=creds)
        self.gen_ai_google = google_ai_studio_services.GoogleAIStudioServices()
    
    def get_emails(self):
        result = self.gmail_service.users().messages().list(maxResults=self.cfg['GOOGLE_API']['no_emails'], userId='me').execute()
        messages = result.get('messages')
        self.logger.info("Got the mails and processing now")
        # messages is a list of dictionaries where each dictionary contains a message id.
        # iterate through all the messages
        for msg in messages:
            # Get the message from its id
            txt = self.gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
            
            # Get value of 'payload' from dictionary 'txt'
            payload = txt['payload']
            headers = payload['headers']
            subject = ""

            # Look for Subject and Sender Email in the headers
            for d in headers:
                if d['name'] == 'Subject':
                    subject = d['value']
                if d['name'] == 'From':
                    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', d['value'])
                    sender = match.group(0)

            # Code for getting only email we want to track
            proceed = False
            subjects = ['Timesheets to sign for Kids Early Learning Family Day Care']
            subject_found = [True if s in subject else False  for s in subjects]
            if True in subject_found:
                proceed = True

            if proceed:
                self.logger.info(f"Processing: '{subject}' started")
                data = payload['body']['data']
                data = data.replace("-","+").replace("_","/")
                decoded_data = base64.b64decode(data)
                soup = BeautifulSoup(decoded_data , "lxml")
                html_content = str(soup)            
                prompt1 = "Extrach the link from this text:"
                prompt2 = "" #" Only give the link and no other text."
                # Query the LLM to extract the link
                result_with_url = self.gen_ai_google.generate_content(prompt1+html_content+prompt2)
                print(result_with_url)
                


        
    def browser_run(self):
        with sync_playwright() as p:
            # Channel can be "chrome", "msedge", "chrome-beta", "msedge-beta" or "msedge-dev".
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("http://playwright.dev")
            print(page.title())
            browser.close()


if __name__ == "__main__":
    automate = Automation()
    automate.get_emails()