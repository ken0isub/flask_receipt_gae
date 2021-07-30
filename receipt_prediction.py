import cv2
import pickle
from data_prep import img_prep
import numpy as np
import os

def allowed_file(filename, ALLOWED_EXTENSIONS):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def model_prediction(model_path, file_path):
    with open(model_path, mode ='rb') as fp:
        clf = pickle.load(fp)
    img = cv2.imdecode(file_path, cv2.IMREAD_COLOR)
    img = img_prep(img, gray_scale=True)
    X_sample = np.array(img)
    X_sample = X_sample.flatten()
    return clf.predict(X_sample.reshape(1, -1))[0]


def predict_receipt(file_path, model_path):
    classes = []
    with open('./models/stores_list.txt', 'r') as f:
        for c in f:
            classes.append(c.rstrip())

    ml_scores = []
    with open('models/ml_scores.txt', 'r') as f:
        for c in f:
            ml_scores.append(c.rstrip())

    models_list = os.listdir(model_path)

    prediction_1 = model_prediction(model_path + '/' + models_list[0], file_path)
    prediction_2 = model_prediction(model_path + '/' + models_list[1], file_path)
    prediction_3 = model_prediction(model_path + '/' + models_list[2], file_path)
    prediction_4 = model_prediction(model_path + '/' + models_list[3], file_path)
    prediction_5 = model_prediction(model_path + '/' + models_list[4], file_path)

    n_1 = np.zeros(len(classes))
    n_1[prediction_1] = ml_scores[0]

    n_2 = np.zeros(len(classes))
    n_2[prediction_2] = ml_scores[1]

    n_3 = np.zeros(len(classes))
    n_3[prediction_3] = ml_scores[2]

    n_4 = np.zeros(len(classes))
    n_4[prediction_4] = ml_scores[3]

    n_5 = np.zeros(len(classes))
    n_5[prediction_5] = ml_scores[4]

    pred_combined = n_1 + n_2 + n_3 + n_4 + n_5
    return classes[np.argmax(pred_combined)]
