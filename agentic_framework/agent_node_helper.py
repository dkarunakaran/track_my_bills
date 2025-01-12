from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from bs4 import BeautifulSoup
import yaml
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
from pypdf import PdfReader
import os

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
    kw_sender = kw_subject = None
    if len(res_sub) > 0:
        method_index_sub = res_sub[0]
        payment_method = payment_methods[method_index_sub]
        download_method = download_methods[method_index_sub]
        kw_subject = subjects[method_index_sub]

    # You can have multiple senders, either from the company or I forward to the email, so relying on subject index is not practical
    res_send = list(compress(range(len(sender_found)), sender_found))
    if len(res_send) > 0:
        method_index_send = res_send[0]
        kw_sender = senders[method_index_send]

    if True in subject_found and True in sender_found:
        proceed = True
    
    return proceed, payment_method, download_method, subject, kw_subject, kw_sender

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

def get_the_text_data_email(gmail_service, logger, cfg, msg, payload, download_method):
    multiple_pdf_data = []
    path = None
    for part in payload['parts']:
        if part['mimeType'] == 'text/plain' and download_method == 'email_body':
            text = utility.get_data_email_body()
        elif part['mimeType'] == 'application/pdf':
            att_id = part['body']['attachmentId']
            response = gmail_service.users().messages().attachments().get(userId="me", messageId=msg['id'],id=att_id).execute()
            file_data = base64.urlsafe_b64decode(response.get('data').encode('UTF-8'))
            path = cfg['dir']+'/'+part['filename']
            multiple_pdf_data.append({'name': path, 'data': file_data})
        elif part['mimeType'] == 'multipart/mixed':
            for p in part['parts']:
                if p['mimeType'] == 'application/pdf':
                    att_id = p['body']['attachmentId']
                    response = gmail_service.users().messages().attachments().get(userId="me", messageId=msg['id'],id=att_id).execute()
                    file_data = base64.urlsafe_b64decode(response.get('data').encode('UTF-8'))
                    path = cfg['dir']+'/'+p['filename']
                    multiple_pdf_data.append({'name': path, 'data': file_data})

    if len(multiple_pdf_data) > 0:
        logger.info("Saving the attachments to a folder")
        content = ""
        for file_data in multiple_pdf_data:
            file_path = file_data['name']
            with open(file_data['name'], 'wb') as f:
                f.write(file_data['data'])
            time.sleep(3)
            logger.info(f"file: {file_path} is processing")
            # Creating a pdf reader object
            reader = PdfReader(file_path)
            content = ""
            for page in reader.pages:
                # Extracting text from page
                content += page.extract_text()
                content += '\n'
            os.remove(file_path)
            logger.info(f"file: {file_path} is removed")  
        text = content
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

def get_JSON(response:str, logger=None): 
    try:
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
    except Exception as err:
        if logger:
            logger.error(f"Unexpected {err=}, {type(err)=}")
        json_data = None

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

def task_API_operation(logger, task_service, session=None):
    try:
        _return = None
        contents = utility.get_all_contents(session=session)
        logger.debug(f"Contents from SQLite: {contents}")
        if len(contents) > 0:
            tasklist_id = get_tasklist_id('Payment', task_service)
            try:
                if tasklist_id is not None:
                    for content in contents:
                        task_id = get_task_id(logger, task_service, tasklist_id=tasklist_id, task_name=content.name)
                        logger.debug(f"Task_id: {task_id}")
                        date_str = content.date
                        date_format = '%Y-%m-%d'
                        date_obj = datetime.strptime(date_str, date_format).astimezone()
                        logger.debug(f"Date object: {date_obj.isoformat()}")
                        notes = f"Amount: {content.amount}\nPayment: {content.payment}"
                        taskdata = { 'title': content.name, 'due': date_obj.isoformat(),'notes': notes}
                        if task_id is None:
                            logger.info(f"TASK API insert operation of '{content.name}' started")
                            result = task_service.tasks().insert(tasklist=tasklist_id, body=taskdata).execute()
                        else:
                            logger.info(f"TASK API update operation '{content.name}' started")
                            result = task_service.tasks().patch(tasklist=tasklist_id, task=task_id, body=taskdata).execute()
                        logger.debug(result)
                        # Insted delete, do the update operation
                        #self.delete_content(id=content[0])
                        _return = utility.update_content(id=content.id, session=session)
                logger.info("All Tasks are created/updated")
            except Exception as err:
                logger.error(f"Unexpected {err=}, {type(err)=} at task_API_operation - first")
        else:
            logger.info("No task data found in SQLite at task_API_operation - second")
    except HttpError as error:
        logger.critical(f"An error occurred: {error} - at task_API_operation - third")
    
    return _return

def get_tasklist_id(keyword, task_service):
        # List all the tasklists for the account.
    id = None
    lists = task_service.tasklists().list().execute()
    for item in lists['items']:
        if item['title'] == keyword:
            id = item['id']
            break

    return id

def get_task_id(logger, task_service, tasklist_id=None, task_name=None):
    id = None
    results = task_service.tasks().list(tasklist=tasklist_id).execute()
    tasks = results.get('items', [])
    logger.debug(f"All tasks: {tasks}")
    for task in tasks:
        if task['title'] == task_name:
            id = task['id']
            break
        
    return id




