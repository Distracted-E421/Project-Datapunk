NeuroImage 303 (2024) 120925 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Using independent component analysis to extract a cross-modality and 
individual-specific brain baseline pattern

Wei Liu a,b, Xuemin Zhang a,b,*
a Beijing Key Laboratory of Applied Experimental Psychology. National Demonstration Center for Experimental Psychology Education (Beijing Normal University). 
Faculty of Psychology, Beijing Normal University, Beijing, People’s Republic of China
b State Key Laboratory of Cognitive Neuroscience and Learning, Beijing Normal University, Beijing, People’s Republic of China

A R T I C L E  I N F O

A B S T R A C T

Keywords:
Brain baseline
Independent component analysis
Functional connectome fingerprinting
Explained variance
Functional magnetic resonance imaging

The  ongoing  brain  activity  serves  as  a  baseline  that  supports  both  internal  and  external  cognitive  processes. 
However, its precise nature remains unclear. Considering that people display various patterns of brain activity 
even  when  engaging  in  the  same  task,  it  is  reasonable  to  believe  that  individuals  possess  their  unique  brain 
baseline pattern. Using spatial independent component analysis on a large sample of fMRI data from the Human 
Connectome Project (HCP), we found an individual-specific component which can be consistently extracted from 
either  resting-state  or  different  task  states  and  is  reliable  over  months.  Compared  to  functional  connectome 
fingerprinting,  it  is  much  more  stable  across  different  fMRI  modalities.  Its  stability  is  closely  related  to  high 
explained variance and is minimally influenced by factors such as noise, scan duration, and scan interval. We 
propose that this component underlying the ongoing activity represents an individual-specific baseline pattern of 
brain activity.

1. Introduction

The human brain is always active with a significant amount of energy 
consumption  (Attwell  and  Laughlin,  2001;  Rolfe  and  Brown,  1997). 
Previous  research  indicated  that  this  ongoing  activity  during  resting 
state, characterized by activation of the default mode network (DMN), is 
a  baseline  which  supports  sustained  information  processing  and  is 
attenuated during external tasks (Gusnard and Raichle, 2001; Raichle 
and Gusnard, 2002; Raichle and Snyder, 2007). However, researchers 
currently argue that the resting state should be regarded as a special type 
of task state, characterized by internal engagement in various cognitive 
activities that are not directly observed or controlled (Finn, 2021; Finn 
et  al.,  2017).  Furthermore,  the  activation  of  DMN  is  not  exclusive  to 
resting  state,  but  rather  occurs  across  all  task  states  (Buckner  and 
DiNicola, 2019; Cole et al., 2014; Krienen et al., 2014). These findings 
collectively  suggest  that  the  brain  activities  linked  to  internal  and 
external cognition are not as distinct as previously assumed.

Consistent with this perspective, a recently introduced brain baseline 
model proposed that the ongoing brain activity serves as a baseline that 
supports both internal and external cognitive processes (Northoff et al., 
2023).  This  model  suggests  that  the  ongoing  brain  activity’s  spatio-
temporal  dynamics  may  provide  a  "common  currency"  for  both 

* Corresponding author.

E-mail address: xmzhang@bnu.edu.cn (X. Zhang). 

internally and externally-oriented cognition. This implies that despite 
their differences, these forms of cognition share underlying spatiotem-
poral  dynamics,  which  are  shaped  by  the  ongoing  activity.  In  other 
words, the ongoing activity serves as a global neural code, providing a 
shared  reference  for  both  types  of  cognition  while  allowing  for  their 
differentiation into distinct forms. From this viewpoint, the resting and 
task states of brain share a common baseline which is integrated with 
various  internally  and  externally-oriented  activities.  Therefore,  the 
distinction between resting and task states may be attributed to varia-
tions  in  cognitive  activity  rather  than  alterations  in  baseline.  Never-
theless, the precise nature of this baseline remains unclear.

Considering that individuals exhibit different brain activities when 
performing same task (Michon et al., 2022), it is reasonable to assume 
that  the  baseline  pattern  is  unique  to  each  person.  Using  functional 
magnetic resonance imaging (fMRI), numerous metrics of brain activity 
that reflect individual-specific characteristics have been proposed (Finn 
et al., 2015; Elliott et al., 2019; Amico and Go˜ni, 2018; Bari et al., 2019; 
Byrge and Kennedy, 2019; Pallar´es et al., 2018; Liu et al., 2018; Chen 
and  Hu,  2018).  These  are  essentially  based  on  the  seminal  work  of 
functional  connectome  fingerprinting  (FCF,  Finn  et  al.,  2015),  which 
discovered  that  the  functional  connectivity  matrices  from  two  fMRI 
scans are substantially more consistent within the same individual than 
between  different  individuals  (Finn  et  al.,  2015;  Graff  et  al.,  2022; 

https://doi.org/10.1016/j.neuroimage.2024.120925
Received 30 September 2024; Received in revised form 6 November 2024; Accepted 11 November 2024  
Available online 12 November 2024 
1053-8119/© 2024 The Authors.  Published by Elsevier Inc.  This is an open access article under the CC BY-NC license ( http://creativecommons.org/licenses/by- 
nc/4.0/ ). 

W. Liu and X. Zhang                                                                                                                                                                                                                           

NeuroImage 303 (2024) 120925 

Abbreviations

maximal independent component

MIC
EVOM explained variance of MIC
FCF

functional connectome fingerpringting

Horien  et  al.,  2019,  2018;  Jalbrzikowski  et  al.,  2020;  Waller  et  al., 
2017). However, FCF may not be an appropriate indicator of the brain 
baseline because comparing to its accurate identification between two 
resting-state  fMRI  scans,  it  becomes  unstable  between  a  resting-state 
fMRI scan and a task fMRI scan, or between two task fMRI scans (Finn 
et al., 2015; Waller et al., 2017). Besides, FCF is mostly calculated using 
resting-state signals, which, as previously noted, do not represent a pure 
baseline  but  are 
substantial  unobserved 
internally-oriented brain activities.

intermingled  with 

Given that the brain baseline is embedded in both resting and task 
states and is mixed with various internally and externally oriented brain 
activities,  one  possible  approach  to  extract  the  baseline  pattern  is  to 
remove  the  cognitive  activity  signals  by  General  Linear  Model 
(Al-Aidroos et al., 2012; Fair et al., 2007). In fact, task states with simple 
block design exhibit a similar functional connectivity pattern compared 
to resting-state after removing the task related signals (Jurkiewicz et al., 
2018). However, it is challenging to further determine an appropriate 
design matrix for complex tasks (Finn, 2021), let alone the resting states 
that  lack  explicit  stimuli.  Consequently,  since  these  internally  and 
externally  oriented  activities  are  difficult  to  observe  and  define,  it  is 
challenging to remove them through a model-driven method to extract 
the baseline pattern. At this point, ICA, a data-driven blind source sep-
aration method, may be a more appropriate approach.

ICA, a method that separates mixed signals into mutually indepen-
dent components, has been widely employed in fMRI studies (Mckeown 
et  al.,  1998;  Beckmann  and  Smith,  2004;  Beckmann  et  al.,  2005;  Sui 
et al., 2009; Salimi-Khorshidi et al., 2014; Pruim et al., 2015). Single 
subject spatial ICA yields mutually independent components in the form 
of spatial brain maps and corresponding time courses. Despite the re-
striction  of  Independent  Component  Analysis  (ICA)  in  decomposing 
fMRI  signals  due  to  its  linearity  assumption,  multiple  research  have 
confirmed  its  viability  and  proposed  that  non-linear  effects  can  be 
roughly represented as a superposition of linear effects (Griffanti et al., 
2017).

Previous  research  using  ICA  focused  on  categorizing  components 
into signal and noise in order to clean the data (Griffanti et al., 2017). 
However, additional information is required to further find a baseline 
pattern from these components. Considering that the brain constantly 
shows a very high energy budget and the task-induced signals are just 
“tip of iceberg”(Attwell and Laughlin, 2001; Raichle and Snyder, 2007; 
Rolfe  and  Brown,  1997),  it  is  reasonable  to  assume  that  the  baseline 
activity of the brain should have the highest level of blood oxygen level 
dependent (BOLD) intensity. In other words, the component represent-
ing the baseline pattern should account for the majority of the variance. 
Consequently,  although  explained  variance  of  each  component  was 
rarely taken into consideration in previous research because it is not an 
indicator  that  distinguishes  between  noise  and  signal,  it  can  be  an 
important indicator to identify baseline pattern. However, it should be 
noted that previous studies typically centered data both spatially and 
temporally before conducting ICA (Beckmann and Smith, 2004; Calhoun 
et al., 2001). Although centering data spatially is a necessary step for 
spatial ICA, centering data temporally has the potential of altering the 
explained variance of the components and consequently reordering their 
ranks. If the number of extracted components is less than the number of 
time points (this is usually the case), some of the important components 
which have been reordered to lower ranks may not be extracted. In this 
case,  the  baseline  pattern  may  be  neglected  because  of  its  reduced 

2 

explained variance and lowered rank (see Section 2.4 for details).

In  a  nutshell,  the  rationale  for  using  ICA  to  derive  the  baseline  is 
threefold.  First,  isolating  the  baseline  using  a  model-driven  approach 
can  be  challenging  due  to  the  integration  of  baseline  activity  with 
diverse internally and externally oriented brain activities. A data-driven 
blind  source  separation  technique  is  more  suitable.  Second,  ICA  is  a 
commonly utilized method in fMRI data analysis, with its efficacy sup-
ported  by  multiple  studies.  Finally,  baseline  activity  exists  inside  the 
brain’s spontaneous activity, whose persistent high energy expenditure 
may coincide with significant explained variance, establishing a basis 
for identifying the baseline.

The aim of this study is to try to extract a brain baseline using ICA. 
Here  we  apply  single  subject  ICA  on  fMRI  data  without  temporally 
centering and focus on the explained variance of each component. We 
concentrate  on  the  component  with  the  highest  explained  variance, 
which we refer as maximal independent component (MIC), to assess its 
potential  as  a  candidate  of  baseline  pattern  by  testing  its  individual- 
specificity  and  stability  across  different  fMRI  modalities.  Specifically, 
using fMRI data from the Human Connectome Project (HCP), we analyze 
the stability and consistency of MIC across different fMRI conditions and 
over long scan intervals with a similar identification procedure as the 
FCF (Finn et al., 2015). We demonstrate that identification using MIC is 
more accuracy than FCF, especially when the MIC exhibits a high level of 
explained  variance.  We  also  investigate  other  factors  that  affect  the 
stability of MIC.

2. Material and methods

2.1. Datasets information

This  analysis  incorporated  four  datasets  from  the  Human  Con-
nectome Project (HCP): HCP Development (HCP-D), HCP Aging (HCP- 
A), HCP Young Adults (HCP-YA) and HCP retest.

The  Lifespan  HCP  2.0  Release  containes  652  healthy  developing 
participants  aged  5–21  (HCP-D),  and  725  aging  participants  aged 
36–100+ (HCP-A). Each participant in HCP-D completed two resting- 
state (RS1 and RS2) and three task fMRI conditions (Emotion process-
ing, Guessing, CARIT, for short EMO, GUE, CAR respectively) during a 
single visit (Somerville et al., 2018). Each of the five fMRI conditions 
comprised  two  scans  with  opposite  phase  encoding  directions: 
anterior-to-posterior (AP) and posterior-to-anterior (PA). The imaging 
protocols of HCP-A were similar to that of HCP-D with the exception that 
the three tasks were VisMotor (VM), FaceName (FN) and CARIT (CAR) 
(Harms  et  al.,  2018).  We  exclusively  evaluated  the  data  for  the 
posterior-anterior (PA) direction because some of the data from AP di-
rection were not supplied.

The  S1200  release  contained  fMRI  data  from  1113  subjects  aged 
22–35 (HCP-YA). For each subject, a resting-state (RS1) and three task 
conditions (Working Memory, WM; Gambling, GAM; Motor, MOT) were 
required  on  day  one,  and  another  resting-state  (RS2)  and  four  task 
conditions (Language, LAN; Social Cognition, SC; Relational Processing, 
REL; Emotion Processing, EMO) were required on day two. Each of the 
nine fMRI conditions contained two different phase encoding direction 
scans, left-to-right (LR) and right-to-left (RL). And only the LR scan data 
were included into our analysis. The HCP retest data package consists of 
45  people  in  HCP-YA  who  re-engaged in  the  same 9  fMRI  conditions 
after an interval of 2–11 months, with 40 people completing all the 18 
conditions (9 for test and 9 for retest). The same as before, only the LR 
scan data of the 18 conditions were analyzed.

2.2. Pre-processing

There were two versions of pre-processed CIFTI format data for each 
dataset. The first was a denoised clean version by using 24-parameter 
motion  regression  followed  by  ICA+FIX  denoising  (Griffanti  et  al., 
2014;  Salimi-Khorshidi  et  al.,  2014;  Smith  et  al.,  2013).  The  ICA-FIX 

W. Liu and X. Zhang                                                                                                                                                                                                                           

NeuroImage 303 (2024) 120925 

clean version was accessible for all resting and task fMRI conditions for 
participants in HCP-D and HCP-A. However, for participants in HCP-YA 
and HCP retest, this clean version was only available for resting-state. 
The  second  was  the  minimal  pre-processed  data  following  the  HCP 
pipeline (Glasser et al., 2013), which included artifact removal, motion 
correction and registration to standard space.

The two versions of fMRI files (ICA-FIX and minimal pre-processed) 
were initially analyzed without any additional pre-processing. Next, we 
applied  several  additional  denoising  steps  on  the  HCP-YA  ICA-FIX 
resting-state  data for further exploration. The denoising steps include 
intensity normalization, nuisance regression (linear trend, white matter 
signals,  cerebrospinal  fluid  signals,  global  signals)  and  Butterworth 
filtering (0.01–0.08 Hz).

Intensity  normalization  was  performed  by  subtracting  a  baseline 
value from the original data. Two types of normalization were employed 
separately: per-vertex normalization, which utilized the mean intensity 
of  each  vertex’s  timeseries  as  the  baseline  values,  and  grand  mean 
normalization, which utilized the mean intensity of the entire data as the 
baseline value. More precisely, each vertex has its unique baseline in the 
former, while all the vertices share a common baseline in the later.

We  performed  two  distinct  nuisance  regression  techniques.  The 
aggressive  regression  method  retained  the  residuals  of  the  regression 
model  for  subsequent  examination.  The  soft  regression  was  to  only 
remove the influence of noise signals on the regression model. There-
fore, the distinction between these two methods lied in the inclusion of 
intercepts  for  each  vertex.  While  both  methods  utilized  identical 
regression  models  and  noise  signals  as  regressors,  the  former  solely 
incorporated the residuals, whilst the latter incorporated both the re-
siduals and intercepts.

2.3. Functional connectivity matrix construction

A 400×400 functional connectivity (FC) matrix based on Schaefer- 
400 parcellation (Schaefer et al., 2018) were created for each partici-
pant for each condition using ciftiTools package in R (Pham et al., 2022). 
Specifically, the mean timeseries of each parcel was obtained by aver-
aging all the vertices’ timeseries within that parcel. Then a symmetric 
400×400 FC matrix for a single CIFTI file was generated by calculating 
pair-wise  Pearson  correlation  coefficient  across  the  400  parcels.  The 
subcortical brain regions were not included.

2.4. Maximum independent component

A data matrix with the size of v × t was generated for each CIFTI 
format  fMRI  data,  where  v  represented  the  number  of  vertices  and  t 
represented  the  number  of  time  points.  Subcortical  regions  were 
excluded from the analysis, resulting in a total of 59,412 vertices for the 
matrix. The mean of the matrix in space (column mean) was removed. 
Then  the  spatially  centered  data  matrix  (X)  was  decomposed  into  a 
signal  matrix  (S)  and  a  mixing  matrix  (M)  by  ICA,  which  could  be 
formulized as follows: 

X = SMT 

Each  column  of  S  represents  an  independent  component  (spatial 
brain  map)  and  the  corresponding  column  of  M  represents  its  time 
course. The explained variance of the ith component can be estimated as 
follows: 
explained variancei = v × mT
(cid:0)

)

i mi
XTX

tr

Where v is the number of vertices and mi  is the ith  column of mixing 
matrix  M.  According  to  this  formula,  the  explained  variance  of  each 
component is determined by the sum of squares of its time course since v 
and X are constant for all components.

The above calculations were done by using the ica package in R with 

the fastICA algorithm (Hyv¨arinen, 1999). The number of components for 
each  fMRI  data was  set  to  30,  among which  the  component  with the 
maximum explained variance  is referred  as  the maximal independent 
component (MIC).

It  should  be  noted  that  we  did  not  additionally  center  the  data 
temporally (removing the row mean of X) before ICA because this would 
alter the explained variance of each component. Specifically, centering 
the data temporally was equivalent to centering the mixing matrix M in 
column (the time course was normalized to zero mean). Although this 
operation  would  not  change  S  and  the  relative  fluctuation  of  time 
course, the sum of squares of the time course would fall disproportion-
ately,  with  those  components  with  high  intensity  and  low  variation 
decreasing  the  most  dramatically,  resulting  reordering  the  rank  of 
components.  Therefore,  the  MIC  may  not  be  correctly  extracted  after 
temporally centering.

2.5. Identification analysis

For each dataset, the identification procedures of FCF or MIC were as 
follows. First, all the fMRI conditions are paired. And for each pair, FC 
matrices (or MIC) are generated for all subjects. The upper triangle of 
each FC matrix is flattened to a 79,600×1 vector (each MIC is flattened 
to a 59,412×1 vector). Next, Pearson correlation of the FC vector (or 
MIC)  was  calculated  between  the  two  conditions  across  all  subjects, 
resulting  a  square  identification  matrix  for  that  pair.  Each  diagonal 
value of the identification matrix represented the correlation coefficient 
for the same subject, and the corresponding off-diagonal values repre-
sented the correlation coefficient between this subject and all the other 
subjects. Because the strength of correlation coefficient was irrelevant to 
its sign, we use its absolute value for identification. That is, if one of the 
absolute diagonal values is the maximum among its corresponding row 
and column, a success of identification was recorded.

The correlation coefficient between two FCs (or MICs) indicated the 
degree of their similarity. We defined the absolute Fisher-z transformed 
correlation  coefficient  as  similarity  score  (S).  For  each  identification 
matrix, the difference between diagonal intra-subject S (Sintra) and off- 
diagonal  inter-subject  S  (Sinter)  could  be  the  index  of  identification 
power. Since a single  subject only has a single  Sintra  value but 2(n-1) 
Sinter  values,  we  decided  to  use  the  maximum  of  Sinter  (Smax-inter),  a 
much  more  conservative  method  than  using  the  mean  of  Sinter,  to 
represent  the  inter-subject  similarity  for  each  subject.  Therefore,  the 
difference between Sintra and Smax-inter could be an index of identification 
power.

To illustrate this identification procedure more specifically, we take 
the  HCP-D  dataset  as  an  example.  Five  fMRI  conditions  (two  resting- 
state and three task fMRI) in HCP-D produced 10 pairs (Fig. 1a). Next, 
for each pair, Pearson correlation of FCF (or MIC) between the two fMRI 
conditions  were  calculated  across  all  subjects.  For  example,  the  FC 
matrix  (or  MIC)  of  any  subject  from  RS1  was  correlated  with  the  FC 
matrix  (or  MIC)  of  any  subject  from  GUE  (Fig.  1b).  This  produces  a 
square identification matrix with the dimension equals to the number of 
subjects in that dataset (Fig. 1c). Each absolute value in the identifica-
tion matrix represented the similarity between the corresponding sub-
jects’  FC  matrices  (or  MICs).  Therefore,  If  an  intra-subject  similarity 
(diagonal value) was the maximum among its corresponding row and 
column,  a  success  of  identification  was  recorded.  The  identification 
power  was  then  defined  as  the  difference  between  the  intra-subject 
similarity  and  the  corresponding  maximum  inter-subject  similarity 
(Fig. 1c).

3. Results

3.1. Identification using ICA-FIX data

We started our analysis on the data that has been preprocessed using 
ICA  and  FSL  tool  FIX  (ICA-FIX),  as  these  data  have  been  “cleaned” 

3 

W. Liu and X. Zhang                                                                                                                                                                                                                           

NeuroImage 303 (2024) 120925 

Fig. 1. Example of identification procedure. a, Combine the five fMRI sessions from HCP-D into 10 pairs. RS1: resting-state 1; RS2: resting state 2; EMO: emotion 
task; GUE: guessing task; CAR: CARIT (GO/NO-GO) task. b, For each pair (e.g., RS1 and GUE), each FCF (left) or MIC (right) from RS1 will be correlated with all the 
FCF or MIC from GUE. c, This produces an identification matrix in which the diagonal values represent intra-subject similarity and off-diagonal values represent inter- 
subject similarity. If the intra-subject similarity (e.g., absolute value of red square) is larger than the corresponding inter-subject similarity (absolute values on the 
blue lines), this subject is successfully identified. The difference between intra-subject similarity (red square) and maximum inter-subject similarity (e.g., purple circle 
which stands for the maximum value among all the values located on the blue lines) represents the identification power.

(Glasser et al., 2016).The ICA-FIX resting-state and task fMRI data are 
accessible for HCP-D and HCP-A, but the ICA-FIX task data for HCP-YA 
are not provided by HCP. Therefore, for HCP-YA only the resting-state 
ICA-FIX data were included into analysis. After excluding the partici-
pants  due  to  data  incompleteness  or  data  file  error,  614  participants 
from HCP-D, 709 participants from HCP-A and 1018 participants from 
HCP-YA  were  included  into  analysis.  The  ICA-FIX  data  was  directly 
analyzed  without  any  further  denoising  procedures  for  FCF  and  MIC 
identification at the first place (Section 3.1.1 to 3.1.5). Next, to explore 
the effect of denoising procedures on MIC identification, we performed 
intensity normalization, nuisance regression (linear trend, white matter 
signals,  cerebrospinal  fluid  signals,  global  signals)  and  Butterworth 
filtering on a subset of ICA-FIX data before FCF and MIC identification 
analysis (Section 3.1.6).

3.1.1. FCF identification

The results of FCF identification were similar to previous research 
(Finn et al., 2015; Waller et al., 2017, p. 201) that the identification rate 
of rest-rest pairs were higher than that of rest-task or task-task pairs for 
HCP-D  (Fig.  2a,  lower  triangle)  and  HCP-A  (Fig.  2b,  lower  triangle). 
Additionally, the identification power exhibited a comparable pattern to 

the identification rate. The results of the paired t-tests indicated that the 
rest-rest pair consistently exhibited the largest effect size of identifica-
tion power compared to the other pairs for HCP-D (Fig. 2a, upper tri-
angle)  and  HCP-A  (Fig.  2b,  upper  triangle).  Some  of  the  rest-task  or 
task-task pairs did not reach statistical significance, and in some cases, 
they  even  exhibited  a  significant  negative  effect  (VM-RS1,  FN-RS1, 
CAR-RS2,  FN-RS2,  VM-RS2  for  HCP-A).  With  regard  to  the  HCP-YA, 
the  identification  rate  of  rest-rest  pairs  was  0.64,  with  a  significant 
identification power (t1017 = 7.38, p < 0.001, Cohen’s d = 0.23, 95 % CI 
= [0.03, 0.05]).

Since we did not apply any further denoising pre-processing to the 
ICA-FIX data, it is reasonable that the FCF identification rate of HCP-YA 
is lower than that of earlier studies(Dubois et al., 2018; Finn et al., 2015; 
Horien et al., 2018; Waller et al., 2017). In addition, we used a new and 
more  stringent  algorithm  to  calculate  the  identification  rate,  which 
simultaneously  considered  all  subject  pairs  between  two  fMRI  condi-
tions rather than alternatively using one of the conditions as a reference. 
In  fact,  the  identification  rate  would  increase  to  0.704  and  0.698 
respectively if we used REST1 or REST2 condition as reference.

Fig.  2. Identification  results  of  FCF.  a,  Identification  rate  (lower-triangle)  and  identification  power  (upper-triangle)  for  each  fMRI  condition  pair  in  HCP-D.  b, 
Identification rate (lower triangle) and identification power (upper triangle) for each fMRI condition pair in HCP-A. RS1: resting-state 1; RS2: resting-state 2; CAR: 
CARIT task; EMO: emotion task; GUE: guessing task; FN: FaceName task; VM: VisMotor task. The violin plots show the difference between intra-subject similarity 
score and maximal inter-subject similarity score tested by paired t-test. d: Cohen’s d; 95 % CI: 95 % confidence interval; NS.: non-significant; *: p < 0.05, **: p < 0.01; 
***: p < 0.001.

4 

W. Liu and X. Zhang                                                                                                                                                                                                                           

NeuroImage 303 (2024) 120925 

3.1.2. MIC identification

Fast ICA algorithm (Hyv¨arinen, 1999) was performed on each of the 
ICA-FIX data. The number of extracted independent components was set 
to 30 based on previous research which suggested this as the minimal 
threshold  for  a  reliable estimation  (Beckmann and Smith,  2004). The 
component with the largest explained variance among the 30 compo-
nents was the MIC. Each MIC represented a spatial brain map. Exam-
ining the brain maps visually can reveal that although the MIC showed 
some  extent  of  similarity  across  subjects  (e.g.,  the  medial  and  lateral 
temporal lobe and medial prefrontal regions), the within-subject simi-
larity was much higher (Fig. 3).

To examining the similarity quantitatively, we created MIC identi-
fication matrix for each pair of conditions following the same procedure 
as  FCF  identification.  The  MIC  identification  rate  for  all  pairs  were 
highly accurate, achieving 100 % in both HCP-D (Fig. 4a, lower triangle) 
and  HCP-A  (Fig.  4b,  lower  triangle).  Furthermore,  the  effect  size  of 
identification power was substantially larger compared to FCF (Fig. 4a 
and 4b, upper triangles). The MIC identification rate of rest-rest pair in 
HCP-YA was 78 % with a significant difference between Sintra and Sinter- 
max (p < 0.001, cohen’s d = 0.67 and 95 %CI = [0.15, 0.18]). While the 
result was not as ideal as HCP-D and HCP-A, it still exceeded the iden-
tification rate obtained by FCF.

3.1.3. Effect of number of extracted components on MIC identification

To  determine  if  the  identification  was  affected  by  the  number  of 
extracted  components,  we  reanalyzed  the  HCP-D  and  HCP-A  data  by 
extracting 50 and 100 components respectively. Despite a minor fall in 
the identification power, the identification rates remained 100 % for all 
pairs. (Fig. 4c and 4d, supplementary Fig. 1).

3.1.4. Effect of scan duration on MIC identification

To further investigate the reasons for the lower MIC identification 
rate in HCP-YA, we first focused on the difference of scan duration be-
tween HCP-YA and HCP-A/D. The duration of the resting state scan for 
HCP-YA, which consists of 1200 vol, is significantly longer compared to 
that for HCP-D and HCP-A, which consist of 478 vol. To determine if this 
is the reason for the decreasing MIC identification rate in HCP-YA, we re- 
analyzed the HCP-YA data using only the initial 478 vol of each scan. 
Nevertheless, the identification rate (73 %) and the effect size (Cohen’s 
d = 0.56, 95 %CI = [0.13, 0.16]) both experienced a modest reduction, 
which did not support the hypothesis.

3.1.5. Effect of explained variance on MIC and FCF identification

We then focused on the explained variance of MIC (EVOM). Partic-
ipants in HCP-A and HCP-D exhibited a very high EVOM (>85 %) in all 

the fMRI conditions, while some of the participants’ EVOM of resting- 
state  in  HCP-YA  only  accounted  for  a  small  portion  of  variance 
(Fig.  5a). To  test  whether  the  identification rate  would  increase  with 
EVOM, we performed a sliding threshold analysis of EVOM from 0 to 
0.75 with step size of 0.05 on HCP-YA resting-state data. Specifically, 
only the subjects whose EVOM larger than the threshold in both of the 
two resting state conditions were included into identification analysis. 
Results showed that MIC identification rate increased dramatically with 
threshold (Fig. 5b). The identification rate increased to 0.87 with 887 
subjects retained when the threshold was set to 0.5, and rose to 0.94 
with 761 subjects retained when threshold was 0.65. However, the FCF 
identification rate was hardly affected by the threshold.

3.1.6. effect of denoising on MIC identification

A high FCF identification rate in previous research was obtained after 
some typical denoising procedures, such as regressing out the noise and 
filtering(Finn et al., 2015; Waller et al., 2017). In order to determine if 
the  MIC  identification  would  also  increase  after  these  additional 
denoising procedures, we performed intensity normalization, nuisance 
regression (linear trend, mean white matter signal, mean cerebrospinal 
fluid  signal,  global  signal),  and  Butterworth  filtering  (0.01–0.08)  on 
ICA-FIX resting-state data in HCP-YA.

We first performed these denoising procedures separately on a single 
subject  resting-state  data  and  checked  the  EVOM  after  each  step.  We 
found that grand mean normalization, soft regression and Butterworth 
filtering  had  minimal  impact  on  the  EVOM.  However,  per-vertex 
normalization  and  aggressive  regression  would  jeopardize  EVOM 
severely  (from  75  %  to  <1  %).  This  is  reasonable  since  per-vertex 
normalization  is  equivalent  to  temporally  centering,  and  aggressive 
regression  removes  the  intercept  which  contains  the  temporal  mean 
value  of  each  vertex.  In  fact,  the  component  with  largest  variance 
explained after per-vertex normalization or aggressive regression is no 
longer  the  previous  MIC  because  the  rank  of  components  has  been 
reordered.

To  directly  compare  the  identification  rate  of  MIC  after  denoising 
procedures, we calculated the MIC identification rate based on denoised 
data  of  132  subjects  from  HCP-YA  ICA-FIX  RS1  and  RS2.  We  used  a 
smaller sample size in this analysis for the purpose of time saving. The 
results were consistent with expectations, as the MIC identification rate 
significantly fell after applying per-vertex normalization and aggressive 
regression.  On  the  contrary,  the  identification  rate  slightly  increased 
after applying grand mean demeaning and soft regression (Table 1).

Fig. 3. MIC brain maps. a, Brain maps from five HCP-A participants. b, brain maps from five HCP-D participants. Each column represents the MIC brain maps from a 
single participant across different fMRI conditions. Note that the maps of HCP-D on the second row and the third column still maintains a similar pattern to other 
maps on the third column when the sign is reversed. Another example can be found at the first row and the fifth column.

5 

W. Liu and X. Zhang                                                                                                                                                                                                                           

NeuroImage 303 (2024) 120925 

Fig. 4. Identification of MIC using ICA-FIX data. a, Identification rate (lower-triangle) and identification power (upper-triangle) for each fMRI condition pair in HCP- 
D.  b,  Identification  rate  (lower  triangle)  and  identification  power  (upper  triangle)  for  each  fMRI  condition  pair  in  HCP-A.  c,  Difference  of  identification  power 
between MIC extracted from 30 and from 50 components for HCP-D. Error bar indicates standard deviation and the square brackets above the error bar show 95 %CI 
of mean differences. d, Difference of identification power between MIC extracted from 30 and from 100 components for HCP-A. RS1: resting-state 1; RS2: resting- 
state 2; CAR: CARIT task; EMO: emotion task; GUE: guessing task; FN: FaceName task; VM: VisMotor task. The violin plots show the difference between intra-subject 
similarity score and maximal inter-subject similarity score tested by paired t-test. d: Cohen’s d; 95 % CI: 95 % confidence interval; *: p < 0.05, **: p < 0.01; ***: p 
< 0.001.

3.2. Identification using minimal preprocessed data

3.2.1. MIC and FCF identification

As there are no ICA-FIX task fMRI data in HCP-YA, we next applied 
the same method to the HCP-YA minimal preprocessed data, which in-
cludes both resting state and seven task fMRI conditions. After removing 
those participants who did not complete all the nine fMRI LR conditions, 
data from 985 subjects were included into analysis. We also analyzed the 
HCP-D  (606 participants) and  HCP-A  (694  participants) minimal pre-
processed data for the completeness of the study. Since denoising have 
minimal effect on MIC identification, we did not perform any further 
denoising procedures on minimal preprocessed data before ICA.

The  identification  results  indicated  a  significant  drop  in  the  FCF 
identification  rate  for  each  pair  when  compared  to  the  ICA-FIX  data 
(Fig. 6a, lower triangle, supplementary Fig. 2a and 2b). This is reason-
able  since  the  minimal  pre-processed  data  have  not  dealt  with  noise, 
which would affect FCF severely. The MIC identification rate for the rest- 
rest pair of HCP-YA reduced from 0.77 to 0.65 (Fig. 6a, upper triangle), 
this decline was much smaller compared to FCF (from 0.64 to 0.21). This 
further indicated that the impact of noise on MIC identification was not 
as severe as it was on FCF. We also found that the MIC identification rate 
of all the pairs markedly increased after excluding the participants with 

6 

W. Liu and X. Zhang                                                                                                                                                                                                                           

NeuroImage 303 (2024) 120925 

Fig. 5. The effect of EVOM on MIC and FCF identification rate. a, Distribution of accounted variance of MIC. Pink bars show the histogram and blue lines show the 
corresponding density plots. The y-axis represents the density. b, Identification rate of MIC (blue) and FCF (red) as functions of EVOM threshold for HCP-YA resting- 
state data. Top x axis represents the number of subjects retained.

Table 1 
Comparison of identification rate between different denoising procedures based on resting state data of 132 subjects from HCP-YA ICA-FIX. Row one: undenoised data; 
Row two: denoised data using per-vertex normalization and aggressive regression; Row three: denoised data using grand mean normalization and soft regression. WM: 
mean white matter signal; CSF: mean cerebrospinal fluid signal; Global: global signal.

Identification rate

Denoising procedures

normalization

Regression

Linear trend

WM

0.85
0.27
0.89

\
Per-vertex
Grand mean

\
aggressive
soft

\
aggressive
soft

CSF

\
aggressive
soft

Global

\
aggressive
soft

Butterworth filtering

\
0.01–0.08Hz

Fig. 6. Identification rate of FCF (lower-triangle) and MIC (upper-triangle) for each fMRI condition pair of HCP-YA minimal preprocess data. a, identification rate 
without thresholding the EVOM. b, Identification with EVOM threshold of 0.65. For each of the figures, the upper-left blue and the lower-right purple squares show 
the identification rate between the conditions of the same day (day one and day two respectively). The upper-right and lower-left area shows the identification rate 
between the conditions of difference days. RS1: resting-state 1; RS2: resting-state 2; EMO: Emotion Processing task; GAM: Gambling task; LAN: Language task; MOT: 
Motor task; REL: Relational Processing task; SOC: Social Cognition task; WM: Working Memory task. The violin plots show the difference between intra-subject 
similarity  score and maximal inter-subject similarity score tested  by paired t-test. d:  Cohen’s  d; 95 % CI:  95 % confidence  interval; NS.:  non-significant; *:  p <
0.05, **: p < 0.01; ***: p < 0.001.

7 

W. Liu and X. Zhang                                                                                                                                                                                                                           

NeuroImage 303 (2024) 120925 

EVOM  lower  than  0.65  (Fig.  6b,  upper  triangle).  The  proportion  of 
subjects excluded from each condition pair ranged from 17 % to 39 %. 
Once again, the FCF identification rate was hardly affected by EVOM 
threshold (Fig. 6b, lower triangle). Notably, The MIC identification rate 
remained 100 % for all pairs in HCP-D and HCPA (supplementary Fig. 2c 
and 2d).

3.2.2. Difference of EVOM between resting- and task-state

Interestingly, we found that the number of subjects excluded from 
rest-rest and rest-task pairs was higher than from task-task pairs. A non- 
parametric  permutation  test  with  5000  iterations  supported  this  hy-
pothesis  that  the  15  pairs  with  resting-state  excluded  more  subjects 

(mean = 316) than the 21 pairs with only task-state (mean = 234), p <
0.001. This suggested that the overall EVOM of resting-state might be 
lower than task-state. To directly compare this difference, we calculated 
the mean of EVOM of resting-state and task-state respectively and con-
ducted a paired t-test. Result showed that the mean EVOM of resting- 
state was significantly lower than task-state, t984  = 21.08, p < 0.001, 
95  %CI  = [(cid:0) 0.06.(cid:0) 0.07].  And  this  result  was  equally  present  in  the 
HCP-D (t605 = 21.53, p < 0.001, 95 %CI = [(cid:0) 0.014, (cid:0) 0.017]) and HCP- 
A (t693 = 20.91, p < 0.001, 95 %CI = [(cid:0) 0.012, (cid:0) 0.014]) datasets

3.2.3.

Identification between long intervals

The identification rate for both the FCF and MIC  was consistently 

Fig. 7. MIC identification using HCP test-retest data. a, Identification rate without thresholding the EVOM. b, Identification rate with EVOM threshold of 0.65. c, 
Identification rate with EVOM threshold of 0.75. d, Identification rate with EVOM threshold of 0.8. The bold numbers represent the identification rate and the italic 
numbers bellow represent the number of subjects retained. Row indexes represent the test conditions and column indexes represent the retest conditions.RS1: resting- 
state 1; RS2: resting-state 2; EMO: Emotion Processing task; GAM: Gambling task; LAN: Language task; MOT: Motor task; REL: Relational Processing task; SOC: Social 
Cognition task; WM: Working Memory task.

8 

W. Liu and X. Zhang                                                                                                                                                                                                                           

NeuroImage 303 (2024) 120925 

greater when the two conditions in a pair were scanned on the same day, 
compared  to  when  they  were  scanned  on  different  days  (Fig.  6). 
Nevertheless, previous research demonstrated that the identification of 
FCF can maintain a satisfactory level of accuracy over months (Horien 
et al., 2019; Jalbrzikowski et al., 2020). To assess the stability of MIC 
identification over a longer period, we incorporated HCP retest data into 
analysis. The HCP retest data package consists of 45 people in HCP-YA 
who  re-engaged  in  the  9  fMRI  conditions  after  an  interval  of  2–11 
months, with 40 people completing all the 18 conditions (9 for test and 9 
for retest). We paired each test condition with all the retest conditions 
(81 pairs) and calculated the MIC identification rate for each pair. Re-
sults  showed  that the  MIC  identification  rate  remained  an  acceptable 
level over months, especially after thresholding the EVOM (Fig. 7).

4. Discussion

Using  single  subject  spatial  ICA  without  temporal  centering,  we 
discovered  a  component  with  dominant  explained  variance  is  highly 
stable  and  constant  within  individuals.  We  refer  this  component  as 
maximum independent component (MIC). Unlike previous studies that 
utilized group-derived parcellations to investigate the functional struc-
ture of the brain, MIC is extracted with little group-level information. In 
addition, the high level of within-subject stability and between-subject 
variability exhibited by MIC aligns it more closely with the notion of 
precision neuroimaging(Michon et al., 2022).

The  properties  of  MIC  make  it  be a  potential  option  to  define the 
brain baseline. First, the consistently high energy consumption of brain 
activity implies an adequately strong neural activity signal at the base-
line,  which  should  significantly  outweigh  signals  generated  by  other 
internal or external cognitive activities. Consistent with this notion, a 
stable MIC is consistently linked to the high explained variance. More 
precisely,  the  brain  map  depicted  by  MIC  is  very  reliable  when  the 
amount of variance explained is greater than a specific threshold, such 
as 0.65. In addition, MIC exhibits a very high individual-specificity that 
the  identification  power  consistently  shows  a  very  large  effect  size 
(Fig. 4a and 4b). Finally, MIC can be reproduced across different fMRI 
conditions, which supports the notion that the ongoing activity of the 
whole brain generates a universally shared neural code for both resting 
and task-related states (Northoff et al., 2023).

One implicit assumption of ICA for fMRI signal separation is that the 
observed signal is a linear combination of the decomposed source sig-
nals.  In  fact,  analysis  of  task  fMRI  using  GLM  and  hemodynamic 
response function is also based on this assumption. Although numerous 
studies  have  shown  that  task-induced  signals  are  not  simply  super-
imposed  on  resting  state  signals(He,  2013;  Wainio-Theberge  et  al., 
2021), this does not completely negate the validity of extracting MIC 
based on linear models. It is possible that when stimulus-evoked activity 
occurs, some (but not all) of the internal neural activity in the resting 
state is suppressed (Mathewson et al., 2014), but the baseline can remain 
stable. Therefore, the difference of brain activity between task and rest is 
not only an increase in stimulus-induced activity, but also a decrease in 
some  internally-oriented  activity.  In  other  words,  resting-state  brain 
signal  consists  of  baseline  and  internally  directed  activities,  while 
task-state  signal  consists  of  baseline,  stimulus-evoked  activities,  and 
partially suppressed internally-oriented activities. Since resting-state is 
not constant and internally-oriented activities changes over time (Allen 
et  al., 2014; Leonardi et al., 2014), it  is only natural that there is  no 
linear additive relationship between resting and task states. However, 
the  potential  for  cognitive  activities,  whether  internally  or  externally 
oriented, to be linearly superimposed on the baseline remains.

The  extraction  of  MIC  is  remarkedly  stable  unless  temporally 
centering  or  similar  manipulations  have  been  performed  (e.g.,  pre- 
processing  with  aggressive  regression).  Other  factors  that  we  have 
examined have limited impact on the stability of MIC, suggesting that 
MIC is a readily obtainable and robust measure of brain baseline. First, 
stable  MIC  can  be  reproduced  across  different  fMRI  conditions  with 

varying scan duration, and the identification rate hardly changed with 
only the first 478 vol from HCP-YA resting-state data. Second, while the 
identification power decreases as the number of extracted components 
grows,  the  decline  is  minimal  and  the  identification rate  remains  un-
changed (Fig. 4). Third, the identification rate of HCP-YA was consis-
tently higher for the scans conducted on the same day compared to those 
conducted on separate days (Fig. 6), which suggests that the scan in-
terval appears to be an important factor that influence the stability of 
MIC. However, the high identification rate for some of the subjects from 
HCP  test-retest  data  shows  that  the  stability  of  MIC  can  persist  for 
several  months  (Fig.  7).  Fourth,  with  the  exception  of  per-vertex 
normalization  and  aggressive  regression  which  have  the  potential  of 
reordering the rank of components, typical denoising algorithms have 
minimal  impact  on  the  identification  rate  of  MIC.  This  is  further 
corroborated by  the observation that stable MIC can be derived from 
both ICA-FIX and minimum preprocess data.

Nevertheless,  our  results  demonstrate  that  the  stability  of  MIC  is 
potentially related to ages. In comparison to children and older adults, 
stability  of  MIC  is  reduced  in  young  adults.  This  is  evidenced  by  the 
decreased  identification  rate  and  the  diminished  identification  power 
for  HCP-YA  data,  as  well  as  the  fact  that  HCP-D  and  HCP-A  subjects 
always showed extremely high EVOM across different conditions while 
some  of  the  subjects  from  HCP-YA  have  much  lower  EVOM  in  some 
conditions (Fig. 5). This suggests that the reproducibility of MIC may be 
subject to influence from developmental factors. For example, the young 
adults  whose  brain  function  are  highly  developed  are  able  to  more 
flexibly modulate baseline brain activity to adapt to different cognitive 
tasks. However, this should be explained with caution and need further 
exploration.

Another interesting result is that the MIC obtained from the resting- 
state  data  exhibited  a  slightly,  albeit  significantly,  lower  EVOM 
compared to the task-state. We assume that this is because the brain’s 
activity in the resting state is unconstrained and consequently contains 
more complex and unpredictable cognitive processes, which leads to a 
decrease in the proportion of variation attributed to MIC. This finding 
provides evidence to support the notion that the resting-state is essen-
tially a distinct type of task state characterized by unpredictable vari-
ability (Finn, 2021).

Finally,  it  is  important  to  note  that  although  we  compared  the 
identification rate between MIC and FCF, these two metrics are entirely 
separate and different from each other. The primary aim of this com-
parison is to utilize certain characteristics of FCF (individual specificity 
and stability) as a benchmark for validating MIC. In fact, the MIC is a 
spatial brain map extracted by ICA, while FCF shows the connections 
between different brain regions during dynamic activity. The findings 
we obtained also demonstrate various disparities between MIC and FCF. 
On the one hand, MIC exhibits greater stability than FCF, especially for 
different  fMRI  conditions.  On  the  other  hand,  standard  denoising 
methods that can significantly impact FCF have minimal effect on MIC, 
whereas, EVOM, which is intimately linked to the stability of MIC, does 
not have any relevance to FCF.

The  psychological  significance  of  the  individual-specific  baseline 
may be explained in terms of the basis model of self-specificity, which 
suggests  that  self-specificity  is  fundamentally  encoded  in  the  brain’s 
spontaneous activity (Northoff, 2016). Recent evidence supported this 
model by using resting-state functional connectivity to predict individ-
ual differences in self-prioritization (Zhang et al., 2023). Since we have 
proposed  that  MIC  is  a  better  indicator  of  brain  baseline  than 
resting-state,  we  assume  that  MIC  may  be  an  better  predictor  of 
self-specificity. This is an interesting question and need further research.
There are some limitations of this study. As previously stated, certain 
participants in HCP-YA exhibit a significantly reduced explained vari-
ance of MIC, resulting in a decreased identification rate. Further inquiry 
is  needed  to  determine  the  reasons  for  the  changing  of  the  baseline 
pattern in certain circumstances, or in other words, the prerequisites for 
a stable baseline. Furthermore, we exclusively utilized the HCP data for 

9 

W. Liu and X. Zhang                                                                                                                                                                                                                           

NeuroImage 303 (2024) 120925 

analysis.  Hence,  additional  research  is  required  to  see  if  this  funda-
mental trend can be replicated in other datasets.

In this study, we have mainly focused on the stability of MIC as well 
as its properties of being the brain baseline. Considering that the brain 
baseline should be characterized by its spatial and temporal dynamics 
(Northoff et al., 2023). Our next research will concentrate on the spatial 
characteristics  and  the  corresponding  temporal  dynamics  of  MIC.  Be-
sides,  another  planned  research  aims  to  investigate  whether  neuro-
developmental disorders or psychiatrics manifest a different temporal 
and spatial characteristics of MIC.

5. Conclusion

In conclusion, using ICA on a large sample of fMRI data from HCP, 
we have found that MIC is highly stable and individual-specific across 
different  fMRI  modalities  and  over  months.  The  stability  of  MIC  is 
closely related to its corresponding explained variance and is minimally 
influenced by factors such as noise, scan duration, and scan interval. We 
propose that MIC potentially represents an individual-specific baseline 
pattern of brain activity.

Ethical statement

HCP was approved by the Washington University Institutional Re-
view Board. Informed consent was obtained from all participants before 
take part in the project. We use the Open Access Data of HCP-YA, which 
is approved by the HCP after the author (Wei Liu) registering on Con-
nectomeDB and agreeing to the data use terms. The use of HCP-D and 
HCP-A data was approved by NDA (Data Access Request ID: 15555)

Data and code availability

All  imaging  data  come  from  publicly  available,  open  access  re-
positories. Human Connectome Project Young Adults and retest data can 
be accessed at https://db.humanconnectome.org/app/template/Login. 
vm after  signing  a  data  use  agreement.  Human  Connectome  Project 
Aging and Development data can be accessed at The National Institute of 
Mental Health Data Archive (NDA) after gaining approval from the NDA. 
Applying  procedures  can  be  found  at  https://nda.nih.gov/ccf/lifespa 
n-studies. Code for this study has been made available at https://gith 
ub.com/LIUWEI867/MIC-brain-baseline.

CRediT authorship contribution statement

Wei  Liu:  Writing  –  original  draft,  Visualization,  Validation,  Soft-
ware,  Resources,  Methodology,  Formal  analysis,  Conceptualization, 
Data curation. Xuemin Zhang: Writing – review & editing, Supervision, 
Resources, Funding acquisition, Conceptualization.

Declaration of competing interest

The authors declare that they have no known competing financial 
interests or personal relationships that could have appeared to influence 
the work reported in this paper.

Acknowledgements

The  present  study  was  supported  by  STI  2030–the  Major  Projects 
(2021ZD0200500)  &  STI2030-Major  Projects+2021ZD0204300.  The 
Key  Program  of  National  Natural  Science  Foundation  of  China 
(61632014).  Data  were  provided  by  the  Human  Connectome  Project, 
WU-Minn  Consortium  (principal  investigators,  D.  Van  Essen  and  K. 
Ugurbil; 1U54MH091657) funded by the 16 US National Institutes of 
Health (NIH) institutes and centers that support the NIH Blueprint for 
Neuroscience  Research;  and  by  the  McDonnell  Center  for  Systems 
Neuroscience at Washington University.

10 

Supplementary materials

Supplementary material associated with this article can be found, in 

the online version, at doi:10.1016/j.neuroimage.2024.120925.

References

Al-Aidroos, N., Said, C.P., Turk-Browne, N.B., 2012. Top-down attention switches 

coupling between low-level and high-level areas of human visual cortex. Proc. Natl. 
Acad. Sci. 109, 14675–14680. https://doi.org/10.1073/pnas.1202095109.
Allen, E.A., Damaraju, E., Plis, S.M., Erhardt, E.B., Eichele, T., Calhoun, V.D., 2014. 

Tracking whole-brain connectivity dynamics in the resting state. Cereb. Cortex 24, 
663–676. https://doi.org/10.1093/cercor/bhs352.

Amico, E., Go˜ni, J., 2018. The quest for identifiability in human functional connectomes. 

Sci. Rep. 8, 8254. https://doi.org/10.1038/s41598-018-25089-1.

Attwell, D., Laughlin, S.B., 2001. An Energy Budget for Signaling in the Grey Matter of 
the Brain. J. Cereb. Blood Flow Metab. 21, 1133–1145. https://doi.org/10.1097/ 
00004647-200110000-00001.

Bari, S., Amico, E., Vike, N., Talavage, T.M., Go˜ni, J., 2019. Uncovering multi-site 
identifiability based on resting-state functional connectomes. Neuroimage 202, 
115967. https://doi.org/10.1016/j.neuroimage.2019.06.045.

Beckmann, C.F., DeLuca, M., Devlin, J.T., Smith, S.M., 2005. Investigations into resting- 

state connectivity using independent component analysis. Philos. Trans. R. Soc. B 
Biol. Sci. 360, 1001–1013. https://doi.org/10.1098/rstb.2005.1634.

Beckmann, C.F., Smith, S.M., 2004. Probabilistic independent component analysis for 
functional magnetic resonance imaging. IEEE Trans. Med. Imaging 23, 137–152. 
https://doi.org/10.1109/TMI.2003.822821.

Buckner, R.L., DiNicola, L.M., 2019. The brain’s default network: updated anatomy, 

physiology and evolving insights. Nat. Rev. Neurosci. 20, 593–608. https://doi.org/ 
10.1038/s41583-019-0212-7.

Byrge, L., Kennedy, D.P., 2019. High-accuracy individual identification using a “thin 

slice” of the functional connectome. Netw. Neurosci. 3, 363–383. https://doi.org/ 
10.1162/netn_a_00068.

Calhoun, V.D., Adali, T., Pearlson, G.D., Pekar, J.J., 2001. Spatial and temporal 

independent component analysis of functional MRI data containing a pair of task- 
related waveforms. Hum. Brain Mapp. 13, 43–53. https://doi.org/10.1002/ 
hbm.1024.

Chen, S., Hu, X., 2018. Individual identification using the functional brain fingerprint 
detected by the recurrent neural network. Brain Connect. 8, 197–204. https://doi. 
org/10.1089/brain.2017.0561.

Cole, M.W., Bassett, D.S., Power, J.D., Braver, T.S., Petersen, S.E., 2014. Intrinsic and 
task-evoked network architectures of the human brain. Neuron 83, 238–251. 
https://doi.org/10.1016/j.neuron.2014.05.014.

Dubois, J., Galdi, P., Han, Y., Paul, L.K., Adolphs, R., 2018. Resting-state functional brain 
connectivity best predicts the personality dimension of openness to experience. 
Personal. Neurosci. 1, e6. https://doi.org/10.1017/pen.2018.8.

Elliott, M.L., Knodt, A.R., Cooke, M., Kim, M.J., Melzer, T.R., Keenan, R., Ireland, D., 
Ramrakha, S., Poulton, R., Caspi, A., Moffitt, T.E., Hariri, A.R., 2019. General 
functional connectivity: shared features of resting-state and task fMRI drive reliable 
and heritable individual differences in functional brain networks. Neuroimage 189, 
516–532. https://doi.org/10.1016/j.neuroimage.2019.01.068.

Fair, D.A., Schlaggar, B.L., Cohen, A.L., Miezin, F.M., Dosenbach, N.U.F., Wenger, K.K., 
Fox, M.D., Snyder, A.Z., Raichle, M.E., Petersen, S.E., 2007. A method for using 
blocked and event-related fMRI data to study “resting state” functional connectivity. 
Neuroimage 35, 396–405. https://doi.org/10.1016/j.neuroimage.2006.11.051.
Finn, Emily S., 2021. Is it time to put rest to rest? Trends Cogn. Sci. 25, 1021–1032. 

https://doi.org/10.1016/j.tics.2021.09.005.

Finn, E.S., Scheinost, D., Finn, D.M., Shen, X., Papademetris, X., Constable, R.T., 2017. 

Can brain state be manipulated to emphasize individual differences in functional 
connectivity? Neuroimage 160, 140–151. https://doi.org/10.1016/j. 
neuroimage.2017.03.064.

Finn, E.S., Shen, X., Scheinost, D., Rosenberg, M.D., Huang, J., Chun, M.M., 

Papademetris, X., Constable, R.T., 2015. Functional connectome fingerprinting: 
identifying individuals using patterns of brain connectivity. Nat. Neurosci. 18, 
1664–1671. https://doi.org/10.1038/nn.4135.

Glasser, M.F., Smith, S.M., Marcus, D.S., Andersson, J.L.R., Auerbach, E.J., Behrens, T.E. 

J., Coalson, T.S., Harms, M.P., Jenkinson, M., Moeller, S., Robinson, E.C., 
Sotiropoulos, S.N., Xu, J., Yacoub, E., Ugurbil, K., Van Essen, D.C., 2016. The human 
connectome project’s neuroimaging approach. Nat. Neurosci. 19, 1175–1187. 
https://doi.org/10.1038/nn.4361.

Glasser, M.F., Sotiropoulos, S.N., Wilson, J.A., Coalson, T.S., Fischl, B., Andersson, J.L., 
Xu, J., Jbabdi, S., Webster, M., Polimeni, J.R., Van Essen, D.C., Jenkinson, M., 
Consortium, WU-Minn HCP, 2013. The minimal preprocessing pipelines for the 
Human Connectome Project. Neuroimage 80, 105–124. https://doi.org/10.1016/j. 
neuroimage.2013.04.127.

Graff, K., Tansey, R., Rai, S., Ip, A., Rohr, C., Dimond, D., Dewey, D., Bray, S., 2022. 
Functional connectomes become more longitudinally self-stable, but not more 
distinct from others, across early childhood. Neuroimage 258, 119367. https://doi. 
org/10.1016/j.neuroimage.2022.119367.

Griffanti, L., Douaud, G., Bijsterbosch, J., Evangelisti, S., Alfaro-Almagro, F., Glasser, M. 
F., Duff, E.P., Fitzgibbon, S., Westphal, R., Carone, D., Beckmann, C.F., Smith, S.M., 
2017. Hand classification of fMRI ICA noise components. Neuroimage 154, 188–205. 
https://doi.org/10.1016/j.neuroimage.2016.12.036.

W. Liu and X. Zhang                                                                                                                                                                                                                           

NeuroImage 303 (2024) 120925 

Griffanti, L., Salimi-Khorshidi, G., Beckmann, C.F., Auerbach, E.J., Douaud, G., Sexton, C. 

E., Zsoldos, E., Ebmeier, K.P., Filippini, N., Mackay, C.E., Moeller, S., Xu, J., 
Yacoub, E., Baselli, G., Ugurbil, K., Miller, K.L., Smith, S.M., 2014. ICA-based artefact 
removal and accelerated fMRI acquisition for improved resting state network 
imaging. Neuroimage 95, 232–247. https://doi.org/10.1016/j. 
neuroimage.2014.03.034.

Gusnard, D.A., Raichle, M.E., 2001. Searching for a baseline: functional imaging and the 
resting human brain. Nat. Rev. Neurosci. 2, 685–694. https://doi.org/10.1038/ 
35094500.

Harms, M.P., Somerville, L.H., Ances, B.M., Andersson, J., Barch, D.M., Bastiani, M., 
Bookheimer, S.Y., Brown, T.B., Buckner, R.L., Burgess, G.C., Coalson, T.S., 
Chappell, M.A., Dapretto, M., Douaud, G., Fischl, B., Glasser, M.F., Greve, D.N., 
Hodge, C., Jamison, K.W., Jbabdi, S., Kandala, S., Li, X., Mair, R.W., Mangia, S., 
Marcus, D., Mascali, D., Moeller, S., Nichols, T.E., Robinson, E.C., Salat, D.H., 
Smith, S.M., Sotiropoulos, S.N., Terpstra, M., Thomas, K.M., Tisdall, M.D., 
Ugurbil, K., Van Der Kouwe, A., Woods, R.P., Z¨ollei, L., Van Essen, D.C., Yacoub, E., 
2018. Extending the human connectome project across ages: imaging protocols for 
the lifespan development and aging projects. Neuroimage 183, 972–984. https://doi. 
org/10.1016/j.neuroimage.2018.09.060.

He, B.J., 2013. Spontaneous and task-evoked brain activity negatively interact. 
J. Neurosci. Off. J. Soc. Neurosci. 33, 4672–4682. https://doi.org/10.1523/ 
JNEUROSCI.2922-12.2013.

Northoff, G., 2016. Is the self a higher-order or fundamental function of the brain? The 
“basis model of self-specificity” and its encoding by the brain’s spontaneous activity. 
Cogn. Neurosci. 7, 203–222. https://doi.org/10.1080/17588928.2015.1111868.

Northoff, G., Vatansever, D., Scalabrini, A., Stamatakis, E.A., 2023. Ongoing brain 

activity and its role in cognition: dual versus baseline models. Neuroscientist 29, 
393–420. https://doi.org/10.1177/10738584221081752.

Pallar´es, V., Insabato, A., Sanju´an, A., Kühn, S., Mantini, D., Deco, G., Gilson, M., 2018. 
Extracting orthogonal subject- and condition-specific signatures from fMRI data 
using whole-brain effective connectivity. Neuroimage 178, 238–254. https://doi. 
org/10.1016/j.neuroimage.2018.04.070.

Pham, D.D., Muschelli, J., Mejia, A.F., 2022. ciftiTools: a package for reading, writing, 
visualizing, and manipulating CIFTI files in R. Neuroimage 250, 118877. https://doi. 
org/10.1016/j.neuroimage.2022.118877.

Pruim, R.H.R., Mennes, M., Van Rooij, D., Llera, A., Buitelaar, J.K., Beckmann, C.F., 

2015. ICA-AROMA: a robust ICA-based strategy for removing motion artifacts from 
fMRI data. Neuroimage 112, 267–277. https://doi.org/10.1016/j. 
neuroimage.2015.02.064.

Raichle, M.E., Gusnard, D.A., 2002. Appraising the brain’s energy budget. Proc. Natl. 

Acad. Sci. 99, 10237–10239. https://doi.org/10.1073/pnas.172399499.

Raichle, M.E., Snyder, A.Z., 2007. A default mode of brain function: a brief history of an 

evolving idea. Neuroimage 37, 1083–1090. https://doi.org/10.1016/j. 
neuroimage.2007.02.041.

Horien, C., Noble, S., Finn, E.S., Shen, X., Scheinost, D., Constable, R.T., 2018. 

Rolfe, D.F., Brown, G.C., 1997. Cellular energy utilization and molecular origin of 

Considering factors affecting the connectome-based identification process: comment 
on Waller et al. Neuroimage 169, 172–175. https://doi.org/10.1016/j. 
neuroimage.2017.12.045.

Horien, C., Shen, X., Scheinost, D., Constable, R.T., 2019. The individual functional 

connectome is unique and stable over months to years. Neuroimage 189, 676–687. 
https://doi.org/10.1016/j.neuroimage.2019.02.002.

Hyv¨arinen, A., 1999. Fast and robust fixed-point algorithms for independent component 

analysis. IEEE Trans. Neural Netw. 10, 626–634. https://doi.org/10.1109/ 
72.761722.

Jalbrzikowski, M., Liu, F., Foran, W., Klei, L., Calabro, F.J., Roeder, K., Devlin, B., 

Luna, B., 2020. Functional connectome fingerprinting accuracy in youths and adults 
is similar when examined on the same day and 1.5-years apart. Hum. Brain Mapp. 
41, 4187–4199. https://doi.org/10.1002/hbm.25118.

Jurkiewicz, M.T., Crawley, A.P., Mikulis, D.J., 2018. Is rest really rest? resting-state 
functional connectivity during rest and motor task paradigms. Brain Connect. 8, 
268–275. https://doi.org/10.1089/brain.2017.0495.

standard metabolic rate in mammals. Physiol. Rev. 77, 731–758. https://doi.org/ 
10.1152/physrev.1997.77.3.731.

Salimi-Khorshidi, G., Douaud, G., Beckmann, C.F., Glasser, M.F., Griffanti, L., Smith, S. 
M., 2014. Automatic denoising of functional MRI data: combining independent 
component analysis and hierarchical fusion of classifiers. Neuroimage 90, 449–468. 
https://doi.org/10.1016/j.neuroimage.2013.11.046.

Schaefer, A., Kong, R., Gordon, E.M., Laumann, T.O., Zuo, X.-N., Holmes, A.J., 

Eickhoff, S.B., Yeo, B.T.T., 2018. Local-global parcellation of the human cerebral 
cortex from intrinsic functional connectivity MRI. Cereb. Cortex 28, 3095–3114. 
https://doi.org/10.1093/cercor/bhx179.

Smith, S.M., Beckmann, C.F., Andersson, J., Auerbach, E.J., Bijsterbosch, J., Douaud, G., 
Duff, E., Feinberg, D.A., Griffanti, L., Harms, M.P., Kelly, M., Laumann, T., Miller, K. 
L., Moeller, S., Petersen, S., Power, J., Salimi-Khorshidi, G., Snyder, A.Z., Vu, A.T., 
Woolrich, M.W., Xu, J., Yacoub, E., U˘gurbil, K., Van Essen, D.C., Glasser, M.F., WU- 
Minn HCP Consortium, 2013. Resting-state fMRI in the human connectome project. 
Neuroimage 80, 144–168. https://doi.org/10.1016/j.neuroimage.2013.05.039.

Krienen, F.M., Yeo, B.T.T., Buckner, R.L., 2014. Reconfigurable task-dependent 

Somerville, L.H., Bookheimer, S.Y., Buckner, R.L., Burgess, G.C., Curtiss, S.W., 

functional coupling modes cluster around a core functional architecture. Philos. 
Trans. R. Soc. Lond. B. Biol. Sci. 369, 20130526. https://doi.org/10.1098/ 
rstb.2013.0526.

Leonardi, N., Shirer, W.R., Greicius, M.D., Van De Ville, D., 2014. Disentangling dynamic 
networks: separated and joint expressions of functional connectivity patterns in time. 
Hum. Brain Mapp. 35, 5984–5995. https://doi.org/10.1002/hbm.22599.
Liu, J., Liao, X., Xia, M., He, Y., 2018. Chronnectome fingerprinting: identifying 

individuals and predicting higher cognitive functions using dynamic brain 
connectivity patterns. Hum. Brain Mapp. 39, 902–915. https://doi.org/10.1002/ 
hbm.23890.

Mathewson, K.E., Beck, D.M., Ro, T., Maclin, E.L., Low, K.A., Fabiani, M., Gratton, G., 
2014. Dynamics of alpha control: preparatory suppression of posterior alpha 
oscillations by frontal modulators revealed with combined EEG and event-related 
optical signal. J. Cogn. Neurosci. 26, 2400–2415. https://doi.org/10.1162/jocn_a_ 
00637.

Mckeown, M.J., Makeig, S., Brown, G.G., Jung, T.-P., Kindermann, S.S., Bell, A.J., 

Sejnowski, T.J., 1998. Analysis of fMRI data by blind separation into independent 
spatial components. Hum. Brain Mapp 6, 160–188. https://doi.org/10.1002/(SICI) 
1097-0193(1998)6:3<160::AID-HBM5>3.0.CO;2-1.

Michon, K.J., Khammash, D., Simmonite, M., Hamlin, A.M., Polk, T.A., 2022. Person- 
specific and precision neuroimaging: current methods and future directions. 
Neuroimage 263, 119589. https://doi.org/10.1016/j.neuroimage.2022.119589.

Dapretto, M., Elam, J.S., Gaffrey, M.S., Harms, M.P., Hodge, C., Kandala, S., 
Kastman, E.K., Nichols, T.E., Schlaggar, B.L., Smith, S.M., Thomas, K.M., Yacoub, E., 
Van Essen, D.C., Barch, D.M., 2018. The lifespan human connectome project in 
development: a large-scale study of brain connectivity development in 5–21 year 
olds. Neuroimage 183, 456–468. https://doi.org/10.1016/j. 
neuroimage.2018.08.050.

Sui, J., Adali, T., Pearlson, G.D., Calhoun, V.D., 2009. An ICA-based method for the 
identification of optimal FMRI features and components using combined group- 
discriminative techniques. Neuroimage 46, 73–86. https://doi.org/10.1016/j. 
neuroimage.2009.01.026.

Wainio-Theberge, S., Wolff, A., Northoff, G., 2021. Dynamic relationships between 

spontaneous and evoked electrophysiological activity. Commun. Biol. 4, 741. 
https://doi.org/10.1038/s42003-021-02240-9.

Waller, L., Walter, H., Kruschwitz, J.D., Reuter, L., Müller, S., Erk, S., Veer, I.M., 2017. 

Evaluating the replicability, specificity, and generalizability of connectome 
fingerprints. Neuroimage 158, 371–377. https://doi.org/10.1016/j. 
neuroimage.2017.07.016.

Zhang, Y., Wang, F., Sui, J., 2023. Decoding individual differences in self-prioritization 
from the resting-state functional connectome. Neuroimage 276, 120205. https://doi. 
org/10.1016/j.neuroimage.2023.120205.

11 

