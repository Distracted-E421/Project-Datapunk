NeuroImage 303 (2024) 120943 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Relaxometry network based on MRI R2* mapping revealing brain iron 
accumulation patterns in Parkinson’s disease

Weizhao Lu a,b, Tianbin Song a,b, Zhenxiang Zang c,d, Jiping Li e, Yuqing Zhang e, Jie Lu a,b,*
a Department of Radiology and Nuclear Medicine, Xuanwu Hospital, Capital Medical University, Beijing, 100053, China
b Beijing Key Laboratory of Magnetic Resonance Imaging and Brain Informatics, Xuanwu Hospital, Beijing, 100053, China
c Beijing Key Laboratory of Mental Disorders, National Clinical Research Center for Mental Disorders & National Center for Mental Disorders, Beijing Anding Hospital, 
Capital Medical University, Beijing, China
d Advanced Innovation Center for Human Brain Protection, Capital Medical University, Beijing, China
e Beijing Institute of Functional Neurosurgery, Xuanwu Hospital, Capital Medical University, Beijing, 100053, China

A R T I C L E  I N F O

A B S T R A C T

Keywords:
Parkinson’s disease
R2* quantification
Iron accumulation
Relaxometry covariance network
Substantia nigra

Background: Excessive iron accumulation in the brain has been implicated in Parkinson’s disease (PD). However, 
the patterns and probable sequences of iron accumulation across the PD brain remain largely unknown. This 
study aimed to explore the sequence of iron accumulation across the PD brain using R2* mapping and a relax-
ometry covariance network (RCN) approach.
Methods: R2* quantification maps were obtained from PD patients (n = 34) and healthy controls (n = 25). RCN 
was configured on R2* maps to identify covariance differences in iron levels between the two groups. Regions 
with excessive iron accumulation and large covariance changes in PD patients compared to controls were defined 
as  propagators  of  iron.  In  the  PD  group,  causal  RCN  analysis  was  performed  on  the  R2*  maps  sequenced  ac-
cording to disease duration to investigate the dynamics of iron accumulations from the propagators. The asso-
ciations between individual connections of the RCN and clinical information were analyzed in PD patients.
Results: The left substantia nigra pars reticulata (SNpr), left substantia nigra pars compacta (SNpc), and lobule VII 
of the vermis (VER7) were identified as primary regions for iron accumulation and propagation (propagator). As 
the disease duration increased, iron accumulation in these three propagators demonstrated positive causal effects 
on the bilateral pallidum, bilateral gyrus rectus, right middle frontal gyrus, and medial and anterior orbitofrontal 
cortex (OFC). Furthermore, individual connections of VER7 with the left gyrus rectus and anterior  OFC were 
positively associated with disease duration.
Conclusions: Our results indicate that the aberrant iron accumulation in PD involves several regions, mainly starts 
from the SN and cerebellum and extends to the pallidum and cortices. These findings provide preliminary in-
formation on sequences of iron accumulation in PD, which may advance our understanding of the disease.

1. Introduction

Parkinson’s  disease  (PD)  is  a  chronic  neurodegenerative  disorder 
that primarily affects a patient’s motor abilities and is often accompa-
nied by non-motor symptoms (Kalia and Lang, 2015). PD can impact the 
quality of patients’ daily lives and lead to mental health problems such 
as depression, anxiety and dementia (Beitz, 2014). Over the past two 
decades,  PD  has  undergone  rapid  growth  in  prevalence,  posing  an 
increasing challenge to global public health (Ou et al., 2021). However, 
the etiology and pathogenesis of PD have not been fully elucidated to 
date (Schapira and Jenner, 2011). Therefore, more in-depth research is 

needed to investigate the etiology and pathogenesis of PD in order to 
provide more effective treatment options for PD patients.

There is a consensus that iron deposition is implicated in the path-
ogenesis  of  PD  (Faucheux  et  al.,  2003).  Two  mechanisms  have  been 
proposed involving iron and the pathology of PD (Zhang et al., 2011). 
First, neuromelanin granules with iron overload, both inside and outside 
the neurons in PD patients, can contribute to oxidative stress and induce 
microglia activation, neuroinflammatory, and subsequent degenerative 
processes  (Shi  et  al., 2019,  Leh´ericy  et  al.,  2020). Second,  iron has  a 
close  connection  with  alpha-synuclein,  the  aggregation  of  which  can 
cause familial PD (Guan et al., 2022, Thomas et al., 2020). In addition, 

* Corresponding author at: Department of Radiology and Nuclear Medicine, Xuanwu Hospital, No.45 Changchun Road, Beijing, 100053, China.

E-mail address: imaginglu@hotmail.com (J. Lu). 

https://doi.org/10.1016/j.neuroimage.2024.120943
Received 12 June 2024; Received in revised form 12 October 2024; Accepted 18 November 2024  
Available online 19 November 2024 
1053-8119/© 2024 Published by Elsevier Inc. This is an open access article under the CC BY-NC-ND license ( http://creativecommons.org/licenses/by-nc-nd/4.0/ ). 

W. Lu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120943 

previous studies using animal models have demonstrated that injury to 
the  nigrostriatal  system  alone  can  induce  iron  accumulation  in  the 
substantia nigra (SN), and dopaminergic cell death precedes iron accu-
mulation,  indicating  that  iron  accumulation  may  contribute  to  the 
progression of nigral degeneration (Du et al., 2022, Liu et al., 2021).

Neuroimaging  techniques,  especially  the  iron-sensitive  magnetic 
resonance imaging (MRI) technique, provide a convenient approach to 
characterize  iron  accumulation  in  the  brain  in  vivo  (Li  et  al.,  2017). 
Using  quantitative  susceptibility  mapping  (QSM),  researchers  have 
revealed increased iron deposition in the SN, red nucleus (RN), frontal, 
posterior parietal and insular cortices, as well as decreased QSM values 
in the occipital lobes of patients with PD (Postuma et al., 2015, Uddin 
et  al.,  2016,  Rolls  et  al.,  2020,  Monsivais  et  al.,  2023).  Furthermore, 
increased QSM values were associated with motor score (Uddin et al., 
2016),  cognitive  decline  (Uddin  et  al.,  2016,  Rolls  et  al.,  2020),  and 
differential expression of genes in the PD brain (Monsivais et al., 2023). 
Additionally, using R2* mapping MRI, Zang et al. reported an interaction 
of  increased  iron  deposition  in  the  SN  and  nigral-putamen  functional 
connectivity on glucose uptake in the putamen, uncovering an in vivo 
pathological  mechanism  of  nigrostriatal  neurodegeneration  of  PD 
(Lewis et al., 2013).

Previous  studies  have  demonstrated  aberrant  iron  accumulation 
across the brain in patients with PD (Postuma et al., 2015, Uddin et al., 
2016,  Rolls  et  al.,  2020,  Monsivais  et  al.,  2023,  Lewis  et  al.,  2013). 
However, these studies failed to report the probable sequences of iron 
accumulations across the brain with disease progression. Indeed, iron 
deposition  in  the  brain  of  patients  with  PD  may  be  related  to  the 
occurrence and development of PD by promoting apoptosis of neurons 
due to the iron-related oxidative reaction and neurotoxicity (Faucheux 
et  al.,  2003,  Barbosa  et  al.,  2015).  One  relevant  study  has  shown 
increased iron deposition in the SN pars compacta (SNpc) in the early 
stages PD, and progressive iron accumulation in the SN pars reticulata 
(SNpr) and pallidum in advanced stages of the disease (Ghassaban et al., 
2019). However, how the abnormal iron depositions in these regions are 
related  to  each  other  and  the  rest  of  the  brain  in  PD  has  not  been 
revealed.  Recently,  covariance  network  approaches,  including  causal 
covariance  network  and  individual  differential  covariance  network, 
have been applied to cross-sectional structural MRI data, revealing the 
ordering  of  brain  structural  changes  over  time  in  disorders  such  as 
schizophrenia (Jiang et al., 2018, Betts et al., 2016). In this study, it was 
hypothesized that PD was associated with a probable sequence of iron 
accumulation across the brain as the disease progressed. The concept of 
covariance  network  analysis  was  applied  to  the  R2*  mapping  data  to 
construct the relaxometry covariance network (RCN) for accessing the 
spatial distribution of iron and exploring the causal relationships of iron 
accumulation between brain regions.

2. Methods

2.1. Participants

This cross-sectional study was approved by the Ethics Committee of 
Xuanwu  Hospital,  Capital  Medical University, in  accordance  with the 
Declaration  of  Helsinki.  All  participants  provided  written  informed 
consent.  Participants  were  recruited  at  the  Department  of  Functional 
Neurosurgery, Xuanwu Hospital, Capital Medical University, based on 
the following inclusion criteria: (1) age between 40 and 75 years old, (2) 
right-handedness,  (3)  self-reported  absence  of  psychiatric  disorders, 
head trauma, and other conditions that may affect the brain, (4) no solid 
lesions  such  as  tumors  detected  in  the  brain  via  medical  imaging  ex-
amination, (5) self-reported absence of cerebrovascular diseases, (6) no 
current alcohol or drug abuse, (7) no MRI scan contraindications. PD 
was  diagnosed according  to the International Movement Disorder So-
ciety PD criteria (Milovic et al., 2022, Wu et al., 2014).

Fifty-nine participants, including 34 PD patients and 25 age- and sex- 
matched healthy controls (HCs), were finally enrolled. The Hoehn and 

2 

Yahr stage (HY stage), Unified Parkinson’s Disease Rating Scale-part III 
(UPDRS-III),  disease  duration  and  daily  dopaminergic  medication 
dosage were recorded for PD patients.

2.2. Magnetic resonance imaging data acquisition

All participants underwent MRI scans using a hybrid PET/MR scan-
ner (uPMR790, United Imaging, China)  with a 24-channel head/neck 
coil. PD patients were instructed to not take dopaminergic medication 
for  at  least  12  h  prior  to  the  scan.  A  three-dimensional  multi-echo 
gradient-echo  sequence  was  used  for  R2*  quantification  with  the 
◦
following parameters: flip angle = 15
, isotropic voxels with a voxel size 
of 1 × 1 × 1 mm3, repetition time (TR) = 29 ms, six echo times (TEs) =
3.1/6.4/9.7/13.0/16.3/19.6 ms, bandwidth = 500 Hz/px, acquisition 
matrix = 256 × 256, number of slices = 120, and monopolar readout 
gradients were used, with a total scan time of 5 min and 41 s. In addition, 
three-dimensional T1-weighted images were acquired with the following 
parameters: TR = 7.9 ms, TE = 3.8 ms, 176 sagittal slices, field of view =
256  × 256 mm2, and spatial resolution of 1 mm3.

2.3. R2* map calculation and processing

R2* maps were calculated from the multi-echo gradient-echo MRI 
data using the package on the vendor server. Specifically, the R2* maps 
were fit with an exponential decay using nonlinear least squares fitting, 
and were corrected for 3D linear susceptibility gradient removal (Wu 
and Hallett, 2013).

Subsequently,  the  voxel-wise  R2*  maps  were  normalized  into  the 
standard  Montreal  Neurological  Institute  (MNI)  space  with  the  assis-
tance of T1-weighted images via statistical parametric mapping 12 (SPM 
12,  https://www.fil.ion.ucl.ac.uk/spm/software/spm12/)  with  the 
following steps: The T1-weighted images of each participant were co- 
registered  to  the  R2*  maps  using  an  affine  transformation,  and  then 
the co-registered T1-weighted images were non-linearly normalized into 
the MNI template. Lastly, the deformation field was applied to the R2* 
maps.

2.4. Relaxometry covariance network approach

In this study, we used a novel RCN approach to evaluate the probable 
sequences of iron accumulation across the PD brain. The RCN approach 
included three main steps, as shown in Fig. 1.

2.4.1. Group-level relaxometry covariance network analysis

The normalized R2* maps were parcellated into 166 brain regions 
according to the automated anatomical labelling 3 (AAL3) atlas (Li et al., 
2023). Because the field of view of the R2* maps did not cover the whole 
cerebellum for some participants, we excluded 8 cerebellar subregions 
(bilateral  cerebellum  crus  II,  bilateral  cerebellum  area  7b,  bilateral 
cerebellum area 8, and bilateral cerebellum area 9), leaving 158 brain 
regions. Mean R2* values were extracted from the 158 brain regions for 
each participant. It is worth noting that the mean values may sometimes 
underestimate the iron accumulation level of brain regions, so we also 
used the median values for the subsequent RCN analysis, and the results 
were similar. Next, we constructed group-level RCNs based on the R2* 
values  from  each  PD  patient  or  HC  using  the  covariance  network 
approach (Fig. 1a). The group-level RCN was a 158 × 158 matrix, where 
each node represented a corresponding brain region, and the edges were 
the  Pearson  correlation  coefficients  of  the  R2*  values  between  paired 
brain regions across the PD or HC groups. Subsequently, we calculated 
the subtraction matrix (PD - HC), and we summed the values per column 
of  the  subtraction  matrix  to  estimate,  for  each  brain  region,  the 
covariance  differences  in  iron  accumulation  for  PD  compared  with 
controls, as demonstrated by Kim and Lee (2014). We could infer that a 
high sum of covariance differences for a brain region represented the 
ability  of  iron  accumulation  in  it  to  cause  covarying  changes  in  iron 

W. Lu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120943 

Fig. 1. The workflow of the proposed RCN approach. (a) Construction of group-level RCN for PD and control group to identify specific brain regions that do not only 
accumulate  iron,  but  also  propagate  iron  to  other  brain  regions  (propagators),  (b)  construction  of  causal  RCN  (CaRCN)  network,  (c)  construction  of  individual 
differential RCN (IDRCN).

accumulation for other brain regions, and vice versa.

Next,  two types  of  nodes,  including “silo”  and  “propagator,”  were 
defined according to a previous study (Kim and Lee, 2014). We defined a 
brain region  as a  “silo”  when  it (1) had  a significant  increase in iron 
accumulation in PD patients with respect to HCs (assessed by indepen-
dent t-test in iron levels between PD and HCs with a p value < 0.05), and 
(2) had a low covariance change (the average covariance changes with 
the rest of the nodes were less than 0.05 between the two groups). We 
defined a brain region as a “propagator”  when it (1) had a significant 
increase in iron accumulation in PD patients compared to HCs (assessed 
by independent t-test in iron levels between PD and HCs with a p value <
0.05), and (2) had a high covariance change (the average covariance 
changes with the rest of the brain regions were greater than or equal to 
0.05 between the two groups).

2.4.2. Causal relaxometry covariance network analysis

After the identification of propagators, we treated the propagators as 
regions of interest (ROIs). The R2* maps of all patients with PD were 
sequenced according to disease duration from short to long. If two pa-
tients had the same disease duration (expressed in years), we sequenced 
their  R2*  maps  according  to the  corresponding  HY stage  from low  to 
high. In this way, we constructed a pseudo-time series of R2* maps from 
all patients with PD, representing the pseudo disease trajectory.

To further investigate the causal relationships of iron accumulation 
from the ROIs to the rest of the brain, we performed ROI-wise causal 
relaxometry  covariance  network  (CaRCN)  analysis  using  the  REST 
software (version 1.27, http://rest.restfmri.net/) (Fig. 1b), which was 

similar to the causal structural covariance network approach described 
in a previous study (Jiang et al., 2018). In this analysis, the signed-path 
Granger coefficient (GC) was calculated between the pseudo-time series 
of  each  ROI  and  the  rest  of  the  brain  regions,  yielding  a  directed 
ROI-wise  causal  network.  Age  and  sex  were  regressed  as  nuisance 
covariates in the CaRCN analysis.

In other words, this study applied GC analysis to the cross-sectional 
data. Therefore, data sequence is essential, which gives a “time” prop-
erty to cross-sectional data. The CaRCN may reflect the iron accumu-
lation in an ROI that precedes and predicts the iron accumulation that 
occurs in other brain regions. Specifically, a positive GC value suggests 
that iron accumulation in another region lagged behind the iron accu-
mulation in the seed ROI, and vice versa. To present statistical signifi-
cance, the threshold was set at a GC value > 0.388, corresponding to p <
0.05.

2.4.3.

Individual differential relaxometry covariance network

To  extract  individual  features  from  the  RCN  for  PD  patients,  we 
constructed  individual  differential  RCN  for  each  PD  patient  using  a 
recently-proposed approach (as demonstrated in Fig. 1c) (Betts et al., 
2016).  Firstly,  we  used  the  group-level  RCN  of  HCs  as  the  reference 
network  (REF),  which  represented  the  common  iron  accumulation 
characteristics  of  healthy  subjects.  For  each  PD  patient,  he/she  was 
added to the control group, forming a new group with 26 participants. A 
new network was then constructed using R2* values from the 26 par-
ticipants,  which  was  called  the  perturbed  network  for  PD  (PN).  The 
difference  between  the  REF  and  PN  was  treated  as  the  individual 

3 

W. Lu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120943 

differential  relaxometry  covariance  network  (IDRCN)  for  the  corre-
sponding PD patient (Fig. 1c).

Previous  work  has  theoretically  confirmed  that  the  individual  dif-
ferential network follows a distribution similar to the normal distribu-
tion (Betts et al., 2016). Therefore, we z-scored the IDRCN of each PD 
patient according to following equation: 

Z =

(cid:0)

IDRCN
)/

1 (cid:0) REF2
n

(n (cid:0) 1)

(4) 

Where n is the number of HCs. Finally, we extracted the edge values 
with significant causal effects identified in the aforementioned CaRCN 
analysis for each propagator in patients with PD.

2.5. Statistical analysis

Statistical analysis was performed using R (version 4.0.4). Compar-
isons of continuous demographic variables between HCs and PD patients 
were  performed using two-sample  Student’s  t-test. Comparison of sex 
between  HCs  and  PD  patients  was  performed  using  chi-square  test. 
Pearson’s correlation analysis was performed between Z-score values of 
edges  with  significant  causal  effects  and  clinical  variables  (HY  stage, 
UPDRS III, and disease duration) in the PD group. Additionally, Pear-
son’s correlation analysis was also performed between mean R2* values 
(s-1)  of  nodes  that  received  significant  causal  projections  from  the 
propagators and clinical variables. P < 0.05 was considered statistically 
significant for all the aforementioned statistical analyses.

3. Results

3.1. Demographic and clinical information

This study enrolled 25 HCs and 34 patients with PD. As demonstrated 
in Table 1, the two groups were well-matched for age and sex (p > 0.05). 
In  addition,  HY  stage,  UPDRS-III,  disease  duration  and  dopaminergic 
medication information were available for the PD patients.

CaRCN analysis, and the corresponding results are provided in Fig. 4. 
Significantly positive causal projections were found from the left SNpr to 
the bilateral pallidum (GC = 0.485 for the projection from the left SNpr 
to left pallidum, GC = 0.490 for the projection from the left SNpr to right 
pallidum). Significantly causal projections were also observed from the 
left SNpc to the bilateral gyrus rectus (GC = 0.388 for the causal pro-
jection from the left SNpc to left gyrus rectus, GC = 0.506 for the causal 
projection from the left SNpc to right gyrus rectus), bilateral pallidum 
(GC = 0.744 for the left SNpc to left pallidum causal projection, GC =
0.487 for the left SNpc to right pallidum causal projection) and right 
middle  occipital  gyrus  (GC  = 0.416).  Meanwhile,  CaRCN  results 
demonstrated significantly positive causal projections from the VER7 to 
the bilateral gyrus rectus (GC = 0.525 for the projection from the VER7 
to left gyrus rectus, GC = 0.502 for the projection from the VER7 to right 
gyrus rectus), right medial orbitofrontal cortex (OFC) (GC = 0.649), and 
right anterior OFC (GC = 0.558). No negative GC from the propagators 
to other regions was observed.

3.4. Correlation analysis results

Then, the edges with statistically significant Granger causalities were 
extracted from the IDRCN of each patient with PD, and Pearson’s cor-
relation analysis was performed between the Z-score values of the edges 
and clinical variables. In addition, we also performed Pearson’s corre-
lation analysis between the mean R2* values of nodes receiving signif-
icant  causal  projections  from  the  propagators  (including  the  bilateral 
pallidum,  bilateral  gyrus  rectus,  right  middle  occipital  gyrus,  right 
medial OFC, and right anterior OFC) and clinical variables.

The correlation results are presented in Fig. 5. Disease duration was 
positively correlated with Z-scores of the connection between the VER7 
and left gyrus rectus (r = 0.355, p = 0.039), as well as the Z-scores of the 
connection between the VER7 and right anterior OFC (r = 0.500, p =
0.003). In addition, UPDRS-III score was positively correlated with the 
mean R2* values in the left gyrus rectus (r = 0.333, p = 0.050) and right 
gyrus rectus (r = 0.394, p = 0.021).

3.2. Silos and propagators of iron

4. Discussion

Comparison of RCN difference between the PD group and HC group 
revealed brain regions with distinctive patterns of iron accumulation in 
patients with PD compared to HCs, as illustrated in Fig. 2. In particular, 
three brain regions, including the left SNpr, left SNpc, and lobule VII of 
the cerebellum vermis (VER7), were found to have significantly higher 
iron accumulation and high covariance change, thus they were identi-
fied as propagators of iron. Additionally, three nodes were identified as 
silos that only accumulate iron, which were the right SNpc, right RN, 
and lobule VIII of cerebellum vermis (VER8), since they showed statis-
tically significant higher iron accumulation in the PD group with low 
covariance change (Fig. 3).

3.3. ROI-wise causality analysis results

The three nodes identified as propagators were used as ROIs in the 

Table 1 
Demographic and clinical information for PD and HC participants.

Age
Sex (F/M)
HY stage
UPDRS III
Disease Duration (years)
Medication uptake (mg/day)

HC 
(n = 25)

60.00 ± 4.55
17/8
–
–
–
–

PD 
(n = 34)

62.32 ± 6.40
21/13
3.00 ± 0.83
59.71 ± 15.00
9.59 ± 4.04
879.88 ± 432.81

P value

0.127
0.621
–
–
–
–

* Continuous variables are presented as mean ± standard deviation.
Abbreviations: n, number; F, female; M, male.

Using  a  novel  RCN  analysis  approach,  this  study  demonstrated 
probable  sequential  patterns  of  iron accumulation  in  the  brain of  pa-
tients with PD. Abnormal iron deposition was initially observed in the 
SNpr, SNpc, RN, and cerebellum vermis. The evaluated iron accumula-
tions in SNpr, SNpc, and VER7 were followed by iron deposition in the 
pallidum, gyrus rectus, and OFC. Additionally, the covariance connec-
tions of iron deposition between propagators and targeted brain regions 
were found to be strongly correlated with PD progression.

While the initial causes of PD are not clearly defined, iron deposition 
has been implicated in the pathogenesis of PD for a long time (Faucheux 
et  al.,  2003).  In  human  studies,  via  postmortem  measurements  or  by 
iron-sensitive MRI, researchers have found significantly increased iron 
levels in the SN of PD patients (Zhang et al., 2011). Additionally, pre-
vious MRI-based studies have demonstrated significantly increased iron 
levels in several brain regions in patients with PD, including the RN (Jin 
et al., 2011, Jiang et al., 2019, He et al., 2015), caudate nucleus (Zang 
et al., 2022, Thomas et al., 2021) and globus pallidus (Zang et al., 2022, 
Thomas  et  al.,  2021,  Biondetti  et  al.,  2021).  However,  the  results 
regarding iron levels observed via MRI were not consistent (Zhang et al., 
2011),  which  might  be  due  to  the  sequential  iron  accumulation  at 
different stages of PD. In addition, the relationships of iron accumula-
tions among these brain regions remained largely unclear.

Covariance  network  approaches,  including  causal  covariance 
network  and  individual  differential  covariance  network,  have  been 
applied  to  structural  MRI  data,  revealing  the  probable  ordering  of 
structural changes in the brain in several disorders (Jiang et al., 2018, 
Betts et al., 2016). In the present study, we utilized covariance network 
approaches to the R2* mapping MRI data to investigate the pattern and 

4 

W. Lu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120943 

Fig. 2. Propagators and silos of iron in the brain of patients with PD. (a) Quadrant plot representing T-values on the horizontal axis and sum of covariance change 
(COV change) on the vertical axis. Brain regions above T = 2.00 (red vertical dashed line) represent those with excessive iron accumulation. Brain regions above COV 
change = 9.23 (red horizontal dashed line) represents those with high covariance change with respect to the rest brain regions. (b) The 3 propagators and 3 silos laid 
on the R2* maps (s-1) show the corresponding locations.
Abbreviations: L, left; R, right, RN, red nucleus; SNpr, substantia nigra pars reticulata; SNpc, substantia nigra pars compacta; VER7, lobule VII of cerebellum vermis; 
VER8, lobule VIII of cerebellum vermis.

Fig. 3. Box plots of comparisons in iron levels between PD group and control group for the propagators and silos. R2* values (s-1) are used to represent iron levels. * 
represents p < 0.05, ** represents p < 0.001.
Abbreviations: L, left; R, right, RN, red nucleus; SNpr, substantia nigra pars reticulata; SNpc, substantia nigra pars compacta; VER7, lobule VII of cerebellum vermis; 
VER8, lobule VIII of cerebellum vermis.

probable sequences of brain iron accumulation in PD. Both R2* mapping 
and QSM can be used to evaluate the level of iron accumulation in the 
PD brain (Postuma et al., 2015, Uddin et al., 2016, Rolls et al., 2020, 
Monsivais  et  al.,  2023,  Lewis  et  al.,  2013).  Compared  to  QSM,  R2* 
mapping is a simpler approach to assess brain iron accumulation levels 
(Hett et al., 2021). However, the measurement results of QSM may be 
affected  by  imaging  parameters  and  post-processing  methods,  and 
further validation is needed (Wang and Liu, 2015). Additionally, QSM 
faces challenges in establishing the reference values necessary for ab-
solute  quantification  (Tremblay  et  al.,  2019).  Furthermore,  artifacts 
such as streaking artifacts may occur in QSM, which could skew the final 
results  (Martin  et  al.,  2019).  Therefore,  R2*  mapping  may  be  a  more 
robust measure for studying iron accumulation in PD.

Via the novel RCN approach on R2* maps by Monsivais et al. (Kim 
and  Lee,  2014),  we  have  revealed  the  sequential  iron  accumulation 
patterns in patients with PD. Specifically, the left SNpr, left SNpc and 
VER7  may  be  involved  in  brain  iron  dynamics  by  accumulating  and 
propagating iron to other regions. In contrast, the right SNpc, right RN 
and VER8 may only act as deposition sites of iron. In addition, distinc-
tive patterns of iron accumulation were found between the left and right 
SN, which might be due to cortical asymmetry, since a previous study 
has reported that the left nigrostriatal system appears more susceptible 
to early degeneration than its counterpart in PD (Claassen et al., 2016).
The significantly elevated iron levels in the SN and RN of patients 
with PD were well supported by previous findings (Zhang et al., 2011, 
Postuma et al., 2015, Uddin et al., 2016, Rolls et al., 2020, Monsivais 

5 

W. Lu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120943 

Fig. 4. ROI-wise CaRCN results by bivariate signed-path coefficient GC analysis showing causal relationship of progressive iron accumulation in patients with PD. 
Causal projections from the (a) left SNpr, (b) SNpc and (c) VER7. The colors of the directed connections represent corresponding GC values.
Abbreviations: L, left; R, right, SNpr, substantia nigra pars reticulata; SNpc, substantia nigra pars compacta; VER7, lobule VII of cerebellum vermis; MOG, middle 
occipital gyrus; OFCmed, medial orbitofrontal cortex; OFCant, anterior orbitofrontal cortex.

et al., 2023, Jin et al., 2011, Jiang et al., 2019, He et al., 2015). How-
ever, the cerebellum has often been overlooked in PD research. Recent 
studies  have  revealed  that  structural  and  functional  changes  in  the 
cerebellum  are  related  to  tremor,  akinesia/rigidity,  and  non-motor 
symptoms of PD (Weil et al., 2016, Wen et al., 2022). Consistent with 
the current findings, previous studies have revealed abnormal functional 
connectivity within the VER7 and VER8 in PD (Wen et al., 2022, Chen 
et  al.,  2023).  The  structural  and  functional  changes  in  the  VER7  and 
VER8 are associated with the motor and non-motor symptoms of PD, as 
studies  have  shown  that  the  abnormalities  in  these  regions  may  be 
involved in the gait impairments and visuospatial disorders of PD (Wen 
et al., 2022, Li et al., 2020), and can be used to differentiate PD from 
essential tremor (Li et al., 2020, Maiti et al., 2020). Moreover, a previous 
study  has  shown  significantly  increased  iron  levels  in  the  cerebellar 
dentate nuclei associated with severe tremors in PD patients (He et al., 

2017). The elevated iron levels in the VER7 and VER8 in the current 
study may support these previous findings.

This study further demonstrated that iron accumulation in the SNpr 
exhibited positive causal effects on the pallidum, and iron accumulation 
in  the  SNpc  showed  causal  effects  on  the  pallidum,  gyrus  rectus  and 
middle  occipital  gyrus.  Additionally,  the  VER7  demonstrated  positive 
causal projections to the gyrus rectus and OFC. These findings suggest 
that the iron accumulation in the pallidum and cortical regions may be 
driven by the aberrant iron accumulation in the SNpr, SNpc and VER7. 
The SNpr and pallidum are both part of the motor circuit according to 
the  parallel  circuit  model  of  the  basal  ganglia  in  PD  (McGregor  and 
Nelson, 2019). Furthermore, in the PD brain, SNpr sends dopaminergic 
projections to the subthalamic nucleus, internal and external segments 
of  globus  pallidus,  and  the  striatum  (Parent  and  Parent,  2010).  The 
causal  projections  of  iron  accumulation  from  the  SN  to  the  pallidum 

6 

W. Lu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120943 

Fig. 5. Correlation analysis results showing significant associations between edge values, mean R2* values of nodes and clinical variables in PD group. Scatter plot 
between (a) disease duration and VER7-left gyrus rectus covariance connection (Z-score), (b) disease duration and VER7-right anterior OFC covariance connection (Z- 
score), (c) UPDRS-III score and mean R2* value (s-1) in the left gyrus rectus, (d) UPDRS-III score and mean R2* value (s-1) in the right gyrus rectus.

provide insights into the ordering of the iron accumulation along the 
motor circuit, which may be related to the pathophysiological aspect of 
PD. The gyrus rectus within the prefrontal cortex is the main projection 
target of midbrain dopaminergic neurons located in the SN (Islam et al., 
2021). The SN and its projection fields are also innervated by seroto-
nergic neurons (Taracha, 2021). In addition, the neural circuit involving 
the  prefrontal  cortex  and  SN  have  been  implicated  in  the  depression 
symptoms in PD (Zhang et al., 2022). These findings may offer possible 
explanations  for  the  significant  causal  projections  from  SNpc  to  the 
gyrus rectus.

A recent study demonstrated the interaction between excessive iron 
deposition in the SN and visual network in the PD brain (Lingor et al., 
2017),  which  was  consistent  with  the  current  findings  of  causal  pro-
jections  of  iron  accumulation  from  the  SNpc  to  the  middle  occipital 
gyrus. Patients with PD often experience various specific visual distur-
bances  (Dawson  and  Dawson,  2003),  which  might  be  related  to  the 
causal  projections  from  the  SNpc  to  the  middle  occipital  gyrus.  The 
current findings also showed causal projections from the VER7 to the 
gyrus rectus and OFC associated with disease duration. Previous studies 
have revealed that the cerebellar vermis and frontal cortex circuit are 
involved in the motor imagery and execution of postural balance in PD 
(Mori et al., 2020, Wang et al., 2016). The cerebellum vermis also plays 
a critical role in modulating large-scale synchronization of neural net-
works in the non-motor frontal cortex (Madhusoodhanan et al., 2019). 
In  line  with  these  findings,  the  significant  projections  from  the  cere-
bellum vermis to the frontal cortex may be related to the pathophysio-
logical changes of PD, which warrants further investigation.

There  are  several  limitations  in  the  current  study  that  need  to  be 
addressed. First, the small sample size may introduce errors in spatial 
normalization  and  limit  the  generalization  ability  of  the  findings. 

Second, this study constructed RCN based on R2* maps. However, R2* 
mapping  is  susceptible  to  vascular  blooming  artifacts  caused  by  non- 
local effects (Li et al., 2015), which may affect the accuracy and reli-
ability of R2* mapping (Tremblay et al., 2019, Li et al., 2015). QSM can 
better  characterize  the  magnetic  susceptibility  distribution  of  tissues, 
thereby  reducing  the  artifacts  caused  by  non-local  effects  (Mochizuki 
et al., 2020). So, RCN analysis based on QSM may be a promising choice 
in the future. Third, the pseudo-time series based on disease duration 
may not accurately reflect the real-time sequence of disease progression. 
Furthermore, the causal projections from the CaRCN analysis only rep-
resented  the  causal  relationships  of  iron  accumulation  between  brain 
regions, and the association between these causal projections and iron 
transport pathways requires further investigation. Therefore, the current 
CaRCN  results  should  be  interpreted  with  caution.  Fourth,  idiopathic 
rapid eye movement sleep behavior disorder, a prodromal symptom of 
PD, has also been linked to aberrant brain iron accumulation (Alushaj 
et al., 2023, Zhang et al., 2021). Future research should expand to the 
prodromal  stage  of  PD  to  investigate  the  dynamic  pattern  of  iron 
deposition throughout the entire course of the disease.

In  conclusion,  using  a  novel  relaxometry  covariance  network 
approach, we have revealed the probable sequences of iron accumula-
tion in patients with PD. Three primary hubs, including the SNpr, SNpc 
and VER7, appeared to act as propagators of iron to the rest of the brain 
regions.  We  further  showed  that  iron  accumulation  in  the  SNpr  was 
followed by accumulation in the pallidum. Additionally, iron accumu-
lation in the pallidum, gyrus rectus, and middle occipital gyrus may be 
driven by iron accumulation in the SNpc. Meanwhile, iron accumulation 
in the VER7 proceeded iron accumulations in the gyrus rectus and OFC. 
The current findings imply the spatial pattern and probable temporal 
sequences of brain iron accumulation in PD, and suggest future research 

7 

W. Lu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120943 

directions  to  further  explore  the  underlying  mechanisms  of  iron  dy-
namics in patients with PD.

Ethics statement

This cross-sectional study was approved by the Ethics Committee of 
Xuanwu  Hospital  Capital  Medical  University  in  accordance  with  the 
Declaration  of  Helsinki.  All  participants  provided  written  informed 
consent.

Data sharing statement

Data  and  further  materials  of  this  study  is  available  from  corre-
sponding authors upon reasonable request with the need for approval 
from the requesting researcher’s local ethics committee.

Funding sources

This study was supported by the National Key Research and Devel-
2022YFC2406900,  No. 

of  China 

(No. 

opment 
Program 
2022YFC2406904).

CRediT authorship contribution statement

Weizhao Lu: Writing – original draft, Visualization, Formal analysis. 
Tianbin Song: Resources, Data curation. Zhenxiang Zang: Validation, 
Supervision,  Methodology.  Jiping  Li:  Resources.  Yuqing  Zhang:  Re-
sources.  Jie  Lu:  Writing  –  review  &  editing,  Supervision,  Project 
administration.

Declaration of competing interest

The authors declare no potential conflicts of interest.

Data availability

Data will be made available on request. 

References

Alushaj, E., Hemachandra, D., Kuurstra, A., et al., 2023. Subregional analysis of striatum 
iron in Parkinson’s disease and rapid eye movement sleep behaviour disorder. 
Neuroimage Clin. 40, 103519.

Barbosa, J.H., Santos, A.C., Tumas, V., Liu, M., Zheng, W., Haacke, E.M., Salmon, C.E., 
2015. Quantifying brain iron deposition in patients with Parkinson’s disease using 
quantitative susceptibility mapping, R2 and R2. Magn. Reson. ImAging 33, 559–565.

Beitz, J.M., 2014. Parkinson’s disease: a review. Front. Biosci. 6, 65–74.
Betts, M.J., Acosta-Cabronero, J., Cardenas-Blanco, A., Nestor, P.J., Düzel, E., 2016. 

High-resolution characterisation of the aging brain using simultaneous quantitative 
susceptibility mapping (QSM) and R2* measurements at 7T. Neuroimage 138, 
43–63.

Biondetti, E., Santin, M.D., Valabr`egue, R., et al., 2021. The spatiotemporal changes in 
dopamine, neuromelanin and iron characterizing Parkinson’s disease. Brain 144, 
3114–3125.

Chen, Z., He, C., Zhang, P., et al., 2023. Abnormal cerebellum connectivity patterns 

related to motor subtypes of Parkinson’s disease. J. Neural Transm. 130, 549–560.

Claassen, D.O., McDonell, K.E., Donahue, M., et al., 2016. Cortical asymmetry in 

Parkinson’s disease: early susceptibility of the left hemisphere. Brain Behav. 6, 
e00573.

Dawson, T.M., Dawson, V.L, 2003. Molecular pathways of neurodegeneration in 

Parkinson’s disease. Science 302, 819–822.

Du, G., Wang, E., Sica, C., et al., 2022. Dynamics of Nigral Iron Accumulation in 

Parkinson’s Disease: from Diagnosis to Late Stage. Mov. Disord. 37, 1654–1662.

Faucheux, B.A., Martin, M.E., Beaumont, C., Hauw, J.J., Agid, Y., Hirsch, E.C., 2003. 
Neuromelanin associated redox-active iron is increased in the substantia nigra of 
patients with Parkinson’s disease. J. Neurochem. 86, 1142–1148.

Ghassaban, K., Liu, S., Jiang, C., Haacke, E.M., 2019. Quantifying iron content in 

magnetic resonance imaging. Neuroimage 187, 77–92.

Guan, X., Guo, T., Zhou, C., et al., 2022. Altered brain iron depositions from aging to 
Parkinson’s disease and Alzheimer’s disease: a quantitative susceptibility mapping 
study. Neuroimage 264, 119683.

He, N., Huang, P., Ling, H., et al., 2017. Dentate nucleus iron deposition is a potential 
biomarker for tremor-dominant Parkinson’s disease. NMR Biomed. 30, e3554.

8 

He, N., Ling, H., Ding, B., et al., 2015. Region-specific disturbed iron distribution in early 
idiopathic Parkinson’s disease measured by quantitative susceptibility mapping. 
Hum. Brain Mapp. 36, 4407–4420.

Hett, K., Lyu, I., Trujillo, P., et al., 2021. Anatomical texture patterns identify cerebellar 
distinctions between essential tremor and Parkinson’s disease. Hum. Brain Mapp. 42, 
2322–2331.

Islam, K.U.S., Meli, N., Blaess, S., 2021. The Development of the Mesoprefrontal 

Dopaminergic System in Health and Disease. Front. Neural Circuits. 15, 746582.
Jiang, H., Song, N., Jiao, Q., Shi, L., Du, X, 2019. Iron Pathophysiology in Parkinson 

Diseases. Adv. Exp. Med. Biol. 1173, 45–66.

Jiang, Y., Luo, C., Li, X., et al., 2018. Progressive Reduction in Gray Matter in Patients 
with Schizophrenia Assessed with MR Imaging by Using Causal Network Analysis. 
Radiology. 287, 633–642.

Jin, L., Wang, J., Zhao, L., et al., 2011. Decreased serum ceruloplasmin levels 

characteristically aggravate nigral iron deposition in Parkinson’s disease. Brain 134, 
50–58.

Kalia, L.V., Lang, A.E., 2015. Parkinson’s disease. Lancet 386, 896–912.
Kim, T.H., Lee, J.H, 2014. Serum uric acid and nigral iron deposition in Parkinson’s 

disease: a pilot study. PLoS. One 9, e112512.

Leh´ericy, S., Roze, E., Goizet, C., Mochel, F, 2020. MRI of neurodegeneration with brain 

iron accumulation. Curr. Opin. Neurol. 33, 462–473.

Lewis, M.M., Du, G., Kidacki, M., Patel, N., Shaffer, M.L., Mailman, R.B., Huang, X., 

2013. Higher iron in the red nucleus marks Parkinson’s dyskinesia. Neurobiol. Aging 
34, 1497–1503.

Li, J., Jin, M., Wang, L., Qin, B., Wang, K, 2017. MDS clinical diagnostic criteria for 

Parkinson’s disease in China. J. Neurol. 264, 476–481.

Li, S.J., Ren, Y.D., Li, J., Cao, B., Ma, C., Qin, S.S., XR, Li, 2020. The role of iron in 
Parkinson’s disease monkeys assessed by susceptibility weighted imaging and 
inductively coupled plasma mass spectrometry. Life Sci. 240, 117091.

Li, T., Le, W., Jankovic, J., 2023. Linking the cerebellum to Parkinson disease: an update. 

Nat. Rev. Neurol. 19, 645–654.

Li, W., Wang, N., Yu, F., et al., 2015. A method for estimating and removing streaking 

artifacts in quantitative susceptibility mapping. Neuroimage 108, 111–122.

Lingor, P., Carboni, E., Koch, J.C, 2017. Alpha-synuclein and iron: two keys unlocking 

Parkinson’s disease. J. Neural Transm. 124, 973–981.

Liu, Z., Palaniyappan, L., Wu, X., et al., 2021. Resolving heterogeneity in schizophrenia 
through a novel systems approach to brain structure: individualized structural 
covariance network analysis. Mol. Psychiatry 26, 7719–7731.

Madhusoodhanan, S., Kesavadas, C., Paul, J.S, 2019. SWI processing using a local phase 

difference modulated venous enhancement filter with noise compensation. Magn. 
Reson. ImAging 59, 17–30.

Maiti, B., Koller, J.M., Snyder, A.Z., et al., 2020. Cognitive correlates of cerebellar 
resting-state functional connectivity in Parkinson disease. Neurology. 94, 
e384–e396.

Martin, J.A., Zimmermann, N., Scheef, L., et al., 2019. Disentangling motor planning and 
motor execution in unmedicated de novo Parkinson’s disease patients: an fMRI 
study. Neuroimage Clin. 22, 101784.

McGregor, M.M., Nelson, A.B., 2019. Circuit Mechanisms of Parkinson’s Disease. Neuron 

101, 1042–1056.

Milovic, C., Lambert, M., Langkammer, C., Bredies, K., Irarrazaval, P., Tejos, C., 2022. 
Streaking artifact suppression of quantitative susceptibility mapping reconstructions 
via L1-norm data fidelity optimization (L1-QSM). Magn. Reson. Med. 87, 457–473.

Mochizuki, H., Choong, C.J., Baba, K., 2020. Parkinson’s disease and iron. J. Neural 

Transm. 127, 181–187.

Monsivais, H., Goni, J., Dydak, U., 2023. A Network Based Approach to Identify Key 
Brain Regions Involved in Storing and Propagating Manganese to Other Brain 
Regions Using MRI. Med. Phys. 50, e126.

Mori, Y., Yoshikawa, E., Futatsubashi, M., Ouchi, Y, 2020. Neural correlates of standing 
imagery and execution in Parkinsonian patients: the relevance to striatal dopamine 
dysfunction. PLoS. One 15, e0240998.

Ou, Z., Pan, J., Tang, S., Duan, D., Yu, D., Nong, H., Wang, Z, 2021. Global Trends in the 
Incidence, Prevalence, and Years Lived With Disability of Parkinson’s Disease in 204 
Countries/Territories From 1990 to 2019. Front. Public Health 9, 776847.

Parent, M., Parent, A., 2010. Substantia nigra and Parkinson’s disease: a brief history of 

their long and intimate relationship. Can. J. Neurol. Sci. 37, 313–319.

Postuma, R.B., Berg, D., Stern, M., et al., 2015. MDS clinical diagnostic criteria for 

Parkinson’s disease. Mov. Disord. 30, 1591–1601.

Rolls, E.T., Huang, C.C., Lin, C.P., Feng, J., Joliot, M., 2020. Automated anatomical 

labelling atlas 3. Neuroimage 206, 116189.

Schapira, A.H., Jenner, P., 2011. Etiology and pathogenesis of Parkinson’s disease. Mov. 

Disord. 26, 1049–1055.

Shi, L., Huang, C., Luo, Q., et al., 2019. The Association of Iron and the Pathologies of 
Parkinson’s Diseases in MPTP/MPP+-Induced Neuronal Degeneration in Non- 
human Primates and in Cell Culture. Front. Aging Neurosci. 11, 215.

Taracha, E., 2021. The role of serotoninergic system in psychostimulant effects. Postep. 

Psychiatr. Neurol. 30, 258–269.

Thomas, G.E.C., Leyland, L.A., Schrag, A.E., Lees, A.J., Acosta-Cabronero, J., Weil, R.S, 
2020. Brain iron deposition is linked with cognitive severity in Parkinson’s disease. 
J. Neurol. Neurosurg. Psychiatry 91, 418–425.

Thomas, G.E.C., Zarkali, A., Ryten, M., et al., 2021. Regional brain iron and gene 

expression provide insights into neurodegeneration in Parkinson’s disease. Brain 
144, 1787–1798.

Tremblay, S.A., Chapman, C.A., Courtemanche, R., 2019. State-Dependent Entrainment 
of Prefrontal Cortex Local Field Potential Activity Following Patterned Stimulation 
of the Cerebellar Vermis. Front. Syst. Neurosci. 13, 60.

W. Lu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120943 

Uddin, M.N., Lebel, R.M., Wilman, A.H., 2016. Value of transverse relaxometry 

difference methods for iron in human brain. Magn. Reson. ImAging 34 (1), 51–59.
Wang, J.Y., Zhuang, Q.Q., Zhu, L.B., et al., 2016. Meta-analysis of brain iron levels of 

Parkinson’s disease patients determined by postmortem and MRI measurements. Sci. 
Rep. 6, 36669.

Wang, Y., Liu, T., 2015. Quantitative susceptibility mapping (QSM): decoding MRI data 

for a tissue magnetic biomarker. Magn. Reson. Med. 73, 82–101.

Weil, R.S., Schrag, A.E., Warren, J.D., Crutch, S.J., Lees, A.J., Morris, H.R, 2016. Visual 

dysfunction in Parkinson’s disease. Brain 139, 2827–2843.

Wen, J., Guo, T., Wu, J., et al., 2022. Nigral Iron Deposition Influences Disease Severity 
by Modulating the Effect of Parkinson’s Disease on Brain Networks. J. Parkinsons. 
Dis. 12, 2479–2492.

Wu, S.F., Zhu, Z.F., Kong, Y., Zhang, H.P., Zhou, G.Q., Jiang, Q.T., Meng, X.P, 2014. 

Assessment of cerebral iron content in patients with Parkinson’s disease by the 
susceptibility-weighted MRI. Eur. Rev. Med. Pharmacol. Sci. 18, 2605–2608.

Wu, T., Hallett, M., 2013. The cerebellum in Parkinson’s disease. Brain 136, 696–709.
Zang, Z., Song, T., Li, J., et al., 2022. Modulation effect of substantia nigra iron 

deposition and functional connectivity on putamen glucose metabolism in 
Parkinson’s disease. Hum. Brain Mapp. 43, 3735–3744.

Zhang, J., Xue, B., Jing, B., et al., 2022. LPS activates neuroinflammatory pathways to 
induce depression in Parkinson’s disease-like condition. Front. Pharmacol. 13, 
961817.

Zhang, W., Phillips, K., Wielgus, A.R., et al., 2011. Neuromelanin activates microglia and 
induces degeneration of dopaminergic neurons: implications for progression of 
Parkinson’s disease. Neurotox. Res. 19, 63–72.

Zhang, X., Chai, C., Ghassaban, K., et al., 2021. Assessing brain iron and volume of 

subcortical nuclei in idiopathic rapid eye movement sleep behavior disorder. Sleep. 
44, zsab131.

9 

