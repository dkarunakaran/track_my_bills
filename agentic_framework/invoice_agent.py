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
from agent_node_helper import process_email_checker, llm_query, get_the_text_data_email, get_JSON
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from bs4 import BeautifulSoup
import time
from pypdf import PdfReader
import os
import json
import sys
parent_dir = ".."
sys.path.append(parent_dir)
import utility
import google_ai_studio_services
from agent_tools import add_task_api_directly, update_sqlitedb_then_task_api


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
    return 'Update Task API directly '

life_tool = Tool(
    name='Update Task API directly on identical data',
    func= meaning_of_life,
    description="Useful for when both data are identical and we just need to update only the Task API directly"
)

def random_num(input=""):
    return 'Update SqliteDB first'

random_tool = Tool(
    name='Update SqliteDB first on non-identical data',
    func= random_num,
    description="Useful for when both data are non-identical and we just need to update the SqliteDB and Task API directly"
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
        '''graph.add_conditional_edges(
            "llm",
            self.exists_action,
            {True: "take_action", False: END}
        )
        graph.add_edge("take_action", END)'''
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)
        self.gen_ai_google = google_ai_studio_services.GoogleAIStudioServices()

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
        return_dict = []
        return_text = []
        text_data = None
        dict_data = None
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
            try:
                proceed, payment_method, download_method, subject, kw_subject, kw_sender = process_email_checker(subjects, payment_methods, download_methods, senders, txt)
                self.logger.info(f"We have read: '{subject}'")
                if proceed == True:
                    self.logger.info(f"Processing: '{subject}' started")
                    payload = txt['payload']

                    # Get the text data from email
                    text_data = get_the_text_data_email(gmail_service, self.logger, self.cfg, msg, payload, download_method)
                    
                    # Find the payment method if it is empty
                    find_payment_method = False
                    if payment_method == "":
                        find_payment_method = True

                    biller_name, due_date, amount, payment_method = llm_query(self.logger, subjects, payment_methods, text_data, payment_method, find_payment_method)

                    dict_data = {
                        'Biller_name': biller_name,
                        'Due_date': due_date,
                        'Amount': amount,
                        'payment_method': payment_method,
                        'kw_subject': kw_subject,
                        'kw_sender': kw_sender
                    }
                    return_dict.append(dict_data)
                    return_text.append(text_data)

            except Exception as err:
                self.logger.error(f"Unexpected {err=}, {type(err)=} at get_email_invoice_node")
                return_dict.append(dict_data)
                return_text.append(text_data)
                
        
        return {'invoices_dict': return_dict, 'invoices_text':return_text}

    def get_drive_invoice_node(self, state: InvoiceAgentState):\
        return {'invoices_dict': [None], 'invoices_text':[None]}
    
    def add_to_sqlite_db_node(self, state: InvoiceAgentState):
        status = False
        for data in state['invoices_dict']:
            if isinstance(data, dict):
                # DB insert operation
                if utility.content_entry_found(data['Biller_name'], data['Due_date'], data['Amount']) == False:
                    utility.insert_content(self.logger, data)
                    status = True
                else:
                    self.logger.info("Data is already exist in SQLite")
            
        return {'add_sqlite_DB': status}
    
    def extract_bank_info_node(self, state: InvoiceAgentState):
        return_data = []
        try:
            index = 0
            for data in state['invoices_text']:
                if data and state['invoices_dict'][index] is not None:
                    invoice_data = state['invoices_dict'][index]
                    self.logger.debug(f"Getting bank details for {invoice_data['kw_subject']} started")
                    group_id = utility.get_group_from_keyword(invoice_data['kw_subject'], invoice_data['kw_sender'])
                    paymentInfo = utility.get_payment_info(group_id)
                    payment_info_prompt= f" Only give {paymentInfo.type} type and no other payment details needed."
                    
                    # Query the LLM to extract the bank info
                    result = self.gen_ai_google.generate_content(self.cfg['invoice_agent']['prompt_for_bank_info']+data+payment_info_prompt)
                    self.logger.debug(f"Data from Google AI Studio: {result}")
                    json_data = get_JSON(result, logger=self.logger)
                    if json_data:
                        json_data['group_id'] = group_id
                        return_data.append(json_data)
                    else:
                        return_data.append(None)
                else:
                    return_data.append(None)
                index += 1

        except Exception as err:
                self.logger.error(f"Unexpected {err=}, {type(err)=} at extract_bank_info_node")
                return_data.append(None)

        return {'bank_info': return_data}
    
    def call_llm_node(self, state: InvoiceAgentState):
        # Compare the data to decide which tool to use
        llm_messages= []
        for info in state['bank_info']:
            proceed = False
            if info:
                existingPaymentInfo = utility.get_payment_info(info['group_id'])
                existing = json.loads(existingPaymentInfo.details)
                existing['type'] = "something" #existingPaymentInfo.type
                existing['group_id'] = existingPaymentInfo.group_id
                existing = sorted(existing.items())
                newPI = sorted(info.items())
                proceed = True
            if proceed:
                custom_msg = f"Existing data:{existing} and new data: {newPI}. Make sure all the keys and values are same on existing and new data."
                self.logger.debug(f"Tool selection msg: {custom_msg}")
                messages = [SystemMessage(content=self.cfg['invoice_agent']['prompt_for_API_tools']),custom_msg]
                message = self.model.invoke(messages)
                llm_messages.append(message)
        
        return {'llm_msg': llm_messages}


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
    tools = [add_task_api_directly, update_sqlitedb_then_task_api]
    initial_state = InvoiceAgentState()
    initial_state['invoices_dict'] = [None]
    initial_state['invoices_text'] = [None]
    agent = InvoiceAgent(tools, system='')
    result = agent.graph.invoke(initial_state)
    print(result)



