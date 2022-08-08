# Importing required libs
import gc
from flask import Flask, render_template, request, redirect, url_for, session, Response, flash, jsonify
from difflib import SequenceMatcher
from werkzeug.utils import secure_filename
import random
import os
from os.path import join, dirname, realpath

from modules import *
import shutil

# flask config
app = Flask(__name__)
# setting the absolute path for file upload folder
path_file = os.getcwd()  # Gets current working directory path
path_final_name = path_file + '/static/uploads/'
UPLOADS_PATH = path_final_name  # Passing it to variable store for config
app.config['UPLOAD_FOLDER'] = UPLOADS_PATH
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # File size limit 20mb


# English Cheattell check route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if request.files:
            # getting the uploaded file
            file = request.files['file']
            sourceFilter = request.form["sourceFilter"]
            if not os.path.exists(path_final_name):
                os.mkdir(path_final_name)
            # empty file name returns error
            if file.filename == "":
                return render_template('error.html')
            # file validation
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # adding the file in the uploads folder
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # getting the file path
                path = f"./static/uploads/{filename}"
                # extracting text from data
                data = extractText(path)
                # print(data)
                res = {}
                try:
                    if os.path.exists(path_final_name):
                        shutil.rmtree(path_final_name)
                    # getting the links and other attributes
                    # print(len( gc.get_objects() ) )
                    res, plagCount, total, mostProbable = checkPlag(data, sourceFilter)

                    # print(len( gc.get_objects() ))

                    # print(res)
                    return render_template('display.html', res=res, plagCount=plagCount, total=total,
                                           mostProbable=mostProbable)
                except:
                    if os.path.exists(path_final_name):
                        shutil.rmtree(path_final_name)
                    return render_template('error.html')
            else:
                if os.path.exists(path_final_name):
                    shutil.rmtree(path_final_name)
                return render_template('error.html')
        else:
            if os.path.exists(path_final_name):
                shutil.rmtree(path_final_name)
            return render_template('error.html')
    return render_template('index.html')

# English text area post route
@app.route('/textdata', methods=['POST'])
def textdata():
    if request.method == 'POST':
        try:
            # getting the text data
            data = request.form["input"]
            sourceFilter = request.form["sourceFilter"]
            if data == "":
                return render_template('error.html')
            # breaking it into sentences
            data = inputDataExtract(data)
            res = {}
            # getting the links
            res, plagCount, total, mostProbable = checkPlag(data, sourceFilter)

            # print(res)
            return render_template('display.html', res=res, plagCount=plagCount, total=total, mostProbable=mostProbable)
        except:
            return render_template('error.html')

# similar para check route
@app.route("/similarparacheck", methods=["POST", "GET"])
def similarparacheck():
    return render_template('similarparacheck.html')

# multilingual Cheattell check route
@app.route('/multilingual', methods=['GET', 'POST'])
def multilingual():
    if request.method == "POST":
        if request.files:
            # getting the uploaded file
            file = request.files["file"]
            sourceFilter = request.form["sourceFilter"]
            language = request.form['language']
            if not os.path.exists(path_final_name):
                os.mkdir(path_final_name)
            # empty file name returns error
            if file.filename == "":
                return render_template('error.html')
            # file validation
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # adding the file in the uploads folder
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # getting the file path
                path = f"./static/uploads/{filename}"
                # extracting text from data
                data, multilingualData = extractMultilingualText(path, language)
                # print(data)
                res = {}
                try:
                    if os.path.exists(path_final_name):
                        shutil.rmtree(path_final_name)
                        # getting the links and other attributes
                    res, plagCount, total, mostProbable = checkPlagNormal(data, sourceFilter)

                    # print(res)
                    return render_template('display.html', res=res, plagCount=plagCount, total=total,
                                           multilingualData=multilingualData, mostProbable=mostProbable)
                except:
                    if os.path.exists(path_final_name):
                        shutil.rmtree(path_final_name)
                    return render_template('error.html')
            else:
                if os.path.exists(path_final_name):
                    shutil.rmtree(path_final_name)
                return render_template('error.html')
        else:
            if os.path.exists(path_final_name):
                shutil.rmtree(path_final_name)
            return render_template('error.html')
    return render_template('multilingual.html')

# multilingual text area post route
@app.route('/multilingualText', methods=['POST'])
def multilingualText():
    if request.method == 'POST':
        try:
            # getting the text data
            data = request.form["input"]
            sourceFilter = request.form["sourceFilter"]
            language = request.form['language']
            if data == "":
                return render_template('error.html')
            # breaking the paragraphs in to sentences
            data, multilingualData = inputMultilingualDataExtract(data, language)

            # print(data)
            res = {}
            # getting the links
            res, plagCount, total, mostProbable = checkPlagNormal(data, sourceFilter)

            # print(res)
            return render_template('display.html', res=res, plagCount=plagCount, total=total,
                                   multilingualData=multilingualData, mostProbable=mostProbable)
        except:
            return render_template('error.html')


@app.route('/getdata', methods=['POST'])
def getdata():
    try:
        content = request.get_json()
        # data processing code
        # content['p'] -> textarea 1 content
        # content['q'] -> textarea 2 content
        # using the sequenceMatcher
        similarity = SequenceMatcher(None, content['p'], content['q']).ratio()
        similarity = similarity * 100
        similarity = int(similarity)
        sim = str(similarity)
        return jsonify({
            'status': True,
            'percentage': similarity,
            'result': "Your data is measured to be nearly " + sim + "% matchably"
        })

    except Exception as e:
        print(e)
        return jsonify({
            'status': False,
            'result': "Error in processing"
        })


@app.errorhandler(413)
def too_large(e):
    return "File size is too large.", 413


if __name__ == "__main__":
    app.run()
