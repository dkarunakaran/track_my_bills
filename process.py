# importing required classes
from pypdf import PdfReader
import json
import re

from ollama_service import OllamaService

class Process:
    def __init__(self):
        self.ollama_service = OllamaService()
    
    def read_and_process(self, file_path):
        # creating a pdf reader object
        reader = PdfReader(file_path)
        content = ""
        for page in reader.pages:
            # extracting text from page
            content += page.extract_text()
            content += '\n'
        print("PDF data extraction completed, now checking with LLM to extract the information")
        response = self.ollama_service.query(content)
        result = self.get_JSON(response)
        print(result)

    def get_JSON(self, response:str):
        
        #Find the index of the first opening curly brace '{' within the extracted_text
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


if __name__ == "__main__":
  process = Process()
  process.read_and_process('pdfs/77090066069 ELEC_1507755.PDF')

