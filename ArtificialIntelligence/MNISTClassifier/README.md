# MNIST CNN Classifier

A small PyTorch example that trains a convolutional neural network on the MNIST handwritten digit dataset. The model uses two convolutional layers with max pooling followed by two fully connected layers.

## Setup
1. Install Python dependencies (PyTorch and torchvision are required in addition to the repository defaults):
   ```bash
   pip install torch torchvision
   ```

## Running the example
Run the trainer with default settings (single epoch, full dataset) from the repository root:
```bash
python ArtificialIntelligence/MNISTClassifier/mnist_cnn.py
```

For quicker experiments on a smaller subset of the training data:
```bash
python ArtificialIntelligence/MNISTClassifier/mnist_cnn.py --subset --subset-size 2000 --epochs 2
```

Adjust `--batch-size`, `--lr`, and `--momentum` as needed. The script prints epoch metrics and a final test accuracy.
