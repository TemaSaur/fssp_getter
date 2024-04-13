import tensorflow as tf
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers


num_to_char = {'0': '2', '1': '4', '2': '5', '3': '6', '4': '7', '5': '8', '6': '9', '7': 'б', '8': 'в', '9': 'г', '10': 'д', '11': 'ж', '12': 'к', '13': 'л', '14': 'м', '15': 'н', '16': 'п', '17': 'р', '18': 'с', '19': 'т', '-1': 'UKN'}


def create_test_dataset():
	img = tf.io.read_file(f"./temp.jpg")
	img = tf.io.decode_jpeg(img, channels=3) 
	img = tf.image.convert_image_dtype(img, tf.float32)
	img = tf.transpose(img, perm=[1, 0, 2])
	img = img.numpy()
	X = np.asarray([img])
	return X


m = keras.models.load_model('model.h5', compile=False)

def test_current():
	X_test = create_test_dataset()

	test_pred = m.predict(X_test)
	test_pred = keras.backend.ctc_decode(test_pred, input_length=np.ones(X_test.shape[0])*50, greedy=True)
	test_pred = test_pred[0][0][0:X_test.shape[0],0:7].numpy()

	answers = ["".join(list(map(lambda x:num_to_char[str(x)], label))).replace("UKN",'') for label in test_pred]
	return answers[0]
