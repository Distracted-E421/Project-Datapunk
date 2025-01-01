NeuroImage 303 (2024) 120896 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Investigating the impact of the regularization parameter on EEG 
resting-state source reconstruction and functional connectivity using real 
and simulated data

F. Leone a,b,*, A. Caporali c,d, A. Pascarella e, C. Perciballi a,b, O. Maddaluno a,b, A. Basti g,  
P. Belardinelli f, L. Marzetti g,h, G. Di Lorenzo b,i, V. Betti a,b,*
a Department of Psychology, Sapienza University of Rome, via dei Marsi 78, Rome, 00185, Italy
b IRCCS Fondazione Santa Lucia, via Ardeatina, 354, Rome, 00179, Italy
c Faculty of Veterinary Medicine, University of Teramo, via R. Balzarini 1, Teramo, 64100, Italy,
d International School of Advanced Studies, University of Camerino, via Gentile III Da Varano, Camerino, 62032, Italy
e Institute for Computational Applications, CNR, Italy
f CIMeC, Center for Mind/Brain Sciences, University of Trento, via delle Regole, 101, Mattarello-Trento, 38123, Italy
g Department of Neuroscience, Imaging and Clinical Sciences, “G. d’Annunzio” University of Chieti-Pescara, via dei Vestini, Chieti, 66100, Italy
h Institute for Advanced Biomedical Technologies, “G. d’Annunzio” University of Chieti-Pescara, via Luigi Polacchi, Chieti, 66100, Italy
i Laboratory of Psychophysiology and Cognitive Neuroscience, University of Rome Tor Vergata, Rome, Italy

A R T I C L E  I N F O

A B S T R A C T

Keywords:
EEG
Resting-state
Regularization parameter
Source reconstruction
Minimum Norm Estimation
Functional connectivity

Accurate EEG source localization is crucial for mapping resting-state network dynamics and it plays a key role in 
estimating  source-level  functional  connectivity.  However,  EEG  source  estimation  techniques  encounter 
numerous  methodological  challenges,  with  a  key  one  being  the  selection  of  the  regularization  parameter  in 
minimum norm estimation. This choice is particularly intricate because the optimal amount of regularization for 
EEG source estimation may not align with the requirements of EEG connectivity

analysis, highlighting a nuanced trade-off. In this study, we employed a methodological approach to determine 
the optimal regularization coefficient that yields the most effective reconstruction outcomes across all simula-
tions involving varying signal-to-noise ratios for synthetic EEG signals. To this aim, we considered three resting 
state networks: the Motor Network, the Visual Network, and the Dorsal Attention Network. The performance was 
assessed  using  three  metrics,  at  different  regularization  parameters:  the  Region  Localization  Error,  source 
extension, and source fragmentation. The results were validated using real functional connectivity data. We show 
(cid:0) 1  has to be preferred when 
that the best estimate of functional connectivity is obtained using 10
source localization only is at target.

(cid:0) 2, while 10

1. Introduction

Spontaneous  brain  activity,  i.e.,  without  any  external  stimulus  or 
task,  is  far  from  random  noise.  Rather,  it  is  temporally  and  spatially 
organized into coherent regions of similar functionality that resemble 
those observed during the execution of cognitive, motor, and visual tasks 
(Smith et al., 2009). Most studies have used functional magnetic reso-
nance  imaging  (fMRI)  to  measure  temporal  correlation  (functional 
connectivity - FC) between blood- oxygenation-level-dependent (BOLD) 
signals  from  different  brain  areas.  These  studies  identified  several 
resting-state  networks  (RSNs),  highly  reproducible  across  subjects 

(Biswal et al., 1995; Raichle et al., 2001; Fox et al., 2005). However, 
fMRI has a low temporal resolution. Moreover, the BOLD signal is only 
an  indirect  measure  of  the  neural  sources  related  to  hemodynamics. 
Non-invasive  electrophysiological  imaging  techniques,  i.e.,  electroen-
cephalography  (EEG)  and  magnetoencephalography  (MEG),  have  an 
excellent temporal resolution on the scale of milliseconds. Using MEG 
(de Pasquale et al., 2010, 2012; Brookes et al., 2011; Hipp et al., 2012; 
Marzetti et al., 2013; Betti et al., 2013; V. 2018) and high-density EEG 
(Siems et al., 2016; Sockeel et al., 2016; Knyazev et al., 2016; Liu et al., 
2017; Q. 2018) similar RSNs were uncovered.

Researchers  investigated  connectivity  in  source  space  rather  than 

* Corresponding authors.

E-mail addresses: f.leone@uniroma1.it (F. Leone), vi-viana.betti@uniroma1.it (V. Betti). 

https://doi.org/10.1016/j.neuroimage.2024.120896
Received 15 May 2024; Received in revised form 4 October 2024; Accepted 18 October 2024  
Available online 8 November 2024 
1053-8119/© 2024 The Authors. Published by Elsevier Inc. This is an open access article under the CC BY-NC-ND license ( http://creativecommons.org/licenses/by- 
nc-nd/4.0/ ). 

F. Leone et al.                                                                                                                                                                                                                                   

NeuroImage 303 (2024) 120896 

sensor  space  to  address  inaccuracies  and  ambiguities  stemming  from 
volume conduction spread. This type of analysis can help mitigate these 
issues (Schoffelen and Gross, 2009). This analysis strategy implies esti-
mating  the  underlying  current  sources,  a  commonly  encountered 
ill-posed  problem  where  numerous  source  configurations  can  equally 
account for the data. Moreover, the inverse problem is not continuously 
dependent on the data due to small perturbations from noise leading to 
large variations in the solution (Grech et al., 2008). Using a regulari-
zation  method  is  a  classic  mathematical  approach  to  address  the 
ill-posed  nature  of  inverse  problems,  as  it  reintroduces  solution 
uniqueness  by  incorporating  prior  information  (Hanke  and  Hansen, 
1993; Baillet et al., 2001; Grech et al., 2008; Sorrentino and Piana, 2017; 
Ilmoniemi and Sarvas, 2019). Different a-priori information/constraints 
depend on different inverse methods, yielding diverse source estimates. 
Minimum Norm Estimation (MNE) is a widely used method in which the 
solution is obtained by looking for a source distribution with minimum 
energy that best fits the data (Lin et al., 2004; Ramírez et al., 2011). The 
regularization parameter λ that tunes the balance between the solution 
accuracy  and  its  numerical  stability  can  be  determined  by  using  an 
inversely  proportional  relationship  with  the  Signal-To-Noise  Ratio 
(SNR) (Lin et al., 2004; Ramírez et al., 2011). In task-evoked studies, the 
typically defined SNR value is set to 3 (Baillet et al., 2001). However, 
this value, a default parameter in Brainstorm (Tadel et al., 2011) and 
MNE-python  (Gramfort  et  al.,  2013),  is  not  necessarily  suited  for 
studying the connectivity at rest.

The optimal selection of the regularization parameter is still debated, 
with increasing interest in studying its impact on functional connectivity 
(Vallarino et al., 2021, 2023). Moreover, most existing studies employed 
MEG and there remains a lack of methodological EEG investigations in 
this domain. In this technical note, we aim at determining the optimal λ 
value for source-space connectivity detection at rest in a minimum-norm 
source estimation setting with a realistic head model.

To  do  so,  we  simulated  synthetic  resting-state  EEG  signals  with 
different  known  SNRs.  Three  different  metrics  were  introduced  to 
evaluate the solution of the inverse problem: i) the region localization 
error,  ii)  the  spatial  dispersion,  and  iii)  the  source  fragmentation. 
Finally, the source reconstruction results were employed for real data 
functional connectivity estimation. The ultimate goal of this work is to 
obtain an optimal regularization parameter based on quantitative met-
rics that encompass several key factors for source and functional con-
nectivity estimations. With respect to the state of the art, determining 
the appropriate values for these parameters is not straightforward. For 
this  reason,  our  study  aims  to  introduce  a  standardized  protocol  to 
ensure the reproducibility of both the simulated and real data results. 
Additionally,  a  proper  evaluation  of  source  estimation  techniques  is 
necessary to use functional connectivity as a reliable research tool and 
mitigate the subjectivity involved in the analysis process.

2. Materials and methods

2.1. Generation of synthetic EEG signal in resting-state networks

The head and sensor models used to generate the EEG signal were 
based on the New York Head model1 (Huang et al., 2016). It contains: i) 
a segmentation of the ICBM-152 template head (De Leener et al., 2018) 
into six different tissue types (i.e. skin, skull, cerebrospinal fluid, grey 
matter, white matter, and air cavities); ii) a triangulated cortical mesh 
with  74.382  vertices;  iii)  labels  and  locations  of  231  EEG  scalp  elec-
trodes defined in accordance with the 10–5 electrode system.

We  computed  a  three-layer  boundary-element  method  (BEM) 
(Oosten- dorp and Van Oosterom, 1989) volume conductor model of the 
head based on the geometry and the electrical propriety of the New York 
Head, considering the following conductivity values: 0.3, 0.004 and 0.3 

1 Available on www.parralab.org/nyhead.

2 

S/m for brain, skull, and scalp, respectively. We then used a uniform 
subsample of 10.016 nodes of the New York Head cortical mesh for the 
source space. Finally, we considered 228 electrodes out of 231 (3 elec-
trodes around the base of the neck were removed) as sensor space. Using 
these models, we computed the lead-field matrix L, with source orien-
tations normal to the local cortical surface, using the Dipoli BEM method 
integrated  into  the  Fieldtrip  toolbox  (Oostenveld  et  al.,  2011).  This 
matrix was used for the generation of the EEG signal, as in (Basti et al., 
2022).

Specific  generation  parameters  were  selected  for  the  EEG  data 
simulation, including source position (refer to Table 1), adjacency ma-
trix,  time delay,  sampling  frequency,  length  of  time series,  frequency 
band, number of brain noise point-like sources, and SNR, divided into 
signal-to-brain-noise ratio

(SBNR) and signal-to-sensor-noise ratio (SSNR). The locations of the 
simulated sources were set to that of the nodes of three different RSNs, 
which were considered for their functional and clinical relevance: the 
Motor Network (MN), which provides information about motor control 
and  motor  task  activities;  the  Visual  Network  (VIS)  about  visual 
perception; and the Dorsal Attention Network (DAN) about the spatial 
attention. It has been shown that there is a hierarchical functional or-
ganization between RSNs (Doucet et al., 2011; Fox et al., 2005). This 
hierarchy can be found in the selected RSNs, since the VIS is represen-
tative of the lowest functional level, the MN of a higher level than VIS, 
and  the  DAN  can  be  considered  the  highest  functional  level.  Every 
point-like  source  within  each  considered  RSN  was  coupled  to  one 
another source belonging to the same RSN. Each network was simulated 
separately from the others. Source locations for the different nodes in 
each RSN are listed in Table 1.

For each RSN, the simulated EEG signal was 1 min long and sampled 
at 256 Hz. It was generated from synthetic source time courses, using 
non-linear dipolar coupled sources and 50 uncorrelated noise sources, 
randomly distributed over the whole cortex. SBNR ranged as [10 20 50 
100], while SSNR as [1 5 10 15 20 30 40 50 75 100]. We performed 10 
simulations for each RSN: in each simulation, one of the different values 
of SSNR was considered.

The ground truth signal was simulated as a summation of sinusoids 
with random amplitudes ranging from 0 to 1. The frequencies ranged 
between 8 and 15 Hz (alpha band), with a step of 0.01 Hz, and the phase 
delay was randomly chosen between 0 and 2π, uniformly distributed. 
These  signals  were  then  processed  using  an  autoregressive  model  of 
order 5 to introduce temporal dependencies within each source’s time 
series, without imposing dependencies between sources (A. Basti et al., 
2018; Sommariva et al., 2017; Haufe et al., 2013; Chella et al., 2019). 
We subsequently modeled amplitude interactions between sources. In 
each  direct  coupling,  the  amplitude  of  the  following  source  was  a 
delayed version of the amplitude of the leading source, with a delay of 
15 ms, while the phase of the signal in the following source was pre-
served. This approach ensured that the influence of the leading source 
manifested  only  through  amplitude  modulation,  without  altering  the 
phase independence between the sources. If the adjacency matrix con-
tained indirect paths between sources, the time delay was adjusted for 
the associated connections. Specifically, the delay from one source to 
another was increased to account for the influence of an intermediate 
source, and redundant direct connections were eliminated. This process 
reduced the complexity of the network while preserving the essential 
(direct  and  directional)  amplitude  dynamics.  A  normally  distributed 
noise with an amplitude equal to the 2 % of the amplitude of each source 
was  added  to  take  into  account  noise  from  interacting  sources.  This 
signal was then multiplied by the columns of the lead field matrix cor-
responding to the selected source locations to account for the volume 
conduction from sources to sensors.

The  EEG  signal  was  modeled  as  a  summation  of  the  ground  truth 
signal  and  of  a  mixture  of  independent  standard  normal  processes 
distributed  both over  randomly chosen cortical  nodes  and  electrodes. 
This approach aims to model the presence of both biological noise and 

F. Leone et al.                                                                                                                                                                                                                                   

NeuroImage 303 (2024) 120896 

Table 1 
Considered source positions divided into RSNs (Smith et al., 2013).

Motor Network

Dorsal Attention Network

Visual Network

Nodes

vPoCe
dPrCe
SMA
mdSPL
vPoCe
dPrCe1
SMA2
dmSP2
M1
M1

MNI Coordinates (mm)

Nodes

MNI Coordinates (mm)

Nodes

MNI Coordinates (mm)

57.95
25.81
10.80
9.53
(cid:0) 59.74
(cid:0) 23.16
(cid:0) 11.90
(cid:0) 5.17
(cid:0) 40.89
40.89

(cid:0) 16.22
(cid:0) 12.80
(cid:0) 34.39
(cid:0) 39.92
(cid:0) 19.10
(cid:0) 14.71
(cid:0) 15.93
(cid:0) 41.50
(cid:0) 18.73
(cid:0) 18.73

37.74
58.56
50.33
56.83
39.65
74.61
41.15
58.62
69.11
69.11

FEF
FEF
vIPS
vIPS
mt
mt
aIPS
pIPS-SPL
pIPS-SPL
dPoCe
dPoCe
PrCe
PrCe
IFG

25.44
(cid:0) 22.85
(cid:0) 30.27
34.11
(cid:0) 44.04
48.60
(cid:0) 31.04
(cid:0) 10.89
21.67
(cid:0) 44.41
51.17
(cid:0) 46.66
46.66
43.19

(cid:0) 5.36
(cid:0) 1.46
(cid:0) 77.82
(cid:0) 79.02
(cid:0) 61.23
(cid:0) 61.98
(cid:0) 37.38
(cid:0) 63.63
(cid:0) 65.40
(cid:0) 34.61
(cid:0) 27.64
1.07
1.07
38.28

53.40
57.91
21.64
24.00
(cid:0) 0.45
(cid:0) 2.57
46.96
53.23
47.40
46.75
52.69
33.49
33.49
6.56

V7-POSd
V3-V3A
LO
Fovea-LO
LOMT
V3A

(cid:0) 5.08
9.52
(cid:0) 37.15
(cid:0) 24.49
44.37
29.33

(cid:0) 85.39
(cid:0) 89.44
(cid:0) 90.14
(cid:0) 96.37
(cid:0) 76.41
(cid:0) 87.72

40.61
34.40
13.81
2.62
(cid:0) 12.00
28.83

instrumental noise, according to the following model: 

x(t) = xi(t) + xb(t) + xn(t)                                                               (1)

where  xi  is  the  previously  described  ground  truth  signal  component 
generated by the interacting sources, 

xb(t) = γ1

∑50

j=1

ljsnoise
j

(t)

(2) 

is the biological noise from 50 uncorrelated sources randomly distrib-
uted over the entire cortex, and 

xn(t) = γ2 ⋅ n(t)                                                                               (3)

represents sensor noise. In Eqs. (2) and (3), lj represents the column of 
the  lead  field  matrix  corresponding  to  the  j-th  noise  source;  n(t)  is, 
instead,  the  unweighted  vector  of  sensor  noise.  Finally,  γ1  and  γ2 
represent scaling parameters that respectively determine the influence 
of biological noise and sensor noise, defined as follows: γ1  is the ratio 
between  the  maximum  variance  of  the  true  signal  and  the  maximum 
variance  of  the  noise  from  non-interacting  sources,  multiplied  by  the 
amount of added noise indicated by SBNR. Similarly, γ2 was computed 
using the variance of the noise from non-interacting sources instead of 
interacting sources, multiplied by SSNR.

Following  the  previous  approach,  we  also  performed  additional 
simulations by modeling fully connected networks (i.e., networks where 
nodes  were  all  connected  to  each  other)  and  fully  unconnected  net-
works,  where  nodes  were  all  independent  among  them.  We  then 
computed  the  difference  between  the  ground  truth  FC  and  the  FC 
reconstructed  with  different  regularization  parameter  values  for  both 
types of networks.

2.2. Source reconstruction and performance evaluation

We  performed  an  independent  component  analysis  (ICA)  via  the 
fastICA  algorithm  (Hyvarinen,  1999)  on  the  EEG  simulated  signals. 
Then, we solved the inverse problem for the sensor-level maps of the 
different Independent Components (ICs). To maintain consistency with 
the pipeline employed for real EEG data, we computed again the lead 
field matrix using the New York Head BEM volume conductor model for 
228 electrodes. Using the same models to solve both the forward and the 
inverse problem may lead to the so-called “inverse crime” (Kaipio and 
Somersalo,  2007):  nevertheless,  the  bias  from  the  inverse  crime  was 
even on all the λ values, and it did not influence our trend results. We 
checked this by solving the inverse crime on a subsample of 7.564 nodes 
from the New York Head cortical mesh: these nodes were completely 
distinct from the 10.016 nodes used in EEG signal generation. The re-
sults from this inverse crime check are provided in SI in Fig. A.3.

The inverse problem was  solved using Tikhonov-regularized Mini-
mum Norm Estimation (MNE) approach. The objective of Tikhonov (i.e. 
MNE)  regularization is  to  achieve an  estimation of distributed  source 
activity  that  finds  a  balance  between  minimizing  the  overall  source 
amplitude, accurately reconstructing measured signals, and effectively 
rejecting  noise  (H¨am¨al¨ainen  et  al.,  1993).  This  means  that  the  MNE 
solution is found as 

̂xλ = argminx

⃒
⃒|Lx (cid:0) y||2 + λ

⃒
⃒|x||2

(4) 

The  MNE  solution  is  strongly  dependent  on  the  regularization 
parameter  λ;  its  value  is  typically  based  on  the  SNR  value,  as  in  the 
following equation (Dale et al., 2000; Lin et al., 2004): 

(cid:0)

)

λ = tr

LRLT
tr(C) ∗ SNR2

(5) 

where L is the lead field matrix, and C and R stand for noise covariance 
and source covariance, respectively. If prewhitening is applied to EEG 
data, C is reduced to identity matrix I and then λ = 1
SNR2. This value of 
SNR can be chosen independently from the real SNR of the data (which 
is usually impossible to know), and the most widely used value in this 
application is 3.

Four different performance metrics were evaluated in this study: the 
Region Localization Error (RLE), the Spatial Dispersion (SD), the Overall 
Amplitude (OA), and the number of clusters obtained with the Density- 
Based Spatial Clustering of Applications with Noise (DBSCAN) algorithm 
(Ester et al., 1996). These metrics were evaluated by varying 30 different 
(cid:0) 4  to 102. These values for λ were computed 
λ values, spanning from 10
using Eq. (5), with the following set of SNR values: 0.1, 0.5, 1, 2, 3, 4, 5, 
6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 30, 40, 50, 60, 70, 80, 
90, and 100.

Region Localization Error (Yao and Dewald, 2005) was introduced to 
quantify  localization  accuracy,  and  it  is  defined  in  Eq.  (6),  where  Q 

̂
represents the number of simulated sources, 
Q represents the estimated 
active  sources  (computed  as  the  number  of  cortical  points  where  the 
solution exceeds the 80 % of its range), sj  is the position of the actual 
sources  and  di  is  the  position  of  the  estimated  sources.  The  first 
component  of  Eq.  (6) evaluates  the  average  distance  from  each  esti-
mated  source  to  the  closest  real  source.  The  remaining  real  sources, 
which are not identified, form the elements of set J. In the subsequent 
component of the equation, the average distance is calculated between 
each undetected source and its nearest estimated source. The expected 
value for RLE (in the ideal case) is zero, if not the lowest possible. 

RLE = 1
Q

∑Q

i

minj‖di (cid:0)

sj‖ + 1
̂
Q

∑ˆ
Q

j∈J

mini ‖ sj (cid:0) di ‖

(6) 

To quantify spatial extension, Spatial Dispersion (Molins et al., 2008; 

3 

​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
​
F. Leone et al.                                                                                                                                                                                                                                   

NeuroImage 303 (2024) 120896 

Hauk et al., 2011; Todaro et al. 2019) was used: it is a measure of the 
“width”  of  the  distribution  around  the  cortical  map  peak,  and  it  is 
defined as in Eq. (7) where N is the number of cortical points, Dj stands 
for the distance between the peak of the solution and the j-th cortical 
point,  Fj  stands  for  the  value  of  the  reconstructed  current  in  the  j-th 
point. In an ideal case, the expected value for SD is the lowest possible: it 
cannot be zero either in ideal case, because the MNE algorithm finds a 
distributed solution, therefore it will never find a solution which com-
prises only a single source point. 

√
√
√
√

̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅
∑
N
j=1DjF2
j∑
N
j=1F2
j

SD =

(7) 

Overall Amplitude (Hauk et al., 2011), defined as in Eq. (8), was also 
considered. This metric is used to take into account the different depths 
of source points; nevertheless, this study does not focus on the evalua-
tion  of  deep  sources  reconstruction  due  to  the  intrinsic  limits  of  the 
unweighted MNE algorithm. In fact, it emphasizes lower amplitude su-
perficial sources with respect to higher amplitude deep sources, and this 
makes it unsuitable to study deep sources. We include this metric any-
way for the sake of completeness in Eq. (8), but we do not have an ex-
pected optimal value for this metric. 

∑
N
j=1
maxj

⃒
⃒
⃒
⃒

Fj

⃒
⃒
⃒
⃒
Fj

OA =

(8) 

Finally, the number of clusters was introduced as a metric to evaluate 
the source fragmentation, by using the DBSCAN algorithm: this method 
(Ester et al., 1996) was designed to cluster data of arbitrary shapes in the 
presence of noise in spatial and non-spatial high dimensional databases. 
We  chose  it  over  the  k-means  algorithm  (Ahmed  et  al.,  2020)  for  its 
ability to identify clusters of non-circular shape and because it does not 
need  the  number  of  clusters  as  an  input  parameter.  It  needs  two 
hyper-parameters:  the  minimum  number  of  points  (MinP)  clustered 
together for a region to be considered dense and a distance (ε) measure 
that will be used to locate the points in the neighborhood of any given 
point. In this work, we chose MinP = 2 and ε  = 8 mm. To apply the 
algorithm, we selected a region of interest (ROI) in every IC topography: 
the ROI was defined as the source space points where the inverse solu-
tion was over 60 % of the range of the solution over the whole brain. The 
DBSCAN algorithm was applied providing the coordinates of the source 
points  in  the  ROI.  To  determine  which  λ  value  provided  the  best 
reconstruction,  we  focused  exclusively  on  source  maps  reconstructed 
from IC showing a clear dipolar pattern (identified by visual inspection), 
ensuring that the optimal number of clusters was always 1.

2.3. EEG signal data collection

2.3.1. Participants

EEG signal was recorded from 31 healthy participants (17 men, 14 
women; mean age ± sd = 26.7 ± 4.1 years old). Informed consent was 
obtained  from  all  the  participants.  The  experimental  protocol  was 
approved by the local ethical committee at the Santa Lucia Foundation 
IRCCS (Prot. CE/PROG. 717) and was conducted according to the ethical 
standards of the Declaration of Helsinki.

2.3.2. Data collection

A 10-minute resting-state EEG signal was recorded with a 256-elec-
trode ANT EEG system (ANT Neuro, The Netherlands), using a wave-
guard™  original  EEG  cap  with  256  channels  located  following  an 
equidistant hexagonal layout. The ground electrode was placed on the 
left mastoid, and the reference electrode at the Z12Z channel, which is 
located over the centroparietal scalp middle line of the interhemispheric 
fissure.  Peripheral  data,  such as  electrocardiographic  (ECG)  and  elec-
trooculographic  signal  (vertical  and  hor-  izontal  -  VEOG/EOG)  were 
acquired to be used in the cleaning phase of the EEG signal from artifact 

contamination. We used two EOG channels (one for vertical eye move-
ments and one for horizontal movements) and two ECG channels, which 
were placed under participants’ clavicle. EEG data were recorded with a 
sampling rate of 2048 Hz. Data were collected while participants were 
comfortably seated fixating a small black cross on a white background 
without any other sensory, motor or cognitive task to perform.

2.3.3. EEG preprocessing and source reconstruction

EEG preprocessing was carried out using Fieldtrip (Oostenveld et al., 
2011). First, raw data were down-sampled at 256 Hz and band-passed 
filtered  within  the  1–102  Hz  frequency  range.  Outlier  channels  and 
signal epochs were automatically identified and removed from further 
analysis.  Specifically,  noisy  channels  were  identified  by  assessing  the 
following metrics: i) the low signal similarity, estimated by computing 
the  correlation  between  each  channel  and  its  neighbors.  We  used  a 
correlation threshold equal to 0.6. In addition, a bad channel is identi-
fied  by  searching  for  outliers  in  the  neighbor  correlation  distribution 
setting a statistical threshold (equal to 2.5 standard deviations below the 
mean neighbor correlation from all the channels). Another additional 
criterion was the ratio between the standard deviations of each channel 
and its neighbors (Winter et al., 2007): a bad channel is identified if its 
standard deviation is more than 50 % higher than that of its neighbors 
(thus our variance ratio threshold is equal to 0.5); ii) the deviation from 
the distribution of channel weights obtained by an ICA-based approach 
(fast-ICA algorithm). Epochs containing large bursts of high-frequency 
activity  were  detected  and  removed.  Then  we  used  an  ICA  approach 
to  classify  components  as  brain-generated  or  artifact  according  to 
different parameters: 1) correlation of the IC time course with those of 
EOG/VEOG  and  ECG  reference  channels:  2)  correlation  of  the  IC 
Power-Spectral  Density  (PSD)  with  those  of  EOG/VEOG  and  ECG 
reference  channels;  3)  correlation  of  the  IC  Power  Time-Course  with 
those of EOG/VEOG and ECG channels; 4) kurtosis; 5) 1/f trend of PSD; 
6) flat- ness of PSD. ICs were band-passed (1–102 Hz) and notch-filtered 
(49–51/99–101 Hz). If only one parameter did not reach the threshold, 
the component was classified as an artifact. This analysis pipeline was 
adapted from the MEG preprocessing pipeline (Larson-Prior et al., 2013) 
used  by  the  Human  Connectome  Project,  as  in  our  previous  study 
(Maddaluno et al., 2024).

Source estimation for real data was carried out with the same pipe-
line described for the artificial signal, except for two steps: i) the volu-
metric segmentation and cortical reconstruction were performed with 
the Freesurfer image analysis suite using individual MRIs data of each 
participant; ii) the cortical mesh is composed by 8004 vertices instead of 
10,016 points of the New York Head.

2.4. Estimation of BLP functional connectivity

Functional connectivity was estimated for both simulated and real 
data. For the simulated data, FC was calculated separately for each of the 
three considered RSNs, focusing solely on connectivity within each RSN. 
For the real data, our analysis was focused on a subset of the original 
8004  vertices,  which  included  nodes  with  functional  importance.  In 
detail, we examined a parcellation scheme composed of 164 vertices of 
the source space belonging to 10 RSNs: Auditory Network (AN); Control 
Network (CN); Dorsal Attention Network (DAN); Default Mode Network 
(DMN); Fronto-Parietal Network (FPN); Language Network (LN); Motor 
Network  (MN);  Ventral  Attention  Network  (VAN);  Visual  Foveal 
Network  (VFN);  Visual  Peripherical  Network(VPN).  Specific  MNI  co-
ordinates are associated with each vertex, as reported in previous studies 
(Baldassarre et al., 2014; de Pasquale et al., 2021).

Before estimating the functional connectivity, we applied the Geo-
metric Correction Scheme (GCS), as in (Wens et al., 2015; V. Betti et al., 
2018). We subsequently determined the Band Limited Power (BLP) (de 
Pasquale et al., 2010, 2012) temporal patterns from the source space 
signals  in α  (8–15  Hz),  low β  (15–26 Hz) and  high β  (26–35 Hz)  fre-
quency bands as the average of the squared activity magnitude within a 

4 

F. Leone et al.                                                                                                                                                                                                                                   

NeuroImage 303 (2024) 120896 

400-millisecond sliding window, sampled at a rate of 50 Hz. Considering 
a  couple  of  nodes  i  and  j,  the  static  functional  connectivity  can  be 
defined as follows Eq. (9): 

{

FC =

corr(BLP(i), BLP(j)⊥i

(cid:0)

) + corr
2

BLP(j), BLP(i)⊥j

)
}

, if d(i, j)

(cid:0) 2), 
comparisons with band (α, low β, high β), λ (equals to 10
and  resting  state  networks  (DAN,  VIS,  MN)  as  within-subject  factors 
averaged across connections of the three defined RSNs.

(cid:0) 1 and 10

3. Results

> 1.5; NaN, otherwise

(9) 

3.1. Source reconstruction

where corr(x,y) is the Pearson’s correlation coefficient between signals x 
and y, BLP (i)⊥j is the BLP computed on the time series of node i in which 
the GCS was applied with respect to node j (see details in (Wens et al., 
2015;  V.  Betti  et  al.,  2018)),  d(i,j)  is  the  Euclidean  distance  between 
nodes i and j, and NaN is a “not a number” element for masking corre-
lation coefficients between nodes closer than 15 mm.

BLP FC on simulated data was computed using both the ground truth 
signal  xi  and  the reconstructed signal with  varying regularization  pa-
rameters. We then calculated the relative error for both the fully con-
nected and fully unconnected simulations to assess whether the choice 
of regularization parameter could introduce a bias in the over- or un-
derestimation of FC.

On  the  other  hand,  to  describe  the  difference  between  FC  with 
different λ  values in real data where we did not have a  ground truth 
value, we computed the percentage relative difference, defined in Eq. 
(10),  where  FCλ=10(cid:0) x  represents  the  functional  connectivity  estimated 
with different regularization parameters. 
ΔFC% = FCλ=10(cid:0) 2 (cid:0) FCλ=10(cid:0) 1

(10) 

FCλ=10(cid:0) 2

2.5. Statistical analyses

To analyze the differences between RLE, OA and SD distributions, we 
ran a one-way ANOVA (α  = 0.05) with 4 factors, represented by λ  in-
terest values. Then, we carried out the Bonferroni correction post-hoc 
test.  Percentage  of  occurrence  distributions  derived  from  DBSCAN 
clustering were compared using multiple two sample chi-squared tests (p 
< 0.05). Simulated FC differences between ground truth FC and recon-
structed FC were tested with a paired t-test (two tails). Regarding real- 
data  functional  connectivity  differences  we  ran  repeated  measures 
ANOVA  (α  = 0.05),  with  Bonferroni  correction  for  post-hoc  multiple 

First, we applied the analysis pipeline outlined in Fig. 1 above to the 
synthetic  EEG  signals,  generated  using  the  procedures  outlined  in 
“Materials and methods” Section. Then, we examined the effects of the 
optimum  λ  value  on  the  functional  connectivity  analysis  in  real  EEG 
data.

Fig. 2 presents the trends (in a semi-logarithmic scale) of the three 
metrics,  averaged  across  all  components  obtained  for  all  simulations, 
introduced  in  Section  2.1,  to  assess  the  performance  of  the  source 
reconstruction. In detail, Fig. 2A shows the RLE metric, which decreases 
as λ  increases. Fig. 2B shows the SD metric: this increases as the λ  in-
creases, meaning that the reconstructed sources become more spread as 
λ increases. At last, Fig. 2C shows the OA metric: this increases when λ 
increases, similarly to SD.

For all three metrics, the λ values of major interest are presented as 
(cid:0) 4 and 102 values appear to be the extreme 
bullet points in Fig. 2: the 10
(cid:0) 1 has been 
points of the distribution of the metrics, while the value 10
chosen as it is traditionally used in many EEG analysis pipelines (Calvetti 
(cid:0) 2 appears to be another 
et al., 2019). Moreover, the λ value equal to 10
notable  point  from  methodological  MEG  literature  (Vallarino  et  al., 
2021, 2023), which indicates that the optimal regularization parameter 
for connectivity estimation must be at least an order of magnitude lower 
than the one used for source localization.

Prior to the full analysis, we present a visual representation of the 
changes occurring in source reconstruction when varying the λ  values 
(Fig.  3):  this  figure  showcases  an  example  of  IC  topographies  for  the 
RSNs of interest. The visualizations reveal a clear trend in the enlarge-
ment of reconstructed source sizes with increasing λ. Additionally, we 
observe shifts in the peak of the solution as λ varies, and a corresponding 
fragmentation of sources at lower λ values.

Next, we focused on the analysis of the SD, OA, and RLE metrics for 
(cid:0) 1, 102), as reported 

only the four points of interest of λ (10

(cid:0) 2, 10

(cid:0) 4, 10

Fig. 1. The analysis pipeline of this study is structured in a data simulation step (orange), the introduction of three metrics to analyze simulated data (green), and 
their validation on real data (yellow).

5 

F. Leone et al.                                                                                                                                                                                                                                   

NeuroImage 303 (2024) 120896 

(cid:0) 4 to 102. 
Fig. 2. A. Region Localization Error (RLE) 2.B. Spatial Dispersion (SD) and 2.C. Overall Amplitude (OA) trends computed in 30 λ values spanning from 10
Visual Network (VIS) results are given in cyan; Motor Network (MN) in green; Dorsal Attention Network (DAN) in red. The bullet points indicate the λ values of 
interest 10

(cid:0) 1, and 102.

(cid:0) 2, 10

(cid:0) 4, 10

Fig. 3. Example of IC topographies at λ values of interest (10
Dorsal Attention Network (DAN) component. Red points represent ground truth positions of the simulated sources.

(cid:0) 4, 10

(cid:0) 2, 10

(cid:0) 1, and 102); A) Visual Network (VIS) component; B) Motor Network (MN) component; C) 

(cid:0) 2  and  10

(cid:0) 2,  and  between  10

in Fig. 4. The red box plots represent the RLE, OA and SD for the DAN 
network: specifically, for the RLE metric, we found a statically signifi-
(cid:0) 4 
cant  difference  between  102  and  10
(F3,228  = 81.36, p < 0.05). The OA (F3,210  = 486.67, p < 0.05) and SD 
(F3,138  = 102.15, p < 0.05) metrics present a significant difference for 
every λ distribution. For the MN, the green box plots show the results for 
the three metrics: for the RLE, there was a statistically significant dif-
(cid:0) 4 values (F3,165  = 9.38, p < 0.05). Also for 
ference between 102 and 10
this network, the OA (F3,129 = 260.20, p < 0.05) and SD (F3,93 = 56.50, p 
< 0.05) metrics present a significant difference for every λ distribution. 
Finally, for the VIS (the cyan box plots), no significant differences in the 
RLE metric were found across the λ distribution. Conversely, for the SD 
(F3,117  = 63.42, p < 0.05) and OA (F3,183  = 354.16, p < 0.05) metrics 
presented  statistically  significant  differences  between  every  λ  value. 
Similar results were observed for the real data, which are presented in SI 
in Fig. A.1.

To evaluate the performance of the source reconstruction, in terms of 
the  fragmentation  of  the  MNE  solution,  we  introduced  the  cluster 
analysis that reduced dimensionality data into groups using the DBSCAN 
algorithm. In Fig. 5, it is reported an example of the clustering results (C) 
for a selected IC, for different λ values compared with the reconstructed 
topography  (B)  and  the  sensor  level  map  (A).  Fig.  6 reports  the  per-
centage  of  occurrences  of  clusters in  real  data:  it  shows  that the  per-
centage  of  true  detections  of  only  one  cluster  is  significantly  higher 
(9)=44.68, p <
when λ  is 10

(cid:0) 1, as compared to 10

(cid:0) 2  and 102  (χ2

(cid:0) 4, 10

(8)= 38.40, p < 0.001; χ2

(6)= 17.14, p = 0.009, respectively). We 
0.001; χ2
(cid:0) 4  and 
can notice that the highest fragmentation is found when λ is 10
(cid:0) 2, with no statistically significant difference between them. This high 
10
fragmentation is expected, as minimal regularization leads to reduced 
numerical  stability  in  the  solution,  as  in  Eq.  (4).  On  the  other  hand, 
fragmentation is reduced for λ = 102 due to strong regularization, which 
tends to diffuse the solution across the brain, as observed in the SD trend. 
Similar results for synthetic data are provided in SI (Fig. A.2).

3.2. Functional connectivity

(cid:0) 2 and λ = 10

Regarding  FC  simulations,  we  compared  the  connectivity  recon-
(cid:0) 1 with the ground truth connectivity. 
structed with λ = 10
The results on the simulations with fully connected networks show an 
average  value  of  ground  truth  connectivity  equal  to  0.95,  while  the 
(cid:0) 1 were 
average values of the reconstructed FC with λ = 10
0.66 and 0.56, respectively.

(cid:0) 2 and λ = 10

We then performed a paired t-test on the difference between ground 
truth  FC  and  reconstructed  FC  for  each  network  and  each  λ  value 
(cid:0) 2 are always closer to 
separately. Results highlight that FC with λ = 10
(cid:0) 1 (t(90)DAN = 33.4, p < 0.001; 
the ground truth FC with respect to λ = 10
t(27)MN  = 13.5,  p  < 0.001;  t(14)VIS  = 21.4,  p  < 0.001).  Regarding  the 
unconnected networks, the ground truth FC was 0.04, and the recon-
(cid:0) 1 was 0.19 and 0.39, respectively. 
structed FC with λ = 10

(cid:0) 2 and λ = 10

6 

F. Leone et al.                                                                                                                                                                                                                                   

NeuroImage 303 (2024) 120896 

(cid:0) 2 are higher than the FC with λ = 10

Once  again,  results  of  the  paired  t-test  showed  that  FC  values  recon-
(cid:0) 1 in the DAN 
structed with λ = 10
and the VIS network (t(90)DAN  = (cid:0) 27.7, p < 0.001; t(14)VIS  = (cid:0) 9.9, p <
0.001). No significant differences were found for MN (t(27)MN =(cid:0) 0.9, p =
0.4).  Difference  matrices  between  ground  truth  FC  values  and  recon-
structed FC values for both fully unconnected and fully connected are 
given in SI, Fig. A.5 and A.6.

Finally,  we  reported  relative  percentage  changes  (defined  in  Eq. 
(10)) in functional connectivity matrices derived from real EEG data in 
Fig. 7. These results, in combination with the simulated data results that 
point  towards  an  inflation  of  functional  connectivity  values  for  the 
(cid:0) 1), speaks for the smallest λ value being able to 
highest λ value (λ = 10
better recover genuine functional connectivity values.

We computed the BLP (see Materials and Methods Section) from the 
source  space  signals  in  the  selected  frequency  bands.  For  consistency 
with the simulated data, we considered only 3 networks (e.g., DAN, VIS, 
MN) for the following statistical analysis. We found a significant main 
effect of the factor BAND (F2,60 = 183.88, p < 0.001), as accounted for by 
higher  FC  in  α  as  compared  to  all  other  bands  (post  hoc  Bonferroni 
corrected, p < 0.05). We also observed a significant main effect of λ (F1,30 
= 6.96, p < 0.05), wherein higher FC was associated with a λ value of 
(cid:0) 1, as depicted in Fig. 8. Furthermore, we 
10
did not detect a significant NETWORK effect.

(cid:0) 2 compared to a value of 10

4. Discussion

Gathering  information  about  the  brain  regions  responsible  for 
generating different EEG signals can yield valuable insights into brain 
function. To estimate the source’s location, one must adopt both a model 
for the source and a model for the head. After selecting these models, an 
inverse  solution  can  be  computed  to  determine  the  source’s  position 
within  the  head  model.  This  estimated  source  is  then  assumed  to 
represent  the  actual  source.  The  precision  of  this  source  localization 
method  is  influenced  by  several  factors,  including  errors  in  source 
modeling, head modeling, measurement locations, and EEG noise (Jatoi 
et al., 2014).

This  study  explored  the  influence  of  different  regularization 
parameter values on the accuracy of source localization for resting- state 
EEG activities. We utilized Minimum Norm Estimation on independent 
components  of  the  brain,  while  incorporating  a  realistic  head  model 
known as the New York Head. First, we generated synthetic resting-state 
EEG signals with varying Signal-to-Noise Ratios for three distinct neural 
networks:  the  Motor  Network,  the  Visual  Network,  and  the  Dorsal 
Attention Network. The source reconstruction evaluation involved four 
performance metrics: the Region Localization Error, the source exten-
sion, the overall amplitude and the source fragmentation. A summary of 
the results for these metrics is provided in Table 2. Specifically, the re-
sults obtained for SD and OA metrics (Fig. 2A and Fig. 2C) are consistent 
with  the  theory  behind  them  (Hauk  et  al.,  2011)  and  behind  MNE. 
Regarding  the  spatial  dispersion  trend,  it  depends  directly  on  the 
mathematical definition of MNE (see Eq. (4)). Indeed, when λ increase, 
the MNE algorithm tends to favor solutions where the energy is mini-
mized;  this  results  in  source  reconstruction  where  cortex  points  have 
more  and  more  similar  source  energy,  rather  than  all  the  energy 
concentrated on a few points. For this reason, the SD in MNE with higher 
λ  has  to  be  higher.  On  the  other  hand,  overall  amplitude  is  the 
normalized  sum  of  reconstructed  source  amplitude  (see  Eq.  (8)):  as 
already  said,  when  the  regularization  parameter  increases,  the 
maximum  of  the  solution  becomes  smaller  while  the  total  energy  re-
mains the same (even if differently distributed throughout the cortex), 
and that is why OA has to get bigger when λ gets bigger. Regarding the 
RLE metric,  the  trend  depended on the  topography  of the  considered 
network and on the lambda values. Indeed, the localization errors were 
smaller for networks that present very close seeds (as the VIS network), 
while were higher when networks got more extended (as for the MN and 

7 

Fig. 4. A. Region Localization Error (RLE) 2.B. Overall Amplitude (OA) and 2. 
(cid:0) 1, and 102) for: 
C. Spatial Dispersion (SD) trends at λ  values (10
Visual  Network  (VIS),  in  cyan;  B)  Motor  Network  (MN)  in  green;  C)  Dorsal 
Attention  Network  (DAN),  in  red.  Distributions  are  made  by  combining  the 
results  from  every  IC  of  different  simulations  to  take  into  account  different 
noise values.

(cid:0) 2, 10

(cid:0) 4, 10

F. Leone et al.                                                                                                                                                                                                                                   

NeuroImage 303 (2024) 120896 

Fig. 5. A) Example of a MN topographic map; B) reconstructed sources at different λ values (10
of the simulated sources; C) clustering results.

(cid:0) 4, 10

(cid:0) 2, 10

(cid:0) 1, and 102). Red points represent ground truth positions 

with  the  DBSCAN  algorithm  on  both  real  and  simulated  EEG  data  to 
evaluate the source fragmentation. Our results suggest that, when λ  is 
(cid:0) 1, the solution is minimally fragmented, in contrast to the 
equal to 10
(cid:0) 4, where high numerical instability 
solutions obtained with 10
led to excessive fragmentation.

(cid:0) 2 and 10

Finally, we examined the impact of the optimal λ values on the FC 
estimation in both simulated and real data (a summary of FC results is 
provided again in Table 2). For the simulated data, we conducted two 
types  of  simulations:  one  where  the  RSNs  were  fully  connected,  and 
another where they were fully unconnected. In both cases, we compared 
the reconstructed FC to the ground truth connectivity. Across all RSNs, 
(cid:0) 2  was closer to the ground truth 
FC reconstructed with λ  equal to 10
(cid:0) 1  (Fig.  A.5  and  A.6).  It  is 
than  FC  reconstructed  with  λ  equal  to  10
important to note, however, that the estimated FC was lower than the 
ground truth in the fully connected case, and higher than the ground 
truth in the unconnected case. This “smoothing” effect may be attributed 
to the approximations introduced during source reconstruction, due to 
the  underdetermined  nature  of  the  inverse  problem.  Regarding  FC  in 
real  data,  even  if  we  did  not  have  a  ground  truth  reference  for  the 
optimal  FC,  we  can  qualitatively  see  the  differences  between  FC 
(cid:0) 2  with respect to the traditional value of 
computed with λ equal to 10
(cid:0) 1 found in the literature (Krishnaswamy et al., 2017; Mikulan et al., 
10
2020; Pascarella et al., 2023). For example, in the present work, we can 
note the effect of the λ value on the FC in the α band. Specifically, we 
found that, in agreement with previous literature (Samogin et al., 2020), 
FC was higher in α as compared to all other bands. Another significant 
effect was found in the value of the λ, which showed higher FC associ-
(cid:0) 1, as depicted in 
ated with a λ value of 10
Fig. 8. Moreover, we did not observe a significant network-related effect 
that  is  noteworthy  because  the  strength  of  FC  values  remains  consis-
(cid:0) 2  regardless of the analyzed resting state net-
tently higher for λ at 10
works. Combining this finding with the simulation results, we can infer 
that the ground truth connectivity in real data is likely higher than our 
estimates.  Indeed,  in  line  with  previous  fMRI,  as  well  as  EEG/MEG, 
literature (Biswal et al., 1995; Raichle et al., 2001; Fox et al., 2005; Betti 
et  al.,  2013;  A.  2018;  Maddaluno  et  al.,  2024)  based  on  power  or 
amplitude envelope correlation, we expect coherent functional patterns 

(cid:0) 2 compared to a value of 10

Fig. 6. Percentage of occurrence derived from cluster distribution in real data 
(cid:0) 1 and 102. The blue color indicates the 
among λ values equal to 10
presence of one cluster; the orange color, the presence of two clusters; the gray 
color,  the  presence  of  three  clusters;  the  yellow  color,  the  presence  of  four 
clusters; the black color, the presence of five clusters.

(cid:0) 2, 10

(cid:0) 4, 10

DAN). This trend occurs since as the brain network spans a larger area, it 
becomes  easier  to  differentiate  between  different  source  points.  For 
instance,  when  considering  VIS  seeds,  no  significant  differences  were 
observed  among  various  λ  values,  primarily  due  to  their  proximity, 
which closely mirrors the spatial resolution of EEG. In contrast, as the 
network expands across the brain, as seen in MN and especially in DAN, 
significant variations in RLE with respect to different λ values become 
(cid:0) 1 fail to 
evident. Furthermore, contiguous values, such as 10
reveal a significant difference for the RLE metric. Our explanation is that 
this metric is not sufficiently sensitive to values spaced by only an order 
of  magnitude.  By  contrast,  SD  and  OA  metrics  are  sensitive  to  small 
distances across nodes (e.g., the VIS network) and values, showing sig-
nificance for  all λ  values. Then, we performed  the clustering analysis 

(cid:0) 2 and 10

8 

F. Leone et al.                                                                                                                                                                                                                                   

NeuroImage 303 (2024) 120896 

Fig. 7. Percentage relative difference between FC matrices for 164 nodes in 10 RSNs obtained with the two different λ values. Matrices display, for the different 
frequency bands, the relative percentage changes in FC calculated according to Eq. (10). A positive entry in the matrices indicates an increase in FC for that specific 
node  pair  when  the  source  is  reconstructed  using  the  smallest  λ  value.See  Fig  A.4  in  SI  for  the  original  matrices  from  which  these  relative  differences  have 
been calculated.

Fig. 8. Representation of Z Fisher values for the significant main effect of frequency band and λ.

Table 2 
Summary of the results for all the metrics regarding both source reconstruction and functional connectivity.

SIMULATED DATA

REAL DATA

SOURCE 

RECONSTRUCTION

REGION 
LOCALIZATION ERROR
SPATIAL DISPERSION
OVERALL AMPLITUDE

(cid:0) 1 always 

RLE trend depends on the RSN. 10
presents with the lowest value, but there is no 
significant difference with 10
(cid:0) 1 nor 10
Neither 10
(cid:0) 1 nor 10
Neither 10

(cid:0) 2
(cid:0) 2 are extrema for SD
(cid:0) 2 are extrema for OA

—

As for simulated data
As for simulated data

SOURCE 
FRAGMENTATION

(cid:0) 1 shows the lowest fragmentation; differences 

10
with other λ values are all significant

(cid:0) 1 shows the lowest fragmentation; differences with other λ values 

10
are all significant. The trend is even stronger than in simulated data

FUNCTIONAL 

CONNECTIVITY

FULLY CONNECTED 
NETWORK

(cid:0) 2 gets closer to ground truth FC than 10

10
(both underestimate ground truth FC)

(cid:0) 1 

FULLY UNCONNECTED 
NETWORK

(cid:0) 2 gets closer to ground truth FC than 10

10
(both overestimate ground truth FC)

(cid:0) 1 

FC ground truth is unknown but combining results from simulated and 
(cid:0) 1), we can infer 
(cid:0) 2 gives back higher FC than 10
real data (where 10
that real FC is very strong. This fits with a resting brain model 
comprised of highly connected RSNs (Raichle et al., 2001)

—

9 

F. Leone et al.                                                                                                                                                                                                                                   

NeuroImage 303 (2024) 120896 

between signals of nodes of canonical RSNs in the resting brain.

Declaration of competing interest

Our finding can be considered highly relevant since there is still an 
open debate for the selection of the regularization parameter within the 
context of the current EEG/MEG literature. For instance, in (Samuelsson 
et al., 2021; Ramírez et al., 2011), the authors compared several source 
localization techniques, including MNE; they analyzed the impact of λ 
on  source  localization,  by  considering  the  Localization  Error  and  the 
Spatial Dispersion parameters, but no analysis was carried out regarding 
source  fragmentation  as  in  our  study.  Moreover,  their  study  did  not 
investigate  functional  connectivity.  Other  works  filled  this  gap  by 
investigating  the  optimal regularization  parameter  in  MEG functional 
connectivity (Hincapi´e et al., 2016; Vallarino et al., 2021, 2023). They 
found  out  that  the  ratio  between  the  regularization  parameter  for 
cross-power spectrum estimation and for source localization should be 
less than 0.5: this finding confirms the trend to use a lower λ value for 
connectivity than for source localization (Vallarino et al., 2021). In their 
latest  study,  the  authors  expanded  this  basis  by  suggesting  that  the 
regularization parameter for connectivity estimation should be 1–2 or-
ders of magnitude lower than the optimal value for source localization 
(Vallarino  et  al.,  2023).  Concerning  the  above-mentioned  works 
(Vallarino  et  al.,  2021,  2023),  we  considered  EEG  signals  instead  of 
MEG, and we validated our methodological study not only on simulated 
data but also on real functional connectivity data. In this context, we 
suggest using λ  values equal to 10
102) for connectivity estima-
tion. Regarding source reconstruction, RLE failed to reveal a significant 
(cid:0) 2.  On  the  other  hand,  a  significant 
difference  between  10
difference was found for SD and OA between all considered λ values, but 
no  conclusion  can  be  drawn  for  the  best  value  of  regularization 
parameter. Source fragmentation metric instead showed a clear direc-
tion: in real data we found a larger source fragmentation for λ equal to 
(cid:0) 1 (see Fig. 6). Therefore, we still support the con-
10
ventional practice of using 10
32) as a reference for the regulari-
zation parameter in source localization.

(cid:0) 2 rather than 10

(cid:0) 1  and  10

(cid:0) 2  (i.e.,  1

(cid:0) 1  (⋍  1

5. Conclusions

This  methodological  study  underscores  the  intricate  interplay  be-
tween regularization parameter, neural network topography, and source 
localization accuracy in high-density EEG for resting-state activity. We 
(cid:0) 1  as a reference for the 
support the conventional practice of using 10
regularization  parameter  in  source  reconstruction.  Furthermore,  we 
(cid:0) 2  for connectivity estimation. This contri-
propose using λ equal to 10
bution aims to advance methodological approaches in EEG research and 
provide valuable guidance for researchers and practitioners striving to 
enhance  source  localization’s  accuracy  and  reliability  in  the  human 
brain’s complex domain.

CRediT authorship contribution statement

F.  Leone:  Writing  –  review  &  editing,  Writing  –  original  draft, 
Validation, Methodology, Investigation, Formal analysis, Data curation, 
Conceptualization. A. Caporali: Writing – review & editing, Writing – 
original  draft,  Investigation,  Formal  analysis,  Conceptualization.  A. 
Pascarella:  Writing  –  review  &  editing,  Supervision,  Methodology, 
Conceptualization.  C.  Perciballi:  Writing  –  review  &  editing,  Data 
curation, Conceptualization. O. Maddaluno: Writing –  review &  edit-
ing,  Supervision,  Methodology,  Data  curation,  Conceptualization.  A. 
Basti: Writing – review & editing, Data curation, Conceptualization. P. 
Belardinelli: Writing –  review &  editing, Supervision, Conceptualiza-
tion. L. Marzetti: Writing –  review &  editing, Supervision, Methodol-
ogy, Funding acquisition, Conceptualization. G. Di Lorenzo: Writing – 
review  &  editing,  Supervision,  Conceptualization.  V.  Betti:  Writing  – 
review  &  editing,  Supervision,  Project  administration,  Methodology, 
Investigation, Funding acquisition, Data curation, Conceptualization.

10 

The authors declare that they have no known competing financial 
interests or personal relationships that could have appeared to influence 
the work reported in this paper.

Acknowledgements

This  project  has  received  funding  from  the  European  Research 
Council (ERC) under the European Union’s Horizon 2020 research and 
innovation programme (HANDmade, grant agreement No 759651) to V. 
B. V.B. and P.B. are supported by the European Union – NextGeneration 
EU – Project acronym “CONTACT” Mission 4 component C2, Investment 
1.1., CUP B53D23014170006. L.M. is supported by the European Union 
–  NextGeneration EU–  Project acronym “NEUROSTAR BTP. Mission 4 
component 2, Investment 1.1. CUP D53D23019260001. A.P. is a mem-
ber  of  the  Gruppo  Nazionale  Calcolo  Scientifico-Istituto  Nazionale  di 
Alta  Matematica  (GNCS-INdAM).  AC  was  supported  by  the  European 
Union-  Next  Generation  EU,  Missione  4,  Componente  2,  CUP 
C53D23008470001.

Supplementary materials

Supplementary material associated with this article can be found, in 

the online version, at doi:10.1016/j.neuroimage.2024.120896.

Data availability

Data will be made available on request. 

References

Ahmed, M., Seraj, R., Islam, S.M.S., 2020. The k-means algorithm: a comprehensive 

survey and performance evaluation. Electronics (Basel) 9, 1295.

Baillet, S., Mosher, J., Leahy, R., 2001. Electromagnetic brain mapping. IEEE Signal 

Process. Mag. 18, 14–30. https://doi.org/10.1109/79.962275.

Baldassarre, A., Ramsey, L., Hacker, C.L., Callejas, A., Astafiev, S.V., Met- calf, N.V., 
Zinn, K., Rengachary, J., Snyder, A.Z., Carter, A.R., Shulman, G.L., Corbetta, M., 
2014. Large-scale changes in network interactions as a physiological signature of 
spatial neglect. Brain 137, 3267–3283. https://doi.org/10.1093/brain/awu297. 
URL10.1093/brain/awu297. 

Basti, A., Chella, F., Guidotti, R., Ermolova, M., D’Andrea, A., Sten- roos, M., Romani, G. 
L., Pizzella, V., Marzetti, L., 2022. Looking through the windows: a study about the 
dependency of phase- coupling estimates on the data length. J. Neural Eng. 19, 
016039. https://doi.org/10.1088/1741-2552/ac542f. URL10.1088/1741-2552/ 
ac542f. 

Basti, A., Pizzella, V., Chella, F., Romani, G.L., Nolte, G., Marzetti, L., 2018. Disclosing 
large-scale directed functional connections in MEG with the multivariate phase slope 
index. Neuroimage 175, 161–175. https://doi.org/10.1016/j. 
neuroimage.2018.03.004. URL10.1016/j.neuroimage.2018.03.004. 

Betti, V., Della Penna, S., de Pasquale, F., Mantini, D., Marzetti, L., Romani, G., 

Corbetta, M., 2013. Natural scenes viewing alters the dynamics of functional 
connectivity in the human brain. Neuron 79, 782–797. https://doi.org/10.1016/j. 
neuron.2013.06.022. URL10.1016/j.neuron.2013.06.022. 

Betti, V., Corbetta, M., de Pasquale, F., Wens, V., Della Penna, S., 2018. Topology of 
functional connectivity and hub dynamics in the beta band as temporal prior for 
natural vision in the human brain. J. Neurosci. 38, 3858–3871.

Biswal, B., Zerrin Yetkin, F., Haughton, V.M., Hyde, J.S., 1995. Functional connectivity 
in the motor cortex of resting human brain using echo-planar mri. Magn. Reson. 
Med. 34, 537–541.

Brookes, M.J., Woolrich, M., Luckhoo, H., Price, D., Hale, J.R., Stephen- son, M.C., 

Barnes, G.R., Smith, S.M., Morris, P.G., 2011. Investigating the electrophysiological 
basis of resting state networks using magnetoen- cephalography. Proc. Natl. Acad. 
Sci. 108, 16783–16788. https://doi.org/10.1073/pnas.1112685108. URL10.1073/ 
pnas.1112685108. 

Calvetti, D., Pascarella, A., Pitolli, F., Somersalo, E., Vantaggi, B., 2019. Brain activity 

mapping from meg data via a hierarchical bayesian algorithm with automatic depth 
weighting. Brain Topogr. 32, 363–393.

Chella, F., Marzetti, L., Stenroos, M., Parkkonen, L., Ilmoniemi, R.J., Romani, G.L., 
Pizzella, V., 2019. The impact of improved MEG–MRI co-registration on MEG 
connectivity analysis. Neuroimage 197, 354–367. https://doi.org/10.1016/j. 
neuroimage.2019.04.061. URL10.1016/j.neuroimage.2019.04.061. 

Dale, A.M., Liu, A.K., Fischl, B.R., Buckner, R.L., Belliveau, J.W., Lewine, J.D., 

Halgren, E., 2000. Dynamic statistical parametric mapping: combin- ing fmri and 
meg for high-resolution imaging of cortical activity. Neuron 26, 55–67.

F. Leone et al.                                                                                                                                                                                                                                   

NeuroImage 303 (2024) 120896 

De Leener, B., Fonov, V.S., Collins, D.L., Callot, V., Stikov, N., Cohen- Adad, J., 2018. 

Pam50: unbiased multimodal template of the brainstem and spinal cord aligned with 
the icbm152 space. Neuroimage 165, 170–179.

Maddaluno, O., Della Penna, S., Pizzuti, A., Spezialetti, M., Corbetta, M., de Pasquale, F., 
Betti, V., 2024. Encoding Manual Dexterity through Modulation of Intrinsic α Band 
Connectivity. J. Neurosci. 44 (20).

de Pasquale, F., Della Penna, S., Snyder, A.Z., Lewis, C., Mantini, D., Marzetti, L., 

Marzetti, L., Della Penna, S., Snyder, A.Z., Pizzella, V., Nolte, G., de Pasquale, F., 

Belardinelli, P., Ciancetta, L., Pizzella, V., Romani, G.L., Corbetta, M., 2010. 
Temporal dynamics of spontaneous meg activity in brain networks. Proc. Natl. Acad. 
Sci. 107, 6040–6045. https://doi.org/10.1073/pnas.0913863107. URL10.1073/ 
pnas.0913863107. 

de Pasquale, F., Della Penna, S., Snyder, A.Z., Marzetti, L., Pizzella, V., Romani, G.L., 

Corbetta, M., 2012. A cortical core for dynamic inte- gration of functional networks 
in the resting human brain. Neuron 74, 753–764. https://doi.org/10.1016/j. 
neuron.2012.03.031. URL10.1016/j.neuron.2012.03.031. 

de Pasquale, F., Spadone, S., Betti, V., Corbetta, M., Della Penna, S., 2021. Temporal 
modes of hub synchronization at rest. Neuroimage 235, 118005. https://doi.org/ 
10.1016/j.neuroimage.2021.118005. URL:10.1016/j.neuroimage.2021.118005. 
Doucet, G., Naveau, M., Petit, L., Delcroix, N., Zago, L., Criv- ello, F., Jobard, G., Tzourio- 
Mazoyer, N., Mazoyer, B., Mel- let, E., Joliot, M., 2011. Brain activity at rest: a multi- 
scale hierarchical functional organization. J. Neurophysiol. 105, 2753–2763. 
https://doi.org/10.1152/jn.00895.2010. URL10.1152/jn.00895.2010. 

Ester, M., Kriegel, H.P., Sander, J., Xu, X., et al., 1996. A Density-Based Algorithm For 
Discovering Clusters in Large Spatial Databases With Noise. kdd, pp. 226–231.
Fox, M.D., Snyder, A.Z., Vincent, J.L., Corbetta, M., Van Essen, D.C., Raichle, M.E., 2005. 
The human brain is intrinsically organized into dynamic, anticorrelated functional 
networks. Proc. Natl. Acad. Sci. 102, 9673–9678.

Gramfort, A., Luessi, M., Larson, E., Engemann, D.A., Strohmeier, D., Brod- beck, C., 

Goj, R., Jas, M., Brooks, T., Parkkonen, L., et al., 2013. Meg and eeg data analysis 
with mne-python. Front. Neurosci. 267.

Grech, R., Cassar, T., Muscat, J., Camilleri, K.P., Fabri, S.G., Zervakis, M., 

Xanthopoulos, P., Sakkalis, V., Vanrumste, B., 2008. Review on solving the inverse 
problem in eeg source analysis. J Neuroeng Rehabil 5, 1–33.

H¨am¨al¨ainen, M., Hari, R., Ilmoniemi, R.J., Knuutila, J., Lounasmaa, O.V., 1993. 
Magnetoencephalography—Theory, instrumentation, and applications to 
noninvasive studies of the working human brain. Rev. Mod. Phys. 65 (2), 413.
Hanke, M., Hansen, P.C., 1993. Regularization methods for large-scale prob- lems. Surv. 

Math. Ind 3, 253–315.

Haufe, S., Nikulin, V.V., Mu¨ller, K.R., Nolte, G., 2013. A critical assessment of 

connectivity measures for EEG data: a simulation study. Neuroimage 64, 120–133. 
https://doi.org/10.1016/j.neuroimage.2012.09.036. URL10.1016/j. 
neuroimage.2012.09.036. 

Hauk, O., Wakeman, D.G., Henson, R., 2011. Comparison of noise-normalized minimum 
norm estimates for MEG analysis us- ing multiple resolution metrics. Neuroimage 54, 
1966–1974. https://doi.org/10.1016/j.neuroimage.2010.09.053. URL10.1016/j. 
neuroimage.2010.09.053. 

Hincapi´e, A.S., Kujala, J., Mattout, J., Daligault, S., Delpuech, C., Mery, D., Cosmelli, D., 
Jerbi, K., 2016. Meg connectivity and power detections with minimum norm 
estimates require different regularization parameters. Comput. Intell. Neurosci. 
2016, 1–11. https://doi.org/10.1155/2016/3979547. URL10.1155/2016/3979547. 

Hipp, J.F., Hawellek, D.J., Corbetta, M., Siegel, M., Engel, A.K., 2012. Large-scale 

cortical correlation structure of spontaneous os- cillatory activity. Nat. Neurosci. 15, 
884–890. https://doi.org/10.1038/nn.3101. URL10.1038/nn.3101. 

Huang, Y., Parra, L.C., Haufe, S., 2016. The new york head—A precise standardized 

volume conductor model for EEG source localization and tES targeting. Neuroimage 
140, 150–162. https://doi.org/10.1016/j.neuroimage.2015.12.019. URL10.1016/j. 
neuroimage.2015.12.019. 

Hyvarinen, Aapo., 1999. Fast and robust fixed-point algorithms for independent 

component analysis. IEEE Trans. Neural Networks 10.3, 626–634.

Ilmoniemi, R.J., Sarvas, J., 2019. Brain signals: Physics and Mathematics of MEG and 

EEG. Mit Press.

Jatoi, M.A., Kamel, N., Malik, A.S., Faye, I., Begum, T., 2014. A survey of methods used 
for source localization using eeg signals. Biomed. Signal Process. Control 11, 42–52.

Kaipio, J., Somersalo, E., 2007. Statistical inverse prob- lems: discretization, model 

reduction and inverse crimes. J. Comput. Appl. Math. 198, 493–504. https://doi. 
org/10.1016/j.cam.2005.09.027. URL10.1016/j.cam.2005.09.027. 

Knyazev, G.G., Savostyanov, A.N., Bocharov, A.V., Tamozh- nikov, S.S., Saprigyn, A.E., 
2016. Task-positive and task- negative networks and their relation to depression: eeg 
beam- former analysis. Behav. Brain Res. 306, 160–169. https://doi.org/10.1016/j. 
bbr.2016.03.033. URL10.1016/j.bbr.2016.03.033. 

Krishnaswamy, P., Obregon-Henao, G., Ahveninen, J., Khan, S., Babadi, B., Iglesias, J.E., 

Ha¨mal¨ainen, M.S., Purdon, P.L., 2017. Sparsity enables estimation of both 
subcortical and cortical activ- ity from meg and eeg. Proc. Natl. Acad. Sci. 114. 
https://doi.org/10.1073/pnas.1705414114. URL10.1073/pnas.1705414114. 
Larson-Prior, L.J., Oostenveld, R., Della Penna, S., Michalareas, G., Prior, F., Babajani- 
Feremi, A., 2013. Adding dynamics to the Human Connectome Project with MEG. 
Neuroimage 80, 190–201.

Lin, F.H., Witzel, T., Ha¨m¨al¨ainen, M.S., Dale, A.M., Belliveau, J.W., Stufflebeam, S.M., 
2004. Spectral spatiotemporal imaging of corti- cal oscillations and interactions in 
the human brain. Neuroimage 23, 582–595. https://doi.org/10.1016/j. 
neuroimage.2004.04.027. URL10.1016/j.neuroimage.2004.04.027. 

Liu, Q., Farahibozorg, S., Porcaro, C., Wenderoth, N., Mantini, D., 2017. Detecting large- 
scale networks in the human brain us- ing high-density electroencephalography: 
imaging brain networks with high density eeg. Hum. Brain Mapp. 38, 4631–4643. 
https://doi.org/10.1002/hbm.23688. URL10.1002/hbm.23688. 

Liu, Q., Ganzetti, M., Wenderoth, N., Mantini, D., 2018. Detect- ing large-scale brain 
networks using eeg: impact of electrode density, head modeling and source 
localization. Frontiers in Neuroin- formatics 12. https://doi.org/10.3389/ 
fninf.2018.00004. URL10.3389/fninf.2018.00004. 

11 

Romani, G.L., Corbetta, M., 2013. Frequency specific interactions of meg resting 
state activity within and across brain networks as revealed by the multivariate 
interaction measure. Neuroimage 79, 172–183.

Mikulan, E., Russo, S., Parmigiani, S., Sarasso, S., Zauli, F.M., Rubino, A., Avanzini, P., 

Cattani, A., Sorrentino, A., Gibbs, S., et al., 2020. Simulta- neous human 
intracerebral stimulation and hd-eeg, ground-truth for source localization methods. 
Sci. Data 7, 127.

Molins, A., Stufflebeam, S., Brown, E., H¨am¨al¨ainen, M., 2008. Quantification of the 
benefit from integrating MEG and EEG data in minimum ℓ2-norm estimation. 
Neuroimage 42, 1069–1077. https://doi.org/10.1016/j.neuroimage.2008.05.064. 
URL10.1016/j.neuroimage.2008.05.064. 

Oostendorp, T.F., Van Oosterom, A., 1989. Source parameter estimation in 

inhomogeneous volume conductors of arbitrary shape. IEEE Trans. Biomed. Eng. 36, 
382–391.

Oostenveld, R., Fries, P., Maris, E., Schoffelen, J.M., 2011. Field- trip: open source 

software for advanced analysis of meg, eeg, and invasive electrophysiological data. 
Intell. Neuroscience. https://doi.org/10.1155/2011/156869, 2011URL10.1155/ 
2011/156869. 

Pascarella, A., Mikulan, E., Sciacchitano, F., Sarasso, S., Ru- bino, A., Sartori, I., 

Cardinale, F., Zauli, F., Avanzini, P., No- bili, L., Pigorini, A., Sorrentino, A., 2023. 
An in–vivo validation of esi methods with focal sources. Neuroimage 277, 120219. 
https://doi.org/10.1016/j.neuroimage.2023.120219. URL10.1016/j. 
neuroimage.2023.120219. 

Raichle, M.E., MacLeod, A.M., Snyder, A.Z., Powers, W.J., Gusnard, D.A., Shulman, G.L., 

2001. A default mode of brain function. Proc. Natl. Acad. Sci. 98, 676–682.
Ramírez, R.R., Kopell, B.H., Butson, C.R., Hiner, B.C., Baillet, S., 2011. Spectral signal 

space projection algorithm for frequency domain MEG and EEG denoising, 
whitening, and source imaging. Neuroimage 56 (1), 78–92.

Samogin, J., Marino, M., Porcaro, C., Wenderoth, N., Dupont, P., Swinnen, S.P., 

Mantini, D., 2020. Frequency-dependent functional connectivity in resting state 
networks. Hum. Brain Mapp. 41, 5187–5198.

Samuelsson, J.G., Peled, N., Mamashli, F., Ahveninen, J., Ha¨m¨al¨ainen, M.S., 2021. 
Spatial fidelity of MEG/EEG source estimates: a general evaluation approach. 
Neuroimage 224, 117430. https://doi.org/10.1016/j.neuroimage.2020.117430. 
URL10.1016/j.neuroimage.2020.117430. 

Schoffelen, J., Gross, J., 2009. Source connectivity analysis with meg and eeg. Hum. 
Brain Mapp. 30, 1857–1865. https://doi.org/10.1002/hbm.20745. URL10.1002/ 
hbm.20745. 

Siems, M., Pape, A.A., Hipp, J.F., Siegel, M., 2016. Measur- ing the cortical correlation 
structure of spontaneous oscilla- tory activity with eeg and meg. Neuroimage 129, 
345–355. https://doi.org/10.1016/j.neuroimage.2016.01.055. URL10.1016/j. 
neuroimage.2016.01.055. 

Smith, S.M., Fox, P.T., Miller, K.L., Glahn, D.C., Fox, P.M., Mackay, C.E., Filippini, N., 
Watkins, K.E., Toro, R., Laird, A.R., et al., 2009. Correspondence of the brain’s 
functional architecture during activation and rest. Proc. Natl. Acad. Sci. 106, 
13040–13045.

Smith, S.M., Vidaurre, D., Beckmann, C.F., Glasser, M.F., Jenkinson, M., Miller, K.L., 

Nichols, T.E., Robinson, E.C., Salimi-Khorshidi, G., Wool- rich, M.W., Barch, D.M., 
U˘gurbil, K., Van Essen, D.C., 2013. Functional connectomics from resting-state fmri. 
Trends Cogn. Sci. (Regul. Ed.) 17, 666–682. https://doi.org/10.1016/j. 
tics.2013.09.016. URL10.1016/j.tics.2013.09.016. 

Sockeel, S., Schwartz, D., P´el´egrini-Issac, M., Benali, H., 2016. Large-scale functional 

networks identified from resting- state eeg using spatial ica. PLoS One 11, e0146845. 
https://doi.org/10.1371/journal.pone.0146845. URL10.1371/journal. 
pone.0146845. 

Sommariva, S., Sorrentino, A., Piana, M., Pizzella, V., Marzetti, L., 2017. A comparative 

study of the robustness of frequency- domain connectivity measures to finite data 
length. Brain Topogra- phy 32, 675–695. https://doi.org/10.1007/s10548-017- 
0609-4. URL10.1007/s10548-017-0609-4. 

Sorrentino, A., Piana, M., 2017. Inverse modeling for meg/eeg data. Mathematical and 

Theoretical Neuroscience: Cell. Network and Data Analysis, pp. 239–253.

Tadel, F., Baillet, S., Mosher, J.C., Pantazis, D., Leahy, R.M., 2011. Brain- storm: a user- 
friendly application for meg/eeg analysis. Computat. Intellig. Neuroscie. 1–13.
Todaro, C., Marzetti, L., Vald´es Sosa, P.A., et al., 2019. Mapping brain activity with 

electrocorticography: resolution properties and robustness of inverse solutions. Brain 
Topogr. 32, 583–598. https://doi.org/10.1007/s10548-018-0623-1.

Vallarino, E., Sorrentino, A., Piana, M., Sommariva, S., 2021. The role of spectral 

complexity in connectivity estimation. Axioms 10, 35. https://doi.org/10.3390/ 
axioms10010035. URL10.3390/axioms10010035. 

Vallarino, E., Hincapi´e, A.S., Jerbi, K., Leahy, R.M., Pascarella, A., Sor- rentino, A., 

Sommariva, S., 2023. Tuning minimum-norm regularization parameters for optimal 
MEG connectivity estimation. Neuroimage 281, 120356. https://doi.org/10.1016/j. 
neuroimage.2023.120356. URL10.1016/j.neuroimage.2023.120356. 

Wens, V., Marty, B., Mary, A., Bourguignon, M., de Beeck, M.O., Gold- man, S., 

Bogaert, P.V., Peigneux, P., Ti`ege, X.D., 2015. A geometric correction scheme for 
spatial leakage effects in MEG/EEG seed-based functional connectivity mapping. 

F. Leone et al.                                                                                                                                                                                                                                   

NeuroImage 303 (2024) 120896 

Hum. Brain Mapp. 36, 4604–4621. https://doi.org/10.1002/hbm.22943. 
URL10.1002/hbm.22943. 

Winter, W.R., Nunez, P.L., Ding, J., Srinivasan, R., 2007. Comparison of the effect of 
volume conduction on EEG coherence with the effect of field spread on MEG 
coherence. Stat. Med. 26 (21), 3946–3957.

Yao, J., Dewald, J.P., 2005. Evaluation of different cortical source localization methods 
using simulated and experimental EEG data. Neuroimage 25, 369–382. https://doi. 
org/10.1016/j.neuroimage.2004.11.036. URL10.1016/j.neuroimage.2004.11.036. 

12 

