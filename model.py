import tensorflow as tf
from tensorflow.keras import layers

def build_model(input_shape=(224, 224, 3)):
    model = tf.keras.Sequential([
        layers.Conv2D(8, (3,3), padding="valid", input_shape=input_shape, activation='relu'),
        layers.MaxPooling2D(pool_size=(2,2)),
        layers.BatchNormalization(),
        
        layers.Conv2D(16, (3,3), padding="valid", activation='relu'),
        layers.MaxPooling2D(pool_size=(2,2)),
        layers.BatchNormalization(),
        
        layers.Conv2D(32, (4,4), padding="valid", activation='relu'),
        layers.MaxPooling2D(pool_size=(2,2)),
        layers.BatchNormalization(),
    
        layers.Flatten(),
        layers.Dense(32, activation='relu'),
        layers.Dropout(0.15),
        layers.Dense(2, activation='softmax')
    ])
    return model
