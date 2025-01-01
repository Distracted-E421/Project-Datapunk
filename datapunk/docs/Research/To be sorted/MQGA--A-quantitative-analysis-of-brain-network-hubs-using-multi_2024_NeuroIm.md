NeuroImage 303 (2024) 120913 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

MQGA: A quantitative analysis of brain network hubs using multi-graph 
theoretical indices

Hongzhou Wu a, Zhenzhen Yang a, Qingquan Cao a, Pan Wang a, Bharat B. Biswal a,b,*,  
Benjamin Klugah-Brown a,*
a The Clinical Hospital of Chengdu Brain Science Institute, MOE Key Laboratory for Neuroinformation, School of Life Science and Technology, University of Electronic 
Science and Technology of China, No.2006, Xiyuan Avenue, West Hi-Tech Zone, Chengdu, Sichuan 611731, China
b Department of Biomedical Engineering, New Jersey Institute of Technology, 619 Fenster Hall, Newark, NJ 07102, USA

A R T I C L E  I N F O

A B S T R A C T

Keywords:
ADHD
Resting-state fMRI
Graph theory
Connector hub
Provincial hub

Recent advancements in large-scale network studies have shown that connector hubs and provincial hubs are 
vital for coordinating complex cognitive tasks by facilitating information transfer between and within specialized 
modules.  However, current  methods  for identifying  these  hubs  often  lack  standardized  measurement  criteria, 
hindering quantitative analysis. This study proposes a novel computational method utilizing multi-graph theo-
retical index calculations to quantitatively analyze hub attributes in brain networks. Using benchmark network, 
random simulation network (N = 100), resting fMRI data from the ADHD-200 NYU dataset (HC = 110, ADHD =
146),  and  the  Peking  dataset  (HC  = 120,  ADHD  = 83),  we  introduce  the  Multi-criteria  Quantitative  Graph 
Analysis (MQGA) method, which employs betweenness centrality, degree centrality, and participation coefficient 
to determine the connector (con) hub index and provincial (pro) hub index. The method’s accuracy, reliability, 
and  stability  were  validated  through  correlation  analysis  of  hub  indices  and  labels,  vulnerability  tests,  and 
consistency analysis across subjects. Results indicate that as network sparsity increases, the con hub index in-
creases while the pro hub index decreases, with the optimal hub node index at 4 % sparsity. Vulnerability tests 
revealed that removing con nodes had a greater impact on network integrity than removing pro nodes. Both con 
and pro exhibited stability in consistency analyses, but con was more stable. The stability of hub scores in disease 
groups was significantly lower than in the healthy control group. High con values were found in the precuneus, 
postcentral gyrus, and precentral gyrus, whereas high pro values were identified in the precentral gyrus, post-
central  gyrus,  superior  parietal  lobule,  precuneus,  and  superior  temporal  gyrus.  This  approach  enhances  the 
accuracy and sensitivity of hub node identification, facilitating precise comparisons and producing consistent, 
replicable results, advancing our understanding of brain network hub nodes, their roles in cognitive processes, 
and their implications for brain disease research.

1. Introduction

Recent large-scale network studies have demonstrated that specific 
brain regions do not operate independently when performing particular 
tasks (Bassett and Bullmore, 2017). Instead, they dynamically reorga-
nize  their  functional  patterns  to  support  various  cognitive  activities 
(Finc  et  al.,  2020).  Prior  to  and  during  task  execution,  the  brain  in-
tegrates various incoming signals from its surroundings and processes 
this complex flow of information into meaningful internal representa-
tions. Subsequently, the brain segregates this information into distinct 
modules that perform localized computations (Lord et al., 2017). This 

process can involve activating a single brain region or multiple coordi-
nating regions (Fair et al., 2007), and studies have found that a special 
class of hubs plays an essential role in this process. However, the high 
concentration of these hubs also makes them vulnerable to disconnec-
tion and dysfunction in brain diseases. Previous studies have highlighted 
the  importance  of  provincial  hubs  and  connector  hubs  in  complex 
cognitive  processes  and  their  association  with  specific  diseases 
(Bagarinao et al., 2022; Rotem-Kohavi et al., 2019; van den Heuvel and 
Sporns, 2013a; Yang et al., 2021). Consequently, increasing attention is 
being directed towards the study of hub nodes within the network.

There are two main types of hub nodes in the network: connector hub 

* Corresponding authors.

E-mail addresses: bbiswal@gmail.com (B.B. Biswal), bklugah@gmail.com (B. Klugah-Brown). 

https://doi.org/10.1016/j.neuroimage.2024.120913
Received 10 July 2024; Received in revised form 29 October 2024; Accepted 31 October 2024  
Available online 1 November 2024 
1053-8119/© 2024 The Authors. Published by Elsevier Inc. This is an open access article under the CC BY-NC-ND license ( http://creativecommons.org/licenses/by- 
nc-nd/4.0/ ). 

H. Wu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120913 

nodes  and  provincial  hub  nodes  (henceforth  termed  “con  and  pro”, 
respectively). con hubs play a key role in brain coordination and com-
plex cognitive tasks by facilitating the transfer of information between 
specialized  modules  in  higher  cognitive  processing  regions  (Bertolero 
et al., 2018). In contrast, a pro hub is a higher-degree node that primarily 
connects nodes within the same module or functional network (Hwang 
et al., 2017). However, most current methods for studying hub nodes 
rely on using one or more graph theoretical indicators to qualitatively 
determine whether a node is a hub under a specific threshold (Franciotti 
et al., 2022; Guimer`a and Amaral, 2005; Sporns et al., 2007). The hub 
nodes  determined  by  these  methods  are  highly  subjective,  lack  stan-
dardized  measurement  standards,  and  make  it  difficult  to  perform 
quantitative analyses of hub nodes.

Quantitative methods for computing hub nodes provide a compre-
hensive and objective analysis, enhancing the accuracy and sensitivity of 
hub node identification while reducing bias. This approach allows for 
precise comparisons and ensures standardized, replicable results, lead-
ing  to  a  deeper  understanding  of  network  structures  and  their  roles. 
Although  some  studies  use  a  single  graph  theoretical  index  (i.e. 
Betweenness Centrality, Nodal Efficiency, or Degree Centrality, etc.) to 
define hub nodes (Crossley et al., 2013; Li et al., 2020; Liang et al., 2013; 
Ma et al., 2015; Xin et al., 2022). It’s possible to quantify hub nodes by 
these graph index, while a single index often fails to distinguish between 
pro hub nodes and con hub nodes and loses information from other graph 
theory dimensions, rendering the judgment unconvincing. In addition to 
the hub nodes, candidate hub nodes as influential network nodes can 
still have a substantial impact on the overall network structure (Bassett 
and Bullmore, 2017). Previous studies focusing mainly on identifying 
hub  nodes  lose  critical  information  about  changes  in  these  candidate 
hub  nodes.  Lastly,  there  is  currently  no  definitive  network  sparsity 
standard in hub node indicator studies (Bassett et al., 2006; Cole et al., 
2010, 2015), leading to differences in hub distribution under varying 
sparsity.

We  therefore  suggest  the  following  considerations  for  quantifying 
hub nodes in the network: (1) Comprehensive Hub Indicator: Different 
nodes should be evaluated using a standard hub indicator that accounts 
for multiple graph-theoretical attributes, rather than relying on a single 
graph property. This allows for a more holistic measurement of a node’s 
hub characteristics. (2) Stability of Core Hub Nodes Across Diseases: In 
various diseases, core hub nodes may exhibit minimal changes due to 
their  inherent  stability.  In  contrast,  some  candidate  hub  nodes  may 
experience significant alterations, making a comprehensive evaluation 
of all nodes’ hub properties particularly advantageous. (3) Variability in 
Hub  Properties  Due  to  Disease  Influence:  Disease  can  affect  the  hub 
properties of different nodes in diverse ways, leading to reduced con-
sistency in the overall hub characteristics of the network across patients. 
(4) Impact of High Hub Attribute Nodes on Network Efficiency: Nodes 
with higher hub attribute scores hold more critical positions within the 
network.  As  a  result,  the  removal  of  such  nodes  will  significantly 
decrease  the  network’s  global  efficiency.  To  implement  the  above-
mentioned approaches, based on the mathematical ideas of TOPSIS al-
gorithm (Hwang and Yoon, 1981), this study proposes a Multi-criteria 
Quantitative Graph Analysis (MQGA) that utilizes multi-graph theoret-
ical index calculations to quantitatively analyze the hub attributes of all 
nodes.

We  hypothesis  that  the  MQGA  will  provide  a  more  objective  and 
comprehensive framework for identifying brain network hubs by inte-
grating multiple graph-theoretical indices. This method will improve the 
precision of distinguishing between connector and provincial hub nodes 
compared  to  traditional  single-index  methods,  while  revealing  candi-
date  hub  nodes  that  might  significantly  impact  network  structure. 
Additionally,  MQGA  will  demonstrate  robustness  across  varying 
network  sparsity  thresholds,  offering  more  consistent  and  reliable  re-
sults in both healthy and disease-affected brain networks.

Specifically, this study utilizes two benchmark networks to initially 
validate  the  accuracy  of  the  MQGA  in  identifying  hub  nodes  and 

demonstrated its superiority over single-indicator methods. The corre-
lation  between  hub  scores  and  hub  labels  in  a  randomly  simulated 
network,  helping  to  determine  the  optimal  sparse  threshold.  While  a 
vulnerability test was conducted to further assess MQGA’s precision in 
identifying hub nodes within complex networks. Additionally, data from 
the  ADHD-200  database  were  employed  to  evaluate  the  real-world 
performance  of  MQGA.  Consistent  with  previous  research  (Buckner 
et al., 2009; Chen et al., 2020; Fransson et al., 2011; Xin et al., 2022; Zuo 
et al., 2012), our findings consistently identified key hub regions, further 
validating the reliability of this method. In addition, it is different from 
previous  studies  that  only  focused  on  changes  in  hub  nodes.  MQGA 
found that compared with healthy subjects, ADHD had significant ab-
normalities in some candidate hub nodes located in the SMN, VAN and 
DMN  networks,  and  the  hub  scores  of  these  abnormal  nodes  were 
significantly correlated with clinical indicators.

2. Materials and methods

2.1. Resting-state fMRI dataset

We utilized resting-state fMRI data from individuals with Attention- 
Deficit  Hyperactivity  Disorder  (ADHD)  to  further  validate  the  MQGA 
method. There are two key reasons for selecting ADHD data: (1) Prior 
research on ADHD has consistently revealed significant abnormalities in 
the functional connectivity networks, particularly in regions associated 
with executive functions, attention, and the default mode network (Chen 
et al., 2021; Gonz´alez-Madruga et al., 2022; Zhang et al., 2020). These 
abnormalities  are  often  reflected  in  altered  functional  connectivity, 
especially at hub nodes within the brain. Given that MQGA is designed 
to  evaluate  hub  node  centrality,  ADHD  provides  an  ideal  context  to 
assess its ability to detect such alterations. (2) ADHD is widely studied 
using  large-scale  datasets,  such  as  the  ADHD-200  Consortium,  which 
offers a rich source of neuroimaging data ideal for validating compu-
tational models. These datasets reveal consistent dysfunction patterns in 
key network hubs, making ADHD an appropriate condition for evalu-
ating the performance of MQGA across different clinical populations.

The ADHD data were sourced from the ADHD-200 consortium (htt 
p://fcon_1000.projects.nitrc.org/indi/adhd200),  specifically  from  the 
New York University Child Study Center (NYU) and Peking University 
Child Study Center (Peking) datasets (Milham et al., 2012). The NYU 
dataset included 152 ADHD subjects and 111 healthy controls (HC). All 
participants  provided  signed  informed  consent  as  approved  by  the 
institutional review board (IRBs) of NYU and the NYU School of Medi-
cine  and  were  compensated.  Due  to  missing  gender  information  for 
subject 10,044 in the NYU dataset, which was excluded. Furthermore, 
after removing 5 ADHD subjects and 1 HC subject with significant head 
movements,  the  final  sample  included  146  ADHD  subjects  and  110 
healthy controls (Table 1).

For  the  Peking  dataset,  all  related  research  was  approved  by  the 
Research  Ethics  Review  Board  of  Institute  of  Mental  Health,  Peking 
University. Informed consent was also obtained from the parents of each 
subject and all of the children agreed to participate in the study. The 
Peking dataset had 83 ADHD subjects and 120 HCs, they all passed head 
movements  check.  Moreover,  all  subjects  provided  informed  consent 
before MRI or neurological assessment (Table 2).

2.2. fMRI preprocessing

All  resting-state  fMRI  images  were  preprocessed  using  the  Data 
Processing and Analysis of Brain Imaging toolbox (DPABI, http://rfmri. 
org/dpabi). The preprocessing steps began with the removal of the first 
five unstable time points, followed by slice timing correction to account 
for differences in acquisition time across slices. The images were then 
realigned to correct for head motion. Next, the images were normalized 
to the Montreal Neurological Institute (MNI) space, allowing for com-
parison across subjects. Regressing out the average time-series signals 

2 

H. Wu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120913 

Table 1 
NYU dataset clinical statistical information.

NYU

age

ADHD(M/F =
111/35)
mean ± SD

11.08 ± 2.67

HC(M/F = 54/ 
56)
mean ± SD

12.12 ± 3.11

ADHD Index

71.86 ± 8.64

45.36 ± 5.98

Inattentive

71.37 ± 9.12

45.67 ± 5.99

Hyper/ 

Impulsive

Verbal IQ

68.57 ± 11.93

46.28 ± 5.34

107.01 ± 13.88

111.99 ± 13.3

Performance IQ

103.03 ± 14.63

Full4 IQ

105.8 ± 14.14

107.51 ±
15.03
111 ± 14.14

Mean FD Power

0.21 ± 0.12

0.18 ± 0.13

Comparison 
ADHD vs HC

t254 = (cid:0) 2.872, p =
0.004
t247 = 27.125, p <
0.0001
t247 = 25.254, p <
0.0001
t247 = 17.948, p <
0.0001
t243 = (cid:0) 2.819, p =
0.005
t243 = (cid:0) 2.338, p =
0.02
t242 = (cid:0) 2.837, p =
0.005
t254 = 1.68, p = 0.09

Note: All subjects in the tables are results after excluding subjects with larger 
head movements. M=male; F=female; SD=standard deviation; FD = framewise 
displacement.

Table 2 
Peking dataset clinical statistical information.

Peking

ADHD(M/F = 71/ 
12)
mean ± SD

HC(M/F = 61/ 
59)
mean ± SD

Comparison 
ADHD vs HC

age
ADHD Index

11.81 ± 2.08
50.41 ± 8.2

11.09 ± 1.79
29.54 ± 6.39

Inattentive

27.95 ± 4.14

15.78 ± 3.75

Hyper/ 

Impulsive

Verbal IQ

22.58 ± 6.53

13.77 ± 3.83

80.16 ± 51.51

94 ± 50.89

Performance IQ

102.81 ± 15.32

115.71 ± 14.37

Full4 IQ

106.27 ± 13.92

119.35 ± 13.3

Mean FD Power

0.19 ± 0.11

0.15 ± 0.09

t201 = 2.649, p = 0.009
t182 = 19.388, p <
0.0001
t182 = 20.801, p <
0.0001
t183 = 11.493, p <
0.0001
t200 = (cid:0) 1.893, p =
0.06
t200 = (cid:0) 6.113, p <
0.0001
t149= (cid:0) 5.789, p <
0.0001
t201= 2.512, p = 0.013

Note:  M=male;  F=female;  SD=standard  deviation;  FD  = framewise 
displacement.

from gray matter, white matter, cerebrospinal fluid, and head motion 
was conducted to minimize confounding effects. This was followed by 
detrending  to  remove  linear  trends  in  the  time  series  and  band-pass 
filtering  (0.01–0.1  Hz)  to  retain  frequencies  of  interest.  Finally,  the 
images  were  smoothed  using  a  6  mm  full-width  at  half-maximum 
(FWHM) Gaussian kernel to increase the signal-to-noise ratio. Subjects 
with  a  maximum  head  movement  greater  than  2  mm  or  a  mean 
framewise displacement (FD) greater than 1 were excluded from further 
analysis (Power et al., 2012). Specifically, the ADHD database removed 
five ADHD subjects and one HC subject from NYU.

2.3. Connectivity matrix analysis

Using  Yeo’s  17  network  atlas  (Thomas  Yeo  et  al.,  2011),  the  pre-
processed ADHD-200 resting-state fMRI data were segmented into 400 
regions of interest (ROIs) (Schaefer et al., 2018). The radius of each ROI 
was  set  to  6  mm.  We  calculated  the  average  time  series  of  all  voxels 
within each ROI to represent the overall time series of different ROIs. To 
construct the brain network, a symmetric connectivity matrix was built 
for each subject by calculating the Pearson correlation coefficient be-
tween pairs of time series signals obtained from different ROIs. These 
functional  connectivity  matrices  were  maintained  in  their  signed 
weighted form, rather than being binary or thresholded. Subsequently, a 

3 

Fisher r-z transformation was applied to the FC matrices. All FC matrix 
and compare results as shown in Supplementary Fig. S1.

2.4. Benchmark network and random simulation network verification

To  verify  the  effectiveness  of  the  MQGA  algorithm,  we  used  two 
benchmark networks and 100 randomly constructed networks contain-
ing  connector  hub  nodes  and  provincial  hub  node  labels  to  verify  it. 
Specifically, for the first benchmark network, we used a simple network 
with 11 nodes and 2 subnetworks (Cole et al., 2015). As a result of the 
simple connector hub and provincial hub labels in the network, we used 
the MQGA algorithm to calculate the corresponding con and pro scores 
and sorted the hub scores and their respective graph theory index scores 
from  high  to  low  (Supplementary  Table1  and  Supplementary 
Table2).  After  determining  that  the  hub  node  score  obtained  by  the 
MQGA algorithm is better than the single index score, we further used 
the “Zachary’s karate club” benchmark network with 34 nodes and two 
sub-networks  to  verify  the  MQGA  (Girvan  and  Newman,  2002).  To 
further evaluate the effectiveness of MQGA in random networks and its 
performance under different sparsity thresholds, we created a synthetic 
dataset consisting of 100 randomly constructed connected networks for 
validation.

For  random  simulation  network,  each  of  these  networks  was 
designed  to  encompass  100  ROIs,  arranged  in  a  100  × 100  random 
connection matrix. The strength of the correlation varied between 0 and 
1.  These  networks  were  systematically  divided  into  five  distinct  sub- 
networks,  with  each  sub-network  containing  an  equal  number  of  20 
ROIs. We first use the mask to create the baseline network, and then 
insert the hubs. More specifically, we added a correlation value within 
sub-networks to create a provincial hub and added correlation values 
between  sub-networks  to  generate  connector  hubs.  To  introduce 
complexity and variability, we randomly assigned 5 to 10 hubs to these 
sub-networks, classifying them as either connector hubs or provincial 
hubs. Connector hubs were characterized by exhibiting higher connec-
tion strengths between sub-networks, whereas provincial hubs demon-
strated stronger connections within their designated sub-networks. This 
approach allowed us to simulate diverse network topologies and assess 
the method’s performance across a wide range of scenarios.

Subsequently, we annotated each ROI within these random networks 
with one of three labels: 1) ordinary node, representing ROIs that did not 
exhibit pronounced hub characteristics; 2) provincial hub node, denot-
ing ROIs that functioned as hubs predominantly within their respective 
sub-networks; and 3) connector hub node, identifying ROIs that served 
as bridges, exhibiting strong connections across multiple sub-networks. 
This labeling process facilitated a detailed analysis of the MQGA’s ac-
curacy  in  identifying  and  categorizing  hubs  within  complex  network 
structures.

Finally, the prediction accuracy is assessed by calculating the cor-
relation between the hub score and the corresponding label. The specific 
calculation process is as follows: first, we convert the con hub node or pro 
hub node labels into dichotomous variables. For example, when calcu-
lating the correlation between the pro hub node label and the pro score, 
if a node is a pro hub node, it is assigned a value of 1; otherwise, it is 
assigned  0.  At  this  point,  the  input  vector  consists  of  a  dichotomous 
variable (label vector) and a continuous variable (hub node score). In 
this case, the Pearson correlation coefficient is mathematically equiva-
lent to the point biserial correlation coefficient. The point biserial cor-
relation  is  appropriate  for  calculating  the  correlation  between  binary 
and continuous variables, therefore we used Pearson correlation anal-
ysis to calculate the correlation between the hub score and the corre-
sponding  label.  In  this  analysis,  the  R  value  indicates  the  degree  of 
consistency between the hub score and the true label. A higher R value 
reflects greater accuracy in the calculation of the hub score.

H. Wu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120913 

2.5. Computing the connector and provincial hubs

As illustrated in the descriptive statistical results of current methods 
for calculating hub nodes (Supplementary Fig. S2), most studies use 
three graph theoretical indicators—betweenness centrality (BC), degree 
centrality  (DC),  and  participation  coefficient  (PC)—to  determine  pro-
vincial hub (pro) nodes and connector hub (con) nodes (the application 
data brain map as shown in Supplementary Fig. S3). There  remains 
debate regarding which threshold network sparsity should be adopted in 
calculating  these  indicators.  To  address  this,  we  used  the  GRETNA 
toolbox  to  calculate  BC,  DC,  and  PC  under  varying  network  sparsity 
levels (0.01 to 0.50, step = 0.01) (Wang et al., 2015).

To normalize the distribution for subsequent calculations, we per-
formed  a  square  root  transformation  on  BC  and  a  complex  inverse 
transformation [1/(1 (cid:0) PC)] on PC. Nodes with higher BC, DC, and PC 
values were classified as con hub nodes, whereas nodes with higher BC, 
DC,  and  lower  PC  values  were  classified  as  pro  hub  nodes.  Before 
calculating  the  pro  hub  index,  we  applied  a  positive  transformation 
[max (PC) (cid:0) PC] to PC to ensure that nodes with higher BC, DC, and PC 
values were identified as pro hubs.

We combined the three graph theoretical indicators for each ROI as a 

high-dimensional vector: 

[
xi,j=1, xi,j=2, xi,j=3

]

X =

(1) 

Where xi,1 = BC, xi,2 = DC, and xi,3 = PC. For each subject, X is a vector 
containing three node indicators, with i representing different ROIs and 
j  representing  graph  indices  in  vector  X.  These  indicators  were  then 
normalized to obtain: 

Zij =

√

xi,j

̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅
∑
n
i=1x(i,j)2

(2) 

After normalization, we calculate the maximum and the minimum 

+

and Z- respectively: 

vectors, Z
+ = [max{Zi1}, max{Zi2}, max{Zi3}]

Z

(cid:0) = [min{Zi1}, min{Zi2}, min{Zi3}]

Z

(3) 

(4) 

+
(cid:0)
We then calculated the Euclidean distances D
i  between the 
i  and D

attribute vector and Z

and Z- of each ROI of different subjects: 

+

√
√
√
√

̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅
∑3
)
2

(cid:0)

+
Z
i

(cid:0) Zij

j=1

√
√
√
√

̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅
∑3
)
2

(cid:0)

(cid:0) Zij

(cid:0)
Z
i

j=1

+
i

D

=

(cid:0)
i

D

=

(5) 

(6) 

+
(cid:0)
Then, the con and pro indicators of each ROI by using D
i  were 
i  and D

calculated: 

proi =

(cid:0)
D
proi
+ D(cid:0)

+
D
proi

proi

coni =

D

(cid:0)
D
coni
+ D(cid:0)

+
coni

coni

(7) 

(8) 

Dconi  represent the result calculated by using BC, DC and PC indicators 
through formulas 1 to 6, while Dproi  represent the result calculated by 
using BC, DC and PC (after positive transformation) through formulas 1 
to 6. These indicators (proi/coni) were Z-score transformed to improve 
the normality of the results and facilitate subsequent statistical analyses. 
The coni  estimated the likelihood of ROI i being a connector hub in the 
network, while the proi  estimated the likelihood of ROI i being a pro-
vincial hub.

To  determine  the  optimal  sparsity  for  hub  node,  we  performed 

4 

Pearson correlation analysis between the hub indices (con and pro) and 
the corresponding hub labels in the simulated network. The higher the R 
value, the higher the degree of prediction of the real hub nodes under the 
sparse  degree.  Therefore,  a  sparsity  threshold  of  0.04  provided  the 
highest  combined  prediction  accuracy  for  both  con  and  pro  indices, 
which was subsequently used for the real data analysis.

2.6. Vulnerability analysis

To further validate our hub node calculation method, we conducted a 
vulnerability analysis. We first calculated the original global efficiency 
(Ego) of different networks. 

Eglobal =

1
N(N (cid:0) 1)

∑

i∕=j

1
dij

(9) 

In Formula 9, Eglobal  is the global efficiency of the network, N is the 
total  number  of  nodes  in  the  network,  dij  is  the  shortest  path  length 
between node i and node j, and i ∕= j means ignoring the path from the 
node to itself. All global efficiency calculations in vulnerability testing 
are based on Eq. (9).

Next,  we  sequentially  removed  each  ROI  from  the  network  and 
calculated the global efficiency (Egi) after removal, obtaining the effi-
ciency change (ΔEgi): 

ΔEgi = Ego (cid:0) Egi

(10) 

The higher the con or pro score, the more the node is at the core of the 
network. Therefore, deleting this node will lead to a greater reduction in 
network efficiency. That is, the higher the con or pro score, the corre-
sponding  greater  the  ΔEgi.  In  order  to  verify  this  hypothesis,  we  per-
formed a Pearson correlation analysis using the hub node score and ΔEgi. 
The ΔEgi  reflects the impact of node i on the global network, with larger 
values indicating more important nodes. The correlation analysis further 
validated the effectiveness of our hub calculation method. In the cor-
relation values of the vulnerability test, the higher the R value, the more 
accurately the hub score obtained by the MQGA algorithm can reflect 
the node type.

3. Consistency analysis

We assessed the stability of the hub node indices by analyzing their 
consistency across different datasets and brain atlases. Specifically, the 
ICC (intra-class correlation coefficient) values in this study were calcu-
lated by analyzing the absolute agreement of multiple raters using a one- 
way random effects model, which specifically focuses on the consistency 
of the overall node hub scores across different subjects. To assess the 
extent to which the measurements were absolutely consistent, we per-
formed the following steps: 

(1) We randomly selected half of the subjects as samples. This sam-
pling method is intended to reduce potential bias and improve the 
generalizability of the study. It should be noted that the data of 
each  subject  includes  the  con  or  pro  scores  of  all  ROI  to  more 
comprehensively  reflect  the  consistency  of  all  node  scores  in 
different subjects.

(2)  We  performed  k  independent  measurements  on  these  selected 
subjects. Here, ‘k independent measurements’ refers to the scores 
of  all  ROIs  by  different  subjects  under  the  same  calculation 
method. In this way, we can more accurately assess the consis-
tency of ROI scores between different subjects. Subsequently, we 
calculated the average of these measurements and used it as the 
basis  for  the  ICC  calculation.  Using  the  average  can  reduce 
random errors and make the ICC estimate more stable.

(3)  To enhance the robustness of the ICC estimate, we repeated the 
entire  process  5000  times,  each  time  performing  random  sam-
pling  and  k  independent  measurements  on  all  subjects.  This 

H. Wu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120913 

repeated calculation method helps us obtain a reliable estimate of 
the ICC, and its confidence interval and stability can be further 
analyzed by statistical methods.

The  higher  the  ICC  value,  the  more  stable  the  distribution  of  hub 

node index of all ROIs in different subjects.

4. Statistics analysis

Finally, we used two-sample t-tests to compare changes in hub node 
indices  between  healthy  control  and  disease  groups  across  different 
datasets, applying FDR correction to all results. Additionally, for nodes 
showing  significant  differences,  we  conducted  Pearson  correlation 
analysis  to  examine  the  relationship  between  hub  node  indices  and 
clinical  indicators.  A  higher  R  value  indicates  a  strength  correlation 
between the hub score and the corresponding clinical index.

5. Results

5.1. Experimental design

The experimental process of this study is depicted in Fig. 1. Unlike 
traditional methods that merely identify hub nodes (defining whether a 
node is a hub node), our approach quantitatively analyzes hub nodes 
using simulation data and ADHD data. We verified the effectiveness and 
stability  of  our  method  through  various  validation  techniques  and 
compared  the  hub  node  indices  between  disease  and  healthy  control 
groups, conducting Pearson correlation analyses with clinical variable 
for nodes with significant differences.

5.2. Simulation results

red)  value  and  the  minimum  (i.e.,  blue)  value,  respectively  Pearson 
correlation analysis (Fig. 2D) indicated that the R value for con increased 
while the R value for pro decreased with increasing network sparsity. At 
a sparsity threshold of 0.04, the R values for con and pro were approx-
imately equal, around 0.62. To verify the reliability of the number of 
nodes in the simulation, we tested networks with varying numbers of 
nodes and subnetworks. While the number of nodes may influence the 
exact optimal threshold, the overall evaluation criteria remained rela-
tively  stable  (Supplementary  Fig.  S4).  The  Supplementary  Fig.  S5 
based  on  real  data  also  shows  a  distribution  law  consistent  with  the 
simulation results.

5.3. Application results

Mapping  the  calculated  average  hub  scores  to  the  brain  revealed 
consistently high con values in the precentral gyrus, postcentral gyrus, 
and precuneus across different fMRI datasets and diseases (Upper left 
position of each sub-image in Fig. 3). Similarly, high pro values were 
observed  in  the  precentral  gyrus,  postcentral  gyrus,  superior  parietal 
lobule, precuneus, and superior temporal gyrus (Upper right position of 
each  sub-image  in  Fig.  3).  These  regions  are  crucial  for  advanced 
cognitive  functions  such  as  motor  control,  sensory  processing,  spatial 
cognition,  and  auditory/language  processing,  indicating  their  central 
role in the brain network.

In the distribution results of hub node indicators at the bottom of 
each subgraph in Fig. 3. Both con and pro distributions showed slight 
skewness, with a longer tail on the left. In general, pro values are more 
tightly  clustered  around  the  mean,  while  the  probability  distribution 
results of con are shifted to the right relative to pro. Differences in the 
distributions between HC and ADHD groups highlight potential changes 
in network characteristics associated with ADHD.

The  simulation  network  (100  nodes)  was  divided  into  five  sub-
networks with randomly inserted provincial and connector hub nodes 
(Fig.  2A).  All  connections  in  the  simulation  networks  were  positive, 
aligning  with  the  positive  connections  considered  in  actual  network 
calculations. Fig. 2B and 2C show the distribution of con and pro values 
mapped  to  a  three-dimensional  space  constructed  with  the  required 
graph theory indices. The two larger points represent the maximum (i.e., 

5.4. Vulnerability results

Fig. 4 demonstrates a strong positive correlation between hub indices 
(con and pro) and ΔEg  across different dataset groups. This correlation 
supports the accuracy of our hub calculation method, highlighting the 
significant impact of con and pro hub nodes on the network.

Interestingly,  except  that  the  correlation  between  pro  and  ΔEg  is 

Fig. 1. Study overview. A) Calculation and verification of hub index of simulation network. B) Verification results of ADHD-200 data in different datasets.

5 

H. Wu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120913 

Fig. 2. Simulation test and verification. A) Stochastic simulation network. B) and C) Distribution of hub node indicators. D) Correlation analysis results between hub 
node indicators and hub labels.

higher  than  that  between  con  and  ΔEg  (Fig.  4E)  in  the  simulation 
network, the correlation between con and ΔEg  is higher than that be-
tween pro and ΔEg  (Fig. 4A to Fig. 4D left) in all real data. The corre-
lation  between  con  and  ΔEg  was  relatively  consistent  across  different 
datasets and groups, while the correlation between pro and ΔEg  (Fig. 4A 
to Fig. 4D right) varied slightly large, which reflects the stability and 
consistency of the overall topological properties of the network in the 
resting state. For the consistently low hub indices (con or pro) and ΔEg 
outlier’s points in the vulnerability test, we mapped them back to each 
subject’s brain and found that they were mainly concentrated in nodes 
Para-hippocampal gyrus and inferior temporal gyrus (Supplementary 
Fig. S6).

5.5. Consistency analysis results

Fig.  5 shows  that  hub  node  indices  had  high  consistency  across 
different datasets, with higher ICC values. We find that the ICC result of 
con is always higher than that of pro in all data. This result is reasonable, 
because  the  connector  hub  often  involves  multiple  networks,  so  the 
stability  of  its  connection  will  affect  the  network  primarily  working 
mode to some extent. However, the scope of the pro hub nodes is smaller, 
so its stability result is lower than that of con hub nodes. In addition, the 
stability of hub node indices was significantly higher in healthy subjects 
than in disease groups (The inter-group variability of the NYU dataset is 
greater than the Peking dataset), indicating that brain network stability 
is compromised in disease conditions (Table 3).

6 

H. Wu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120913 

Fig. 3. Hub indexes mapping and its probability distribution results. For each subgraph, the upper part shows the con and pro mapping results from left to right, and 
the lower part shows the corresponding probability distribution results. A) HC in the NYU dataset. B) ADHD in the NYU dataset. C) HC in the Peking dataset. D) 
ADHD in the Peking dataset. The brain map shown in each sub-image is a mapping of the average con and pro scores of all subjects on 400 ROIs. The probability 
distribution in the sub-image is the overall probability distribution of CON and PRO scores of all subjects on 400 ROIs.

5.6. Group comparison and clinical correlation analysis

Fig. 6 presents the comparison results between groups and the cor-
relation analysis  with  clinical variables. After  FDR correction,  signifi-
cant differences were observed in the con indices between the ADHD and 

HC groups in the Peking dataset. According to the Yeo network division, 
these significant differences are particularly evident in the DMN, SMN, 
and  VAN  networks,  which  have  all  been  previously  associated  with 
ADHD in earlier studies. Supplementary Fig. S7 shows the uncorrected 
results at p < 0.001. Among all significantly changed nodes, the DMN 

7 

H. Wu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120913 

Fig. 4. Global efficiency impact of hub nodes. From top to bottom, each subgraph is the correlation between con and ΔEgand between pro and ΔEg  respectively. A) 
HC in the NYU dataset. B) ADHD in the NYU dataset. C) HC in the Peking dataset. D) ADHD in the Peking dataset. E) Simulation data.

Fig. 5. Hub index consistency analysis. A) Consistency analysis of hub index in NYU dataset. B) Consistency analysis of the hub index in the Peking dataset.

Table 3 
Comparison results between groups of ICC values.

NYU dataset

ICC con: mean ± SD

ICC pro: mean ± SD

SomMotA-1  node  index  con  and  the  ADHD  index,  inattention  score, 
impulsivity score, and verbal-IQ. Finally, we also found that the FrMed-2 
node index con located in the VAN network has a significant positive 
correlation with p-IQ.

HC
ADHD
HC-ADHD

Peking dataset

HC
ADHD
HC-ADHD

0.903 ± 0.006
0.901 ± 0.006
t9998 = 19.978, p < 0.0001

0.892 ± 0.006
0.888 ± 0.006
t9998 = 25.43, p < 0.0001

6. Discussion

0.929 ± 0.004
0.92 ± 0.004
t9998 = 115.72, p < 0.0001

0.905 ± 0.005
0.898 ± 0.005
t9998 = 72.631, p < 0.0001

network showed the largest number of significant differences, and the 
nodes with the greatest changes (pCunPCC-3) are concentrated in the 
DMN network. As shown in Table 4, the con of the four nodes (pCunPCC- 
2, pCunPCC-3, PFCl-1, and IPL-1) belonging to the DMN network in the 
ADHD  group  were  significantly lower  than the  HC  group.  The  con of 
nodes  SomMotA-1  and  FrMed-2  belonging  to  the  SMN  and  VAN  net-
works were significantly higher than the HC group.

Pearson  correlation  analysis  of  these  significantly  different  nodes 
with clinical indicators in pCunPCC-2 and IPL-1 are significantly nega-
tively  correlated  with  ADHD  index,  full-IQ,  and  Performance-IQ 
respectively.  There  is  a  significant  positive  correlation  between  the 

8 

The current study employs three graph theoretical indices BC, DC, 
and  PC  to  propose  a  method  for  quantitatively  analyzing  hub  node 
indices and their candidate hub node across large-scale brain networks. 
A series of tests (benchmark verification, correlation of hub index and 
hub label, vulnerability test, and consistency analysis among subjects) 
using  benchmark  network,  random  simulation  networks  and  whole- 
brain  networks  constructed  from  different  datasets  (ADHD-200  NYU 
and  Peking)  demonstrated that  our proposed  method  for  quantitative 
calculation of node attributes exhibits high accuracy and stability.

In  the  verification  results  based  on  the  benchmark  network  (Cole 
et al., 2015), the connector hub node E and the provincial hub node H 
obtained  the  highest  con  and  pro  scores,  respectively,  after  MQGA 
calculation. In the con score ranking, nodes F and I ranked second and 
third as candidate connector hub nodes. Additionally, the MQGA algo-
rithm assigned more reasonable pro scores reflecting the importance of 
different nodes within their respective sub-networks. This demonstrates 

H. Wu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120913 

Fig.  6. Comparison  of  con  between  groups  in  the  Peking  dataset  and  the  correlation  results  with  clinical  index.  All  comparisons  are  ADHD-HC  and  pass  FDR 
correction. The correlation result is the Pearson correlation between significant differences in node and clinical indicators.

Table 4 
Peking dataset ADHD con score vs HC con score comparison result.

ROI name

MNI (x, y, z)

network

t(201)

p

q

SomMotA-1
pCunPCC-2
pCunPCC-3
PFCl-1
IPL-1
FrMed-2

((cid:0) 8, (cid:0) 15, 47)
((cid:0) 5, (cid:0) 60, 30)
((cid:0) 7, (cid:0) 44, 32)
((cid:0) 41, 19, 48)
((cid:0) 40, (cid:0) 79, 30)
(6, 11, 58)

SMN-A
DMN-A
DMN-A
DMN-B
DMN-C
VAN-A

3.658216
(cid:0) 4.2635
(cid:0) 3.44292
(cid:0) 3.46742
(cid:0) 3.77832
3.485452

0.000324
3.09E-05
0.0007
0.000643
0.000208
0.000603

0.043256
0.012377
0.046676
0.046676
0.041598
0.046676

Note: The t values in the table were obtained by performing a two-sample t-test 
to compare the pro scores of ADHD subjects at different nodes with the pro scores 
of HC subjects at the corresponding nodes.

that the MQGA algorithm can accurately identify both connector and 
provincial hub nodes in the network.

However,  when  considering  the  rankings  based  on  BC,  DC,  or  PC 
separately, certain limitations arise. The BC indicator only considers the 
frequency of a node in all shortest paths, while DC focuses solely on the 
degree centrality of the node. These two indicators alone are insufficient 

to correctly identify connector hub node E and provincial hub node H in 
the  network.  Additionally,  in  the  PC  indicator,  nodes  not  connected 
across sub-networks are assigned a participation coefficient of 0, which 
makes  it  impossible  to  identify  provincial  hub  nodes.  These  findings 
have  been  further  validated  using  the  benchmark  network  based  on 
“Zachary’s karate club.”

Correlation analysis between hub index and hub label demonstrated 
increasing trend in sparsity with increase in the accuracy of determining 
con increased while that of pro decreased. This opposite trend is due to 
the inherent properties of con and pro. Brain networks are known to have 
modular  properties,  where  connections  within  different  networks  are 
higher than those between networks (Gallen et  al., 2023; Sang et  al., 
2023). At low network sparsity, higher connections are mostly concen-
trated within networks, effectively reducing potential interference from 
inter-network connections. This results in higher accuracy for pro and 
lower accuracy for con. As sparsity increases, more inter-network con-
nections  are  included  in  the  computation,  which  provides  additional 
information  for  improving  the  accuracy  of  con  while  simultaneously 
interfering with pro. Thus, we chose a threshold of 0.04, where the ac-
curacy of con and pro are balanced, for subsequent verification.

9 

H. Wu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120913 

In the study using fMRI data, we found that even with the influence 
of factors such as different data sets and differences in subject samples 
(Supplementary  Fig.  S1),  the  distributions  of  con  and  pro  were  still 
highly  consistent.  Interestingly,  we  consistently  found  relatively  high 
con  values  in  the  precentral  gyrus,  postcentral  gyrus,  and  precuneus 
across different atlases, and relatively high pro values in the precentral 
gyrus,  postcentral  gyrus,  superior  parietal  lobule,  precuneus,  and  su-
perior temporal gyrus. These brain regions have been frequently iden-
tified as hub areas in previous studies (Buckner et al., 2009; van den 
Heuvel and Sporns, 2013a).

The  probability  density  distribution  results  of  con  and  pro  are 
consistent  with  the  distribution  of  their  mapping  in  the  three  graph 
theory spaces (Supplementary Fig. S5). The smaller standard deviation 
of pro further confirms that its distribution is more concentrated than 
con, even though the two have very similar mean results. These results 
reflect their different functional roles and structural characteristics in 
the network, and the following four reasons work together to lead to this 
result.  1)  Connection  pattern:  Provincial  hub  nodes  are  mainly  con-
nected to internal nodes of the network, that is, they are more involved 
in the connection of local networks. Since these connections are rela-
tively  stable  and  concentrated,  their  probability  distribution  is  more 
concentrated.  Connector  hub  nodes  build  bridges  between  different 
brain  regions  and  connect  different  modules.  These  connections  are 
more diverse and dispersed, resulting in a more dispersed probability 
distribution.  2)  Functional  role:  Provincial  hub  nodes  are  mainly 
involved in the local processing of specific functions, so their role in the 
same or similar tasks is relatively consistent, which is manifested as a 
more  concentrated  distribution.  Connector  hub  nodes  play  a  coordi-
nating role between multiple functions and tasks, and their activity and 
connection  patterns  may  vary  from  task  to  task,  resulting  in  a  more 
dispersed  distribution.  3) Topological  structure:  Provincial  hub  nodes 
mainly connect internal nodes, and their network topology is relatively 
fixed and concentrated. However, due to cross-module connections, the 
network topology of connector hub nodes is more complex and diverse, 
and this diversity is reflected in the more dispersed probability distri-
bution.  4)  Node  importance:  The  high  connectivity  and  centrality  of 
provincial hub nodes are usually concentrated in specific areas, making 
their distribution concentrated. The importance of connector hub nodes 
is not only reflected within a single module but also in the connection 
between modules. This extensive connection leads to a more dispersed 
distribution. In summary, the probability distribution of provincial hub 
nodes is more concentrated because they mainly connect local nodes and 
have  relatively  consistent  functions  and  topologies;  while  the  proba-
bility distribution of connector hub nodes is more dispersed due to their 
diversified connections, complex functions, and topological structures.

In the vulnerability test and consistency analysis of all real data, this 
was  evident  in  the  consistently  higher  R-value  for  the  con  in  the 
vulnerability  test  and  higher  ICC  value  in  the  consistency  test.  This 
finding  is  reasonable  because  the  influence  of  con  hub  nodes  in  the 
network is greater than that of pro hub nodes, and the required stability 
of hub nodes across the network is higher than that of hub nodes within 
the network (Rubinov and Sporns, 2010). When a certain brain area is 
affected, the brain often  compensatory organizes other brain areas to 
replace the corresponding functions of the affected brain area (Berger 
et al., 2019; Laing and Hampstead, 2021). This is reflected in the sta-
bility of the network topology properties at the whole brain scale. This 
may explain why some people with ADHD experience mild symptoms or 
symptoms  disappear  after  reaching  a  certain  age  (Biederman  et  al., 
2011;  Karam  et  al.,  2015;  Sibley  et  al.,  2021).  However,  despite  this 
compensatory mechanism, we still find that compared to the HC group, 
the ICC of both ADHD groups decreased significantly. This indicates that 
different types of lesions in the hub structure of different subjects lead to 
varied  clinical  ADHD  symptoms  (Alexander-Bloch  et  al.,  2013;  Griffa 
et al., 2013; McColgan et al., 2015).

In comparing the HC group and disease groups, we identified only six 
significant difference nodes between ADHD and HC groups in the Peking 

dataset after FDR correction. Most of these nodes with significant dif-
ferences are not hub nodes in the traditional definition. However, sig-
nificant inter-group differences were still observed in this study. This 
proves the necessity of studying candidate hub nodes through quanti-
tative analysis methods. According to the division of whole-brain net-
works (Thomas Yeo et al., 2011), these significantly different nodes are 
located in the DMN, SMN, and VAN networks. These networks have been 
repeatedly  found  to  be  associated  with  ADHD  (Chen  et  al.,  2021; 
Gonz´alez-Madruga et al., 2022; Janssen et al., 2018; Liu et al., 2022; Sun 
et al., 2021; Tsai et al., 2024; Wang et al., 2022; You et al., 2024; Zhang 
et al., 2023). The Pearson correlation analysis between the con of these 
nodes  and clinical  indicators further  confirmed their association with 
ADHD. It is worth noting that the SomMotA_1 node showed a positive 
correlation  with  all  ADHD  indicators  and  Verbal-IQ.  All  nodes  of  the 
DMN  exhibit  different  tendencies  compared  to  other  nodes  in  both 
inter-group comparison and correlation analysis. This discrepancy may 
be  attributed  to  the  unique  operational  mode  of  the  DMN  as  a 
resting-state network, distinct from regional networks.

After applying multiple comparison corrections, no significant group 
differences  were  found  between  HC  and  ADHD  in  the  NYU  dataset. 
However, the FC matrix results in Supplementary Fig. S1 reveal sig-
nificant differences between datasets within the same group (HC/ADHD: 
NYU vs. Peking). Furthermore, the results of inter-group comparisons 
across different datasets also varied. Additionally, the consistency test 
showed that the inter-group differences in the NYU dataset were smaller 
than those in the Peking dataset. This indicates that the differences be-
tween the ADHD and HC groups in the NYU dataset are less pronounced 
than in the Peking dataset. Given the stability of hub nodes within the 
network,  this  finding  underscores  the  difficulty  of  using  hub  node 
analysis to detect minor local connection changes within the network.

6.1. Implications of MQGA method

The  distribution  of  core  nodes  identified  by  the  MQGA  method  is 
consistent with previous large-scale resting-state network studies, while 
MQGA provides more granular insights. By employing a 400 ROI-based 
approach, we assessed specific brain regions with enhanced resolution, 
uncovering  biologically  relevant  hub  dynamics  often  obscured  in 
broader  network  studies.  Using  this  ROI-based  framework  (Schaefer 
et al., 2018), our study adds precision to prior hub node analyses that 
relied on larger networks. This approach enabled us to explore the to-
pological  properties  of  brain  network  organization  in  greater  detail, 
revealing biologically significant hubs that broader network definitions 
tend to overlook.

Moreover, while earlier studies typically relied on DC or other con-
ventional indices, our multi-criteria approach incorporates not only a 
node’s prominence based on its connections (i.e., DC) but also its role in 
information  flow  (i.e.,  BC)  and  its  involvement  in  cross-network 
communication  (i.e.,  PC).  As  shown  in  Fig.  3,  several  identified  hubs 
exhibited  high  con  values,  particularly  in  the  precentral  gyrus,  post-
central gyrus, and precuneus across multiple datasets. High pro values 
were also consistently observed in regions such as the precentral gyrus, 
superior parietal lobule, and superior temporal gyrus—areas implicated 
in  critical  cognitive  functions,  including  motor  control  and  sensory 
processing (Buckner et al., 2008; van den Heuvel and Sporns, 2013b). 
The strength of MQGA lies in its ability to precisely quantify the relative 
contributions of these hubs across different graph properties.

In addition to offering a detailed assessment of traditional hub nodes, 
MQGA also highlights changes in candidate hub nodes, which are often 
overlooked by conventional methods that primarily focus on identifying 
the  most  prominent  hubs.  These  candidate  hub  nodes,  though  not 
exhibiting the highest centrality values, are crucial to the stability and 
efficiency of brain networks. This distinction is particularly relevant in 
ADHD, where subtle but widespread network disruptions occur. In our 
comparison of ADHD and HC, we observed significant differences not 
only in prominent hubs but also in several candidate hub nodes. This 

10 

H. Wu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120913 

demonstrates MQGA’s advantage in providing a comprehensive analysis 
of disease-related network alterations. Candidate hubs within networks 
such  as  the  DMN,  SMN,  and  VAN  are  essential  for  understanding 
ADHD’s broad effects on brain function (Castellanos and Proal, 2012; 
Fair et al., 2013). These findings suggest that the impact of ADHD on 
brain  connectivity  is  diffuse,  affecting  both  prominent  and  candidate 
hubs.

Overall,  the  method  proposed  in  this  study  for  quantitatively 
analyzing hub nodes in different networks demonstrates high accuracy 
and stability, with the distribution of high hub node scores aligning with 
previous  hub  node  studies  (Buckner  et  al.,  2009;  Chen  et  al.,  2020; 
Fransson et al., 2011; Xin et al., 2022; Zuo et al., 2012). Unlike previous 
qualitative methods for defining hub nodes (Harriger et al., 2012; Huang 
et al., 2021; Liao et al., 2017; Van Den Heuvel and Fornito, 2014), our 
approach  quantitatively  measures  the  attributes  of  all  hub  nodes  and 
candidate  hub  nodes,  making  them  suitable  for  subsequent  statistical 
analysis.  The  ability  of  this  hub  node  quantification  method  was 
demonstrated using real datasets from the ADHD-200 NYU and Peking 
sites. This approach allows for a more detailed quantitative analysis of 
disease impact through changes in hub nodes and further explores dif-
ferences in whole-brain network topological properties. Thus, this study 
makes a valuable contribution to the quantitative investigation of brain 
network topology.

7. Limitations

This  study  has  several  limitations.  Firstly,  the  potential  effects  of 
sparsity  on  pro  prediction  accuracy  must  be  considered.  As  network 
sparsity increases, the reliance on global centrality measures, such as 
degree and betweenness, becomes problematic. With fewer connections 
overall, global measures may be less effective at capturing the local at-
tributes  of  nodes.  Future  studies  should  explore  centrality  measures 
within  specific  network  modules,  such  as  intra-module  degree  or 
betweenness centrality, to improve pro accuracy. Secondly, this study 
did not delve deeper into how ADHD affects brain networks at the hub 
level, an important topic that will be considered in future research.

CRediT authorship contribution statement

Hongzhou Wu: Writing –  original draft, Validation, Methodology, 
Investigation,  Formal  analysis,  Data  curation,  Conceptualization. 
Zhenzhen Yang: Visualization, Validation. Qingquan Cao: Data cura-
tion. Pan Wang: Validation, Data curation. Bharat B. Biswal: Writing – 
review & editing. Benjamin Klugah-Brown: Writing – review & edit-
ing, Supervision, Project administration, Methodology, Funding acqui-
sition, Formal analysis, Conceptualization.

Declaration of competing interest

The authors declare no conflict of interest.

Funding

This work was supported by the National Natural Science Foundation 

of China (NSFC82250410380, NSFC62171101).

Supplementary materials

Supplementary material associated with this article can be found, in 

the online version, at doi:10.1016/j.neuroimage.2024.120913.

Data availability

The  ADHD  data  were  sourced  from  the  ADHD-200  consortium 
(http://fcon_1000.projects.nitrc.org/indi/adhd200),  specifically  from 
the  New  York  University  Child  Study  Center  (NYU)  and  Peking  Uni-

11 

versity Child Study Center (Peking) datasets (Milham et al., 2012).

References

Alexander-Bloch, A., Giedd, J.N., Bullmore, E., 2013. Imaging structural co-variance 

between human brain regions. Nat. Rev. Neurosci. 14 (5), 322–336. https://doi.org/ 
10.1038/nrn3465. Nat Rev Neurosci. 

Bagarinao, E., Kawabata, K., Watanabe, H., Hara, K., Ohdake, R., Ogura, A., Masuda, M., 
Kato, T., Maesawa, S., Katsuno, M., Sobue, G., 2022. Connectivity impairment of 
cerebellar and sensorimotor connector hubs in Parkinson’s disease. Brain Commun. 
4 (5). https://doi.org/10.1093/braincomms/fcac214.

Bassett, D.S., Bullmore, E.T., 2017. Small-world brain networks revisited. Neuroscientist 
23 (5), 499–516. https://doi.org/10.1177/1073858416667720. Neuroscientist. 
Bassett, D.S., Meyer-Lindenberg, A., Achard, S., Duke, T., Bullmore, E., 2006. Adaptive 
reconfiguration of fractal small-world human brain functional networks. Proc. Natl. 
Acad. Sci. U.S.A. 103 (51), 19518–19523. https://doi.org/10.1073/ 
pnas.0606005103.

Berger, D., Varriale, E., van Kessenich, L.M., Herrmann, H.J., de Arcangelis, L., 2019. 

Three cooperative mechanisms required for recovery after brain damage. Sci Rep 9 
(1). https://doi.org/10.1038/s41598-019-50946-y.

Bertolero, M.A., Yeo, B.T.T., Bassett, D.S., D’Esposito, M, 2018. A mechanistic model of 
connector hubs, modularity and cognition. Nature Human Behav. 2 (10), 765–777. 
https://doi.org/10.1038/s41562-018-0420-6. NIH Public Access. 

Biederman, J., Petty, C.R., Clarke, A., Lomedico, A., Faraone, S.V., 2011. Predictors of 
persistent ADHD: an 11-year follow-up study. J. Psychiatr. Res 45 (2), 150–155. 
https://doi.org/10.1016/j.jpsychires.2010.06.009.

Buckner, R.L., Andrews-Hanna, J.R., Schacter, D.L., 2008. The brain’s default network: 
anatomy, function, and relevance to disease. Ann. N. Y. Acad. Sci. https://doi.org/ 
10.1196/annals.1440.011.

Buckner, R.L., Sepulcre, J., Talukdar, T., Krienen, F.M., Liu, H., Hedden, T., Andrews- 

Hanna, J.R., Sperling, R.A., Johnson, K.A., 2009. Cortical hubs revealed by intrinsic 
functional connectivity: mapping, assessment of stability, and relation to 
Alzheimer’s disease. J. Neurosci. 29 (6), 1860–1873. https://doi.org/10.1523/ 
JNEUROSCI.5062-08.2009.

Castellanos, F.X., & Proal, E. (2012). Large-scale brain systems in ADHD: beyond the 

prefrontal-striatal model. In Trends in Cognitive Sciences (Vol. 16, Issue 1, pp. 17–26). 
https://doi.org/10.1016/j.tics.2011.11.007.

Chen, C., Lidstone, D., Crocetti, D., Mostofsky, S.H., Nebel, M.B., 2021. Increased 
interhemispheric somatomotor functional connectivity and mirror overflow in 
ADHD. NeuroImage 31. https://doi.org/10.1016/j.nicl.2021.102759.

Chen, J., Yang, J., Huang, X., Lu, C., Liu, S., Dai, Y., Yao, Z., Chen, Y., Yu, M., 2020. 

Variation in brain subcortical network topology between men with and without PE: a 
diffusion tensor imaging study. J. Sexual Med. 17 (1), 48–59. https://doi.org/ 
10.1016/j.jsxm.2019.10.009.

Cole, M.W., Ito, T., Braver, T.S., 2015. Lateral prefrontal cortex contributes to fluid 
intelligence through multinetwork connectivity. Brain Connect 5 (8), 497–504. 
https://doi.org/10.1089/BRAIN.2015.0357.

Cole, M.W., Pathak, S., Schneider, W., 2010. Identifying the brain’s most globally 
connected regions. NeuroImage 49 (4), 3132–3148. https://doi.org/10.1016/j. 
neuroimage.2009.11.001.

Crossley, N.A., Mechelli, A., V´ertes, P.E., Winton-Brown, T.T., Patel, A.X., Ginestet, C.E., 
McGuire, P., Bullmore, E.T., 2013. Cognitive relevance of the community structure 
of the human brain functional coactivation network. Proc. Natl. Acad. Sci. U.S.A. 
110 (28), 11583–11588. https://doi.org/10.1073/pnas.1220826110.

Fair, D.A., Dosenbach, N.U.F., Church, J.A., Cohen, A.L., Brahmbhatt, S., Miezin, F.M., 

Barch, D.M., Raichle, M.E., Petersen, S.E., Schlaggar, B.L., 2007. Development of 
distinct control networks through segregation and integration. Proc. Natl. Acad. Sci. 
U.S.A. 104 (33), 13507–13512. https://doi.org/10.1073/pnas.0705843104.

Fair, D.A., Nigg, J.T., Iyer, S., Bathula, D., Mills, K.L., Dosenbach, N.U.F., Schlaggar, B.L., 
Mennes, M., Gutman, D., Bangaru, S., Buitelaar, J.K., Dickstein, D.P., Martino, A.Di, 
Kennedy, D.N., Kelly, C., Luna, B., Schweitzer, J.B., Velanova, K., Wang, Y.F., 
Milham, M.P, 2013. Distinct neural signatures detected for ADHD subtypes after 
controlling for micro-movements in resting state functional connectivity MRI data. 
Front. Syst. Neurosci. 1–31. https://doi.org/10.3389/fnsys.2012.00080. FEB. 
Finc, K., Bonna, K., He, X., Lydon-Staley, D.M., Kühn, S., Duch, W., Bassett, D.S., 2020. 
Dynamic reconfiguration of functional brain networks during working memory 
training. Nat. Commun 11 (1). https://doi.org/10.1038/s41467-020-15631-z.
Franciotti, R., Moretti, D.V., Benussi, A., Ferri, L., Russo, M., Carrarini, C., Barbone, F., 

Arnaldi, D., Falasca, N.W., Koch, G., Cagnin, A., Nobili, F.M., Babiloni, C., 
Borroni, B., Padovani, A., Onofrj, M., Bonanni, L., 2022. Cortical network modularity 
changes along the course of frontotemporal and Alzheimer’s dementing diseases. 
Neurobiol. Aging 110, 37–46. https://doi.org/10.1016/J. 
NEUROBIOLAGING.2021.10.016.

Fransson, P., Åden, U., Blennow, M., Lagercrantz, H., 2011. The functional architecture 
of the infant brain as revealed by resting-state fMRI. Cerebral. Cortex 21 (1), 
145–154. https://doi.org/10.1093/cercor/bhq071.

Gallen, C.L., Hwang, K., Chen, A.J.W., Jacobs, E.G., Lee, T.G., D’Esposito, M, 2023. 

Influence of goals on modular brain network organization during working memory. 
Front Behav. Neurosci. 17. https://doi.org/10.3389/fnbeh.2023.1128610.
Girvan, M., Newman, M.E.J., 2002. Community structure in social and biological 
networks. Proc. Natl. Acad. Sci. U.S.A. 99 (12), 7821–7826. https://doi.org/ 
10.1073/pnas.122653799.

Gonz´alez-Madruga, K., Staginnus, M., Fairchild, G., 2022. Alterations in structural and 
functional connectivity in ADHD: implications for theories of ADHD. In: Stanford, S. 

H. Wu et al.                                                                                                                                                                                                                                      

NeuroImage 303 (2024) 120913 

C., Sciberras, E. (Eds.), New Discoveries in the Behavioral Neuroscience of Attention- 
Deficit Hyperactivity Disorder. Springer International Publishing, pp. 445–481. 
https://doi.org/10.1007/7854_2022_345.

Griffa, A., Baumann, P.S., Thiran, J.P., Hagmann, P., 2013. Structural connectomics in 

brain diseases. NeuroImage 80, 515–526. https://doi.org/10.1016/j. 
neuroimage.2013.04.056.

Guimer`a, R., Amaral, L.A.N., 2005. Cartography of complex networks: modules and 
universal roles. J. Statist.l Mech. 2005 (2), 1–13. https://doi.org/10.1088/1742- 
5468/2005/02/P02001.

Harriger, L., van den Heuvel, M.P., Sporns, O., 2012. Rich club organization of macaque 
cerebral cortex and its role in network communication. PLoS ONE 7 (9). https://doi. 
org/10.1371/journal.pone.0046497.

Huang, X., Xie, B.J., Qi, C.X., Tong, Y., Shen, Y., 2021. Abnormal intrinsic functional 
network hubs in diabetic retinopathy patients. NeuroReport 32 (6), 498–506. 
https://doi.org/10.1097/WNR.0000000000001620.

Hwang, C.-L., & Yoon, K. (1981). Methods for multiple attribute decision making. 58–191. 

https://doi.org/10.1007/978-3-642-48318-9_3.

Hwang, K., Bertolero, M.A., Liu, W.B., D’Esposito, M, 2017. The human thalamus is an 
integrative hub for functional brain networks. J. Neurosci. 37 (23), 5594–5607. 
https://doi.org/10.1523/JNEUROSCI.0067-17.2017.

Janssen, T.W.P., Heslenfeld, D.J., van Mourik, R., Gelad´e, K., Maras, A., Oosterlaan, J., 
2018. Alterations in the ventral attention network during the stop-signal task in 
children with ADHD: an event-related potential source imaging study. J. Atten. 
Disord 22 (7), 639–650. https://doi.org/10.1177/1087054715580847.

Karam, R.G., Breda, V., Picon, F.A., Rovaris, D.L., Victor, M.M., Salgado, C.A.I., Vitola, E. 
S., Silva, K.L., Guimar˜aes-Da-Silva, P.O., Mota, N.R., Caye, A., Belmonte-De- 
Abreu, P., Rohde, L.A., Grevet, E.H., Bau, C.H.D, 2015. Persistence and remission of 
ADHD during adulthood: a 7-year clinical follow-up study. Psychol. Med 45 (10), 
2045–2056. https://doi.org/10.1017/S0033291714003183.

Laing, J.M., Hampstead, B.M., 2021. Cognitive compensatory mechanisms. Encyclopedia 
of Gerontology and Population Aging. Springer, Cham, pp. 1057–1061. https://doi. 
org/10.1007/978-3-030-22009-9_689.

Li, Y., Wang, Y., Wang, Y., Wang, H., Li, D., Chen, Q., Huang, W., 2020. Impaired 
topological properties of gray matter structural covariance network in epilepsy 
children with generalized tonic–clonic seizures: a graph theoretical analysis. Front. 
Neurol 11. https://doi.org/10.3389/fneur.2020.00253.

Liang, X., Zou, Q., He, Y., Yang, Y., 2013. Coupling of functional connectivity and 

regional cerebral blood flow reveals a physiological basis for network hubs of the 
human brain. Proc. Natl. Acad. Sci. U.S.A. 110 (5), 1929–1934. https://doi.org/ 
10.1073/pnas.1214900110.

Liao, X., Vasilakos, A.V., He, Y., 2017. Small-world human brain networks: perspectives 
and challenges. Neurosci. Biobehav. Rev. 77, 286–300. https://doi.org/10.1016/j. 
neubiorev.2017.03.018. Neurosci Biobehav Rev. 

Liu, N., Jia, G., Li, H., Zhang, S., Wang, Y., Niu, H., Liu, L., Qian, Q., 2022. The potential 
shared brain functional alterations between adults with ADHD and children with 
ADHD co-occurred with disruptive behaviors. Child Adolesc. Psych. Ment. Health 16 
(1). https://doi.org/10.1186/s13034-022-00486-7.

Lord, L.D., Stevner, A.B., Deco, G., Kringelbach, M.L., 2017. Understanding principles of 

integration and segregation using whole-brain computational connectomics: 
implications for neuropsychiatric disorders. Philosoph. Transac. Royal Society A 375 
(2096). https://doi.org/10.1098/rsta.2016.0283. Philos Trans A Math Phys Eng Sci. 

Ma, X., Jiang, G., Li, S., Wang, J., Zhan, W., Zeng, S., Tian, J., Xu, Y., 2015. Aberrant 

functional connectome in neurologically asymptomatic patients with end-stage renal 
disease. PLoS ONE 10 (3). https://doi.org/10.1371/journal.pone.0121085.

McColgan, P., Seunarine, K.K., Razi, A., Cole, J.H., Gregory, S., Durr, A., Roos, R.A.C., 
Stout, J.C., Landwehrmeyer, B., Scahill, R.I., Clark, C.A., Rees, G., Tabrizi, S.J., 2015. 
Selective vulnerability of Rich Club brain regions is an organizational principle of 
structural connectivity loss in Huntington’s disease. Brain 138 (11), 3327–3344. 
https://doi.org/10.1093/brain/awv259.

Milham, P.M., Damien, F., Maarten, M., Stewart, H.M., 2012. The ADHD-200 

Consortium: a model to advance the translational potential of neuroimaging in 
clinical neuroscience. Front. Syst. Neurosci 6, 1–5. https://doi.org/10.3389/ 
fnsys.2012.00062. SEPTEMBER. 

Power, J.D., Barnes, K.A., Snyder, A.Z., Schlaggar, B.L., Petersen, S.E., 2012. Spurious 
but systematic correlations in functional connectivity MRI networks arise from 
subject motion. NeuroImage 59 (3), 2142–2154. https://doi.org/10.1016/j. 
neuroimage.2011.10.018.

maternal depression and SSRI antidepressants. Depress Anxiety 36 (8), 753–765. 
https://doi.org/10.1002/da.22906.

Rubinov, M., Sporns, O., 2010. Complex network measures of brain connectivity: uses 
and interpretations. NeuroImage 52 (3), 1059–1069. https://doi.org/10.1016/j. 
neuroimage.2009.10.003.

Sang, F., Xu, K., Chen, Y., 2023. Brain network organization and aging. Adv. Exp. Med. 

Biol. 1419, 99–108. https://doi.org/10.1007/978-981-99-1627-6_8. Adv Exp Med 
Biol. 

Schaefer, A., Kong, R., Gordon, E.M., Laumann, T.O., Zuo, X.N., Holmes, A.J., Eickhoff, S. 

B., Yeo, B.T.T, 2018. Local-global parcellation of the human cerebral cortex from 
intrinsic functional connectivity mri. Cerebral. Cortex 28 (9). https://doi.org/ 
10.1093/cercor/bhx17.

Sibley, M.H., Eugene Arnold, L., Swanson, J.M., Hechtman, L.T., Kennedy, T.M., 

Owens, E., Molina, B.S.G., Jensen, P.S., Hinshaw, S.P., Roy, A., Chronis-Tuscano, A., 
Newcorn, J.H., Rohde, L.A, 2021. Variable patterns of remission from ADHD in the 
multimodal treatment study of ADHD. Am. J. Psych. 179 (2), 142–151. https://doi. 
org/10.1176/appi.ajp.2021.21010032.

Sporns, O., Honey, C.J., K¨otter, R., 2007. Identification and classification of hubs in brain 
networks. PLoS ONE 2 (10). https://doi.org/10.1371/journal.pone.0001049.

Sun, Y., Lan, Z., Xue, S.W., Zhao, L., Xiao, Y., Kuai, C., Lin, Q., Bao, K., 2021. Brain state- 

dependent dynamic functional connectivity patterns in attention-deficit/ 
hyperactivity disorder. J. Psychiatr. Res 138, 569–575. https://doi.org/10.1016/j. 
jpsychires.2021.05.010.

Thomas Yeo, B.T., Krienen, F.M., Sepulcre, J., Sabuncu, M.R., Lashkari, D., 

Hollinshead, M., Roffman, J.L., Smoller, J.W., Z¨ollei, L., Polimeni, J.R., Fisch, B., 
Liu, H., Buckner, R.L., Yeo, B.T.T., Krienen, F.M., Sepulcre, J., Sabuncu, M.R., 
Lashkari, D., Hollinshead, M., Buckner, R.L., 2011. The organization of the human 
cerebral cortex estimated by intrinsic functional connectivity. J. Neurophysiol. 106 
(3), 1125–1165. https://doi.org/10.1152/jn.00338.2011.

Tsai, C.J., Lin, H.Y., Gau, S.S.F., 2024. Correlation of altered intrinsic functional 

connectivity with impaired self-regulation in children and adolescents with ADHD. 
European Archives of Psychiatry and Clinical Neuroscience. https://doi.org/ 
10.1007/s00406-024-01787-y.

Van Den Heuvel, M.P., Fornito, A, 2014. Brain networks in schizophrenia. Neuropsychol. 
Rev 24 (1), 32–48. https://doi.org/10.1007/s11065-014-9248-7. Neuropsychol Rev. 

van den Heuvel, M.P., Sporns, O., 2013a. Network hubs in the human brain. Trends 

Cogn. Sci. (Regul. Ed.) 17 (12), 683–696. https://doi.org/10.1016/j. 
tics.2013.09.012. Trends Cogn Sci. 

van den Heuvel, M.P., Sporns, O., 2013b. Network hubs in the human brain. Trends 

Cogn. Sci. (Regul. Ed.) 17 (12), 683–696. https://doi.org/10.1016/j. 
tics.2013.09.012.

Wang, J., Wang, X., Xia, M., Liao, X., Evans, A., He, Y., 2015. Corrigendum: GRETNA: a 
graph theoretical network analysis toolbox for imaging connectomics. Front. Hum. 
Neurosci 9, 458. https://doi.org/10.3389/fnhum.2015.00458. AUGUST. 

Wang, P., Wang, J., Jiang, Y., Wang, Z., Meng, C., Castellanos, F.X., Biswal, B.B., 2022. 
Cerebro-cerebellar dysconnectivity in children and adolescents with attention- 
deficit/hyperactivity disorder. J. Am. Acad. Child Adolesc. Psych. 61 (11), 
1372–1384. https://doi.org/10.1016/j.jaac.2022.03.035.

Xin, H., Wen, H., Feng, M., Gao, Y., Sui, C., Zhang, N., Liang, C., Guo, L., 2022. Disrupted 
topological organization of resting-state functional brain networks in cerebral small 
vessel disease. Hum. Brain Mapp 43 (8), 2607–2620. https://doi.org/10.1002/ 
hbm.25808.

Yang, D., Zhu, X., Yan, C., Peng, Z., Bagonis, M., Laurienti, P.J., Styner, M., Wu, G., 2021. 

Joint hub identification for brain networks by multivariate graph inference. Med. 
Image Anal 73. https://doi.org/10.1016/j.media.2021.102162.

You, W., Li, Q., Chen, L., He, N., Li, Y., Long, F., Wang, Y., Chen, Y., McNamara, R.K., 
Sweeney, J.A., DelBello, M.P., Gong, Q., Li, F., 2024. Common and distinct cortical 
thickness alterations in youth with autism spectrum disorder and attention-deficit/ 
hyperactivity disorder. BMC Med 22 (1). https://doi.org/10.1186/s12916-024- 
03313-2.

Zhang, H., Zhao, Y., Cao, W., Cui, D., Jiao, Q., Lu, W., Li, H., Qiu, J., 2020. Aberrant 
functional connectivity in resting state networks of ADHD patients revealed by 
independent component analysis. BMC Neurosci 21 (1). https://doi.org/10.1186/ 
s12868-020-00589-x.

Zhang, R., Murray, S.B., Duval, C.J., Wang, D.J.J., Jann, K., 2023. Functional 

Connectivity and Complexity Analyses of Resting-State fMRI in Pre-Adolescents with 
ADHD. MedRxiv. https://doi.org/10.1101/2023.08.17.23294136.

Rotem-Kohavi, N., Williams, L.J., Muller, A.M., Abdi, H., Virji-Babul, N., Bjornson, B.H., 
Brain, U., Werker, J.F., Grunau, R.E., Miller, S.P., Oberlander, T.F., 2019. Hub 
distribution of the brain functional networks of newborns prenatally exposed to 

Zuo, X.N., Ehmke, R., Mennes, M., Imperati, D., Castellanos, F.X., Sporns, O., Milham, M. 
P., 2012. Network centrality in the human functional connectome. Cerebral. Cortex 
22 (8), 1862–1875. https://doi.org/10.1093/cercor/bhr269.

12 

