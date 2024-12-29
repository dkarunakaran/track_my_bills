FROM python:3.12.5-bookworm

RUN pip install --upgrade pip
RUN pip install google-api-python-client
RUN pip install google-auth
RUN pip install google-auth-httplib2
RUN pip install google-auth-oauthlib

# Web scraping
RUN pip install beautifulsoup4~=4.12.3
RUN pip install lxml
RUN pip install PyYAML

# Webservices
RUN pip install requests==2.32.3
RUN pip install flask==3.0.3
RUN pip install ollama==0.3.2

RUN pip install pypdf

# Langchain
RUN pip install langchain
RUN pip install langchain-chroma
RUN pip install langchain-ollama
RUN pip install langchain-huggingface

RUN pip install fpdf2

RUN apt-get update && apt-get -y install tesseract-ocr 
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y
RUN pip3 install opencv-python
RUN pip3 install pandas

RUN pip install pillow>=6.2.0
RUN pip install pytesseract>=0.2.6
RUN pip install werkzeug>=2.0

# For the API
RUN pip install certifi==2018.11.29
RUN pip install Click>=7.1.2
RUN pip install Flask>=2.0.1
RUN pip install gunicorn>=19.9.0
RUN pip install itsdangerous>=2.0
RUN pip install Jinja2>=2.10.1
RUN pip install MarkupSafe>=2.0
RUN pip install werkzeug>=2.0
RUN pip install pytest==6.2.3
RUN pip install pytest-cov==2.11.1
RUN pip install pylint==2.7.4

WORKDIR /app

# For kubernetes cron job
COPY . .

EXPOSE 5000

#For testing
#CMD ["/bin/bash"]

# For production
CMD ["python", "app.py"]