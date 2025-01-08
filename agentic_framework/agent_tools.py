# Import things that are needed generically
from langchain.tools import tool

@tool
def add_task_api_directly(input=""):
    """"Useful for when both data are identical and we just need to update only the Task API directly"""

    return 'Add Task API directly '

@tool
def update_sqlitedb_then_task_api(input=""):
    """"Useful for when both data are non-identical and we just need to update the SqliteDB and then update Task API"""
    
    return 'Update SqliteDB first, then Task API'
    
