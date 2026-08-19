from tensorflow.keras.preprocessing.image import ImageDataGenerator
import config

def get_data_generators():
    train_datagen = ImageDataGenerator(rescale=1./255)
    val_datagen = ImageDataGenerator(rescale=1./255)
    test_datagen = ImageDataGenerator(rescale=1./255)

    train_batches = train_datagen.flow_from_directory(
        config.TRAIN_DIR, 
        target_size=config.IMAGE_SIZE, 
        batch_size=config.BATCH_SIZE,
        shuffle=True
    )
    val_batches = val_datagen.flow_from_directory(
        config.VAL_DIR, 
        target_size=config.IMAGE_SIZE, 
        batch_size=config.BATCH_SIZE,
        shuffle=True
    )
    test_batches = test_datagen.flow_from_directory(
        config.TEST_DIR, 
        target_size=config.IMAGE_SIZE, 
        batch_size=config.BATCH_SIZE,
        shuffle=False
    )

    return train_batches, val_batches, test_batches
