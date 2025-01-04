# Import things that are needed generically
from langchain.tools import tool
from typing import List
import yaml

import sys
sys.path.append("/app")
from download import Download


@tool
def invoice_email() -> List[str]:
    """"Useful for when you need to get invoices from email"""
    
    download = Download()

    # Read and process emails
    #download.get_emails()
    

    return ["LangChain"]
    

if __name__ == '__main__':
    print(invoice_email.name)
    print(invoice_email.description)
    print(invoice_email.args)
