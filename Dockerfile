FROM python:3.12.5-bookworm

RUN pip install --upgrade pip

# Google API
RUN pip install google-api-python-client==2.159.0
RUN pip install google-auth==2.37.0
RUN pip install google-auth-httplib2==0.2.0
RUN pip install google-auth-oauthlib==1.2.0

# Web scraping
RUN pip install beautifulsoup4~=4.12.3
RUN pip install lxml==5.3.0
RUN pip install PyYAML==6.0.2

# Webservices
RUN pip install requests==2.32.3
RUN pip install flask==3.0.3
RUN pip install ollama==0.3.2
RUN pip install certifi==2018.11.29
RUN pip install Click>=7.1.2
RUN pip install gunicorn>=19.9.0
RUN pip install itsdangerous>=2.0
RUN pip install Jinja2>=2.10.1
RUN pip install MarkupSafe>=2.0
RUN pip install werkzeug>=2.0
RUN pip install pytest==6.2.3
RUN pip install pytest-cov==2.11.1
RUN pip install pylint==2.7.4
RUN pip install fastapi==0.115.6
RUN pip install uvicorn[standard]==0.34.0
RUN pip install jinja2==3.1.5
RUN pip install python-multipart==0.0.20
RUN pip install sqlalchemy==1.4.41
RUN pip install pillow>=6.2.0
RUN pip install pytesseract>=0.2.6


# Langchain, Langgraph, GenAI
RUN pip install langchain==0.3.14
RUN pip install langchain-chroma==0.2.0
RUN pip install langchain-ollama==0.2.2
RUN pip install langchain-huggingface==0.1.2
RUN pip install langchain_community==0.3.14
RUN pip install langchain-openai==0.3.0
RUN pip install langgraph==0.2.60 
RUN pip install langgraph-checkpoint-sqlite==2.0.1
RUN pip install -q -U google-generativeai==0.8.4


RUN apt-get update && apt-get -y install tesseract-ocr 
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y
RUN pip3 install opencv-python
RUN pip3 install pandas
RUN apt-get install -y vim
RUN apt-get update && apt-get install -y supervisor
RUN pip install python-dotenv==1.0.1

# Browser
RUN pip install pytest-playwright==0.6.2
RUN playwright install
RUN apt-get update
RUN playwright install-deps 
RUN playwright install chrome

RUN pip install fpdf2==2.8.2
RUN pip install pypdf==5.1.0

WORKDIR /app

EXPOSE 8000

#For testing
CMD ["/bin/bash"]

# For production
#CMD ["python", "app.py"]
