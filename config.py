import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data paths
TRAIN_CSV = os.path.join(BASE_DIR, 'train.csv')
SRC_IMAGE_DIR = os.path.join(BASE_DIR, 'gaussian_filtered_images', 'gaussian_filtered_images')

# Working directories
DATA_DIR = os.path.join(BASE_DIR, 'data')
TRAIN_DIR = os.path.join(DATA_DIR, 'train')
VAL_DIR = os.path.join(DATA_DIR, 'val')
TEST_DIR = os.path.join(DATA_DIR, 'test')

# Model parameters
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 30
LEARNING_RATE = 1e-5

# Classes
DIAGNOSIS_DICT_BINARY = {
    0: 'No_DR',
    1: 'DR',
    2: 'DR',
    3: 'DR',
    4: 'DR'
}

DIAGNOSIS_DICT = {
    0: 'No_DR',
    1: 'Mild',
    2: 'Moderate',
    3: 'Severe',
    4: 'Proliferate_DR',
}
