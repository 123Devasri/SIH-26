import os
import tensorflow as tf
import cv2
import numpy as np
import matplotlib.pyplot as plt
import config

def predict_class(image_path, model_path="64x3-CNN.model"):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image from {image_path}")
        return

    RGBImg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    RGBImg = cv2.resize(RGBImg, config.IMAGE_SIZE)
    
    # Display image
    plt.imshow(RGBImg)
    plt.show()

    image = np.array(RGBImg) / 255.0
    
    try:
        model = tf.keras.models.load_model(model_path)
    except Exception as e:
        print(f"Error loading model from {model_path}: {e}")
        return

    predict = model.predict(np.array([image]))
    per = np.argmax(predict, axis=1)
    
    if per == 1:
        print('No DR')
    else:
        print('DR')

if __name__ == "__main__":
    # Example usage:
    # replace with an actual path to test
    sample_path = os.path.join(config.SRC_IMAGE_DIR, 'Severe', '03c85870824c.png')
    predict_class(sample_path)
