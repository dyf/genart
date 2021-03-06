import tensorflow as tf
from tensorflow.keras.layers import Conv2D, Conv2DTranspose, BatchNormalization, ReLU, LeakyReLU, Dropout, Input, Activation, ZeroPadding2D, Concatenate
from tensorflow.keras import Model
from tensorflow.keras.models import Sequential

def upsample(filters, size, apply_dropout=False):
    initializer = tf.random_normal_initializer(0., 0.02)

    result = Sequential()
    result.add(
        Conv2DTranspose(filters, size, strides=2,
                        padding='same',
                        kernel_initializer=initializer,
                        use_bias=False)
    )

    result.add(BatchNormalization())

    if apply_dropout:
        result.add(Dropout(0.5))

    result.add(ReLU())

    return result

def downsample(filters, size, apply_batchnorm=True):
    initializer = tf.random_normal_initializer(0., 0.02)

    result = Sequential()
    result.add(
        Conv2D(filters, size, strides=2, padding='same',
               kernel_initializer=initializer, use_bias=False)
    )

    if apply_batchnorm:
        result.add(BatchNormalization())

    result.add(LeakyReLU())

    return result

def UpScaleModel(levels=2):
    inputs = Input(shape=[None,None,3])
    x = inputs    

    for level in range(levels):
        x = upsample(64, 4, apply_dropout=True)(x)

    initializer = tf.random_normal_initializer(0., 0.02)
    last = Conv2D(3, 4, padding='same', activation='tanh', kernel_initializer=initializer)
    x = last(x)

    return tf.keras.Model(inputs=inputs, outputs=x)


def Discriminator():
    initializer = tf.random_normal_initializer(0., 0.02)

    inp = Input(shape=[None, None, 3], name='input_image')
    tar = Input(shape=[None, None, 3], name='target_image')

    x = tf.keras.layers.concatenate([inp, tar]) # (bs, 256, 256, channels*2)

    down1 = downsample(32, 4)(x) # (bs, 128, 128, 64)
    down2 = downsample(64, 4)(down1) # (bs, 64, 64, 128)
    down3 = downsample(128, 4)(down2) # (bs, 32, 32, 256)
    
    zero_pad1 = ZeroPadding2D()(down3) # (bs, 34, 34, 256)
    conv = Conv2D(256, 4, strides=1,
                  kernel_initializer=initializer,
                  use_bias=False)(zero_pad1) # (bs, 31, 31, 512)

    batchnorm1 = BatchNormalization()(conv)

    leaky_relu = LeakyReLU()(batchnorm1)

    zero_pad2 = ZeroPadding2D()(leaky_relu) # (bs, 33, 33, 512)

    last = Conv2D(1, 4, strides=1,
                   kernel_initializer=initializer)(zero_pad2) # (bs, 30, 30, 1)

    return tf.keras.Model(inputs=[inp, tar], outputs=last)