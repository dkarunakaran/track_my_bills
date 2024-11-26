# importing required classes
from pypdf import PdfReader
import json
import re
from sqlitedb import SqliteDB
from ollama_service import OllamaService
import os
from utility import logger_helper
from os import listdir
from os.path import isfile, join
import yaml
from itertools import compress 

class Process:
    def __init__(self, logger=None):
        with open("config.yaml") as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)
        self.ollama_service = OllamaService()
        self.sql_db = SqliteDB()
        self.logger = logger
        if self.logger is None:
            self.logger = logger_helper()
        self.subjects = self.cfg['GOOGLE_API']['subjects']
        self.payment_methods = self.cfg['GOOGLE_API']['payment_methods']
    
    # find_payment_method flag force the code the find the payment method again. In some cases, especially drive files, we do not have specific subject field,
    # so finding the payment method without subject will be hard intitally. Once we get the subject field after LLm processing, we need to initiate
    # the payment method finding. 
    def read_and_process(self, file_path=None, payment_method="", is_pdf=True, text=None, is_image=False, find_payment_method=False):
        try:
            if is_pdf == True:
                if os.path.exists(file_path):
                    self.logger.info(f"file: {file_path} is processing")
                    # Creating a pdf reader object
                    reader = PdfReader(file_path)
                    content = ""
                    for page in reader.pages:
                        # Extracting text from page
                        content += page.extract_text()
                        content += '\n'
                    #content = reader.pages[0]
                    self.llm_check_and_db_insert(content, payment_method)
                    os.remove(file_path)
                    self.logger.info(f"file: {file_path} is removed")  
                else:
                    self.logger.warning("The file does not exist")
            else:
                self.llm_check_and_db_insert(text, payment_method, find_payment_method)
                if is_image == True:
                    os.remove(file_path)
                    self.logger.info(f"file: {file_path} is removed")  

        except Exception as err:
            self.logger.error(f"Unexpected {err=}, {type(err)=}")
        

    def llm_check_and_db_insert(self, content, payment_method, find_payment_method = False):
        self.logger.info("Got the Data, now requesting LLM to extract the information")
        response = self.ollama_service.query(content)  
        self.logger.debug(f"data from LLM: {response}")
        result = self.get_JSON(response)
        self.logger.info(f"Got the JSON ecncoded data: {result}")
        if find_payment_method == True:
            self.logger.info("Searching for the payment method")
            title = result['Biller_name']
            # To find the payment method
            title_found = [True if title in s else False  for s in self.subjects]
            res_sub = list(compress(range(len(title_found)), title_found))
            payment_method = ""
            if len(res_sub) > 0:
                method_index = res_sub[0]
                payment_method = self.payment_methods[method_index]
                self.logger.info(f"Found the payment method: {payment_method}")
        
        if self.content_entry_found(result['Biller_name'], result['Due_date'], result['Amount']) == False:
            self.sql_db.cursor.execute("""INSERT INTO Content (name, date, amount, payment) VALUES (?,?,?,?)""", [result['Biller_name'], result['Due_date'], result['Amount'], payment_method])
            self.sql_db.conn.commit()
            self.logger.info("Data inserted to SQLite")
        else:
            self.logger.info("Data is already exist in SQLite")


    def get_JSON(self, response:str):
        
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

    def content_entry_found(self, name, date, amount):
        query = f"SELECT id FROM Content where name LIKE '%{name}%' and date LIKE '%{date}%'and amount LIKE '%{amount}%' LIMIT 1"
        self.sql_db.cursor.execute(query)
        content_id = self.sql_db.cursor.fetchall()
        status = True
        if len(content_id) == 0:
            status = False

        return status
    
    def read_dir(self):
        onlyfiles = [f for f in listdir(self.cfg['dir']) if isfile(join(self.cfg['dir'], f))]
        for file in onlyfiles:
            file_path = self.cfg['dir']+"/"+file
            self.read_and_process(file_path)    



if __name__ == "__main__":
  process = Process()
  #process.read_and_process('pdfs/FDC Receipt Dev WE 03:11:24 & 11:11:24.pdf')
  process.read_dir()

