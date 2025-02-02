import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import time
import copy
import torch
from torchvision import transforms, datasets

import torch
import torchvision
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms
from torch.utils.data import DataLoader, TensorDataset
from torchvision.utils import make_grid

from torchsummary import summary
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable

from sklearn.metrics import precision_recall_fscore_support
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
import seaborn as sns

from google.colab import drive
drive.mount('/content/drive')

!unzip cnn_dataset.zip

# Initializing transformations for the dataset
# Converting images to grayscale with one channel

transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.ToTensor(),
])

base_directory = "cnn_dataset"

image_data = datasets.ImageFolder(root=base_directory, transform=transform)

print(f"Number of classes: {len(image_data.classes)}")
print(f"Class names: {image_data.classes}")
print(f"Number of images: {len(image_data)}")

def plot_class_distribution_pie(dataset, figsize=(10, 10), label_distance=1.1):
    labels = [label for i, label in dataset]
    unique_labels, counts = np.unique(labels, return_counts=True)

    plt.figure(figsize=figsize)
    patches, texts, autotexts = plt.pie(counts, labels=unique_labels, autopct=lambda p: f'{p:.1f}%%', startangle=90)

    for text, autotext in zip(texts, autotexts):
        text.set(size='small')
        autotext.set(size='small')
        autotext.set(va='center')
    plt.axis('equal')
    plt.title('Pie Chart representation of different classes ')
    plt.show()

plot_class_distribution_pie(image_data)

def fetch_mean_and_std(dataset):
    mean = torch.zeros(1)
    std = torch.zeros(1)
    squared_sum = torch.zeros(1)
    total_pixels = 0

    for data in dataset:
        img = data[0]
        img = img.view(1, -1)
        total_pixels += img.size(1)

        mean += img.mean(dim=1)
        squared_sum += img.pow(2).mean(dim=1)

    mean /= len(dataset)
    var = (squared_sum / len(dataset)) - mean.pow(2)
    std = torch.sqrt(var)

    return mean, std

mean, std = fetch_mean_and_std(image_data)

print(f"Mean of dataset: {mean}")
print(f"Standard deviation of dataset: {std}")

transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.ToTensor(),
    transforms.Normalize((0.1758,), (0.3337,))
])

base_directory = "cnn_dataset"

normalized_image_data = datasets.ImageFolder(root=base_directory, transform=transform)

normalized_image_data

len(normalized_image_data)

# Splitiing the dataset into train, validation and test

image_data_size = len(normalized_image_data)
train_size = int(0.8 * image_data_size)
validation_size = int(0.1 * image_data_size)

test_size = image_data_size - (train_size + validation_size)

train_dataset, validation_dataset, test_dataset = random_split(normalized_image_data, [train_size, validation_size, test_size])

# Create data loaders
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, num_workers=2)
validation_loader = DataLoader(validation_dataset, batch_size=64, shuffle=False, num_workers=2)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False, num_workers=2)

len(train_dataset)

train_loader, validation_loader, test_loader

print(f"Number of classes: {len(image_data.classes)}")
print(f"Class names: {image_data.classes}")
print(f"Number of images: {len(image_data)}")

normalized_image_data[0][0].shape

class ImageClassificationNet(nn.Module):
    def __init__(self, classes):
        super(ImageClassificationNet, self).__init__()

        self.convolution_block = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.linear_block = nn.Sequential(
            nn.Dropout(p=0.5),
            nn.Linear(128 * 7 * 7, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(64, classes)
        )

    def forward(self, X):
        X = self.convolution_block(X)
        X = X.view(X.size(0), -1)
        X = self.linear_block(X)
        return X

len(test_loader)

classification_model = ImageClassificationNet(classes=36)

# classification_model = classification_model.cuda()
input_size = (1, 28, 28)

print(classification_model)
# Print the summary of your model
summary(classification_model, input_size=input_size,batch_size = 64)

learning_rate = 0.001
batch_size = 64
epochs = 10

# Loss function
criterion = nn.CrossEntropyLoss()
# classification_model = classification_model.to(torch.device('cuda'))
# Optimizer
optimizer = optim.Adam(classification_model.parameters(), lr=learning_rate)

start_time = time.time()

train_losses = []
train_accuracies = []
valid_losses = []
valid_accuracies = []
test_losses = []
test_accuracies = []

for epoch in range(epochs):
    classification_model.train()
    running_loss = 0.0
    correct_preds = 0
    total_preds = 0
    for i, (images, labels) in enumerate(train_loader):
       ## labels = labels.to(torch.device('cuda'))
        # Forward pass
        outputs = classification_model(images)
        loss = criterion(outputs, labels)

        # Backward and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        _, predicted = torch.max(outputs.data, 1)
        total_preds += labels.size(0)
        correct_preds += (predicted == labels).sum().item()

        if (i+1) % 100 == 0:
            print(f'Epoch [{epoch+1}/{epochs}], Step [{(i+1) * len(images)} /{len(train_loader.dataset)}], Loss: {loss.item():.4f}')


    train_losses.append(running_loss / len(train_loader))
    accuracy = 100.0 * correct_preds / total_preds
    train_accuracies.append(accuracy)

    # Validation phase
    classification_model.eval()
    running_loss = 0.0
    correct_preds = 0
    total_preds = 0
    for i, (images, labels) in enumerate(validation_loader):
        #images = images.to(torch.device('cuda'))
        #labels = labels.to(torch.device('cuda'))
        outputs = classification_model(images)
        loss = criterion(outputs, labels)
        running_loss += loss.item()

        _, predicted = torch.max(outputs.data, 1)
        total_preds += labels.size(0)
        correct_preds += (predicted == labels).sum().item()

    valid_losses.append(running_loss / len(validation_loader))
    accuracy = 100.0 * correct_preds / total_preds
    valid_accuracies.append(accuracy)

    # Print statistics
    print(f'Epoch {epoch+1}/{epochs}')
    print(f'Training Loss: {train_losses[-1]:.4f}')
    print(f'Validation Loss: {valid_losses[-1]:.4f}')
    print(f'Validation Accuracy: {accuracy:.2f}%')

    # Test phase
    classification_model.eval()
    running_loss = 0.0
    correct_preds = 0
    total_preds = 0
    with torch.no_grad():
        for images, labels in test_loader:
            #images = images.to(torch.device('cuda'))
            #labels = labels.to(torch.device('cuda'))
            outputs = classification_model(images)
            loss = criterion(outputs, labels)
            running_loss += loss.item()

            _, predicted = torch.max(outputs.data, 1)
            total_preds += labels.size(0)
            correct_preds += (predicted == labels).sum().item()

        test_losses.append(running_loss / len(test_loader))


        accuracy = 100.0 * correct_preds / total_preds
        test_accuracies.append(accuracy)
        print(f'Test Loss: {test_losses[-1]:.4f}')
        print(f'Test Accuracy: {accuracy:.2f}%')

total_time = time.time() - start_time
print(f'Training complete in {total_time // 60:.0f}m {total_time % 60:.0f}s')

# Getting the inmportant metrics for the model
def get_metrics(true_labels, predictions):
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

    accuracy = accuracy_score(true_labels, predictions) # Accuracy\
    precision, recall, f1_score, _ = precision_recall_fscore_support(true_labels, predictions, average='weighted', zero_division=0)

    print(f'Acuracy of the model: {accuracy:.4f}')
    print(f'Precision of the model: {precision:.4f}')
    print(f'Recall of the model: {recall:.4f}')
    print(f'F1 score of the model: {f1_score:.4f}')


# Plotting Confusion Matrix
def plot_confusion_matrix(y_test, y_pred):
    confusion = confusion_matrix(y_test, y_pred)

    plt.figure(figsize=(7, 7))
    sns.heatmap(confusion, annot=True, fmt="d", cmap="Blues")
    plt.xlabel('Predicted Values')
    plt.ylabel('True Values')
    plt.title('Plot for Confusion Matrix')
    plt.show()


# Plotting relation between losses
def plot_loss(training_loss, validation_loss, testing_loss):
    plt.figure(figsize=(10, 6))
    plt.plot(list(range(1, len(training_loss) + 1)), training_loss, label='Training Loss')
    plt.plot(list(range(1, len(validation_loss) + 1)), validation_loss, label='Validation Loss')
    plt.plot(list(range(1, len(testing_loss) + 1)), testing_loss, label='Test Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Loss Comparison')
    plt.legend()
    plt.show()

# Plotting relation between accuracies
def plot_accuracies(training_accuracy, validation_accuracy, testing_accuracy):
    plt.figure(figsize=(20, 10))
    plt.subplot(1, 2, 1)
    plt.plot(list(range(1, len(training_accuracy) + 1)), training_accuracy, label='Training Accuracy')
    plt.plot(list(range(1, len(validation_accuracy) + 1)), validation_accuracy, label='Validation Accuracy')
    plt.plot(list(range(1, len(testing_accuracy) + 1)), testing_accuracy, label='Test Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.title('Accuracy Comparison')
    plt.legend()
    plt.show()

get_metrics(true_labels, predictions)

plot_confusion_matrix(true_labels, predictions)

from sklearn.metrics import roc_curve, auc
y_true = true_labels
y_pred = probabilities
n_classes = 36
fpr = dict()
tpr = dict()
roc_auc = dict()

for i in range(n_classes):
    y_true_one_vs_all = [1 if label == i else 0 for label in y_true]
    fpr[i], tpr[i], _ = roc_curve(y_true_one_vs_all, [y[i] for y in y_pred])
    roc_auc[i] = auc(fpr[i], tpr[i])

# Plot ROC curves
plt.figure(figsize=(12, 8))
colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']  # Add more colors as needed

for i in range(n_classes):
    plt.plot(fpr[i], tpr[i], color=colors[i//7], lw=2, label=f'Class {i} (AUC = {roc_auc[i]:.2f})')

plt.plot([0, 1], [0, 1], color='black', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve for Multiclass Classification')
plt.legend(loc='lower right')
plt.show()

plot_loss(train_losses, valid_losses, test_losses)

plot_accuracies(train_accuracies, valid_accuracies, test_accuracies)

from google.colab import drive
drive.mount('/content/gdrive')

# Saving the model
torch.save(classification_model.state_dict(), '/content/gdrive/My Drive/amruthap_CNN.h5')
print(f"Model weights are saved successfuly")





class ImageClassificationNet(nn.Module):
    def __init__(self, classes):
        super(ImageClassificationNet, self).__init__()

        self.convolution_block = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.SELU(inplace=True),
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.SELU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.SELU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )

        self.linear_block = nn.Sequential(
            nn.Dropout(p=0.5),
            nn.Linear(256 * 7 * 7, 256),
            nn.BatchNorm1d(256),
            nn.SELU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.SELU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.SELU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(64, classes)
        )

    def forward(self, X):
        X = self.convolution_block(X)
        X = X.view(X.size(0), -1)
        X = self.linear_block(X)
        return X

classification_model = ImageClassificationNet(classes=36)
classification_model = classification_model.to(torch.device('cuda'))
input_size = (1, 28, 28)

print(classification_model)
# Print the summary of your model
summary(classification_model, input_size=input_size)

learning_rate = 0.01
batch_size = 64
epochs = 10

# Loss function
criterion = nn.CrossEntropyLoss()
# classification_model = classification_model.to(torch.device('cuda'))
# Optimizer
optimizer = optim.RMSprop(classification_model.parameters(), lr=learning_rate)

start_time = time.time()

train_losses = []
train_accuracies = []
valid_losses = []
valid_accuracies = []
test_losses = []
test_accuracies = []

for epoch in range(epochs):
    classification_model.train()
    running_loss = 0.0
    correct_preds = 0
    total_preds = 0
    for i, (images, labels) in enumerate(train_loader):
        images = images.to(torch.device('cuda'))
        labels = labels.to(torch.device('cuda'))
        # Forward pass
        outputs = classification_model(images)
        loss = criterion(outputs, labels)

        # Backward and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

        _, predicted = torch.max(outputs.data, 1)
        total_preds += labels.size(0)
        correct_preds += (predicted == labels).sum().item()

        if (i+1) % 100 == 0:
            print(f'Epoch [{epoch+1}/{epochs}], Step [{(i+1) * len(images)} /{len(train_loader.dataset)}], Loss: {loss.item():.4f}')


    train_losses.append(running_loss / len(train_loader))
    accuracy = 100.0 * correct_preds / total_preds
    train_accuracies.append(accuracy)

    # Validation phase
    classification_model.eval()
    running_loss = 0.0
    correct_preds = 0
    total_preds = 0
    for i, (images, labels) in enumerate(validation_loader):
        images = images.to(torch.device('cuda'))
        labels = labels.to(torch.device('cuda'))
        outputs = classification_model(images)
        loss = criterion(outputs, labels)
        running_loss += loss.item()

        _, predicted = torch.max(outputs.data, 1)
        total_preds += labels.size(0)
        correct_preds += (predicted == labels).sum().item()

    valid_losses.append(running_loss / len(validation_loader))
    accuracy = 100.0 * correct_preds / total_preds
    valid_accuracies.append(accuracy)

    # Print statistics
    print(f'Epoch {epoch+1}/{epochs}')
    print(f'Training Loss: {train_losses[-1]:.4f}')
    print(f'Validation Loss: {valid_losses[-1]:.4f}')
    print(f'Validation Accuracy: {accuracy:.2f}%')

    # Test phase
    classification_model.eval()
    running_loss = 0.0
    correct_preds = 0
    total_preds = 0
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(torch.device('cuda'))
            labels = labels.to(torch.device('cuda'))
            outputs = classification_model(images)
            loss = criterion(outputs, labels)
            running_loss += loss.item()

            _, predicted = torch.max(outputs.data, 1)
            total_preds += labels.size(0)
            correct_preds += (predicted == labels).sum().item()

        test_losses.append(running_loss / len(test_loader))


        accuracy = 100.0 * correct_preds / total_preds
        test_accuracies.append(accuracy)
        print(f'Test Loss: {test_losses[-1]:.4f}')
        print(f'Test Accuracy: {accuracy:.2f}%')

total_time = time.time() - start_time
print(f'Training complete in {total_time // 60:.0f}m {total_time % 60:.0f}s')





