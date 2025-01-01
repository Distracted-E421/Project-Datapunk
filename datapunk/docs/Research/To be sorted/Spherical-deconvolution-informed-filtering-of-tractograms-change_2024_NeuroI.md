NeuroImage 303 (2024) 120904 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Spherical-deconvolution informed filtering of tractograms changes 
laterality of structural connectome

Yifei He a, Yoonmi Hong b,*, Ye Wu a,*
a School of Computer Science and Technology, Nanjing University of Science and Technology, Nanjing, China
b Department of Psychiatry, University of North Carolina at Chapel Hill, Chapel Hill, USA

A R T I C L E  I N F O

A B S T R A C T

Keywords:
Brain laterality
Diffusion MRI
Tractography filtering
Brain connectome

Diffusion MRI-driven tractography, a non-invasive technique that reveals how the brain is connected, is widely 
used in brain lateralization studies. To improve the accuracy of tractography in showing the underlying anatomy 
of the brain, various tractography filtering methods were applied to reduce false positives. Based on different 
algorithms,  tractography  filtering  methods  are  able  to  identify  the  fibers  most  consistent  with  the  original 
diffusion data while removing fibers that do not align with the original signals, ensuring the tractograms are as 
biologically accurate as possible. However, the impact of tractography filtering on the lateralization of the brain 
connectome remains unclear. This study aims to investigate the relationship between fiber filtering and laterality 
changes  in  brain  structural  connectivity.  Three  typical  tracking  algorithms  were  used  to  construct  the  raw 
tractography, and two popular fiber filtering methods(SIFT and SIFT2) were employed to filter the tractography 
across a range of parameters. Laterality indices were computed for six popular biological features, including four 
microstructural measures (AD, FA, RD, and T1/T2 ratio) and two structural features (fiber length and connec-
tivity)  for  each  brain  region.  The  results  revealed  that  tractography  filtering  may  cause  significant  laterality 
changes  in  more  than  10%  of  connections,  up  to  25%  for  probabilistic  tracking,  and  deterministic  tracking 
exhibited minimal laterality changes compared to probabilistic tracking, experiencing only about 6%. Except for 
tracking  algorithms,  different  fiber  filtering  methods,  along  with  the  various  biological  features  themselves, 
displayed more variable patterns of laterality change. In conclusion, this study provides valuable insights into the 
intricate  relationship  between  fiber  filtering  and  laterality  changes  in  brain  structural  connectivity.  These 
findings can be used to develop improved tractography filtering methods, ultimately leading to more robust and 
reliable measurements of brain asymmetry in lateralization studies.

1. Introduction

Diffusion MRI (dMRI) is a non-invasive technique that utilizes the 
diffusion  of  water  molecules  to  generate  the  mapping  of  structural 
connections  in  the  human  brain  (Basser  et  al.,  2000).  Based  on  data 
collected with dMRI, tractography can illustrate the fiber tracts in the 
human  brain’s  white  matter  and  reconstruct  the  human  connectome, 
allowing neuroscientists to do quantitative analysis of neuronal geom-
etry and know more about the anatomical structure of white matter. As 
the only methodology to reconstruct brain fiber tracts in vivo currently, 
dMRI  has  been  widely  used  to  study  the  inner structural  connections 
within  the brain and has been playing  a significant role in fields like 
neuropsychology, oncology, disease detection, and assessment (Mueller 
et al., 2015; Baliyan et al., 2016). However, due to technical limitations, 

dMRI  still  faces  several  challenges.  First,  various  kinds  of  deviations 
could occur during the construction of tractograms, such as curvature 
overshoot  bias,  termination  bias  and  connection  density  bias  (Zhang 
et al., 2022). Second, a potential challenge arises from the variability in 
the number of fiber bundles generated from tractography. It ranges from 
10  million  to  100  million  fibers  per  subject,  leading  to  uncertainty 
during analysis. Third, during the process of reconstruction, plenty of 
false positive fibers are typically generated. At the same time, long-range 
connections tend to be incomplete and inaccurate for several reasons, 
such as the over-definition of longer streamlines and different selections 
of fiber orientation, reducing the specificity of the constructed tractog-
raphy.  Most  studies  have  managed  to  optimize  dMRI-based  fiber 
tracking  to  obtain  better  construction  results,  typically  tuning  the  al-
gorithm parameters in a heuristic way (Gutierrez et al., 2020).

* Corresponding authors.

E-mail addresses: yoonmi_hong@med.unc.edu (Y. Hong), dr.yewu@outlook.com (Y. Wu). 

https://doi.org/10.1016/j.neuroimage.2024.120904
Received 30 July 2024; Received in revised form 22 October 2024; Accepted 23 October 2024  
Available online 28 October 2024 
1053-8119/© 2024 The Authors. Published by Elsevier Inc. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ). 

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

An effective way to improve the accuracy of construction results is to 
apply  tractography  filtering  methods.  These  methods  enable  the 
reduction of the number of generated fiber bundles and eliminate false 
positive  fiber  tracts.  Different  tractography  filtering  techniques  have 
been  designed  to  address  the  problem  of  false  positive  biases  and 
enhance the specificity of tractography. By processing the raw data from 
tractography through these filtering methods, the tractogram becomes 
more  accurate  and  can  reveal  the  underlying  biological  connections 
more precisely. This striking balance between specificity and sensitivity 
is crucial in obtaining reliable results. Linear fascicle evaluation (LiFE) 
(Pestilli et al., 2014) compares the measured and predicted streamline 
results to compute the estimation error. Convex optimization modeling 
for  microstructure  informed  tractography  (COMMIT)  (Daducci  et  al., 
2015) has used some efficient algorithms from the global convex opti-
mization problem area to solve the reconstruction biases problem, dig-
ging out the adequate volume of each streamline to best fit the collected 
signal from dMRI. COMMIT2 (Schiavi et al., 2020) extends the COMMIT 
and tries to build a connectome with a more accurate axon density. This 
study  is  keen  on  improving  the  specificity  during  reconstruction, 
showing a distinguished performance on only keeping the truly existing 
fiber  bundles.  Recently,  spherical-deconvolution-informed  filtering  of 
tractograms (SIFT) (Smith et al., 2013) managed to select a subset of 
streamlines most consistent with the original diffusion signal, reducing 
reconstruction biases to a great extent. SIFT210, as an improved alter-
native based on SIFT, aims to make the solution more logically direct 
and  computationally  efficient.  Instead  of  decreasing  the  number  of 
streamlines oriented by the estimated fiber densities used in SIFT, SIFT2 
utilizes  several  specific  parameters 
the  effective 
cross-sectional  area  for  each  streamline  to  match  the  estimated  fiber 
volumes best. Some novel tractography filtering methods also have been 
developed in recent years. Battocchio et al. (2021) exploited the position 
and shape information of the input tractography to improve the recon-
struction  results,  achieving  higher  spatial  coverage  and  fewer  invalid 
bundles.  Sairanen  et  al.  (2022) introduced  an  evolved  version  of 
COMMIT to reduce the impact of motion artifacts using outlier infor-
mation.  Gabusi  et  al.  (2024) developed  a  new  method  called  blurred 
streamlines to remove redundant streamlines and decrease the compu-
tational  time  of  filtering.  Legarreta  et  al.  (2021) built  a  tractography 
filtering method named FINTA using an auto-encoder to learn the robust 
representation  of  structural  connectomes  in  an  unsupervised  way. 
Tractography filtering, as a promising method to optimize reconstructed 
tractography,  has  been  emphasized  and  has  been  applied  to  many 
studies  related  to  brain  structural  connectivity.  These  fiber  filtering 
methods  are  employed  in  neuroimaging  studies  to  remove  or 
down-weight streamlines that do not correspond to the diffusion signal 
and  have  also  been  widely  used  in  recent  studies  related  to  brain 
structural connectivity (Pascual-Diaz et al., 2020; Shahbodaghy et al., 
2023;  Bispo  et  al.,  2023;  Carrozzi  et  al.,  2023).  However,  to  our 
knowledge, there is no research indicating whether fiber filtering would 
influence the lateralization of brain structural connectivity.

to  optimize 

Brain  lateralization  constitutes  a  unique  biological  feature  of  the 
human brain. It denotes the inclination of certain neural functions to be 
specialized in either hemisphere of the brain. Current research on brain 
asymmetry  is  primarily focused on investigating  laterality patterns  in 
diseases and disorders (Zou and Yang, 2021a; 2021b; Li et al., 2023; Zhu 
et al., 2024; Beheshti et al., 2020; Lubben et al., 2021; Persichetti et al., 
2022).  This  is  done  to  establish  a  connection  between  lateralization 
tendency  and  clinical  symptoms,  highlighting  the  significance  of 
acquiring  accurate  lateralization  information  from  medical  images. 
Many  studies  have  aimed  to  develop  techniques  for  measuring asym-
metry  and  have  used  fiber  filtering  methods  to  mitigate  biases  from 
tractography reconstruction. For instance, Indovina et al. (2020) used 
probabilistic tractography and SIFT filtering to investigate the structural 
connectivity  patterns  of  the  human  vestibular  cortex  and  found  a 
left-lateralized  tendency  for  the  posterior  insular  cortex  and  OP2,  a 
subregion of the parietal operculum. Liu et al. (2021) used SIFT to filter 

iFOD2  and 

the  tractography  obtained  from 
identified  distinct 
left-lateralization in the neocortex and right-lateralization in the deep 
brain regions in infants during the first half-year of life. Honnedevas-
thana  Arun  et  al.  (2021) characterized  human  brain  white  matter 
asymmetry  and  its  relationship  with  diseases,  aging,  and  cognitive 
measures  using  iFOD2  and  SIFT.  At  the same  time,  Yoo et  al.  (2024)
investigated  the  relationship  between  brain  asymmetry  and  autism 
spectrum disorder using a probabilistic algorithm to build tractography 
and SIFT2 to optimize the cross-section multiplier for each streamline by 
weighting the streamlines.

As filtering methods such as SIFT and SIFT2 are widely used in recent 
research  to  demonstrate  the  underlying  biological  and  anatomical 
characteristics of brain connectome, it is essential to consider their po-
tential  effects  on  the  structural  connectivity  of  the  brain  in  future 
research.  The  effects  of  fiber  filtering  on  structural  connectome  have 
been studied previously. McColgan et al. (2018) explored the impacts of 
SIFT2  on  structural  connectome.  They  estimated  a  reduction  in  vari-
ability in the intra-subject case and among subjects, as well as an in-
crease in variability in the intra-scan case. Koch et al. (2022) evaluated 
SIFT2 and COMMIT2 and found that both filtering methods could pre-
serve the reproducibility of raw tractography but reduce the specificity 
of the original tractography. Wan (2023) et al. used deep learning to 
assess the effectiveness of COMMIT and found biases in fiber length. In 
the research conducted by Frigo et al. (2020), SIFT2 and COMMIT were 
observed to  alter the topology of the  structural connectome, both for 
pathological and healthy subjects. K¨opff et al. (K¨opff, 2020) studied the 
influence of SIFT on the structural connectomes of subjects with mild 
cognitive impairment. Results showed that the connectome was altered 
from  an  individual  scale,  which  was  also  applied  to  microstructural 
measurements. However, the filtered tractography performed better in 
deep-learning  classification  tasks.  However,  no  research  has  yet  been 
conducted to investigate the lateralization changes from filtering.

The overarching objective of our study was to evaluate the feasibility 
and practical value of tractography filtering and determine its possible 
impact  on  brain  lateralization  indices.  In  pursuit  of  this  aim,  we  un-
dertook  a  comprehensive  analysis  of  laterality  changes  under  diverse 
circumstances. We aim to establish a clear understanding of the utility 
and  effectiveness  of  tractography  filtering,  along  with  an  in-depth 
appraisal of the various filtering methods and tractography algorithms 
under review. This study investigated brain laterality as a critical factor 
in evaluating the structural similarity between filtered and raw tracto-
grams.  Our  research  has  evaluated  the  performance  of  two  widely 
recognized  filtering  solutions,  SIFT  and  SIFT2,  in  maintaining  asym-
metrical characteristics of the raw tractogram. The capability of filtering 
methods  in  maintaining  the  biological  properties  of  tractograms  was 
measured  by  comparing  the  density  of  fiber  connectivity  before  and 
after  filtering.  Our  research  has  made  two  significant  contributions. 
Firstly, it provides significant insights into the effects of filtering algo-
rithms  on  brain  asymmetry  that  has  not  been  previously  explored. 
Secondly, we  have  drawn  novel conclusions  based  on  brain laterality 
displayed in different samples that could inspire future research.

2. Materials and methods

Data acquisition. The dataset comprises 19 subjects from the WU- 
Minn HCP Young Adult 1200 Subjects dataset (Van Essen et al., 2013) 
and  36  subjects  (25  patients  and  11  control  subjects)  from  the  Brain 
Tumor  Connectomics  (BTC)  (Aerts  et  al.,  2018),  spanning  a  range  of 
gradient strengths.

For  HCP  data,  each  subject  includes  both  structural  and  diffusion 
MRI data from 3T, 7T, and a re-test sample from a 3T scanner. The 3T 
data is the primary object of interest, and 3TR is the retested 3T data 
used for reproducible analysis. The 7T images were acquired through a 
higher magnetic field strength and with a developed acquisition proto-
col.  Holding  higher  nominal  spatial  resolution  and  utilizing  three 
different algorithms to mitigate false positive fibers, 7T data has higher 

2 

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

image  quality  and  presents  more  anatomical  details  compared  to  3T 
data. In this study, 7T data is used to validate the conclusions drawn 
from 3T data due to its higher image precision. All subjects are healthy 
adults  aged  22  to  35  years  without  neuropsychiatric  or  neurological 
disorders.  Both  diffusion  and  structural  data  were  minimally  pre-
processed  with  the  Human  Connectome  Project  pipeline  (Van  Essen 
et al., 2013; Glasser et al., 2013). 

The 3T images were acquired using a 3T Siemens Skyra scanner. A 
3D MPRAGE sequence with a field of view of 224 × 244 mm was 
employed to obtain the 3T T1-weighted images (TR = 2400 ms, TE =
◦
2.14 ms, TI = 1000 ms, flip angle of 8
, BW = 210 HZ/Px), which 
were  obtained  over  7  min  and  40  s.  A  multiband  spin-echo  EPI 
sequence with a field of view of 210 × 180 mm was used to acquire 
the 3T diffusion-weighted images (TR = 5520 ms, TE = 89.5 ms, flip 
◦
, BW = 1488 Hz/Px), which were obtained over 9 min 
angle of 78
and 50 s. Diffusion-weighted scans were distributed over three shells 
with b-values of 1000 (DWI volumes = 90), 2000 (DWI volumes =
90), and 3000 (DWI volumes = 90) s/mm2.
The  7T  images  were  obtained  using  a  7T  Siemens  MAGNETOM 
scanner. The 7T T1-weighted images shared the same protocol with 
3T. The 7T diffusion images were collected using a multiband spin- 
echo  EPI  sequence  with  a  field  of  view  of  210  × 210  mm  (TR  =
◦
7000 ms, TE = 71.2 ms, flip angle of 78
, BW = 1388 HZ/Px), which 
were obtained over 9 min and 50 s. Diffusion-weighted scans were 
distributed over two shells with b-values of 1000 (DWI volumes =
64) and 2000 (DWI volumes = 64) s/mm2.

To  enrich the  diversity  of  subjects and  demonstrate  the  generaliz-
ability  of  the  conclusions,  we  used  samples  from  the  BTC  dataset  for 
analysis. The BTC dataset contains 25 patients and 11 control subjects, 
both from the pre-operative data (Aerts et al., 2018). The BTC images 
were obtained through a Siemens 3T Magnetom Trio MRI scanner. The 
T1-MPRAGE anatomic images were acquired with a field of view of 256 
◦
× 256 mm (TR = 1750 ms, TE = 4.18 ms, flip angle of 9
), which were 
obtained  over  4  min  and  5  s.  A  multishell  high-angular  resolution 
diffusion MRI scan was acquired with a field of view of 240 × 240 mm 
(TR = 8700 ms, TE = 110 ms), which was obtained over 15 min and 14 s 
and was distributed over four shells with b-values of 0, 700, 1200, and 
2800 s/mm2.

Whole-brain Tractography. The Multi Shell Multi Tissue (MSMT) 
model  parameters  were estimated  in  MRtrix3  (Tournier  et  al., 2019), 
utilizing the Dhollander method with default parameters to estimate the 
MSMT  response  function  for  each  subject.  Tractography  algorithms, 
including two typical probabilistic algorithms (iFOD1 and iFOD2) and a 
deterministic  algorithm  (DET)  (Tournier  et  al.,  2012,  2010),  were 
separately  applied  using  MRtrix3  to  generate  tractography  for  each 
subject. The First-order Integration over Fiber Orientation Distributions 
(iFOD1)  algorithm  employs  probabilistic  tractography  to  randomly 
select a direction of the fiber orientation distribution (FOD), with the 
amplitude of the FOD along that direction determining the probability of 
a  particular  direction  being  produced.  The  Second-order  Integration 
over  Fiber  Orientation  Distributions  (iFOD2)  algorithm,  an  improved 
version of iFOD1, chooses a random curve proportional to the extent of 
FOD matching at the next point. The SD_STREAM (DET) deterministic 
algorithm estimates fiber orientation from FOD, identifying the nearest 
peak using a Newton-Raphson gradient ascent algorithm to match the 
current direction of tracking best. These three tracking algorithms have 
been frequently utilized to generate tractography. During tractography 
reconstruction,  we  introduced  the  Anatomically-Constrained  Tractog-
raphy  (ACT)  technique  (Smith  et  al.,  2012),  which  utilized  the  seg-
mentation information of an anatomical contrast image saved in the 5TT 
(five-tissue-type)  format  to  build  a  tractogram  with  more  anatomical 
reliability.  Parameters  used  for  tracking  are  the  default  setting  in 
MRtrix3, which has been listed in Table 1, where MRtrix3 recommends 
the cut-off value to be 0.06 for HCP data in particular.

3 

Table 1 
Parameters used in fiber tracking algorithms.

Tracking 
algorithms

Select 
number

Min 
length

Max 
length

Cutoff

Angle

Trials

iFOD1

iFOD2

10M

10M

SD_STREAM 

10M

(DET)

2 x voxel 
size
2 x voxel 
size
2 x voxel 
size

250

250

250

0.06

0.06

0.06

◦

15

◦

45

◦

60

1K

1K

–

Biological  modeling.  Population  biological  models  have  been 
employed  to  estimate  the  volume  fractions  of  distinct  compartments 
from diffusion signals. Diffusion tensors were estimated at each voxel 
within the MRtrix3 software package using a non-linear tensor operator. 
Subsequently,  fundamental  biological  features  (microstructure  mea-
sures), such as fractional anisotropy (FA), mean diffusivity (MD), axial 
diffusivity (AD), and radial diffusivity (RD), were computed based on 
the estimated diffusion tensor. Furthermore, the study measured con-
nectivity (connection numbers divided by the sum of the two brain re-
gions’  volumes),  which  would  better  demonstrate  the  density  of 
streamlines between two regions. The mean length of streamlines be-
tween two brain regions and the T1w/T2 w Ratio were also determined. 
The  T1w/T2  w  ratio  (dividing  T1-weighted  images  by  T2-weighted 
images)  is  an  effective  index  to  quantify  the  myelin  concentration 
straightforwardly and has been frequently used for tissue microstructure 
assessment in recent research (Uddin et al., 2019).

Tractography filtering. SIFT and SIFT2 are two techniques utilized 
to process raw tractography data obtained from dMRI. These methods 
aim  to  facilitate  any  prevailing  bias  present  in  the  fiber  tracts.  SIFT 
computes  the  contribution  of  each  fiber  tract,  eliminates  multiple 
streamlines,  and  halts  the  removal  process  by  specific  termination 
conditions. In contrast, SIFT2 establishes a cross-sectional area for each 
streamline, retains the entire reconstructed tractogram, and modifies the 
cost  function  expression  of  SIFT by  introducing  a  regularization  term 
and altering the calculation of a parameter.

∑

Both SIFT and SIFT2 first calculate the track density (TD) based on 
fibers assigned to these FOD lobes, which is considered as the angular 
spread of the precise direction on the unit hemisphere for which the FOD 
amplitude is a maximum. SIFT defined the track density in the FOD lobe 
l as TDl =
s:|sl>0||sl|, where sl  is the length of streamlines attributed to 
]
FOD  lobes.  SIFT2  calculated  TD  as  TDl =
,  where  eFs 
serves  as  a  weighting  factor,  Fs  being  the  weighting  coefficient  for 
streamlines.  Then,  a  proportionality  coefficient  is  defined  to  demon-
strate the global scaling index between streamline density and FOD lobe 
integrals: 
∑
∑

[
|sl|⋅eFs

s:|sl>0|

μ =

∑

L
l=1
L
l=1

[PMl⋅FDl]
[PMl⋅TDl]

∑
L
l=1

[
PMl⋅(μ⋅TDl (cid:0) FDl)2

where L is the total number of FOD lobes in the image, FDl  and TDl  are 
the fiber density and the track density attributed to the lobe l, respec-
tively, and PMl  is the value of the processing mask (definition of which 
voxels should influence the model fit and the degree of influence from 
each of them). In SIFT2, the TDl stays are fixed TD0
l during optimization. 
]
SIFT defines loss function f =
, which can be 
utilized to quantify whether a reconstructed streamline fits the under-
lying  diffusion  data.  SIFT2  modifies  this  loss  function  f =
PMl⋅ 
[
]
freg(s)

(μ⋅TDl (cid:0) FDl)2
by  adding  a  regularization  term 
where λreg  is a user-controllable parameter (Smith et al., 2015), and A =
1
N

]
, where N is the number of streamlines.
For  both  SIFT  and  SIFT2,  we  filtered  the  tractography  with  and 
without using ACT separately to depict the influence of ACT on filtering 
results. Following are some experimental details during filtering.

[
PMl⋅FDl

∑
L
l=1

∑
L
l=1

+ A⋅λreg⋅

N
s=1

∑

]

[

2

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

In  SIFT:  (a)  N:  definition  of  the  number  of  remaining  streamlines 
after filtering; (b) R: a regularization parameter which biases towards a 
filtered reconstruction with a greater density of streamlines, defined as a 
ratio between reduction of cost function and the fractional change in the 
overall streamline density, the smaller the ratio is, the fewer streamlines 
would be kept after filtering; (c) μ: the SIFT proportionality coefficient is 
not  allowed  to  be  smaller  than  this  value.  We  take  N  as  the  primary 
variable during filtering, from 1 M to 10 M with an interval of 1 M, as it 
is  more stable than R and  presents a better  continuity in results.  The 
remaining number of streamlines is also the parameter most commonly 
used when using SIFT.

In  SIFT2:  SIFT2  itself  does  not  directly  change  the  original  track. 
Instead, it calculates each fiber’s weight. Fibers weighing more are not 
likely to be false positives and should be kept after filtering. Increasing 
weight thresholds, from 0.1 to 0.9 with an interval of 0.1, are practiced 
to remove different numbers of fibers, creating nine different groups of 
data in all. SIFT2 is practiced on the filtered track files again in the end to 
acquire  the  final  weights  of  fibers.  Then,  connectome  matrices  of 
streamlines’ number, mean length, mean inverted length and inverted 
volumes of two nodes were calculated for each sample using MRtrix3. 
The  parameters  used  for  SIFT  and  SIFT2  filtering  have  been  listed  in 
Table 2.

Structural  connectivity.  A  structural  connectome  was  generated 
based  on  dMRI  tractography.  Cortical  parcellations  and  subcortical 
segmentations  of  the  T1-weighted  images  were  estimated  with  Free-
Surfer using the automatic Desikan-Killiany (DKT) atlas. The abbrevia-
tions and full names of 42 brain regions in the DKT atlas have been listed 
in  Table  3.  We  used  the  sum  of  streamline  weights  to  compute  edge 
weights.

While diffusion tractography remains the only available tool for in 
vivo connectivity mapping in humans, it can vary in its specificity and 
sensitivity  for  tract  reconstruction  and  is  not  always  reflective  of  the 
underlying fiber density (Nielsen et al., 2013). To mitigate effects from 
motion-related  confounds  and  false  positives,  an  effective  method  is 
employed to optimize per-streamline cross-section multipliers to match 
the tractogram to fiber densities, then capture the streamline weights 
and  incorporate  them  into  this  computation  (Cacciola  et  al.,  2019). 
Weighting edges by diffusion metric in this manner is thought to provide 
an index of the microstructural integrity of the underlying white matter 
connections. In this process, the weights of the edges were calculated 
using  SIFT2.  We  calculated  structural  connectomes  with  and  without 
using  the  weight  information  separately  to  compare  the  differences. 
Structural connectivity was also conducted by revealing morphological 
measurements.  The  number  of  fibers  connecting  two  specific  regions 
and the inverted volume of regions (reciprocal of the sum of two brain 
regions’ volumes) were also calculated.

Each structural connectivity generated by biological features appears 
to be a matrix of dimensions 84 × 84, with the horizontal and vertical 
axes representing 42 regions on the left hemisphere and 42 regions on 
the  right  hemisphere,  respectively.  Every  element  in  these  matrices 
stands for a feature of fibers linking two regions (left to left or right to 
right) or just a physical characteristic of the brain regions. We calculated 
the connectivity matrix, the product of fiber number and the inverted 
volume of two regions to reveal the level of connection density between 
them.

Laterality  index.  Due  to  the  symmetrical  structure  of  the  human 

Table 2 
Parameters used in fiber filtering methods.

Filtering 
algorithms

SIFT

SIFT2

Streamline 
count

1–10M

–

Filter 
threshold

Remove 
untracked

–

0–0.9

yes

yes

ACT

yes/ 
no
yes/ 
no

4 

brain, each connection pair in the left brain can have a corresponding 
pair in the right brain. The difference in number and length between 
these  connection  pairs  could  be  used  to  quantify  the  degree  of  brain 
asymmetry. A comparison of the lateralization indices before and after 
filtering demonstrates the change in asymmetry. We use the expression 
(L1L2 (cid:0) R1R2)/(L1L2 +R1R2) to make a quantitative calculation of con-
nectomes’ laterality index (LI), which L1L2  refers to the connection be-
tween  regions  one  and  two  from  the  left  hemisphere  and  R1R2  the 
connection between the same two regions from the right hemisphere. 
Then, the asymmetry values before and after filtering are compared to 
help  us  know  whether  the  asymmetry  has  changed  due  to  filtering 
within two specific brain region pairs.

Statistical  analysis.  We  investigate  the  filtered  tractograms  with 
different variables using the raw tractogram. Each sample has 903 pairs 
of connections, each of which has a laterality index, representing the 
asymmetry  level  of  the  connection  between  the  two  brain  regions  (1 
stands  for  wholly  left-lateralized  while  (cid:0) 1  means  completely  right- 
lateralized). A paired two-tailed permutation t-test (p < 0.05) is prac-
ticed  among  the  19  samples  in  HCP  data  of  laterality  indices  of  one 
connection to check if there appears to be a significant difference in the 
overall asymmetry of the 19 subjects before and after filtering. For the 
BTC dataset, we applied the exact paired two-tailed permutation t-test (p 
< 0.05)  for  the  25  patients  and  11  control  subjects  separately.  The 
percentage of connections that have significant laterality changes was 
calculated and analyzed to demonstrate the severity of impact on whole 
brain lateralization after filtering.

3. Results

3.1. The overall changes in connectivity before and after filtering

Fiber filtering is a crucial step towards refining structural connec-
tivity. This process entails the removal of some fibers, which results in 
significant anatomical changes in the streamlined features. The overall 
processing of structural connectome and data analysis are depicted in 
Fig. 1. The streamline bundle pairs and the circular graph of the whole 
brain connectivity before and after filtering by SIFT are shown in Fig. 2, 
which  provides  a  visual  representation  of  the  effects  of  filtering.  The 
average laterality indices of all 903 connections are visualized in Fig. 3. 
The  number  of  fibers  in  each  bundle  decreases  as  more  streamlines 
undergo filtering, which is more noticeable with a higher percentage of 
filtering. For instance, when 90% of the streamlines undergo filtering, 
there are no MOFG to FG streamlines left in the right brain. The phe-
nomenon that a fiber bundle in one hemisphere is totally filtered would 
lead  to complete  bundle  pair  left-lateralization  or right-lateralization, 
which is an essential anatomical change that affects the overall struc-
tural connectivity of the brain. Three streamline bundle pairs adjacent to 
the tumor before and after filtering by SIFT2 are shown in Fig. 4.

3.2. The percentage of connections with significant laterality changes

In our study, we conducted a T-test to evaluate the extent to which 
different parameters affected the number of connections that exhibited 
significant (p < 0.05) laterality changes. Our analysis involved exam-
ining 42 regions within the brain, which were connected by 903 fibers. 
The changes in values are illustrated in Fig. 5, with different variables. 
These figures indicate that fiber filtering could lead to more than 10% of 
connections having significant changes in laterality indices. To be more 
specific,  we  compared  the  laterality  change  trend  among  different 
groups of variables, including three datasets, three tracking algorithms, 
six  biological  features,  and  conducting  ACT  and  weighting  or  not,  to 
reveal their impact on laterality changes, respectively. To be noted, we 
took  the  3T  dataset,  connectivity  (fiber  numbers/nodes  volume),  and 
iFOD1 tracking, with 5tt and weight as the default setting when making 
comparisons.  The  percentage  of  connections  whose  laterality  indices 
underwent significant changes was calculated and fitted to a curve with 

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

Table 3 
The abbreviation and the full name of 42 brain anatomical regions from the Desikan-Killiany atlas.

Abbreviation

Anatomy

Abbreviation

Anatomy

Abbreviation

Anatomy

Abbreviation

Anatomy

BSTS
CACG
CMFG
CU
EC
FG
IPG
ITG
ICG
LOG

bankssts
caudal anterior cingulate
caudal middle frontal
cuneus
entorhinal
fusiform
inferior parietal
inferior temporal
isthmus cingulate
lateral occipital

PCG
PrCG
PCU
RACG
RMFG
SFG
SPG
STG
SMG
FP

posterior cingulate
precentral
precuneus
rostral anterior cingulate
rostral middle frontal
superior frontal
superior parietal
superior temporal
supramarginal
frontal pole

LOFG
LG
MOFG
MTG
PHIG
PaCG
POP
POR
PTR
PCAL
PoCG

lateral orbitofrontal
lingual
medial orbitofrontal
middle temporal
parahippocampal
paracentral
pars opercularis
pars orbitalis
pars triangularis
peri-calcarine
postcentral

TP
TTG
IN
CER
TH
CA
PU
PA
HI
AM
AC

temporal pole
transverse temporal
insula
Cerebellum-Cortex
Thalamus
Caudate
Putamen
Pallidum
Hippocampus
Amygdala
Accumbens-area

Fig. 1. The overall pipeline of the experiment and data analysis. Three tracking algorithms were used to construct the raw tractography from dMRI, and two fiber 
filtering  methods,  SIFT  and SIFT2, were employed  to  filter the tractography.  Laterality indices were  computed for six  biological features,  including four micro-
structural measures (AD, FA, RD, and T1/T2 ratio) and two structural features (fiber length and connectivity) for each brain region.

a third-order polynomial along the filtering parameters.

First, we compared the results between three datasets - 3T, 3TR, and 
7T - to show the influence of the accuracy of dMRI images. We found 
that for SIFT, different datasets did not have a significant impact on the 
proportion of changes in laterality. However, for SIFT2, as the number of 
filtered  fibers  increased,  the  laterality  indices  of  higher  precision  7T 
images  underwent  more  notable  changes.  These  findings  suggest  that 
the accuracy of dMRI images can have an impact on the results of studies 
that rely on tractography algorithms to some extent. At the same time, 
the laterality change trend was also depicted for BTC datasets in Fig. 6. 
The  percentages  of  connections  with  significant  laterality  changes  in 
patients and control subjects were calculated separately. Compared to 
HCP,  the  BTC  dataset  showed  less  significant  laterality  changes  after 
filtering. For most biological features, the BTC dataset showed around 

7% of connections to have significant laterality changes. However, the 
laterality  of  connectivity  was  more  likely  to  be  significantly  changed 
after filtering (around 10%). To be noted, the curve of control subjects in 
connectivity was different from others, which showed more significant 
laterality  changes  with  smaller  SIFT2  thresholds  (0.2  and  0.3).  These 
findings  demonstrated  that  different  datasets  or  different  acquisition 
protocols  may  produce  significant  changes  in  the  sensitivity  of  the 
lateralization of brain structural connectivity to fiber filtering.

Second, we investigated different tracking algorithms to identify any 
laterality changes that may occur after filtering. As depicted in Fig. 5(b), 
we found that the deterministic algorithm (DET) was the most effective 
in  producing  robust  results  with  minimal  laterality  changes,  showing 
only  5%  of  laterality  changes  after  filtering.  In  comparison,  the  two 
probabilistic algorithms (iFOD1 and iFOD2) had a significantly higher 

5 

​
​
​
​
Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

Fig. 2. The streamlines of four bundle pairs (MOFG to FG, MOFG to LOG, MOFG to PHIG, and MOFG to TH) and overall brain connectivity of the raw tractogram of 
one representative subject from the HCP dataset, 50% filtered tractogram and 90% filtered tractogram, tracked by iFOD2 and filtered by SIFT.

Fig. 3. The average value of the laterality index between two brain regions of the raw tractogram, 50% filtered tractogram, and 90% filtered tractogram, respec-
tively, tracked by iFOD1 and filtered by SIFT.

percentage of laterality changes, with DET showing only one-third of the 
laterality changes of iFOD1 and iFOD2. Additionally, DET was also more 
consistent and stable across various filtering parameters. Our findings 
also showed that the SIFT2 algorithm had a higher likelihood of later-
ality  changes  when  more  fibers  were  removed,  whereas  SIFT  did  not 
exhibit  this  behavior.  In  SIFT,  when  we  kept  90%  of  the  streamlines 
(with  10%  filtered),  we  found  most  laterality  changes  occurred  in 
connections.

Third, in order to gain a thorough understanding of the impact of 
filtering methods on different biological features, a detailed investiga-
tion was conducted to evaluate the laterality change trends of six distinct 
features. A comprehensive analysis was carried out to compare the lat-
erality change trends of each feature individually, shown in Fig. 5(c), 
and  the  microstructural  measures  were  sampled  to  the  tractography 
with all streamlines connected to region pars-opercularis (POP) before 
and after SIFT2 filtering as shown in Fig. 7. The six features exhibited a 

6 

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

Fig. 4. The fiber streamlines of three bundle pairs adjacent to the tumor (PoCG to PrCG, SMG to MTG, and PrCG to SMG) of the raw tractogram of one representative 
patient  subject  from  the BTC dataset,  and filtered  tractograms using  SIFT2, the  threshold being  0.5  and 0.9 respectively.  The 3d modeling  of  the tumor  is also 
visualized among the fiber streamlines.

Fig. 5. Change in the percentage of laterally significantly altered brain regions with the percentage of retained fiber count after SIFT and SIFT2 filtering: (a) 3T, 3TR, 
and  7T  datasets.  (b)  DET  (SD_STREAM),  iFOD1,  and  iFOD2  tracking  algorithms.  (c)  Six  curves  represent  AD,  RD,  FA,  T1/T2  ratio,  connectivity,  and  length  of 
connection,  respectively.  (d)  Four  curves  represent  respectively  filtering  with  ACT  and  weights,  without  ACT,  without  weights,  and  both  ACT  and  weights, 
respectively. iFOD1 algorithm generates the first-column tractography and the second column by the DET(SD_STREAM) algorithm. Each curve is from a fitted line for 
the color-corresponding points with third-degree polynomial thresholds.

generally consistent trend in their curves, with some subtle variations 
between them. Specifically, it was observed that the radial diffusivity 
(RD) and connectivity of connections demonstrated a higher likelihood 
of  experiencing  changes  in  laterality  indices  compared  to  the  other 
features. These findings indicate that the RD and connectivity of con-
nections  may  be  more  sensitive  to  the  filtering  methods  employed, 
which  could  have  significant  implications  for  further  research  in  this 
field.

3.3. Study on the possible influence of ACT and weight files during 
filtering

To better understand the effects of ACT and weighting in filtering 
and their influence on laterality changes, we compared their percentage 
of laterally changed connections as well. The fitted curve of laterality 
changes’ percentage has been shown in Fig. 5(d), and the fiber bundles 
filtered  with  and  without  ACT  have  been  depicted  in  Fig.  8.  The 

7 

weighting algorithm did not have an impact on the number of fibers in 
the filtered tractogram. Still, we only looked at the biological feature 
values, so we did not depict the visualization result of weighting. In the 
connectome  analysis  using  the  probabilistic  algorithm  iFOD1,  it  was 
observed  that  the  results  obtained  without  taking  into  account  the 
edges’ weighting were less likely to undergo laterality alterations. This 
finding was more pronounced in the case of SIFT2. However, the dif-
ference  in  the  results  obtained  using  the  deterministic  algorithm  was 
relatively  small.  When  it  comes  to  using  or  not  using  ACT  or  edge 
weighting in SIFT, no significant difference was observed. On the con-
trary, in SIFT2, the use of edge weighting could influence the trend of 
lateralization  change,  making  it  more  closely  related  to  the  filtering 
results than in SIFT. Thus, it becomes essential to consider the use of 
edge  weighting  in  SIFT2  when  analyzing  the  connectome  to  achieve 
more accurate lateralization results.

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

Fig. 6. Change in the percentage of laterally significantly altered brain regions of the BTC dataset with the percentage of retained fiber count after SIFT2 filtering for 
connectivity and RD of connection.

Fig. 7. Four microstructural measures (FA, AD, RD and T1/T2 ratio) were sampled to the fiber bundles along the tract of one representative subject, of the raw 
tractogram and tractogram filtered by SIFT2 with a threshold of 0.9 and SIFT with 10% of fibers kept, containing all streamlines connected to POP.

3.4. Laterality changes the tendency of each brain region

The present investigation aimed to evaluate the impact of filtering on 
the  lateralization  of  various  brain  regions.  The  study  involved  the 
application of a T-test to 42 brain regions to explore the influence of 
filtering on their lateralization with respect to their connected regions. 
The  average  laterality  indices  of  each  brain  region  before  and  after 
filtering for connectivity and AD, with 50% of fibers filtered using SIFT, 
were shown in Fig. 9, respectively, where the names of brain regions 
whose laterality indices underwent significant changes through filtering 
were marked with ”*” when p < 0.05. The findings indicated that the 
changes in laterality indices of the regions differed significantly among 
various biological features. However, specific trends were observed. The 
regions that demonstrated significant laterality changes tended to retain 

their  original  lateralization  direction.  Specifically,  the  left-lateralized 
regions  showed  fluctuations  in  their  average  laterality  indices,  and 
their leftward bias sometimes increased. However, they were less likely 
to  become  right-lateralized  after  filtering.  Interestingly,  the  laterality 
indices of some brain regions reversed direction after filtering. The re-
sults indicated that only a subset of the regions demonstrated laterality 
change, and the direction of change differed, leading to an unobvious 
change in the average laterality index. The study also revealed that some 
regions  consistently  exhibited  more  one-sided  lateralization  but  not 
significantly,  which  resulted  in  an  apparent  difference  between  the 
average laterality index and no significant T-tested changes.

In order to better understand the changes in laterality indices within 
each region of the brain, we analyzed and determined the brain regions 
that  exhibited  significant  lateralization.  Furthermore,  we  identified 

8 

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

Fig. 8. The streamlines of two bundle pairs (MOFG to TH and MOFG to LOG) of the tractogram filtered by SIFT2 of one representative subject, with a threshold of 
0.9, with and without using ACT, respectively.

brain regions whose lateralization indices were particularly susceptible 
to  filtering. In cases where  a brain region’s  overall lateralization was 
significantly  altered  when  50% of  fibers  were  filtered from  SIFT or  a 
threshold of 0.5 was used in SIFT2 connectivity, we recognized the re-
gion’s laterality index as sensitive to filtering and included it in Table 4. 
The brain regions with “*” in Table 4 are the same as the regions marked 
with “*” in Fig. 9 (p < 0.05), and we marked brain regions with more 
significant laterality changes with “**” and “***” when p < 0.01 and p <
0.001, respectively.

In addition to connectivity, we also analyzed brain regions sensitive 
to filtering for other biological features. We found that the tendency for 
laterality  change  in  each  brain  region  could  differ  when  focusing  on 
different  biological  features,  which  meant  that  the  overall  laterality 
change of a specific brain region also depended on different biological 
features. The sensitive brain regions for AD are listed in Table 5.

4. Discussion

The present study focuses on assessing the influence of fiber filtering 
on brain structural connectivity and diffusion metrics. The study con-
ducted a series of comprehensive experiments to examine the impact of 
fiber tracking algorithms, the use of anatomically constrained tractog-
raphy (ACT), and the application of a weighting matrix in constructing 
connectomes. A t-test was employed to analyze the laterality indices of 
each connection among the 42 brain regions prior to and post-filtering to 
determine significant changes in the laterality indices of brain structural 
connectivity.  The  results  indicated  that  both  Spherical-deconvolution 
Informed Filtering of  Tractograms (SIFT) and SIFT2 led to significant 
changes in more than 10% of connections, with some parameters lead-
ing  to  changes  up  to  20%  of  connections.  Different  fiber  tracking 
methods  and  biological  features  were  observed  to  significantly  alter 
laterality due to filtering, with probabilistic algorithms resulting in more 
laterality  changes  than  deterministic  algorithms.  Moreover,  RD  and 
connectivity  were  found  to  cause  more  laterality  changes  than  other 
biological  features.  These  findings  suggest  that  the  impact  of  fiber 
filtering on brain structural connectivity and diffusion metrics should be 

carefully  considered  before  concluding  subsequent  analyses.  The  fact 
that more than 10 percent of brain region connections are possible to 
show  significant  laterality  changes  from  filtering  is  significant  for 
studies  centered  on  brain  laterality,  especially  for  those  researches 
focusing on the relationship between some disorders and the laterali-
zation pattern of some specific brain regions. Possible errors caused by 
tractography filtering could lead to inaccurate conclusions with regard 
to brain asymmetry, and some potential lateralization patterns may be 
overlooked. It is recommended that researchers employ robust methods 
for fiber tracking and carefully choose the appropriate biological fea-
tures to derive more accurate and reliable results.

Brain lateralization has been observed structurally, functionally, and 
behaviorally (Toga and  Thompson, 2003). The measurement of  later-
alization in the human brain is crucial in comprehending the functioning 
of different brain regions and the structural changes that occur during 
the  aging  process.  It  is  also  extensively  employed  in  the  study  of 
connection  abnormalities  in  brain  networks  of  neurological  diseases. 
The  laterality  of  the  connectome,  which  refers  to  the  comprehensive 
map  of  neural connections  and their  asymmetry in  the  brain, plays  a 
crucial role in various fields of neuroscience. This includes applications 
in  detecting  and  treating  psychiatric  disorders,  understanding  brain 
cognition, and informing other brain-related research (Zou and Yang, 
2021a; Herzog and Magoulas, 2021; Kong et al., 2022; Parthasarathy 
and  Bhalla,  2013;  Lai  et  al.,  2024;  Agcaoglu  et  al.,  2022;  Ambrosini 
et al., 2020; Linn et al., 2024).

Previous studies have employed large datasets to investigate various 
laterality metrics and their contributing factors. This has substantiated 
the  existence  of  brain  asymmetry  and  yielded  valuable  insights  into 
disorders.  Brain  lateralization  could  be  the  characterization  of  more 
compact connections between the cortico-cortical areas within a specific 
hemisphere than another. Various researchers have invested in the study 
of brain asymmetry or have used asymmetry as a valid biological feature 
in their studies based on brain structural connection. NJ. Herzog et al. 
(Herzog and Magoulas, 2021) proposed a method for brain asymmetry 
detection and brain asymmetry feature generation using both magnetic 
resonance  imaging  (MRI)  and  positron  emission  tomography  (PET), 

9 

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

Fig. 9. The average laterality indices(Y-axis) of all brain regions(X-axis) before and after filtering. For all 42 brain regions, the red bar is the average laterality index 
before filtering, while the yellow bar is after filtering. Bolded regions with “*” show significant laterality changes in a paired two-tailed T-test. The filtered laterality 
index and significantly altered regions would differ due to different biological features and filtering parameters we calculate. The results of AD and connectivity, 
filtered 50% fibers by SIFT, are taken as representative examples (For interpretation of the references to color in this figure legend, the reader is referred to the web 
version of this article).

aiming  to  diagnose  dementia  from  an  early  stage  using  asymmetry 
features. Propper et al. (2010) examined human language lateralization 
using diffusion tensor imaging (DTI) in conjunction with functional MRI 
(fMRI), finding that handedness lateralization and language functions 
could have some relationship with arcuate fasciculus (AF) asymmetry. 
Parker  et  al.  (2005) studied  the  lateralization  of  auditory-language 
pathways  in  the  human  brain  using  diffusion  MRI.  Indovina  et  al. 
(2020) studied  the  human  vestibular  cortex  and  their  structural  con-
nectivity pattern lateralization using dMRI images. Coghill et al. (2001)
emphasized  the  lateralization  of  somatosensory  function  using  both 
fMRI  and  structural  MRI 
that  human 
right-lateralized  mechanisms  are  essential  in  extrapersonal  and  inter-
personal information processing. Liang et al. (2021) used a functional 
connectivity-based gradient to investigate the gender difference in brain 
asymmetry and found more left lateralization in males. Maximov and 
Westlye  (2023) investigated  the  neurite  density  metrics,  which  were 
based on dMRI, and utilized asymmetry indices for evaluation. Despite a 

images.  They 

found 

substantial body of research, our understanding of human brain asym-
metry still needs to be completed. Inconsistencies across studies pose a 
challenge in reaching a definitive consensus. One significant contributor 
to this ongoing debate could be the limitations of current brain struc-
tural connectivity techniques themselves. Techniques like tractography, 
for instance, are susceptible to issues like false positives, which can lead 
to misrepresentations of the brain’s true biological structure. To mini-
mize the tractography biases as much as possible, tractography filtering 
methods are frequently used in relative studies.

A comparison of the two filtering methods revealed that the degree of 
sensitivity of the brain’s lateralization varies with different parameters 
from SIFT and SIFT2. For SIFT, regardless of the number of filtered fi-
bers,  over  10%  of  connections  exhibited  a  significant  change  in  the 
laterality index. Interestingly, a smaller number of filtered fibers could 
lead to more laterality changes. In comparison to SIFT, the parameter of 
SIFT2, which is the threshold of weights of fiber pathways to determine 
whether or not the fiber tract should be removed, is positively associated 

10 

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

Table 4 
Brain regions whose laterality indices for connectivity are most sensitive to filtering use two-tailed T-tests and one-tailed T-tests from the left and right sides separately. 
The left part is from SIFT, when 5 M fibers are kept after filtering. The right part is from SIFT2, taking a threshold of 0.5. Regions with significant laterality changes are 
marked with “*”  when p < 0.05 and are marked with “**”  and “***”  when p < 0.01 and p < 0.001, respectively. The darker color of the table represents more 
significance.

Table 5 
Brain regions whose laterality indices for AD are most sensitive to filtering use two-tailed T-tests and one-tailed T-tests from the left and right sides separately. The left 
part is from SIFT, when 5 M fibers are kept after filtering. The right part is from SIFT2, taking a threshold of 0.5. Regions with significant laterality changes are marked 
with “*” when p < 0.05 and are marked with “**” and “***” when p < 0.01 and p < 0.001, respectively. The darker color of the table represents more significance.

with the degree of lateralization change. This indicates that the more 
streamlines  are  removed,  the  greater  the  degree  of  lateralization 
changes  will  occur.  However,  the  research  indicates  that  when  the 
threshold reaches a certain level, around 0.5, the laterality changes will 

no  longer  continue  to  increase  accordingly  but  will  remain  relatively 
stable. Using SIFT2 with a smaller threshold(<0.5) when trying to filter 
fewer fibers while using SIFT to filter more fibers(more than 50%) would 
be  a  relatively  better  option  to  avoid  laterality  changes  from 

11 

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

tractography filtering as much as possible.

The  experiments  were  conducted  on  two  different  datasets:  HCP 
(Van Essen et al., 2013) and BTC (Aerts et al., 2018). HCP is a classical 
dataset  commonly  used  in  the  neuroscience  area,  and  BTC  is  a  com-
plementary  dataset  composed  of  scans  on  tumor  patients  and  control 
subjects. BTC dataset was included for the following two reasons. First, 
as dMRI-based tractography has been widely used in studies focusing on 
tumors and neurosurgery (Kamagata et al., 2024; Almairac et al., 2023; 
Yang et al., 2021; Mahmoodi et al., 2023), dMRI and tractography were 
also employed to compare the structural network topology of the pa-
tients and the control subjects, highlighting the necessity of extending 
dMRI-based research to tumor patient samples. Second, compared with 
patients with neurodegenerative diseases, the structural and spatial or-
ganization of white matter fibers in tumor patients may differ more from 
those in control subjects due to the presence of tumors. The great dif-
ference in white matter structure between tumor patients and healthy 
samples creates uncertainty and challenges in the measurement of lat-
erality, which is our primary concern compared to neurodegenerative 
samples.  The  inclusion  of  tumor  subjects  can  both  enrich  our  sample 
diversity and enhance the reliability of the findings.

This  study  demonstrates  that  applying  tractography  filtering  can 
bring about significant laterality changes to the structural connectome. 
It is essential to emphasize the accuracy of reconstructed tractography 
due  to  the  need  for  ground  truth  in  brain  lateralization  studies.  Re-
searchers  have  been  grappling  with  the  challenges  and  limitations  of 
tractography, such as the high incidence of false positives and the un-
derestimation  of  the  connectivity  strength  for  long-range  connections 
(Kong  et  al., 2022;  Yeh et  al.,  2021). Our findings  indicate that fiber 
filtering  may  eliminate  all  streamlines  of  a  bundle  from  a  particular 
hemisphere, causing complete left or right lateralization. Additionally, 
short streamlines  are more prone  to filtering than longer  connections 
(Sarwar et al., 2023), leading to more significant laterality changes in 
some shorter connections.

The study also compared deterministic tracking with two probabi-
listic  tracking  algorithms  and  found  that  the  deterministic  algorithm 
underwent 60% fewer laterality changes than the other two. This was 
because streamlines in deterministic tractography are determined based 
on  a  fixed  direction  for  each  voxel.  In  contrast,  in  probabilistic  trac-
tography, the streamline is built using the randomly selected orientation 
distribution  of  each  voxel.  While  probabilistic  tracking  is  generally 
regarded  as  superior  in  yielding  individual  white  matter  fascicles 
(Descoteaux et al., 2009), deterministic tracking outperforms probabi-
listic tracking in reconstructing ground truth with fewer false-positive 
connections.  It  is  less  prone  to  false  positives,  albeit  with  a  more 
extended  computation  time  (Sarwar  et  al.,  2019;  Maier-Hein  et  al., 
2017;  Fitzpatrick  et  al.,  2024).  Both  algorithms  showed  varying  per-
formance in different tasks (Joshi et al., 2024; Tsolaki et al., 2024), and 
our study found that deterministic tracking underwent much less sig-
nificant  changes  in  the  lateralization  of  tractography  after  filtering, 
supporting its better stability. We tend to recommend deterministic fiber 
tracking when  stable and  robust lateralization metrics are  needed for 
analysis.

Moreover, we focused on specific brain regions and the links between 
them to identify any specific patterns. We found that most brain regions 
did not show significant changes in asymmetry after filtering. However, 
there  were  still  some  specific  regions,  such  as  MOFG  and  PA,  whose 
lateralization was extremely sensitive to filtering. Previous studies on 
brain  asymmetry  have  highlighted  the  lateralized  feature  of  these  re-
gions,  and  our  findings  support  these  conclusions  (Ambrosini  et  al., 
2020; Wise et al., 1999; Kann et al., 2016; Nemati et al., 2023; Wu et al., 
2022; Naghibi et al., 2024). For instance, fMRI studies have shown that 
the  region  MOFG  is  more  left-lateralized  and  CACG  is  more 
right-lateralized, consistent with the trend of laterality changes found in 
SIFT  and  SIFT243.  Another  study  using  SIFT  for  filtering  on  the  trac-
tography of the pallidum found significant left lateralization in the oc-
cipital cluster (Cacciola et al., 2019), further supporting our findings. 

These findings provide evidence that SIFT and SIFT2 filtering methods 
effectively refine the anatomical features of raw tractography, promot-
ing better alignment with the diffusion model while partially preserving 
subject-specific features.

The  present  research  employs  the  SIFT  (Smith  et  al.,  2013)  and 
SIFT210 for tractography filtering and laterality change analysis. Despite 
exhibiting distinct patterns in laterality changes, both SIFT and SIFT2 
filtering methods significantly affect the laterality index. The possibility 
of laterality changes due to fiber filtering is also likely to increase with 
the use of filtering methods such as the Connectivity Informatics Tech-
nology  for  Imaging  (COMMIT)  (Daducci  et  al.,  2015)  and  the  Linear 
Fascicle Evaluation (LiFE) (Pestilli et al., 2014), particularly when large 
numbers of fibers are being filtered. The asymmetry of the brain renders 
some  connection  bundles  with  fewer  fiber  streamlines  than  their 
mirrored  bundles  in  the  other  hemisphere,  and  filtering  is  likely  to 
remove streamlines from them, exacerbating the asymmetry. The study 
finds that different filtering techniques can lead to varying degrees and 
trends  of  laterality  changes  in  brain  connectivity.  The  percentage  of 
laterally changed connections resulting from SIFT2 increased gradually 
with more filtered fibers. However, even when only 10% of fibers were 
filtered using SIFT, the filtering led to more than 15% of connections 
exhibiting significant laterality changes. This contrast can be attributed 
to the differences in the methodology of SIFT and SIFT2. By computing 
the fiber weights of the whole brain tractography rather than directly 
removing streamlines, SIFT2 may lead to a smoother curve in laterality 
changes.

The  overall  lateralization  of  some  specific  brain  regions  has 
remarkably changed after filtering (Tables 4 and 5). Some of these brain 
regions’  laterality features  were transformed  to match  better  the bio-
logical features mentioned in previous studies, which means that fiber 
filtering  improves  the  tractography  to  demonstrate  their  underlying 
biological  characteristics  to  some  extent.  However,  this  improvement 
does not apply to every brain region with significant laterality change, 
and  the  brain  regions  with  laterality  changes  also  vary  for  SIFT  and 
SIFT2. Given the unclear influence of filtering on connectome laterality 
and the absence of general filtering rules, caution is required when using 
these methods in brain asymmetry studies.

The insights gained from this study offer valuable guidance for future 
research utilizing fiber filtering methods. Although we cannot control 
the laterality changes from filtering, more suitable parameters can be 
applied to avoid consistent changes in laterality indices. The severity of 
the  impact  of  SIFT2  on  brain  structural  connectivity  is  likely  to  be 
positively correlated with the number of filtered fibers (a more signifi-
cant weight threshold in SIFT2 leads to more filtered fibers). The use of 
SIFT for fiber filtering is likely to result in more than 10% of laterality 
changes, regardless of the number of filtered streamlines. The usage of 
fiber weighting during connectome generation could lead to more lat-
erality changes.

At the same time, the findings of this study could also inspire future 
research  on  tractography  reconstruction.  Tractography  techniques, 
along with tractography filtering methods, have been applied to study 
the brain’s structural connectivity in health and disease more and more 
frequently, making it necessary for researchers to take the robustness of 
these fiber tracking methods in the face of fiber filtering into consider-
ation.  Significant  changes  from  tractography  filtering  in  biological 
measurements,  such  as  laterality  indices,  node  degree(the  number  of 
direct connections from one brain region to other brain regions), and 
modularity(the degree to which a brain region network can be divided 
into  distinct  modules  or  communities),  reflect  that  the  reconstructed 
tractograms are mainly unstable. As a result, different data processing 
methods may affect the results of the analysis of biomarkers, leading to 
ambiguous or even erroneous findings. Recent research has been paying 
more attention to the robustness and stability of tractograms (Meesters 
et al., 2023; Forsting et al., 2022; Reid et al., 2020; Gruen et al., 2023). 
Future fiber tracking algorithms should aim to improve the stability of 
tractograms  across  different  post-processing  pipelines,  thus  ensuring 

12 

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

correct biometrics analysis.

This  study has conducted a series of  experiments, but it has some 
limitations  that  need  to  be  addressed.  First  and  foremost,  we  have 
analyzed  a  relatively  small  sample  size  of  19  subjects.  For  these  19 
subjects, more than 10% of the connections showed significant overall 
laterality changes detected by a paired T-test after filtering with SIFT 
filtering and probabilistic tracking. However, it is essential to note that 
this impact may vary on an individual scale. We have used a T-test to 
detect any significant laterality change for one connection in 19 samples 
before  and  after  tractography  filtering.  However,  we  have  conducted 
this test on a 19-subject scale instead of an individual scale. To obtain 
more conclusive results, a larger sample size is necessary. This study did 
not use any multiple comparisons control. We tried to figure out any 
significant laterality change from filtering for each connection, regard-
less of the number of brain regions. However, the multiple comparison 
controlled results were highly related to the number of t-tests and could 
lead  to  false  negatives  and  biases  (Barnett  et  al.,  2022;  Lazic,  2023). 
Secondly, while SIFT and SIFT2 are filtering methods that influence the 
laterality indices, the effects of other fiber filtering methods on the lat-
erality indices still need to be clarified. As SIFT and SIFT2 have shown 
different trends in laterality changes across filtering parameters, other 
tractography filtering methods such as COMMIT and COMMIT2 could 
also 
laterality  changes.  The 
laterality-changing trend for other filtering methods remains uncertain 
at the current stage.

in  varying  patterns  of 

result 

However, based on the conclusions drawn from SIFT and SIFT2, the 
impact of other fiber filtering methods on the laterality indices would 
also be between 10% and 25% of the total number of region connections. 
Thirdly,  we  need  to  incorporate  more  tracking  algorithms  into  our 
research. In this study, we have used SD_STREAM to represent deter-
ministic tractography and iFOD1 and iFOD2 to represent probabilistic 
tractography. However, other new tracking algorithms should also be 
taken  into  account,  such  as  parallel  transport  tractography  (Aydogan 
and Shi, 2021), probabilistic tracking for U-fibers (Nie and Shi, 2022), 
and active cortex tractography (Wu et al., 2021). We have found that 
there  were  significant  variations  in  the  percentage  of  significantly 
laterally  changed  connections  between  deterministic  tracking  and 
probabilistic  tracking.  The  deterministic  tracking  algorithm  demon-
strated  much  fewer  laterality  changes  than  the  probabilistic  tracking 
algorithms.  The  two  probabilistic  tracking  algorithms  showed  similar 
patterns in laterality changes. However, we need to investigate whether 
this finding could be extended to other deterministic and probabilistic 
algorithms. Finally, the research about laterality change for each brain 
region is also based on the 42 brain regions obtained from the DKT atlas. 
However, the application of other parcellations, such as Brodmann and 
Kleist brain parcellations (Pijnenburg et al., 2021), can lead to different 
results.  A  more  detailed  delineation  of  brain  regions  may  help  re-
searchers  probe  exactly  which  fiber  bundles  show  more  laterality 
changes through tractography filtering.

At the same time, some unclear issues still exist in this study. Results 
showed  that the  filtered tractogram  underwent significant  changes in 
laterality indices, which was caused by the filtered fibers. However, it 
was difficult to tell the composition of the filtered tractogram, and which 
part of the filtered tractogram changed the laterality index of the brain 
connectivity. We believed that the filtered tractogram was a mixture of 
both false positive fibers and real fibers, in which the true positive fibers 
might account for a more significant portion. Tractography filtering was 
used  not  only  for  eliminating  false  positives  but  also  to  reduce  the 
number of streamlines, let alone this study, which had a relatively large 
initial fiber number. The precision of tractography filtering, or SIFT and 
SIFT2,  still  needs  to  be  further  examined  and  improved  (Hain  et  al., 
2023; Smith et al., 2022) . Although the effects of tractography filtering 
methods,  including  SIFT,  SIFT2,  and  other  filtering  such  as  LiFE, 
COMMIT,  COMMIT2  and  some  recent  filtering  methods,  had  been 
assessed by previous studies, there still is an open challenge in how to 
evaluate the performance across the methods in clinical application.

13 

This study provides valuable insights into future research on brain 
asymmetry,  notwithstanding  its  limitations.  The  study  found  that  the 
deterministic tracking algorithm demonstrated fewer changes in later-
ality indices after filtering compared to probabilistic algorithms, indi-
cating that it is more stable in the trend of laterality change. With SIFT 
filtering,  the  percentage  of  laterally  changed  connections  remained 
consistent regardless of the number of filtered fibers. On the other hand, 
with SIFT2 filtering, the number of filtered fibers positively correlated 
with the severity of laterality changes. Notably, a higher threshold in 
SIFT2  would  result  in  more  fibers  being  filtered,  leading  to  a  higher 
percentage of connections with significant laterality change when the 
threshold is lower than 0.5. In contrast, when the threshold is above 0.5, 
the percentage tends to be more stable. The study found that ACT had no 
distinct influence on laterality change during the study. However, using 
the  weight  of  streamlines  to  optimize  connectome  structural  connec-
tivity may have an impact on the trend of laterality changes for different 
biological  features,  which  requires  further  attention.  These  findings 
suggest  that  future  research  related  to  brain  asymmetry  should  use 
appropriate algorithms and parameters to calculate the laterality indices 
of structural connectomes. Given fiber filtering’s significant impact on 
connectome  lateralization,  future  researchers  must  be  mindful  of  this 
effect. Different filtering methods and varying parameters can lead to 
changes  in  laterality  indices.  Therefore,  it  is  essential  to  apply  these 
methods  with  care  and  appropriate  parameters  to  avoid  constant 
changes in connectome lateralization.

5. Conclusion

Tractography  is  a  way  to  investigate  the  connections  in  the  brain 
without being invasive. It helps to understand how the brain is wired 
and which side of the brain is more active. However, it is important to 
acknowledge limitations like the presence of false positives, which can 
introduce inaccuracies in the results. While filtering methods have been 
proposed to address these limitations, a clearer understanding of their 
impact on the results is necessary. This study investigates how filtering 
can change the results of brain connectivity and lateralization. To this 
end, the study utilized the impact of different datasets, tracking algo-
rithms,  optimization  methods,  and  microstructural  measures.  The  re-
sults show that filtering can have a significant effect on the lateralization 
of the brain’s connections. Still, the extent of this change depends on the 
tracking  algorithm  and  microstructural  measure  used.  This  research 
provides  new  insights  into  the  relationship  between  tractography 
filtering  and  changes  in  brain  connectivity.  Future  studies  should  be 
cautious  when  using  filtering  methods  to  investigate  the  brain’s  con-
nections and lateralization.

Ethics statement

The data used in this study were obtained from publicly available 
datasets, WU-Minn HCP Young Adult 1200 Subjects(https://db.humanc 
onnectome.org/) dataset and the Brain Tumor Connectomics (https://op 
enneuro.org/datasets/ds001226).  Ethical  approval  and  informed  con-
sent for data collection were handled by the original data providers. No 
new data were collected specifically for this study, and all analyses were 
conducted  in  accordance  with  the  guidelines  and  policies  set  by  the 
respective data repositories.

Data availability statement

Data used in this research was from two open-source dataset: WU- 
Minn  HCP  Young  Adult  1200  Subjects  dataset  and  the  Brain  Tumor 
Connectomics.

Code availability statement

Scripts, supporting documents, and other information necessary to 

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

implement  all  aspects  of  data  organization,  preparation,  and  analysis 
using open-source software packages. Except for special instructions in 
the paper, all tools always use default parameters. No custom code was 
instructed.

CRediT authorship contribution statement

Yifei  He:  Writing  –  original  draft,  Visualization,  Methodology, 
Investigation,  Formal  analysis.  Yoonmi  Hong:  Writing  –  review  & 
editing, Validation, Supervision, Methodology, Data curation. Ye Wu: 
Writing  –  review  &  editing,  Validation,  Supervision,  Project  adminis-
tration,  Methodology, 
curation, 
Conceptualization.

acquisition,  Data 

Funding 

Declaration of competing interest

None.

Acknowledgments

This work was supported by the National Key R&D Program of China 
(Nos. 2023YFE0118600 and 2023YFF1204800) and the National Nat-
ural Science Foundation of China (No. 62201265).

References

Aerts, H., et al., 2018. Modeling brain dynamics in brain tumor patients using the virtual 

brain. eNeuro 5, 1–22.

Agcaoglu, O., et al., 2022. Lateralization of resting-state networks in children: 

association with age, sex, handedness, intelligence quotient, and behavior. Brain 
Connect 12, 246–259.

Almairac, F., et al., 2023. Free-water correction DTI-based tractography in brain tumor 
surgery: assessment with functional and electrophysiological mapping of the white 
matter. Acta Neurochir. (Wien) 165, 1675–1681.

Ambrosini, E., Capizzi, M., Arbula, S., Vallesi, A., 2020. Right-lateralized intrinsic brain 
dynamics predict monitoring abilities. Cogn. Affect. Behav. Neurosci. 20, 294–308.
Aydogan, D.B., Shi, Y., 2021. Parallel transport tractography. IEEE Trans. Med. Imaging 

40, 635–647.

Baliyan, V., Das, C.J., Sharma, R., Gupta, A.K., 2016. Diffusion weighted imaging: 

technique and applications. World J. Radiol. 8, 785–798.

Barnett, M.J., Doroudgar, Shadi., Khosraviani, Vista., Ip, E.J, 2022. Multiple 

comparisons: to compare or not to compare, that is the question. Res. Soc. Adm. 
Pharm. 18, 2331–2334.

Basser, P.J., Pajevic, S., Pierpaoli, C., Duda, J., Aldroubi, A., 2000. In vivo fiber 

tractography using DT-MRI data. Magn. Reson. Med. 44, 625–632.

Battocchio, M., Schiavi, S., Descoteaux, M., Daducci, A., et al., 2021. Improving 
tractography accuracy using dynamic filtering. In: Gyori, N., et al. (Eds.), 
Computational Diffusion MRI. Springer International Publishing, Cham, pp. 45–54. 
https://doi.org/10.1007/978-3-030-73018-5_4.

Beheshti, I., et al., 2020. Pattern analysis of glucose metabolic brain data for 

lateralization of MRI-negative temporal lobe epilepsy. Epilepsy Res. 167, 106474.
Bispo, D.D.D.C., et al., 2023. Altered structural connectivity in olfactory disfunction after 

mild COVID-19 using probabilistic tractography. Sci. Rep. 13, 12886.

Cacciola, A., et al., 2019. Structural connectivity-based topography of the human globus 
pallidus: implications for therapeutic targeting in movement disorders. Mov. Disord. 
34, 987–996.

Carrozzi, A., et al., 2023. Methods of diffusion MRI tractography for localization of the 
anterior optic pathway: a systematic review of validated methods. NeuroImage Clin. 
39, 103494.

Coghill, R.C., Gilron, I., Iadarola, M.J, 2001. Hemispheric lateralization of somatosensory 

processing. J. Neurophysiol. 85, 2602–2612.

Daducci, A., Dal Palu, A., Lemkaddem, A., Thiran, J.-P., 2015. COMMIT: convex 

optimization modeling for microstructure informed tractography. IEEE Trans. Med. 
Imaging 34, 246–257.

Descoteaux, M., Deriche, R., Kn¨osche, T., Anwander, A, 2009. Deterministic and 

probabilistic tractography based on complex fibre orientation distributions. IEEE 
Trans. Med. Imaging 28, 269–286.

Fitzpatrick, J., Hutchinson, C., Smith, M., 2024. Streamlining streamlines: probabilistic 
versus deterministic tractography algorithms in two CE marked software packages. 
Phys. Medica Eur. J. Med. Phys. 118.

Forsting, J., et al., 2022. Robustness and stability of volume-based tractography in a 

multicenter setting. NMR Biomed. 35, e4707.

Frigo, M., et al., 2020. Diffusion MRI tractography filtering techniques change the 

topology of structural connectomes. J. Neural Eng. 17, 065002.

Gabusi, I., Battocchio, M., Bosticardo, S., Schiavi, S., Daducci, A., 2024. Blurred 

streamlines: a novel representation to reduce redundancy in tractography. Med. 
Image Anal. 93, 103101.

14 

Glasser, M.F., et al., 2013. The minimal preprocessing pipelines for the human 

connectome project. NeuroImage 80, 105–124.

Gruen, J., Groeschel, S., Schultz, T, 2023. Spatially regularized low-rank tensor 
approximation for accurate and fast tractography. NeuroImage 271, 120004.
Gutierrez, C.E., et al., 2020. Optimization and validation of diffusion MRI-based fiber 

tracking with neural tracer data as a reference. Sci. Rep. 10, 21285.

Hain, A., J¨orgens, D., Moreno, R., 2023. Randomized iterative spherical-deconvolution 

informed tractogram filtering. NeuroImage 278, 120248.

Herzog, N.J., Magoulas, G.D, 2021. Brain asymmetry detection and machine learning 

classification for diagnosis of early dementia. Sensors 21, 778.

Honnedevasthana Arun, A., Connelly, A., Smith, R.E., Calamante, F, 2021. 

Characterisation of white matter asymmetries in the healthy human brain using 
diffusion MRI fixel-based analysis. NeuroImage 225, 117505.

Indovina, I., et al., 2020. Structural connectome and connectivity lateralization of the 

multimodal vestibular cortical network. NeuroImage 222, 117247.

Joshi, D., Sohn, M.H., Dewald, J.P.A., Murray, W.M., Ingo, C, 2024. Sensitivity analyses 
of probabilistic and deterministic DTI tractography methodologies for studying arm 
muscle architecture. Magn. Reson. Med. 91, 497–512.

Kamagata, K., et al., 2024. Advancements in diffusion MRI tractography for 

neurosurgery. Invest. Radiol. 59, 13–25.

Kann, S., Zhang, S., Manza, P., Leung, H.-C., Li, C.-S.R., 2016. Hemispheric lateralization 
of resting-state functional connectivity of the anterior insula: association with age, 
gender, and a novelty-seeking trait. Brain Connect 6, 724–734.

Koch, P.J., et al., 2022. Evaluating reproducibility and subject-specificity of 

microstructure-informed connectivity. NeuroImage 258, 119356.

Kong, X.-Z., et al., 2022. Mapping brain asymmetry in health and disease through the 

ENIGMA consortium. Hum. Brain Mapp 43, 167–181.

K¨opff, M. Impact of tractogram filtering and graph creation for structural connectomics 

in subjects with mild cognitive impairment. (2020).

Lai, B., et al., 2024. Atypical brain lateralization for speech processing at the sublexical 

level in autistic children revealed by fNIRS. Sci. Rep. 14, 2776.

Lazic, S.E. Why multiple hypothesis test corrections provide poor control of false 

positives in the real world. Preprint at 10.48550/arXiv.2108.04752 (2023).

Legarreta, J.H., et al., 2021. Filtering in tractography using autoencoders (FINTA). Med. 

Image Anal. 72, 102126.

Li, Q., Zhao, W., Palaniyappan, L., Guo, S., 2023. Atypical hemispheric lateralization of 
brain function and structure in autism: a comprehensive meta-analysis study. 
Psychol. Med. 53, 6702–6713.

Liang, X., et al., 2021. Sex-related human brain asymmetry in hemispheric functional 

gradients. NeuroImage 229, 117761.

Linn, W.-J., et al., 2024. Probabilistic coverage of the frontal aslant tract in young adults: 
insights into individual variability, lateralization, and language functions. Hum. 
Brain Mapp. 45, e26630.

Liu, T., et al., 2021. Diffusion MRI of the infant brain reveals unique asymmetry patterns 

during the first-half-year of development. NeuroImage 242, 118465.

Lubben, N., Ensink, E., Coetzee, G.A., Labrie, V, 2021. The enigma and implications of 
brain hemispheric asymmetry in neurodegenerative diseases. Brain Commun. 3, 
fcab211.

Mahmoodi, A.L., Landers, M.J.F., Rutten, G.-J.M., Brouwers, H.B., 2023. 

Characterization and classification of spatial white matter tract alteration patterns in 
glioma patients using magnetic resonance tractography: a systematic review and 
meta-analysis. Cancers (Basel) 15, 3631.

Maier-Hein, K.H., et al., 2017. The challenge of mapping the human connectome based 

on diffusion tractography. Nat. Commun. 8, 1349.

Maximov, I.I., Westlye, L.T., 2023. Comparison of different neurite density metrics with 

brain asymmetry evaluation. Z. Für Med. Phys. 33, 474–483.

McColgan, P. et al. Stability and sensitivity of structural connectomes: effect of 

thresholding and filtering and demonstration in neurodegeneration. bioRxiv (2018).

Meesters, S., Landers, M., Rutten, G.-J., Florack, L, 2023. Subject-specific automatic 

reconstruction of white matter tracts. J. Digit. Imaging 36, 2648–2661.

Mueller, B.A., Lim, K.O., Hemmy, L., Camchong, J, 2015. Diffusion MRI and its role in 

neuropsychology. Neuropsychol. Rev. 25, 250–271.

Naghibi, N., et al., 2024. Embodying time in the brain: a multi-dimensional 

neuroimaging meta-analysis of 95 duration processing studies. Neuropsychol. Rev. 
34, 277–298.

Nemati, S.S., Sadeghi, L., Dehghan, G., Sheibani, N., 2023. Lateralization of the 

hippocampus: a review of molecular, functional, and physiological properties in 
health and disease. Behav. Brain Res. 454, 114657.

Nie, X. & Shi, Y. Probabilistic tracking of U-fibers on the superficial white matter surface. 

bioRxiv (2022).

Nielsen, J.A., Zielinski, B.A., Ferguson, M.A., Lainhart, J.E., Anderson, J.S., 2013. An 
evaluation of the left-brain vs. right-brain hypothesis with resting state functional 
connectivity magnetic resonance imaging. PLOS One 8, e71275.

Parker, G.J.M., et al., 2005. Lateralization of ventral and dorsal auditory-language 

pathways in the human brain. NeuroImage 24, 656–666.

Parthasarathy, K., Bhalla, U.S, 2013. Laterality and symmetry in rat olfactory behavior 

and in physiology of olfactory input. J. Neurosci. 33, 5750–5760.
Pascual-Diaz, S., Varriano, F., Pineda, J., Prats-Galino, A., 2020. Structural 

characterization of the extended frontal aslant tract trajectory: a ML-validated 
laterality study in 3T and 7T. NeuroImage 222, 117260.

Persichetti, A.S., Shao, J., Gotts, S.J., Martin, A, 2022. Maladaptive laterality in cortical 
networks related to social communication in autism spectrum disorder. J. Neurosci. 
42, 9045–9052.

Pestilli, F., Yeatman, J.D., Rokem, A., Kay, K.N., Wandell, B.A, 2014. Evaluation and 
statistical inference for human connectomes. Nat. Methods 11, 1058–1063.

Y. He et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120904 

Pijnenburg, R., et al., 2021. Myelo- and cytoarchitectonic microstructural and functional 
human cortical atlases reconstructed in common MRI space. NeuroImage 239, 
118274.

Propper, R.E., et al., 2010. A combined fMRI and DTI examination of functional language 
lateralization and arcuate fasciculus structure: effects of degree versus direction of 
hand preference. Brain Cogn. 73, 85–92.

Reid, L.B., Cespedes, M.I., Pannek, K, 2020. How many streamlines are required for 

reliable probabilistic tractography? Solutions for microstructural measurements and 
neurosurgical planning. NeuroImage 211, 116646.

Sairanen, V., Ocampo-Pineda, M., Granziera, C., Schiavi, S., Daducci, A, 2022. 

Incorporating outlier information into diffusion-weighted MRI modeling for robust 
microstructural imaging and structural brain connectivity analyses. NeuroImage 
247, 118802.

Proceedings of the International Society for Magnetic Resonance in Medicine, 
p. 1670.

Tournier, J.-D., Calamante, F., Connelly, A., 2012. MRtrix: diffusion tractography in 

crossing fiber regions. Int. J. Imaging Syst. Technol. 22, 53–66.

Tsolaki, E., Kashanian, A., Chiu, K., Bari, A., Pouratian, N., 2024. Connectivity-based 
segmentation of the thalamic motor region for deep brain stimulation in essential 
tremor: a comparison of deterministic and probabilistic tractography. NeuroImage 
Clin. 41, 103587.

Uddin, M.N., Figley, T.D., Solar, K.G., Shatil, A.S., Figley, C.R., 2019. Comparisons 
between multi-component myelin water fraction, T1w/T2w ratio, and diffusion 
tensor imaging measures in healthy human brain structures. Sci. Rep. 9, 2500.
Van Essen, D.C., et al., 2013. The WU-Minn human connectome project: an overview. 

NeuroImage 80, 62–79.

Sarwar, T., et al., 2023. Evaluation of tractogram filtering methods using human-like 

Wan, X. Assessing the streamline plausibility through convex optimization for 

connectome phantoms. NeuroImage 281, 120376.

Sarwar, T., Ramamohanarao, K., Zalesky, A., 2019. Mapping connectomes with diffusion 

MRI: deterministic or probabilistic tractography? Magn. Reson. Med. 81, 
1368–1384.

Schiavi, S., et al., 2020. A new method for accurate in vivo mapping of human brain 
connections using microstructural and anatomical information. Sci. Adv. 6, 
eaba8245.

Shahbodaghy, F., et al., 2023. Symmetry differences of structural connectivity in 

multiple sclerosis and healthy state. Brain Res. Bull. 205, 110816.

Smith, R.E., Calamante, F., Gajamange, S., Kolbe, S. & Connelly, A. Modulation of white 
matter bundle connectivity in the presence of axonal truncation pathologies. bioRxiv 
(2022).

Smith, R.E., Tournier, J.-D., Calamante, F., Connelly, A., 2012. Anatomically-constrained 
tractography: improved diffusion MRI streamlines tractography through effective 
use of anatomical information. NeuroImage 62, 1924–1938.

Smith, R.E., Tournier, J.-D., Calamante, F., Connelly, A., 2013. SIFT: spherical- 
deconvolution informed filtering of tractograms. NeuroImage 67, 298–312.
Smith, R.E., Tournier, J.-D., Calamante, F., Connelly, A., 2015. SIFT2: enabling dense 
quantitative assessment of brain white matter connectivity using streamlines 
tractography. NeuroImage 119, 338–351.

Toga, A.W., Thompson, P.M., 2003. Mapping brain asymmetry. Nat. Rev. Neurosci. 4, 

37–48.

microstructure informed tractography(COMMIT) with deep learning. (2023).
Wise, R., Greene, J., Büchel, C., Scott, S., 1999. Brain regions involved in articulation. 

Lancet 353, 1057–1061.

Wu, X., et al., 2022. Dynamic changes in brain lateralization correlate with human 

cognitive performance. PLOS Biol. 20, e3001560.

Wu, Y., Hong, Y., Ahmad, S., Yap, P.Z.-T., De Bruijne, M., et al., 2021. Active cortex 

tractography. In: Medical Image Computing and Computer Assisted Intervention – 
MICCAI 2021, 12907. Springer International Publishing, Cham, pp. 467–476.
Yang, J.Y.-M., Yeh, C.-H., Poupon, C., Calamante, F., 2021. Diffusion MRI tractography 
for neurosurgery: the basics, current state, technical reliability and challenges. Phys. 
Med. Biol. 66, 15TR01.

Yeh, C.-H., Jones, D.K., Liang, X., Descoteaux, M., Connelly, A., 2021. Mapping structural 
connectivity using diffusion MRI: challenges and opportunities. J. Magn. Reson. 
Imaging 53, 1666–1682.

Yoo, S., et al., 2024. Whole-brain structural connectome asymmetry in autism. 

NeuroImage 288, 120534.

Zhang, F., et al., 2022. Quantitative mapping of the brain’s structural connectivity using 

diffusion MRI tractography: a review. NeuroImage 249, 118870.

Zhu, C., et al., 2024. Temporal dynamic synchronous functional brain network for 

schizophrenia diagnosis and lateralization analysis. IEEE Trans. Med. Imaging 1–12.
Zou, H., Yang, J., 2021a. Exploring the brain lateralization in ADHD based on variability 

of resting-state fMRI signal. J. Atten. Disord. 25, 258–264.

Tournier, J.-D., et al., 2019. MRtrix3: a fast, flexible and open software framework for 

Zou, H., Yang, J., 2021b. Temporal variability–based functional brain lateralization 

medical image processing and visualisation. NeuroImage 202, 116137.

Tournier, J.-D., Calamante, F., Connelly, A., 2010. Improved probabilistic streamlines 
tractography by 2nd order integration over fibre orientation distributions. In: 

study in ADHD. J. Atten. Disord. 25, 839–847.

15 

