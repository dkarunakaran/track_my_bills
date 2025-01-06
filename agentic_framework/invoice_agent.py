from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
import operator
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_ollama import ChatOllama
import yaml
from langchain.agents import Tool
from langchain.tools import BaseTool
import random
from agent_state import InvoiceAgentState
from agent_node_helper import process_email_checker,llm_query
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from bs4 import BeautifulSoup
import time
from pypdf import PdfReader
import os
import sys
parent_dir = ".."
sys.path.append(parent_dir)
import utility



memory = SqliteSaver.from_conn_string(":memory:")
# download = Download()
# generate = Generate()
# Read and process emails - node 1
# download.get_emails()

# Read and check bank details. This is to make sure the bank details has not been changed - node 2
# If there is any change to bank details, wait for the human to proceed to update the bank details, otherwise continute to node 3

# Read and process drive files - node 3
# download.get_drive_files()

# Read and check bank details. This is to make sure the bank details has not been changed - node 4
# If there is any change to bank details, wait for the human to proceed to update the bank details, otherwise continute to node 5

# Create the Task based on the processed data - node 5
# generate.task_API_operation()

# Ref 1: https://www.analyticsvidhya.com/blog/2024/10/setting-up-custom-tools-and-agents-in-langchain/
# Ref 2: https://learn.deeplearning.ai/courses/ai-agents-in-langgraph/lesson/3/langgraph-components
# Ref 3: https://learn.deeplearning.ai/courses/ai-agents-in-langgraph/lesson/7/essay-writer
# Ref 4: https://medium.com/@lorevanoudenhove/how-to-build-ai-agents-with-langgraph-a-step-by-step-guide-5d84d9c7e832

def meaning_of_life(input=""):
    return 'The meaning of life is 42 if rounded but is actually 42.17658'

life_tool = Tool(
    name='Meaning of Life',
    func= meaning_of_life,
    description="Useful for when you need to answer questions about the meaning of life. input should be MOL "
)

def random_num(input=""):
    return random.randint(0,5)

random_tool = Tool(
    name='Random number',
    func= random_num,
    description="Useful for when you need to get a random number. input should be 'random'"
)

class InvoiceAgent:
    def __init__(self, tools, system=""):
        # Creating databse if not existed
        utility.create_database()
        self.logger = utility.logger_helper()
        with open("/app/config.yaml") as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)
        model = ChatOllama(model=self.cfg['invoice_agent']['model_for_API_tool'], base_url=self.cfg['invoice_agent']['host'])
        self.system = system
        graph = StateGraph(InvoiceAgentState)
        graph.add_node("email-invoices", self.get_email_invoice_node)
        graph.add_node("drive-invoices", self.get_drive_invoice_node)
        graph.add_node("add-sqlitedb", self.add_to_sqlite_db_node)
        graph.add_node("extract-bank-info", self.extract_bank_info_node)
        graph.add_node("llm", self.call_llm_node)
        graph.add_node("take_action", self.take_action_node)
        graph.set_entry_point("email-invoices")
        graph.add_edge("email-invoices", "drive-invoices") 
        graph.add_edge("drive-invoices", "add-sqlitedb") 
        graph.add_edge("add-sqlitedb", "extract-bank-info") 
        graph.add_edge("extract-bank-info", "llm") 
        graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "take_action", False: END}
        )
        graph.add_edge("take_action", END)
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def google_api_authentication(self, type:str):

        # Authenticate with GOOGLE API
        creds = utility.authenticate(self.cfg)
        self.logger.info(f"Authenticated for {type} API")

        # Define GMAIL API service
        if type == 'GMAIL':
            return build("gmail", "v1", credentials=creds)
        else:
            return build('drive', 'v3', credentials=creds)
        

    def get_email_invoice_node(self, state: InvoiceAgentState):
        return_data = []
        self.logger.info("Reading the email using GMAIL API")
        subjects, payment_methods, download_methods, senders = utility.get_keywords_data_from_db()
        # Authenticate with GOOGLE API
        creds = utility.authenticate(self.cfg)
        # Define GMAIL API service
        gmail_service = self.google_api_authentication(type='GMAIL')
        result = gmail_service.users().messages().list(maxResults=self.cfg['GOOGLE_API']['no_emails'], userId='me').execute()
        messages = result.get('messages')
        self.logger.info("Got the mails and processing now")
        # messages is a list of dictionaries where each dictionary contains a message id.
        # iterate through all the messages
        for msg in messages:
            # Get the message from its id
            txt = gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
            # Use try-except to avoid any Errors
            multiple_pdf_data = []
            path = None
            try:
                proceed, payment_method, download_method, subject = process_email_checker(subjects, payment_methods, download_methods, senders, txt)
                self.logger.info(f"We have read: '{subject}'")
                if proceed == True:
                    self.logger.info(f"Processing: '{subject}' started")
                    payload = txt['payload']
                    for part in payload['parts']:
                        if part['mimeType'] == 'text/plain' and download_method == 'email_body':
                            text = utility.get_data_email_body()
                        elif part['mimeType'] == 'application/pdf':
                            att_id = part['body']['attachmentId']
                            response = gmail_service.users().messages().attachments().get(userId="me", messageId=msg['id'],id=att_id).execute()
                            file_data = base64.urlsafe_b64decode(response.get('data').encode('UTF-8'))
                            path = self.cfg['dir']+'/'+part['filename']
                            multiple_pdf_data.append({'name': path, 'data': file_data})
                        elif part['mimeType'] == 'multipart/mixed':
                            for p in part['parts']:
                                if p['mimeType'] == 'application/pdf':
                                    att_id = p['body']['attachmentId']
                                    response = gmail_service.users().messages().attachments().get(userId="me", messageId=msg['id'],id=att_id).execute()
                                    file_data = base64.urlsafe_b64decode(response.get('data').encode('UTF-8'))
                                    path = self.cfg['dir']+'/'+p['filename']
                                    multiple_pdf_data.append({'name': path, 'data': file_data})

                    if len(multiple_pdf_data) > 0:
                        self.logger.info("Saving the attachments to a folder")
                        content = ""
                        for file_data in multiple_pdf_data:
                            file_path = file_data['name']
                            with open(file_data['name'], 'wb') as f:
                                f.write(file_data['data'])
                            time.sleep(3)
                            self.logger.info(f"file: {file_path} is processing")
                            # Creating a pdf reader object
                            reader = PdfReader(file_path)
                            content = ""
                            for page in reader.pages:
                                # Extracting text from page
                                content += page.extract_text()
                                content += '\n'
                            os.remove(file_path)
                            self.logger.info(f"file: {file_path} is removed")  
                        text = content

                    # Find the payment method if it is empty
                    find_payment_method = False
                    if payment_method == "":
                        find_payment_method = True

                    biller_name, due_date, amount, payment_method = llm_query(self.logger, subjects, payment_methods, text, payment_method, find_payment_method)
            
                    return_data.append({
                        'Biller_name': biller_name,
                        'Due_date': due_date,
                        'Amount': amount,
                        'payment_method': payment_method
                    })

            except Exception as err:
                self.logger.error(f"Unexpected {err=}, {type(err)=}")
                return_data.append({})
        
        
        return {'invoices': return_data}

    def get_drive_invoice_node(self, state: InvoiceAgentState):

        return {'invoices': ["hi2"]}
    
    def add_to_sqlite_db_node(self, state: InvoiceAgentState):

        return {'add_sqlite_DB': True}
    
    def extract_bank_info_node(self, state: InvoiceAgentState):

        return {'bank_info': ['sdds','fgfg']}
    
    def call_llm_node(self, state: InvoiceAgentState):
        # Compare the data to decide which tool to use
        messages = [SystemMessage(content=self.cfg['invoice_agent']['prompt_for_API_tools']),"What is the meaning of life?"]
        message = self.model.invoke(messages)
        
        return {'llm_msg': message}

    def exists_action(self, state: InvoiceAgentState):
        result = state['llm_msg']
        return len(result.tool_calls) > 0
    
    def take_action_node(self, state: InvoiceAgentState):
        tool_calls = state['llm_msg'].tool_calls
        results = []
    
        for t in tool_calls:
            print(f"Calling: {t}")
            if not t['name'] in self.tools:      # check for bad tool name from LLM
                print("\n ....bad tool name....")
                result = "bad tool name, retry"  # instruct LLM to retry if bad
            else:
                result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))
        print("Back to the model!")
    
        return {'api_operation': results}

if __name__ == "__main__":
    tools = [random_tool, life_tool]
    initial_state = InvoiceAgentState()
    initial_state['invoices'] = ['None']
    agent = InvoiceAgent(tools, system='')
    result = agent.graph.invoke(initial_state)
    print(result)



