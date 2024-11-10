from ollama import Client
import yaml
class OllamaService:
    def __init__(self):
        with open("config.yaml") as f:
            self.cfg = yaml.load(f, Loader=yaml.FullLoader)
        self.client = Client(host=self.cfg['ollama']['host'])
        # https://github.com/ollama/ollama-python
        # https://github.com/ollama/ollama/blob/main/docs/api.md
        
        # We cannot use llama 3.2-vision model as it required atleast 8 gb of VRAM which is not avaialble in our server.
        # https://ollama.com/blog/llama3.2-vision


if __name__=="__main__":
    ollama_service =OllamaService()
        
