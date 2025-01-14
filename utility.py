import logging
import yaml
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import csv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_
import time
from datetime import datetime
import pytz
from typing import Optional

import sys
parent_dir = ".."
sys.path.append(parent_dir)
# Need to import all model files to create table
import models.content
import models.base
import models.payment_methods
import models.download_methods
import models.keywords
import models.payment_info
import models.group
import models.different_name



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

def create_database(session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  models.base.Base.metadata.create_all(models.base.engine) 
  time.sleep(2)
  PaymentMethods = models.payment_methods.PaymentMethods
  DownloadMethods = models.download_methods.DownloadMethods
  Keywords = models.keywords.Keywords
  PaymentInfo = models.payment_info.PaymentInfo
  Group = models.group.Group
  
  # Adding Default values
  filename = '/app/data/initial_keywords.csv' 
  with open(filename, 'r') as file:
    reader = csv.DictReader(file)
    data = [row for row in reader]

  # Inserting the payment methods and download methods to its respective tables
  payment = []
  download = []
  group = []
  for row in data:
      payment.append(row['payment']) 
      download.append(row['download_method']) 
      group.append(row['group'])

  # Making the values unique
  payment = set(payment)
  download = set(download)
  group = set(group)

  # Insert Groups
  all_group= session.query(Group).all()
  if len(all_group) > 0:
     for name in group:
        # Query data using 'like' and 'where'
        search_term = f"{name}%"  # Search for names
        id = session.query(Group).filter(Group.name.like(search_term)).first() 
        # No such method in the db 
        if id is None:
            # Create a new group object
            gr = Group(name=name)
            # Add the new group to the session
            session.add(gr)
            # Commit the changes to the database
            session.commit()       
  else:
      for name in group:
        # Create a new group object
        gr = Group(name=name)
        # Add the new group to the session
        session.add(gr)
        # Commit the changes to the database
        session.commit() 


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
      # Get the Group id
      search_term = f"{row['group']}%"  # Search for names
      group = session.query(Group).filter(Group.name.like(search_term)).first() 
      group_id = group.id 

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
          kw = Keywords(subject=row['subject'],payment_method_id=payment_id,download_method_id=download_id,group_id=group_id,sender=row['sender'])
          # Add the new KW to the session
          session.add(kw)
          # Commit the changes to the database
          session.commit() 
  
  # Add the default payment info
  # Adding Default values
  filename = '/app/data/initial_payment_info.csv'
  with open(filename, 'r') as file:
    reader = csv.DictReader(file,  delimiter='|')
    pi_data = [row for row in reader]

  p_infos = session.query(PaymentInfo).all()
  if len(p_infos) > 0:
      for row in pi_data:
        search_term = f"{row['group']}%"  # Search for names
        group = session.query(Group).filter(Group.name.like(search_term)).first() 
        id = session.query(PaymentInfo).filter(PaymentInfo.group_id==group.id).first() 
        if id is None:
          pi= PaymentInfo(details=row['payment_details'],type=row['payment_type'], group_id=group.id)
          session.add(pi)
          session.commit() 
  else:
    for row in pi_data:
      search_term = f"{row['group']}%"  # Search for names
      group = session.query(Group).filter(Group.name.like(search_term)).first() 
      pi= PaymentInfo(details=row['payment_details'],type=row['payment_type'], group_id=group.id)
      session.add(pi)
      session.commit() 

  session.close()

def get_keywords_data_from_db(session=None):
  subjects = []
  payment_methods = []
  download_methods = []
  senders = []

  if session is None:
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

def get_keyword_subject_sender(subject, sender, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  Keywords = models.keywords.Keywords
  #sub_search_term = f"%{subject}%"
  sender_search_term = f"%{sender}%"
  keyword = session.query(Keywords).filter(Keywords.sender.like(sender_search_term)).first() 
  
  return keyword

def content_entry_found(name, date, amount, session=None):
  content = None
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  Session = sessionmaker(bind=models.base.engine)
  session = Session()
  Content = models.content.Content
  # Query data using 'like' and 'where'
  name_search_term = f"%{name}%"  
  date_search_term = f"%{date}%"  
  content = session.query(Content).filter(and_(Content.name.like(name_search_term), Content.date.like(date_search_term))).first() 

  return content
   
def insert_content(logger, data, session=None):

  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  Content = models.content.Content
  group_id = get_group_from_keyword(data['kw_subject'], data['kw_sender'], session)
  if group_id:
    created_datetime = datetime.now(pytz.timezone('Australia/Sydney'))
    # Create a new content object
    content = Content(name=data['Biller_name'], date=data['Due_date'], amount=data['Amount'], payment=data['payment_method'], processed=0, group_id=group_id, created_date=created_datetime)
    # Add the new content to the session
    session.add(content)
    # Commit the changes to the database
    session.commit() 
    logger.info("Data inserted to SQLite")
  else:
    logger.error("Failed to insert to SQLite due to unable to find the group_id")
     
def get_group_from_keyword(subject, sender, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  Keywords = models.keywords.Keywords
  # Query data using 'like' and 'where'
  sub_search_term = f"%{subject}%"  # Search for subjects
  sender_search_term = f"%{sender}%"  # Search for sender
  keyword = session.query(Keywords).filter(and_(Keywords.subject.like(sub_search_term), Keywords.sender.like(sender_search_term))).first() 
  if keyword:
    return keyword.group_id
  else:
    return None

def get_payment_info(group_id, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  PaymentInfo = models.payment_info.PaymentInfo
  paymentInfo = session.query(PaymentInfo).filter(PaymentInfo.group_id == group_id).first() 

  return paymentInfo

def update_payment_info(BankInfoDict, session=None):
  try:
    if session is None:
      Session = sessionmaker(bind=models.base.engine)
      session = Session()
    PaymentInfo = models.payment_info.PaymentInfo
    result = session.query(PaymentInfo).filter(and_(PaymentInfo.group_id == BankInfoDict['group_id'], PaymentInfo.type == BankInfoDict['type'])).update({"details":BankInfoDict['details'], 'group_id': BankInfoDict['group_id'], 'type': BankInfoDict['type']})
    session.commit()    
  except Exception as err:
    print(f"Unexpected {err=}, {type(err)=}")
    result = None
      
  return result

def get_all_contents(session=None):
    if session is None:
      Session = sessionmaker(bind=models.base.engine)
      session = Session()
    Content = models.content.Content
    contents = session.query(Content).all()#filter(Content.processed == 0).all() 

    return contents

def delete_content(id, session=None):
    if session is None:
      Session = sessionmaker(bind=models.base.engine)
      session = Session()
    Content = models.content.Content
    # Retrieve single record
    content = session.query(Content).filter(Content.id==1).first()
    # Perform Delete Action
    session.delete(content)
    # Commit changes
    session.commit()
   
def update_content(id, session=None, processed=1):
  try:
    if session is None:
      Session = sessionmaker(bind=models.base.engine)
      session = Session()
    Content = models.content.Content
    result = session.query(Content).filter(Content.id == id).update({"processed": processed})
    session.commit()
  except Exception as err:
    print(f"Unexpected {err=}, {type(err)=}")
    result = None
  
  return result

def update_content_all_by_id(id, data, session=None):
  try:
    if session is None:
      Session = sessionmaker(bind=models.base.engine)
      session = Session()
    Content = models.content.Content
    result = session.query(Content).filter(Content.id == id).update({'name':data['Biller_name'], 'date':data['Due_date'], 'amount':data['Amount']})
    session.commit()
  except Exception as err:
    print(f"Unexpected {err=}, {type(err)=}")
    result = None
  
  return result



def get_all_contents_unfiltered(session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  Content = models.content.Content
  contents = session.query(Content).all() 

  return contents

def get_all_payment_methods(session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  PaymentMethods = models.payment_methods.PaymentMethods
  pms = session.query(PaymentMethods).all() 

  return pms

def get_all_download_methods(session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  DownloadMethods = models.download_methods.DownloadMethods
  dms = session.query(DownloadMethods).all() 

  return dms

def get_payment_method(id, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  PaymentMethods = models.payment_methods.PaymentMethods
  pm = session.query(PaymentMethods).filter(PaymentMethods.id == id).first() 

  return pm

def get_download_method(id, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  DownloadMethods = models.download_methods.DownloadMethods
  dm = session.query(DownloadMethods).filter(DownloadMethods.id == id).first() 

  return dm

def get_all_groups(session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  Group = models.group.Group
  groups = session.query(Group).all() 

  return groups

def insert_keyword_api(formData:dict, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  PaymentMethods = models.payment_methods.PaymentMethods
  DownloadMethods = models.download_methods.DownloadMethods
  Keywords = models.keywords.Keywords
  Group = models.group.Group
  # Get the Group id
  group = session.query(Group).filter(Group.id == int(formData['group'])).first() 
  if group:
    group_id = group.id
  else:
    raise Exception("No group id found")

  # Query data using 'like' and 'where'
  sub_search_term = f"%{formData['subject']}%"  # Search for subjects
  sender_search_term = f"%{formData['sender']}%"  # Search for sender
  keyword = session.query(Keywords).filter(and_(Keywords.subject.like(sub_search_term), Keywords.sender.like(sender_search_term))).first() 
  # No such keywords in the db 
  if keyword is None:        
    # Get the payment_id
    payment= session.query(PaymentMethods).filter(PaymentMethods.id == int(formData['payment_method'])).first() 
    if payment:
      payment_id = payment.id
    else:
      raise Exception("No payment id found")
        
    # Get the download_id
    download = session.query(DownloadMethods).filter(DownloadMethods.id == int(formData['download_method'])).first() 
    if download:
      download_id = download.id
    else:
      raise Exception("No download id found")
    
    # Create a new KW object
    kw = Keywords(subject=formData['subject'],payment_method_id=payment_id,download_method_id=download_id,group_id=group_id,sender=formData['sender'])
    # Add the new KW to the session
    session.add(kw)
    # Commit the changes to the database
    session.commit() 
    message = 'Form submitted successfully!'
  else:
    message = 'Data exists already'
  
  return message

def insert_download_methods_api(download, session=None):

  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  DownloadMethods = models.download_methods.DownloadMethods
  # Query data using 'like' and 'where'
  search_term = f"{download}%"  # Search for names
  id = session.query(DownloadMethods).filter(DownloadMethods.name.like(search_term)).first() 
  # No such method in the db 
  if id is None:
    # Create a new DM object
    dm = DownloadMethods(name=download)
    # Add the new DM to the session
    session.add(dm)
    # Commit the changes to the database
    session.commit()   
    message = 'Form submitted successfully!'
  else:
    message = 'Data exists already'
   
  return message

def insert_payment_methods_api(p_methods, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  PaymentMethods = models.payment_methods.PaymentMethods
  # Query data using 'like' and 'where'
  search_term = f"{p_methods}%"  # Search for names
  id = session.query(PaymentMethods).filter(PaymentMethods.name.like(search_term)).first() 
  # No such method in the db 
  if id is None:
    pm = PaymentMethods(name=p_methods)
    session.add(pm)
    session.commit()      
    message = 'Form submitted successfully!'
  else:
    message = 'Data exists already'

  return message

def insert_group_api(group_name, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  Group = models.group.Group
  # Query data using 'like' and 'where'
  search_term = f"{group_name}%"  # Search for names
  id = session.query(Group).filter(Group.name.like(search_term)).first() 
  # No such method in the db 
  if id is None:
    # Create a new group object
    gr = Group(name=group_name)
    # Add the new group to the session
    session.add(gr)
    # Commit the changes to the database
    session.commit()    
    message = 'Form submitted successfully!'
  else:
    message = 'Data exists already'

  return message

def insert_new_name_api(new_name, group_id, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  DifferentName = models.different_name.DifferentName
  # Query data using 'like' and 'where'
  search_term = f"{new_name}"  # Search for names
  name = session.query(DifferentName).filter(DifferentName.name.like(search_term)).first() 
  if name is None:
    dn = DifferentName(name=new_name, group_id=group_id)
    session.add(dn)
    session.commit()       
    message = 'Form submitted successfully!'
  else:
    message = 'Data exists already'

  return message

def get_group_name(biller_name, session=None):
  group_name = None
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  DifferentName = models.different_name.DifferentName
  # Query data using 'like' and 'where'
  search_term = f"{biller_name}%"  # Search for names
  name = session.query(DifferentName).filter(DifferentName.name.like(search_term)).first() 
  if name:
    group_id = name.group_id
    Group = models.group.Group
    group = session.query(Group).filter(Group.id == group_id).first() 
    group_name = group.name

  return group_name

def get_group_by_id(id, session=None):
  group = None
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  
  Group = models.group.Group
  group = session.query(Group).filter(Group.id == id).first() 
  
  return group

def submit_as_paid(content_id, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  Content = models.content.Content
  result = session.query(Content).filter(Content.id == content_id).update({"paid":1})
  session.commit() 
  if result:
    message = 'Paid status updated'
  else:
    message = 'Something gone wrong'
  return message

def get_keyword_on_title(title, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  name_search_term = f"%{title}%"  # Search for sender
  Keywords = models.keywords.Keywords
  keyword = session.query(Keywords).filter(Keywords.subject.like(name_search_term)).first() 
  
  return keyword

def get_different_names_on_title(title, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  name_search_term = f"%{title}%"  # Search for sender
  DifferentName= models.different_name.DifferentName
  differentName = session.query(DifferentName).filter(DifferentName.subject.like(name_search_term)).first() 
  
  return differentName

def get_payment_method_by_group_id(group_id, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  Keywords = models.keywords.Keywords
  keyword = session.query(Keywords).filter(Keywords.id == group_id).first() 
  PaymentMethods = models.payment_methods.PaymentMethods
  pm = session.query(PaymentMethods).filter(PaymentMethods.id == keyword.payment_method_id).first()

  return pm 


def get_keyword_by_group_id(group_id, session=None):
  if session is None:
    Session = sessionmaker(bind=models.base.engine)
    session = Session()
  Keywords = models.keywords.Keywords
  keyword = session.query(Keywords).filter(Keywords.id == group_id).first() 

  return keyword









