
import random  # For generating random numbers
import json    # For working with JSON data
import pickle  # For serializing and deserializing Python objects
import numpy as np  # For numerical operations
import tensorflow as tf  # For building and training deep learning models

import nltk  # Natural Language Toolkit
from nltk.stem import WordNetLemmatizer  # Lemmatization for word normalization

# Initializing lemmatizer
lemmatizer = WordNetLemmatizer()

# Loading intents from JSON file
import json

with open('intents.json', encoding='utf-8') as f:
    intents = json.load(f)



# Initializing lists for words, classes, documents, and ignored letters
words = []
classes = []
documents = []
ignoreLetters = ['?', '!', '.', ',']

# Preparing words, cla'sses, and documents
for intent in intents['intents']:
    for pattern in intent['patterns']:
        # Tokenizing words in patterns
        wordList = nltk.word_tokenize(pattern)
        words.extend(wordList)
        documents.append((wordList, intent['tag']))
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

# Lemmatizing and filtering words
words = [lemmatizer.lemmatize(word) for word in words if word not in ignoreLetters]
words = sorted(set(words))
classes = sorted(set(classes))

# Saving words and classes to pickle files
pickle.dump(words, open('words.pkl', 'wb'))
pickle.dump(classes, open('classes.pkl', 'wb'))

# Initializing training data
training = []
outputEmpty = [0] * len(classes)

# Creating training data
for document in documents:
    bag = []
    wordPatterns = document[0]
    wordPatterns = [lemmatizer.lemmatize(word.lower()) for word in wordPatterns]
    for word in words:
        bag.append(1) if word in wordPatterns else bag.append(0)

    outputRow = list(outputEmpty)
    outputRow[classes.index(document[1])] = 1
    training.append(bag + outputRow)

# Shuffling and converting training data to numpy array
random.shuffle(training)
training = np.array(training)

# Splitting training data into input and output
trainX = training[:, :len(words)]
trainY = training[:, len(words):]

# Réseau neuronal FNN 
model = tf.keras.Sequential()
model.add(tf.keras.layers.Dense(128, input_shape=(len(trainX[0]),), activation='relu'))
model.add(tf.keras.layers.Dropout(0.5))
model.add(tf.keras.layers.Dense(64, activation='relu'))
model.add(tf.keras.layers.Dropout(0.5))
model.add(tf.keras.layers.Dense(len(trainY[0]), activation='softmax'))

# Compiling the model
sgd = tf.keras.optimizers.SGD(learning_rate=0.01, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

# Training the model
hist = model.fit(np.array(trainX), np.array(trainY), epochs=200, batch_size=5, verbose=1)

# Saving the trained model
model.save('chatbot_model10.h5', hist)
# Printing the model's training loss and accuracy
print("Model training loss:", hist.history['loss'][-1])
print("Model training accuracy:", hist.history['accuracy'][-1])



import matplotlib.pyplot as plt
import matplotlib.pyplot as plt

# Compiling the model with accuracy as a metric
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

# Training the model with validation data
hist = model.fit(np.array(trainX), np.array(trainY), epochs=200, batch_size=5, verbose=1, validation_split=0.1)

# Saving the trained model
model.save('chatbot_model10.h5', hist)

# Printing the model's training loss, accuracy, and validation loss
print("Model training loss:", hist.history['loss'][-1])
print("Model training accuracy:", hist.history['accuracy'][-1])
print("Model validation loss:", hist.history['val_loss'][-1])

# Plotting training and validation loss
plt.plot(hist.history['loss'], label='Training Loss')
plt.plot(hist.history['val_loss'], label='Validation Loss')
plt.title('Training and Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

# Plotting training and validation accuracy
plt.plot(hist.history['accuracy'], label='Training Accuracy')
plt.plot(hist.history['val_accuracy'], label='Validation Accuracy')
plt.title('Training and Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.show()

# Printing 'Done' when finished
print('Done')
