######################################## Load Packages ############################################

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

################################### Set Paths and Parameters #########################################

if not os.path.exists('Pipeline_Sample'):
    os.system('mkdir Pipeline_Sample')
if not os.path.exists('Pipeline_Sample/Generating_Ratio_Samples'):
    os.system('mkdir Pipeline_Sample/Generating_Ratio_Samples')

All_NUM = int(sys.argv[3])
FOLD = sys.argv[2]
KIND = sys.argv[1]
MIN_LEN = int(sys.argv[4])
MAX_LEN = int(sys.argv[5])
#MIN_LEN = 60
#MAX_LEN = 160

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
TOP_NUM = 10

fold_len = 20 #MK add

######################################## Load Data ############################################

lib.print_model_settings(locals().copy())

seqs, folds, folds_dict, charmap, inv_charmap = data_helpers.load_dataset_protein( #MK change
    max_length=SEQ_LEN,
    max_n_examples=MAX_N_EXAMPLES,
    data_dir=DATA_DIR
)

######################################## Construct DeepSF ############################################

class K_max_pooling1d(Layer):
    def __init__(self,  ktop, **kwargs):
        self.ktop = ktop
        super(K_max_pooling1d, self).__init__(**kwargs)

    def get_output_shape_for(self, input_shape):
        return (input_shape[0],self.ktop,input_shape[2])

    def call(self,x,mask=None):
        output = x[T.arange(x.shape[0]).dimshuffle(0, "x", "x"),
              T.sort(T.argsort(x, axis=1)[:, -self.ktop:, :], axis=1),
              T.arange(x.shape[2]).dimshuffle("x", "x", 0)]
        return output

    def get_config(self):
        config = {'ktop': self.ktop}
        base_config = super(K_max_pooling1d, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))

def create_aa_feature(inp,num):

    num_class = 20
    output = np.zeros((num,SEQ_LEN,num_class))
    for i in range(num):
        output[i,:,:] = np.eye(num_class)[inp[i,]-1]

    return output

model_file="./DeepSF_model_weight_more_folds/model-train-DLS2F.json"
model_weight="./DeepSF_model_weight_more_folds/model-train-weight-DLS2F.h5"
deepsf_fold="./DeepSF_model_weight_more_folds/fold_label_relation2.txt"
kmaxnode=30

json_file_model = open(model_file, 'r')
loaded_model_json = json_file_model.read()
json_file_model.close()
DLS2F_CNN = model_from_json(loaded_model_json, custom_objects={'K_max_pooling1d': K_max_pooling1d})
DLS2F_CNN.load_weights(model_weight)
DLS2F_CNN.compile(loss="categorical_crossentropy", metrics=['accuracy'], optimizer="nadam")

fold_index = DataLoading.Accuracy_index(path = 'DeepSF_model_weight_more_folds/fold_label_relation2.txt')

print 'Data loading successfully!'

################################ Build the Architecture of the Model ################################

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

######################################## Run the Generator ############################################

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

    test_se = []
    num = 0

    s_file = open('Pipeline_Sample/Generating_Ratio_Samples/' + KIND + '_Sample_Fasta_gen_' + FOLD + '_' + str(All_NUM),'w')
    stat_file = open('Pipeline_Sample/Generating_Ratio_Samples/' + KIND + '_Stat_gen_' + FOLD + '_' + str(All_NUM),'w')
    s_file.close()
    stat_file.close()
    num_all = 0
    num_gen = 0
    
    g_start = time.time()     

    while(num_gen < All_NUM):
        
        f_batch = [folds_dict[FOLD]] * BATCH_SIZE
        samples = generate_samples(f_batch)
        test_se = []
        for sa in samples:
            sam = ''.join(sa)
            samp = sam.strip('!')
            if ((len(samp) >= MIN_LEN) and (len(samp) <= MAX_LEN)) and ((not ('!' in samp)) and (sam[0] != '!')):
                test_se.append(sa)     
  
        V_SIZE = len(test_se)   
        if V_SIZE > 0: 

            test_seq = create_aa_feature(np.asarray([[charmap[c] for c in l] for l in test_se]).reshape((V_SIZE,SEQ_LEN)),V_SIZE)
            prediction= DLS2F_CNN.predict([test_seq])
            top_prediction=prediction.argsort()[:,::-1][:,:TOP_NUM]
        
            for p in range(V_SIZE):
                f_pre = [fold_index[i] for i in top_prediction[p]]
                num_all += 1
                if FOLD in f_pre:
                    temp_time = time.time()
                    record_time = temp_time - g_start
                    num += 1
                    num_gen = num_all
                    s_file = open('Pipeline_Sample/Generating_Ratio_Samples/' + KIND + '_Sample_Fasta_gen_' + FOLD + '_' + str(All_NUM),'a')
                    stat_file = open('Pipeline_Sample/Generating_Ratio_Samples/' + KIND + '_Stat_gen_' + FOLD + '_' + str(All_NUM),'a')
                    seq_g = ''.join(test_se[p])                    
                    s_file.write('>' + str(num) + '\n')
                    s_file.write(seq_g + '\n')
                    stat_file.write(str(num) + '\t' + str(num_all) + '\t' + str(record_time) + '\n')
                    s_file.close()
                    stat_file.close()
                if num_gen >= All_NUM:
                    break

        if num_gen >= All_NUM:
            break
        

