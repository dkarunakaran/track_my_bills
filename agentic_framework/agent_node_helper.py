import importlib
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from bs4 import BeautifulSoup
import yaml
from agent_state import InvoiceAgentState
from itertools import compress 
import time
import io
from tqdm import tqdm
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image
import pytesseract
import sqlite3
import re

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

