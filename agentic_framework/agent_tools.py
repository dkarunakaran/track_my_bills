# Import things that are needed generically
from langchain.tools import tool

@tool
def add_task_api_directly(existing="", new=""):
    """"Useful for when both data are same and we just need to update only the Task API directly"""

    return 'Add Task API directly '

@tool
def update_sqlitedb_then_task_api(existing="", new=""):
    """"Useful for when both data are different and we just need to update the SqliteDB and then update Task API"""
    
    return 'Update SqliteDB first, then Task API'
    
