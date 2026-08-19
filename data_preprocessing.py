import os
import shutil
import pandas as pd
from sklearn.model_selection import train_test_split
import config

def preprocess_data():
    # Load and map types
    df = pd.read_csv(config.TRAIN_CSV)
    df['binary_type'] = df['diagnosis'].map(config.DIAGNOSIS_DICT_BINARY.get)
    df['type'] = df['diagnosis'].map(config.DIAGNOSIS_DICT.get)

    # Split dataset
    train_intermediate, val = train_test_split(df, test_size=0.15, stratify=df['type'])
    train, test = train_test_split(train_intermediate, test_size=0.15 / (1 - 0.15), stratify=train_intermediate['type'])

    print("Train class distribution:\n", train['type'].value_counts())
    print("Test class distribution:\n", test['type'].value_counts())
    print("Validation class distribution:\n", val['type'].value_counts())

    # Create directories
    for dir_path in [config.TRAIN_DIR, config.VAL_DIR, config.TEST_DIR]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
        os.makedirs(dir_path)

    def copy_images(df_split, dest_dir):
        for index, row in df_split.iterrows():
            diagnosis = row['type']
            binary_diagnosis = row['binary_type']
            id_code = row['id_code'] + ".png"
            srcfile = os.path.join(config.SRC_IMAGE_DIR, diagnosis, id_code)
            dstfile = os.path.join(dest_dir, binary_diagnosis)
            os.makedirs(dstfile, exist_ok=True)
            # Only copy if source file exists
            if os.path.exists(srcfile):
                shutil.copy(srcfile, dstfile)
            else:
                print(f"Warning: Source file not found: {srcfile}")

    print("Copying training images...")
    copy_images(train, config.TRAIN_DIR)
    
    print("Copying validation images...")
    copy_images(val, config.VAL_DIR)
    
    print("Copying testing images...")
    copy_images(test, config.TEST_DIR)
    
    print("Data preprocessing complete.")

if __name__ == "__main__":
    preprocess_data()
