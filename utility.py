import logging
import yaml
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import sqlite3
import csv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_
import time

import sys
parent_dir = ".."
sys.path.append(parent_dir)
# Need to import all model files to create table
import models.content
import models.base
import models.payment_methods
import models.download_methods
import models.keywords



# Ref - https://medium.com/pythoneers/beyond-print-statements-elevating-debugging-with-python-logging-715b2ae36cd5

def logger_helper():
  with open("/app/config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

  logger = logging.getLogger('my_logger')
  logger.setLevel(logging.DEBUG)  # Capture all messages of debug or higher severity

  ### File handler for errors
  # Create a file handler that writes log messages to 'error.log'
  file_handler = logging.FileHandler('error.log') 
  # Set the logging level for this handler to ERROR, which means it will only handle messages of ERROR level or higher
  file_handler.setLevel(logging.ERROR)  

  ### Console handler for info and above
  # Create a console handler that writes log messages to the console
  console_handler = logging.StreamHandler()  
  
  if cfg['debug'] == True:
      console_handler.setLevel(logging.DEBUG)  
  else:
      # Set the logging level for this handler to INFO, which means it will handle messages of INFO level or higher
      console_handler.setLevel(logging.INFO)  

  ### Set formats for handlers
  # Define the format of log messages
  formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s') 
  # Apply the formatter to the file handler 
  file_handler.setFormatter(formatter) 
  # Apply the formatter to the console handler
  console_handler.setFormatter(formatter)  

  ### Add handlers to logger
  # Add the file handler to the logger, so it will write ERROR level messages to 'error.log'
  logger.addHandler(file_handler)  
  # Add the console handler to the logger, so it will write INFO level messages to the console
  logger.addHandler(console_handler)  

  # Now when you log messages, they are directed based on their severity:
  #logger.debug("This will print to console")
  #logger.info("This will also print to console")
  #logger.error("This will print to console and also save to error.log")

  return logger

def authenticate(cfg):
  # If modifying these scopes, delete the file token.json.
  SCOPES = cfg['GOOGLE_API']['scopes']

  # Authenticate
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("/app/token.json"):
    creds = Credentials.from_authorized_user_file("/app/token.json", SCOPES)

  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "/app/credentials.json", SCOPES
      )
      creds = flow.run_console(port=0)
    # Save the credentials for the next run
    with open("/app/token.json", "w") as token:
      token.write(creds.to_json())

  return creds

def create_database():
  Session = sessionmaker(bind=models.base.engine)
  session = Session()
  models.base.Base.metadata.create_all(models.base.engine) 
  time.sleep(2)
  PaymentMethods = models.payment_methods.PaymentMethods
  DownloadMethods = models.download_methods.DownloadMethods
  Keywords = models.keywords.Keywords
  
  # Adding Default values
  filename = '/app/data/initial_keywords.csv' 
  with open(filename, 'r') as file:
    reader = csv.DictReader(file)
    data = [row for row in reader]

  # Inserting the payment methods and download methods to its respective tables
  payment = []
  download = []
  for row in data:
      payment.append(row['payment']) 
      download.append(row['download_method']) 

  # Making the values unique
  payment = set(payment)
  download = set(download)

  # Inserting payment methods to its table if the value is not present in the db.
  p_methods = session.query(PaymentMethods).all()
  if len(p_methods) > 0:
      for name in payment:
        # Query data using 'like' and 'where'
        search_term = f"{name}%"  # Search for names
        id = session.query(PaymentMethods).filter(PaymentMethods.name.like(search_term)).first() 
        # No such method in the db 
        if id is None:
            # Create a new PM object
            pm = PaymentMethods(name=name)
            # Add the new PM to the session
            session.add(pm)
            # Commit the changes to the database
            session.commit()       
  else:
      for name in payment:
        # Create a new PM object
        pm = PaymentMethods(name=name)
        # Add the new PM to the session
        session.add(pm)
        # Commit the changes to the database
        session.commit() 
  
  # Inserting download methods to its table if the value is not present in the db.
  d_methods = session.query(DownloadMethods).all()
  if len(d_methods) > 0:
      for name in download:
        # Query data using 'like' and 'where'
        search_term = f"{name}%"  # Search for names
        id = session.query(DownloadMethods).filter(DownloadMethods.name.like(search_term)).first() 
        # No such method in the db 
        if id is None:
            # Create a new DM object
            dm = DownloadMethods(name=name)
            # Add the new DM to the session
            session.add(dm)
            # Commit the changes to the database
            session.commit()         
  else:
      for name in download:
        # Create a new DM object
        dm = DownloadMethods(name=name)
        # Add the new DM to the session
        session.add(dm)
        # Commit the changes to the database
        session.commit() 

  # Insert keywords if they are not in db
  for row in data:
      # Query data using 'like' and 'where'
      sub_search_term = f"%{row['subject']}%"  # Search for subjects
      sender_search_term = f"%{row['sender']}%"  # Search for sender
      keyword_id = session.query(Keywords).filter(and_(Keywords.subject.like(sub_search_term), Keywords.sender.like(sender_search_term))).first() 

      # No such keywords in the db 
      if keyword_id is None:
          
          # Get the payment_id
          search_term = f"{row['payment']}%"  # Search for names
          payment= session.query(PaymentMethods).filter(PaymentMethods.name.like(search_term)).first() 
          if payment:
            payment_id = payment.id
          else:
            raise Exception("No payment id found")
             

          # Get the download_id
          search_term = f"{row['download_method']}%"  # Search for names
          download = session.query(DownloadMethods).filter(DownloadMethods.name.like(search_term)).first() 
          if download:
            download_id = download.id
          else:
            raise Exception("No payment id found")
          

          # Create a new KW object
          kw = Keywords(subject=row['subject'], payment_method_id=payment_id,download_method_id=download_id,sender=row['sender'])
          # Add the new KW to the session
          session.add(kw)
          # Commit the changes to the database
          session.commit() 
          session.close()


def get_keywords_data_from_db():
  subjects = []
  payment_methods = []
  download_methods = []
  senders = []
  Session = sessionmaker(bind=models.base.engine)
  session = Session()
  PaymentMethods = models.payment_methods.PaymentMethods
  DownloadMethods = models.download_methods.DownloadMethods
  Keywords = models.keywords.Keywords
  keywords = session.query(Keywords).all()
  for keyword in keywords:
    # Getting subject
    subjects.append(keyword.subject)

    # Getting payment name
    payment= session.query(PaymentMethods).filter(PaymentMethods.id == keyword.payment_method_id).first() 
    payment_methods.append(payment.name)

    # Getting download name
    download= session.query(DownloadMethods).filter(DownloadMethods.id == keyword.download_method_id).first() 
    download_methods.append(download.name)

    # Getting sender
    senders.append(keyword.sender)

  return subjects, payment_methods, download_methods, senders

def content_entry_found(name, date, amount):
    query = f"SELECT id FROM Content where name LIKE '%{name}%' and date LIKE '%{date}%' LIMIT 1"
    self.sql_db.cursor.execute(query)
    content_id = self.sql_db.cursor.fetchall()
    status = True
    if len(content_id) == 0:
        status = False

    return status
   
