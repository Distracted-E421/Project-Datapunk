NeuroImage 303 (2024) 120917 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Investigation of white matter functional networks in young smokers

Junxuan Wang a,1, Ting Xue b,1,*, Daining Song a, Fang Dong a, Yongxin Cheng a, Juan Wang a,  
Yuxin Ma a, Mingze Zou a, Shuailin Ding a, Zhanlong Tao b, Wuyuan Xin a, Dahua Yu c,**,  
Kai Yuan a,c,d,e,***
a School of Digital and Intelligent Industry, Inner Mongolia University of Science and Technology, Baotou, Inner Mongolia 014010, China
b School of Science College, Inner Mongolia University of Science and Technology, Baotou, Inner Mongolia 014010, China
c School of Automation and Electrical Engineering, Inner Mongolia University of Science and Technology, Baotou, Inner Mongolia 014010, China
d Life Sciences Research Center, School of Life Science and Technology, Xidian University, Xi’an, Shaanxi 710071, China
e Hainan Free Trade Port Health Medical Research Institute, Baoting, Hainan 572300, China

A R T I C L E  I N F O

A B S T R A C T

Keywords:
Smoking addiction
Resting-state fMRI
White matter functional networks

Aims:  This  study  investigated  the  changes  in  the  organizational  and  intrinsical  activities  of  the  white  matter 
functional networks (WMFNs) in young smokers using resting-state functional magnetic resonance imaging.
Methods: A data-driven approach was used to characterize the WMFNs of 30 young smokers and 30 non-smokers. 
We applied K-means clustering to the neuroimaging data to delineate the WMFNs. Functional neural activities of 
the WMFNs were compared between the two groups. Correlation analyses were also conducted for the WMFNs 
neural activities of and clinical indicators of smoking.
Results: Eight WMFNs were identified in both groups. Compared to non-smokers, young smokers demonstrated a 
different  dorsal  attention  network  and  lack  of  a  frontostriatal  network.  The  neural  activities  in  the  frontal 
network, deep frontoparietal network, and visual network were reduced in young smokers. Further correlation 
analyses showed that the decreased neural activity in the deep frontal network and deep frontoparietal network 
were significantly negatively correlated with the Fagerstr¨om Test for Nicotine Dependence.
Conclusion: Young smokers exhibited differences in the organizational structure and neural activity intensities of 
the WMFNs. The present findings may indicate the importance of WMFNs in young smokers, which can help in 
obtaining a comprehensive understanding of the neural mechanisms underlying smoking addiction.

1. Introduction

Smoking  has  become  the  leading  preventable  cause  of  premature 
death  and  disease  worldwide,  with  an  estimated  5.4  million  people 
dying each year from tobacco-related causes. This number is expected to 
rise  to  8  million  by  2030  (https://www.cdc.gov/tobacco/global).  Ac-
cording to a 2018 survey, the total number of smokers in China was as 
high as 308 million, of whom 22.2% started smoking before the age of 
18  years  (http://www.chinacdc.cn).  Studies  have  shown  that  adoles-
cence is a critical period for the formation of smoking behavior and that 
brain functions gradually mature during this period (Leslie, 2020). The 
younger  the  age  individuals  first  start  smoking,  the  higher  the 

probability of nicotine addiction (National Center for Chronic Disease P, 
Health  Promotion  Office  on  S,  Health  2012;  White  et  al.,  2009). 
Furthermore,  nicotine  use  during  adolescence  can  lead  to  changes  in 
cognitive  function  and  behavior,  which  may  contribute  to  psychopa-
thology (Wen et al., 2023). Therefore, studying the neural mechanisms 
underlying smoking in young smokers is of great significance to help us 
understand  the  pathogenesis  of  nicotine  addiction,  which  may 
contribute to the development of interventions for nicotine addiction.

The  blood  oxygen  level  dependent  (BOLD)  signal  was  mainly 
determined by the change in paramagnetic deoxyhemoglobin, which is 
the result of the combined effect of oxygen metabolism, cerebral blood 
flow and cerebral blood volume (Raimondo et al., 2021). In recent years, 

* Corresponding author at: School of Science College, Inner Mongolia University of Science and Technology, Baotou, Inner Mongolia 014010, China.
** Corresponding  author  at:  School  of  Automation  and  Electrical  Engineering,  Inner  Mongolia  University  of  Science  and  Technology,  Baotou,  Inner  Mongolia 
014010, China.
*** Corresponding author at: Life Sciences Research Center, School of Life Sciences and Technology, Xidian University, Xi’an, Shaanxi, 710071, China.

E-mail addresses: xueting41@imust.edu.cn (T. Xue), fmydh@imust.edu.cn (D. Yu), kyuan@xidian.edu.cn (K. Yuan). 

1 Both authors contributed equally to this article.

https://doi.org/10.1016/j.neuroimage.2024.120917
Received 23 August 2024; Received in revised form 11 October 2024; Accepted 4 November 2024  
Available online 5 November 2024 
1053-8119/© 2024 The Authors.  Published by Elsevier Inc.  This is an open access article under the CC BY-NC license ( http://creativecommons.org/licenses/by- 
nc/4.0/ ). 

J. Wang et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120917 

resting-state functional magnetic resonance imaging (fMRI) has become 
an important tool to study the functional structure of human cerebral 
cortex  (Yu  et  al.,  2024).  By  comparing  the  correlations  of  functional 
BOLD signal fluctuations in different regions, the brain can be valuated 
as a complex network with hierarchical spatial and functional organi-
zation (Biswal et al., 1995; Park and Friston, 2013; Yeo et al., 2011). For 
example, fMRI studies based on BOLD signals found that the density and 
functional connectivity of the gray matter in the anterior insula were 
lower in smokers than in non-smokers (Stoeckel et al., 2016). One recent 
study focusing on large-scale networks reported that the abnormal in-
teractions between two core gray matter networks (default mode and 
salience networks) in smokers, with brain function moving away from 
the  default  mode  network  and  towards  the  salience  network.  They 
speculated  that  this  might  be  related  to  reduced  inwardly  focused 
cognition and enhanced processing of salient external stimuli in smokers 
(Wang et al., 2021). However, hemodynamic changes in white matter 
can also be detected by resting-state fMRI, although the extent of the 
hemodynamic changes is smaller than that in the gray matter (Gawryluk 
et  al.,  2014).  Recent  studies  had  shown  that  BOLD  signal  changes  in 
white  matter  were  related  to  disease  pathophysiology.  One  study  re-
ported  decreased  functional  connectivity  of  the  deep  white  matter  in 
patients  with  temporal  lobe  epilepsy;  they  concluded  that  the  deep 
white matter network was a  key network node  for functional impair-
ment in temporal lobe epilepsy (Cui et al., 2021). Another study found 
that the functional connectivity from deep to superficial white matter 
networks  was  suppressed  in  patients  with  Parkinson’s  disease,  thus 
providing evidence for the weakening of white matter function caused 
by Parkinson’s disease (Meng et al., 2022). These results indicated that 
the BOLD signal in white matter reflected the neural activity in the brain 
to some extent. Therefore, studies on the functional signals of the white 
matter  in  smoking  addiction  may  provide  additional  perspectives  for 
elucidating of the neural mechanisms underlying nicotine addiction (Ji 
et al., 2017; Xue et al., 2022).

Current research had focused on the structural abnormalities of the 
white matter and the integrity of fiber bundles based on diffusion tensor 
imaging  (He  et  al.,  2022;  Zhang  et  al.,  2022;  Yuan  et  al.,  2018a,  b). 
Compared  to  non-smokers,  those  who  smoke  demonstrated  increased 
fractional anisotropy (FA) in the left superior longitudinal fasciculus, left 
anterior  corona  radiata,  left  superior  corona  radiata,  left  posterior 
corona radiata, left external capsule, left fronto-occipital fasciculus, and 
sagittal layer, whereas they exhibited decreased radial diffusivity (RD) 
in  the  left  superior  longitudinal  fasciculus  (Yu  et  al.,  2016).  These 
studies  have  revealed  structural  abnormalities  in  the  white  matter  of 
smokers.  However,  to  our  knowledge,  very  little  is  known  about  the 
dysfunction  of  white  matter  in  young  smokers  and  their  functional 
neural activity within the white matter functional networks (WMFNs).
The  white  matter  acted  as  an  efficient  communication  bridge  be-
tween brain regions (Ji et al., 2017) and the WMFNs provide important 
information for understanding the organization of the functional activ-
ities of the white matter, thus enabling human behavior and cognitive 
function to be more deeply understood (Li et al., 2020). Recent studies 
had  demonstrated that  WMFNs  were  similar to  the  gray  matter  func-
tional  networks  in  organization  and  small-world  topology  properties, 
and highly coexisted spatially with several important white matter fiber 
bundles  (Peer  et  al.,  2017;  Wang  et  al.,  2022).  In  smokers,  lower 
small-world  attributes  of  white  matter  functional  connectivity  were 
found than non-smokers, which can be used as biomarkers of nicotine 
addiction (Fan et al., 2023). These findings illustrated that elucidation of 
WMFNs  may  provide  important  complementary  information  on  how 
intrinsic brain activity interacted and was organized in smokers.

In this study, we adopted a data-driven approach to explore the or-
ganization  and  functional  neural  activity  intensity  of  the  WMFNs  in 
young smokers. K-means clustering was used to separately delineate the 
WMFNs  of  the  two  groups  (Peer  et  al.,  2017;  Bu  et  al.,  2022).  The 
functional neural activities of the WMFNs were compared between the 
two groups. Correlation analyses were also conducted to examine the 

relationships  between  the  intensity  of  the  functional  activities  of 
WMFNs and the clinical indicators of smoking. We hypothesized that (1) 
young  smokers  exhibited  different  WMFN  patterns  compared  with 
nonsmokers  and  (2)  altered  WMFNs  may  be  associated  with  clinical 
indicators of nicotine addiction. We hope the study may provide a more 
in-depth understanding of the neural mechanisms underlying nicotine 
addiction from WMFN perspective.

2. Materials and methods

This  study  was  approved  and  supervised  by  the  Medical  Ethics 
Committee  of  the  First  Affiliated  Hospital of  Baotou  Medical College, 
Inner Mongolia University of Science & Technology. The experimental 
procedures complied with the ethical guidelines of the Declaration of 
Helsinki.  All  participants  in  this  study  were  college  students.  After  a 
detailed understanding of the experimental process, all participants and 
their guardians signed informed consent forms.

2.1. Participants

The  young  male  smokers  were  selected  based  on  the  diagnostic 
criteria  for  nicotine  dependence  in  the  American  Diagnostic  and  Sta-
tistical Manual of Mental Disorders, Fifth Edition. The main inclusion 
criteria were: (1) smoking behavior lasting for more than 2 years, and 
the number of cigarettes smoked per day was greater than or equal to 10; 
(2)  no  smoking  cessation  behavior  in  the  past  6  months;  and  (3)  no 
history of other drug abuse. Healthy male non-smokers, matched for age 
and education level, were recruited from non-smoking dormitories and 
neither of their parents were smokers to avoid the effects of secondhand 
smoke  exposure.  This  study  focused  on  different  neural  activity  of 
WMFNs  between  non-deprived  young  smokers  and  non-smokers. 
Therefore,  participants  were only  asked to  refrain  from  smoking dur-
ing the 30 min immediately preceding the scan to exclude withdrawal 
symptoms.

All participants met the following criteria: (1) no organic brain dis-
eases such as brain tumors; (2) no history of other drug abuse; (3) no 
history of mental illness; and (4) no contraindications for MRI (such as 
pacemakers). Thirty young smokers and 30 healthy non-smokers were 
recruited. All the participants were males and right-handed. All partic-
ipants underwent routine MRI before the resting-state scan, and no brain 
lesions were found. The detailed demographic information is presented 
in Table 1.

2.2. Image acquisition

The Philips 3.0T magnetic resonance scanner was used for the study. 
During scanning, the heads of all participants were fixed with a foam 
pad to reduce head movement. Ear plugs were used to minimize noise. 
Resting-state fMRI data were acquired using a gradient echo-echo planar 

Table 1 
Participant demographic and clinical information.

Age (years)
Age range (years)
Sex
Age started smoking
Smoking years
FTND
Pack-years
Strong hand
Educational level

Smokers  
(n = 30)

19.7 ± 2.0
16–23
males
14.9 ± 2.0
3.8 ± 1.5
7.0 ± 1.6
2.7 ± 1.5
Dextral
Bachelor’s degree

Non-smokers  
(n = 30)

19.3 ± 1.4
16–23
males
–
–
–
–

Dextral
Bachelor’s degree

P

0.29
–
–
–
–
–
–
–
–

Data are presented as mean ± standard deviation.
FTND: Fagerstr¨om Test for Nicotine Dependence.
Pack-years: smoking years × daily consumption/20.

2 

J. Wang et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120917 

imaging  sequence  with  the  following  scanning  parameters:  repetition 
time 2 s; echo time 30 ms; matrix, 64 × 64; field of view, 220 mm; flip 
◦
; scanning time, 6 min. During the scanning process, all par-
angle 90
ticipants were required to keep their entire body still and eyes closed.

2.3. Image preprocessing

Image preprocessing was performed using the Data Processing As-
sistant  for  Resting-State  fMRI  (http://rfmri.org/DPARSF),  Statistical 
Parametric  Mapping  toolkits  (SPM12,  http://www.fil.ion.ac.uk/spm) 
and open MATLAB scripts (https://www.beyropsychiatrylab.com/code 
s_wm). The first 10 volumes of fMRI scans were removed. Next, slice- 
timing correction and realignment were performed. T1 anatomical im-
ages  were  then  coregistered  to  the  functional  images,  and  further 
segmented  into  tissue  probability  maps  of  white  matter,  gray  matter, 
and  cerebrospinal  fluid  (CSF)  by  using  a  diffeomorphic  nonlinear 
registration algorithm in SPM12. Linear trends were removed to correct 
for signal drift. The mean CSF signals (95% threshold) and 24-parameter 
motion parameters (six motion parameters, their values at the previous 
time point, and the 12 corresponding squared values) were regressed out 
from functional data. The mean white matter and global brain signals 
were  not  regressed  out  to  prevent  eliminating  the  meaningful  neural 
signals  (Peer  et  al.,  2017).  To  minimize  the  potential  effects  of  head 
motion, we also applied temporal scrubbing (framewise displacement >
0.2 mm). A bandpass filtering (0.01–0.08 Hz) was performed to mini-
mize high-frequency non-neuronal noise. To mitigate the partial volume 
effect,  spatial  smoothing  (with  a  4-mm  full-width  at  half-maximum 
Gaussian kernel) was applied separately to the white matter and gray 
matter images. Finally, the functional images were spatially normalized 
into  the  Montreal  Neurologic  Institute space  by  T1  segmentation  and 
were resampled into 3 × 3 × 3 mm3.

2.4. Creation of group-level white matter templates

We used the segmentation results from each participant to obtain a 
mask for voxel selection for clustering in groups. Each voxel was iden-
tified as white matter, grey matter, or CSF depending on the segmented 
maximum probability graph. All masks from the participants were then 
averaged to obtain the percentage of participants classified as white or 
grey matter in each voxel.

Voxels identified as white matter in more than 60% of the partici-
pants were used to create the stencil. We then compared the resulting 
masks to the functional data and removed the voxels identified as white 
matter with functional data from less than 80% of the participants (such 
as parts of the medulla and spinal cord). We used the Harvard-Oxford 
Atlas to label the grey matter voxels included in the thalamus, caudate 
nucleus,  putamen,  globus  pallidus,  and  nucleus  accumbens  (removed 
from the white matter mask) as grey matter voxel (Lorio et al., 2016; 
Wonderlick et al., 2009).

2.5. Neural activity analysis of WMFNs

In this study, a data-driven clustering method was used to separately 
create  WMFNs  for  the  smoker  and  nonsmoker  groups.  According  to 
previous researches (Peer et al., 2017; Bu et al., 2020), firstly, two sets of 
white matter masks were created to select the voxels for clustering in 
smoker  and  non-smoker  groups  respectively.  More  precisely, we  only 
retained voxels that were determined to be white matter and covered 
more than 80% of the participants’ functional data. Next, a voxel-wise 
Pearson correlation matrix of the white matter was calculated for each 
participant.  These  individual-level  correlation  matrices  were  then 
averaged for each group, yielding two group-level correlation matrices. 
Finally, the K-means clustering method was used to cluster white matter 
voxels with similar functional connections for the two group-level cor-
relation matrices (Blumensath et al., 2013; Moreno-Dominguez et al., 
2014; Peer et al., 2014). The number of clusters was set between 2 and 

22, and the Dice coefficient was used to evaluate cluster stability, with a 
value greater than 0.9 as the evaluation criterion (Peer et al., 2017). A 
power  spectrum  analysis  has  been  widely  used  to  detect  significant 
differences in signal amplitude across different neurological regions and 
pathological states of gray matter (Yang et al., 2007; Zuo et al., 2010). 
We  used  this  method  to  analyze  the  neural  activity  of  white  matter 
networks in young smokers. Fourier transform was performed for each 
white  matter  network  of  each  participant  to  extract  each  frequency 
amplitude. Frequency–power plots for each network were generated by 
averaging the amplitudes of all participants within each group.

2.6. Statistical analysis

For  each  white  matter  network,  the  average  amplitude  of  all  par-
ticipants  was  used  to  represent  the  degree  of  network  activity,  and  a 
two-sample  t-test  was  performed  to  detect  neural  activity  differences 
between the two groups. False discovery rate (FDR) correction was used 
to resolve multiple comparisons among multiple white matter networks. 
P < 0.05 was used to determined significance.

Pearson correlation analysis was used to elucidate the relationships 
between the aberrant neural activity of WMFNs and clinical indicators of 
smoking (FTND score). We used false discovery rate (FDR) correction to 
address multiple correlation analysis. P < 0.05 was used to determine 
significance.

3. Results

3.1. Clustering results of WMFNs

Using the K-means clustering method with the white matter corre-
lation  matrix,  nine  WMFNs  were  found  in  smokers  and  non-smokers 
(Fig. 1A and B). Then, we qualitatively defined the WMFNs according 
to  their  corresponding  relationships  with  known  resting-state  grey 
matter  networks  (Yeo  et  al.,  2011). Finally,  the  default  mode,  visual, 
deep frontal, cognitive control, somatomotor, deep frontoparietal (FPN), 
and  inferior  corticospinal-cerebellar  networks  were  observed  in  both 
young smokers and non-smokers. Notably, compared to non-smokers, 
young  smokers  had  a  different  dorsal  attention  network  (DAN)  and 
lacked a frontalstriatal network. The WMFNs scores for each group were 
displayed in Fig. 2.

3.2. Different neural activity of WMFNs between smokers and non- 
smokers

Frequency amplitude was used to represent the neural activity of the 
WMFNs.  Generally,  for  most  WMFNs,  the  trend  for  each  amplitude 
decreased with  frequency. The exception was  the FPN, which  had an 
increasing trend in amplitude with frequency. Compared with the non- 
smokers, the lower average amplitudes of the deep frontal, deep FPN, 
and visual networks were observed in young smokers (Fig. 3). Activity in 
the  deep  frontal  network  was  inversely  associated  with  FTND  scores 
(r=(cid:0) 0.47, P-FDR corrected=0.008) and FPN activity was also negatively 
correlated with FTND scores (r=(cid:0) 0.39, P-FDR corrected=0.035) (Fig. 4).

4. Discussion

In the present study, the functional organization of WMFNs in young 
smokers and non-smokers was investigated,; and neural activity alter-
ations of the WMFNs were also examined. A total of nine WMFNs were 
found  in  young  smokers  and  non-smokers,  among  which  seven  were 
observed in both young smokers and non-smokers. However, compared 
with young non-smokers, young smokers showed a different DAN and 
lacked  the  frontostriatal  network.  Compared  to  non-smokers,  young 
smokers exhibited decreased amplitudes in the deep frontal, FPN, and 
visual networks. Moreover, the decreased amplitudes in the deep frontal 
network and FPN were negatively correlated with the degree of nicotine 

3 

J. Wang et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120917 

Fig. 1. A) Based on the Dice coefficient, eight reliable and stable clustering results were obtained for young smokers. B) Eight reliable and stable clustering results 
were obtained for non-smokers. C) The eight WMFNs in young smokers. D) The eight WMFNs in non-smokers. WMFNs, white matter functional networks.

addiction.  Our  findings  provide  additional  evidence  for  the  neural 
mechanisms underlying smoking addiction.

4.1. Abnormal WMFNs organization in young smokers

Previous  studies  have  found  structural  abnormalities  in  the  white 
matter of young smokers (Zhou et al., 2022). The current study further 
explored potential changes in white matter functional activity in young 
smokers from the perspective of WMFNs. Seven WMFNs were identified 
in both the groups. Notably, we found a characteristic DAN and a loss in 
the frontostriatal network of young smokers, suggesting differences in 
the organization of WMFNs between young smokers and non-smokers.

The current findings showed that young smokers presented with a 
characteristic white matter network, the DAN. The DAN is considered to 
be involved in attention regulation and spatial cognition and is mainly 
involved in top-down attention control (Majerus et al., 2012; Majerus 
et  al.,  2016).  As  a  behavioral  addiction,  smoking  addiction  involves 
complex cognitive and behavioral processes (Hall et al., 2016). In this 
study, we found that the DAN appeared to be a characteristic network in 

young smokers. Thus, compared to young non-smokers, young smokers 
may have a higher attentional dependence on smoking behavior and be 
more sensitive and attentive to smoking-related information, which will 
eventually  lead  to  an  abnormal  allocation  of  attention  to  smoking 
stimuli.  In  addition,  the  DAN  plays  an  important  role  in  reward  and 
memory, which may be related to the reward enhancement and memory 
encoding of smoking addiction (Le Foll et al., 2022; Dumais et al., 2018). 
Therefore,  abnormal  DAN  activity  may  also  be  related  to  impaired 
reward mechanisms in young smokers.

The  absence  of  a  frontostriatal  network  in  young  smokers  was 
another  important  finding  in  this  study.  The  frontostriatal  network 
mainly  includes  the  ventral  prefrontal  cortex,  orbitofrontal  cortex, 
striatum, and the limbic system (Cubillo et al., 2012). One recent study 
found that young adults who have less developed frontostriatal circuits 
are more likely to be satisfied with immediate rewards, whereas with the 
development of the frontostriatal network, cognitive control function is 
more biased towards long-term rewards (van den Bos et al., 2015). The 
absence  of  a  frontostriatal  network  in  young  smokers  may  indicate 
impaired  cognitive  control  and  a  preference  for  immediate  rewards. 

4 

J. Wang et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120917 

Fig. 2. Nine WMFNs were obtained by the K-means clustering method. Among these WMFNs, seven white matter networks were found in both groups: default mode, 
visual,  deep  frontal, cognitive control, the somatomotor,  the deep frontoparietal, and the inferior corticoponal-cerebellum networks. The dorsal  attention white 
matter network was found only in young smokers, whereas the frontostriatal was found only in non-smokers. WMFNs, white matter functional networks.

Additionally, our previous study that focused on the grey matter fron-
tostriatal  network  found  decreased  intra-resting-state  functional  con-
nectivity (FC) in young smokers; decreased FC within the frontostriatal 
network was negatively correlated with FTND (Yuan et al., 2016). The 
absence of the white matter frontostriatal network in the current study 
may  provide  additional  evidence  for  the  disruption  of  this  network, 
illustrating  its  important  role  in  the  neuropathology  of  nicotine 
addiction.

4.2. Hypoactive activity in the WMFNs

The  current  study  identified  three  less  active  WMFNs  in  young 
smokers: the deep frontal network, the FPN, and the visual network. The 
deep frontal network primarily includes the orbitofrontal cortex, supe-
rior  frontal  gyrus  (SFG),  anterior  cingulate  cortex,  and  dorsolateral 
prefrontal  cortex  (Goldstein  and  Volkow,  2011).  Compared  to 
non-smokers, smokers show abnormal intra-network FC within the deep 
frontal network, manifesting as decreased FC between the orbitofrontal 
cortex and the SFG (Zhou et al., 2017). One study focused on craving 
regulation in cigarette smokers and found that the SFG plays a signifi-
cant role in modulating cigarette cravings (Rose et al., 2011). Given that 
the deep frontal network plays an important role in cognitive control, 
emotion  regulation,  social  behavior,  decision  making  and  self-control 
(Case, 1992; Chen et al., 2024), we speculated that the decreased ac-
tivity in the white matter deep frontal network is likely associated with 
impaired cognitive control, decision-making, and emotion regulation in 
young  smokers.  We  found  that  decreased  activity  in  the  deep  frontal 
network  was  negatively  correlated  with  FTND.  This  highlights  the 
essential  role  of  the  deep  frontal  network  in  smoking  addiction,  as  a 
function of the structural network.

The FPN includes the dorsolateral prefrontal cortex (DLPFC), lateral 
frontal  pole,  dorsal  attention  cingulate  cortex,  intraparietal  sulcus, 

anterior insula, and precuneus (Vincent et al., 2008; Shao et al., 2024). 
This network is often associated with cognitive and executive control 
function (Menon, 2011). Several studies have reported that abstinence 
can disrupt DLPFC function (Hong et al., 2011; Kozink et al., 2010a, b; 
Guo et al., 2023). For example, a study exploring the effect of abstinence 
on  cognitive  control  found  that  the  DLPFC  of  abstinent  smokers  was 
hyperactivated  when  performing  a  color-word  Stroop  task  (Froeliger 
et al., 2012). These findings may indicate a need to recruit additional 
frontal  executive  neural  resources  to  execute  cognitive  control  over 
competing information in efforts to perform primary task goals. Addi-
tionally,  it  has  been  suggested  that  executive  function  can  be  distin-
guished  as  hot  and  cool,  and  cold  executive  function  is  mainly 
non-emotional  cognitive  control,  which  is  regulated  by  the  FPN  (Bu 
et  al.,  2022).  Previous  studies  have  shown  that  smokers  have  signifi-
cantly  reduced  functional  connectivity  in  the  FPN  compared  to 
non-smokers (Yip et al., 2022). Our finding of lower intrinsic activity in 
the white matter within the FPN and its correlation with FTND provides 
direct  evidence  of  functional  disruption  in  this  network,  which  may 
contribute to cognitive executive control deficits in young smokers.

The  regulation  of  visual  attention  relies  heavily  on  the  visual 
network, and empirical evidence has consistently demonstrated the in-
tegral role of vision in the selective attention process (Fox et al., 2005a, 
b). Smoking addiction may result in a stronger attentional bias towards 
smoking-related stimuli, indicating that smokers may be more sensitive 
to  smoking-related  visual  stimuli  (Sanders-Jackson  et  al.,  2011). 
Therefore, aberrant functional connectivity in visual networks may be 
related to attentional biases in the processing of smoking-related visual 
stimuli.

5. Limitations

This study has several limitations that should be considered. First, 

5 

J. Wang et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120917 

Fig. 3. Averaged amplitude of young smokers and non-smokers for the WMFNs. The left panel is a frequency plot showing the activity frequency within each WMFN. 
The right panel is a plot of the differences in the mean amplitude for each WMFN between young smokers and non-smokers. An asterisk indicates a significant 
difference (*P < 0.05, false discovery rate corrected). CNN, cognitive control network; CST, corticospinal tract; DAN, dorsal attention network; DMN, default mode 
network; SMN, somatomotor network; WMFNs, white matter functional network.

the participants were all adolescent males; whether female adolescents 
addicted  to  smoking  are  applicable  to  the  results  of  this  study  is  un-
known. Second, for the clustering algorithm, the sample size used in this 
study was relatively small, which may have affected the robustness of 
the results. However, multiple comparisons were performed to support 
the  reliability  of  the  results.  Finally,  due  to  the  complexity  of  white 
matter  fiber  bundles,  it  was  difficult  to  determine  from  which  nerve 
bundle the white matter BOLD signal originates. In future research we 
will consider the relationship between white matter tracts and WMFNs 
more accurately in combination with tractography.

6. Conclusions

In this study, we used a data-driven approach to cluster WMFNs. We 
found that young smokers showed a characteristic DAN, lacked a fron-
tostriatal network, and neural activity in the deep frontal network, FPN, 
and visual network was decreased. Moreover, we found that decreased 

6 

activity  in  the  FPN  and  deep  frontal  network  was  significantly  nega-
tively associated with FTND, suggesting an essential role they play in 
smoking  addiction,  especially  the  degree  of  smoking  addiction.  The 
present  findings  may  indicate  the  importance  of  WMFNs  in  nicotine 
addiction  in  young  smokers,  and  help  obtain  a  more  comprehensive 
understanding of neural activity in young smokers.

Funding

and 

Brain-like 

This work was supported by the Chinese National Programs for Brain 
Science 
[number 
Intelligence 
2022ZD0214500]; National Natural Science Foundation of China [grant 
numbers  82260359,  82371500,  U22A20303,  61971451,  82260359]; 
Natural Science Foundation of Inner Mongolia [numbers 2021MS08014, 
2023QN08007]; Fundamental Research Funds from the Inner Mongolia 
University of Science and Technology; Development Program for Young 
Talents  of  Science  and  Technology  in  Universities  of  Inner  Mongolia 

Technology 

J. Wang et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120917 

Fig. 4. A) The activity of the deep frontal network shows a significant negative correlation with FTND (P < 0.05, FDR corrected). B) The FPN activity shows a 
significant negative correlation with the FTND (P < 0.05, FDR corrected). FPN, frontoparietal; Fagerstr¨om Test for Nicotine Dependence.

[number NJYT24030]; and the Key Research and Development Program 
of BaoTing [number BTZDYF2024004].

CRediT authorship contribution statement

Junxuan Wang: Writing – original draft, Validation, Methodology, 
Formal analysis, Data curation, Conceptualization. Ting Xue: Writing – 
review & editing, Funding acquisition, Formal analysis, Data curation, 
Conceptualization. Daining Song: Methodology, Formal analysis. Fang 
Dong: Resources, Investigation. Yongxin Cheng: Formal analysis. Juan 
Wang:  Software.  Yuxin  Ma:  Resources.  Mingze  Zou:  Data  curation. 
Shuailin  Ding:  Visualization.  Zhanlong  Tao:  Investigation.  Wuyuan 
Xin:  Visualization.  Dahua  Yu:  Writing  –  review  &  editing,  Funding 
acquisition, Conceptualization. Kai Yuan: Writing – review & editing.

Declaration of competing interest

The authors have no conflict of interests to disclose.

Data availability

The  datasets  presented  in  this  article  are  not  readily  available 
because  of  the  privacy  of  all  the  participants.  Requests  to  access  the 
datasets should be directed to the corresponding authors. 

References

Biswal, B., Yetkin, F.Z., Haughton, V.M., Hyde, J.S., 1995. Functional connectivity in the 
motor cortex of resting human brain using echo-planar MRI. Magn. Reson. Med. 34 
(4), 537–541.

Fox, M.D., Snyder, A.Z., Vincent, J.L., Corbetta, M., Van Essen, D.C., Raichle, M.E., 
2005a. The human brain is intrinsically organized into dynamic, anticorrelated 
functional networks. Proc. Natl. Acad. Sci. U. S.A. 102 (27), 9673–9678.

Fox, P.T., Laird, A.R., Lancaster, J.L., 2005b. Coordinate-based voxel-wise meta-analysis: 
dividends of spatial normalization. Report of a virtual workshop. Hum. Brain Mapp. 
25 (1), 1–5.

Froeliger, B., Modlin, L., Wang, L., Kozink, R.V., McClernon, F.J., 2012. Nicotine 
withdrawal modulates frontal brain function during an affective Stroop task. 
Psychopharmacology (Berl) 220 (4), 707–718.

Gawryluk, J.R., Mazerolle, E.L., D’Arcy, R.C, 2014. Does functional MRI detect activation 
in white matter? A review of emerging evidence, issues, and future directions. Front. 
Neurosci. 8, 239.

Goldstein, R.Z., Volkow, N.D., 2011. Dysfunction of the prefrontal cortex in addiction: 
neuroimaging findings and clinical implications. Nat. Rev. Neurosci. 12 (11), 
652–669.

Guo, Y., Zhao, X., Zhang, X., et al., 2023. Effects on resting-state EEG phase-amplitude 

coupling in insomnia disorder patients following 1 Hz left dorsolateral prefrontal 
cortex rTMS. Hum. Brain Mapp. 44 (8), 3084–3093.

Hall, B.J., Cauley, M., Burke, D.A., Kiany, A., Slotkin, T.A., Levin, E.D., 2016. Cognitive 

and behavioral impairments evoked by low-level exposure to tobacco smoke 
components: comparison with nicotine alone. Toxicol. Sci. 151 (2), 236–244.
He, Z., Du, L., Huang, Y., et al., 2022. Gyral hinges account for the highest cost and the 
highest communication capacity in a corticocortical network. Cereb. Cortex 32 (16), 
3359–3376.

Hong, L.E., Schroeder, M., Ross, T.J., et al., 2011. Nicotine enhances but does not 
normalize visual sustained attention and the associated brain network in 
schizophrenia. Schizophr. Bull. 37 (2), 416–425.

Ji, G.J., Liao, W., Chen, F.F., Zhang, L., Wang, K., 2017. Low-frequency blood oxygen 
level-dependent fluctuations in the brain white matter: more than just noise. Sci. 
Bull. (Beijing) 62 (9), 656–657.

Kozink, R.V., Kollins, S.H., McClernon, F.J., 2010a. Smoking withdrawal modulates right 
inferior frontal cortex but not presupplementary motor area activation during 
inhibitory control. Neuropsychopharmacology 35 (13), 2600–2606.

Kozink, R.V., Lutz, A.M., Rose, J.E., Froeliger, B., McClernon, F.J., 2010b. Smoking 

withdrawal shifts the spatiotemporal dynamics of neurocognition. Addict. Biol. 15 
(4), 480–490.

Le Foll, B., Piper, M.E., Fowler, C.D., et al., 2022. Tobacco and nicotine use. Nat. Rev. 

Dis. Primers 8 (1), 19.

Leslie, F.M., 2020. Unique, long-term effects of nicotine on adolescent brain. Pharmacol. 

Blumensath, T., Jbabdi, S., Glasser, M.F., et al., 2013. Spatially constrained hierarchical 

Biochem. Behav. 197, 173010.

parcellation of the brain with resting-state fMRI. Neuroimage 76, 313–324.
Bu, X., Gao, Y., Liang, K., Chen, Y., Guo, L., Huang, X., 2022. Investigation of white 
matter functional networks underlying different behavioral profiles in attention- 
deficit/hyperactivity disorder. Psychoradiology 2 (3), 69–77.

Bu, X., Liang, K., Lin, Q., et al., 2020. Exploring white matter functional networks in 
children with attention-deficit/hyperactivity disorder. Brain Commun. 2 (2), 
fcaa113.

Case, R., 1992. The role of the frontal lobes in the regulation of cognitive development. 

Brain Cogn. 20 (1), 51–73.

Chen, K., Yang, J., Li, F., et al., 2024. Molecular basis underlying default mode network 
functional abnormalities in postpartum depression with and without anxiety. Hum. 
Brain Mapp. 45 (5), e26657.

Cubillo, A., Halari, R., Smith, A., Taylor, E., Rubia, K, 2012. A review of fronto-striatal 
and fronto-cortical brain abnormalities in children and adults with Attention Deficit 
Hyperactivity Disorder (ADHD) and new evidence for dysfunction in adults with 
ADHD during motivation and attention. Cortex 48 (2), 194–215.

Cui, W., Shang, K., Qiu, B., Lu, J., Gao, J.H., 2021. White matter network disorder in 

mesial temporal epilepsy: an fMRI study. Epilepsy Res. 172, 106590.

Dumais, K.M., Chernyak, S., Nickerson, L.D., Janes, A.C., 2018. Sex differences in default 
mode and dorsal attention network engagement. PLoS One 13 (6), e0199049.
Fan, C., Zha, R., Liu, Y., et al., 2023. Altered white matter functional network in nicotine 

addiction. Psychiatry Res. 321, 115073.

Li, J., Chen, H., Fan, F., et al., 2020. White-matter functional topology: a neuromarker for 
classification and prediction in unmedicated depression. Transl. Psychiatry 10 (1), 
365.

Lorio, S., Fresard, S., Adaszewski, S., et al., 2016. New tissue priors for improved 

automated classification of subcortical brain structures on MRI. Neuroimage 130, 
157–166.

Majerus, S., Attout, L., D’Argembeau, A., et al., 2012. Attention supports verbal short- 
term memory via competition between dorsal and ventral attention networks. Cereb. 
Cortex 22 (5), 1086–1097.

Majerus, S., Cowan, N., P´eters, F., Van Calster, L., Phillips, C., Schrouff, J., 2016. Cross- 
modal decoding of neural patterns associated with working memory: evidence for 
attention-based accounts of working memory. Cereb. Cortex 26 (1), 166–179.
Meng, L., Wang, H., Zou, T., et al., 2022. Attenuated brain white matter functional 

network interactions in Parkinson’s disease. Hum. Brain Mapp. 43 (15), 4567–4579.

Menon, V., 2011. Large-scale brain networks and psychopathology: a unifying triple 

network model. Trends. Cogn. Sci. 15 (10), 483–506.

Moreno-Dominguez, D., Anwander, A., Kn¨osche, T.R., 2014. A hierarchical method for 

whole-brain connectivity-based parcellation. Hum. Brain Mapp. 35 (10), 
5000–5025.

National Center for Chronic Disease P, Health Promotion Office on S, Health, 2012. 

Reports of the Surgeon general. Preventing Tobacco Use Among Youth and Young 

7 

J. Wang et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120917 

Adults: A Report of the Surgeon General. Centers for Disease Control and Prevention 
(US), AtlantaGA. 

Park, H.J., Friston, K., 2013. Structural and functional brain networks: from connections 

White, H.R., Bray, B.C., Fleming, C.B., Catalano, R.F., 2009. Transitions into and out of 

light and intermittent smoking during emerging adulthood. Nicotine Tob. Res. 11 
(2), 211–219.

to cognition. Science 342 (6158), 1238411.

Peer, M., Nitzan, M., Bick, A.S., Levin, N., Arzy, S., 2017. Evidence for functional 

networks within the human brain’s white matter. J. Neurosci. 37 (27), 6394–6407.

Peer, M., Nitzan, M., Goldberg, I., et al., 2014. Reversible functional connectivity 
disturbances during transient global amnesia. Ann. Neurol. 75 (5), 634–643.
Raimondo, L., Oliveira, ´L.A.F, Heij, J., et al., 2021. Advances in resting state fMRI 

acquisitions for functional connectomics. Neuroimage 243, 118503.

Rose, J.E., McClernon, F.J., Froeliger, B., Behm, F.M., Preud’homme, X., Krystal, A.D., 
2011. Repetitive transcranial magnetic stimulation of the superior frontal gyrus 
modulates craving for cigarettes. Biol. Psychiatry 70 (8), 794–799.

Sanders-Jackson, A.N., Cappella, J.N., Linebarger, D.L., Piotrowski, J.T., O’Keeffe, M., 
Strasser, A.A, 2011. Visual attention to antismoking PSAs: smoking cues versus other 
attention-grabbing features. Hum. Commun. Res. 37 (2), 275–292.

Shao, Z., Guo, Y., Yue, L., et al., 2024. Comparisons of transcranial alternating current 
stimulation and repetitive transcranial magnetic stimulation treatment therapy for 
insomnia: a pilot study. Gen. Psychiatr. 37 (1), e101184.

Stoeckel, L.E., Chai, X.J., Zhang, J., Whitfield-Gabrieli, S., Evins, A.E., 2016. Lower gray 

matter density and functional connectivity in the anterior insula in smokers 
compared with never smokers. Addict. Biol. 21 (4), 972–981.

van den Bos, W., Rodriguez, C.A., Schweitzer, J.B., McClure, S.M., 2015. Adolescent 
impatience decreases with increased frontostriatal connectivity. Proc. Natl. Acad. 
Sci. U.S.A. 112 (29), E3765–E3774.

Wonderlick, J.S., Ziegler, D.A., Hosseini-Varnamkhasti, P., et al., 2009. Reliability of 
MRI-derived cortical and subcortical morphometric measures: effects of pulse 
sequence, voxel geometry, and parallel imaging. Neuroimage 44 (4), 1324–1333.

Xue, K., Liang, S., Yang, B., et al., 2022. Local dynamic spontaneous brain activity 

changes in first-episode, treatment-naïve patients with major depressive disorder 
and their associated gene expression profiles. Psychol. Med. 52 (11), 2052–2061.
Yang, H., Long, X.Y., Yang, Y., et al., 2007. Amplitude of low frequency fluctuation 

within visual areas revealed by resting-state functional MRI. Neuroimage 36 (1), 
144–152.

Yeo, B.T., Krienen, F.M., Sepulcre, J., et al., 2011. The organization of the human 

cerebral cortex estimated by intrinsic functional connectivity. J. Neurophysiol. 106 
(3), 1125–1165.

Yip, S.W., Lichenstein, S.D., Garrison, K., et al., 2022. Effects of smoking status and state 
on intrinsic connectivity. Biol. Psychiatry Cogn. Neurosci. NeuroimAging 7 (9), 
895–904.

Yu, D., Yuan, K., Zhang, B., et al., 2016. White matter integrity in young smokers: a tract- 

based spatial statistics study. Addict. Biol. 21 (3), 679–687.

Yu, X., Chen, K., Ma, Y., et al., 2024. Molecular basis underlying changes of brain entropy 
and functional connectivity in major depressive disorders after electroconvulsive 
therapy. CNS Neurosci. Ther. 30 (3), e14690.

Yuan, K., Yu, D., Bi, Y., et al., 2016. The implication of frontostriatal circuits in young 

smokers: a resting-state study. Hum. Brain Mapp. 37 (6), 2013–2026.

Vincent, J.L., Kahn, I., Snyder, A.Z., Raichle, M.E., Buckner, R.L., 2008. Evidence for a 

Yuan, K., Yu, D., Zhao, M., et al., 2018a. Abnormal frontostriatal tracts in young male 

frontoparietal control system revealed by intrinsic functional connectivity. 
J. Neurophysiol. 100 (6), 3328–3342.

Wang, K.S., Brown, K., Frederick, B.B., et al., 2021. Nicotine acutely alters temporal 

tobacco smokers. Neuroimage 183, 346–355.

Yuan, K., Zhao, M., Yu, D., et al., 2018b. Striato-cortical tracts predict 12-h abstinence- 

induced lapse in smokers. Neuropsychopharmacology 43 (12), 2452–2458.

properties of resting brain states. Drug Alcohol Depend. 226, 108846.

Zhang, S., Chavoshnejad, P., Li, X., et al., 2022. Gyral peaks: novel gyral landmarks in 

Wang, P., Wang, J., Michael, A., et al., 2022. White matter functional connectivity in 
resting-state fMRI: robustness, reliability, and relationships to gray matter. Cereb. 
Cortex 32 (8), 1547–1559.

developing macaque brains. Hum. Brain Mapp. 43 (15), 4540–4555.

Zhou, M., Hu, Y., Huang, R., et al., 2022. Right arcuate fasciculus and left uncinate 

fasciculus abnormalities in young smoker. Addict. Biol. 27 (2), e13132.

Wen, X., Yue, L., Du, Z., et al., 2023. Implications of neuroimaging findings in addiction. 

Zhou, S., Xiao, D., Peng, P., et al., 2017. Effect of smoking on resting-state functional 

Psychoradiology 3, kkad006.

connectivity in smokers: an fMRI study. Respirology 22 (6), 1118–1124.

Zuo, X.N., Di Martino, A., Kelly, C., et al., 2010. The oscillating brain: complex and 

reliable. Neuroimage 49 (2), 1432–1445.

8 

