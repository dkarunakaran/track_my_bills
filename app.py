from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import sqlite3
from collections import defaultdict
from sqlitedb import SqliteDB
import time
from main import run
import yaml
import csv
from utility import create_database


app = Flask(__name__)
#sql_db = SqliteDB()
with open("config.yaml") as f:
    cfg = yaml.load(f, Loader=yaml.FullLoader)

create_database()

@app.route('/')
def index():
    conn = sqlite3.connect('data/data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Content') 
    contents = cursor.fetchall()
    cursor.execute("SELECT * FROM Payment_methods")
    payment_methods = cursor.fetchall()
    cursor.execute("SELECT * FROM Download_methods")
    download_methods = cursor.fetchall()
    conn.close()
    return render_template("index.html", contents=contents,payment_methods=payment_methods,download_methods=download_methods)

@app.route('/query_invoices', methods=['POST'])
def query_invoices():
    try:
        run()
        return jsonify({'message': 'Invoices processed'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/add_new_kw_entry', methods=['POST'])
def add_new_keyword_entry():
    if request.method == 'POST':
        try:
            # Get form data
            subject = request.form.get('subject')
            payment_method = request.form.get('payment_methods')
            download_method = request.form.get('download_methods')
            sender = request.form.get('sender')
            time.sleep(3)
            conn = sqlite3.connect('data/data.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT id FROM Keywords where subject LIKE '%{subject}%' and sender LIKE '%{sender}%'") 
            keyword_id = cursor.fetchone()

            # No such keywords in the db 
            if keyword_id is None:
                
                # Get the payment_id
                query = f"SELECT payment_method_id FROM Payment_methods where payment_method_id={payment_method}"
                cursor.execute(query)
                payment_id = cursor.fetchone()[0]

                # Get the download_id
                query = f"SELECT download_method_id FROM Download_methods where download_method_id={download_method}"
                cursor.execute(query)
                download_id = cursor.fetchone()[0]

                cursor.execute("""INSERT INTO Keywords (subject, payment_method_id, download_method_id, sender) VALUES (?, ?, ?, ?)""", [subject, payment_id, download_id, sender])
                conn.commit()  
                message = 'Form submitted successfully!'
            else:
                message = 'Data exists already'

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
            conn = sqlite3.connect('data/data.db')
            cursor = conn.cursor()
            query = f"SELECT download_method_id FROM Download_methods where name LIKE '%{download}%'"
            cursor.execute(query)
            id = cursor.fetchone()
            # No such method in the db 
            if id is None:
                cursor.execute("""INSERT INTO Download_methods (name) VALUES (?)""", [download])
                conn.commit()        
                message = 'Form submitted successfully!'
            else:
                message = 'Data exists already'

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
            conn = sqlite3.connect('data/data.db')
            cursor = conn.cursor()
            query = f"SELECT payment_method_id FROM Payment_methods where name LIKE '%{payment}%'"
            cursor.execute(query)
            id = cursor.fetchone()
            # No such method in the db 
            if id is None:
                cursor.execute("""INSERT INTO Payment_methods (name) VALUES (?)""", [payment])
                conn.commit()        
                message = 'Form submitted successfully!'
            else:
                message = 'Data exists already'

            return jsonify({'message': message}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7000))
    app.run(debug=True, host='0.0.0.0', port=port)