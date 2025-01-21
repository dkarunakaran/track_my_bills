from playwright.sync_api import sync_playwright
from googleapiclient.discovery import build
import yaml
import re
import base64
from bs4 import BeautifulSoup
from langchain_ollama import ChatOllama
#from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import create_sync_playwright_browser
from langchain import hub
from langchain.agents import AgentType, initialize_agent
from langchain.agents import AgentExecutor, create_react_agent, create_openai_tools_agent
from langchain_openai import ChatOpenAI
import getpass
import os

import sys
parent_dir = ".."
sys.path.append(parent_dir)
import utility
import secret

#from langchain_community.agent_toolkits import PlayWrightBrowserToolkit #This is the replaced import
from custom_playwright_toolkit import PlayWrightBrowserToolkit

from langchain_community.tools.playwright.utils import (
    create_sync_playwright_browser,  # A synchronous browser is available, though it isn't compatible with jupyter.\n",      },
)

# Ref 1: https://medium.com/@abhyankarharshal22/mastering-browser-automation-with-langchain-agent-and-playwright-tools-c70f38fddaa6
# Ref 2: 
class Automation:
    def __init__(self):
        with open("/app/config.yaml") as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)
        self.logger = utility.logger_helper()

        self.secret = secret.Secret()

        # Authenticate with GOOGLE API
        creds = utility.authenticate(self.cfg)
        self.gmail_service = build("gmail", "v1", credentials=creds)

        if not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = self.secret.open_ai_token

        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0) 
        #self.model = ChatOllama(model=self.cfg['invoice_agent']['model_for_API_tool'], base_url=self.cfg['invoice_agent']['host'])
        
        sync_browser = create_sync_playwright_browser()
        toolkit = PlayWrightBrowserToolkit.from_browser(sync_browser=sync_browser)
        self.tools = toolkit.get_tools()

        #self.prompt = hub.pull("hwchase17/react")
        self.prompt = hub.pull("hwchase17/openai-tools-agent")

    def test(self):
        agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        #agent = create_openai_tools_agent(self.model, self.tools, self.prompt)
        agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        agent_executor.invoke({"input": "Go to https://www.google.com, search for Elon Musk and spaceX using Search label textarea HTML element you find from that page, click google search button and return the summary of results you get. Use fill tool to fill in fields and print out url at each step."})

        """agent_chain = initialize_agent(
            self.tools,
            self.model,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )

        result = agent_chain.run("Go to https://python.langchain.com/v0.2/docs/integrations/toolkits/playwright/ and give me summary of all tools mentioned on the page you get. Print out url at each step.")
        print(result)"""
        
    
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

                # Browser tools for langraph: https://python.langchain.com/docs/integrations/tools/playwright/

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
    automate.test()