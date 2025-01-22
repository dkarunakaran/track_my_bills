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
from langchain.agents import AgentExecutor, create_react_agent, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
import os

#from langchain_community.agent_toolkits import PlayWrightBrowserToolkit #This is the replaced import
from custom_playwright_toolkit import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import (
    create_sync_playwright_browser,  # A synchronous browser is available, though it isn't compatible with jupyter.\n",      },
)
from agent_node_helper import get_JSON


import sys
parent_dir = ".."
sys.path.append(parent_dir)
import utility
import secret
import google_ai_studio_services

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
        self.prompt = hub.pull("ebahr/openai-tools-agent-with-context:3b3e6baf") 
        self.conext_manger_model = google_ai_studio_services.GoogleAIStudioServices()
        agent = create_openai_tools_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    def test(self):
        # Context Manger 
        system_message_context_manager = """
            You are expert in finding the context on what is this user messgae about. We have three context: 'google search', 'arxiv search', and 'not found'. Select one of these. If you can't determine output then return as 'not found'. Return in JSON format an no other text required.
            For example:
            {
                'context': 'arxiv search'
            }
        """
        input_msg = """
            Go to https://duckduckgo.com, search for insurance usecases in connected vehicles using input box you find from that page, click search button and return the summary of results you get. Use fill tool to fill in fields and print out url at each step.
        """

        result = self.conext_manger_model.generate_content(system_message_context_manager+input_msg)
        json_text = get_JSON(result)
        self.logger.info(f"Context of the automation: {json_text['context']}")
        context = ''
        if json_text['context'] == 'google search':
            context = "If it is google, look for textarea html element instead of input element for filling."

        
        self.agent_executor.invoke({"chat_history":[], "agent_scratchpad":"", "context": context,"input": input_msg})
       
    
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
            #subjects = ['Timesheets to sign for Kids Early Learning Family Day Care']
            subjects = ['Open-Source Rival to OpenAI']
            subject_found = [True if s in subject else False  for s in subjects]
            if True in subject_found:
                proceed = True

            if proceed:
                self.logger.info(f"Processing: '{subject}' started")
                data = payload['parts'][0]['body']['data']
                data = data.replace("-","+").replace("_","/")
                decoded_data = base64.b64decode(data)
                soup = BeautifulSoup(decoded_data , "lxml")
                html_content = str(soup)            
                #prompt1 = "Extrach the link from this text:"
                #prompt2 = "" #" Only give the link and no other text."
                # Query the LLM to extract the link
                #result_with_url = self.gen_ai_google.generate_content(prompt1+html_content+prompt2)
                # Browser tools for langraph: https://python.langchain.com/docs/integrations/tools/playwright/
                #print(result_with_url)

                context = ""
                input_msg = "GO through this content and find the url and navigate to the URLs in the content and summarise the text from there. As a final result, give list of urls in the content and their summary. Content:"+html_content
                self.agent_executor.invoke({"chat_history":[], "agent_scratchpad":"", "context": context,"input": input_msg})
                


        
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