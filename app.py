import cv2
from flask import Flask, request, redirect, render_template, flash, session, url_for
from google.cloud import vision
import io
import numpy as np
import os
import re
# from tensorflow.keras.models import Sequential, load_model
# from tensorflow.keras.preprocessing import image
from werkzeug.utils import secure_filename
from receipt_prediction import allowed_file, predict_receipt
from read_receipts import read_costco, read_seven, read_lawson, read_kasumi
import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials
from to_sheet import write_sheet
from google.cloud import storage
import urllib
from datetime import datetime, timedelta


ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'del/project-delete-soon.json'
client = vision.ImageAnnotatorClient()


def allowed_file(filename, ALLOWED_EXTENSIONS):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(__name__)


# set secret_key for session
app.secret_key = b'kdjlfks3092i1@")#))('


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return redirect(request.url)
        if uploaded_file and allowed_file(uploaded_file.filename, ALLOWED_EXTENSIONS):
            filename = secure_filename(uploaded_file.filename)
            # uploaded_file.save(os.path.join(UPLOAD_FOLDER, filename))

            client = storage.Client()
            bucket = client.get_bucket('receipt_sample')
            # blob = bucket.blob(uploaded_file.filename)

            now = datetime.now()
            now_ts = now.timestamp()
            file_name = str(now_ts) + '.jpg'

            # get file_name from session
            session.permanent = True
            app.permanent_session_lifetime = timedelta(seconds=30)
            session['file_name'] = file_name

            blob = bucket.blob(file_name)
            print(uploaded_file.filename)
            print("blob: ", blob)
            print("blob name: ", blob.name)
            blob.upload_from_file(uploaded_file)

            return redirect(url_for('page2'))
    else:
        # variable (file_name) was removed
        return render_template("index.html")


@app.route('/page2/', methods=['GET', 'POST'])
def page2():
    if request.method == 'POST':
        store = request.form.get('store')
        price = request.form.get('price')
        date = request.form.get('date')
        category = request.form.get('category')
        point = request.form.get('point')
        who = request.form.get('who')
        note = request.form.get('note')

        write_sheet(price, store, category, date, note, who, point)
        return 'POST'

    # UPLOAD_FOLDER = "./static/uploads"
    # UPLOAD_FOLDER2 = "../static/uploads"
    # filepath = os.path.join(UPLOAD_FOLDER, filename)
    # filepath2 = os.path.join(UPLOAD_FOLDER2, filename)

    file_name = session['file_name']
    client = storage.Client()
    bucket = client.get_bucket('receipt_sample')
    blob2 = bucket.get_blob(file_name)

    print(blob2)

    pred_store = 'failed'
    price = 'failed'
    date_dt = 'failed'


    file_url = 'https://storage.googleapis.com/receipt_sample/' + file_name
    resp = urllib.request.urlopen(file_url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    print(image)

    pred_store = predict_receipt(image, 'models/ML')
    print(pred_store)


    #get result from google vision API
    client = vision.ImageAnnotatorClient()
    image_2 = vision.Image()
    image_2.source.image_uri = file_url
    response = client.document_text_detection(image=image_2)


    discount = ''
    if pred_store == 'costco':
        price, date_dt = read_costco(response)
    else:
        pass

    if pred_store == 'seven':
        price, date_dt = read_seven(response)
    if pred_store == 'lawson':
        price, date_dt = read_lawson(response)
    if pred_store == 'familymart':
        price, date_dt = read_lawson(response)
    if pred_store == 'kasumi':
        price, date_dt, discount = read_kasumi(response)

    print(price)

    return render_template('page2.html', filepath=blob2, price=price, store=pred_store,
                           date=date_dt, discount=discount)

if __name__ == '__main__':
    app.run(port=8080, host="0.0.0.0")
