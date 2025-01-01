NeuroImage 303 (2024) 120949 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Investigating unilateral and bilateral motor imagery control using 
electrocorticography and fMRI in awake craniotomy

Jie Ma a,b,1, Zhengsheng Li e,1, Qian Zheng c,1, Shichen Li j, Rui Zong b, Zhizhen Qin a,b, Li Wan f,  
Zhenyu Zhao d, Zhiqi Mao b, Yanyang Zhang b, Xinguang Yu b, Hongmin Bai d,*,  
Jianning Zhang b,*
a PLA Medical School, Beijing 100853, PR China
b Department of Neurosurgery, Chinese PLA General Hospital, 28 Fuxing Road, Haidian District, Beijing 100853, PR China
c College of Computer Science and Control Engineering, Shenzhen Institutes of Advanced Technology, Chinese Academy of Sciences, Shenzhen, Guangzhou 818055, PR 
China
d Department of Neurosurgery, General Hospital of the Southern Theater Command of PLA, Guangzhou, Guangzhou 510051, PR China
e Department of Neurology, General Hospital of the Southern Theater Command of PLA, Guangzhou, Guangzhou 510051, PR China
f Zhejiang Flexolink Technology Co., Ltd., Hangzhou 518048, PR China
j Level 5, Centre for Children’s Health Research, 62 Graham St, South Brisbane, Qld 4101, Australia

A R T I C L E  I N F O

A B S T R A C T

Keywords:
Awake craniotomy
Electrocorticography
Functional magnetic resonance imaging
Motor imagery
Bilateral motor control

Background: The rapid development of neurosurgical techniques, such as awake craniotomy, has increased op-
portunities to explore the mysteries of the brain. This is crucial for deepening our understanding of motor control 
and imagination processes, especially in developing brain–computer interface (BCI) technologies and improving 
neurorehabilitation strategies for neurological disorders.
Objective: This study aimed to analyze brain activity patterns in patients undergoing awake craniotomy during 
actual movements and motor imagery, mainly focusing on the motor control processes of the bilateral limbs.
Methods:  We  conducted  detailed  observations  of  patients  undergoing  awake  craniotomies.  The  experimenter 
requested participants to perform and imagine a series of motor tasks involving their hands and tongues. Brain 
activity during these tasks was recorded using functional magnetic resonance imaging (fMRI) and intraoperative 
electrocorticography  (ECoG).  The  study  included  left  and  right  finger  tapping,  tongue  protrusion,  hand 
clenching, and imagined movements corresponding to these actions.
Results: fMRI revealed significant activation in the brain’s motor areas during task performance, mainly involving 
bilateral  brain  regions  during  imagined  movement.  ECoG  data  demonstrated  a  marked  desynchronization 
pattern in the ipsilateral motor cortex during bilateral motor imagination, especially in bilateral coordination 
tasks.  This  finding  suggests  a  potential  controlling  role  of  the  unilateral  cerebral  cortex  in  bilateral  motor 
imagination.
Conclusion: Our study highlights the unilateral cerebral cortex’s significance in controlling bilateral limb motor 
imagination,  offering  new  insights  into  future  brain  network  remodeling  in  patients  with  hemiplegia.  Addi-
tionally, these findings provide important insights into understanding motor imagination and its impact on BCI 
and neurorehabilitation.

1. Introduction

Innovative  advancements  in  neurosurgery,  particularly  break-
throughs in awake craniotomy techniques, have significantly expanded 
our  understanding  of  brain  function  regarding  motor  control  and 

cognitive processes (Eseonu et al., 2018; Gerritsen et al., 2022; Lecho-
wicz-Głogowska et al., 2022; Maldonado et al., 2011; Meyer et al., 2001; 
Pereira  et  al.,  2009;  Picht  et  al.,  2006;  Serletis  and  Bernstein,  2007; 
Taylor and Bernstein, 1999; Trimble et al., 2015). These surgical pro-
cedures allow direct brain mapping and real-time patient interactions, 

* Corresponding authors.

E-mail addresses: baihmmu@vip.163.com (H. Bai), zhang_jianning@yeah.net (J. Zhang). 

1 J.M., Z.L. and Q.Z. Contributed equally to this work and are co-first authors.

https://doi.org/10.1016/j.neuroimage.2024.120949
Received 14 March 2024; Received in revised form 1 November 2024; Accepted 18 November 2024  
Available online 19 November 2024 
1053-8119/© 2024 The Authors. Published by Elsevier Inc. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ). 

J. Ma et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120949 

offering  a  unique  perspective  for  studying  brain  activity  during 
conscious motor tasks and motor imagery (Dziedzic et al., 2021; Garrett 
et al., 2012; Jung et al., 2020; Satoer et al., 2016; Starowicz-Filip et al., 
2022; Zarino et al., 2020).

Within  neuroscience  and  rehabilitative  medicine,  motor  image-
ry—the  ability  to  mentally  simulate  tasks  without  actual  physical 
movement—has  become  a  topic  of  significant  interest  (Batson,  2004; 
Dunsky and Dickstein, 2018; Tong et al., 2017). Previous studies using 
fMRI  and  EEG  have  identified  several  brain  areas  involved  in  both 
unimanual  and  bimanual  movements,  as  well  as  the  imagination  of 
movements. Key regions include the primary motor cortex (M1), pre-
motor  cortex  (PMC),  supplementary  motor  area  (SMA),  and  parietal 
lobes, The SMA, in particular, is believed to serve as the primary coor-
dinator for bimanual movements (Bonifazi et al., 2020; Casimo et al., 
2017).

However,  fMRI,  while  providing  excellent  spatial  resolution,  is 
limited  by  low  temporal  resolution  and  cannot  capture  rapid  neural 
dynamics (Lu et al., 2011; Maldaun et al., 2014). EEG offers high tem-
poral  resolution  but  lacks  spatial  precision  due  to  signal  dispersion 
across  the  scalp  (Chacko  et  al.,  2013).  Electrocorticography  (ECoG), 
which  records  electrical  activity  directly  from  the  cortical  surface, 
overcomes these limitations by providing both high temporal and spatial 
resolution . Even when performed unilaterally, ECoG can detect neural 
activity associated with  bilateral motor tasks  due to interhemispheric 
communication pathways (Breshears et al., 2012; Errante et al., 2019; 
Zarino et al., 2021). This makes ECoG particularly valuable for clarifying 
uncertainties about the roles of specific cortical areas in unilateral and 
bilateral movements and motor imagery.

Despite  the  growing  interest,  the  neural  mechanisms  underlying 
motor  imagery,  especially  in  surgical  contexts,  remain  largely  unex-
plored. The rationale of this study is to leverage the unique conditions of 
awake craniotomy and employ ECoG technology to explore the brain’s 
neural activity during both unilateral and bilateral motor actions and 
motor  imagery  (Borggraefe  et  al.,  2016;  Errante  et  al.,  2019;  Gabriel 
et al., 2006; Rech et al., 2014; Ruddy et al., 2017; Simon-Martinez et al., 
2019). We hypothesize that: 

(1)  Unilateral  cortical  areas  can  generate  neural  activity  patterns 
associated with both unilateral and bilateral motor imagery tasks.
(2)  ECoG, even when performed on one side, can clarify the extent of 
bilateral  brain  activation  due  to  the  interconnectedness  of 
cortical networks involved in motor control.

(3)  The SMA and other motor-related areas play significant roles in 
coordinating  both unimanual  and bimanual  movements during 
execution and imagery.

Objectives
Specifically, the main objectives of this study include: 

(1)  Using ECoG data to analyze brain activity patterns during specific 
motor tasks and motor imagery, focusing on identified cortical 
regions involved in motor control.

(2)  Investigating the presence and extent of bilateral brain activity 
during unilateral motor tasks, particularly the role of the SMA in 
coordinating movements.

(3)  Exploring the possibility of unilateral cortical areas controlling 
bilateral limb movements, enhancing our understanding of motor 
control mechanisms.

In  this  study,  we  examine  brain  activity  related  to  motor  control 
during tasks involving actual and imagined motor execution (Decety and 
Gr`ezes, 2006; Jeannerod, 2001). The motor tasks tested include tapping 
with the left index finger, tapping with the right index finger, and co-
ordinated  bimanual  movements  (Munzert  et  al.,  2009).  During  the 
motor imagery phases, participants were instructed to vividly imagine 
performing  these  same  tasks  without  any  physical  movement.  These 

tasks are inherently motoric and engage cognitive processes (Hardwick 
et al., 2018), allowing us to investigate the neural substrates involved in 
both execution and imagination of movements.

This  approach  aims  to  elucidate  the  intersection  between  motor 
control and cognition, particularly how unilateral cortical activity con-
tributes  to  bilateral  motor  functions.  The  findings  will  profoundly 
impact  the  practice  of  neurosurgery,  foundational  research  in  neuro-
science,  and  the  development  of  BCI  technology  in  rehabilitative 
medicine.

2. Method

2.1. Selection and preoperative preparation of participants

Study Participants: This study is part of an ongoing registered clinical 
trial active for over a year. It currently includes 11 participants, which is 
expected to increase (Table 1). The trial is aimed at acquiring cortical 
brainwave data under awake craniotomy in patients with tumors in the 
left  central  region.  Despite  the  growing  cohort,  cases  like  WCS  are 
sporadic, with hers being our study’s only instance. Given the unique 
clinical characteristics and the potential insights into the neurobiolog-
ical  underpinnings  of  brain-computer  interface  applications  that  her 
case  presents,  we  have  posited  WCS  as  representative  of  this  unique 
subgroup. This focused approach allows us to harness broad data from a 
larger cohort and to delve into a detailed examination of WCS’s case, 
thus providing significant insights into how tumors in the left central 
region affect cortical activity and cognitive functions. To complement 
this in-depth analysis, we have conducted statistical analyses to describe 
our participant group’s demographic and cognitive baseline, including 
calculating the mean and standard deviation for age and MMSE scores. 
These  statistics  are  presented  in  the  text  accompanying  the  tables  to 
offer a clear and comprehensive overview of the participant character-
istics without complicating the data presentation. WCS’s singular case, 
therefore, serves as the cornerstone of our study, offering a unique lens 
through which we explore the complexities of cortical brainwave data 
under  the  specific  context  of  awake  craniotomy.  Inclusion  criteria 
comprised participants with no fMRI or ECoG contraindications capable 
of active cooperation throughout surgical and experimental procedures, 
such as preoperative tumor localization (Fig. 1A–F) and intraoperative 
neuro-navigation for positioning (Fig. 1G–I). We can see that the tumor 
is located in the hand area of the left precentral gyrus without significant 
compression of the corticospinal tract. This participant, a young woman 
fully conscious of her condition, willingly provided her informed con-
sent and was actively engaged throughout the study.

Preoperative Assessment: The participants underwent neurological 
function  assessment  by  two  neurosurgeons  before  surgery,  scoring 
muscle  strength  using  the  Medical  Research  Council  (MRC)  muscle 
strength scale, which ranges from 0 (no muscle contraction) to 5 (normal 
strength) (O’Brien, 2023)). Muscle groups assessed included upper limb 
muscles, particularly those relevant to finger tapping and hand move-
ments involved in the study’s motor tasks. A neuropsychologist evalu-
ated  the  patients’  cognitive  function  using  the  Mini-Mental  State 
Examination (MMSE) (Folstein et al., 1975), which assesses psychiatric 
symptoms  such  as  depression,  anxiety,  hallucinations,  and  unusual 
behavior.  In  addition  to  hand  dominance  assessed  via  the  Edinburgh 
Handedness  Inventory  and  cognitive  screening  with  the  Mini-Mental 
State Examination (MMSE), patients’ alertness and mental imagery ca-
pabilities were evaluated using the Vividness of Visual Imagery Ques-
tionnaire (VVIQ) (Roberts et al., 2008) and the Kinesthetic and Visual 
Imagery Questionnaire (KVIQ) (Malouin et al., 2007). Notably, patient 
WCS scored at the top end of both VVIQ and KVIQ, indicative of her 
exceptional mental imagery skills honed through intensive preoperative 
training. We evaluated language functions using the Western Aphasia 
Battery-Revised (WAB-R) (Jacobs et al., 2023), which assesses speech 
fluency, comprehension, repetition, and naming abilities to screen for 
aphasia.  Dysarthria  was  assessed  using  the  Frenchay  Dysarthria 

2 

J. Ma et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120949 

Table 1 
Participant demographics and tumor characteristics in motor imagery study.

Name

Age (years)

Gender

MMSE

EHI

Tumor location

Diagnosis

Symptoms

DES

BOLD-fMRI

ECoG

YLF
QXG
MJF
HYC
ZHZ
SGH
WCS
XRG
ZW
HTV
XXL

35
48
33
21
43
51
26
45
18
71
20

Male
Male
Male
Female
Female
Male
Female
Male
Male
Female
Male

30
30
30
30
30
30
30
30
30
26
30

1
1
1
1
1
1
1
1
1
1
1

Left frontal operculum
Left parieto-occipital
Left frontal
Left temporal
Left cerebral multifocal
Left central region
Left precentral gyrus
Left frontal
Left temporal
Right cerebral multifocal
Left parietal

Diffuse Astrocytoma
Low-grade Glioma
Astrocytoma
Oligodendroglioma
Astrocytoma
Astrocytoma
High-grade Glioma
Oligodendroglioma
Low-grade Glioma
Glioblastoma
Cavernous Hemangioma

Epilepsy
Headache
Epilepsy
Epilepsy
Epilepsy
Epilepsy
Epilepsy
Dizziness
Epilepsy
Headache
Epilepsy

Yes
Yes
Yes
Yes
Yes
Yes
Yes
Yes
Yes
Yes
Yes

Yes
Yes
Yes
Yes
Yes
Yes
Yes
Yes
Yes

Yes

Yes

Yes
Yes

Yes

MMSE, mini-mental state examination; EHI, Edinburgh handedness inventory; DES, direct electrical stimulation; BOLD-fMRI, blood-oxygen-level-dependent func-
tional magnetic resonance imaging; ECoG, electrocorticography.

Fig. 1. Experimental paradigm involving perioperative imaging data, preoperative task-state functional MRI, and cortical EEG.
Panels A–F show the participant’s preoperative MRI, with T2 and FLAIR sequences indicating a left central region tumor. Panels G–I display tumor localization and its 
relation to the corticospinal tract, precisely determined using intraoperative neuronavigation. Panel J represents the experimental paradigm of task-state functional 
MRI performed preoperatively by the patient. Panel K illustrates the experimental paradigm for intraoperative cortical EEG acquisition.

Assessment  (FDA-2)  (Cloud  et  al.,  2024),  which  examines  orofacial 
movements,  speech  intelligibility,  and  articulation,  with  a  maximum 
score of 14 points. For the picture-naming task, participants completed 
the Snodgrass and Vanderwart picture set (Snodgrass and Vanderwart, 
1980), naming 80 black-and-white images to assess naming accuracy, 
with  a  standard  benchmark  of  ≥95  %  correctness.  We  also  utilized 
preoperative  magnetic  resonance  imaging  (MRI)  and  conducted 
task-state  fMRI  to  map  the  brain  regions  associated  with  motor 
functions.

2.2. Task design and protocol

2.2.1. Preoperative fMRI protocol

During the completion of the presurgical fMRI, participants engaged 
in  experiments  related  to  a  specifically  designed  task  paradigm,  per-
forming four sessions: light tapping with the left index finger (S1), light 
tapping with the right index finger (S2), sticking out the tongue, (S3) 
and threading a needle with the right hand (S4). Each action consisted of 
four  phases  represented  by  color-coded  blocks:  blue  for  actual  move-
ment  (C1),  light  blue  for  motor  imagery  (C2),  purple  for  watching  a 
video (C3), and green for the recall phase (C4). Each color block rep-
resented a 40 s duration, including 10 s of preparation and 30 s of task 

3 

​
​
​
​
​
​
​
​
J. Ma et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120949 

performance,  repeated  over  three  cycles.  The  recall  phase,  herein 
referred to as the ’final recall action,’ was an 8-s mental review of the 
tasks performed, intended to reinforce each motor action’s cognitive and 
neural  representation.  This  phase  was  recorded  using  BOLD-fMRI  to 
identify motor areas activated during recall, which was consistent with 
the other task phases. Including this recall phase, the entire sequence for 
each activity totaled 472 s (Fig. 1J).

2.2.2.

Intraoperative ECoG task outline

Participants performed a series of unimanual motor tasks involving 
their  hands  and  tongue.  After  completing  cortical  localization,  they 
proceeded with motor execution and motor imagery tasks following the 
experimental paradigm illustrated in Fig. 1K, while we simultaneously 
recorded cortical activity. The study involved unimanual actions such as 
tapping the index finger of the left hand, tapping the index finger of the 
right hand, protruding the tongue, making a fist with the left hand, and 
making a fist with the right hand. Each task was performed using a single 
limb  at  a  time.  After  each  physical  movement,  participants  vividly 
imagined performing the same task without any actual movement. Each 
training session lasted 8 min and included 5 min of exercise and imag-
ery. They completed five cycles of five actions in each set, totaling five 
sets,  with  a  duration  of  77  s  per  set.  A  fixed  pad  with  a  self-written 
electronic program presented task cues that provided the correspond-
ing visual and auditory prompts, as depicted in Fig. 1N. During each rest 
and  preparation  phase  switch,  the  pad  displayed  a  cross  image  and 
reminded participants to pay attention.

In  our  motor  imagery  paradigm,  the  preparatory  period  involved 
participants receiving specific instructions to focus on the upcoming task 
and establish mental readiness without commencing any motor activity. 
This  stage  was  designed  to  prime  the  cognitive  elements  of  motor 
planning, distinct from the execution phase, where participants imag-
ined  the  enactment  of  the  movement.  Explicit  instructions  delineated 
these  phases,  ensuring  participants  could  differentiate  between  them 
behaviorally and functionally (Guillot et al., 2012).

To  ensure  clear  behavioral  and  functional  distinctions  between 
preparation and execution, separate neural activations expected for each 
phase  were monitored  and recorded.  These activations correlate with 
established neuroscience research on the role of different brain hemi-
spheres and circuits in motor imagery and execution.

2.2.3.

Intraoperative procedure

Awake Craniotomy: The critical points of awake craniotomy include 
patient positioning, awake anesthesia, neuro-navigation, intraoperative 
ultrasonography,  direct  electrical  stimulation  (DES)  mapping,  and 
tumor  resection.  The  medical  team  anesthetized  all  patients  with  a 
target-controlled  infusion  of  propofol  and  remifentanil  and  intubated 
them with a laryngeal mask airway during the craniotomy. Local anes-
thetic  with  epinephrine  (1:200,000),  0.67  %  lidocaine,  and  0.33  % 
ropivacaine was injected into the ipsilateral critical sensory scalp nerves, 
needle  insertion,  and  scalp  incision  sites  to  provide  rapid  and  lasting 
local anesthesia and minimize bleeding. Ultrasound was utilized intra-
operatively to locate the tumor before brain localization and subsequent 
resection. DES mapping was performed using a bipolar nerve stimulator 
(Osiris NeuroStimulator; informed Medizintechnik GmbH, Emmendin-
gen,  Germany)  at  5  mm  intervals,  with  a  frequency  of  60  Hz,  pulse 
duration of 1 ms, and current ranging from 2 to 6 mA (typically 3–4 mA).
Motor and sensory tasks are timed at 1 s, while language or other 
cognitive tasks are timed at 4 s. When stimulation induced contralateral 
limb or facial movement, it was considered positive for the motor area. 
The sensory area’s impulse was positive if it caused abnormal sensations 
in the contralateral limb or face. It was considered positive if the patient 
exhibited counting stops, aphasia, speech repetition, or other language 
disorders without seizures upon inspiration in the language area. Sur-
geons  alternated  resection  with  regular  subcortical  stimulation  after 
mapping  the  cortex  and  removing  the  lesion.  While  resecting  near 
subcortical structures, surgeons instructed patients to move their arms, 

4 

hands, or legs, count numbers, or name pictures to protect functional 
pathways. Surgeons immediately performed subcortical DES using the 
same  stimulus  parameters  if  a  patient  exhibited  limb  weakness,  lan-
guage, or sensory abnormalities. Surgeons confirmed the necessity of a 
subcortical  conduction  pathway  if  positive  responses  were  observed. 
They  then  interrupted  resection  in  this  direction  and  continued  in 
others. Resection continued after the patient’s functional recovery until 
reaching subcortical areas (positive stimulus) or normal brain bound-
aries,  like  the  falx  cerebri,  fissure,  ventricle,  or  arachnoid  border,  or 
when ordinary white matter was visible beyond 1 cm around the tumor 
if no positive response occurred. Surgeons performed tumor resection 2 
mm from eloquent brain areas within the sulcus and then within the pia 
mater to avoid damage to essential arteries in the subarachnoid space. 
Surgeons safely removed the lesion to preserve critical functional areas, 
cortical and subcortical structures of the draining veins, and supplying 
arteries. After identifying available regions, they safely placed the ECoG 
grid on the exposed brain surface to record cortical activity.

2.3. Data analysis

2.3.1. fMRI data analysis

2.3.1.1. The  preliminary  processing  of  task-oriented  data. After the par-
ticipants completed the tasks, the researchers collected and organized 
the  data  using  MATLAB.  For  preprocessing,  MRI  data  analysis  was 
conducted using Statistical Parametric Mapping software (SPM 12; http 
://www.fil.ion.ucl.ac.uk/spm/). Each scan has an inherent 2-s delay due 
to the magnetic resonance instrument’s shimming process, yielding 118 
whole-brain images per run (including 28 slices per brain volume) and 
totaling 236 volumes for analysis.

The preprocessing sequence was as follows: 1) Slice-timing correc-
tion  using  the  27th  slice  as  the  reference;  2)  Head  motion  correction 
with  stringent  parameters  (realign) ensuring  translational movements 
within 3 mm and rotational movements within 1
; 3) Spatial normali-
zation using the  Montreal Neurological Institute (MNI) template with 
bounding boxes set to [(cid:0) 90 (cid:0) 126 (cid:0) 72] and [90 90 108]; 4) Smoothing 
applied twice with a 4 mm FWHM Gaussian kernel to individual images 
after realignment and to the normalized group data.

◦

A  design  matrix  was  created  for  statistical  analysis  incorporating 
multiple  regressors  derived  from  head  motion  correction.  Each  run’s 
head movement parameter files were incorporated into the model, fol-
lowed  by  time  series  examination  and  spectral  density  plot  analysis. 
Parameter estimates obtained from the model were subjected to a single- 
sample t-test, allowing us to pinpoint active motor areas with significant 
BOLD signal changes.

2.3.1.2. Centrally presents the visualization of the task-activated regions.
The  researchers  processed  and  analyzed  data  using  a  general  linear 
model to identify active brain regions during task performance. Signif-
icant activity changes in the relevant brain regions during task perfor-
mance were determined by comparing brain activity during the task and 
resting states.

To further process the image data, a skull-stripping algorithm was 
employed  as  a  preliminary  step  for  the  structural  image  data.  This 
crucial  step  aimed  to  eliminate  interference  from  the  skull  and  other 
non-brain  structures,  revealing  the  brain’s  anatomical  structure  more 
clearly. After skull stripping, the quality of the structural image data was 
enhanced, facilitating more accurate localization and interpretation of 
the functional data.

Finally,  the  visualization  toolkit  was  used  for  three-dimensional 
reconstruction  and  rendering.  This  process  involves  combining  pro-
cessed  fMRI  data  with  skull-stripped  structural  image  data  to  present 
them in a three-dimensional form.

J. Ma et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120949 

2.3.2. Electrocorticography (ECoG) data recording and processing

ECoG  signals  were  continuously  recorded  in  the  resting  and  task 
states using an XLTEK Netlink LTM 128-channel amplifier (USA) with a 
reference connection to the ipsilateral mastoid. An 8 × 3 cortical strip 
electrode  (Huake  Electrode, China)  maintained  EEG  electrode  imped-
ances  below  5  kΩ.  The  system  sampled  the  signals  at  1024  Hz  and 
filtered  them  between  0.1  and  100  Hz.  For  continuous  ECoG  signal 
recording,  the  process  involved  using  a  high-density  3  × 8  electrode 
array placed over the functional areas of the patient’s brain.

2.3.2.1. Data  preprocessing. Python  3.8  scripts  performed  ECoG  pre-
processing, which included detrended fluctuation analysis and a 1–200 
Hz band-pass filter (based on a 2nd-order Butterworth digital filter) to 
remove  the  baseline  drift  caused  by  ultra-low-frequency  signals.  The 
scripts also applied notch filters at specific frequencies (50 Hz, 100 Hz, 
150 Hz, and 200 Hz) using an infinite impulse response digital filter to 
eliminate power line interference. After filtering, the scripts read signals 
from 24 channels during each actual movement and motor imagery task, 
excluding channels 1, 8, 17, and 18, which were not placed in practical, 
functional areas. This process included the preparatory period (2–3 s) 
before  each  action  and  the  action  execution  period  (5  s).  For  each 
channel,  the  scripts  calculated  the  average  signal  value  and  standard 
deviation  during  the  preparatory  period  as  a  baseline.  We  used  the 
preparatory period as a baseline to establish a ready state reference for 
each  motor  task.  However,  to  ensure  a  clear  demarcation  between 
cognitive  anticipation and  actual motor  execution, we  have reconsid-
ered this approach. We now establish baseline levels based on a proper 
resting  state  without  specific  task-related  cognitive  or  motor  activity. 
This  adjustment  provides  a  more  accurate  measure  against  which  to 
compare the neural activity during the actual motor and imagery tasks 
(Jeannerod, 2001).

The signs were normalized before and after the onset of action using 
z-scores.  The  observations  revealed  significant  anomalies  (exceeding 
four standard deviations) during the preparatory and execution phases 
of the activity. We removed all signal segments’ initial and final 0.25 s to 
avoid interference from anomalies in the analysis. The other parts with 
abnormalities were detected and restored in three steps. 

(a)  Cubic  spline  interpolation  is  used  to  determine  the  upper  and 

lower envelopes of the signal.

(b)  Observation areas exceeding four standard deviations
(c)  Restore  the  anomalous  areas  by  detrending  or  covering  all 

abnormal areas with the nearest average signal.

2.3.2.2. Data analysis.

(1) Time-frequency and frequency-domain integration analysis

The preprocessed signal was analyzed using the short-time Fourier 
transform  algorithm  to  obtain  a  time-frequency  graph  of  the  signal 
segment. Averages of the time-frequency graphs were calculated from 
five  repetitions  of  each  action  to  discern  the  differences  between  the 
actual movement and motor imagery. These averages served as the time- 
frequency graph for the effort and corresponding motor imagery period. 
Following this, the differences in power and phase between the actual 
movement and motor imagery segments were compared by calculating 
the  integral  curves  (total  capacity)  of  the  alpha  (8–13  Hz)  and  beta 
(13–30 Hz) bands in the average time-frequency graphs. (2) static and 
dynamic brain area heatmaps.

To obtain a static heat map, we calculated the power difference of 
each channel’s preprocessed signal after the action started, compared to 
the  preprocessed  signal  before  the  beginning.  The  power  from  the 
ineffective electrodes was set to zero.

To explore the temporal variation of brain area power during actual 
movement and motor imagery, we applied a sliding window algorithm 

with a window length of 0.5 s and a step length of 0.1 s to the signals of 
all channels after the action started. We calculated the power difference 
within each window and compared it to the preprocessed signal before 
the action started to create dynamic heatmaps.

3. Results

3.1. Preoperative fMRI results

Analysis  of  activation  patterns  across  the  11  participants  during 
motor imagery tasks revealed activation in motor cortex regions. Spe-
cifically, activation was observed in areas associated with motor func-
tion and planning, such as the precentral gyrus and inferior frontal gyrus 
(Fig.  2A–N).  The  activation  patterns  varied  among  participants,  with 
some showing bilateral activation and others exhibiting more lateralized 
patterns (Table 2).

The degree of lateralization differed across the cohort. While acti-
vation was present in the motor cortices, the expected dominant hemi-
sphere  activation  controlling  contralateral  hand  movements  was  not 
consistently observed in all participants. Fig. 2O summarizes the overall 
activation patterns during motor imagery tasks across participants.

3.2. Intraoperative ECoG observations

Intraoperative ECoG data were collected from functional brain areas 
adjacent to the left surgical region (Fig. 3A). During motor imagery tasks 
involving  tapping  with  the  left  and  right  index  fingers,  significant 
desynchronization was observed. Specifically, during the motor imagery 
of tapping with the left index finger, 10 electrodes over the left hemi-
sphere showed significant desynchronization, as illustrated in Fig. 3B. 
During  the  motor  imagery  of  tapping  with  the  right  index  finger,  18 
electrodes over the left hemisphere also exhibited significant desynch-
ronization, as shown in Fig. 3C.

In our analysis, channels 5 and 16 exhibited notable desynchroni-
zation in both the alpha (8–13 Hz) and beta (13–30 Hz) frequency bands 
during motor execution and motor imagery tasks. 

• Panels A and B of Fig. 4 illustrate the alpha and beta band power 
maps  of  the  left  hand’s  motor  imagery  projected  onto  the  brain. 
These  maps  highlight  regions  where  significant  desynchronization 
occurred during the motor imagery of left-hand movements.

• Panels C and D display similar alpha and beta band power maps for 
the right hand’s motor imagery, indicating desynchronization areas 
during the motor imagery of right-hand movements.

• Panels E and F present the frequency domain integrals for the alpha 
band recorded by electrode 5 during left index finger tapping. The 
blue  line  represents  actual  movement,  and  the  red  line  represents 
motor  imagery.  These  comparisons  show  differences  in  power 
spectral density between the two conditions.

• Panels G and H provide the beta band frequency domain integrals for 
the same electrode and task, again comparing actual movement (blue 
line) and motor imagery (red line).

• Panels  I  and  J  depict  the  alpha  band  frequency  domain  integrals 
recorded  by  electrode  16  during  right  index  finger  tapping,  with 
comparisons between actual movement and motor imagery.

• Panels K and L show the beta band frequency domain integrals for 
electrode 16, highlighting the differences between actual movement 
and motor imagery.

These analyses demonstrate that channels 5 and 16 showed signifi-
cant  desynchronization  in  both  alpha  and  beta  bands  during  motor 
imagery tasks, mirroring the patterns observed during actual movement. 
This provides further evidence of the dynamic changes in brain activity 
within these specific frequency bands during motor imagery.

These panels emphasize the significant desynchronization observed 
in  channels  5  and  16  during  motor  imagery  tasks,  illustrating  the 

5 

J. Ma et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120949 

Fig. 2. Brain activation during various finger movements.
Panels A–M display brain activation during tasks involving the left and right index fingers. Each panel corresponds to a specific Region of Interest (ROI) and task 
condition as follows: S1: Session involving tasks with the left index finger, S2: Session involving tasks with the right index finger, C1: Actual movement, C2: Motor 
imagery, C3: Video watching, C4: Recall phase. Panels I-M illustrate the brain activation regions during bilateral index finger tapping, activating both sides of the 
brain, including supplementary motor areas, motor areas, and parts of the frontal, parietal, and occipital lobes.Panel O depicts the activated brain regions for both 
hands (S1 and S2) of the 11 participants in the cohort.

changes in brain activity within the alpha and beta frequency bands.

Three phases were identified in the data analysis: 

(1)  Onset of Motor Imagery: Specific activity patterns in the α and β 
frequency bands were noted at the beginning of motor imagery.
(2) Transition  Phase:  A shift  from synchronization  to  desynchroni-

• Panels G–I illustrate the transition phase in the alpha band, where 
desynchronization becomes more pronounced, indicating increased 
cortical involvement.

• Panels J–L display the full desynchronization phase in the beta band, 

corresponding to sustained motor imagery activity.

zation was observed.

4. Discussion

(3)  Complete  Desynchronization:  A  clear  change  in  brain  activity 
patterns indicated full engagement in the motor imagery state.

To illustrate the dynamic changes in brain area power during motor 
imagery tasks, we generated heatmaps focusing on the alpha and beta 
frequency bands. Fig. 5 presents these dynamic brain area power graphs, 
highlighting different phases of motor imagery processing: 

• Panels  A–C  show  the  initial  activation  phase  in  the  alpha  band, 
representing the onset of desynchronization as the participant begins 
motor imagery.

• Panels D–F depict the initial activation phase in the beta band during 

the same period.

Our study demonstrates that motor imagery tasks elicit significant 
activation  in  bilateral  motor  cortical  areas,  particularly  the  supple-
mentary motor area (SMA) and primary motor cortex (M1). Preopera-
tive  fMRI  analyses  revealed  engagement  of  both  hemispheres  during 
motor imagery, aligning with previous findings (Gerardin et al., 2000; 
Solodkin et al., 2004). Notably, heightened activation was observed in 
areas corresponding to the dominant hand, underscoring hemispheric 
specialization  in  motor  control.  Analysis  of  the  preoperative  fMRI 
revealed  significant  activation  of  the  bilateral  motor  cortical  areas, 
particularly the supplementary and primary motor areas, during motor 
imagery (Crotti  et  al., 2022; Lebon et  al., 2018; Marzoli  et  al.,  2013; 
Zapała et al., 2021). The observed activations during movement prep-
aration  and  simulation  illustrate  the  integrated  contribution  of  the 
frontal, parietal, and occipital lobes, highlighting a network approach to 

6 

J. Ma et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120949 

Table 2 
Activation points during task execution.

Region 
ID

Brain area name

MNI coordinates 
(X, Y, Z)

Session- 
condition

1
2
3
4

5

6

7
8
9

10
11

12

13

Right Inferior Occipital Gyrus
Left Superior Occipital Gyrus
Left Superior Occipital Gyrus
Right Inferior Frontal Gyrus 
(Triangular Part)
Left Inferior Frontal Gyrus 
(Frontal Pole)
Left Precentral Gyrus (Frontal 
Middle Gyrus)
Left Inferior Frontal Gyrus
Right Anterior Cerebellar Lobe
Right Transverse Temporal 
Gyrus
Left Inferior Frontal Gyrus
Right Transverse Temporal 
Gyrus
Right Transverse Temporal 
Gyrus
Left Inferior Occipital Gyrus

39.4 (cid:0) 74.9 (cid:0) 11
(cid:0) 7.78 (cid:0) 92.8 22
(cid:0) 3.67 (cid:0) 87.3 15
35.4 50.6 (cid:0) 4.06

S1-C1
S1-C2
S1-C2
S1-C4

(cid:0) 2.38 47.3 (cid:0) 25.8

S2-C1

(cid:0) 38.3 (cid:0) 17 54.9

(cid:0) 43.9 15.6 (cid:0) 23.8
17.8 (cid:0) 42.5 (cid:0) 46.6
64.2 (cid:0) 35.8 (cid:0) 2.63

(cid:0) 1.18 45.3 (cid:0) 6.82
64.2 (cid:0) 35.8 (cid:0) 2.63

(cid:0) 12.4 (cid:0) 78.2 4.7

S2-C1

S2-C1
S2-C3
S2-C3

S2-C3
S2-C3

S2-C3

(cid:0) 30.4 (cid:0) 74.9 (cid:0) 11

S2-C3

Abbreviations: Sessions (S):S1: Light tapping with the left index finger, S2: Light 
tapping with the right index finger, S3: Sticking out the tongue, S4: Threading a 
needle with the right hand, Conditions (C): C1: Actual movement, C2: Motor 
imagery, C3: Watching a video, C4: Recall phase.

understanding  brain function  in motor  tasks (Watanabe et  al., 2002). 
Subsequent  analysis  indicated  a  more  pronounced  activation  in  the 
functional  brain  areas  correlated  with  the  dominant  motor  hand  of 
participants during motor imagery tasks. This observation agrees with 
established  neuroscience  theories  suggesting  that  the  left  brain  pre-
dominantly governs right-sided movement in right-handed individuals. 
Such  a  phenomenon  is  markedly  present  during  motor  imagery,  sug-
gesting brain lateralization that occurs even without physical action.

Intraoperative  ECoG  data  provided  detailed  insights  into  cortical 
dynamics  during  motor  imagery.  Significant  desynchronization  was 
observed in the alpha and beta bands, especially in electrodes overlying 
motor areas. This finding is consistent with prior studies indicating that 
desynchronization  in  these  frequency  bands  is  associated  with  active 
motor processing, even in the absence of overt movement (Panov et al., 
2017). The desynchronization patterns were more pronounced during 
tasks involving the dominant hand, reinforcing the role of hemispheric 
dominance. Specifically, we observed notable desynchronization during 
the participants’  motor-imagery tapping tasks using the left and right 

index  fingers.  This  desynchronization  demonstrates  that  the  cerebral 
cortex remains active during motor imagery even without movement. 
This  finding  contributes  to  our  understanding  of  how  the  brain  may 
simulate  movement,  as  evidenced  by  observed  desynchronization  in 
motor  imagery  tasks  (Igasaki  et  al.,  2018;  Vukeli´c  et  al.,  2019;  Yang 
et  al.,  2021;  Zapała  et  al.,  2020).  This  is  consistent  with  previous 
neuroscience research highlighting multiple brain regions’ coordinated 
engagement  during  motor  imagery.  Our  study  confirmed  this  finding 
and  provided  new  perspectives  on  how  these  brain  regions  interact 
during motor imagery by combining fMRI and ECoG data. Specifically, 
the  ECoG  data  revealed  how  the  brain  simulates  movement  through 
desynchronization without actual action.

In this focused case study, we recognize the potential for individual 
variation  due  to  tumor  location  and  awake  craniotomy.  Despite  the 
inherent  variability  of  tumor-induced  neuroanatomical  changes,  the 
precise localization of our subject’s tumor, based on classic landmarks, 
provided a unique and accurate backdrop for our functional mapping 
(Zakaria et al., 2018). This precision enhances the scientific reliability of 
our findings despite the acknowledged variability that may arise in MR 
imaging and more extensive cohort studies. As such, in our single-case 
study,  the  individual  variability  in  neuroanatomical  terms  was  mini-
mal.  We  are  committed  to  further  exploring  individual  differences  in 
future  studies  with  a  more  extensive  patient cohort  to  generalize  our 
findings robustly (Ojemann et al., 2008).

First,  the  static  brain  area  power  graphs  alpha  and  beta  band 
revealed  that the  unilateral  motor  cortex  could produce  desynchroni-
zation activation during bilateral motor imagery tasks. These activation 
sites aligned with the fMRI results, suggesting the potential role of the 
unilateral  motor  cortex  in  governing  bilateral  motor  imagery  tasks. 
Previous  studies  using  noninvasive  techniques  such  as  EEG  demon-
strated desynchronization activation in the motor cortex during physical 
and  imagined  movements.  Our  study  builds  on  this  with  more 
convincing  evidence  from  higher  temporal  resolution  ECoG  data, 
aligning with the preoperative fMRI data. Bilateral brain activity was 
recorded  in  participants  even  during  unilateral  motor  imagery  tasks, 
suggesting the involvement of both hemispheres in the mental simula-
tion of movement (Errante et al., 2019). Our results indicate that the 
brain’s processing of motor tasks involves functional differentiation and 
cooperation  between  hemispheres,  enriching  our  understanding  of 
motor imagery.

These  findings  support  established  theories  on  interhemispheric 
communication  and  the  integrated  nature  of  motor  planning  and 
execution (Cook et al., 1994; Jarczok et al., 2021), and are consistent 

Fig. 3. Cortical mapping and ECoG electrode placement.
Panel A shows the mapping of the surgical area on the patient’s brain and the corresponding ECoG electrode placement based on functional MRI-derived brain 
meningeal mapping. Panels B and C display time-frequency maps of left and right-hand motor imagery related to cortical EEG electrode placements on the brain, with 
electrodes 1–8, 9–16, 17–24 from left to right, and color-coded electrode stripes (green, red, blue) from top to bottom. Blank spaces indicate that no EEG signals were 
collected in these areas.

7 

J. Ma et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120949 

example, in conditions such as stroke or other disorders causing loss of 
function on one side of the body, activating the unaffected hemisphere 
may play a vital role in patient rehabilitation. This discovery opens up 
possibilities for developing new rehabilitation training methods, mainly 
using  motor  imagery as  an  intervention  measure.  Finally,  the  partici-
pation of the ipsilateral brain in unilateral motor imagery could signif-
icantly  impact  the  development  of  brain–machine  interface  (BMI) 
technology.  BMIs  rely  on  decoding  brain  signals  to  control  external 
devices and computers. Our study suggests that even in bilateral motor 
imagery,  the  activity  of  the  ipsilateral  brain  should  be  considered, 
potentially  offering  new  approaches  for  enhancing  the  accuracy  and 
efficiency of BMI systems. The involvement of the ipsilateral brain in 
unilateral motor imagery provides new insights into how the brain co-
ordinates and optimizes movement and offers valuable information for 
multiple fields of neuroscience, including disease rehabilitation, devel-
opment of BMI technology, and broader cognitive science research. This 
discovery  underscores  the  flexibility  and  diversity  of  the  brain  as  a 
highly integrated and coordinated system for handling complex tasks. 
Future  research  will  further  reveal  the  mechanisms  underlying  these 
processes in the brain, thus providing a more profound understanding 
and practical application strategies.

The  significant  desynchronization  observed  in  the  alpha  and  beta 
bands  during  motor  imagery  underscores  the  active  engagement  of 
cortical networks even in the absence of physical movement. This neural 
activity  is  crucial  for  the  development  of  brain–machine  interfaces 
(BMIs), as desynchronization patterns can be utilized to decode motor 
intentions and control external devices for patients with motor impair-
ments.  By  harnessing  these  neural  signals,  BMIs  can  become  more 
responsive  and  accurate,  enhancing  their  effectiveness  in  assistive 
technologies.

Moreover,  the  implications  for  rehabilitation  are  profound.  Incor-
porating  motor  imagery that induces  desynchronization into  rehabili-
tation  protocols  may  promote  neural  plasticity  and  facilitate  the 
recovery of motor functions. Engaging both hemispheres through motor 
imagery can aid in functional reorganization of neural networks, offer-
ing new avenues for therapy in conditions such as stroke or unilateral 
motor deficits. Understanding the bilateral involvement during motor 
imagery allows for the design of more effective rehabilitation strategies 
tailored to individual neural architectures.

Subsequent research is required to establish if the activation patterns 
observed in the ipsilateral hemisphere during motor imagery could pave 
the way for innovative treatments in neurological rehabilitation (Yang 
and  Ogawa,  2022).In  designing–Machine  Interface  (BMI)  systems, 
knowledge of how the brain performs motor imagery bilaterally can help 
decode brain signals more precisely, thus improving the accuracy and 
efficiency of these systems. This knowledge can significantly enhance 
the  practicality  and  effectiveness  of  plans,  especially  for  developing 
BMIs to assist disabled individuals or rehabilitation patients. While our 
study has made progress in revealing the mechanisms underlying brain 
motor imagery, many questions remain unanswered (Bennet and Reiner, 
2022; Fazeli et al., 2021; Maier et al., 2019; Mizuguchi and Kanosue, 
2017; Monaco et al., 2020; Vasilyev et al., 2017; Yoo et al., 2020). For 
example,  do  different  types  of  motor  imagery  (such  as  simple  versus 
complex movements) activate other brain areas? Does the brain exhibit 
different activation patterns after long-term motor training? Addition-
ally, is the involvement of the bilateral brain consistent across all in-
dividuals, or does it vary based on individual differences (such as left- or 
right-handedness)? Answering these questions will deepen our under-
standing of the mechanisms of motor imagery in the brain and guide 
future clinical applications and research.

This  study  demonstrated  bilateral  involvement  and  significant 
desynchronization of the brain during unilateral motor imagery. Further 
studies  are  needed  to  confirm  whether  activation  of  the  ipsilateral 
hemisphere in motor imagery can offer new insights into neurological 
disease treatment. However, our study has some limitations that indi-
cate possible directions for future research. The primary burden lies in 

Fig. 4. Mapping of static brain region power in alpha and beta bands during 
motor imagery.
Panels  A  and  B:  Alpha  and  beta  band  power  maps  of  the  left  hand’s  motor 
imagery  projected  onto  the  brain,  highlighting  regions  of  desynchronization. 
Panels C and D: Alpha and beta band power  maps of  the right hand’s motor 
imagery,  indicating  areas  of  desynchronization.  Panels  E  and  F:  Frequency 
domain  integrals  in  the  alpha  band  for  left  index  finger  tapping  recorded  by 
electrode  5,  comparing  actual movement  (blue  line)  and  motor  imagery  (red 
line).  Panels  G  and  H:  Frequency  domain  integrals  in  the  beta  band  for  left 
index  finger  tapping  by  electrode  5,  comparing  actual  movement  and  motor 
imagery. Panels I and J: Frequency domain integrals in the alpha band for right 
index finger tapping recorded by electrode 16, comparing actual movement and 
motor imagery. Panels K and L: Frequency domain integrals in the beta band for 
right  index  finger  tapping  by  electrode  16,  comparing  actual  movement  and 
motor imagery.

with previous studies indicating shared neural substrates between motor 
imagery and execution. By demonstrating bilateral activation and sig-
nificant desynchronization during motor imagery, our results enrich the 
understanding  of  motor  imagery  mechanisms  and  highlight  the 
complexity of neural networks involved in motor control.

The study provides evidence that may extend our understanding of 
brain  localization  theories,  highlighting  the  importance  of  neural 
network integration in task processing. Moreover, this phenomenon may 
reveal how the brain flexibly switches between cognitive states. While 
the contralateral hemisphere primarily controls the actual movement, 
co-participation  of  the  ipsilateral  brain  in  motor  imagery  may  reflect 
different working modes of the brain in simulating and planning exer-
cises. This mode switching is crucial for understanding how the brain 
adapts  to  other  task  demands,  especially  in  brain–machine  interfaces 
and  neurorehabilitation  applications.  Additionally,  activation  of  the 
ipsilateral hemisphere in motor imagery may provide new perspectives 
for  understanding  and  treating  certain  neurological  diseases.  For 

8 

J. Ma et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120949 

Fig. 5. Dynamic changes in brain area power during motor imagery tasks.
(A–C) Initial activation phase in the alpha band showing the onset of desynchronization during motor imagery of index finger tapping. (D–F) Initial activation phase 
in  the  beta  band  for  the  same  task.  (G–I)  Transition  phase  in  the  alpha  band  illustrating  increased  desynchronization  as  motor  imagery  progresses.  (J–L)  Full 
desynchronization phase in the beta band indicating sustained neural engagement during motor imagery.

the small number of participants and their unique medical backgrounds. 
Future studies should expand the sample size to include individuals of 
different  ages,  sexes,  and  handedness  levels  (left-  and  right-handed). 
This expansion will enhance the general applicability and accuracy of 
the research conclusions.

Additionally,  considering  individual  differences  in  brain  structure 
and  function,  future  research  should  explore  the  electrophysiological 
activity  patterns  of  the  brain  during  motor  imagery  across  various 
populations and the connections between these patterns and individual 
characteristics (such as cognitive abilities and motor skills).

Given  that  our  study  primarily  focused  on  the  immediate  brain 
electrical  activity  during  surgery,  long-term  postoperative  brain  elec-
trical  activity  studies  would  be  invaluable  in  enhancing  our  under-
standing.  Conducting  longitudinal  studies  could  provide  insights  into 
the adaptability and recovery capabilities of the brain’s motor system. 
Especially after neurosurgical operations, observing how the brain ad-
justs its functions to adapt to new physical conditions and how these 
adjustments  change  over  time  is  crucial.  This  observation  provides  a 
profound  theoretical  basis  for  neurorehabilitation  and  reveals  brain 
plasticity during injury and repair processes.

Our  findings  have  significant  implications  for  neurorehabilitation. 
The  observed  activation  patterns  during  motor  imagery  suggest  that 
incorporating motor imagery into rehabilitation protocols can enhance 
recovery for patients with motor impairments, such as stroke survivors 
or  individuals  with  neurodegenerative  diseases.  By  actively  engaging 
motor cortical areas through mental simulation of movements, patients 
may promote neural plasticity and facilitate the reorganization of motor 
networks (Batson, 2004; Dunsky and Dickstein, 2018). This aligns with 
existing  therapeutic  strategies  that  utilize  motor  imagery  to  improve 
motor function and suggests that tailored motor imagery practices could 
further optimize rehabilitation outcomes.

Furthermore,  the  significant  desynchronization  observed  in  the 
alpha and beta bands during motor imagery tasks underscores the po-
tential of using these neural signals in brain–machine interface (BMI) 
technologies. BMIs that decode motor intentions from cortical activity 
can  provide  alternative  communication  and  control  pathways  for  in-
dividuals with severe motor disabilities (Bonifazi et al., 2020; Errante 

et al., 2019). Our demonstration of distinct neural patterns associated 
with  motor  imagery  supports  the  development  of  more  accurate  and 
responsive BMIs, capable of interpreting users’  intentions without the 
need for overt movement. This could greatly enhance the quality of life 
for  patients  with  conditions  such  as  amyotrophic  lateral  sclerosis  or 
spinal cord injuries.

One  limitation  of  our  study  is  the  absence  of  electromyography 
(EMG) recordings during the motor imagery tasks. Without EMG data, 
we cannot conclusively confirm that participants did not engage in any 
inadvertent muscle activation during motor imagery. This lack of EMG 
monitoring  means  that  subtle  muscle  movements  could  have  contrib-
uted to the observed neural activity. Future studies should incorporate 
EMG  recordings  to  ensure  that  motor  imagery  tasks  are  performed 
without  actual  muscle  movements,  thereby  isolating  neural  activity 
related solely to motor imagery. These initial findings hint at the brain’s 
potential flexibility and integration in complex tasks, warranting further 
investigation. Despite the insights provided by our study, several limi-
tations should be acknowledged. First, the small sample size and unique 
medical backgrounds of the participants limit the generalizability of our 
findings. Second, the use of unilateral ECoG recordings may not fully 
capture bilateral neural dynamics during motor imagery. Additionally, 
individual differences in brain structure and function, as well as tumor- 
induced  neuroanatomical  changes,  may  have  influenced  the  results. 
Future studies with larger, more diverse cohorts and bilateral recordings 
are needed to validate and extend our findings.

Future  research  should  aim  to  include  a  larger  and  more  diverse 
participant  cohort  to  enhance  the  generalizability  of  the  findings. 
Incorporating  bilateral  ECoG  recordings  would  provide  a  more 
comprehensive view of hemispheric interactions during motor imagery. 
Longitudinal studies could also offer valuable insights into the brain’s 
adaptability  and  recovery  processes  following  neurosurgical  in-
terventions,  contributing  to  the  development  of  targeted  neuro-
rehabilitation strategies.

5. Conclusion

In conclusion, our study provides significant insights into the neural 

9 

J. Ma et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120949 

mechanisms of motor imagery by demonstrating the active involvement 
of  bilateral cortical areas  during unilateral  motor imagery tasks.  This 
challenges traditional views of strict hemispheric lateralization in motor 
control  and suggests  that the  brain utilizes an integrated  network for 
motor planning and simulation, even without actual movement.

These findings are crucial for understanding how the brain adapts to 
motor impairments. Specifically, the observed bilateral activation pat-
terns indicate that motor imagery can engage neural circuits similar to 
those used in physical execution, which may promote neural plasticity 
and facilitate recovery in patients with motor deficits. This highlights 
the potential of incorporating motor imagery into neurorehabilitation 
programs to enhance motor function recovery.

Furthermore,  our  results  have  significant  implications  for  the 
development  of  brain–machine  interface  (BMI)  technology.  By  eluci-
dating  the  neural  signatures  associated  with  motor  imagery,  we 
contribute to creating more precise and responsive BMI systems capable 
of  interpreting  users’  intentions  without  the  need  for  physical  move-
ment.  This  advancement opens  new  possibilities for  assistive  devices, 
potentially  improving  the  quality  of  life  for  individuals  with  severe 
motor impairments.

Overall, our study enhances the understanding of the brain’s func-
tional organization during motor imagery and underscores the impor-
tance of bilateral cortical involvement. Future research should expand 
on  these  findings  by  including  larger,  more  diverse  populations  and 
exploring  the  long-term  effects  of  motor  imagery  practices  on  neural 
adaptability and recovery.

Ethics

A well-trained nurse responsible for intraoperative motor and lan-
guage  testing  conducted  the  intraoperative  stimulation  monitoring 
program and thoroughly informed all patients about the surgical risks. 
Patients  provided  detailed  informed  consent before  surgery  and  were 
kept  awake  during  the  operation  while  ensuring  that  they  did  not 
experience  pain.  All  the  participants  provided  informed  consent.  The 
Southern Theater Command General Hospital of the Chinese People’s 
Liberation  Army  Scientific  Research  Ethics  Committee  approved  the 
research  protocol  (approval  number:  NZLLKZ2022096),  ensuring 
compliance  with  the  ethical  standards  for  research  involving  human 
subjects. This clinical trial was registered in the Chinese Clinical Trial 
Registry (Chictr.org.cn) (ChiCTR2200067029).

Data and code availability statement

The  authors  confirm  that  the  data  supporting  the  findings  of  this 

study are available within the article.

Funding

This  research  did  not  receive  any  specific  grant  from  funding 

agencies in the public, commercial, or not-for-profit sectors.

CRediT authorship contribution statement

Jie  Ma:  Writing  –  review  &  editing,  Writing  –  original  draft. 
Zhengsheng Li: Writing –  review &  editing, Writing –  original draft. 
Qian Zheng: Writing – review & editing, Writing – original draft. Shi-
chen  Li:  Software,  Investigation.  Rui  Zong:  Software,  Investigation. 
Zhizhen Qin: Software, Investigation. Li Wan: Software, Investigation. 
Zhenyu Zhao: Software, Investigation. Zhiqi Mao: Resources, Investi-
gation.  Yanyang  Zhang:  Resources,  Investigation.  Xinguang  Yu:  Su-
pervision,  Project  administration,  Methodology.  Hongmin  Bai: 
Supervision,  Project  administration,  Methodology.  Jianning  Zhang: 
Supervision, Project administration, Methodology.

Declaration of competing interest

The authors declare that they have no known competing financial 
interests or personal relationships that could have appeared to influence 
the work reported in this paper.

Acknowledgments

This research received no specific grant from funding agencies in the 

public, commercial, or not-for-profit sectors.

Data availability

Data will be made available on request. 

References

Batson, G., 2004. Motor imagery for stroke rehabilitation: current research as a guide to 
clinical practice. Altern. Complement. Ther. 10, 84–89. https://doi.org/10.1089/ 
10762800477393332.

Bennet, R., Reiner, M., 2022. Shared mechanisms underlie mental imagery and motor 
planning. Sci. Rep. 12, 2947. https://doi.org/10.1038/s41598-022-06800-9.
Bonifazi, S., Passamonti, C., Vecchioni, S., Trignani, R., Martorano, P.P., Durazzi, V., 

Lattanzi, S., Mancini, F., Ricciuti, R.A., 2020. Cognitive and linguistic outcomes after 
awake craniotomy in patients with high-grade gliomas. Clin. Neurol. Neurosurg. 
198, 106089. https://doi.org/10.1016/j.clineuro.2020.106089.

Borggraefe, I., Catarino, C.B., R´emi, J., Vollmar, C., Peraud, A., Winkler, P.A., 
Noachtar, S., 2016. Lateralization of cortical negative motor areas. Clin. 
Neurophysiol. 127, 3314–3321. https://doi.org/10.1016/j.clinph.2016.08.001.
Breshears, J.D., Gaona, C.M., Roland, J.L., Sharma, M., Bundy, D.T., Shimony, J.S., 
Rashid, S., Eisenman, L.N., Hogan, R.E., Snyder, A.Z., Leuthardt, E.C., 2012. 
Mapping sensorimotor cortex with slow cortical potential resting-state networks 
while awake and under anesthesia. Neurosurgery 71, 305–316. https://doi.org/ 
10.1227/NEU.0b013e318258e5d1 discussion 316. 

Casimo, K., Levinson, L.H., Zanos, S., Gkogkidis, C.A., Ball, T., Fetz, E., Weaver, K.E., 

Ojemann, J.G., 2017. An interspecies comparative study of invasive 
electrophysiological functional connectivity. Brain Behav. 7, e00863. https://doi. 
org/10.1002/brb3.863.

Chacko, A.G., Thomas, S.G., Babu, K.S., Daniel, R.T., Chacko, G., Prabhu, K., Cherian, V., 
Korula, G., 2013. Awake craniotomy and electrophysiological mapping for eloquent 
area tumours. Clin. Neurol. Neurosurg. 115, 329–334. https://doi.org/10.1016/j. 
clineuro.2012.10.022.

Cloud, C., Georgen-Schwartz, K., Hilger, A., 2024. The contributions of pitch, loudness, 
and rate control to speech naturalness in cerebellar ataxia. Am. J. Speech. Lang. 
Pathol. 33, 2536–2555. https://doi.org/10.1044/2024_ajslp-24-00018.

Cook, N.D., Früh, H., Mehr, A., Regard, M., Landis, T., 1994. Hemispheric cooperation in 
visuospatial rotations: evidence for a manipulation role for the left hemisphere and a 
reference role for the right hemisphere. Brain Cogn. 25, 240–249. https://doi.org/ 
10.1006/brcg.1994.1034.

Crotti, M., Koschutnig, K., Wriessnegger, S.C., 2022. Handedness impacts the neural 

correlates of kinesthetic motor imagery and execution: a FMRI study. J. Neurosci. 
Res. 100, 798–826. https://doi.org/10.1002/jnr.25003.

Decety, J., Gr`ezes, J., 2006. The power of simulation: imagining one’s own and other’s 
behavior. Brain Res. 1079, 4–14. https://doi.org/10.1016/j.brainres.2005.12.115.
Dunsky, A., Dickstein, R., 2018. Motor imagery training for gait rehabilitation of people 

with post-stroke hemiparesis: practical applications and protocols. Glob. J. Health 
Sci. 10, 66. https://doi.org/10.5539/GJHS.V10N11P66.

Dziedzic, T.A., Bala, A., Podg´orska, A., Piwowarska, J., Marchel, A., 2021. Awake 

intraoperative mapping to identify cortical regions related to music performance: 
technical note. J. Clin. Neurosci. 83, 64–67. https://doi.org/10.1016/j. 
jocn.2020.11.027.

Errante, A., Bozzetti, F., Sghedoni, S., Bressi, B., Costi, S., Crisi, G., Ferrari, A., Fogassi, L., 
2019. Explicit motor imagery for grasping actions in children with spastic unilateral 
cerebral palsy. Front. Neurol. 10, 837. https://doi.org/10.3389/fneur.2019.00837.

Eseonu, C.I., Rincon-Torroella, J., Lee, Y.M., ReFaey, K., Tripathi, P., Quinones- 

Hinojosa, A., 2018. Intraoperative seizures in awake craniotomy for perirolandic 
glioma resections that undergo cortical mapping. J. Neurol. Surg. A Cent. Eur. 
Neurosurg. 79, 239–246. https://doi.org/10.1055/s-0037-1617759.

Fazeli, D., Taheri, H., Kakhki, A.S., 2021. Utilizing the variability of practice in physical 

execution, action observation, and motor imagery: similar or dissimilar 
mechanisms? Motor Control 25, 198–210. https://doi.org/10.1123/mc.2020-0021.

Folstein, M.F., Folstein, S.E., McHugh, P.R., 1975. ``Mini-mental state". A practical 

method for grading the cognitive state of patients for the clinician. J. Psychiatr. Res. 
12, 189–198. https://doi.org/10.1016/0022-3956(75)90026-6.

Gabriel, D.A., Kamen, G., Frost, G., 2006. Neural adaptations to resistive exercise: 

mechanisms and recommendations for training practices. Sports Med. 36, 133–149. 
https://doi.org/10.2165/00007256-200636020-00004.

Garrett, M.C., Pouratian, N., Liau, L.M., 2012. Use of language mapping to aid in 

resection of gliomas in eloquent brain regions. Neurosurg. Clin. N. Am. 23, 497–506. 
https://doi.org/10.1016/j.nec.2012.05.003.

10 

J. Ma et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120949 

Gerardin, E., Sirigu, A., Leh´ericy, S., Poline, J.B., Gaymard, B., Marsault, C., Agid, Y., Le 
Bihan, D., 2000. Partially overlapping neural networks for real and imagined hand 
movements. Cereb. Cortex 10, 1093–1104. https://doi.org/10.1093/cercor/ 
10.11.1093.

Gerritsen, J.K., Zwarthoed, R.H., Kilgallon, J.L., Nawabi, N.L., Jessurun, C.A., 

Versyck, G., Pruijn, K.P., Fisher, F.L., Larivi`ere, E., Solie, L., 2022. Effect of awake 
craniotomy in glioblastoma in eloquent areas (GLIOMAP): a propensity score- 
matched analysis of an international, multicentre, cohort study. Lancet Oncol. 23, 
802–817. https://doi.org/10.1016/S1470-2045(22)00213-3.

Guillot, A., Di Rienzo, F., Macintyre, T., Moran, A., Collet, C., 2012. Imagining is not 

doing but involves specific motor commands: a review of experimental data related 
to motor inhibition. Front. Hum. Neurosci. 6, 247. https://doi.org/10.3389/ 
fnhum.2012.00247.

Hardwick, R.M., Caspers, S., Eickhoff, S.B., Swinnen, S.P., 2018. Neural correlates of 

action: comparing meta-analyses of imagery, observation, and execution. Neurosci. 
Biobehav. Rev. 94, 31–44. https://doi.org/10.1016/j.neubiorev.2018.08.003.
Igasaki, T., Takemoto, J., Sakamoto, K., 2018. Relationship between kinesthetic/visual 
motor imagery difficulty and event-related desynchronization/synchronization. In: 
Annu Int Conf IEEE Eng Med Biol Soc 2018, pp. 1911–1914. https://doi.org/ 
10.1109/embc.2018.8512673.

Jacobs, M., Briley, P.M., Wright, H.H., Ellis, C., 2023. Marginal assessment of the cost 

and benefits of aphasia treatment: evidence from community-based 
telerehabilitation treatment for aphasia. J. Telemed. Telecare 29, 271–281. https:// 
doi.org/10.1177/1357633x20982773.

Jarczok, T.A., Roebruck, F., Pokorny, L., Biermann, L., Roessner, V., Klein, C., Bender, S., 
2021. Single-pulse TMS to the temporo-occipital and dorsolateral prefrontal cortex 
evokes lateralized long latency EEG responses at the stimulation site. Front. 
Neurosci. 15, 616667. https://doi.org/10.3389/fnins.2021.616667.

Jeannerod, M., 2001. Neural simulation of action: a unifying mechanism for motor 

cognition. Neuroimage 14, S103–S109. https://doi.org/10.1006/nimg.2001.0832.

patients. 1989. J. Neurosurg. 108, 411–421. https://doi.org/10.3171/jns/2008/ 
108/2/0411.

Panov, F., Levin, E., de Hemptinne, C., Swann, N.C., Qasim, S., Miocinovic, S., Ostrem, J. 
L., Starr, P.A., 2017. Intraoperative electrocorticography for physiological research 
in movement disorders: principles and experience in 200 cases. J. Neurosurg. 126, 
122–131. https://doi.org/10.3171/2015.11.Jns151341.

Pereira, L.C.M., Oliveira, K.M., L ‘Abbate, G.L., Sugai, R., Ferreira, J.A., da Motta, L.A., 
2009. Outcome of fully awake craniotomy for lesions near the eloquent cortex: 
analysis of a prospective surgical series of 79 supratentorial primary brain tumors 
with long follow-up. Acta Neurochir. 151, 1215–1230. https://doi.org/10.1007/ 
s00701-009-0363-9.

Picht, T., Kombos, T., Gramm, H.J., Brock, M., Suess, O., 2006. Multimodal protocol for 

awake craniotomy in language cortex tumour surgery. Acta Neurochir. 148, 
127–137. https://doi.org/10.1007/s00701-005-0706-0 discussion 137–128. 
Rech, F., Herbet, G., Moritz-Gasser, S., Duffau, H., 2014. Disruption of bimanual 

movement by unilateral subcortical electrostimulation. Hum. Brain Mapp. 35, 
3439–3445. https://doi.org/10.1002/hbm.22413.

Roberts, R., Callow, N., Hardy, L., Markland, D., Bringer, J., 2008. Movement imagery 

ability: development and assessment of a revised version of the vividness of 
movement imagery questionnaire. J. Sport Exerc. Psychol. 30, 200–221. https://doi. 
org/10.1123/jsep.30.2.200.

Ruddy, K.L., Leemans, A., Woolley, D.G., Wenderoth, N., Carson, R.G., 2017. Structural 

and functional cortical connectivity mediating cross education of motor function. 
J. Neurosci. 37, 2555–2564. https://doi.org/10.1523/jneurosci.2536-16.2017.
Satoer, D., Visch-Brink, E., Dirven, C., Vincent, A., 2016. Glioma surgery in eloquent 
areas: can we preserve cognition? Acta Neurochir. 158, 35–50. https://doi.org/ 
10.1007/s00701-015-2601-7.

Serletis, D., Bernstein, M., 2007. Prospective study of awake craniotomy used routinely 
and nonselectively for supratentorial tumors. J. Neurosurg. 107, 1–6. https://doi. 
org/10.3171/JNS-07/07/0001.

Jung, R.E., Wertz, C.J., Ramey, S.J., Mims, R.L., Flores, R.A., Chohan, M.O., 2020. 

Simon-Martinez, C., Jaspers, E., Alaerts, K., Ortibus, E., Balsters, J., Mailleux, L., 

Subcortical contributions to higher cognitive function in tumour patients undergoing 
awake craniotomy. Brain Commun. 2, fcaa084. https://doi.org/10.1093/ 
braincomms/fcaa084.

Lebon, F., Horn, U., Domin, M., Lotze, M., 2018. Motor imagery training: kinesthetic 
imagery strategy and inferior parietal fMRI activation. Hum. Brain Mapp. 39, 
1805–1813. https://doi.org/10.1002/hbm.23956.

Lechowicz-Głogowska, B., Uryga, A., Weiser, A., Salomon-Tuchowska, B., Burzy´nska, M., 

Fortuna, W., Kasprowicz, M., Tabakow, P., 2022. Awake craniotomy with 
dexmedetomidine during resection of brain tumours located in eloquent regions. 
Anaesthesiol. Intensive Ther. 54, 347–356. https://doi.org/10.5114/ 
ait.2022.123151.

Lu, J.F., Zhang, J., Wu, J.S., Yao, C.J., Zhuang, D.X., Qiu, T.M., Gong, X., Xu, G., Mao, Y., 
Zhou, L.F., 2011. Awake craniotomy and intraoperative language cortical mapping 
for eloquent cerebral glioma resection: preliminary clinical practice in 3.0 T 
intraoperative magnetic resonance imaging integrated surgical suite. Zhonghua Wai 
Ke Za Zhi. Chin. J. Surg. 49, 693–698.

Maier, M., Ballester, B.R., Verschure, P., 2019. Principles of neurorehabilitation after 
stroke based on motor learning and brain plasticity mechanisms. Front. Syst. 
Neurosci. 13, 74. https://doi.org/10.3389/fnsys.2019.00074.

Blommaert, J., Sleurs, C., Klingels, K., Amant, F., Uyttebroeck, A., Wenderoth, N., 
Feys, H., 2019. Influence of the corticospinal tract wiring pattern on sensorimotor 
functional connectivity and clinical correlates of upper limb function in unilateral 
cerebral palsy. Sci. Rep. 9, 8230. https://doi.org/10.1038/s41598-019-44728-9.

Snodgrass, J.G., Vanderwart, M., 1980. A standardized set of 260 pictures: norms for 
name agreement, image agreement, familiarity, and visual complexity. J. Exp. 
Psychol. 6, 174–215. https://doi.org/10.1037//0278-7393.6.2.174.

Solodkin, A., Hlustik, P., Chen, E.E., Small, S.L., 2004. Fine modulation in network 
activation during motor execution and motor imagery. Cereb. Cortex 14, 
1246–1255. https://doi.org/10.1093/cercor/bhh086.

Starowicz-Filip, A., Prochwicz, K., Myszka, A., Krzy˙zewski, R., Stachura, K., Chrobak, A. 
A., Rajtar-Zembaty, A.M., Bętkowska-Korpała, B., Kwinta, B., 2022. Subjective 
experience, cognitive functioning and trauma level of patients undergoing awake 
craniotomy due to brain tumor—Preliminary study. Appl. Neuropsychol. Adult 29, 
983–992. https://doi.org/10.1080/23279095.2020.1831500.

Taylor, M.D., Bernstein, M., 1999. Awake craniotomy with brain mapping as the routine 
surgical approach to treating patients with supratentorial intraaxial tumors: a 
prospective trial of 200 cases. J. Neurosurg. 90, 35–41. https://doi.org/10.3171/ 
jns.1999.90.1.0035.

Maldaun, M.V., Khawja, S.N., Levine, N.B., Rao, G., Lang, F.F., Weinberg, J.S., 

Tong, Y., Pendy Jr, J.T., Li, W.A., Du, H., Zhang, T., Geng, X., Ding, Y., 2017. Motor 

Tummala, S., Cowles, C.E., Ferson, D., Nguyen, A.T., Sawaya, R., Suki, D., Prabhu, S. 
S., 2014. Awake craniotomy for gliomas in a high-field intraoperative magnetic 
resonance imaging suite: analysis of 42 cases. J. Neurosurg. 121, 810–817. https:// 
doi.org/10.3171/2014.6.Jns132285.

Maldonado, I.L., Moritz-Gasser, S., de Champfleur, N.M., Bertram, L., Moulini´e, G., 

Duffau, H., 2011. Surgery for gliomas involving the left inferior parietal lobule: new 
insights into the functional anatomy provided by stimulation mapping in awake 
patients. J. Neurosurg. 115, 770–779. https://doi.org/10.3171/2011.5.Jns112.
Malouin, F., Richards, C.L., Jackson, P.L., Lafleur, M.F., Durand, A., Doyon, J., 2007. The 
kinesthetic and visual imagery questionnaire (KVIQ) for assessing motor imagery in 
persons with physical disabilities: a reliability and construct validity study. 
J. Neurol. Phys. Ther. 31, 20–29. https://doi.org/10.1097/01. 
npt.0000260567.24122.64.

Marzoli, D., Menditto, S., Lucaf`o, C., Tommasi, L., 2013. Imagining others’ handedness: 
visual and motor processes in the attribution of the dominant hand to an imagined 
agent. Exp. Brain Res. 229, 37–46. https://doi.org/10.1007/s00221-013-3587-0.
Meyer, F.B., Bates, L.M., Goerss, S.J., Friedman, J.A., Windschitl, W.L., Duffy, J.R., 
Perkins, W.J., O’Neill, B.P., 2001. Awake craniotomy for aggressive resection of 
primary gliomas located in eloquent brain. Mayo Clin. Proc. 76, 677–687. https:// 
doi.org/10.4065/76.7.677.

Mizuguchi, N., Kanosue, K., 2017. Changes in brain activity during action observation 
and motor imagery: their relationship with motor learning. Prog. Brain Res. 234, 
189–204. https://doi.org/10.1016/bs.pbr.2017.08.008.

Monaco, S., Malfatti, G., Culham, J.C., Cattaneo, L., Turella, L., 2020. Decoding motor 
imagery and action planning in the early visual cortex: overlapping but distinct 
neural mechanisms. Neuroimage 218, 116981. https://doi.org/10.1016/j. 
neuroimage.2020.116981.

Munzert, J., Lorey, B., Zentgraf, K., 2009. Cognitive motor processes: the role of motor 
imagery in the study of motor representations. Brain Res. Rev. 60, 306–326. https:// 
doi.org/10.1016/j.brainresrev.2008.12.024.

O’Brien, M., 2023. Aids to the examination of the peripheral nervous system: 6th edition. 

Pract. Neurol. 23, 263–264. https://doi.org/10.1136/pn-2022-003686.

Ojemann, G., Ojemann, J., Lettich, E., Berger, M., 2008. Cortical language localization in 
left, dominant hemisphere. An electrical stimulation mapping investigation in 117 

imagery-based rehabilitation: potential neural correlates and clinical application for 
functional recovery of motor deficits after stroke. Aging Dis. 8, 364–371. https://doi. 
org/10.14336/ad.2016.1012.

Trimble, G., McStravick, C., Farling, P., Megaw, K., McKinstry, S., Smyth, G., Law, G., 
Courtney, H., Quigley, G., Flannery, T., 2015. Awake craniotomy for glioma 
resection: technical aspects and initial results in a single institution. Br. J. Neurosurg. 
29, 836–842. https://doi.org/10.3109/02688697.2015.1054354.

Vasilyev, A., Liburkina, S., Yakovlev, L., Perepelkina, O., Kaplan, A., 2017. Assessing 

motor imagery in brain-computer interface training: psychological and 
neurophysiological correlates. Neuropsychologia 97, 56–65. https://doi.org/ 
10.1016/j.neuropsychologia.2017.02.005.

Vukeli´c, M., Belardinelli, P., Guggenberger, R., Royter, V., Gharabaghi, A., 2019. 

Different oscillatory entrainment of cortical networks during motor imagery and 
neurofeedback in right and left handers. Neuroimage 195, 190–202. https://doi.org/ 
10.1016/j.neuroimage.2019.03.067.

Watanabe, J., Sugiura, M., Sato, K., Sato, Y., Maeda, Y., Matsue, Y., Fukuda, H., 

Kawashima, R., 2002. The human prefrontal and parietal association cortices are 
involved in NO-GO performances: an event-related fMRI study. Neuroimage 17, 
1207–1216. https://doi.org/10.1006/nimg.2002.1198.

Yang, H., Ogawa, K., 2022. Decoding of motor imagery involving whole-body 
coordination. Neuroscience 501, 131–142. https://doi.org/10.1016/j. 
neuroscience.2022.07.029.

Yang, Y.J., Jeon, E.J., Kim, J.S., Chung, C.K., 2021. Characterization of kinesthetic motor 
imagery compared with visual motor imageries. Sci. Rep. 11, 3751. https://doi.org/ 
10.1038/s41598-021-82241-0.

Yoo, P.E., Oxley, T.J., Hagan, M.A., John, S., Ronayne, S.M., Rind, G.S., Brinded, A.M., 
Opie, N.L., Moffat, B.A., Wong, Y.T., 2020. Distinct neural correlates underlie 
inhibitory mechanisms of motor inhibition and motor imagery restraint. Front. 
Behav. Neurosci. 14, 77. https://doi.org/10.3389/fnbeh.2020.00077.

Zakaria, H.M., Massa, P.J., Smith, R.L., Moharram, T.H., Corrigan, J., Lee, I., Schultz, L., 
Hu, J., Patel, S., Griffith, B., 2018. The reliability of identifying the omega sign using 
axial T2-weighted magnetic resonance imaging. Neuroradiol. J. 31, 345–349. 
https://doi.org/10.1177/1971400918762140.

11 

J. Ma et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120949 

Zapała, D., Iwanowicz, P., Francuz, P., Augustynowicz, P., 2021. Handedness effects on 
motor imagery during kinesthetic and visual-motor conditions. Sci. Rep. 11, 13112. 
https://doi.org/10.1038/s41598-021-92467-7.

Zapała, D., Zabielska-Mendyk, E., Augustynowicz, P., Cudo, A., Ja´skiewicz, M., 
Szewczyk, M., Kopi´s, N., Francuz, P., 2020. The effects of handedness on 
sensorimotor rhythm desynchronization and motor-imagery BCI control. Sci. Rep. 
10, 2087. https://doi.org/10.1038/s41598-020-59222-w.

Zarino, B., Di Cristofori, A., Fornara, G.A., Bertani, G.A., Locatelli, M., Caroli, M., 

Rampini, P., Cogiamanian, F., Crepaldi, D., Carrabba, G., 2020. Long-term follow-up 

of neuropsychological functions in patients with high grade gliomas: can cognitive 
status predict patient’s outcome after surgery? Acta Neurochir. (Wien) 162, 
803–812. https://doi.org/10.1007/s00701-020-04230-y.

Zarino, B., Sirtori, M.A., Meschini, T., Bertani, G.A., Caroli, M., Bana, C., Borellini, L., 

Locatelli, M., Carrabba, G., 2021. Insular lobe surgery and cognitive impairment in 
gliomas operated with intraoperative neurophysiological monitoring. Acta 
Neurochir. 163, 1279–1289. https://doi.org/10.1007/s00701-020-04643-9.

12 

