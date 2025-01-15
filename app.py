from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import time
from main import run
import yaml
import utility
from sqlalchemy.orm import sessionmaker
import json
import subprocess
import sys
parent_dir = ".."
sys.path.append(parent_dir)
import models.base

app = FastAPI()
templates = Jinja2Templates(directory="templates")

with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)
utility.create_database()
Session = sessionmaker(bind=models.base.engine)
session = Session()

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    try:
        contents = utility.get_all_contents_unfiltered(session=session)
        payment_methods = utility.get_all_payment_methods(session=session)
        download_methods = utility.get_all_download_methods(session=session)
        groups = utility.get_all_groups(session=session)
    except Exception as err:
        contents = []
        payment_methods = []
        download_methods = []
        groups = []

    return templates.TemplateResponse(request=request, name="index.html",context={"contents":contents,"payment_methods":payment_methods,
                                      "download_methods":download_methods, "groups":groups})
    
@app.post('/query_invoices/')
async def query_invoices(request: Request):
    #run(session)
    #return "Invoices processed"
    # For some reason, each time we get request, calling to run function was mulplying.
    # Temprray solution was to eun the supervisor each time we get request.
    result = subprocess.run(
        "supervisord -c /app/supervisord.conf", 
        shell=True, 
        check=True
    )
    if result.returncode == 0:
        time.sleep(60)
        reply = {"message": "supervisord started succesfully and wait for 30 seconds"}

        return Response(content=json.dumps(reply), media_type="application/json")
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Command execution failed: {result.stderr}"
        )

@app.post('/add_new_kw_entry/')
async def add_new_keyword_entry(request: Request):
    form_data = await request.form() 
    dict_data = {
        'subject': form_data.get('subject'),
        'payment_method': form_data.get('payment_methods'),
        'download_method': form_data.get('download_methods'),
        'group': form_data.get('groups'),
        'sender': form_data.get('sender')
    }
    time.sleep(3)
    message = utility.insert_keyword_api(dict_data, session=session)
    reply = {"message": message}
    return Response(content=json.dumps(reply), media_type="application/json")
        
@app.post('/add_new_dwm_entry/')
async def add_new_download_entry(request: Request):
    # Get form data
    form_data = await request.form() 
    download = form_data.get('download')
    time.sleep(3)
    message = utility.insert_download_methods_api(download, session=session)
    reply = {"message": message}
    
    return Response(content=json.dumps(reply), media_type="application/json")
    
@app.post('/add_new_pm_entry/')
async def add_new_payment_entry(request: Request):
    # Get form data
    form_data = await request.form() 
    payment = form_data.get('payment')
    time.sleep(3)
    message = utility.insert_payment_methods_api(payment, session=session)
    reply = {"message": message}
    
    return Response(content=json.dumps(reply), media_type="application/json")

@app.delete('/delete_content/')
async def delete_content_update(request: Request):
    # Get form data
    form_data = await request.form() 
    content_id = form_data.get('delete_content')
    time.sleep(3)
    utility.delete_content(content_id, session=session)
    reply = {"message": f"Deleted the content: {content_id}"}

    return Response(content=json.dumps(reply), media_type="application/json")

@app.post('/add_new_group_entry/')
async def add_new_group_entry(request: Request):
    # Get form data
    form_data = await request.form() 
    group = form_data.get('group')
    time.sleep(3)
    message = utility.insert_group_api(group, session=session)
    reply = {"message": message}
    
    return Response(content=json.dumps(reply), media_type="application/json")
        
@app.post('/add_new_name_under_group/')
async def add_new_name_under_group_entry(request: Request):
    # Get form data
    form_data = await request.form() 
    new_name =  form_data.get('new_name')
    group_id = form_data.get('group')
    time.sleep(3)
    message = utility.insert_new_name_api(new_name, group_id, session=session)
    reply = {"message": message}
    
    return Response(content=json.dumps(reply), media_type="application/json")
        
@app.post('/submit_as_paid/')
async def submit_as_paid_entry(request: Request):
    # Get form data
    form_data = await request.form() 
    content_id =  form_data.get('content_id')
    time.sleep(3)
    message = utility.submit_as_paid(content_id, session=session)
    reply = {"message": message}
    
    return Response(content=json.dumps(reply), media_type="application/json")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
