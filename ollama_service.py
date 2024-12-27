from ollama import Client
import yaml
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
class OllamaService:
    def __init__(self):
        with open("config.yaml") as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)

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
        model = OllamaLLM(model=self.cfg['ollama']['model'], base_url=self.cfg['ollama']['host'])
        self.chain = prompt | model
    
    def query(self, text):
        return self.chain.invoke({"context": text})



if __name__=="__main__":
    ollama_service =OllamaService()
        
