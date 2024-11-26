FROM python:3.12.5-bookworm

RUN pip install --upgrade pip
RUN pip install google-api-python-client==1.7.2
RUN pip install google-auth==2.14.1
RUN pip install google-auth-httplib2==0.0.3
RUN pip install google-auth-oauthlib==0.4.1

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



WORKDIR /app

CMD ["/bin/bash"]