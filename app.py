from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import sys
import argparse
import cv2
import sqlite3
import re
import pandas as pd
from collections import defaultdict

app = Flask(__name__)

@app.route('/')
def hello_world():
    """
    A simple route that returns a JSON response.

    Returns:
        dict: A dictionary containing a greeting message.
    """
    return jsonify({'message': 'Hello, World!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)