################################ Import packages #################################

import os, sys
sys.path.append(os.getcwd())

import time

import numpy as np
import tensorflow as tf
import data_helpers #SZ change
import tflib as lib
import tflib.ops.linear
import tflib.ops.conv1d
import tflib.plot
import DataLoading #SZ add
import matplotlib.pyplot as plt #SZ add
import os

from keras.models import model_from_json
from keras.engine.topology import Layer
import theano.tensor as T
from keras import backend as K
from keras.constraints import maxnorm

from keras.models import Model
from keras.layers import Activation, Dense, Dropout, Flatten, Input, Merge, Convolution1D
from keras.layers.normalization import BatchNormalization

############################ Set paths and parameters ################################

GEN_NUM = int(sys.argv[1])
FOLD = sys.argv[2]
KIND = sys.argv[3]
MIN_LEN = int(sys.argv[4])
MAX_LEN = int(sys.argv[5])

fold_name = FOLD.split('.')[0] + '_' + FOLD.split('.')[1]

if KIND == 'cWGAN':
    check_point = '../../Checkpoints/cWGAN/model_0.0001_5_64/model_100_5233.ckpt'
elif KIND == 'gcWGAN':
    check_point = '../../Checkpoints/gcWGAN/Checkpoints_0.0001_5_64_0.02_semi_diff/model_100_5233.ckpt'
else:
    print 'Error! Wrong Kind.'
    quit()

noise_len = 64

DATA_DIR = '../../Data/Datasets/Final_Data/'
if len(DATA_DIR) == 0:
    raise Exception('Please specify path to data directory in gan_language.py!')

BATCH_SIZE = 200 # Batch size
SEQ_LEN = 160 # Sequence length in characters
DIM = 512 # Model dimensionality. This is fairly slow and overfits, even on
          # Billion Word. Consider decreasing for smaller datasets.
LAMBDA = 10 # Gradient penalty lambda hyperparameter.
MAX_N_EXAMPLES = 50000 # Max number of data examples to load. If data loading
                          # is too slow or takes too much RAM, you can decrease
                          # this (at the expense of having less training data).

if not os.path.exists('Pipeline_Sample'):
    os.system('mkdir Pipeline_Sample')

fold_len = 20 #MK add

lib.print_model_settings(locals().copy())

################################ Load data #################################

seqs, folds, folds_dict, charmap, inv_charmap = data_helpers.load_dataset_protein( #MK change
    max_length=SEQ_LEN,
    max_n_examples=MAX_N_EXAMPLES,
    data_dir=DATA_DIR
)

print 'Data loading successfully!'

############################ Structure of the Model #################################

def softmax(logits):
    return tf.reshape(
        tf.nn.softmax(
            tf.reshape(logits, [-1, len(charmap)])
        ),
        tf.shape(logits)
    )

def make_noise(shape):
    return tf.random_normal(shape)

def ResBlock(name, inputs):
    output = inputs
    output = tf.nn.relu(output)
    output = lib.ops.conv1d.Conv1D(name+'.1', DIM, DIM, 5, output)
    output = tf.nn.relu(output)
    output = lib.ops.conv1d.Conv1D(name+'.2', DIM, DIM, 5, output)
    return inputs + (0.3*output)

def ResBlock_v2(name, inputs,size): #MK add
    output = inputs
    output = tf.nn.relu(output)
    output = lib.ops.conv1d.Conv1D(name+'.1', size, size, 5, output)
    output = tf.nn.relu(output)
    output = lib.ops.conv1d.Conv1D(name+'.2', size, size, 5, output)
    return inputs + (0.3*output)

def Generator(n_samples, labels, prev_outputs=None): #MK change
    output = make_noise(shape=[n_samples, noise_len])
    output = tf.concat([output,labels],axis=1) #MK add
    output = lib.ops.linear.Linear('Generator.Input', noise_len+fold_len, SEQ_LEN*DIM, output) #MK change
    output = tf.reshape(output, [-1, DIM, SEQ_LEN])
    output = ResBlock('Generator.1', output)
    output = ResBlock('Generator.2', output)
    output = ResBlock('Generator.3', output)
    output = ResBlock('Generator.4', output)
    output = ResBlock('Generator.5', output)
    output = lib.ops.conv1d.Conv1D('Generator.Output', DIM, len(charmap), 1, output)
    output = tf.transpose(output, [0, 2, 1])
    output = softmax(output)
    return output

def Discriminator(inputs,labels): #MK change
    output = tf.transpose(inputs, [0,2,1])
    output = lib.ops.conv1d.Conv1D('Discriminator.Input', len(charmap), DIM, 1, output)
    output = ResBlock('Discriminator.1', output)
    output = ResBlock('Discriminator.2', output)
    output = ResBlock('Discriminator.3', output)
    output = ResBlock('Discriminator.4', output)
    output = ResBlock('Discriminator.5', output)
    output = tf.reshape(output, [-1, SEQ_LEN*DIM])
    size= 100 #MK add
    output = lib.ops.linear.Linear('Discriminator.reduction', SEQ_LEN*DIM,size, output) #MK change
    output = tf.concat([output,labels],axis=1) #MK add
    output = tf.contrib.layers.fully_connected(output,300,scope='Discriminator.fully',reuse=tf.AUTO_REUSE) #MK add
    output = lib.ops.linear.Linear('Discriminator.output',300 , 1, output) #MK add
    return output

real_inputs_discrete = tf.placeholder(tf.int32, shape=[BATCH_SIZE, SEQ_LEN])
real_inputs = tf.one_hot(real_inputs_discrete, len(charmap))
real_inputs_label = tf.placeholder(tf.float32, shape=[BATCH_SIZE, fold_len]) #MK add
fake_inputs = Generator(BATCH_SIZE,real_inputs_label) #MK change
fake_inputs_discrete = tf.argmax(fake_inputs, fake_inputs.get_shape().ndims-1)

disc_real = Discriminator(real_inputs,real_inputs_label) #MK change 
disc_fake = Discriminator(fake_inputs,real_inputs_label) #MK change

disc_cost = tf.reduce_mean(disc_fake) - tf.reduce_mean(disc_real)
gen_cost = -tf.reduce_mean(disc_fake)

# WGAN lipschitz-penalty
alpha = tf.random_uniform(
    shape=[BATCH_SIZE,1,1],
    minval=0.,
    maxval=1.
)
differences = fake_inputs - real_inputs
interpolates = real_inputs + (alpha*differences)
gradients = tf.gradients(Discriminator(interpolates,real_inputs_label), [interpolates])[0] #MK change
slopes = tf.sqrt(tf.reduce_sum(tf.square(gradients), reduction_indices=[1,2]))
gradient_penalty = tf.reduce_mean((slopes-1.)**2)

################################ Generate Sequences #################################

saver  = tf.train.Saver()

with tf.Session() as session:

    session.run(tf.initialize_all_variables())

    def generate_samples(label): #MK change
        samples = session.run(fake_inputs,feed_dict={real_inputs_label:label}) #MK change
        samples = np.argmax(samples, axis=2)
        decoded_samples = []
        for i in xrange(len(samples)):
            decoded = []
            for j in xrange(len(samples[i])):
                decoded.append(inv_charmap[samples[i][j]])
            decoded_samples.append(tuple(decoded))
        return decoded_samples

    start_time = time.time()

    saver.restore(session,check_point)
    print 'Restore Successfully!'

    samples_f = []
    test_se = []
    num = 0
    while(num < GEN_NUM):
        f_batch = [folds_dict[FOLD]] * BATCH_SIZE
        samples = generate_samples(f_batch)
        test_se = []
        for sa in samples:
            sam = ''.join(sa)
            samp = sam.strip('!')
            if ((len(samp) >= MIN_LEN) and (len(samp) <= MAX_LEN)) and ((not ('!' in samp)) and (sam[0] != '!')):
                samples_f.append(sa)     
                num += 1
                if num >= GEN_NUM:
                    break
  
    samples_f = [''.join(sa) for sa in samples_f]
    
    s_file = open('Pipeline_Sample/' + KIND + '_Fasta_' + str(GEN_NUM) + '_random_' + fold_name,'w')
    s_index = 0
    for i in range(GEN_NUM):
        s = samples_f[i]
        s = s.strip('!')
        s = s.upper()
        s_index += 1
        s_file.write('>' + str(s_index) + '\n')
        s_file.write(s + '\n')

    s_file.close()
