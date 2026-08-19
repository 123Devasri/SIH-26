import tensorflow as tf
import config
from dataset import get_data_generators
from model import build_model

def train():
    print("Loading data generators...")
    train_batches, val_batches, test_batches = get_data_generators()

    print("Building model...")
    model = build_model(input_shape=(config.IMAGE_SIZE[0], config.IMAGE_SIZE[1], 3))

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=config.LEARNING_RATE),
        loss=tf.keras.losses.BinaryCrossentropy(),
        metrics=['accuracy']
    )

    print("Starting training...")
    history = model.fit(
        train_batches,
        epochs=config.EPOCHS,
        validation_data=val_batches
    )

    print("Saving model...")
    model.save('64x3-CNN.model')

    print("Evaluating model on test set...")
    loss, acc = model.evaluate(test_batches, verbose=1)
    print("Test Accuracy: ", acc)

if __name__ == "__main__":
    train()
