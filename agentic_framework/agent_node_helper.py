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
import io
from tqdm import tqdm
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image
import pytesseract

parent_dir = ".."
sys.path.append(parent_dir)

import utility


def process_email_checker(session, subjects, senders, txt):
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
    download_method = payment_method = ""
    keyword = kw_sender = kw_subject = None
    if True in subject_found and True in sender_found:
        proceed = True
        #Get Payment Method and Download Method 
        keyword = utility.get_keyword_subject_sender(subject, sender, session)
        if keyword != None:
            dm = utility.get_download_method(keyword.download_method_id, session)
            pm = utility.get_payment_method(keyword.payment_method_id, session)
            download_method = dm.name
            payment_method = pm.name
            kw_subject = keyword.subject 
            kw_sender = keyword.sender 
    
    return proceed, payment_method, download_method, subject, kw_subject, kw_sender, keyword

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


def get_json_data_from_text_email(logger, content):
    result = llm_query(logger, content)
    
    return result['Biller_name'], result['Due_date'], result['Amount']

def llm_query(logger, content):
    logger.info("Got the Data, now requesting LLM to extract the information")
    response = ollama_query(content)  
    logger.debug(f"data from LLM: {response}")
    result = get_JSON(response)
    logger.info(f"Got the JSON ecncoded data: {result}")

    return result 

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

def get_drive_files(drive_service, logger, cfg, files):
    text = []
    for file in files:
        if str(file["mimeType"]) == str("application/pdf"):
            logger.info(f"Downloading: {file['name']} is started") 
            downloadfiles(drive_service, logger, cfg, file['id'], file['name'])
            drive_service.files().delete(fileId=file['id']).execute()
            logger.info(f"file: {file['name']} is deleted from Google Drive") 
            file_path=cfg['dir']+"/"+file['name']
            if os.path.exists(file_path):
                logger.info(f"file: {file_path} is processing")
                # Creating a pdf reader object
                reader = PdfReader(file_path)
                content = ""
                for page in reader.pages:
                    # Extracting text from page
                    content += page.extract_text()
                    content += '\n'
                text.append(content)
                os.remove(file_path)
                logger.info(f"file: {file_path} is removed")  

        if str(file["mimeType"]) == str("image/png"):
            logger.info(f"Downloading: {file['name']} is started") 
            downloadfiles(drive_service, logger, cfg, file['id'], file['name'])
            drive_service.files().delete(fileId=file['id']).execute()
            logger.info(f"File: {file['name']} is deleted from Google Drive") 
            # perform OCR on the processed image
            content = pytesseract.image_to_string(Image.open(cfg['dir']+"/"+file['name']))
            text.append(content)
            file_path=cfg['dir']+"/"+file['name']
            os.remove(file_path)
            logger.info(f"file: {file_path} is removed")  

        if str(file["mimeType"]) == str("image/jpeg"):
            logger.info(f"Downloading: {file['name']} is started") 
            downloadfiles(drive_service, logger, cfg, file['id'], file['name'])
            drive_service.files().delete(fileId=file['id']).execute()
            logger.info(f"File: {file['name']} is deleted from Google Drive") 
            file_path=cfg['dir']+"/"+file['name']
            im = Image.open(file_path)
            replace_path = cfg['dir']+"/"+"temp.png"
            im.save(replace_path)
            # perform OCR on the processed image
            content = pytesseract.image_to_string(Image.open(replace_path))
            text.append(content)
            os.remove(file_path)
            os.remove(replace_path)
            logger.info(f"file: {file_path} is removed")  

    return text

def downloadfiles(drive_service, logger, cfg, file_id, dfilespath):
    folder = cfg['dir']
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    pbar = tqdm(total=100, ncols=70)
    while done is False:
        status, done = downloader.next_chunk()
        if status:
            pbar.update(int(status.progress() * 100) - pbar.n)
    pbar.close()
    with io.open(folder + "/" + dfilespath, "wb") as f:
        fh.seek(0)
        f.write(fh.read())
    logger.info(f"Downloading: {dfilespath} is finished") 

def get_json_data_from_text_drive(logger, session, text_data):
    _return = []
    for content in text_data:
        group_id = None
        result = llm_query(logger, content)
        title = result['Biller_name']
        keyword = utility.get_keyword_on_title(title, session)
        if keyword is None:
            differentName = utility.get_different_names_on_title(title, session)
            if differentName != None:
                group_id = differentName.group_id
        else:
            group_id = keyword.group_id
        if group_id != None:
            pass
    return _return
            
    
    