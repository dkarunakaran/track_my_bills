import os.path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlitedb import SqliteDB
import os
from utility import logger_helper,authenticate
import yaml
from datetime import datetime, timezone

# Ref 1: https://gist.github.com/qmacro/973175/19d4a7947fdaf45767699286b594a4075dbcc12f
# Ref 2: https://github.com/googleapis/google-api-python-client/blob/main/samples/service_account/tasks.py
# Ref 3: https://developers.google.com/tasks/reference/rest/v1/tasks

class Generate:
    def __init__(self, logger=None, creds=None):
        self.sql_db = SqliteDB()
        self.logger = logger
        if self.logger is None:
            self.logger = logger_helper()
        with open("config.yaml") as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)
        
        # Authenticate with GOOGLE API
        if creds is None:
            self.creds = authenticate(self.cfg)

        # Define the TASK API
        self.service = build("tasks", "v1", credentials=self.creds)
        self.logger.info("Authenticated")

    def task_API_operation(self):
        try:
            contents = self.get_all_contents()
            self.logger.debug(f"Contents from SQLite: {contents}")
            if len(contents) > 0:
                tasklist_id = self.get_tasklist_id(keyword='Payment')
                try:
                    if tasklist_id is not None:
                        for content in contents:
                            task_id = self.get_task_id(tasklist_id=tasklist_id, task_name=content[1])
                            self.logger.debug(f"Task_id: {task_id}")
                            date_str = content[2]
                            date_format = '%Y-%m-%d'
                            date_obj = datetime.strptime(date_str, date_format).astimezone()
                            self.logger.debug(f"Date object: {date_obj.isoformat()}")
                            notes = f"Amount: {content[3]}\nPayment: {content[4]}"
                            taskdata = { 'title': content[1], 'due': date_obj.isoformat(),'notes': notes}
                            if task_id is None:
                                self.logger.info(f"TASK API insert operation of '{content[1]}' started")
                                result = self.service.tasks().insert(tasklist=tasklist_id, body=taskdata).execute()
                            else:
                                self.logger.info(f"TASK API update operation '{content[1]}' started")
                                result = self.service.tasks().patch(tasklist=tasklist_id, task=task_id, body=taskdata).execute()
                            self.logger.debug(result)
                            self.delete_content(id=content[0])
                    self.logger.info("All Tasks are created/updated")
                except Exception as err:
                    self.logger.error(f"Unexpected {err=}, {type(err)=}")
            else:
                self.logger.info("No task data found in SQLite")
        except HttpError as error:
            self.logger.critical(f"An error occurred: {error}")

    def get_tasklist_id(self, keyword):
         # List all the tasklists for the account.
        id = None
        lists = self.service.tasklists().list().execute()
        for item in lists['items']:
            if item['title'] == keyword:
                id = item['id']
                break
        return id
    
    def get_task_id(self, tasklist_id=None, task_name=None):
        id = None
        results = self.service.tasks().list(tasklist=tasklist_id).execute()
        tasks = results.get('items', [])
        self.logger.debug(f"All tasks: {tasks}")
        for task in tasks:
            if task['title'] == task_name:
                id = task['id']
                break
        return id
    
    def get_all_contents(self):
        query = f"SELECT id, name, date, amount, payment FROM Content"
        self.sql_db.cursor.execute(query)
        contents = self.sql_db.cursor.fetchall()
        return contents
    
    def delete_content(self, id):
        query = f"DELETE FROM Content WHERE id={id}"
        self.sql_db.cursor.execute(query)
        self.sql_db.conn.commit()

if __name__ == "__main__":
  generate = Generate()
  generate.task_API_operation()
