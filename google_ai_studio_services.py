import google.generativeai as genai
from secret import Secret

class GoogleAIStudioServices(Secret):
    def __init__(self):
        genai.configure(api_key=self.google_ai_studio_token)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def generate_content(self, prompt):
        response = self.model.generate_content(prompt)
        return response.text

if __name__ == "__main__":
    service = GoogleAIStudioServices()
    response_text = service.generate_content("Explain how AI works")
    print(response_text)