# Import things that are needed generically
from langchain.tools import tool
from agent_state import BankInfoDict
import json

import sys
parent_dir = ".."
sys.path.append(parent_dir)
import utility

@tool
def add_task_api_directly(existing="", new=""):
    """"Useful for when both data are same and we just need to update only the Task API directly"""

    return 'Add Task API directly '

@tool
def update_sqlitedb_then_task_api(existing="", new=""):
    """"Useful for when both data are different and we just need to update the SqliteDB and then update Task API"""
    
    _return = ""
    # Sample data: '197954,7,77090066069,BPay'
    #               biller_code,group_id,reference_number,type
    print(new)
    new_data = new.split(",")
    details = {}
    if new_data[3] == 'BPay':
        details["biller_code"] = new_data[0]
        details["reference_number"] = new_data[2]
    if new_data[3] == 'bank account':
        details["bsb"] = new_data[0]
        details["account_number"] = new_data[2]

    bankInfoDict = BankInfoDict(details=json.dumps(details), type=new_data[3], group_id=new_data[1])
    update_result = utility.update_payment_info(bankInfoDict)
    
    if update_result:
        _return += "Update Operation successful"
    else:
        _return += "Update Operation failed, so stopping the next operation"
    
    
    return _return
    


