import imageio
import os
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt

import genart.tf.chinese.model as model
import genart.tf.chinese.data as data

def generate_and_save_images(model, test_input, out_path, figsize):
    # Notice `training` is set to False.
    # This is so all layers run in inference mode (batchnorm).
    predictions = model(test_input, training=False)

    fig = plt.figure(figsize=figsize)

    for i in range(predictions.shape[0]):
        plt.subplot(figsize[0], figsize[0], i+1)
        plt.imshow(predictions[i, :, :, 0] * 127.5 + 127.5, cmap='gray')
        plt.axis('off')

    plt.savefig(out_path)
    plt.close()

def render_canned_images():
    png_dir = './data/chinese_output/'
    images = []
    file_names = os.listdir(png_dir)

    def sortkey(x):
        o = x[:-4].split('_')[-1]
        return int(o)

    file_names = sorted([f for f in file_names if f.endswith('.png')], key=sortkey)

    for file_name in file_names:    
        file_path = os.path.join(png_dir, file_name)
        images.append(imageio.imread(file_path))
    
    imageio.mimsave('testa.gif', images)

def render_interp():    
    latent_size = 100
    num_ts = 100
    figsize = (2,2)
    checkpoint_dir = './data/chinese_output/'
    out_gif = './data/chinese.gif'
    num_examples_to_generate = figsize[0]*figsize[1]
    num_seeds = 3
    
    seeds = [ tf.random.normal([num_examples_to_generate, latent_size]) for _ in range(num_seeds) ]
    
    generator, discriminator = model.build_gan(latent_size=latent_size)    

    generator_optimizer = tf.keras.optimizers.Adam(1e-5)
    discriminator_optimizer = tf.keras.optimizers.Adam(4e-5)

    
    checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt")
    checkpoint = tf.train.Checkpoint(generator_optimizer=generator_optimizer,
                                     discriminator_optimizer=discriminator_optimizer,
                                     generator=generator,
                                     discriminator=discriminator)

    manager = tf.train.CheckpointManager(checkpoint, checkpoint_prefix, max_to_keep=3)                                    

    checkpoint.restore(manager.latest_checkpoint)

    ts = np.linspace(0,1,num_ts,endpoint=False)
    out_images = []
    for si in range(num_seeds):        
        snext = si+1 if si < (num_seeds-1) else 0

        print("seed",si,snext)
        
        seed1 = seeds[si]
        seed2 = seeds[snext]

        for ti,t in enumerate(ts):
            print("t",ti,t)
            seed = seed1*(1-t) + seed2*t
            file_name = 'tmp.png'
            generate_and_save_images(generator, seed, file_name, figsize)
            out_images.append(imageio.imread(file_name))
    
    imageio.mimsave(out_gif, out_images, duration=0.02)

def render_class_interp():
    latent_size = 100
    num_ts = 100
    figsize = (2,2)
    checkpoint_dir = './data/chinese_class_output/'
    out_gif = './data/chinese_class.gif'
    num_examples_to_generate = figsize[0]*figsize[1]
    num_seeds = 3
    
    df = data.load()       
    font_lut =  data.font_lut(df['font'])
    all_fonts = font_lut.values()
    
    seeds = [ tf.random.normal([num_examples_to_generate, latent_size]) for _ in range(num_seeds) ]
    seed_classes = [ tf.one_hot(tf.random.uniform([num_examples_to_generate], minval=1, maxval=len(data.CharacterClass), dtype=tf.dtypes.int32), depth=len(data.CharacterClass)) for _ in range(num_seeds) ]
    seed_fonts = [ tf.one_hot(tf.random.uniform([num_examples_to_generate], minval=1, maxval=len(all_fonts), dtype=tf.dtypes.int32), depth=len(all_fonts)) for _ in range(num_seeds) ]
    
    generator, discriminator = model.build_class_gan(latent_size=latent_size, num_fonts=len(all_fonts))    

    generator_optimizer = tf.keras.optimizers.Adam(1e-5)
    discriminator_optimizer = tf.keras.optimizers.Adam(4e-5)

    
    checkpoint_prefix = os.path.join(checkpoint_dir, "ckpt")
    checkpoint = tf.train.Checkpoint(generator_optimizer=generator_optimizer,
                                     discriminator_optimizer=discriminator_optimizer,
                                     generator=generator,
                                     discriminator=discriminator)

    manager = tf.train.CheckpointManager(checkpoint, checkpoint_prefix, max_to_keep=3)                                    

    checkpoint.restore(manager.latest_checkpoint)

    ts = np.linspace(0,1,num_ts,endpoint=False)
    out_images = []
    for si in range(num_seeds):        
        snext = si+1 if si < (num_seeds-1) else 0

        print("seed",si,snext)
        
        seed_1 = seeds[si]
        seed_class_1 = seed_classes[si]
        seed_font_1 = seed_fonts[si]
        
        seed_2 = seeds[snext]
        seed_class_2 = seed_classes[snext]
        seed_font_2 = seed_fonts[snext]

        for ti,t in enumerate(ts):
            print("t",ti,t)
            seed = seed_1*(1-t) + seed_2*t
            seed_class = seed_class_1*(1-t) + seed_class_2*t
            seed_font = seed_font_1*(1-t) + seed_font_2*t

            file_name = 'tmp.png'
            generate_and_save_images(generator, [seed, seed_class, seed_font], file_name, figsize)
            out_images.append(imageio.imread(file_name))
    
    imageio.mimsave(out_gif, out_images, duration=0.02)

if __name__ == "__main__":
    render_class_interp()