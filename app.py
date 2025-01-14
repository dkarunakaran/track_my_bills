from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import time
from main import run
import yaml
import utility
from sqlalchemy.orm import sessionmaker

import sys
parent_dir = ".."
sys.path.append(parent_dir)
import models.base


app = Flask(__name__)

with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

utility.create_database()

Session = sessionmaker(bind=models.base.engine)
session = Session()

@app.route('/')
def index():  
    try:
        contents = utility.get_all_contents_unfiltered(session=session)
        payment_methods = utility.get_all_payment_methods(session=session)
        download_methods = utility.get_all_download_methods(session=session)
        groups = utility.get_all_groups(session=session)
    except:
        contents = []
        payment_methods = []
        download_methods = []
        groups = []
    return render_template("index.html", contents=contents,payment_methods=payment_methods,download_methods=download_methods,groups=groups)

@app.route('/query_invoices', methods=['POST'])
def query_invoices():
    try:
        run(session)
        return jsonify({'message': 'Invoices processed'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/add_new_kw_entry', methods=['POST'])
def add_new_keyword_entry():
    if request.method == 'POST':
        try:
            # Get form data
            form_data = {
                'subject': request.form.get('subject'),
                'payment_method': request.form.get('payment_methods'),
                'download_method': request.form.get('download_methods'),
                'group': request.form.get('groups'),
                'sender': request.form.get('sender')
            }
            time.sleep(3)
            message = utility.insert_keyword_api(form_data, session=session)

            return jsonify({'message': message}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
@app.route('/add_new_dwm_entry', methods=['POST'])
def add_new_download_entry():
    if request.method == 'POST':
        try:
            # Get form data
            download = request.form.get('download')
            time.sleep(3)
            message = utility.insert_download_methods_api(download, session=session)
            return jsonify({'message': message}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
@app.route('/add_new_pm_entry', methods=['POST'])
def add_new_payment_entry():
    if request.method == 'POST':
        try:
            # Get form data
            payment = request.form.get('payment')
            time.sleep(3)
            message = utility.insert_payment_methods_api(payment, session=session)
    
            return jsonify({'message': message}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
@app.route('/delete_content', methods=['DELETE'])
def delete_content_update():
    if request.method == 'DELETE':
        try:
            # Get form data
            content_id = request.form.get('delete_content')
            time.sleep(3)
            utility.delete_content(content_id, session=session)
    
            return jsonify({'message': f"Deleted the content: {content_id}"}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/add_new_group_entry', methods=['POST'])
def add_new_group_entry():
    if request.method == 'POST':
        try:
            # Get form data
            group = request.form.get('group')
            time.sleep(3)
            message = utility.insert_group_api(group, session=session)

            return jsonify({'message': message}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
@app.route('/add_new_name_under_group', methods=['POST'])
def add_new_name_under_group_entry():
    if request.method == 'POST':
        try:
            # Get form data
            new_name =  request.form.get('new_name')
            group_id = request.form.get('group')
            time.sleep(3)
            message = utility.insert_new_name_api(new_name, group_id, session=session)

            return jsonify({'message': message}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
@app.route('/submit_as_paid', methods=['POST'])
def submit_as_paid_entry():
    if request.method == 'POST':
        try:
            # Get form data
            content_id =  request.form.get('content_id')
            time.sleep(3)
            message = utility.submit_as_paid(content_id, session=session)
            return jsonify({'message': message}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    #port = int(os.environ.get('PORT', 7000))
    #app.run(debug=True, host="0.0.0.0", port=port)
    app.run(debug=False, host="0.0.0.0", port=7000)