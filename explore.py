import pandas as pd
import matplotlib.pyplot as plt
import config

def explore_data():
    df = pd.read_csv(config.TRAIN_CSV)
    df['binary_type'] = df['diagnosis'].map(config.DIAGNOSIS_DICT_BINARY.get)
    df['type'] = df['diagnosis'].map(config.DIAGNOSIS_DICT.get)

    print("Class distribution (Fine-grained):")
    print(df['type'].value_counts())
    
    # Plot fine-grained
    df['type'].value_counts().plot(kind='barh', title='Fine-grained Class Distribution')
    plt.show()

    print("\nClass distribution (Binary):")
    print(df['binary_type'].value_counts())
    
    # Plot binary
    df['binary_type'].value_counts().plot(kind='barh', title='Binary Class Distribution')
    plt.show()

if __name__ == "__main__":
    explore_data()
