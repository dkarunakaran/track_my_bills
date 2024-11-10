import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os.path
import base64
from bs4 import BeautifulSoup
import yaml
from ollama_service import OllamaService

class Download:
  def __init__(self):
    with open("config.yaml") as f:
      self.cfg = yaml.load(f, Loader=yaml.FullLoader)
    self.subjects = self.cfg['gmail']['subjects']
    self.senders = self.cfg['gmail']['senders']
    
    # If modifying these scopes, delete the file token.json.
    SCOPES = self.cfg['gmail']['scopes']

    self.ollama_service = OllamaService()

    # Authenticate
    self.creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
      self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not self.creds or not self.creds.valid:
      if self.creds and self.creds.expired and self.creds.refresh_token:
        self.creds.refresh(Request())
      else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        self.creds = flow.run_console(port=0)
      # Save the credentials for the next run
      with open("token.json", "w") as token:
        token.write(self.creds.to_json())

  def get_emails(self):
    
    try:
      # Call the Gmail API
      service = build("gmail", "v1", credentials=self.creds)
      
      # request a list of all the messages
      # We can also pass maxResults to get any number of emails. Like this:
      # result = service.users().messages().list(maxResults=200, userId='me').execute()
      result = service.users().messages().list(maxResults=3, userId='me').execute()
      
      messages = result.get('messages')
      

      # messages is a list of dictionaries where each dictionary contains a message id.

      # iterate through all the messages
      for msg in messages:
        # Get the message from its id
        txt = service.users().messages().get(userId='me', id=msg['id']).execute()
        # Use try-except to avoid any Errors
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
          if True in subject_found and True in sender_found:
            proceed = True

          if proceed == True:
            for part in payload['parts']:
              if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                  data = part['body']['data']
                  data = data.replace("-","+").replace("_","/")
                  decoded_data = base64.b64decode(data)

                  # Now, the data obtained is in lxml. So, we will parse
                  # it with BeautifulSoup library
                  soup = BeautifulSoup(decoded_data , "lxml")
                  text = soup.body()
                  #print(text)
              elif part['mimeType'] == 'application/pdf':
                att_id = part['body']['attachmentId']
                att = service.users().messages().attachments().get(userId="me", messageId=msg['id'],id=att_id).execute()
                data = att['data']
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                path = part['filename']
                with open(path, 'w') as f:
                  f.write(file_data)
              elif part['mimeType'] == 'multipart/mixed':
                for p in part['parts']:
                  if p['mimeType'] == 'application/pdf':
                    att_id = p['body']['attachmentId']
                    response = service.users().messages().attachments().get(userId="me", messageId=msg['id'],id=att_id).execute()
                    file_data = base64.urlsafe_b64decode(response.get('data').encode('UTF-8'))
                    path = 'pdfs/'+p['filename']
                    with open(path, 'wb') as f:
                      f.write(file_data)


        except Exception as err:
          print(f"Unexpected {err=}, {type(err)=}")
          pass
    except HttpError as error:
      # TODO(developer) - Handle errors from gmail API.
      print(f"An error occurred: {error}")


if __name__ == "__main__":
  download = Download()
  download.get_emails()