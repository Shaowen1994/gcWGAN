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
import Assessment #SZ add
from Bio.SubsMat import MatrixInfo as matlist #SZ add
import matplotlib.pyplot as plt #SZ add
matrix = matlist.blosum62 #SZ add
import os

test_index = sys.argv[1]

sample_path = 'cWGAN_Validation_Samples/NonsenseRatio_Sample_' + test_index
check_path = '../../Checkpoints/cWGAN/model_' + test_index
#os.system('mkdir ' + sample_path)
if not os.path.exists('cWGAN_Validation_Samples'):
    os.system('mkdir cWGAN_Validation_Samples')
if not os.path.exists(sample_path):
    os.system('mkdir ' + sample_path)
if not os.path.exists('cWGAN_Validation_Results'):
    os.system('mkdir cWGAN_Validation_Results')

noise_len = int(test_index.split('_')[-1])
CRITIC_ITERS = int(test_index.split('_')[1])

DATA_DIR = '../../Data/Datasets/Final_Data/'
if len(DATA_DIR) == 0:
    raise Exception('Please specify path to data directory in gan_language.py!')

BATCH_SIZE = 100 # Batch size
SEQ_LEN = 160 # Sequence length in characters
DIM = 512 # Model dimensionality. This is fairly slow and overfits, even on
          # Billion Word. Consider decreasing for smaller datasets.
#CRITIC_ITERS = 10 # How many critic iterations per generator iteration. We
                  # use 10 for the results in the paper, but 5 should work fine
                  # as well.
LAMBDA = 10 # Gradient penalty lambda hyperparameter.
MAX_N_EXAMPLES = 50000 # Max number of data examples to load. If data loading
                          # is too slow or takes too much RAM, you can decrease
                          # this (at the expense of having less training data).

fold_len = 20 #MK add

lib.print_model_settings(locals().copy())

seqs, folds, folds_dict, charmap, inv_charmap = data_helpers.load_dataset_protein( #MK change
    max_length=SEQ_LEN,
    max_n_examples=MAX_N_EXAMPLES,
    data_dir=DATA_DIR
)

inter_dic = Assessment.Interval_dic(DATA_DIR + 'Interval_1.fa') #SZ add
unique_train = Assessment.file_list(DATA_DIR + 'unique_fold_train') #SZ add
unique_new = Assessment.file_list(DATA_DIR + 'unique_fold_new')  #SZ add

print 'Data loading successfully!'

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


check_dic = {}
f_list = os.listdir(check_path+'/')
for f in f_list:
    f = f.split('.')[0].split('_')
    if f[0] == 'model':
        check_dic[f[1]] = f[2]

check_index = sorted([int(i) for i in check_dic.keys()])

print 'Load the index of check points successfully!'

saver  = tf.train.Saver()

pt_file = open('cWGAN_Validation_Results/' + test_index + '_Nonsense_Ratio_train.fa','w')
pn_file = open('cWGAN_Validation_Results/' + test_index + '_Nonsense_Ratio_new.fa','w')
pt_file.close()
pn_file.close()

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
    PR_train = []
    PR_new = []
    for c in check_index:
        print c
        print check_dic[str(c)]
        saver.restore(session,check_path + "/model_"+str(c)+"_" + check_dic[str(c)] + ".ckpt")
        print 'Restore Successfully!'
        PR_t = []
        PR_n = []
        file_t = open(sample_path + '/sample_train_{}.fa'.format(c),'w')
        file_n = open(sample_path + '/sample_new_{}.fa'.format(c),'w')
        for fo in unique_train:
            f_batch = [folds_dict[fo]] * BATCH_SIZE
            samples = generate_samples(f_batch)
            samples_strip = [''.join(sam) for sam in samples]
            k = 0
            for samp in samples_strip:
                file_t.write(fo + ": "+''+ samp + '\n')
                if samp[0] == '!':
                    k += 1
                else:
                    samp = samp.strip("!")
                    if ('!' in samp) or (samp == ''):
                        k += 1
                #samp = samp.strip("!")
                #if ('!' in samp) or (samp == ''):
                #    k += 1
            file_t.write('\n')
            PR_t.append(float(k)/float(BATCH_SIZE))
        pr_train = np.mean(PR_t)
        pt_file = open('cWGAN_Validation_Results/' + test_index + '_Nonsense_Ratio_train.fa','a')
        pt_file.write(str(pr_train)  + '\n')
        pt_file.close()
        PR_train.append(pr_train)
        for fo in unique_new:
            f_batch = [folds_dict[fo]] * BATCH_SIZE
            samples = generate_samples(f_batch)
            samples_strip = [''.join(sam) for sam in samples]
            k = 0
            for samp in samples_strip:
                file_n.write(fo + ": "+''+ samp + '\n')
                if samp[0] == '!':
                    k += 1
                else:
                    samp = samp.strip("!")
                    if ('!' in samp) or (samp == ''):
                        k += 1
                #samp = samp.strip("!")
                #if ('!' in samp) or (samp == ''):
                #    k += 1
            file_n.write('\n')
            PR_n.append(float(k)/float(BATCH_SIZE))
        pr_new = np.mean(PR_n)
        pn_file = open('cWGAN_Validation_Results/' + test_index + '_Nonsense_Ratio_new.fa','a')
        pn_file.write(str(pr_new)  + '\n')
        pn_file.close()
        PR_new.append(pr_new)
        file_t.close()
        file_n.close()
       
