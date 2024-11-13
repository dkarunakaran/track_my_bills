from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from bs4 import BeautifulSoup
import yaml
from utility import logger_helper, authenticate
from itertools import compress 
import time
from process import Process
import io
import argparse
from tqdm import tqdm
from googleapiclient.http import MediaIoBaseDownload
import re

class Download:
  def __init__(self):
    with open("config.yaml") as f:
      self.cfg = yaml.load(f, Loader=yaml.FullLoader)
    self.subjects = self.cfg['GOOGLE_API']['subjects']
    self.senders = self.cfg['GOOGLE_API']['senders']
    self.payment_methods = self.cfg['GOOGLE_API']['payment_methods']
    self.download_methods = self.cfg['GOOGLE_API']['download_methods']
    self.logger = logger_helper()
    self.process = Process(logger=self.logger)

    # Authenticate with GOOGLE API
    self.creds = authenticate(self.cfg)

    # Define GMAIL API service
    self.gmail_service = build("gmail", "v1", credentials=self.creds)
    self.drive_service = build('drive', 'v3', credentials=self.creds)
    self.logger.info("Authenticated")

  def get_emails(self):
    try:
      self.logger.info("Reading the email using GMAIL API")
      # request a list of all the messages
      # We can also pass maxResults to get any number of emails. Like this:
      # result = service.users().messages().list(maxResults=200, userId='me').execute()
      result = self.gmail_service.users().messages().list(maxResults=self.cfg['GOOGLE_API']['no_emails'], userId='me').execute()
      messages = result.get('messages')
      self.logger.info("Got the mails and processing now")
      # messages is a list of dictionaries where each dictionary contains a message id.
      # iterate through all the messages
      for msg in messages:
        # Get the message from its id
        txt = self.gmail_service.users().messages().get(userId='me', id=msg['id']).execute()
        # Use try-except to avoid any Errors
        multiple_pdf_data = []
        path = None
        try:
          # Get value of 'payload' from dictionary 'txt'
          payload = txt['payload']
          headers = payload['headers']

          # Look for Subject and Sender Email in the headers
          for d in headers:
            if d['name'] == 'Subject':
              subject = d['value']
            if d['name'] == 'From':
              sender = d['value']

          # Code for getting only email we want to track
          proceed = False
          subject_found = [True if subject.find(s) != -1 else False  for s in self.subjects]
          sender_found = [True if sender.find(sen) != -1 else False  for sen in self.senders]
          res_sub = list(compress(range(len(subject_found)), subject_found))
          download_method = ""
          # Selecting payment methods
          payment_method = ""
          if len(res_sub) > 0:
            method_index = res_sub[0]
            payment_method = self.payment_methods[method_index]
            download_method = self.download_methods[method_index]

          if True in subject_found and True in sender_found:
            proceed = True

          self.logger.info(f"Processing: '{subject}' now")
          if proceed == True:
            for part in payload['parts']:
              if part['mimeType'] == 'text/plain' and download_method == 'email_body':
                if 'data' in part['body']:
                  data = part['body']['data']
                  data = data.replace("-","+").replace("_","/")
                  decoded_data = base64.b64decode(data)

                  # Now, the data obtained is in lxml. So, we will parse
                  # it with BeautifulSoup library
                  soup = BeautifulSoup(decoded_data , "lxml")
                  text = soup.get_text()
                  self.process.read_and_process(payment_method=payment_method, is_pdf=False, text=text)        
                
              elif part['mimeType'] == 'application/pdf':
                att_id = part['body']['attachmentId']
                response = self.gmail_service.users().messages().attachments().get(userId="me", messageId=msg['id'],id=att_id).execute()
                file_data = base64.urlsafe_b64decode(response.get('data').encode('UTF-8'))
                path = self.cfg['dir']+'/'+part['filename']
                multiple_pdf_data.append({'name': path, 'data': file_data})
                
              elif part['mimeType'] == 'multipart/mixed':
                for p in part['parts']:
                  if p['mimeType'] == 'application/pdf':
                    att_id = p['body']['attachmentId']
                    response = self.gmail_service.users().messages().attachments().get(userId="me", messageId=msg['id'],id=att_id).execute()
                    file_data = base64.urlsafe_b64decode(response.get('data').encode('UTF-8'))
                    path = self.cfg['dir']+'/'+p['filename']
                    multiple_pdf_data.append({'name': path, 'data': file_data})
                    
            if len(multiple_pdf_data) > 0:
              self.logger.info("Saving the attachments to a folder")
              for file_data in multiple_pdf_data:
                with open(file_data['name'], 'wb') as f:
                  f.write(file_data['data'])
                time.sleep(3)
                self.process.read_and_process(file_data['name'],payment_method)
        except Exception as err:
          self.logger.error(f"Unexpected {err=}, {type(err)=}")
    except HttpError as error:
      self.logger.critical(f"An error occurred: {error}")

  def get_drive_files(self):
    # Ref: https://medium.com/the-team-of-future-learning/integrating-google-drive-api-with-python-a-step-by-step-guide-7811fcd16c44
    
    self.logger.info('Finding the folder id to get all files')
    folder_id = None
    results = self.drive_service.files().list(pageSize=20, fields="files(id, name)").execute() 
    for item in results.get('files', []):
      if item['name'] == self.cfg['GOOGLE_API']['drive_folder_name']:
        folder_id = item['id']
        self.logger.info('Found folder id')  
        break

    if folder_id is not None:
      file_results = self.drive_service.files().list(
                  pageSize=self.cfg['GOOGLE_API']['no_of_drive_files'],
                  q="'" + folder_id + "'" + " in parents",
                  fields="nextPageToken, files(id, name, mimeType)",
              ).execute()
      files = file_results.get('files', [])
      self.logger.debug(f"Found files:{files}")
      if len(files) > 0:   
        for file in files:
          if str(file["mimeType"]) == str("application/pdf"):
            self.logger.info(f"Downloading: {file['name']} is started") 
            self.downloadfiles(file['id'], file['name'])
            self.drive_service.files().delete(fileId=file['id']).execute()
            self.logger.info(f"file: {file['name']} is deleted from Google Drive") 
            file_path=self.cfg['dir']+"/"+file['name']
            self.process.read_and_process(file_path, payment_method="")

      else:
        self.logger.info(f"No files found")


  def downloadfiles(self, file_id, dfilespath):
    folder = self.cfg['dir']
    request = self.drive_service.files().get_media(fileId=file_id)
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
    self.logger.info(f"Downloading: {dfilespath} is finished") 

if __name__ == "__main__":
  download = Download()
  #download.get_emails()
  download.get_drive_files()