# DeNovoFoldDesign

**Motivation:** Facing data quickly accumulating on protein sequence and structure, this study is addressingthe following question: to what extent could current data alone reveal deep insights into the sequence-structure relationship, such that new sequences can be designed accordingly for novel structure folds?

**Results:** We have developed novel deep generative models,  constructed low-dimensional andgeneralizable representation of fold space, exploited sequence data with and without paired structures,and developed ultra-fast fold predictor as an oracle providing feedback. The resulting semi-supervisedgcWGAN is assessed with the oracle over 100 novel folds not in the training set and found to generatemore yields and cover 3.6 times more target folds compared to a competing data-driven method (cVAE).Assessed with structure predictor over representative novel folds (including one not even part of basisfolds), gcWGAN designs are found to have comparable or better fold accuracy yet much more sequencediversity and novelty than cVAE. gcWGAN explores uncharted sequence space to design proteins bylearning from current sequence-structure data. The ultra fast data-driven model can be a powerful additionto principle-driven design methods through generating seed designs or tailoring sequence space.

![Training-Process](/gcWGAN/Training-Process.png)

***

## Pre-requisite 
### * [Anaconda 2](https://www.anaconda.com/distribution/).
### * Environments:
To build the enviroments for this project, go to the ***Environments*** folder, then run
```
conda env create -f tensorflow_training.yml
```
```
conda env create -f DeepDesign_acc.yml
```
### * Check Points:
* **To train the model (For *cWGAN* and *gcWGAN*):** Directly go to the ***cWGAN*** or ***gcWGAN*** model and follow the instructions. 
* **Apply our model for evaluation or sequence generation (For *Model_Test* and *Model_Evaluation*):** Go to the ***Checkpoints*** folder and download the related check points into the correct path according to the instruction. 

Our check points were gotten after 100 epoch of training. If you have already downloaded our check points but want to retrain the model with the same hyper-parameters, the downlowded ones may be replaced if the training process reach the 100th epoch.

***

## Table of contents:
* **Environments:** Contain the *\*.yml* with which you can build required environments.
* **Data:** Contain the original data, processed data and ralated processing scripts.
* **Oracle:** Contain the scripts for the sequence features and applying the oracles.
* **cWGAN:** Contain the scripts for cWGAN model training and validation (hpper-parameter tuning).
* **gcWGAN:** Contain the scripts for gcWGAN model training.
* **Model_Evaluation:** Contain the scripts for model performance evaluation.
* **Model_Apply:** Contain the scripts to apply the trained model.
* **Generated_Results:** Contain the sequence samples generated by our model for the evaluation part (except the yiled ratio part which can be too large to upload) and the selected structure prediction from Rosetta based on gcWGAN.

***

## Model Application

In this part you can apply our models to generate protein sequences according to a given protein fold (\*.pbd file). With the scripts you can represent the givern fold with a 20 dimensional vector and send it to the generator for sequence generation. Go to the ***Model_Apply*** folder for more dtails.

Some examples of the generated sequences (10 sequences based on gcWGAN that pass the oracle):
```
>1
MIAPDQTIEKYVKFMAPVFTTTEYLKIVEMEEKGITTIAHGPVIHTARNPYAEVRLVSVTHELLIELQASGFLNISKTICLFETGIDENKEVLIDKDDYKEEPLLVDLFLEMEGPMDGQEIMTKLVRVPVMGQSLKPYAVKKAGVIKSAKHVG
>2
PCYALTVEAVENLLQAPAVRTLQKDEGLTPRLQPGIAAYASFIAGGAGCGLTRGSSDNMAKALIQEIEKTLRAVELTPATVQILVNNNEVKLPEKEKPNAIAKGILTVNLISKMDEFTKLVLVGENYTAILIDHIAKHKVGPV
>3
MCYDIAQSYLNFMMINGTVLIQTATRTLCPAVHSACRYDYIKVTAAKGNIVTDIGLMYFVRNMELVGPLMTATVAISKSIYTVQKATKETVNEMRTLQVAGTRTMFCRIYHVDMTKMMMQTGISIVGEKKPTRHDAEITYDQLAGHLVPLAHLKKL
>4
CTKAQRGVHKIYEVEKNYMPNRTLGDPNSLRIDSIGIRPVNERKDNTRYVAKKAKAILAKKDIMYCLPINIDVVKVTSTLDNYLDGDPYSKRPRFDDNLIKAVIPTDVALKPSPRYDVQAGRETPPAYTAVVQRFFSVKLNRL
>5
CPNVYQKLLYSMTEGPMDIGPVEVGQLLAVIPSAIGKVVSEITTSVHPAAPFEEAARVTAMAQRAALQYSTQTYLVGKESIALMYGKYRALHQDLARMVLADGQTADVQEVVPIIADIQRMHPAGQVAPRLIESGVVTASVLMTAA
>6
LLHGKLEVFHKCVAKADEASGLTFFHCGCSAYVTSEAAKGRYRPRACSTVHYFEKGATIPGLQYTNMYENAMVCTSKIRIYLEAMNMAPNVPLHRAAKYDNVSAALTANNNKVALIAEYYVTALLEGEVTQHLEEYKKNPPPELYEEIC
>7
MNKINIKYCPFNFNKVFRKEAFITQMAGENMAVLKELSEQIDHCSCFHKNTARQLLHRAEDGPVTEVETLLELRAAMICCFRRRAPRLVLGSSMSTTVITKCIAICTGQPYPGNGPPTTLGQPACSGVEVINNQAAIVIQTVEQRFILMTPGK
>8
CTVTAVQEFTENYGGLPLYVTRNQTLAPADKRLTPRYAGNFPEGAEVPAPNLAQTSPGVTYGKNIGRYLKNGLPDVAICTSPNLNLSGAYPDIVKYNYQQPEVFIRQYHPGNEMDVVKALEQFSSELLPGKTMSIVVNSYNNLADK
>9
CETTIDIEASVISQVIAVIVALTPIHKYAHASSKALASGASDVNVGPKLVAYIGKIAYSDPPIDLIPPVKVVVALLAPELAGVTAADYISYNEGKPATGESAGNAAFADGTTTIAPQRTIYEGEHKARINIITIADGAPLGSHEIP
>10
PEPDLVLTCTNLSFSAMVSCLRETSAFAGVEYAYNGIHPAGSCCLAAMKKGFFPHTEGMNALVIEPTPPVPCAPTKDLVQNKIQKAKLLPPAATTADEYSETLGQEDFLKLLTNPKITEKKKSPTTLILVTVNSELMISPVYFTGPLMKELLYHCNGEN
```
***

## Training Process:

In the ***cWGAN*** folder and ***gcWGAN*** folder there are scripts for traning our two models. For cWGAN there are also scripts for validation (hyper-parameter tuning) and for gcWGAN there are also scripts for the Warmstart. Go to the ***cWGAN*** folder or ***gcWGAN*** folder for more details.

Some examples of the generated sequences during the training process:
```
fold a.39: vvaitfdnvhfpcshapltkaltvkklqvsannvsllvfddakmtkkidiekaikgfymmknnpqaqleiierftpttrgkpvikpiasftltspeilgkegykk!!!!!!!!!!!!!!!!!!!itkmlidavks!!!!!!!!!!!!!!!!!!!!!!!!!
fold d.78: leemskvgntpaltyreardvavigifnngkqmksrddvtdeaddyqceidpisnllelgallpplhvaetkmllyykneakmhlfegag!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
fold d.240: tlaedippklpleveqcneiivdaqnkryvavgealllitcpmlqnnsmsttcgyrfeakskdgvicespeeglqndtthyachkraaavqiptekkttvyrlhacttklegcaeadnrvladvgldgivqravcdivttfsaevnp!!!!!!!!!!!!!
fold d.227: sckpglplvcagkkstyleklltgylvyslladyispkaleeavisekkpniampafatmpslvaddvtaliakkglqnaakcpndhmeiyeaeedpaiigqgynkhqgvgcnivvmagaipdeqkvenlrsliei!!!!!!!!!!!!!!!!!!!!!!!!
fold d.301: mtakstvqlpaeykgqniaeilnnvafnlaaivysattivayramacfpcgeknykeilgkvltlfidkhpiqnnr!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
fold d.223: mqtyeeavtlgltneqqtgknvtpiniaeekllvtnglvcqapalpvneevliklsentdnikpllciigkkseaispcsfraeeafdrsadymankatimcrkgnyaiilhsdgeellaihqtsgviirlghvpgkknrymppgaliplcngp!!!!!!
fold a.216: eelakrmiqrapdveligknkiatelkrlcllirgqtaanimnvillcataisvipkkskpasqyeetvnpadlakeiilqekkeaftriltteylvtsllkmypvhkvpkp!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
fold b.60: qpifvtykrlnrlallkshplhkdpkyltavlvmeldpsslpvavqpqrvvtiqsccpiiepsappeecdiqapnklkallendkptsqn!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
fold c.9: ayfereelilltpthggnepktldiptnlpakilgtplrkvklasqkellgeahpnnavstlideayylgdeqrevvvlteqekkagpidithyvngtegsckkpnisdsptphakafkqilkemqariqhhkelittalerlkn!!!!!!!!!!!!!!!
fold a.180: mpeecvctglepgevrrqngvipllnqgfhavltpagktylccttatknqvivhmfcqtaaeniyaeitvsylrtaatstylefmkhccqnvssihygiymslmdllkeyvveklv!e!!!!!!!!!!!!!!!!!!!iaeqipearkyaaalvg!!!!!!
```
***

## Evaluate Model Performance:

This part contains the scripts we applied to evaluate the performance of our model. We also generate several sequences with the previouse state-of-art model [cVAE](https://github.com/psipred/protein-vae) and applied our evaluation method for comparison. Model evalustion consists of three part, model accuracy, sequence generating rate and sequence diversity and novelty, and for model accuracy we both applied yield ratio calculation for all the training, validation and test folds, and [Rosetta](https://www.rosettacommons.org/docs/latest/application_documentation/structure_prediction/abinitio-relax) analysis for 6 selected test folds and a novel fold. Go to the ***Model_Evaluation*** folder for more details.

***

## Citation:
'''
@article{karimi2019novo,
  title={De Novo Protein Design for Novel Folds using Guided Conditional Wasserstein Generative Adversarial Networks (gcWGAN)},
  author={Karimi, Mostafa and Zhu, Shaowen and Cao, Yue and Shen, Yang},
  journal={bioRxiv},
  pages={769919},
  year={2019},
  publisher={Cold Spring Harbor Laboratory}
}
'''

***

## Contacts:
**Yang Shen:** yshen@tamu.edu 

**Mostafa Karimi:** mostafa_karimi@tamu.edu

**Shaowen Zhu:** shaowen1994@tamu.edu

**Yue Cao:** cyppsp@tamu.edu
