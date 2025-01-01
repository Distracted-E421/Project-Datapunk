NeuroImage 303 (2024) 120923 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Processing demands modulate the activities and functional connectivity 
patterns of the posterior (VWFA-1) and anterior (VWFA-2) VWFA

Aqian Li a,b,c,d, Chuansheng Chen e, Xiaoyan Wu a,b,c,d,  
Yuan Feng a,b,c,d, Jingyu Yang a,b,c,d, Xiaoxue Feng a,b,c,d,  
Rui Hu a,b,c,d, Leilei Mei a,b,c,d,*
a Philosophy and Social Science Laboratory of Reading and Development in Children and Adolescents (South China Normal University), Ministry of Education, China
b Center for Studies of Psychological Application, South China Normal University, 510631, Guangzhou, China
c Key Laboratory of Brain, Cognition and Education Sciences (South China Normal University), Ministry of Education, China
d Guangdong Key Laboratory of Mental Health and Cognitive Science, South China Normal University, 510631, Guangzhou, China
e Department of Psychological Science, University of California, Irvine, CA, USA

A R T I C L E  I N F O

A B S T R A C T

Keywords:
VWFA
Functional connectivity
Processing demands
gPPI
DCM

Previous  studies  have  shown  that  the  visual  word  form  area  (VWFA)  has  structural  and  intrinsic  functional 
connectivity  with  both  language  and  attention  networks.  Nevertheless,  it  is  still  unclear  how  the  functional 
connectivity  pattern  of  the  VWFA  is  regulated  by  processing  demands  induced  by  experimental  tasks,  and 
whether processing demands differentially regulate the posterior (VWFA-1) and anterior (VWFA-2) subregions of 
the VWFA. To address these questions, the present study adopted two tasks varying in processing demands (i.e., 
verbal and non-verbal tasks), and used generalized psychophysiological interaction (gPPI) and dynamic causal 
modeling (DCM) analyses to explore the task-dependent functional connectivity patterns of the two subregions of 
the VWFA. Activation analysis revealed that the VWFA-2 showed higher activation for the verbal task than the 
non-verbal  task,  while  there  were  no  activation  differences  in  the  VWFA-1  after  controlling  for  the  stimulus 
driven effects. Functional and effective connectivity analyses revealed that, for both VWFA-1 and VWFA-2, the 
verbal  task  enhanced  connections  from  VWFAs  to  the  ventral  language  regions  (e.g.,  the  left  orbital  frontal 
cortex), while the non-verbal task enhanced connections from VWFAs to the dorsal visuospatial regions (e.g., the 
left  intraparietal  sulcus).  Results  of  the  present  study  indicate  that  processing  demands  induced  by  tasks 
modulate both the local activity and functional connectivity patterns of the VWFA, providing new insights for 
understanding its domain-general function.

1. Introduction

The left ventral occipitotemporal cortex (vOT) is known to be crucial 
for recognizing visual words (Price and Devlin, 2011; Taylor et al., 2019; 
Vinckier  et  al.,  2007).  It  is  centered  on  the  occipitotemporal  sulcus, 
extending laterally over the medial crest of the inferior temporal gyrus 
and  medially  onto  the  lateral  crest  of  the  fusiform  gyrus  (Price  and 
Devlin, 2011). The visual word form area (VWFA), which is located in 
the middle of the left vOT, has been extensively studied and discussed 
over the past two decades (e.g., Cohen and Dehaene, 2004; McCandliss 
et al., 2003; Lerma-Usabiaga et al., 2018). As for the functional role of 
the  VWFA,  numerous  neuroimaging  studies  have  revealed  that  the 
VWFA  shows  greater  activation  for  orthographic  symbols,  including 

letters  and  words,  as  compared  to  a  variety  of  other  visual  stimuli 
(Cohen  et  al.,  2002;  Cohen  and  Dehaene,  2004;  Baker  et  al.,  2007; 
Gaillard et al., 2006; Glezer et al., 2009; Hannagan et al., 2015; Polk 
et  al.,  2002;  Vinckier  et  al.,  2007).  Based  on  these  findings,  the  pre-
dominant  model  of  the  VWFA  function  states  that  the  VWFA  plays  a 
specific  role  in  decoding  written  forms  of  words  (Cohen  et  al.,  2002; 
Dehaene and Cohen, 2011; McCandliss et al., 2003). In contrast, other 
studies have revealed strong activation in the VWFA not only for written 
words, but also for various types of visual stimuli, such as faces, objects, 
numerical symbols, line drawings, and gratings (Grotheer et al., 2018; 
Kherif et al., 2011; Mei et al., 2010; Peters et al., 2015; Ploran et al., 
2007; Tagamets et al., 2000; Van Doren et al., 2010; Vogel et al., 2012a; 
Xue et al., 2006), implying that the VWFA is not exclusively specialized 

* Corresponding author at: School of Psychology, South China Normal University, Guangzhou, 510631, China

E-mail address: mll830925@126.com (L. Mei). 

https://doi.org/10.1016/j.neuroimage.2024.120923
Received 13 April 2024; Received in revised form 14 October 2024; Accepted 7 November 2024  
Available online 8 November 2024 
1053-8119/© 2024 The Author(s). Published by Elsevier Inc. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ). 

A. Li et al.                                                                                                                                                                                                                                        

NeuroImage 303 (2024) 120923 

for written words, but may play a more general role in visual processing.
In  addition  to  the  local  activity  of  the  VWFA,  recent  studies  have 
attempted  to  understand  the  functional  and  structural  connectivities 
between  the  VWFA  and  other  brain  regions  (Price  and  Devlin,  2011; 
Saygin et al., 2016). Several such studies have found that the VWFA is a 
part of both language and attention circuitries (e.g., Chen et al., 2019; 
Vogel  et  al.,  2012b;  Yeatman  et  al.,  2021).  It  has  been  reported  that 
attentional  systems  play  a  key  role  in  VWFA  function  by  tuning  and 
amplifying  a  range  of  visual  stimuli  for  use  and  distribution  to  other 
brain systems (Kay et al., 2017; Vogel et al., 2014). Attentional systems 
contain  two  distinct  frontoparietal  networks:  the  dorsal  attention 
network (such as the intraparietal sulcus, the junction of the precentral 
gyrus, and the frontal eye field) and the ventral attention network (such 
as the temporal-parietal junction and the ventrolateral frontal cortex) 
(Corbetta and Shulman, 2002). Neuroimaging evidence suggests that the 
intraparietal  sulcus  (IPS)  is  critical  for  mediating  spatial  working 
memory and shifts in spatial attention (Silk et al., 2010). The frontal eye 
field  (FEF)  and  inferior-frontal  junction  (IFJ)  encode  spatial  and 
nonspatial  (such  as  feature-  or  object-based)  representations,  respec-
tively, during visual attention and working memory tasks (Bedini and 
Baldauf, 2021, 2023, 2024; Soyuhos and Baldauf, 2023). The IFJ was 
found to direct the flow of visual processing during object-based atten-
tion (Baldauf and Desimone, 2014). In terms of structural connectivity, 
the VWFA has been found to be connected to Broca’s area (a region for 
high-level language processing) through the arcuate fasciculus (Catania 
and Mesulam, 2008), and to the IPS (a region for visuospatial attention) 
through the vertical occipital fasciculus (Bullock et al., 2019; Kay et al., 
2017; Takemura et al., 2016; Yeatman et al., 2013, 2014). Consistent 
with  structural  connections,  research  on  resting-state  functional  con-
nectivity (rsFC) also found that the VWFA had intrinsic connections with 
language-related network, such as the lateral prefrontal cortex, superior 
temporal sulcus, and inferior parietal cortex (Bouhali et al., 2014; Chen 
et al., 2019; Li et al., 2017; L´opez-Barroso et al., 2020; Stevens et al., 
2017; Yeatman et al., 2013), as well as with the fronto-parietal attention 
network, including the IPS, FEF, and middle temporal visual area (Chen 
et al., 2019; Vogel et al., 2012b). The VWFA’s structural and intrinsic 
functional connectivity with the language and attention networks may 
form the neural basis of its multiple functions. Consistent with this view, 
further  studies  on  brain-behavior  relation  showed  that  individuals’ 
language and attention abilities were predicted by the anatomical con-
nections  of  VWFA-language-network  and  VWFA-attention-network, 
respectively (Chen et al., 2019).

In  contrast  to  the  accumulating  research  on  rsFC  and  structural 
connectivity  of  the  VWFA,  there  are  scarce  studies  on  the  task- 
dependent  functional  connectivity  of  the  VWFA.  To  the  best  of  our 
knowledge,  three  studies  attempted  to  probe  the  effect  of  processing 
demands (induced by task) on the functional connectivity of the VWFA 
(Chauhan  et  al., 2024;  Chen  et  al., 2019;  White  et  al.,  2023). Specif-
ically,  Chen  et  al.,  (2019) found  that  the  VWFA  enhanced  functional 
connectivity to both language and attention networks when performing 
the reading task (i.e., the rhyme judgment task), and to attention net-
works when performing the attention task (i.e., the Flanker task). White 
et al., (2023) revealed that in contrast to the non-linguistic task (i.e., the 
gap task), the lexical decision task elicited stronger functional connec-
tivity  between  the  VWFA  and  Broca’s  region.  Chauhan  et  al.,  (2024)
further used English words and unfamiliar characters with matched vi-
sual features as materials, and found that for both types of materials, the 
functional  connectivity  between  the  VWFA  and  Broca’s  region  was 
greater during the lexical decision task (i.e., detecting real words) than 
the fixation task (i.e., detecting color in the fixation mark).

Although  previous  studies  have  found  that  the  functional  connec-
tivity of the VWFA was regulated by processing demands, there are still 
some unresolved issues. First, the direction of information flow between 
the VWFA and high-level frontoparietal cortex during different tasks is 
unclear. Therefore, effective connectivity analysis is needed to address 
this  issue.  Second,  recent  studies  have  identified  two  VWFAs  (i.e., 

VWFA-1 and VWFA-2) in the left ventral occipitotemporal cortex and 
suggested that the VWFA-1 (the posterior subregion) and VWFA-2 (the 
anterior subregion) are responsible for visuoperceptual and lexical as-
pects  of  words,  respectively  (Lerma-Usabiaga  et  al.,  2018;  Yablonski 
et al., 2024; Yeatman and White, 2021). However, only a few studies (e. 
g.,  Chauhan  et  al.,  2024)  have  investigated  whether  the  functional 
connectivity patterns differ across the two subregions of the VWFA and 
whether they are differentially regulated by processing demands.

The current study aimed to explore task-dependent functional con-
nectivity patterns among the two VWFAs and high-level frontoparietal 
regions by using effective connectivity analysis. Sixty-two native Chi-
nese speakers conducted a localizer task and two experimental tasks (i. 
e., the verbal task and the non-verbal task) during functional magnetic 
resonance imaging (fMRI) scanning. To eliminate the potential stimulus 
driven  effects  between  the  two  tasks,  both  high-level  and  low-level 
conditions  were  included  for  each  task.  The  low-level  condition  was 
included to control for the stimulus driven effects across the two tasks. 
Following  previous  studies  (Can´ario  et  al.,  2020;  Cohen  et  al.,  2002; 
Glezer and Riesenhuber, 2013; Lerma-Usabiaga et al., 2018; White et al., 
2019),  we  first  defined  VWFA-1  and  VWFA-2  as  regions  of  interest 
(ROIs)  for  each  participant  based  on  the  localizer  task.  Second,  we 
examined the effects of processing demands on BOLD responses, func-
tional  connectivity,  and  effective  connectivity  of  the  two  VWFAs  by 
using  activation  analysis,  psychophysiological  interaction  (PPI)  anal-
ysis, and dynamic causal modeling (DCM), respectively. Based on the 
functional  differences  between  the  two  subregions  of  the  VWFA 
(Lerma-Usabiaga et al., 2018; Yeatman and White, 2021) and previous 
findings  on  the  VWFA  circuits  (Chen  et  al.,  2019;  Kay  and  Yeatman, 
2017; White et al., 2023), we expected that 1) the VWFA-2 would show 
higher activation for the verbal task than the non-verbal task, and the 
VWFA-1 would show no difference in activation between the two tasks; 
and 2) the VWFAs would show a stronger connection with regions in the 
language  network  (e.g.,  the  left  inferior  frontal  gyrus),  and  a  weaker 
connection  with  regions  in  the  visuospatial  network  (e.g.,  the  left 
intraparietal  sulcus)  during  the  verbal  task  relative  to  the  non-verbal 
task.

2. Materials and methods

2.1. Participants

Sixty-two  native  Chinese  speakers  participated  in  the  study  (27 
males, mean age = 21.61 ± 2.46 years, range: 18–25 years). They had 
normal or corrected-to-normal eyesight, and did not have any prior in-
stances of head trauma or neurological or mental disorders. We assessed 
the  handedness  of  each  participant  using  the  Edinburgh  Handedness 
Inventory (Snyder et al., 1993). All of the participants included in this 
study were right-handed (mean = 74.97 ± 26.26). Before the experi-
ment, they provided written informed consent. The research received 
approval  from  the  Institutional  Review  Board  (IRB)  of  the  School  of 
Psychology at South China Normal University.

2.2. Materials and fMRI tasks

The  fMRI  scans  included  the  localizer  task,  verbal  task  and  non- 
verbal  task  (Fig.  1).  Each  task  contained  two  runs.  The  localizer  task 
aimed to identify the VWFA-1 and VWFA-2. The verbal and non-verbal 
tasks  were  adopted  to  explore  task-based  neural  responses  in  the 
VWFAs, as well as their connections to high-level frontoparietal cortex. 
The order of verbal  and non-verbal tasks was  counterbalanced across 
participants. Block design was used for the three tasks. Before the fMRI 
scan, participants were given a practice session to be familiarized with 
the procedure. The materials used in the practice session were not pre-
sented during the fMRI scan.

During the localizer task, participants viewed sequences of stimuli 
from  four  different  categories:  Chinese  characters,  scrambled  images, 

2 

A. Li et al.                                                                                                                                                                                                                                        

NeuroImage 303 (2024) 120923 

Fig. 1. Experimental designs for the fMRI tasks. (A) In the localizer task, participants were instructed to carefully view the stimuli and to make a response when they 
saw a stimulus that was framed with black lines. (B) In the verbal task, participants were instructed to judge whether the second Chinese character rhymed with (the 
rhyme judgment task) or was semantically related to (the semantic judgment task) the first one in the high-level condition, and whether the second stimulus was 
identical to the first one in the low-level condition. (C) In the non-verbal task, participants were instructed to keep track of the locations of the highlighted cells, and 
then chose the grid containing all locations in the four preceding grids from the two options.

false fonts, and facial images (Fig. 1A). Each type of materials had 52 
items. Chinese characters and scrambled images were used to localize 
the  VWFAs,  and  the  other  two  types  of  materials  were  included  for 
reasons not related to this study and hence omitted from the following 
data analyses. The Chinese characters consisted of 5–13 strokes (mean =
8.33 ± 0.31) with high usage frequency (mean = 581.52 ± 60.86 per 
million  words)  (Cai  and  Brysbaert,  2010).  Scrambled  images  were 
created by scrambling the Chinese character images with a 4-pixel tile 
size (FischerBaum et al., 2017). Each of the localizer run consisted of 16 
blocks,  with  4  blocks  for  each  category  of  materials.  Blocks  were  ar-
ranged in Latin square order. Task blocks were interspersed with 12 s 
fixation  blocks.  There  were  14  trials  in  each  block.  In  each  trial,  the 
stimulus was presented for 0.2 s, followed by a 0.8 s fixation. To ensure 
that participants were attentive to the stimuli, they were instructed to 
press a button when they saw a stimulus that was framed with black 
lines. Each of the localizer run lasted for 428 s.

For the verbal task (Fig. 1B), since phonological and semantic pro-
cessing are both important high-level processes in reading (Seidenberg, 
2005),  the  high-level  condition  contained  phonological  (i.e.,  rhyme 
judgment)  and  semantic  (i.e.,  semantic  judgment)  tasks.  Seventy-two 
pairs of Chinese characters were used for high-level linguistic process-
ing: 36 pairs for rhyme judgment and 36 pairs for semantic judgment. 
These characters consisted of 2–13 strokes (mean = 6.70 ± 2.40) with 
medium to high usage frequency (mean = 75.11 ± 114.05 per million 
words). For the 36 pairs of Chinese characters used for rhyme judgment, 
half of the pairs rhymed (e.g., “谷”/gu3/, “库”/ku4/), and the other half 
did not (e.g., “改”/gai3/, “劫”/jie2/). For the 36 pairs of Chinese char-
acters used for semantic judgment, half pairs were semantically related 
(e.g.,  “花”/flower/,  “叶”/leaf/)  and  the  other  half  were  not  (e.g., 
“沙”/sand/, “肚”/belly/). In addition, 36 pairs of false fonts were used 
for  low-level  perceptual  processing.  They  consisted  of  3–12  strokes 
(mean = 6.69 ± 1.93) and were constructed by scrambling the strokes of 

3 

A. Li et al.                                                                                                                                                                                                                                        

NeuroImage 303 (2024) 120923 

the characters to ensure that they had similar orthographic complexity 
to the real words without linguistic features (Xu et al., 2017). Half pairs 
were identical and the other half were different. Each run of the verbal 
task consisted of 9 blocks, with 6 blocks for high-level processing (i.e., 
rhyme  judgment  and  semantic  judgment),  and  3  blocks  for  low-level 
processing  (i.e.,  perceptual  judgment).  The  blocks  followed  a  Latin 
square order, and were interleaved with 16 s fixation. We used different 
colors of fixations before the two types of high-level blocks (i.e., green 
for rhyme judgment and blue for semantic judgment) to let participants 
know  the  nature  of  the  subsequent  task.  There  were  6  trials  in  each 
block.  Every  trial  started  with  a  0.5  s  fixation,  followed  by  two 
sequentially presented stimuli. The first stimulus (Chinese characters or 
false  fonts)  was  presented  for  0.5  s.  After  a  0.5  s  blank,  the  second 
stimulus was presented for up to 2.5 s and disappeared once a response 
was made. Participants had to judge whether the second stimulus was 
identical / rhymed / semantically related / with the first one via a button 
press. Each of the verbal run lasted for 376 s.

The non-verbal  task  is  a spatial working  memory task  (Fedorenko 
et  al.,  2011)  that  demands  more  visuospatial  attention  than  does  the 
verbal task. It contained low-level and high-level conditions (Fig. 1C). 
There were 96 pairs of stimuli, with half of the pairs used for high-level 
condition, and the other half used for low-level condition. The materials 
were 3 × 4 grids with some cells highlighted in blue. The grids had no 
verbal information. Each run consisted of 6 blocks of low-level condi-
tion, 6 blocks of high-level condition, and 4 blocks of fixation. The three 
types of blocks were randomly presented in each run. There were 4 trials 
in each task block. Each trial started with a 0.5 s fixation, followed by 
sequentially presented grids across four steps. Each of the steps lasted for 
1 s and highlighted one cell in the low-level condition and two cells in 
the high-level condition. Participants had to keep track of the locations 
of the highlighted cells, and then chose the grid containing all locations 
in the four preceding grids from the two options (the incorrect option 
contained one to two wrong locations) by pressing one of the two but-
tons on the decision phase. The decision phase was presented for up to 
3.5 s. For the non-verbal task, each run lasted for 448 s.

2.3. MRI data acquisition

All  MRI images were collected using a  3.0  T Siemens Prisma MRI 
scanner in the MRI Center at South China Normal University. Functional 
images  were  acquired  with  a  single-shot  T2*-weighted  gradient-echo 
EPI  sequence  (58  axial  slices,  TR  = 2000  ms,  TE  = 30  ms,  θ  = 90
, 
matrix size = 112 × 112, slice thickness = 2 mm, FOV = 224 × 224 mm). 
Anatomical  images  were  acquired  with  a  T1-weighted,  three-dimen-
sional, gradient-echo pulse-sequence (176 sagittal slices, TR = 2530 ms, 
◦
TE = 1.94 ms, θ = 7
, matrix size = 256 × 256, slice thickness = 1 mm, 
FOV = 256 × 256 mm).

◦

2.4. Activation analysis

FEAT Version 6.00 in FSL (http://www.fmrib.ox.ac.uk/fsl) was used 
for data preprocessing. To get steady-state imaging, the first six volumes 
of each run were eliminated. The remaining images were then motion- 
corrected. Translational movement parameters never exceeded 1 voxel 
(2 mm) in any direction for any participant or run. A nonlinear high-pass 
filter with a 60-second cutoff was utilized to temporally filter the data. 
Gaussian kernel with a full-width-half-maximum (FWHM) of 5 mm was 
employed to spatially smooth the functional data. The functional images 
were first aligned with the MPRAGE structural image and then regis-
tered  to  the  standard  Montreal  Neurological  Institute  (MNI)  template 
(Jenkinson et al., 2001).

At  the  first  level  of  activation  analysis,  the  general  linear  model 
(GLM) was applied to model the preprocessed data for each participant 
and each run. The onsets and durations of the events were convolved 
with a double-gamma hemodynamic response function to generate the 
regressors used in the GLM. The 6 motion parameters (3 translations and 

3 rotations) and temporal derivatives were included as covariates of no 
interest  to  improve  statistical  sensitivity.  In  the  localizer  task,  the 
contrast of Chinese characters minus scrambled images was computed 
for each participant and for each run to define the VWFAs. In the main 
experiment (i.e., the verbal and nonverbal tasks), two GLMs were esti-
mated. In the first GLM, the high-level and low-level condition blocks in 
each  task  were  modeled  as  two  regressors,  with  the  fixation  blocks 
serving as the baseline. In the second model, we modeled the high-level 
condition  as  regressors,  with  the  low-level  condition  serving  as  the 
baseline to eliminate the stimulus driven effects (Vogel et al., 2012b). 
For  both  models,  the  contrast  image  of  high-level  condition  minus 
baseline in each task was computed for each participant and each run.
Then, a  fixed-effects  model was  used  to get  the  averaged  imaging 
data  across  2  runs  of  each  task.  Finally,  the  third-level  models  were 
constructed to get group activations by using a random-effects model 
(Beckmann et al., 2003). All reported group images were thresholded 
with a height threshold of Z > 3.1 and a cluster probability of p < .05, 
corrected  for  whole-brain  multiple  comparisons  using  the  Gaussian 
random field theory (Worsley, 2001).

2.5. Region of interest analysis

All of the ROIs were defined in volumetric space. To examine task- 
based neural responses and functional connectivity of the VWFA-1 and 
VWFA-2,  we  functionally  defined  individuals’  VWFAs  around  the  left 
occipito-temporal sulcus (OTS) based on the localizer scan. Specifically, 
we raised the threshold from Z = 1.96 until the number of contiguous 
surviving voxels fell in between 50 and 100 around the coordinates of 
the VWFA-1 (MNI coordinates: (cid:0) 43 (cid:0) 69 (cid:0) 12) and VWFA-2 (MNI co-
ordinates: (cid:0) 43 (cid:0) 54 (cid:0) 12) reported in previous literature (Can´ario et al., 
2020; Cohen et al., 2002; Glezer and Riesenhuber, 2013; White et al., 
2019). The two ROIs failed to be defined in three participants, resulting 
in 59 participants in subsequent analyses (for the detailed coordinates, 
please see Supplementary Table 1).

To  compare  the  neural  activations  between  the  verbal  and  non- 
verbal  tasks,  we  extracted  percent  signal  changes  in  the  two  VWFAs. 
Similar to the activation analysis above, we computed the percent signal 
changes in the VWFAs separately from the contrast of high-level con-
dition vs. fixation and that of high-level condition vs. low-level condi-
tion. The beta values were extracted and then averaged across all voxels 
in the ROI for each participant. The percent signal changes in each ROI 
were estimated by using the following formula: 

[contrast image / (mean of run)] × ppheight × 100% 

The contrast image represents the hemodynamic response in contrast 
of high-level vs. fixation or high-level vs. low-level, ppheight represents 
the peak height of the hemodynamic response versus the baseline level 
of activity. Finally, for the percent signal changes of VWFAs, we con-
ducted 2 (task: verbal task, non-verbal task) × 2 (subregion: VWFA-1, 
VWFA-2) repeated-measures ANOVA separately for the two contrasts.

To  compute  the  functional  connectivity  between  the  VWFAs  and 
high-level frontoparietal cortex, the left orbital frontal cortex (OFC, MNI 
coordinates:  (cid:0) 33  36  (cid:0) 15)  and  intraparietal  sulcus  (IPS,  MNI  co-
ordinates: (cid:0) 21 (cid:0) 60 51) were additionally defined as ROIs based on peak 
activations in the contrast of the verbal (high-level condition vs. fixa-
tion) minus non-verbal (high-level condition vs. fixation) task and in the 
reverse contrast, respectively (Fig. 2A). The left OFC and IPS have been 
reported to be, respectively, critical for high-level language processing 
and visuospatial processing (Lauritzen et al., 2009; Saur et al., 2008), 
and to be functionally and structurally connected to the VWFA (Yeatman 
and White, 2021). For each subject, ROIs were defined as 6-mm spher-
ical volumes centered at the peak activation voxels by searching voxels 
that survived at the threshold of Z > 2.3, uncorrected. The left OFC and 
IPS were successfully defined in all 59 participants.

Finally, as an additional verification, we employed two additional 
approaches to define the  IPS and OFC. First,  the left  IPS was defined 

4 

A. Li et al.                                                                                                                                                                                                                                        

NeuroImage 303 (2024) 120923 

Fig. 2. Brain activations during the verbal and non-verbal tasks. (A) Brain activations for non-verbal > verbal tasks (the upper panel) and verbal > non-verbal tasks 
(the lower panel) with the fixation as baseline. Brain maps were thresholded at Z > 3.1 (whole-brain corrected). The left OFC and IPS outlined in black showed peak 
activation of the verbal task vs. non-verbal task contrast, and were defined as two ROIs for the functional connectivity analysis. (B) The bar chart displays the percent 
signal changes in VWFA-1 and VWFA-2 during the verbal and non-verbal tasks. The right panel shows the locations of the VWFA-1 and VWFA-2 defined for one 
representative participant. ***p < 0.001.

based  on  the  Human  Connectome  Project  Multi-Modal  Parcellation 
version 1.0 atlas (HCP-MMP 1.0) (Glasser et al., 2016), and the left OFC 
was  defined  based  on  the  automated  anatomical  atlas  (AAL) 
(Tzourio-Mazoyer et al., 2002) (Supplementary Fig. 2A). Second, the left 
OFC and IPS were redefined based on the peak activations in the contrast 
of  the  verbal  task  (low-level  condition  vs.  fixation)  minus  non-verbal 
task (low-level condition vs. fixation) and in the reverse contrast (Sup-
plementary  Fig.  3A).  ROIs  were  defined  as  6-mm  spherical  volumes 
centered at the peak activation voxels (OFC: -39 33 -13, IPS: -24 -60 48) 
(Supplementary Fig. 3B).

2.6. Generalized psychophysiological interaction analysis

To examine how whole-brain functional connectivity with the VWFA 
was affected by task demands, we performed generalized psychophysi-
ological  interaction  (gPPI)  analysis  (McLaren  et  al.,  2012),  which  is 
especially  suited  for  assessing  functional  connectivity  in  block-design 
experiments  (Cisler  et  al.,  2014).  In  this  analysis,  the  VWFA-1  and 
VWFA-2 were used as two seed regions. The physiological variable was 
the time series from the seed region, and the psychological variable was 
the contrast vector representing the task effect (high-level condition vs. 
fixation in the verbal and non-verbal tasks). These regressors and their 
interaction were estimated for each participant. The results from these 
analyses  were  further  averaged  across  participants  in  the  group-level 
analysis with the same threshold as in the activation analysis above.

To  specifically  investigate  functional  connectivity  between  the 
VWFAs and the two high-level regions (i.e., the left OFC and IPS) in the 
two tasks, we further performed ROI-based gPPI analysis. Specifically, 
the time series of the BOLD signal (high-level condition vs. fixation in 
the verbal task or non-verbal task) for each ROI served as a physiological 
regressor.  The  psychological  regressor  was  a  contrast  vector  of  high- 
level condition vs. fixation in the verbal task and nonverbal task. Beta 
values were then extracted to measure the strength of functional con-
nectivity between the VWFAs and the two brain areas (i.e., the left OFC 
and  IPS)  interacted  in  a  task-dependent  manner  for  each  participant. 
Results were transformed into Fisher’s Z-scores. Finally, we conducted 2 
(task: verbal task, non-verbal task) × 2 (subregion: VWFA-1, VWFA-2) 
repeated-measures ANOVAs on the PPI values of VWFA-OFC and VWFA- 
IPS, respectively.

2.7. Dynamic causal modeling

To specify task-induced changes in directional information flow be-
tween the VWFAs and the two high-level regions (i.e., the left OFC and 
IPS), we performed DCM analysis (Friston et al., 2003).

The cortical dynamics of the neuronal populations in brain regions 
were modeled using the differential equations: dx/dt = (A + uB) x + Cu, 
where vector x represents the neural state of brain regions (high-level 
condition vs. fixation in the verbal task or non-verbal task), and vector u 
represents external input. Matrix A represents the connection when no 
external  input  exists.  Because  the  three  regions  have  been  found  to 
intrinsically and anatomically connect via the vertical occipital fascic-
ulus  and  the  arcuate  fasciculus  (Yablonski  et  al.,  2024;  Yeatman  and 
White, 2021), we assumed that a reciprocal fixed connection between 
each  pair of the  brain regions  existed, and thus  all parameters  in the 
matrix A would be set to a nonzero value (Stephan, et al., 2010). Matrix 
B  represents  the  modulation  of  the  connections  by  the  experimental 
manipulation  (i.e.,  external  inputs).  In  the  present  study,  this  is  the 
verbal task or non-verbal task. Matrix C quantifies how brain regions 
respond to external stimuli. The external inputs are commonly regarded 
as sensory stimuli. In this study, the visual stimuli from the verbal or 
non-verbal tasks served as driving input. The network comprised three 
nodes: the VWFA, OFC, and IPS. As the VWFA was widely regarded as an 
interface between bottom-up sensory inputs and top-down predictions 
(Price  et  al.,  2011),  we  assumed  that  the  driving  inputs  entered  the 
network  through  the  VWFA  node.  All  nonzero  parameters  in  the 
matrices were assumed to follow a Gaussian distribution.

In each subject, eigenvectors (i.e., time series) were extracted from 
each ROI (i.e., VWFA-1, VWFA-2, left OFC and IPS) for the verbal and 
non-verbal  tasks  separately.  The  VWFA-1,  OFC,  and  IPS  in  the  left 
hemisphere constituted the nodes of the first model, and the VWFA-2, 
OFC, and IPS in the left hemisphere constituted the nodes of the sec-
ond model. They were both fully connected (all forward and backward 
connections specified) (the left panel in Fig. 4). Any combination of six 
directed connections among the three regions can be modulated by the 
experimental task, resulting in 63 (i.e., 26  - 1) models being estimated 
and compared for each network (i.e., VWFA1-IPS-OFC and VWFA2-IPS- 
OFC) under each task (i.e., verbal task and non-verbal task).

All parameters of DCM models and their posterior probabilities were 
assessed using Bayesian inversion by means of expectation and maxi-
mization  (Friston  et  al.,  2003).  For  each  participant,  Bayesian  model 
average  (BMA)  analysis  was  conducted  to  get  averaged  connectivity 
values for each connection across all models. Finally, one sample t-test 
was used to examine the statistical significance of modulation (nonzero 
parameters  in  matrix  B)  across  59  subjects  based  on  individual  BMA 
results with a threshold of p < 0.05 (FWE corrected). To eliminate the 
stimulus driven effects, we additionally performed the DCM analyses by 
using the low-level conditions as the baseline (described in 2.4 Activation 
analysis).

5 

A. Li et al.                                                                                                                                                                                                                                        

NeuroImage 303 (2024) 120923 

3. Results

3.1. Behavioral performance

The mean accuracies for the verbal task and the non-verbal task were 
0.95 (SD = 0.04) and 0.78 (SD = 0.06), respectively. The mean reaction 
times for the verbal task and the non-verbal task were 763.59 ms (SD =
123.87) and 1402.93 ms (SD = 234.01), respectively. Paired sample t 
tests showed higher accuracy for verbal task than non-verbal task (t(58) 
= 18.545, p < 0.001), and lower reaction time for verbal task than non- 
verbal task (t(58) = (cid:0) 23.480, p < 0.001). Overall, the non-verbal task is 
behaviorally harder than the verbal task.

3.2. Activation differences between verbal and non-verbal processing in 
the VWFAs

In the whole-brain activation analysis (Figure 2A), the contrast of 
non-verbal  task  > verbal  task  revealed  activations  in  brain  regions 
related to visuospatial processing (Lauritzen et al., 2009), including the 
bilateral dorsal prefrontal cortex, occipitoparietal cortex, and posterior 
fusiform  gyrus.  The  reverse  contrast  revealed  activations  in  brain  re-
gions related to language processing (Saur et al., 2008), including the 
bilateral ventral prefrontal cortex, lateral temporal cortex, angular gyrus 
(AG), and the left anterior fusiform gyrus.

To  specifically  examine  activation  differences  between  verbal  and 
nonverbal  processing  in  the  VWFAs,  we  performed  two  ROI  analyses 
(Figure 2B). In the first analysis, the percent signal changes of the high- 
level condition (baseline: fixation) of the two tasks were extracted from 
the  VWFA-1  and  VWFA-2.  ANOVA  revealed  that  VWFA-1  showed 
greater activations than VWFA-2 (F(1, 58) = 64.374, p < 0.001, η2
p  =
0.526),  which  is  consistent  with  previous  studies  (Vogel  et  al.,  2012; 
White et al., 2023). The main effect of task was not significant (F(1, 58) 
= 1.706, p = 0.197, η2
p = 0.029). More importantly, there was a signif-
icant task-by-subregion interaction (F(1, 58) = 74.736, p < 0.001, η2
p =
0.563). Simple-effects analysis showed that, compared to the nonverbal 
task, the verbal task elicited a smaller response in VWFA-1 (p < 0.001), 
but a larger response in VWFA-2 (p < 0.001). To eliminate the stimulus 
driven  effects,  we  used  the  low-level  condition  as  the  baseline  in  the 
second analysis. Results showed that the main effects of task (F(1, 58) =
25.606, p < 0.001, η2 = 0.306) and subregion (F(1, 58) = 33.946, p <
0.001, η2
p  = 0.369), as well as  the task-by-subregion interaction were 
significant (F(1, 58) = 41.010, p < 0.001, η2
p  = 0.414). Simple-effects 
analysis  revealed  that the  VWFA-2  still showed  greater  activations in 
the verbal task than the non-verbal task (p < 0.001), but the VWFA-1 
responded  equally  to  verbal  and  non-verbal  tasks  (p  = 0.132)  after 
controlling for the stimulus driven effects.

To confirm that the results were not affected by the discrepancy in 
the ratio of low-level condition trials across the two tasks, we selected 
only half blocks of the high-level condition in the verbal task, so that the 
number of high-level and low-level trials in the verbal tasks was equal, 
and  re-calculated  the  percent  signal  changes  in  the  VWFAs  from  the 
contrast  of  high-level  condition  vs.  low-level  condition  in  the  verbal 
task. The results were almost the same as before. ANOVA revealed that 
the main effects of task (F(1, 58) = 26.112, p < 0.001, η2 = 0.310) and 
subregion (F(1, 58) = 30.181, p < 0.001, η2
p = 0.342), as well as the task- 
by-subregion interaction were still significant (F(1, 58) = 25.279, p <
0.001, η2
p  = 0.304). Simple-effects analysis revealed that the VWFA-2 
still showed greater activations in the verbal task than the non-verbal 
task  (p  < 0.001),  and  the  VWFA-1  responded  equally  to  verbal  and 
non-verbal  tasks  (p  = 0.214)  after  controlling  for  the  low-level 
condition.

We also compared the differences of the VWFAs between the rhyme 
and semantic judgment tasks (Supplementary Fig. 5). When the fixation 
served as baseline, the main effect of task (F(1, 58) = 0.128, p = 0.721) 
was not significant. The main effect of the subregion was significant (F 
(1, 58) = 5.32, p = 0.025, η2
p = 0.084). There was no interaction between 

the task and subregion (F(1, 58) = 0.495, p = 0.485). When the low-level 
condition served as the baseline, results showed that the main effects of 
task (F(1, 58) = 0.015, p = 0.902) and subregion (F(1, 58) = 3.789, p =
0.056) were not significant. There was an interaction between the task 
and subregion (F(1, 58) = 4.019, p = 0.05, η2
p = 0.065). Simple-effects 
analysis  revealed  that  the  VWFA-1  showed  greater  activations  than 
VWFA-2  in  the  rhyme  judgement  task  (p  = 0.019),  but  there  was  no 
significant difference between the VWFA-1 and VWFA-2 in the semantic 
judgement task (p = 0.184).

3.3. The VWFAs showed greater FC to ventral regions and weaker FC to 
dorsal regions for the verbal task relative to the non-verbal task

To examine whether the pattern of whole-brain functional connec-
tivity to the VWFA was affected by task demands, we performed whole- 
brain gPPI analysis on the data of the verbal and non-verbal tasks. As 
shown in Fig. 3A, VWFA-1 and VWFA-2 showed similar distributions of 
whole-brain  functional  connectivity,  but  differed  in  the  extent  of  the 
regions.  Specifically,  both  VWFA-1  and  VWFA-2  showed  connections 
with the bilateral dorsal prefrontal, parietal, and occipital cortex during 
the  non-verbal  task,  and  with  bilateral  prefrontal,  occipito-temporal, 
and temporoparietal cortex during the verbal task. As for the contrast 
of the two tasks (Fig. 3B), the VWFAs had greater FC to the ventral brain 
regions when performing the verbal task relative to the non-verbal task, 
including the bilateral anterior temporal lobe (ATL), MTG, and ventral 
inferior  frontal  gyrus  (vIFG).  In  contrast,  greater  FC  to  the  occipital 
cortex and dorsal brain regions was found when performing the non- 
verbal task relative to the verbal task, including the bilateral superior 
frontal gyrus (SFG), middle frontal gyrus (MFG), superior parietal lobule 
(SPL), anterior supramarginal gyrus (SMG), and lateral occipital cortex 
(LOC).

To specifically examine the strength of FC between the VWFAs and 
high-level regions (i.e., left IPS and OFC) during non-verbal and verbal 
processing, we further performed ROI-based gPPI analyses for the two 
tasks (Fig. 3C). ANOVA on the PPI values revealed that the VWFAs had 
greater FC with the left IPS (F(1, 58) = 47.55, p < 0.001, η2
p = 0.45) in 
the non-verbal task than the verbal task, and greater FC with the left OFC 
(F(1, 58) = 22.48, p < 0.001, η2
p = 0.279) in the verbal task than the non- 
verbal task, indicating that the strength of functional connections be-
tween  VWFAs  and  high-level  frontoparietal  cortex  were  regulated  by 
task demands. In addition, the VWFA-1 had greater connection with the 
left IPS than the VWFA-2 (F(1, 58) = 14.34, p < 0.001, η2
p  = 0.198), 
which was in line with the structural connections (Yeatman and White, 
2021). There was no interaction between task and subregion for either 
the connection between VWFAs and IPS (F(1, 58) = 1.163, p = 0.285) or 
the connection between VWFAs and OFC (F(1, 58) = 1.481, p = 0.229).
As  an  additional  verification,  we  employed  two  additional  ap-
proaches to define the IPS and OFC (described in 2.5 Region of interest 
analysis), and conducted ROI-based gPPI analyses. The results are basi-
cally consistent with the above results. For the PPI values between the 
VWFAs  and  OFC  defined  by  atlas  (Supplementary  Fig.  2B),  results 
showed that the main effects of task (F(1, 58) = 11.543, p = 0.001, η2
p =
0.167) and subregion were significant (F(1, 58) = 6.383, p = 0.014, η2
p =
0.101), and there was no interaction between task and subregion (F(1, 
58) = 3.080, p = 0.085). For the PPI values between the VWFAs and IPS 
defined by atlas, the main effects of the task was significant (F(1, 58) =
104.975, p < 0.001, η2
p = 0.648). The main effects of the subregion was 
not significant (F(1, 58) = 3.211, p = 0.078). There was an interaction 
between task and subregion (F(1, 58) = 9.118, p = 0.004, η2
p = 0.138). 
Simple-effects analysis revealed that the IPS had greater connection with 
the VWFA-1 than VWFA-2 in the verbal task (p = 0.003), but there was 
no significant difference between the VWFA-1 and VWFA-2 in the non- 
verbal task (p = 0.895).

For  the  PPI  values  between  the  VWFAs  and  OFC  defined  by  the 
contrast  of  the  low-level  condition  of  the  two  tasks  (Supplementary 
Fig. 3C), results showed that the main effects of task (F(1, 58) = 36.153, 

6 

A. Li et al.                                                                                                                                                                                                                                        

NeuroImage 303 (2024) 120923 

Fig. 3. Results of gPPI analysis. (A) Brain maps of PPI analysis for the non-verbal task (the upper panel) and the verbal task (the lower panel) with the seed in VWFA- 
1 (the left panel) and VWFA-2 (the right panel). (B) Brain maps of gPPI analysis for the contrast of the two tasks thresholded at Z > 3.1 (whole-brain corrected). (C) 
PPI values between VWFAs and left IPS/OFC during the verbal and non-verbal tasks. OFC = left orbital frontal cortex, IPS = left intraparietal sulcus. ***p < 0.001.

p < 0.001, η2
p = 0.388) and subregion were significant (F(1, 58) = 6.383, 
p = 0.014, η2
p = 0.101), and there was no interaction between task and 
subregion (F(1, 58) = 3.012, p = 0.088). For the PPI values between the 
VWFAs and IPS, the main effects of task (F(1, 58) = 82.966, p < 0.001, η2
p 
= 0.593) and subregion were significant (F(1, 58) = 8.496, p = 0.005, η2
p 
= 0.130), and there was no interaction between task and subregion (F(1, 
58) = 2.969, p = 0.090).

Finally, as an additional verification, we employed two additional 
approaches to define the IPS and OFC (described in 2.5 Region of interest 
analysis),  and  performed  DCM  using  the  fixation  as  the  baseline.  The 
results (see Supplementary Fig. 2C & Fig. 3D) were basically consistent 
with the above results. These results indicated that processing demands 
not only modulated the strength of FC between VWFAs and higher-level 
regions, but also influenced the information flow among them.

3.4. Effective connectivity among the VWFAs, left OFC, and left IPS 
during the verbal and non-verbal tasks

We further performed DCM to specify the information flow among 
the VWFAs, left OFC, and left IPS during the two tasks, and examined 
how processing demands modulated effective connectivity among them 
(Fig. 4). First, we used the fixation as the baseline, and performed DCM 
on the time series of each node under the high-level condition for each 
task. Results showed that, for both the verbal and non-verbal tasks, the 
connection patterns of the VWFA-1 were similar to those of the VWFA-2. 
Specifically,  the  non-verbal  task  enhanced  the  VWFAs-to-IPS  connec-
tion, but inhibited the VWFAs-to-OFC connection. On the contrary, the 
verbal task enhanced the VWFAs-to-OFC connection, but inhibited the 
VWFAs-to-IPS connection. To control for the stimulus driven effects, we 
also performed the second DCM by extracting the time series of each 
node  with  the  low-level  condition  as  the  baseline.  The  results  (see 
Supplementary Fig. 1) were basically consistent with the above results 
using fixation as the baseline (see Fig. 4).

4. Discussion

The  current  study  aimed  to  investigate  how  processing  demands 
induced by verbal and non-verbal tasks modulated the neural responses 
in  the  two  VWFAs  (i.e.,  VWFA-1  and  VWFA-2),  as  well  as  their  con-
nections to high-level frontoparietal cortex. Activation analysis revealed 
that the anterior subregion (VWFA-2) showed greater activations in the 
verbal  task  than  the  non-verbal  task,  while  the  posterior  subregion 
(VWFA-1)  showed greater activations  in the  non-verbal task  than the 
verbal task. After controlling for the stimulus driven effects, there was 
no difference in activations in the VWFA-1 between the two tasks. As for 
the  functional  connectivity  of  the  VWFAs,  the  VWFA-1  and  VWFA-2 
exhibited similar connectivity patterns. Specifically, gPPI revealed that 
both  VWFAs  showed  a  stronger  connection  with  ventral  language  re-
gions (e.g., the left OFC), and a weaker connection with dorsal attention 
regions (e.g., the left IPS) in the verbal task relative to the non-verbal 
task. In terms of the direction of information flow, DCM revealed that 
functional connectivity of VWFAs-to-OFC was enhanced in the verbal 

7 

A. Li et al.                                                                                                                                                                                                                                        

NeuroImage 303 (2024) 120923 

Fig. 4. Results of DCM analysis. Four dynamic causal models were defined and estimated separately. The visual stimuli entered the network via VWFA in all of the 
models. The arrowed lines display the information flow among three brain regions. The solid and dashed lines indicate enhanced and decreased modulation of the 
tasks, respectively. The mean modulatory parameter estimates (in hertz) are presented alongside the arrowed lines (FWE corrected). OFC = left orbital frontal cortex, 
IPS = left intraparietal sulcus. *p < 0.05, **p < 0.01, ***p < 0.001, FWE corrected.

task,  but  decreased  in  the  non-verbal  task,  while  the  VWFAs-to-IPS 
connectivity showed the opposite pattern. Results of the present study 
indicate that processing demands induced by tasks modulate both the 
local activity and functional connectivity pattern of the VWFA.

The  results  of  our  study  made  three  contributions  to  our  under-
standing of the functions of the VWFA. First, the current study identified 
distinct  local  activation  patterns  between  the  two  subregions  of  the 
VWFA. Despite that VWFA-1 and VWFA-2 were activated in both verbal 
and non-verbal tasks, they exhibited distinct sensitivity to the two tasks. 
Specifically, there was no difference in activations in the VWFA-1 be-
tween the verbal and non-verbal tasks after controlling for the stimulus 
driven  effects.  In  contrast,  the  VWFA-2  consistently  showed  greater 
activation  for  the  verbal  task  than  for  the  non-verbal  task  (Fig.  2B). 
Recent evidence suggests that the subregions of VWFA differ in the level 
of visual encoding, with the more posterior VWFA being more sensitive 
to visuospatial features of visual stimuli, and the more anterior VWFA 
being  more 
information 
(Lerma-Usabiaga et al., 2018; White et al., 2019; Yeatman and White, 
2021; Zhan et al., 2023). Given the functional segregation of subregions 
of  the  VWFA,  verbal  and  non-verbal  tasks  differentially  regulate  the 
activation patterns of the VWFA-1 and VWFA-2.

to  higher 

language 

sensitive 

level 

It should be noted that a recent study found that the VWFA-1 had 
larger responses to letter strings than shape strings (White et al., 2023), 
which  seems  inconsistent  with  our  finding  that  the  VWFA-1  showed 
greater activations in the non-verbal task than the verbal task with the 
fixation as baseline. This inconsistency may have been due to the fact 
that the non-verbal stimuli in our study were complex (as compared to 
the simple shapes used in the previous study) and that the non-verbal 
task was more difficult than the verbal task in our study. We infer that 
the VWFA-1 might be more sensitive to task effort. In support of this 
view, Vogel et al., (2012) also found that the posterior VWFA exhibited 
stronger activation in response to Amharic characters than real words. In 
that study, processing Amharic strings was more difficult than process-
ing words (manifested as lower accuracy and higher reaction time for 
Amharic strings than words). Future research can further verify whether 

8 

the VWFA-1 is more sensitive to task effort than stimulus condition.

Second, our study elucidated the effects of processing demands on 
the functional connectivity of the VWFA. Specifically, seed-based func-
tional connectivity analysis showed that both the VWFA-1 and VWFA-2 
had  connections  with  a  broad  network  containing  ventral  language 
areas and dorsal attention regions under the verbal and non-verbal tasks 
(Fig. 3A). These results extended previous findings regarding the VWFA 
as a  part of both language and attention circuitries (e.g., Chen et  al., 
2019; Vogel et al., 2012b; Yeatman et al., 2021) from the perspective of 
task-based functional connectivity. More importantly, the contrast be-
tween the two tasks revealed that both the VWFA-1 and VWFA-2 had 
stronger  connections  with  ventral  language  regions,  but  weaker  con-
nections with dorsal attention regions under the verbal task relative to 
the non-verbal task (Fig. 3B). As the left OFC and IPS have been reported 
to be critical for high-level language processing and visuospatial atten-
tion, respectively (Lauritzen et al., 2009; Saur et al., 2008), we further 
performed ROI-based gPPI analyses for the two tasks. Consistent with 
the  results  of  whole-brain  analysis,  ROI-based  analysis  further 
confirmed that the verbal task induced a stronger VWFAs-OFC connec-
tion,  but  a  weaker  VWFAs-IPS  connection  than  the  non-verbal  task 
(Fig. 3C). It has been reported that the bottom-up representation of the 
ventral  temporal  cortex  is  scaled  by  the  IPS,  and  the  level  of  IPS 
engagement reflects the cognitive demands of the task (Kay and Yeat-
man, 2017). Therefore, the greater connections between the VWFAs and 
IPS in the non-verbal task than the verbal task can be attributed to more 
visuospatial and attention demands of the former. Overall, these results 
indicate that processing demands modulate the strength of functional 
connectivity between the VWFA and frontoparietal cortex.

The third contribution of our study was to specify the direction of 
information flow between the VWFA and two high-level frontoparietal 
regions  (i.e.,  the  left  OFC  and  IPS)  during  the  verbal  and  non-verbal 
tasks. Based on the strength of the functional connectivity between the 
VWFAs and the left OFC and IPS, DCM further revealed that the verbal 
task enhanced the connections from VWFAs to OFC, but inhibited the 
connections  from  VWFAs  to  IPS.  Conversely,  the  non-verbal  task 

A. Li et al.                                                                                                                                                                                                                                        

NeuroImage 303 (2024) 120923 

enhanced  the  connections from  VWFAs to  IPS,  but inhibited the  con-
nections from VWFAs to OFC. These findings indicate that when per-
forming the verbal task, VWFAs enhance connectivity to task-relevant 
regions (i.e., the left OFC), and meanwhile inhibit the connectivity to 
task-unrelated  regions  (i.e.,  the  left  IPS).  The  inverse  pattern  also 
applied to the non-verbal task. Consistent with our findings, a previous 
study on conceptual processing also found that the left posterior parietal 
cortex  showed  increased  connectivity  to  somatomotor  regions  during 
action knowledge retrieval, and increased connectivity to auditory re-
gions during sound knowledge retrieval (Kuhnke et al., 2023). There-
fore,  it  can  be  inferred  that  for  a  particular  region,  its  functional 
connections  are flexible  and strongly depend  on tasks. Processing  de-
mands may influence the functions of the VWFA by regulating its con-
nectivity with the high-level regions.

Our results support the connectivity-biased computation hypothesis 
that the function of a brain region not only depends on the generalized 
neurocomputation of this local area, but also depends on its long-range 
connectivity  (Humphreys  et  al.,  2015,  2017,  2020,  2021;  Price  and 
Devlin, 2011). From this perspective, the function of VWFA is reflected 
not  only  in  its  local activation,  but also  in  its  functional connectivity 
patterns with higher level regions. As the verbal and non-verbal tasks 
elicited distinct connectivity patterns between VWFAs and higher level 
frontoparietal cortex, it can be inferred that the VWFA may play a more 
domain-general role in visual processing. Therefore, the controversies 
on the VWFA’s functions might be attributed to the various processing 
demands  across  previous  studies.  Future  research  should  carefully 
explain  the  functions  of  the  VWFA  by  considering  the  effects  of  pro-
cessing demands induced by different tasks.

The whole brain activation and gPPI results both demonstrate sig-
nificant engagement of the attention networks in verbal and non-verbal 
tasks. Specifically, activation analysis revealed that the non-verbal task 
elicited more attention regions than did the verbal task, such as FEF, IFJ, 
and  IPS  (Fig.  2A).  This  indicates  that  the  non-verbal  task  required 
greater attentional resources than did the verbal task. We selected the 
IPS  as  the  representative  attentional  brain  region  because  it  had  the 
highest  activation  among  these  brain  regions.  In  addition,  the  seed- 
based  PPI  analyses  revealed  strong  functional  connectivities  between 
VWFAs  and  these  attentional  brain  regions  (e.g.,  FEF,  IFJ,  and  IPS) 
during both verbal and nonverbal tasks (Fig. 3A), which provides evi-
dence for the modulation of the attentional brain regions in downstream 
visual areas (Baldauf and Desimone, 2014, 2021).

The  comparison  of  VWFA-1  and  VWFA-2  is  another  topic  that  is 
worth  discussing.  VWFA-1  and  VWFA-2  showed  distinct  activation 
patterns  for  the  two  tasks.  However,  for  the  functional  and  effective 
connectivities,  the  VWFA-1  and  VWFA-2  showed  similar  functional 
connectivity patterns with high-level frontoparietal cortex for the two 
tasks.  The  inconsistency  between  the  activation  and  functional  con-
nectivity patterns might be attributed to the following reasons. Specif-
ically,  brain  activation  and  functional  connectivity  measure  different 
aspects  of  neural  responses.  Brain activation  represents  blood  oxygen 
level-dependent  (BOLD)  signals  in  the  local  area  (Fox  et  al.,  2006). 
Functional connectivity is the synchrony of the signal fluctuations be-
tween different areas induced by task (Smith et al., 2012), while effec-
tive connectivity measures the influence that one activated area exerts 
over another activated area (Friston, 2011). Computational models have 
shown that even if local computations are identical, there are emergent 
variations  in  function  due  to  the  differential  long-range  connectivity 
(Plaut,  2002).  Furthermore,  given  that activation  and  functional  con-
nectivity represent distinct facets of brain activity, processing demands 
might also affect the activation and functional connectivity in different 
ways.

5. Conclusions

To summarize, the present study aimed to determine how processing 
demands  induced  by  verbal  and  non-verbal  tasks  modulated  the 

activation and functional connectivity patterns of two subregions of the 
VWFA.  Activation  results  revealed  that  the  VWFA-2  showed  higher 
activation for the verbal task than the non-verbal task, while there were 
no  activation  differences  in  the  VWFA-1  after  controlling  for  the  vi-
suospatial difference of materials. Functional and effective connectivity 
results  revealed  that  for  both  VWFAs,  the  verbal  task  enhanced  the 
connections  between  VWFAs  and  left  OFC,  while  the  non-verbal  task 
enhanced  the  connections  between  VWFAs  and  left  IPS.  Our  findings 
provide  new  insights  into  the  understanding  of  the  domain-general 
functions of the VWFA from the perspective of functional connectivity.

Data and code availability statement

The raw MRI data and codes are available upon reasonable request to 
the corresponding author, LM, given appropriate ethical, data protec-
tion, and data-sharing agreements.

CRediT authorship contribution statement

Aqian  Li:  Writing  –  review  &  editing,  Writing  –  original  draft, 
Visualization,  Investigation,  Formal  analysis,  Data  curation.  Chuan-
sheng  Chen:  Writing  –  review  &  editing,  Writing  –  original  draft. 
Xiaoyan  Wu:  Formal  analysis,  Data  curation.  Yuan  Feng:  Writing  – 
review  &  editing,  Visualization.  Jingyu  Yang:  Writing  –  review  & 
editing, Investigation. Xiaoxue Feng: Writing – review & editing. Rui 
Hu: Writing – review & editing. Leilei Mei: Writing – review & editing, 
Writing – original draft, Supervision, Methodology, Funding acquisition, 
Conceptualization.

Declaration of competing interest

The authors declare no competing interests.

Acknowledgments

and  Human  Development,  Guangdong, 

This study was supported by grants from the National Natural Sci-
ence  Foundation  of  China  (32271098),  Research  Center  for  Brain 
Cognition 
China 
(2024B0303390003),  and  the  Guangdong  Basic  and  Applied  Basic 
Research  Foundation  (2022A1515011082,  2024A1515011023),  and 
Striving  for  the  First-Class,  Improving  Weak  Links  and  Highlighting 
Features  (SIH)  Key  Discipline  for  Psychology  in  South  China  Normal 
University.

Supplementary materials

Supplementary material associated with this article can be found, in 

the online version, at doi:10.1016/j.neuroimage.2024.120923.

Data availability

Data will be made available on request. 

References

Baker, C.I., Liu, J., Wald, L.L., Kwong, K.K., Benner, T., Kanwisher, N., 2007. Visual word 

processing and experiential origins of functional selectivity in human extrastriate 
cortex. Proc. Natl. Acad. Sci. U.S.A. 104 (21), 9087–9092. https://doi.org/10.1073/ 
pnas.0703300104.

Baldauf, D., Desimone, R., 2014. Neural mechanisms of object-based attention. Science 

(1979) 344 (6182), 424–427. https://doi.org/10.1126/science.1247003.

Beckmann, C.F., Jenkinson, M., Smith, S.M., 2003. General multilevel linear modeling 
for group analysis in FMRI. Neuroimage 20 (2), 1052–1063. https://doi.org/ 
10.1016/S1053-8119(03)00435-X.

Bedini, M., Baldauf, D., 2021. Structure, function and connectivity fingerprints of the 
frontal eye field versus the inferior frontal junction: a comprehensive comparison. 
Eur. J. Neurosci. 54 (4), 5462–5506. https://doi.org/10.1111/ejn.15393.
Bedini, M., Olivetti, E., Avesani, P., Baldauf, D., 2023. Accurate localization and 

coactivation profiles of the frontal eye field and inferior frontal junction: an ALE and 

9 

A. Li et al.                                                                                                                                                                                                                                        

NeuroImage 303 (2024) 120923 

MACM fMRI meta-analysis. Brain Struct. Funct. 228 (3–4), 997–1017. https://doi. 
org/10.1007/s00429-023-02641-y.

Bedini, M., Olivetti, E., Avesani, P., Baldauf, D., 2024. Surface-based probabilistic 

tractography uncovers segregated white matter pathways underlying spatial and 
non-spatial control. bioRxiv.

Bouhali, F., Thiebaut de Schotten, M., Pinel, P., Poupon, C., Mangin, J.F., Dehaene, S., 
Cohen, L., 2014. Anatomical connections of the visual word form area. J. Neurosci. 
34 (46), 15402–15414. https://doi.org/10.1523/JNEUROSCI.4918-13.2014.

Bullock, D., Takemura, H., Caiafa, C.F., Kitchell, L., McPherson, B., Caron, B., Pestilli, F., 
2019. Associative white matter connecting the dorsal and ventral posterior human 
cortex. Brain Struct. Funct. 224 (8), 2631–2660. https://doi.org/10.1007/s00429- 
019-01907-8.

Cai, Q., Brysbaert, M., 2010. SUBTLEX-CH: chinese word and character frequencies 

based on film subtitles. PLoS. One 5 (6), e10729. https://doi.org/10.1371/journal. 
pone.0010729.

Can´ario, N., Jorge, L., Castelo-Branco, M., 2020. Distinct mechanisms drive hemispheric 
lateralization of object recognition in the visual word form and fusiform face areas. 
Brain Lang. 210, 104860. https://doi.org/10.1016/j.bandl.2020.104860.

Catani, M., Mesulam, M., 2008. The arcuate fasciculus and the disconnection theme in 
language and aphasia: history and current state. Cortex 44 (8), 953–961. https://doi. 
org/10.1016/j.cortex.2008.04.002.

Chauhan, V.S., McCook, K.C., White, A.L., 2024. Reading reshapes stimulus selectivity in 
the visual word form area. eNeuro 11 (7). https://doi.org/10.1523/ENEURO.0228- 
24.2024. ENEURO.0228-24.2024. 

Chen, L., Wassermann, D., Abrams, D.A., Kochalka, J., Gallardo-Diez, G., Menon, V., 
2019. The visual word form area (VWFA) is part of both language and attention 
circuitry. Nat. Commun. 10 (1), 5601. https://doi.org/10.1038/s41467-019-13634- 
z.

Cisler, J.M., Bush, K., Steele, J.S., 2014. A comparison of statistical methods for detecting 
context-modulated functional connectivity in fMRI. Neuroimage 84, 1042–1052. 
https://doi.org/10.1016/j.neuroimage.2013.09.018.

Cohen, L., Dehaene, S., 2004. Specialization within the ventral stream: the case for the 
visual word form area. Neuroimage 22 (1), 466–476. https://doi.org/10.1016/j. 
neuroimage.2003.12.049.

Cohen, L., Leh´ericy, S., Chochon, F., Lemer, C., Rivaud, S., Dehaene, S., 2002. Language- 
specific tuning of visual cortex? Functional properties of the visual word form area. 
Brain 125 (Pt 5), 1054–1069. https://doi.org/10.1093/brain/awf094.
Corbetta, M., Shulman, G.L., 2002. Control of goal-directed and stimulus-driven 

attention in the brain. Nat. Rev. Neurosci. 3 (3), 201–215. https://doi.org/10.1038/ 
nrn755.

Dehaene, S., Cohen, L., 2011. The unique role of the visual word form area in reading. 

Trends Cogn. Sci. (Regul. Ed.) 15 (6), 254–262. https://doi.org/10.1016/j. 
tics.2011.04.003.

Fedorenko, E., Behr, M.K., Kanwisher, N., 2011. Functional specificity for high-level 
linguistic processing in the human brain. Proc. Natl. Acad. Sci. U.S.A. 108 (39), 
16428–16433. https://doi.org/10.1073/pnas.1112937108.

Fischer-Baum, S., Bruggemann, D., Gallego, I.F., Li, D.S.P., Tamez, E.R., 2017. Decoding 

levels of representation in reading: a representational similarity approach. Cortex 
90, 88–102. https://doi.org/10.1016/j.cortex.2017.02.017.

Fox, M.D., Snyder, A.Z., Zacks, J.M., Raichle, M.E., 2006. Coherent spontaneous activity 
accounts for trial-to-trial variability in human evoked brain responses. Nat. Neurosci. 
9 (1), 23–25. https://doi.org/10.1038/nn1616.

Humphreys, G.F., Jackson, R.L., Lambon Ralph, M.A., 2020. Overarching principles and 

dimensions of the functional organization in the inferior parietal cortex. Cerebral 
Cortex 30 (11), 5639–5653. https://doi.org/10.1093/cercor/bhaa133.

Humphreys, G.F., Lambon Ralph, M.A., Simons, J.S., 2021. A unifying account of angular 
gyrus contributions to episodic and semantic cognition. Trends Neurosci. 44 (6), 
452–463. https://doi.org/10.1016/j.tins.2021.01.006.

Jenkinson, M., Smith, S., 2001. A global optimisation method for robust affine 

registration of brain images. Med. Image Anal. 5 (2), 143–156. https://doi.org/ 
10.1016/s1361-8415(01)00036-6.

Kay, K.N., Yeatman, J.D., 2017. Bottom-up and top-down computations in word- and 
face-selective cortex. Elife 6, e22341. https://doi.org/10.7554/eLife.22341.

Kherif, F., Josse, G., Price, C.J., 2011. Automatic top-down processing explains common 
left occipito-temporal responses to visual words and objects. Cerebral Cortex 21 (1), 
103–114. https://doi.org/10.1093/cercor/bhq063.

Kuhnke, P, Kiefer, M, Hartwigsen, G, 2023. Conceptual representations in the default, 

control and attention networks are task-dependent and cross-modal. Brain Lang 244, 
105313. https://doi.org/10.1016/j.bandl.2023.105313.

Lauritzen, T.Z., D’Esposito, M., Heeger, D.J., Silver, M.A., 2009. Top-down flow of visual 
spatial attention signals from parietal to occipital cortex. J. Vis. 9 (13), 1–14. 
https://doi.org/10.1167/9.13.18.

Lerma-Usabiaga, G., Carreiras, M., Paz-Alonso, P.M., 2018. Converging evidence for 

functional and structural segregation within the left ventral occipitotemporal cortex 
in reading. Proc. Natl. Acad. Sci. U.S.A. 115 (42), E9981–E9990. https://doi.org/ 
10.1073/pnas.1803003115.

Li, Y., Zhang, L., Xia, Z., Yang, J., Shu, H., Li, P., 2017. The relationship between intrinsic 
couplings of the visual word form area with spoken language network and reading 
ability in children and adults. Front. Hum. Neurosci. 11, 327. https://doi.org/ 
10.3389/fnhum.2017.00327.

L´opez-Barroso, D., Thiebaut de Schotten, M., Morais, J., Kolinsky, R., Braga, L.W., 
Guerreiro-Tauil, A., Dehaene, S., Cohen, L., 2020. Impact of literacy on the 
functional connectivity of vision and language related networks. Neuroimage 213, 
116722. https://doi.org/10.1016/j.neuroimage.2020.116722.

McCandliss, B.D., Cohen, L., Dehaene, S., 2003. The visual word form area: expertise for 
reading in the fusiform gyrus. Trends Cogn. Sci. (Regul. Ed.) 7 (7), 293–299. https:// 
doi.org/10.1016/s1364-6613(03)00134-7.

McLaren, D.G., Ries, M.L., Xu, G., Johnson, S.C., 2012. A generalized form of context- 
dependent psychophysiological interactions (gPPI): a comparison to standard 
approaches. Neuroimage 61 (4), 1277–1286. https://doi.org/10.1016/j. 
neuroimage.2012.03.068.

Mei, L., Xue, G., Chen, C., Xue, F., Zhang, M., Dong, Q., 2010. The "visual word form 

area" is involved in successful memory encoding of both words and faces. 
Neuroimage 52 (1), 371–378. https://doi.org/10.1016/j.neuroimage.2010.03.067.
Peters, L., De Smedt, B., Op de Beeck, H.P., 2015. The neural representation of Arabic 
digits in visual cortex. Front. Hum. Neurosci. 9, 517. https://doi.org/10.3389/ 
fnhum.2015.00517.

Plaut, D.C., 2002. Graded modality-specific specialisation in semantics: a computational 
account of optic aphasia. Cogn. Neuropsychol. 19 (7), 603–639. https://doi.org/ 
10.1080/02643290244000112.

Ploran, E.J., Nelson, S.M., Velanova, K., Donaldson, D.I., Petersen, S.E., Wheeler, M.E., 

2007. Evidence accumulation and the moment of recognition: dissociating 
perceptual recognition processes using fMRI. J. Neurosci. 27 (44), 11912–11924. 
https://doi.org/10.1523/JNEUROSCI.3522-07.2007.

Friston, K.J., 2011. Functional and effective connectivity: a review. Brain Connect. 1 (1), 

Polk, T.A., Farah, M.J., 2002. Functional MRI evidence for an abstract, not perceptual, 

13–36. https://doi.org/10.1089/brain.2011.0008.

Friston, K.J., Harrison, L., Penny, W., 2003. Dynamic causal modelling. Neuroimage 19 

(4), 1273–1302. https://doi.org/10.1016/s1053-8119(03)00202-7.

Gaillard, R., Naccache, L., Pinel, P., Cl´emenceau, S., Volle, E., Hasboun, D., Dupont, S., 
Baulac, M., Dehaene, S., Adam, C., Cohen, L., 2006. Direct intracranial, FMRI, and 
lesion evidence for the causal role of left inferotemporal cortex in reading. Neuron 
50 (2), 191–204. https://doi.org/10.1016/j.neuron.2006.03.031.

Glasser, M.F., Coalson, T.S., Robinson, E.C., Hacker, C.D., Harwell, J., Yacoub, E., 

Ugurbil, K., Andersson, J., Beckmann, C.F., Jenkinson, M., Smith, S.M., Van Essen, D. 
C., 2016. A multi-modal parcellation of human cerebral cortex. Nature 536 (7615), 
171–178. https://doi.org/10.1038/nature18933.

Glezer, L.S., Riesenhuber, M., 2013. Individual variability in location impacts 

orthographic selectivity in the "visual word form area". J. Neurosci. 33 (27), 
11221–11226. https://doi.org/10.1523/JNEUROSCI.5002-12.2013.

Glezer, L.S., Jiang, X., Riesenhuber, M., 2009. Evidence for highly selective neuronal 
tuning to whole words in the "visual word form area". Neuron 62 (2), 199–204. 
https://doi.org/10.1016/j.neuron.2009.03.017.

Grotheer, M., Jeska, B., Grill-Spector, K., 2018. A preference for mathematical processing 

outweighs the selectivity for Arabic numbers in the inferior temporal gyrus. 
Neuroimage 175, 188–200. https://doi.org/10.1016/j.neuroimage.2018.03.064.
Hannagan, T., Amedi, A., Cohen, L., Dehaene-Lambertz, G., Dehaene, S., 2015. Origins of 
the specialization for letters and numbers in ventral occipitotemporal cortex. Trends 
Cogn. Sci. (Regul. Ed.) 19 (7), 374–382. https://doi.org/10.1016/j.tics.2015.05.006.
Humphreys, G.F., Lambon Ralph, M.A., 2015. Fusion and fission of cognitive functions in 
the human parietal cortex. Cerebral cortex 25 (10), 3547–3560. https://doi.org/ 
10.1093/cercor/bhu198.

Humphreys, G.F., Lambon Ralph, M.A., 2017. Mapping domain-selective and 

counterpointed domain-general higher cognitive functions in the lateral parietal 
cortex: evidence from FMRI comparisons of difficulty-varying semantic versus visuo- 
spatial tasks, and functional connectivity analyses. Cerebral Cortex 27 (8), 
4199–4212. https://doi.org/10.1093/cercor/bhx107.

word-form area. J. Exp. Psychol. Gen. 131 (1), 65–72. https://doi.org/10.1037// 
0096-3445.131.1.65.

Price, C.J., Devlin, J.T., 2011. The interactive account of ventral occipitotemporal 

contributions to reading. Trends Cogn. Sci. (Regul. Ed.) 15 (6), 246–253. https://doi. 
org/10.1016/j.tics.2011.04.001.

Saur, D., Kreher, B.W., Schnell, S., Kümmerer, D., Kellmeyer, P., Vry, M.S., Umarova, R., 
Musso, M., Glauche, V., Abel, S., Huber, W., Rijntjes, M., Hennig, J., Weiller, C., 
2008. Ventral and dorsal pathways for language. Proc. Natl. Acad. Sci. U.S.A. 105 
(46), 18035–18040. https://doi.org/10.1073/pnas.0805234105.

Saygin, Z.M., Osher, D.E., Norton, E.S., Youssoufian, D.A., Beach, S.D., Feather, J., 

Gaab, N., Gabrieli, J.D., Kanwisher, N., 2016. Connectivity precedes function in the 
development of the visual word form area. Nat. Neurosci. 19 (9), 1250–1255. 
https://doi.org/10.1038/nn.4354.

Seidenberg, M.S., 2005. Connectionist models of word reading. Curr. Dir. Psychol. Sci. 

14, 238.

Silk, T.J., Bellgrove, M.A., Wrafter, P., Mattingley, J.B., Cunnington, R., 2010. Spatial 
working memory and spatial attention rely on common neural processes in the 
intraparietal sulcus. Neuroimage 53 (2), 718–724. https://doi.org/10.1016/j. 
neuroimage.2010.06.068.

Smith, S.M., Miller, K.L., Moeller, S., Xu, J., Auerbach, E.J., Woolrich, M.W., 

Beckmann, C.F., Jenkinson, M., Andersson, J., Glasser, M.F., Van Essen, D.C., 
Feinberg, D.A., Yacoub, E.S., Ugurbil, K., 2012. Temporally-independent functional 
modes of spontaneous brain activity. Proc. Natl. Acad. Sci. U.S.A. 109 (8), 
3131–3136. https://doi.org/10.1073/pnas.1121329109.

Snyder, P.J., Harris, L.J., 1993. Handedness, sex, and familial sinistrality effects on 
spatial tasks. Cortex 29 (1), 115–134. https://doi.org/10.1016/s0010-9452(13) 
80216-x.

Soyuhos, O., Baldauf, D., 2023. Functional connectivity fingerprints of the frontal eye 

field and inferior frontal junction suggest spatial versus nonspatial processing in the 
prefrontal cortex. Eur. J. Neurosci. 57 (7), 1114–1140. https://doi.org/10.1111/ 
ejn.15936.

10 

A. Li et al.                                                                                                                                                                                                                                        

NeuroImage 303 (2024) 120923 

Stephan, K.E., Penny, W.D., Moran, R.J., den Ouden, H.E., Daunizeau, J., Friston, K.J., 

Vogel, A.C., Petersen, S.E., Schlaggar, B.L., 2014. The VWFA: it’s not just for words 

2010. Ten simple rules for dynamic causal modeling. Neuroimage 49 (4), 
3099–3109. https://doi.org/10.1016/j.neuroimage.2009.11.015.

Stevens, W.D., Kravitz, D.J., Peng, C.S., Tessler, M.H., Martin, A., 2017. Privileged 

functional connectivity between the visual word form area and the language system. 
J. Neurosci. 37 (21), 5288–5297. https://doi.org/10.1523/JNEUROSCI.0138- 
17.2017.

Tagamets, M.A., Novick, J.M., Chalmers, M.L., Friedman, R.B., 2000. A parametric 

approach to orthographic processing in the brain: an fMRI study. J. Cogn. Neurosci. 
12 (2), 281–297. https://doi.org/10.1162/089892900562101.

Takemura, H., Rokem, A., Winawer, J., Yeatman, J.D., Wandell, B.A., Pestilli, F., 2016. 
A major human white matter pathway between dorsal and ventral visual cortex. 
Cerebral Cortex 26 (5), 2205–2214. https://doi.org/10.1093/cercor/bhv064.

anymore. Front. Hum. Neurosci. 8, 88. https://doi.org/10.3389/fnhum.2014.00088.

White, A.L., Boynton, G.M., Yeatman, J.D., 2019. You can’t recognize two words 

simultaneously. Trends Cogn. Sci. (Regul. Ed.) 23 (10), 812–814. https://doi.org/ 
10.1016/j.tics.2019.07.001.

White, A.L., Kay, K.N., Tang, K.A., Yeatman, J.D., 2023. Engaging in word recognition 
elicits highly specific modulations in visual cortex. Curr. Biol. 33 (7), 1308–1320.e5. 
https://doi.org/10.1016/j.cub.2023.02.042.

Worsley, K.J., 2001. 14 Statistical analysis of activation images. Functional MRI: An 

Introduct. Methods 25.

Xu, M., Baldauf, D., Chang, C.Q., Desimone, R., Tan, L.H., 2017. Distinct distributed 

patterns of neural activity are associated with two languages in the bilingual brain. 
Sci. Adv. 3 (7), e1603309. https://doi.org/10.1126/sciadv.1603309.

Taylor, J.S.H., Davis, M.H., Rastle, K., 2019. Mapping visual symbols onto spoken 

Xue, G., Chen, C., Jin, Z., Dong, Q., 2006. Language experience shapes fusiform 

language along the ventral visual stream. Proc. Natl. Acad. Sci. U.S.A. 116 (36), 
17723–17728. https://doi.org/10.1073/pnas.1818575116.

Tzourio-Mazoyer, N., Landeau, B., Papathanassiou, D., Crivello, F., Etard, O., 

Delcroix, N., Mazoyer, B., Joliot, M., 2002. Automated anatomical labeling of 
activations in SPM using a macroscopic anatomical parcellation of the MNI MRI 
single-subject brain. Neuroimage 15 (1), 273–289. https://doi.org/10.1006/ 
nimg.2001.0978.

Van Doren, L., Dupont, P., De Grauwe, S., Peeters, R., Vandenberghe, R., 2010. The 
amodal system for conscious word and picture identification in the absence of a 
semantic task. Neuroimage 49 (4), 3295–3307. https://doi.org/10.1016/j. 
neuroimage.2009.12.005.

Vinckier, F., Dehaene, S., Jobert, A., Dubus, J.P., Sigman, M., Cohen, L., 2007. 

Hierarchical coding of letter strings in the ventral stream: dissecting the inner 
organization of the visual word-form system. Neuron 55 (1), 143–156. https://doi. 
org/10.1016/j.neuron.2007.05.031.

Vogel, A.C., Miezin, F.M., Petersen, S.E., Schlaggar, B.L., 2012b. The putative visual 

word form area is functionally connected to the dorsal attention network. Cerebral 
Cortex 22 (3), 537–549. https://doi.org/10.1093/cercor/bhr100.

Vogel, A.C., Petersen, S.E., Schlaggar, B.L., 2012a. The left occipitotemporal cortex does 
not show preferential activity for words. Cerebral Cortex 22 (12), 2715–2732. 
https://doi.org/10.1093/cercor/bhr295.

activation when processing a logographic artificial language: an fMRI training study. 
Neuroimage 31 (3), 1315–1326. https://doi.org/10.1016/j. 
neuroimage.2005.11.055.

Yablonski, M., Karipidis, I.I., Kubota, E., Yeatman, J.D., 2024. The transition from vision 
to language: distinct patterns of functional connectivity for subregions of the visual 
word form area. Hum. Brain Mapp. 45 (4), e26655. https://doi.org/10.1002/ 
hbm.26655.

Yeatman, J.D., White, A.L., 2021. Reading: the Confluence of Vision and Language. Annu 
Rev. Vis. Sci. 7, 487–517. https://doi.org/10.1146/annurev-vision-093019-113509.

Yeatman, J.D., Rauschecker, A.M., Wandell, B.A., 2013. Anatomy of the visual word 

form area: adjacent cortical circuits and long-range white matter connections. Brain 
Lang. 125 (2), 146–155. https://doi.org/10.1016/j.bandl.2012.04.010.

Yeatman, J.D., Weiner, K.S., Pestilli, F., Rokem, A., Mezer, A., Wandell, B.A., 2014. The 

vertical occipital fasciculus: a century of controversy resolved by in vivo 
measurements. Proc. Natl. Acad. Sci. U.S.A. 111 (48), E5214–E5223. https://doi. 
org/10.1073/pnas.1418503111.

Zhan, M., Pallier, C., Agrawal, A., Dehaene, S., Cohen, L., 2023. Does the visual word 
form area split in bilingual readers? A millimeter-scale 7-T fMRI study. Sci. Adv. 9 
(14), eadf6140. https://doi.org/10.1126/sciadv.adf6140.

11 

