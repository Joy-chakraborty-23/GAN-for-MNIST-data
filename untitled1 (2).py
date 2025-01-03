# -*- coding: utf-8 -*-
"""Untitled1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1svKGrboOfmkc3q3D5Qqai-0I-fXt02MK
"""

import tensorflow as tf
from tensorflow.keras import layers
import numpy as np
import matplotlib.pyplot as plt
import os

# Set random seeds for reproducibility
tf.random.set_seed(42)
np.random.seed(42)

# Load and preprocess the dataset
def load_data():
    dataset_name = 'mnist'  # Change this to the desired dataset from TensorFlow Datasets
    (x_train, _), (_, _) = getattr(tf.keras.datasets, dataset_name).load_data()
    x_train = x_train.reshape(x_train.shape[0], 28, 28, 1).astype('float32')
    x_train = (x_train - 127.5) / 127.5  # Normalize to [-1, 1]
    return x_train

# Generator Model
def build_generator():
    model = tf.keras.Sequential()
    model.add(layers.Dense(7 * 7 * 128, use_bias=False, input_shape=(100,)))
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU())

    model.add(layers.Reshape((7, 7, 128)))
    model.add(layers.Conv2DTranspose(128, (5, 5), strides=(1, 1), padding='same', use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU())

    model.add(layers.Conv2DTranspose(64, (5, 5), strides=(2, 2), padding='same', use_bias=False))
    model.add(layers.BatchNormalization())
    model.add(layers.LeakyReLU())

    model.add(layers.Conv2DTranspose(1, (5, 5), strides=(2, 2), padding='same', use_bias=False, activation='tanh'))

    return model

# Discriminator Model
def build_discriminator():
    model = tf.keras.Sequential()
    model.add(layers.Conv2D(64, (3, 3), strides=(2, 2), padding='same', input_shape=[28, 28, 1]))
    model.add(layers.LeakyReLU())
    model.add(layers.Dropout(0.3))

    model.add(layers.Conv2D(128, (3, 3), strides=(2, 2), padding='same'))
    model.add(layers.LeakyReLU())
    model.add(layers.Dropout(0.3))

    model.add(layers.Flatten())
    model.add(layers.Dense(1))

    return model

# Loss Functions and Optimizers
def generator_loss(fake_output):
    return tf.keras.losses.BinaryCrossentropy(from_logits=True)(tf.ones_like(fake_output), fake_output)

def discriminator_loss(real_output, fake_output):
    real_loss = tf.keras.losses.BinaryCrossentropy(from_logits=True)(tf.ones_like(real_output), real_output)
    fake_loss = tf.keras.losses.BinaryCrossentropy(from_logits=True)(tf.zeros_like(fake_output), fake_output)
    return real_loss + fake_loss

generator_optimizer = tf.keras.optimizers.Adam(1e-4)
discriminator_optimizer = tf.keras.optimizers.Adam(1e-4)

# Training Step
@tf.function
def train_step(images, generator, discriminator):
    noise = tf.random.normal([BATCH_SIZE, NOISE_DIM])

    with tf.GradientTape() as gen_tape, tf.GradientTape() as disc_tape:
        generated_images = generator(noise, training=True)

        real_output = discriminator(images, training=True)
        fake_output = discriminator(generated_images, training=True)

        gen_loss = generator_loss(fake_output)
        disc_loss = discriminator_loss(real_output, fake_output)

    gradients_of_generator = gen_tape.gradient(gen_loss, generator.trainable_variables)
    gradients_of_discriminator = disc_tape.gradient(disc_loss, discriminator.trainable_variables)

    generator_optimizer.apply_gradients(zip(gradients_of_generator, generator.trainable_variables))
    discriminator_optimizer.apply_gradients(zip(gradients_of_discriminator, discriminator.trainable_variables))

    return gen_loss, disc_loss

# Training Loop
def train(dataset, epochs, generator, discriminator):
    gen_losses = []
    disc_losses = []

    for epoch in range(epochs):
        gen_loss_avg = 0
        disc_loss_avg = 0
        step = 0

        for image_batch in dataset:
            gen_loss, disc_loss = train_step(image_batch, generator, discriminator)
            gen_loss_avg += gen_loss
            disc_loss_avg += disc_loss
            step += 1

        gen_loss_avg /= step
        disc_loss_avg /= step

        gen_losses.append(gen_loss_avg)
        disc_losses.append(disc_loss_avg)

        print(f"Epoch {epoch + 1}/{epochs}, Generator Loss: {gen_loss_avg:.4f}, Discriminator Loss: {disc_loss_avg:.4f}")

        # Generate and save images
        generate_and_save_images(generator, epoch + 1, tf.random.normal([16, NOISE_DIM]))

    # Plot the losses
    plot_losses(gen_losses, disc_losses)

# Plot Losses
def plot_losses(gen_losses, disc_losses):
    plt.figure(figsize=(10, 6))
    plt.plot(gen_losses, label='Generator Loss')
    plt.plot(disc_losses, label='Discriminator Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.title('Generator and Discriminator Loss Over Epochs')
    plt.legend()
    plt.grid(True)
    plt.show()

# Generate and Save Images
def generate_and_save_images(model, epoch, test_input):
    predictions = model(test_input, training=False)
    fig = plt.figure(figsize=(4, 4))

    for i in range(predictions.shape[0]):
        plt.subplot(4, 4, i + 1)
        plt.imshow(predictions[i, :, :, 0] * 127.5 + 127.5, cmap='gray')
        plt.axis('off')

    plt.savefig(f'epoch_{epoch}.png')
    plt.show()

# Hyperparameters
BUFFER_SIZE = 60000
BATCH_SIZE = 128
NOISE_DIM = 100
EPOCHS = 1000

# Main
if __name__ == "__main__":
    # Load data
    train_data = load_data()
    train_dataset = tf.data.Dataset.from_tensor_slices(train_data).shuffle(BUFFER_SIZE).batch(BATCH_SIZE)

    # Build models
    generator = build_generator()
    discriminator = build_discriminator()

    # Train models
    train(train_dataset, EPOCHS, generator, discriminator)

    # Save generator for testing
    generator.save("gan_generator.h5")