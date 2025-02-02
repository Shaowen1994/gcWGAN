import os, sys

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

SAMPLE_PATH = sys.argv[1]
if not SAMPLE_PATH.endswith('/'):
    SAMPLE_PATH += '/'

if 'gcWGAN' in SAMPLE_PATH:
    MODEL = 'gcWGAN'
    model_index = SAMPLE_PATH.strip('/').split('/')[-1].strip('model_')
elif 'cWGAN' in SAMPLE_PATH:
    MODEL = 'cWGAN'
    model_index = SAMPLE_PATH.strip('/').split('/')[-1].strip('model_')
elif 'cVAE' in SAMPLE_PATH:
    MODEL = 'cVAE'
    model_index = 'No model index.'
else:
    print 'Error! Path of the samples is wrong!'
    quit()

Result_PATH = '../../Results/Accuracy/Yield_Ratio_Result/' + MODEL + '/' + '/'.join(SAMPLE_PATH.split('/')[2:])

print MODEL
print model_index
print Result_PATH

PATH = ''
for folder in Result_PATH.strip('/').split('/'):
    PATH += folder + '/'
    if not os.path.exists(PATH):
        os.mkdir('mkdir ' + PATH)

if PATH != Result_PATH:
    print 'Path Error!'
    quit()
 
TARGET = sys.argv[2]
TARGET_NAME = '_'.join(TARGET.split('.'))
SET_KIND = sys.argv[3]

GEN_SIZE = 100000
SUC_SIZE = 10
BATCH_SIZE = 1000

SEQ_LEN = 160
MAX_N_EXAMPLES = 50000
DATA_DIR = '../../Data/Datasets/Final_Data/'

if SET_KIND == 'train':
    fold_list = DataLoading.file_list(DATA_DIR + 'unique_fold_train')
elif SET_KIND == 'vali':
    fold_list = DataLoading.file_list(DATA_DIR + 'fold_val')
elif SET_KIND == 'test':
    fold_list = DataLoading.file_list(DATA_DIR + 'fold_test')
else:
    print 'Error! No set named %s'%SET_KIND
    quit()

if len(DATA_DIR) == 0:
    raise Exception('Please specify path to data directory in gan_language.py!')

seqs, folds, folds_dict, charmap, inv_charmap = data_helpers.load_dataset_protein( #MK change
    max_length=SEQ_LEN,
    max_n_examples=MAX_N_EXAMPLES,
    data_dir=DATA_DIR
)

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

model_file= "DeepSF_model_weight_more_folds/model-train-DLS2F.json"
model_weight="DeepSF_model_weight_more_folds/model-train-weight-DLS2F.h5"
deepsf_fold="DeepSF_model_weight_more_folds/fold_label_relation2.txt"
kmaxnode=30

json_file_model = open(model_file, 'r')
loaded_model_json = json_file_model.read()
json_file_model.close()
DLS2F_CNN = model_from_json(loaded_model_json, custom_objects={'K_max_pooling1d': K_max_pooling1d})
DLS2F_CNN.load_weights(model_weight)
DLS2F_CNN.compile(loss="categorical_crossentropy", metrics=['accuracy'], optimizer="nadam")

fold_index = DataLoading.Accuracy_index(path = 'DeepSF_model_weight_more_folds/fold_label_relation2.txt')

def file_list(path):
    fil = open(path,'r')
    lines = fil.readlines()
    lis = []
    for line in lines:
        if line != '\n':# and not ('X' in line):
            lis.append(line.strip('\n').lower())
    fil.close()
    return lis

with tf.Session() as session:

    session.run(tf.initialize_all_variables())

    file_name = Result_PATH + MODEL + '_Overfitting_' + SET_KIND + '_' + TARGET_NAME

    if (not os.path.exists(file_name)) or (len(DataLoading.columns_to_lists(file_name)) < 4):
        fil_overfit = open(file_name,'w')
        fil_overfit.close()
        yield_ratio_list = []
    else:
        yield_ratio_list = DataLoading.columns_to_lists(file_name)[-1]
    
    for FOLD in fold_list:
        
        if (MODEL == 'cVAE') and (os.path.exists(SAMPLE_PATH + FOLD)):
            print FOLD
            S_list = file_list(SAMPLE_PATH + FOLD)
        elif os.path.exists(SAMPLE_PATH + 'sample_' + model_index + '_' + FOLD):
            print FOLD
            S_list = file_list(SAMPLE_PATH + 'sample_' + model_index + '_' + FOLD)
        else:
            print FOLD, 'not exist'
            continue
                        
        gen_num = 0
        suc_num = 0
 
        while(len(S_list) > 0):
            if len(S_list) > BATCH_SIZE:
                S_select = S_list[0:BATCH_SIZE]
                S_list = S_list[BATCH_SIZE:]
            else:
                S_select = S_list
                S_list = []
            S_test = []
            for seq in S_select:
                if not ('x' in seq):
                    S_test.append(seq)
            TEST_SIZE = len(S_test)
            gen_num += TEST_SIZE
        
            test_se = [s+'!'*(SEQ_LEN - len(s)) for s in S_test]
            test_se = [tuple(s) for s in test_se]
            test_seq = create_aa_feature(np.asarray([[charmap[c] for c in l] for l in test_se]).reshape((TEST_SIZE,SEQ_LEN)),TEST_SIZE)
            prediction= DLS2F_CNN.predict([test_seq])
            top10_prediction=prediction.argsort()[:,::-1][:,:10]
            for p in top10_prediction:
                f_pre = [fold_index[i] for i in p]
                if TARGET in f_pre:
                    suc_num += 1
            if gen_num >= BATCH_SIZE and (suc_num >= SUC_SIZE or gen_num >= GEN_SIZE):
                 break

        ratio = float(suc_num)/float(gen_num)
        yield_ratio_list.append(ratio)

        fil_overfit = open(file_name,'a')
        fil_overfit.write(FOLD + '\t' + str(suc_num) + '\t' + str(gen_num) + '\t' + str(ratio) + '\n')
        fil_overfit.close()

    yield_ratio_list = [float(i) for i in yield_ratio_list]
    fil_overfit = open(file_name,'a')
    fil_overfit.write('\n')
    fil_overfit.write('Average Yield Ratio: %f\n'%np.mean(yield_ratio_list))
    fil_overfit.close()
    
    #print FOLD    
    #print suc_num
    #print gen_num
    #print ratio

