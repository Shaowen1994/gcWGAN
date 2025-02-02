import matplotlib.pyplot as plt
plt.switch_backend('agg')
import DataLoading
import sys
import os

FOLD = sys.argv[2]
KIND = sys.argv[1]

if len(sys.argv) >= 4:
    target_flag = True
    target = '_' + sys.argv[3]
else:
    target_flag = False
    target = ''

if 'nov' in FOLD:
    fold_name = 'nov'
    i_xy_range = [0,1,0,25]
    n_xy_range = [0,0.3,0,30]
    i_bins = [0.01*i for i in range(0,101)]
    n_bins = [0.01*i for i in range(0,31)]
elif '.' in FOLD:
    fold_name = FOLD.split('.')[0] + '_' + FOLD.split('.')[1]
    i_xy_range = [0,1,0,25]
    n_xy_range = [0,0.7,0,50]
    i_bins = [0.01*i for i in range(0,101)]
    n_bins = [0.01*i for i in range(0,71)]
else:
    print 'Error! Wrong fold name!'

if not os.path.exists('../../Results'):
    os.system('mkdir ../../Results')

path = '../../Results/Diversity_and_Novelty/'

if not os.path.exists(path):
    os.system('mkdir ' + path)
if not os.path.exists(path + 'Div_Nov_Image/' ):
    os.system('mkdir ' + path + 'Div_Nov_Image/' )

def case_columns_to_lists(file_name):
    fil = open(file_name,'r')
    lines = fil.readlines()
    fil.close()
    n = len(lines[0].strip('\n').split('\t'))
    result = []
    for i in range(n):
        result.append([])
    for line in lines:
        line = line.strip('\n').split('\t')
        if len(line) == n:
            for i in range(n):
                result[i].append(line[i])
    return result

def merge_hist_plot(data_1,data_2,data_3,fold,xlabel,ylabel,path,xy_range,kind,figsize = None,bins = None):
    if figsize != None:
        plt.figure(figsize = figsize)
    else:
        plt.figure()
    plt.axis(xy_range)
    step = int((xy_range[3] - xy_range[2])/5)
    y_ticks = range(xy_range[2],xy_range[3] + 1,step)
    if bins != None:
        plt.hist(data_1,bins = bins,color = 'blue',density = True,alpha = 0.5,label = kind + ' (oracle-filtered)')
        plt.hist(data_2,bins = bins,color = 'grey',density = True,alpha = 0.5,label = kind + ' (not filtered)')
        plt.hist(data_3,bins = bins,color = 'darkorange',density = True,alpha = 0.5,label = 'cVAE (not filtered)')
    else:
        plt.hist(data_1,color = 'blue',density = True,alpha = 0.5,label = kind + ' (oracle-filtered)')
        plt.hist(data_2,color = 'grey',density = True,alpha = 0.5,label = kind + ' (not filtered)')
        plt.hist(data_3,color = 'darkorange',density = True,alpha = 0.5,label = 'cVAE (oracle-filtered)')
    plt.legend(fontsize = 15,prop = {'weight':'bold'})
    plt.xticks(fontsize = 15,fontweight = 'bold')
    plt.yticks(y_ticks,fontsize = 15,fontweight = 'bold')
    plt.xlabel(xlabel,fontsize = 20, weight = 'bold')
    plt.ylabel(ylabel,fontsize = 20, weight = 'bold')
    plt.tight_layout()
    plt.savefig(path)
    plt.savefig(path + '.eps')

if target_flag:
    Iden_s = [float(i) for i in DataLoading.columns_to_lists(path + 'Identity_' + KIND + '_Fasta_100_success_' + fold_name + target)[0][0:-2]]
else:
    Iden_s = [float(i) for i in DataLoading.columns_to_lists(path + KIND + '_Identity_Successful_' + fold_name)[0][0:-2]]
Iden_r = [float(i) for i in DataLoading.columns_to_lists(path + KIND + '_Identity_Random_' + fold_name)[0][0:-2]]
Iden_j = [float(i) for i in DataLoading.columns_to_lists(path + 'cVAE_Identity_' + fold_name)[0][0:-2]]
Iden_j_noX = [float(i) for i in DataLoading.columns_to_lists(path + 'cVAE_Identity_noX_' + fold_name)[0][0:-2]]

if fold_name == 'nov':
    if target_flag:
        nov_s = [float(i) for i in DataLoading.columns_to_lists(path + 'Novelty_' + KIND + '_Fasta_100_success_' + fold_name + target)[0][0:-2]]
    else:
        nov_s = [float(i) for i in DataLoading.columns_to_lists(path + KIND + '_Novelty_Successful_' + fold_name + target)[0][0:-2]]
    nov_r = [float(i) for i in DataLoading.columns_to_lists(path + KIND + '_Novelty_Random_' + fold_name)[0][0:-2]]
    nov_j = [float(i) for i in DataLoading.columns_to_lists(path + 'cVAE_Novelty_' + fold_name)[0][0:-2]]
    nov_j_noX = [float(i) for i in DataLoading.columns_to_lists(path + 'cVAE_Novelty_noX_' + fold_name)[0][0:-2]]
else:
    if target_flag:
        nov_s = [float(i) for i in case_columns_to_lists(path + 'Novelty_' + KIND + '_Fasta_100_success_' + fold_name + target)[1]]
    else:
        nov_s = [float(i) for i in case_columns_to_lists(path + KIND + '_Novelty_Successful_' + fold_name + target)[1]]
    nov_r = [float(i) for i in case_columns_to_lists(path + KIND + '_Novelty_Random_' + fold_name)[1]]
    nov_j = [float(i) for i in case_columns_to_lists(path + 'cVAE_Novelty_' + fold_name)[1]]
    nov_j_noX = [float(i) for i in case_columns_to_lists(path + 'cVAE_Novelty_noX_' + fold_name)[1]]
    #print len(nov_s)

merge_hist_plot(Iden_s,Iden_r,Iden_j,FOLD,'Sequence Identity','Distribution Density',path + 'Div_Nov_Image/' + KIND + '_Identity_Distribution_' + fold_name + target,xy_range = i_xy_range,kind = KIND,bins = i_bins)    # plot the diversity distribution

merge_hist_plot(Iden_s,Iden_r,Iden_j_noX,FOLD,'Sequence Identity','Distribution Density',path + 'Div_Nov_Image/' + KIND + '_Identity_Distribution_noX_' + fold_name + target,xy_range = i_xy_range,kind = KIND,bins = i_bins)    # plot the diversity distribution of sequences without X

merge_hist_plot(nov_s,nov_r,nov_j,FOLD,'Maximum Sequence Identity','Distribution Density',path + 'Div_Nov_Image/' + KIND + '_Novelty_Distribution_' + fold_name + target,xy_range = n_xy_range,kind = KIND,bins = n_bins)    # plot the novelty distribution

merge_hist_plot(nov_s,nov_r,nov_j_noX,FOLD,'Maximum Sequence Identity','Distribution Density',path + 'Div_Nov_Image/' + KIND + '_Novelty_Distribution_noX__' + fold_name + target,xy_range = n_xy_range,kind = KIND,bins = n_bins)    # plot the novelty distribution of sequences without X
