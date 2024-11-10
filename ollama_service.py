from ollama import Client
import yaml
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
class OllamaService:
    def __init__(self):
        with open("config.yaml") as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)
        
        # https://python.langchain.com/docs/integrations/llms/ollama/
        # We cannot use llama 3.2-vision model as it required atleast 8 gb of VRAM which is not avaialble in our server.
        # https://ollama.com/blog/llama3.2-vision

        template = self.cfg['ollama']['template']
        prompt = ChatPromptTemplate.from_template(template)
        model = OllamaLLM(model=self.cfg['ollama']['model'], base_url=self.cfg['ollama']['host'])
        self.chain = prompt | model
    
    def query(self, text):
        return self.chain.invoke({"context": text})



if __name__=="__main__":
    ollama_service =OllamaService()
        
