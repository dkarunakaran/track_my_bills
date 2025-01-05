import importlib
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from bs4 import BeautifulSoup
import yaml
#from ..utility import logger_helper, authenticate, get_keywords_data_from_db
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


def get_emails_invoice_node():
    """logger = utility.logger_helper()
    logger.info("Reading the email using GMAIL API")
    
    with open("/app/config.yaml") as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
        
    subjects, payment_methods, download_methods, senders = utility.get_keywords_data_from_db()

    # Authenticate with GOOGLE API
    creds = utility.authenticate(cfg)

    # Define GMAIL API service
    gmail_service = build("gmail", "v1", credentials=creds)
    logger.info("Authenticated")"""
    pass