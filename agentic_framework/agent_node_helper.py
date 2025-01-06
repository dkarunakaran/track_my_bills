from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from bs4 import BeautifulSoup
import yaml
from agent_state import InvoiceAgentState
from itertools import compress 
import time
import re
import json
from datetime import datetime
from ollama import Client
import yaml
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
import sys

parent_dir = ".."
sys.path.append(parent_dir)

import utility


def process_email_checker(subjects, payment_methods, download_methods, senders, txt):
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
    subject_found = [True if s in subject else False  for s in subjects]
    sender_found = [True if sen in sender else False  for sen in senders]
    res_sub = list(compress(range(len(subject_found)), subject_found))
    download_method = ""
    payment_method = ""
    if len(res_sub) > 0:
        method_index = res_sub[0]
        payment_method = payment_methods[method_index]
        download_method = download_methods[method_index]

    if True in subject_found and True in sender_found:
        proceed = True
    
    return proceed, payment_method, download_method, subject

def get_data_email_body(part):
    text = ""
    if 'data' in part['body']:
        data = part['body']['data']
        data = data.replace("-","+").replace("_","/")
        decoded_data = base64.b64decode(data)

        # Now, the data obtained is in lxml. So, we will parse
        # it with BeautifulSoup library
        soup = BeautifulSoup(decoded_data , "lxml")
        text = soup.get_text()
    
    return text


def llm_query(logger, subjects_all, payment_methods_all, content, payment_method, find_payment_method = False):
    logger.info("Got the Data, now requesting LLM to extract the information")
    response = ollama_query(content)  
    logger.debug(f"data from LLM: {response}")
    result = get_JSON(response)
    logger.info(f"Got the JSON ecncoded data: {result}")
    if find_payment_method == True:
        logger.info("Searching for the payment method")
        title = result['Biller_name']
        # To find the payment method
        title_found = [True if title in s else False  for s in subjects_all]
        res_sub = list(compress(range(len(title_found)), title_found))
        payment_method = ""
        if len(res_sub) > 0:
            method_index = res_sub[0]
            payment_method = payment_methods_all[method_index]
            logger.info(f"Found the payment method: {payment_method}")


    return result['Biller_name'], result['Due_date'], result['Amount'], payment_method

    # DB insert operation
    '''if utility.content_entry_found(result['Biller_name'], result['Due_date'], result['Amount']) == False:
        created_datetime = datetime.now(pytz.timezone('Australia/Sydney'))
        self.sql_db.cursor.execute("""INSERT INTO Content (name, date, amount, payment, processed, created_date) VALUES (?,?,?,?,?,?)""", [result['Biller_name'], result['Due_date'], result['Amount'], payment_method, 0, created_datetime])
        self.sql_db.conn.commit()
        self.logger.info("Data inserted to SQLite")
    else:
        self.logger.info("Data is already exist in SQLite")'''

def get_JSON(response:str): 
    # Find the index of the first opening curly brace '{' within the extracted_text
    start_index = response.find('{') + 1
    # Extract text from extracted_text starting from the position after the first '{'
    text_after_first_brace = response[start_index:]
    # Find the index of the last closing curly brace '}' within the text_after_first_brace
    end_index = text_after_first_brace.rfind('}')
    # Extract text from text_after_first_brace up to the position of the last '}'
    text_before_last_brace = text_after_first_brace[:end_index]
    # Concatenate the extracted text with braces to ensure a valid JSON format
    result = "{" + text_before_last_brace + "}"
    # Replace single quotes "'" with double quotes '"' in the result
    output_string = result.replace("'", '"')
    # Use regular expression substitution to remove backslashes '\'
    output_string2 = re.sub(r'\\', '', output_string)
    json_data = json.loads(output_string2)

    return json_data


def ollama_query(text):
    
    with open("/app/config.yaml") as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)

    instruction = f"""
            Your task is to extract invoice data from the Input text.

            Reply Structures:
            - Amount 
            - Due_date 
            - Biller_name   

            Reply with valid json. Please make sure Due_date is in year-month-day format and Biller_name has only a few words
        """
    instruction_text = (
        f"Below is an instruction that describes a task. "
        f"Write a response that appropriately completes the request."
        f"\n\n### Instruction:\n{instruction}"
    )

    input_text = "\n\n### Input:\n'{context}'"
    desired_response = f"\n\n### Response:\n"
    template = instruction_text + input_text + desired_response

    prompt = ChatPromptTemplate.from_template(template)
    model = OllamaLLM(model=cfg['ollama']['model'], base_url=cfg['ollama']['host'])
    chain = prompt | model

    return chain.invoke({"context": text})



