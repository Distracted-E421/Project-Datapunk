NeuroImage 303 (2024) 120927 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Neural correlates of sensorimotor adaptation: Thalamic contributions to 
learning from sensory prediction error

Shirin Mahdavi a, Axel Lindner b,c,1, Carsten Schmidt-Samoa a,d, Anna-Lena Müsch a,  
Peter Dechent a,d, Melanie Wilke a,e,1,*
a Department of Cognitive Neurology, University Medicine G¨ottingen, G¨ottingen, Germany
b Hertie-Institute for Clinical Brain Research, Division of Neuropsychology, University of Tübingen, Tübingen, Germany
c Tübingen Center for Mental Health, Department of Psychiatry and Psychotherapy, University of Tübingen, Tübingen, Germany
d MR-Research in Neurosciences, University Medicine G¨ottingen, G¨ottingen, Germany
e Cognitive Neurology Group, Department of Cognitive Neuroscience, German Primate Center, Leibniz Institute for Primate Research, G¨ottingen, Germany

A R T I C L E  I N F O

A B S T R A C T

Keywords:
fMRI
Motor learning
Sensory prediction error
Thalamus
Visuomotor adaptation

Understanding the neural mechanism of sensorimotor adaptation is essential to reveal how the brain learns from 
errors, a process driven by sensory prediction errors. While the previous literature has focused on cortical and 
cerebellar  changes,  the  involvement  of  the  thalamus  has  received  less  attention.  This  functional  magnetic 
resonance imaging study aims to explore the neural substrates of learning from sensory prediction errors with an 
additional  focus  on  the  thalamus.  Thirty  participants  adapted  their  goal-directed  reaches  to  visual  feedback 
rotations  introduced  in  a  step-wise  manner,  while  reporting  their  predicted  visual  consequences  of  their 
movements  intermittently.  We  found  that  adaptation  initially  engaged  the  cerebellum  and  fronto-parietal 
cortical regions, which persisted as adaptation progressed. By the end of adaptation, additional regions within 
the  fronto-parietal  cortex  and  medial  pulvinar  of  the  thalamus  were  recruited.  Another  finding  was  the 
involvement  of  bilateral  medial  dorsal  nuclei,  which  showed  a  positive  correlation  with  the  level  of  motor 
adaptation. Notably, the gradual shift in the predicted hand movement consequences was associated with ac-
tivity in the cerebellum, motor cortex and thalamus (ventral lateral, medial dorsal, and medial pulvinar). Our 
study presents clear evidence for an involvement of the thalamus, both classical ‘motor’ and higher-order nuclei, 
in error-based motor learning.

1. Introduction

In order to successfully carry out many daily activities, the central 
nervous system must continually refine motor functions and respond to 
environmental and bodily changes. Central to this process is not only the 
brain’s capacity to learn new motor skills but also maintaining existing 
motor  behaviors.  Performing  motor  actions  in  harmony  with  the  re-
quirements  of  each  situation  depends  on  establishing  an  accurate 
sensorimotor  map  that  links  specific  motor  commands  to  the  desired 
outcomes (i.e. inverse internal models). However, when discrepancies 
emerge between the desired outcome and the performed action, known 
as prediction error, the brain must adjust the internal models of the body 
and  environment  to  achieve  successful  motor  control  (Wolpert  et  al., 

1998). Specifically, an internal forward model is thought to capture the 
predicted sensory consequences of the motor command, while predic-
tion errors serve as a training signal, helping to adapt the inverse in-
ternal model to the new situation (Miall  &  Wolpert, 1996; Shadmehr 
et  al.,  2010).  In  laboratory  settings,  one  of  the  classic  sensorimotor 
adaptation  paradigms  used  to  study  motor  learning  involves  manipu-
lating the relationship between the actual hand position and the corre-
sponding visual feedback (Kim et al., 2021).

While the neural underpinnings of motor learning are not fully un-
derstood,  there  is  evidence  indicating  that  motor  adaptation  is  sup-
ported by a distributed network encompassing the cerebellum, fronto- 
parietal  cortices  and  subcortical  structures.  This  has  been  character-
ized through behavioral studies in patients, demonstrating that damage 

* Corresponding author at: Department of Cognitive Neurology, Heart & Brain Center, University Medicine G¨ottingen, Robert-Koch-Strasse 42, G¨ottingen 37075, 

Germany.

E-mail address: melanie.wilke@med.uni-goettingen.de (M. Wilke). 

1 Equal contribution.

https://doi.org/10.1016/j.neuroimage.2024.120927
Received 1 July 2024; Received in revised form 30 October 2024; Accepted 11 November 2024  
Available online 12 November 2024 
1053-8119/© 2024 University Medical Center Göttingen, Robert-Koch-Str. 40, Göttingen, 37077. Published by Elsevier Inc. This is an open access article under the 
CC BY license ( http://creativecommons.org/licenses/by/4.0/ ). 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

within the cerebellum (Butcher et al., 2017; Synofzik et al., 2008; Tseng 
et al., 2007), parietal cortex (Mutha et al., 2011; Schaefer et al., 2009), 
or the cerebellar thalamus (Chen et al., 2006) results in motor learning 
deficits. While a large body of behavioral evidence has investigated the 
contributions  of  specific  brain  regions  to  error-based  learning,  a 
comprehensive  understanding  of  neural  activation  during  visuomotor 
adaptation  has  not  yet  been  achieved.  A  number  of  studies  have 
employed functional neuroimaging techniques to determine changes in 
brain activation during different stages of motor adaptation (B´edard & 
Sanes, 2014; Graydon et al., 2005; Krakauer et al., 2004; Nezafat et al., 
2001;  Tzvi  et  al.,  2020).  Despite  methodological  differences,  these 
studies  consistently  reported  regions  that  are  recruited  during  the 
establishment of motor learning. For instance, activation of cortical re-
gions including prefrontal, premotor, and parietal cortices has shown to 
be increased during the early phase of learning where errors are more 
salient and decreased over the learning period with improved perfor-
mance (B´edard &  Sanes,  2014; Graydon et al., 2005; Krakauer et  al., 
2004; Tzvi et al., 2020). Additionally, the cerebellum as a main potential 
region for recalibration of internal forward model has shown different 
time-dependent  engagements  with  increase  and  gradual  decrease  of 
activity (Tzvi et al., 2020), increase in activation during the consolida-
tion phase (Graydon et al., 2005), and overall adjustments of learning 
(B´edard & Sanes, 2014).

Aside  from  the  cerebellar-cortical  dependency,  there  is  emerging 
evidence that the thalamus contributes to learning through its extensive 
connections with the fronto-parietal, sensorimotor, and cerebellar net-
works.  Different  thalamic  nuclei  are  highly  interconnected  with 
different structures in the cerebellum and cerebral cortex (Hwang et al., 
2017; Kumar et al., 2022; Prevosto & Sommer, 2013). While most motor 
studies  have  focused  on  motor  thalamic  nuclei  including  the  ventral 
lateral  nucleus  due  to  its  afferent  input  from  the  cerebellum  and  its 
projection to the motor cortex, higher-order thalamic nuclei such as the 
medial  dorsal  nucleus  also  integrate  input  from  the  cerebellum  and 
project to the premotor cortex (Prevosto & Sommer, 2013; Sakai, 2022). 
Furthermore, the medial pulvinar is a multimodal thalamic nucleus with 
extensive  connectivity  to  motor  learning  regions,  including  the  pre-
motor  and  parietal  cortex  (Arcaro  et  al.,  2018;  Froesel  et  al.,  2021; 
Passarelli et al., 2021). Using electrophysiological studies in rodents, it 
has been suggested that the pulvinar not only encodes visual signals but 
also a visuomotor mismatch between movement and visual information, 
indicating  its  role  in  multisensory  integration  (Roth  et  al.,  2016). 
Furthermore, medial pulvinar lesions in humans result in limb-specific 
reach and grasp deficits (Wilke et al., 2018). In neuroimaging studies 
of  motor  learning  in  humans,  increased  activity  in  the  medial  dorsal 
nucleus (MD) and pulvinar has been associated with the early phase of 
motor sequence learning, which was related to learning changes when 
controlled for motor execution (Müller et al., 2002). A study by Shad-
mehr and Holcomb, which employed PET scanning while participants 
were adapted to force field perturbations, also showed brain activation 
in the medial dorsal and pulvinar nuclei. Specifically, the authors found 
that  brain  activations  in  these  regions  were  heightened  during  early 
learning  when  brain  activation  was  compared  to  a  random  field 
perturbation, a similar task condition to adaptation but without learning 
(Shadmehr  &  Holcomb,  1997).  While  thalamic  involvement  in  visuo-
motor adaptation has been observed in other studies using functional 
imaging (Graydon et al., 2005; Ruitenberg et al., 2018; Seidler, 2010), 
its  exact  functional  role  has  remained  less  explored.  To  gain  a  better 
understanding of how the thalamus contributes to motor adaptation, it is 
important to consider the sub-territories of the thalamus to determine 
which  thalamic  nuclei  are  part  of  the  brain  network  that  facilitates 
adaptation.

Although the mentioned neuroimaging studies have shed light on the 
neural  activity  that  governs  motor  learning,  the  errors  serving  as  a 
learning signal to drive adaptation were imposed through abrupt per-
turbations. Although adaptation conventionally has been assumed as an 
implicit  learning  process,  there  is  emerging  evidence  that  besides 

2 

implicit  mechanisms  also  explicit  learning  mechanisms  contribute  to 
learning, with one potentially superseding the other depending on the 
specific  feature  of  the  applied  perturbation  (Taylor  et  al.,  2014).  In 
particular, adaptation to an abrupt and large visual perturbation entails 
cognitive strategies especially in early adaptation phase, when partici-
pants had to counteract the perturbation. Taken together, the increase in 
neural  activity  reported  in  neuroimaging  studies  cannot  be  solely 
attributable to the reduction in sensory prediction error but likely re-
flects also explicit strategies. In contrast, behavioral studies that have 
employed adaptation tasks using smaller steps of increasing perturba-
tions, have shown similar to better adaptation performance compared to 
large,  single-step  perturbations  without  conflating  the  impact  of  stra-
tegic  adjustments  during  adaptation  (Kagerer  et  al.,  1997)  and  with 
larger  aftereffects  (Modchalingam  et  al.,  2023).  However,  the  neural 
processing underlying stepwise motor adaptation, presumably implicit, 
has not been studied.

In  this  functional  magnetic  resonance  imaging  (fMRI)  study,  we 
employed a similar behavioral paradigm to that used in patient studies 
by  Izawa  et  al.  (2012) and  Synofzik  et  al.  (2008),  but  with  several 
modifications  to  accommodate  the  needs  of  our  fMRI  study.  We 
designed  a  visuomotor  adaptation  task  wherein  the  discrepancy  be-
tween  hand  movement  and  visual  cursor  feedback  was  introduced 
incrementally  in  a  stepwise  manner.  Given  the  results  from  similar 
variants  of  this  motor  learning  task,  we  expect  that  participants  will 
adjust their motor performance and thus their inverse internal models in 
response  to  the  rotated  visual  feedback.  Additionally,  we  used  a 
behavioral paradigm to intermittently assess the perceived hand posi-
tion throughout adaptation as a proxy for forward model adaptation. By 
performing fMRI concurrently, we aimed to identify specific thalamic 
nuclei as well as other brain regions that contribute to these mechanisms 
of  sensorimotor  adaptation.  The  experimental  design  was  structured 
into blocks of movement with unperturbed visual feedback (baseline), 
rotated  visual  feedback  (adaptation),  and  no  feedback  (washout). 
Following  each  block,  participants  were  instructed  to  report  their 
perceived hand position after performing a movement in a self-selected 
direction.  By  measuring  hand  perception  intermittently,  we  aimed  to 
explore how participants changed their perception in response to newly 
introduced  levels  of  adaptation  and  identify  brain  regions  associated 
with the change in the predicted visual consequences of hand movement 
as adaptation proceeds.

2. Materials and methods

2.1. Participants

Thirty-six participants  were recruited from the University  Medical 
Center  of  G¨ottingen,  Department  of  Cognitive  Neurology  research 
participant  pool  (22  females;  age  = 24.55  ± 2.56  yrs.,  mean  ± SD). 
Participants  were  screened  using  a  general  health  questionnaire.  All 
participants self-reported being neurologically intact and had normal or 
corrected to normal vision. The study was approved by the local Ethics 
Committee of the Georg-August-University G¨ottingen according to the 
Declaration of Helsinki. Participants provided written informed consent 
and received monetary compensation for their participation (15€/h). Six 
participants were excluded from the analysis: two due to abnormalities 
detected during structural brain imaging, one for failure to follow the 
instructions  properly,  and  one  due  to  incomplete  performance.  Addi-
tionally, one participant was excluded because of severe head motion, 
and another’s behavioral data were not saved correctly. Consequently, 
the final sample cohort consisted of 30 participants (19 females, age =
24.16 ± 2.49 yrs., mean ± SD). The Edinburgh Handedness Inventory 
revealed  that  the  majority  were  right-handed  (29  right-handed,  1 
ambidextrous) (Oldfield, 1971).

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

2.2. Experimental setup

Participants lay supine inside the scanner. Visual stimuli were pre-
sented via a back-projection system (VPixx Technologies, QC, Canada; 
1920 × 1080 screen resolution) located at the rear end of the scanner. 
Participants viewed the screen through a mirror mounted on the head 
coil. An fMRI-compatible digitizing tablet (Hybridmojo LLC, CA, USA, 
size: 25.4 × 20.3 cm) was secured to a Plexiglas board positioned above 
the  participants’  waist  (Fig.  1A).  The  touchscreen  recorded  finger 
movements in Cartesian coordinates at 100 Hz. Movements were always 
started from a central home position, marked by a wooden cube glued to 
the  center  of  the  touchscreen.  Participants  performed  center-out 
reaching movements with the right index finger either toward a target 
displayed in a diagonal direction or a self-chosen direction in the same 
quadrant of the workspace and close to the target location. Given the 
participant’s position inside the scanner, the direct view of the hand was 
precluded. A fiber optic button box (Current Designs, Inc., Philadelphia, 
PA, USA) was used to record responses with the left hand (Fig. 1A, right 
panel). To ensure the participant’s comfort during the experiment, the 
touchscreen  and  the  button  box  positions  were  adjusted  individually 
depending on the participant’s arm length. To minimize head and trunk 
movements, a memory foam cushion was placed beneath the head. The 
chest and arms were stabilized using a strap. During the experiment, the 
scanner room was dimly lit to reduce visual distractions.

2.3. Experimental task

◦

The  experimental  task  was  programmed  in  MATLAB  (The  Math-
Works  Inc.,  2015b)  using  the  Psychtoolbox-3  extension  for  Windows 
(Brainard, 1997). We used a visuomotor adaptation task in which par-
ticipants were required to perform reaching movements to an explicit 
target while receiving online visual feedback of their unseen hand po-
sition (Fig. 1B). At the onset of each trial, a cross sign was displayed for 
500  ms  at the  center of the  screen, signaling  the  start of a  new  trial. 
Participants were instructed to maintain their hand in the home posi-
tion, which was a wooden cube placed on the center of the digitizing 
tablet, to minimize unnecessary movements in finding the starting po-
sition  during  the  preparatory  phase.  To  initiate  a  movement,  a  solid 
white circle (0.4
visual angle) replaced the cross sign, and this circle 
indicated  the  starting  position  on  the  screen.  When  participants  held 
their finger directly above the upper edge of the cube, it was aligned 
with the starting position on the digitizing tablet. The target location 
◦
◦
was indicated by another solid white circle (0.4
visual angle) at a 45
angle from the cardinal axes. The target appeared on an invisible circle 
◦
visual angle from the starting position. The feedback 
with a radius of 4
◦
of  the  hand  was  provided  as  a  solid  white  circle  (0.3
visual  angle). 
When the hand moved to the precise starting position, it turned green, 
indicating that the movement should be performed. Participants were 
instructed  to  move  the  hand  straight  and  rapidly  through  the  target. 
Once the hand exceeded the target location eccentricity, the trial was 
considered completed. Participants had 2 s to complete the movement 
phase, although the movement duration from the starting position to the 
target  was  restricted  to  500  ms.  If  participants  failed  to  execute  the 
movement within this time frame, a ‘Too Slow’ message was displayed 
for a brief period of time (500 ms) to inform them of the speed limit 
violation  in  that  trial.  Similarly,  a  ‘Failed’  message  appeared  on  the 
screen in cases of undershooting. Participants had to release the finger 
from the touchscreen and return the hand to the home position to start 
the  next trial.  Depending  on  the  task  condition,  participants  received 
one  of  three  types  of  visual  feedback:  veridical,  rotated,  or  no  visual 
feedback. During the veridical feedback trials, the visual cursor accu-
rately reflected the finger’s position. In contrast, during the rotated vi-
sual feedback trials, the visual representation of the hand’s position was 
rotated  relative  to  actual  hand  movement.  Additionally,  in  blocks 
without visual feedback, participants performed the task without visual 
cues to guide their movements.

Localization  trials  started  with  an  11  s  fixation  phase,  where  par-
ticipants  were instructed  to  remain  still and  focus on  a  fixation  cross 
displayed on the screen (Fig. 1C). This was followed by a 1 s message 
that  appeared  on  the  screen  prompting  participants  to  prepare  for 
movement  in  a  self-selected  direction.  A  3  s  countdown  signaled  the 
transition from the rest to the movement phase. During the movement 
◦
visual  angle)  appeared  on  the  screen,  indi-
phase,  a  solid  circle  (0.4
cating the starting position. Upon positioning the finger in the starting 
position, the circle turned green, and the feedback cursor was hidden for 
the trial’s duration. Participants had to move the hand toward an arbi-
trary direction and then return it to the home position. Participants were 
instructed before the experiment to only choose directions close to the 
trained target. The movement phase lasted for 3 s. However, a move-
ment  was  considered  successful  if  the  time  from  leaving  the  starting 
position until it reached the maximum amplitude was within 500 ms. To 
isolate  the  BOLD  responses  from  movement  execution  and  response 
recording, another fixation phase was started following the movement 
phase, which lasted for 15 s.

◦

If the movement was successful,  participants entered the response 
phase.  Otherwise,  the  performed  movement  was  considered  an  error 
trial, and the next trial began. In the response phase, participants were 
presented with a dotted circle (radial distance of 4
visual angle, dots 
◦
) to indicate the perceived endpoint of their movement. 
separated by 3
To facilitate the participants’ response recording, a marker (a red hollow 
circle) was presented along the dotted circle, positioned on one of the 
dots in the same quadrant of the workspace. Participants had to indicate 
the corresponding dot they perceived as the crossing point of their hand 
movement by adjusting the marker’s position using two buttons on the 
response box and confirming their choice with a third button (Fig. 1A, 
right  panel).  They  had  4  s  for  response  selection,  with  a  countdown 
displayed  on  the  screen’s  upper  left  corner,  indicating  the  remaining 
time.

2.4. Experimental design

2.4.1. Localizer

On the first visit, a localizer task was carried out to identify brain 
regions associated with basic reach movements. Additionally, this ses-
sion served as a familiarization with the apparatus and task to reduce the 
scanning time in the main experimental session on day 2. In this task, 
participants performed reaching movements toward a target, positioned 
diagonally, the same as the target position in the main experiment (Day 
2).  The  session  included  blocks  of  reaching  under  veridical  visual 
feedback,  no  visual  feedback,  and  movement  observation  from  the 
preceding blocks. Each condition consisted of 6 blocks, with 15 trials 
each, totaling 18 blocks. Each task block was followed by a 20 s rest 
period. During the rest block, a cross sign was displayed. Participants 
were instructed to fixate their gaze on it for the duration of the block.

2.4.2. Main-task fMRI session

Each participant underwent a single fMRI session, divided into two 
functional  runs:  Each  task  run  followed  a  mixed  block/event-related 
design  with  baseline,  adaptation,  and  washout  phases  organized  into 
blocks,  while  interspersed  localization  trials  followed  a  slow  event- 
related design. The use of a block design for adaptation was chosen to 
increase  the  statistical  power  while  preserving  the  continuity  of  the 
learning  process.  Localization  trials  were  treated  as  slow  events  to 
dissociate  the  hemodynamic  response  associated  with  the  movement 
phase from the successive response collection, which would otherwise 
overlap in closely spaced events. The first run consisted of nine sets of 
blocks and event trials, while the second run included 10 sets (Fig. 1D). 
During the first run, participants completed four baseline blocks where 
feedback accurately reflected their actual hand movements. After these 
baseline  blocks,  a  stepwise  visuomotor  rotation  was  introduced, 
◦
◦
increasing the visual rotation by 5
offset  was  reached.  The  visual  cursor  was  deviated  counterclockwise 

every two training blocks until a 15

3 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

(caption on next page)

4 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

Fig.  1. Experimental  design  and  task structure.  (A)  Illustrates a  participant  in  a  supine  position  with  the touch  tablet  positioned  above the  participant’s  waist. 
Participants initiated each trial from a home position. The screen was viewed through a mirror attached to the head coil, and the experimental setup prevented 
participants from seeing their hand movements. The right panel shows the button box used to collect responses during localization trials. (B) Schematic trial timeline 
for movements performed during the blocks. Each trial was initiated with a fixation cross (500 ms) cue at the start, followed by the presentation of a fixation dot and 
target. Participants had 2 s to execute the movement toward the target, with a strict movement duration limit of 500 ms. The feedback phase was only displayed upon 
violation of task conditions, such as being “too slow” or a “failed” attempt. Depending on the task condition in each block, the visual feedback, when presented, was 
either veridical or rotated. In the rotated visual feedback condition, the cursor’s position was shifted counterclockwise relative to the actual hand position. (C) Trial 
timeline for localization trials. The trial started with a 15 s rest phase, followed by a movement phase for 3 s, where participants were instructed to move the hand in 
an arbitrary direction (self-selected target) without receiving any visual feedback. The constraint on movement time was set to 500 ms. The movement phase was 
succeeded by another rest phase (15 s) and a response phase for 4 s, during which participants had to report the estimation of the crossing point between the actual 
performed movement and a displayed dotted circle on the screen. A button box controlled with their left hand was used to collect the responses. The two rightmost 
buttons aimed to move the red hollow circle back and forth, while the third button from the right was used to confirm the answer. (D) Experimental design. The 
experiment consisted of blocks of movement toward an explicit target interspersed with localization trials in an event-related design. The experiment began with four 
◦
blocks of no rotation serving as the baseline. The stepwise adaptation was introduced by incrementally rotating the visual feedback by 5
every two blocks, reaching a 
discrepancy. The adaptation phase was succeeded by washout blocks with no visual feedback to assess aftereffects. Each block consisted of 15 
maximum of a 30
trials. The numbers in the gray squares indicate the size of the rotated visual feedback. During the washout blocks, no visual feedback was presented. Localization 
trials were conducted after each block in a set of four trials (vertical lines).

◦

from the actual hand trajectory. After run 1 and halfway through the 
adaptation phase (after block 9), a 2 min break was provided, allowing 
participants  to  rest  their  hands.  In  the  second  run,  the  adaptation 
training blocks continued following the same procedure as the first run, 
increasing the perturbation between the visual cursor and hand move-
◦
ment to a total of 30
. After completing the adaptation training, par-
ticipants underwent a washout phase consisting of 3 blocks, where their 
relearning performance was assessed under a no-visual feedback con-
dition. In this phase, visual feedback was removed when the hand was 
placed  in  the  starting  position.  Throughout  the  experimental  session, 
localization  trials  were  interspersed  in  a  slow  event-related  design. 
Following  each  block,  participants  completed  four  localization  trials, 
executing movements in a self-selected direction, and then estimating 
their  perceived  crossing  point  for  these  movements.  Before  the  fMRI 
session, participants were reacquainted with the task by completing 60 
trials  of  reaching  the  target  under  veridical  visual  feedback  and  10 
localization trials inside the scanner. These trials were excluded from the 
main analysis.

Upon  completion  of  the  experiment,  participants  were  asked 
whether they noticed any changes in task conditions using a structured 
questionnaire  (Benson  et  al.,  2011).  This  was  done  to  assess  their 
awareness of the visuomotor perturbation, which could potentially lead 
to the use of an explicit cognitive strategy.

2.5. Behavioral analysis

All behavioral and statistical analyses were conducted using custom- 
written scripts in MATLAB (The MathWorks Inc., 2019b) and R (R Core 
Team, 2023). In our analysis cohort, we employed R packages including 
dplyr  (Wickham  et  al.,  2023),  afex  (Singmann  et  al.,  2023),  effsize 
(Torchiano, 2016), rstatix (Kassambara, 2023b), openxlsx (Schauberger 
& Walker, 2023), ggplot2 (Wickham, 2016), and ggpubr (Kassambara, 
2023a). The 2D hand position was recorded at a sampling rate of 100 Hz. 
Before conducting any analysis, data were screened for trials in which 
participants  did  not  meet  the  criteria  of  the  experimental  conditions, 
such  as  trajectory  undershooting  or  not  performing  the  movement 
within the predetermined time frame (mean ± SD of excluded trials: 32 
± 18, 11%). As a second step to define outliers, trials in which the hand 
angle  deviated  by  more  than  3  standard  deviations  from  the  moving 
average of a 5-trial window in each block were excluded from the main 
dataset (<1% of all trials). For each trial, we quantified the hand angle at 
the peak radial velocity, defined as the angle of the line connecting the 
starting position to the peak velocity position of the hand. Accordingly, a 
◦
hand angle of 0
was indicative of alignment with the target position, 
with  positive  and  negative  values  denoting  counterclockwise  and 
clockwise  directions,  respectively.  Additionally,  we  assessed  other 
behavioral metrics, including movement time and reaction time for each 
trial. Movement time was determined as the time from when the hand 

passed the starting position until it reached the target. Reaction time was 
measured  from  the  moment  the  hand  was  positioned  at  the  starting 
position until movement initiation.

Localization  trials:  Localization  trials  were  structured  into  two 
phases:  movement  execution  and  response  submission.  Outlier  trials, 
characterized by incomplete movement execution or participants’ fail-
ure to deliver the response, were excluded from the analysis (mean ± SD 
of excluded trials, 7 ± 7, 8%). Hand position data at the intersection 
between the invisible circle and the hand trajectory were converted to 
angular form to define the measure of hand angle. Similarly, response 
data derived from button box presses were converted into reported hand 
angle. The hand perception on each trial was calculated by subtracting 
the reported angle from the actual hand position (i.e., hand angle – re-
ported  angle).  Therefore,  a  positive  value  indicates  that  participants 
perceived the hand at an angle less than the actual hand position (e.g., 
◦
)), and a negative value showed the perception of the hand 
0
at angles larger than the actual hand position (0
). To assess 
participants’  performance  across  different  stages  of  adaptation,  we 
adopted  a  unified  measure  derived  from  localization  trials.  For  each 
adaptation level, defined by the size of rotation, we averaged the results 
of the 4 localization trials. This averaged perception served as a unified 
measure  of  the  participant’s  performance  at  that  specific  time  point 
within the adaptation phase.

◦
) = -5

◦
) = 5

- (-5

- (5

◦

◦

◦

Statistical  analyses:  Participants’  performance  in  the  adaptation 
blocks  and  localization  trials  was  analyzed  by  employing  repeated 
measure ANOVAs. We conducted separate ANOVAs to assess the effect 
of  adaptation  or  aftereffect  (in  the  washout  phase)  on  hand  angles, 
movement  time,  and  reaction  time,  each  individually  as  the  primary 
dependent  variable.  A  similar  approach  was  utilized  to  evaluate  the 
significance  of  observed  changes  in  the  localization  trials  across 
different time points of learning (adaptation or washout effect). More 
details are described in the results section. Mauchly’s test of sphericity 
was used to examine the homogeneity of variances. Where Mauchly’s 
test  indicated  significant  deviations  from  sphericity  (p  < 0.05)  in 
repeated  measures  ANOVAs,  Greenhouse–Geisser  corrections  were 
implemented to adjust the degrees of freedom for the F-tests. Should the 
ANOVA reveal a significant effect, post-hoc pairwise comparisons were 
conducted.  The  ANOVA  effect  size  was  quantified  with  Partial  Eta 
Squared (Partial ƞ²). The assumption of normality was confirmed by the 
Shapiro-Wilk test. Whenever data did not meet the normality require-
ment for t-tests, the Wilcoxon signed-rank test was performed. Cohen’s 
d and Wilcoxon effect size r were reported for the t-test and Wilcoxon 
signed-rank pairwise comparisons, respectively. To account for multiple 
comparisons, we used the FDR correction method.

2.6. Imaging data acquisition

All  functional  and  structural  imaging  data  were  acquired  on  a  3T 

5 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

Siemens Magnetom Prisma scanner equipped with a  32-channel head 
coil at the University Medical Center G¨ottingen. At the beginning of the 
first  session,  a  high-resolution  structural T1-weighted  dataset  was  ac-
quired with a Magnetization Prepared Rapid Gradient Echo (MPRAGE) 
sequence  (~8.5  min).  The  acquisition  parameters  were  as  follows: 
◦
repetition time (TR) = 2.25 s, echo time (TE) = 3.3 ms, flip angle = 9
, 
with 1 mm isotropic resolution and matrix dimensions of 256 × 256 ×
176.  On  the  second  day,  an  anatomical  T1  dataset  with  accelerated 
acquisition  (integrated  parallel  acquisition  factor  (ipat)  2,  ~4.5  min) 
was obtained to achieve co-registration between sessions.

For each functional scan, the blood-oxygen-level dependent (BOLD) 
responses  were  measured  using  a  gradient  echo-planar  imaging  (EPI) 
sequence  with  the  following  specifications:  TR  = 1.5  s,  TE  = 30  ms, 
acceleration using ipat factor 2 and multiband acceleration factor 3, flip 
angle = 70
, number of slices = 69, 2 mm isotropic resolution. Addi-
tionally, to estimate and correct for distortions arising from magnetic 
field  inhomogeneity,  two  spin-echo  EPI  datasets  with  opposite  phase 
encoding directions were acquired with parameters set as: TR = 5.25 s, 
TE = 0.042 s, slice number = 69, 2 mm isotropic resolution.

◦

2.7. Preprocessing and univariate analysis

The imaging data were preprocessed and analyzed using tools from 
the FSL (FMRIB Software Library, version 6.0 (Jenkinson et al., 2012), 
Statistical Parametric Mapping software (version SPM12: v7487; https 
://www.fil.ion.ucl.ac.uk/spm/),  CONN  toolbox  (Nieto-Castanon  & 
Whitfield-Gabrieli,  2022;  Whitfield-Gabrieli  &  Nieto-Castanon,  2012) 
and custom-written scripts in MATLAB (The MathWorks Inc., 2019b). 
Prior to analysis, all imaging data were reoriented by setting the origin 
of  the anatomical  image to the  anterior commissure’s location.  Func-
tional images were corrected for distortions using the TopUp tool from 
the FSL library (Andersson et al., 2003; Smith et al., 2004). Additionally, 
the NORDIC method was applied to the magnitude images to suppress 
non-Gaussian  noise  components,  addressing  thermal  noise  (Moeller 
et al., 2021). Functional and structural images were preprocessed using 
SPM and included head motion correction using the six-parameter rigid 
body  transformation  (three  translations,  three  rotations),  slice  time 
correction  for  the  multiband  interleaved  sequence,  coregistration  of 
functional data to the individual’s anatomical image, segmentation of 
the brain tissues based on the tissue probability maps, spatial normali-
zation to the Montreal Neurological Institute (MNI) space, and spatial 
smoothing using a Gaussian kernel of 6 mm full width at half maximum 
(FWHM). In a subsequent denoising step, noise components associated 
with white matter (WM) and cerebrospinal fluid (CSF) were estimated 
using  the  aCompCor  approach  implemented  in  the  CONN  toolbox 
(Nieto-Castanon,  2020;  Behzadi  et  al.,  2007;  Chai  et  al.,  2012).  The 
extracted components were then used in the specification of the General 
Linear  Model  (GLM)  design.  Functional  BOLD  signals  were  high-pass 
filtered at 128 s to remove low-frequency artifacts caused by signal drift.

2.7.1. GLM specification

The  preprocessed  functional  data  were  analyzed  using  a  GLM 
(Friston et al., 1994). We specified separate GLMs based on the specific 
analysis of interest. First GLM: To investigate brain responses to applied 
visuomotor  perturbations  during  adaptation  blocks,  we  constructed  a 
GLM using separate regressors for each block of movement within the 
adaptation  blocks.  This  was  done  at  the  participant  level,  with  each 
regressor consisting of a boxcar function with the onset and duration of 
the  respective  block.  Additionally,  two  further  regressors  were  desig-
nated for the localization trials, one each for the movement and response 
phases, along with a single regressor for error trials that occurred during 
the  localization  events.  Regressors  associated  with  localization  trials 
were not analyzed in this GLM. All regressors were convolved with the 
canonical  hemodynamic  response  function  (HRF).  We  did  not  model 
explicitly  an  additional  rest  phase,  instead,  it  was  captured  by  the 
intercept  for  each  run.  As  part  of  the  nuisance  regression,  motion 

◦

parameters derived from the realignment preprocessing step, their first 
derivatives, the first five components of the signal from white matter 
(WM) and cerebrospinal fluid (CSF) masks, and the instruction messages 
were included. This analysis resulted in one activation beta map for each 
condition  per  participant,  which  was  then  used  in  the  subsequent 
whole-brain  voxel-wise  analyses  or  region  of  interest  (ROI)  analyses 
(refer to ROI analysis section). We then defined contrasts of interest (see 
the results section) using the estimated beta maps at the single-subject 
level  and  conducted  one-sample  t-tests  for  the  group-level  analysis. 
The first contrast aimed to identify brain regions that were active during 
◦
,  blocks  #5–6) 
the  first  rotation  of  the  adaptation  phase  (rotation  5
compared to baseline performance (no rotation, blocks #1–4). Another 
contrast examined the activation differences between the final rotation 
◦
rotation,  blocks  #15–16)  and  the  first 
in  the  adaptation  phase  (30
, blocks #5–6). The resulting group-level activation 
rotation (rotation 5
maps are presented at p < 0.001 (uncorrected) with a minimum cluster 
size of 10 voxels to better visualize the extent of activity. Results that 
were significant after family-wise error correction (FWE) at p < 0.05 are 
also  reported  in  Table  2.  Small  volume  correction  (SVC)  was  applied 
using a mask of the bilateral thalamus with FWE correction at p < 0.05.
Second GLM: To identify brain regions implicated in the recalibra-
tion  of  sensory  prediction  (localization  trials),  we  specified  another 
design matrix to capture the neural response associated with changes in 
hand perception. Within this GLM, we defined two distinct phases of the 
experimental task; one consisted of task conditions related to both the 
baseline and adaptation phases, and the other consisted of the washout 
phase. Accordingly, the experimental blocks spanning from baseline (no 
visual  rotation)  to  adaptation  (visual  rotation)  were  modeled  as  one 
regressor. A similar modeling strategy was employed for the washout 
blocks.  Event-related  localization  trials  were  aggregated  across  the 
baseline and the adaptation phases, and modeled as one regressor. This 
included one regressor for the movement phase, and one regressor for 
the response phase, defined by the onset and duration of each phase. For 
each localization trial, the difference between the estimated hand po-
sition (recorded from the response phase) and the actual crossing point 
of  the  performed  movement  with  the  invisible  circle  was  calculated, 
serving  as  a  metric  of  the  participant’s  perception  of  their  estimated 
hand position. Consequently, a parametric modulator, including hand 
perception on each trial, was added to the regressor of the movement 
phase. The rotation level  at which hand perception was assessed was 
added as an additional parametric modulator. Likewise, event-related 
trials  within the  washout phase  were modeled as  two regressors: one 
for the movement phase with a parametric modulator of hand percep-
tion, and the  other for  the response phase. All task-related  regressors 
were convolved with the HRF and high pass filtered at 128 s prior to 
model estimation. Regressors of no interest consisted of six parameters 
of rigid-body head motion (three translational, three rotational) for each 
run, their first derivatives, the first five principal components derived 
from the CSF mask, the first five principal components derived from the 
WM mask, and events of no interest (i.e., instruction massage). Similar 
to the first GLM, the additional rest phases were not explicitly modeled 
and captured by the intercept for each run. Ultimately, beta activation 
maps for each condition were estimated on the basis of the first-level 
analysis.  We  defined  the  contrast  for  hand  perception  regressor  per 
participant, targeting regions that exhibited increased neural response 
correlating with changes in perception of hand position. The resulting 
contrast  images  were  entered  into  a  second-level  group  analysis  by 
running a one-sample t-test across the group. The statistical maps were 
thresholded at uncorrected p < 0.001 with a minimum cluster size of 10 
voxels. Similar to the previous GLM, we employed SVC using a bilateral 
thalamus mask with FWE correction at p < 0.05.

We  used  the  Julich  brain  atlas  as  implemented  in  the  Anatomy 
Toolbox (Eickhoff et al., 2007), the AAL atlas from SPM, the probabi-
listic  cerebellar  atlas  (Diedrichsen  et  al.,  2009),  and  the  Morel  atlas 
(Krauth et al., 2010; Morel et al., 1997) to anatomically define and label 
activated regions.

6 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

2.7.2. ROI definition

We selected several ROIs in the brain based on prior information and 
our hypothesis regarding the recruitment of these regions during per-
forming and learning a new visuomotor transformation (Hardwick et al., 
2013).  These  ROIs  included  the  left  primary  motor  cortex  (M1),  left 
dorsal premotor cortex (PMd), bilateral superior parietal lobule (SPL), 
bilateral intraparietal sulcus (IPS), right lobule VI of the cerebellum (VI), 
and  right  lobule  VIII  of  the  cerebellum  (VIII).  ROI  coordinates  were 
determined  from  functional  data  acquired  during  the  independent 
functional localizer task (see Localizer section). The localizer task con-
sisted of alternating blocks of hand reaches to the same target position 
(as the main fMRI task) with veridical visual feedback and a rest phase. 
Based on this task condition, we determined the ROI coordinates using 
group  statistics  from  the  second-level  activation  map  (movement  >
rest). Cortical and cerebellar ROIs were defined as spheres with a 4 mm 
radius centered on peak activity from significant voxels (FWE voxel level 
p < 0.05) and labeled based on the Julich Brain Atlas in the Anatomy 
Toolbox (Table 1). For the definition of the SPL ROI, we had to relax our 
statistical  threshold  and  used  a  p  < 0.001  (uncorrected)  threshold  to 
locate the SPL using the suprathreshold voxels.

Thalamic ROIs were delineated using the same group activation map 
derived from the localizer task, with a relaxed statistical threshold of p <
0.001 (uncorrected)  to cover the right thalamic nuclei. These regions 
consisted  of  higher-order  thalamic  nuclei  including  the  left  medial 
pulvinar  nucleus  (PuM)  and  bilateral  medial  dorsal  nuclei  (MD).  In 
addition,  we selected two additional  thalamic nuclei that were previ-
ously  recognized  as  ‘motor’  and  ‘somatosensory’  nuclei  (Prevosto  & 
Sommer,  2013;  Sakai,  2022).  These  included  bilateral  ventral  lateral 
nuclei  (VL)  and  the  left  ventral  posterior  lateral  nucleus  (VPL).  To 
anatomically define the thalamic subregions, we used the Morel Atlas as 
the anatomical reference (Krauth et al., 2010; Morel et al., 1997). The 
digitized version of the Morel atlas is provided in the FSL MNI space, 
which  is  slightly  different  from  the  MNI  space  defined  in  SPM.  We 
aligned the atlas in the SPM MNI space by segmenting the avg FSL152T1 
template image to obtain the deformation field using the segmentation 
tool in SPM, then interpolated the deformation field to 0.5 mm to match 
the Morel atlas resolution. Finally, we used the interpolated deformation 
field to transform the Morel regions. To define the thalamic ROIs, we 
used a cropped version of the Morel Atlas to minimize spatial overlap 
with  adjacent  nuclei.  The  activation  map  was  multiplied  with  the 
thalamic ROIs of interest from the atlas by first transforming the Morel 
regions  into  the  functional  activation  map  space  and  then  extracting 
common  voxels  within  each  ROI  as  a  binary  mask  (Supplementary 
Fig. S1). Table 1 summarizes the center of the masks in MNI space and 
the number of voxels in each ROI. For each predefined ROI, we extracted 

Table 1 
Selected ROIs identified in the fMRI localizer task during hand movements under 
veridical visual feedback.

ROI

Anatomical Label

MNI-coordinates

T-value

Left M1
Left PMd
Left SPL
Right SPL
Left IPS
Right IPS
Right VI
Right VIIIb
Thalamus
Left VL
Left VPL
Left MD
Left PuM
Right VL
Right MD

Primary motor cortex
Dorsal premotor cortex
Superior parietal lobule
Superior parietal lobule
Intraparietal sulcus
Intraparietal sulcus
Cerebellum lobule VI
Cerebellum lobule VIIIb

Ventral lateral nucleus
Ventral posterior lateral
Medial dorsal nucleus
Medial pulvinar
Ventral lateral nucleus
Medial dorsal nucleus

Note. *Voxel size: 2 × 2 × 2 mm3

X

-30
-28
-24
20
-24
32
26
18

-14
-18
-8
-16
14
10

y

-24
-6
-56
-58
-56
-50
-54
-56

-14
-20
-18
-26
-12
-16

z

60
52
60
58
54
48
-24
-50

8
6
8
8
6
8

13
12.1
13.2
12.4
11.3
12.4
14.2
13.2
ROI size (voxels*)
89
43
25
32
75
24

7 

the  beta  weights  from  each  condition  using  the  Region  toolbox  for 
MATLAB/SPM  (https://github.com/DiedrichsenLab/region)  and  aver-
aged them across all voxels within each ROI for each participant.

3. Results

In  our  experiment,  participants  (N  = 30)  performed  a  stepwise 
visuomotor learning task and localization trials during an fMRI imaging 
session (Fig.  1). Specifically, participants underwent a series of adap-
tation blocks, each followed by four localization trials implemented in a 
slow-event-related  design.  This  experimental  design  enabled  us  to 
continuously assess the impact of adaptation learning on changes in the 
predicted  consequences  of  hand  position  following  exposure  to  sys-
tematically  varying  levels  of  feedback  rotation.  In  the  visuomotor 
adaptation  task,  participants  performed  a  rotation  task  by  moving  a 
cursor, which represented their unseen hand’s position, toward a target 
positioned  diagonally.  After  completing 
four  baseline  blocks 
(comprising  60  trials),  the  correspondence  between  the  actual  hand 
position and the cursor was rotated counter-clockwise, with the degree 
◦
of rotation increasing by 5
every two blocks. This gradual increase in 
rotation required participants to adjust their movements clockwise to 
accurately  align  the  cursor  with  the  target.  Following  the  adaptation 
phase, participants performed three blocks of a washout phase, where 
the visual cursor was removed. In the localization task, we evaluated 
whether adaptation to visual rotation led to shifts in hand perception. 
Participants were asked to make a center-out movement in a self-chosen 
direction.  After  a  15  s  fixation  period,  they  reported  the  perceived 
crossing point of their movement trajectory on a circle displayed on the 
screen.

3.1. Behavioral results

3.1.1. Post-Experiment questionnaire

In our post-experiment questionnaire, nine subjects noticed a change 
in the experiment and reported small visual feedback deviations of the 
◦
cursor in the range of 5–10
after the 2 min break and thus only during 
the second half of adaptation. Since in our measures of adaptation, there 
were  no  significant  differences  between  the  subgroup  of  participants 
who were aware of some perturbation and those who remained unaware 
of it, we did not exclude the earlier participants (compare Supplemen-
tary Materials Section S1; also compare Supplementary Figs. S2 and S3, 
in which the respective subjects are presented in red).

3.1.2. Motor adaptation

Behavioral performance associated with the adaptation task is shown 
in  Fig.  2A (compare  Supplementary  Fig.  S2  for  individual  subjects’ 
learning  curves).  To  enhance  visualization,  we  aggregated  learning 
trajectories across blocks as a continuous learning pattern. As expected, 
and  shown  in  Fig.  2A,  participants  adapted  successfully  to  the  visual 
perturbation, thereby reducing their errors by moving the hand in the 
direction opposite to the applied perturbation. As stated in the methods, 
participants performed a set of hand localization trials after each block 
of the experiment. This likely contributed to a reduction in the acquired 
adaptation amount observed at the beginning of each block (labile effect 
– compare discussion). In order to statistically assess the time course of 
adaptation at each step of rotation, we measured the mean hand angles 
for blocks sharing the same rotation size. A one-way repeated measures 
◦
ANOVA with the factor Rotation size (0
) was 
performed on these mean hand angles, revealing a significant main ef-
fect of  Rotation size (F(1.58, 45.74) = 435.87,  partial ƞ2  = 0.93,  p <
0.001). Post-hoc pairwise comparisons confirmed significant adaptation 
at each step of rotation level compared to the preceding size (all p <
0.001, see Supplementary Table 1). Additionally, we quantified the level 
of adaptation per participant by subtracting the mean hand angle during 
◦
the baseline condition (block #4; 0
feedback rotation) from that in the 
final  block  of  adaptation  (block  #16;  30
feedback  rotation),  where 

◦
, 20

◦
, 15

◦
, 25

◦
, 5

, 30

, 10

◦

◦

◦

​
​
​
​
S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

(caption on next page)

8 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

Fig. 2. Behavioral results. (A) Participants’ learning pattern shows the average hand direction in all experimental blocks. Trials from all blocks were aggregated to 
form a continuous learning pattern for visualization. Gray boxes show the main experimental conditions divided into baseline, each of the adaptation blocks, and 
three washout blocks. The x-axis displays the first trial number in every new rotation condition. The dot represents the group average and the shaded area denotes the 
SEM. (B) Shown is the group mean hand perception averaged over each localization trial set (average of four trials). Hand perception was calculated by subtracting 
the reported hand angle from the actual one. The negative value indicates that participants’ predictions shifted in the counterclockwise direction and deviated from 
their actual hand position. The vertical dashed line represents the experimental condition, where hand perception was assessed. (C) Group average movement time. 
Movement time was calculated from the initiation of the movement until the target was crossed. These times were then averaged over each block (15 trials) for 
individual participants and subsequently averaged across the group to derive the group average. (D) Group average reaction time. Reaction time refers to the time 
that has elapsed from positioning the hand in the starting position until movement initiation. It was measured on each trial and averaged over the block for each 
participant and subsequently for the group. For plots (B), (C), and (D) the solid line with circle markers represents the group average and the shaded area represents 
the SEM.

◦

learning approached the final stage. The median deviation in hand angle 
(IQR; 21.8–27.2) and was statistically significant, showing 
was 25.71
that  participants  adjusted  their  hand  trajectories  over  the  course  of 
adaptation (Wilcoxon signed rank test, V = 465, p < 0.001).

To  test  whether  participants  retained  the  adaptation  effect  in  the 
absence  of  learning,  we  measured  the  aftereffect  during  three  blocks 
where cursor feedback was removed. This method has been proven to 
show the degree of sensorimotor recalibration (Galea et al., 2011). As 
can be seen in Fig. 2A, the hand angle at the beginning of the washout 
phase remained in the direction opposite to the imposed rotation in the 
adaptation  phase,  indicating  that  participants  retained  the  adapted 
state.  To  statistically  test  this  aftereffect,  we  conducted  a  one-way 
repeated  measures  ANOVA  on  hand  angles  with  the  main  factor  of 
Phase including the baseline blocks and three washout blocks (F(2.87, 
83.18) = 32.95, partial ƞ2 = 0.53, p < 0.001). Although the magnitude 
of the aftereffect declined across blocks of the washout phase (washout 
block #19 vs. washout block #17; t(29) = 3.85, Padj < 0.001, Cohen’s 
d = 0.58), it remained substantially large for all three blocks compared 
to  the  baseline  (all  adjusted  p-values  < 0.001),  suggesting  that  the 
aftereffect lasted until the last experimental block.

In addition to the primary behavioral measure of adaptation, we also 
analyzed movement time and reaction time as additional learning pa-
rameters. We quantified the movement time for each block per partici-
pant and then averaged it for the group (Fig. 2C&D). To test whether 
participants spent more time executing movements with each adapta-
tion  step,  we  submitted  movement  time,  blocks  grouped  by  rotation 
condition,  to  one-way  repeated  measure  ANOVA  with  the  factor  of 
◦
◦
Rotation  size  (0
).  With  this  analysis,  we 
,  20
aimed to uncover differences that could arise generally in response to 
the  introduction of a new  rotation. There  was no significant  effect of 
Rotation size (F (3.36, 97.47) = 2.53, partial ƞ2  = 0.08, p = 0.055) on 
movement time (see Supplementary Materials Section S2).

◦
,  30

◦
,  25

◦
,  5

,  15

,  10

◦

◦

Next, we evaluated the change in movement time during the washout 
phase. As evident in Fig. 2C, there was a substantial decrease in move-
ment time starting from the first washout block, which remained stable 
through to the end of the experiment. To statistically test this reduction, 
we  conducted  a  one-way  repeated  measure  ANOVA  on  movement 
duration  with  the  main  factor  of  Phase  including  baseline  and  each 
washout block. This analysis revealed a large and significant effect of 
Phase  (F(2.31,  66.86)  = 5.02,  partial  ƞ2  = 0.14,  p  = 0.007).  The 
movement  duration  significantly  decreased  in  all  washout  blocks 
compared to the baseline (all Padj < 0.05), but remained stable across the 
washout  phase  (washout  block  #19  vs.  washout  block  #17;  t(29)  =
0.54, p = 0.6, Cohen’s d = 0.07). Since movements during the washout 
phase were performed without visual feedback to assess the aftereffect, 
it is likely that the reduction in movement duration could be attributed 
to lesser need for sensory integration when executing the movement.

◦

Similarly, we analyzed reaction time to assess whether participants 
responded  differently  across  various  rotation  conditions  (Fig.  2D).  A 
one-way repeated measure ANOVA was performed with Rotation (0
, 
10
) as the main factor on the measured reaction time 
to determine whether reaction times increased with the introduction of 
adaptation and stepwise learning. To do this, we pooled reaction time 
data for each rotation size to focus on distinct conditions. Our findings 

◦
, 20

◦
, 15

◦
, 25

◦
, 30

◦
, 5

◦

indicated no significant main effect of Rotation (F(3.56, 103.2) = 1.31, 
partial ƞ2  = 0.04, p = 0.27; see Supplementary Materials section S3). 
During the washout phase, as can be seen in Fig. 2D, visual inspection of 
the  data suggested  a  decreasing  trend  in reaction  time from the  final 
adaptation step to the initial washout block, which appeared to continue 
to  the  last  washout  block.  However,  a  one-way  repeated  measures 
ANOVA on reaction time data with the main factor of Phase including 
baseline  and  each  washout  block  did  not  show  a  significant  effect  of 
Phase (F(2.44, 70.62) = 0.89, partial η2  = 0.03, p = 0.43; see Supple-
mentary Materials section S4). Taken together, our analyses indicated 
that  participants’  reaction  times  were  not  significantly  impacted  by 
rotation conditions.

3.1.3. Hand localization

By interspersing localization trials after each adaptation block, we 
assessed  whether  and  to  what  extent  training  under  perturbed  visual 
feedback could potentially lead to changes in participants’ predictions 
about the expected visual consequences of their hand movements in the 
absence of visual feedback. We quantified hand perception on each trial 
by  measuring  the  angular  difference  between  actual  hand  movement 
and the reported hand position. Similar to the behavioral results from 
the adaptation blocks, we concatenated the results of localization trials 
from  each  block  into  a  continuous  pattern  for  better  visualization. 
Fig.  2B depicts  the  mean  performance  of  participants  throughout  the 
experiment  (compare  Supplementary  Fig.  S3  for  individual  subjects’ 
hand  perception  per  block).  For  a  visualization  of  the  within-  and 
between-subject variability and spatial distribution of chosen hand di-
rections, refer to Supplementary Fig. S4. The data on hand perception 
showed  a  gradual  shift  from  the  baseline  blocks  as  adaptation  pro-
ceeded. At the beginning of the experiment, when cursor feedback was 
veridical, participants’ perception of the crossing point of the reach was 
close to the actual hand position. However, as a rotation was introduced 
between  the  cursor  position  and  hand  trajectory,  participants’  pre-
dictions of hand movement consequences were shifted in response to the 
new sensorimotor transformation such that the perceived hand position 
was inclined toward the rotated feedback. When we analyzed the hand 
perception  data  using  a  one-way  repeated  measures  ANOVA  with 
◦
◦
Rotation (0
) as a repeated measure, a main 
, 30
effect of Rotation was found (F(2.86, 82.84) = 22.22, partial η2 = 0.43, p 
< 0.001).  Although  there  was  a  slight  gradual  divergence  from  the 
baseline  to  subsequent  blocks,  post-hoc  pairwise  comparisons  only 
revealed significant differences between each pair of consecutive blocks 
starting  from  the  third  step  of  adaptation  (Supplementary  Table  2). 
Moreover, by focusing on the total amount of change in perception until 
the last adaptation step, we found an average change in participants’ 
perception of 11.01 ± 9.56
(mean ± SD). This change was large and 
significant for all participants compared to the baseline (paired t-test; t 
(29) = 6.30, p < 0.001, Cohen’s d = 1.30).

◦
, 15

◦
, 25

◦
, 10

, 20

, 5

◦

◦

◦

After  completing  the  adaptation,  participants  were  tested  for  the 
presence  of  an  aftereffect  during  the  washout  phase.  Similar  to  our 
experimental  design  for  intermittent  localization  trials  within  the 
adaptation  phase,  here,  we  employed  the  same  paradigm  for  the 
washout  phase.  As  depicted  in  Fig.  2B,  hand  perception  followed  a 
reverse direction compared to the adaptation phase. As hand trajectories 

9 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

in  washout  blocks  deviated  to  match  the  target  position  (compare 
Fig. 2A, adaptation pattern), the perception of the hand also shifted in 
the opposite direction to align with the actual movement. To statistically 
assess  the  presence  of  retention  on  hand  perception,  we  conducted  a 
one-way  repeated  measure  ANOVA  on  hand  perception  data  with  a 
factor  of  Condition  (baseline  and  three  separate  washout  blocks).  The 
effect of Condition was significant (F (2.35, 68.04) = 5.17, partial ƞ2 =
0.151,  p  < 0.01).  Despite  a  reduction  in  the  aftereffect  over  time,  a 
significant change in hand perception persisted for the first two washout 
sets compared to baseline (washout block 1 vs. baseline and washout 
block  2  vs.  baseline;  Padj  < 0.01),  underscoring  the  lasting  impact  of 
adaptation on participants’ sensorimotor recalibration.

3.2. Neuroimaging results

3.2.1. Neural correlates of the adaptation phase

To explore the learning-related BOLD response in the initial adap-
tation phase, we first focused on the neural responses to the first intro-
◦
duction  of  perturbed  visual  feedback  (rotation  5
).  This  condition, 
where the discrepancy between hand movement and visual cursor was 
introduced, showed a significant increase in activation in several regions 
compared  to  the  baseline  condition  (unperturbed  visual  feedback; 
compare Table 2 for PFWEc < 0.05). The brain activation map (see Fig. 3; 
Puncorrected  < 0.001)  demonstrates  regions  in  the  frontal  cortex, 
including  the  right  inferior  frontal  gyrus  and  bilateral  middle  frontal 
gyrus. In the parietal lobe, we observed a significant cluster in the left 
intraparietal sulcus and a cluster in the right intraparietal sulcus (note 
that the latter only surfaced for Puncorrected < 0.001; compare Table 2). 
The cerebellar cortex exhibited strong activation in the Crus II on the left 

Table 2 
Whole-brain voxel-wise analysis results.

Anatomical Label

MNI Coordinates

T

X

Y

Z

Cluster Size 
(voxels)

Rotation 5

◦ > Baseline 

(FWEc < 0.05)

R, Inferior frontal gyrus
R, Middle frontal gyrus
L, Cerebellum Crus II
L, Intraparietal sulcus
L, Middle frontal gyrus
Rotation 30

◦
◦ > Rotation 5

(FWEc < 0.05)

R, PMd
L, PMd
L, SPL
R, SPL
L, Thalamus, medial pulvinar*
◦
◦ > Rotation 5
Rotation 10
No suprathreshold clusters
Rotation 15> Rotation 10
No suprathreshold clusters
Rotation 20
B, Inferior occipital gyrus
Rotation 25
No suprathreshold clusters
Rotation 30
No suprathreshold clusters
Hand Perception (uncorrected p <

◦
◦ > Rotation 25

◦
◦ > Rotation 15

◦
◦ > Rotation 20

46
44
-8
-36
-44

26
-14
-4
10
-18

22
12
-78
-52
8

4
4
-58
-62
-28

18
56
-34
42
30

68
72
60
58
8

5.59
5.53
5.10
5.03
4.86

6.22
5.85
5.66
4.76
4.79

579
181
326
217
371

356
615
778
244
22

-38

-84

-10

8.69

534

0.001, k=10)
R, Cerebellum, VIIb
R, Cerebellum, Crus II/ VIIb
B, Thalamus*
R, Posterior cingulate
L, Caudate
L, pallidum
R, Cerebellum, VI
L, Putamen

22
36
-12
10
-16
-22
34
-30

-78
-70
-10
-48
2
-10
-66
-18

-48
-50
10
20
16
0
-24
-2

4.25
4.23
4.18
4.17
4.09
4.06
3.96
3.88

17
35
74
17
14
15
12
10

Note.  *, small  volume  correction for  bilateral  thalamus corrected  at  pFWE <
0.05; R, right; L, left; B, bilateral.

10 

◦ >
Fig. 3. Group average univariate activation map for the contrast rotation 5
baseline (no rotation), thresholded at voxel-wise p < 0.001, uncorrected, with a 
minimum cluster extent of 10 voxels (see Table 2 for a list of significant clusters 
based on p < 0.05 FWE cluster level correction). The statistical analysis shows 
◦
) 
an increase in BOLD response for the introduction of adaptation (rotation 5
compared to movements under no rotation condition (baseline). Increased ac-
tivity  is  found  in  the  posterior  cerebellum,  parietal,  and  frontal  regions.  The 
color  bar  indicates  group-level  T-values.  The  slice  number  on  the  top  left  of 
each  image  indicates  MNI  coordinates  in  the  coronal  view.  IPS,  intraparietal 
sulcus; MFG, middle frontal gyrus.

side and moderate activation in the right hemisphere, with the peak of 
activation in the Crus II extending to lobule VIIb.

As  behavioral  data  indicated  that  participants  continued  showing 
adaptation to each new level of perturbation, we assessed whether there 
were incremental changes in brain activation as the task progressed and 
participants continued to adapt. We tested for evidence of changes in 
brain activation that might suggest the recruitment of more brain re-
gions as adaptation demands increase and participants actively engage 
in the learning process. Alternatively, less activation in some areas could 
indicate more efficient task performance. However, this scenario is less 
likely to occur as a result of habituation since the nature of the experi-
mental task imposes a new adaptation level every two blocks. To test 
these predictions, we compared the BOLD responses between successive 
adaptation  steps.  We  examined  the  differences  in  brain  activation  by 
◦
defining separate contrasts for each rotation step starting at rotation 10
compared to the preceding block (e.g., rotation 10
). The 
results, summarized in Table 2, did not reveal additional recruitment of 
◦
◦ > rotation 5
or rotation 
brain territories for contrasts of rotation 10
◦ > rotation 
◦
◦ > rotation 10
15
. Only, the contrast comparing rotation 20
◦
15
showed a significant cluster of increasing activation in the inferior 
occipital gyrus. Although behaviorally there was a change in hand angle 
introduced  at  each  rotation  level,  GLM  contrasts  between  successive 
adaptation  steps  revealed  no  additional  regions  in  the  fronto-parietal 
cortices or subcortical regions. In fact, the common absence of signifi-
cant changes in brain activation suggests that the same neural processes 
recruited during the first exposure to the visual perturbation remained 
consistently  engaged.  The  activation  increase  in  the  occipital  cortex 
during rotation 20
could mark a shift in increased reliance on visual 
processing  of  the  perturbed  feedback  and  integration  of  the  visual 
feedback with the ongoing acquisition of the new internal model.

◦
◦ > rotation 5

◦

◦

◦
compared to rotation 5

To further examine how accumulated adaptation can be dissociated 
from the initial exposure to the perturbation, we contrasted blocks of 
rotation 30
. In other words, in the stepwise 
adaptation paradigm, the size of the error that participants experience at 
each level is kept small but increases incrementally up to the last level of 
◦
the adaptation condition. Hence, the last adaptation level (rotation 30
) 
incorporates the preceding incremental adjustments that occurred until 
the  end  of  the  adaptation.  This  contrast  could  possibly  elucidate  the 
neural correlates of accumulated adaptation over time as participants 
adjusted to increasing visual feedback discrepancies. Fig. 4 depicts the 
activation  map  (uncorrected  p  < 0.001,  k=10)  for  the  regions  that 

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
S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

perturbation level. To facilitate a group-level analysis, we averaged the 
individual  scores  across  all  participants  to  obtain  a  mean  adaptation 
level  for  each  block.  Using  the  sequence  of  4  baseline  blocks  and  12 
adaptation blocks (comprising six rotation levels, each applied over two 
blocks), we correlated the adaptation level with the mean activity for 
each task block. We sought to examine whether there was a pattern of 
increase or decrease in neural activity as the hand adapted to a newly 
imposed rotation. Our analysis revealed the strongest correlations be-
tween overall change in neural activity and adaptation level for both 
cortical  and  thalamic  regions.  Among  the  fronto-parietal  regions,  left 
SPL, left IPS, and left PMd showed an increase in activity as participants 
adapted to a new perturbation level (all adjusted p-values for multiple 
comparisons < 0.001). However, ROIs in M1 and two cerebellar regions 
did not display this modulation (Fig. 5). In the thalamus, a strong cor-
relation was found for bilateral MD nuclei (Fig. 6, Padj < 0.01). Although 
the ventral lateral nucleus and medial pulvinar showed a similar trend of 
increased activation as the hand adapted, the statistical significance did 
not withstand the correction for multiple comparisons across ROIs. In 
summary,  our  ROI  analysis  identified  overlapping  regions  with  our 
voxel-wise  GLM  analysis  which  exhibited  increased  activity  in  the 
adaptation task.

3.3.1. Cerebello-thalamo-cortical responses modulated by localization trials
Having characterized the neural responses to motor adaptation, we 
next examined the neural basis of the predicted consequences of hand 
movement, aiming to elucidate how adaptation leads to the recalibra-
tion of the forward model. We assessed participants’ predictions of hand 
movements in the absence of an explicit target. As previously described, 
our behavioral data indicated that participants shifted their prediction 
of hand movement consequences in response to every adaptation level. 
To  identify  brain  regions  associated  with  changes  in  perceived  hand 
position, we subtracted the reported angle from the hand angle on each 
trial to derive a unified parameter for hand perception. This parameter 
was  then  convolved  with  a  canonical  HRF  to  construct  a  parametric 
regressor  in  the  GLM  (refer  to  the  methods  section  for  a  detailed 
description).  We  used  trials  from  the  baseline  block  up  to  the  last 
adaptation step to pinpoint regions where neural activity was modulated 
by altered forward model predictions (compare Fig. 2B). We revealed a 
positive  modulation  in  the  left  thalamus,  several  regions  in  the  cere-
bellar cortex, and the basal ganglia (Table 2). Fig. 7A shows brain re-
gions  that  positively  correlated  with  the  parametric  modulator 
(thresholded at uncorrected p < 0.001, k= 10). Within the thalamus, a 
large cluster was identified spanning the left VL nucleus and the left MD 
nucleus,  extending  to  the  right  MD  (Fig.  7B).  Within  the  cerebellum, 
multiple  clusters  surfaced  in  lobules  VI,  VII,  and  Crus  II  of  the  right 
cerebellar hemisphere.

To further explore how brain activity relates to forward model pre-
dictions, we conducted a correlation analysis using independently pre- 
defined  ROIs  (Table  1)  and  the  overall  change  in  hand  perception 
throughout  the  adaptation.  For  each  selected  ROI,  we  extracted  the 
predicted beta from the task modulator regressor (hand perception) and 
averaged  it  for  the  included  voxels.  As  the  measure  of  change  in 
perceived  hand  position,  we  focused  on  two  time  points  within  the 
experiment:  the  average  hand  perception  during  baseline  localization 
trials for a baseline measure and the average during rotation 30
trials 
for the final adaptation state. The change in hand perception, calculated 
as the difference between these two measures for each participant, re-
flected the overall change in hand perception as a result of adaptation. 
The correlation between estimated beta values and the overall change in 
hand perception showed a strong positive relationship for ROIs in the 
cerebellum, thalamus, and motor cortex. To address whether our anal-
ysis  was  affected  by  one  outlier  data  point,  we  re-analyzed  the  data 
excluding the data point in which the change in hand perception was 
greater than 2.5 on the Z-score. We still found the same positive corre-
lation even after correcting for multiple comparisons with the Bonfer-
roni  method  (n=29,  Fig.  8).  Within  M1  and  cerebellum  lobule  VIII, 

◦

◦

◦
) and the first adaptation step (rotation 5

Fig. 4. Difference in evoked activity between the final adaptation step (rotation 
30
). The group level activation map 
in 
shows  the  increased  bold  response  for  contrast  rotation  30
frontal (PMd) and parietal (SPL) regions as well as the thalamus (thresholded at 
p < 0.001, uncorrected, and p < 0.05 FWE cluster level correction, see Table 2
for more details). The color bar indicates group-level T-values. The slice num-
ber on the top left of each image indicates MNI coordinates in the axial view. 
The lower panel shows two slices from the thalamus activation, PuM: the left 
image displays the coronal view, and the right image an axial view. PMd, dorsal 
premotor cortex; SPL, superior parietal lobule; PuM, medial pulvinar.

◦
◦ > rotation  5

showed an increase in neural response. The anatomical locations asso-
ciated with these regions are summarized in Table 2 (PFWEc < 0.05). This 
comparison  revealed  increased  activation  in  the  bilateral  dorsal  pre-
motor cortex, bilateral superior parietal lobule with a small cluster on 
the right side, right cerebellum lobule VIII, and medial pulvinar. We did 
not  observe  increased  or  decreased  activation  in  the  areas  associated 
◦ > baseline contrast, specifically in the cerebellar Crus II 
with rotation 5
and  intraparietal  sulcus.  This  could  be  in  line  with  the  ongoing 
involvement of the aforementioned regions in adaptation.

3.3. ROI analysis

We accompanied our voxel-wise GLM analysis with an ROI analysis 
derived from the localizer task to determine how specific brain regions 
modulated their activity in response to a new adaptation level. In the 
first step, we evaluated whether the average beta estimates from each 
condition within the selected pre-defined ROIs were significant, using 
one-sample  t-tests.  This  step  ensured  that  these  regions  were  actively 
engaged  during  the  task  at  a  group  level.  The  results  of  this  initial 
evaluation are provided in Supplementary Figs. S5 and S6 for all initially 
defined ROIs. Based on these results, we excluded the right SPL and right 
VL  due  to  their  lack  of  consistent  significant  task  activations.  This 
resulted in 12 ROIs for the subsequent regression analysis.

Next,  to  quantify  participants’  reach  performance  throughout  the 
baseline and adaptation blocks, for each participant, we calculated the 
average  angular  deviation  from  the  target  position  for  each  block  of 
trials.  A  positive  value  indicates  the  total  compensation  for  the 

11 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

Fig. 5. Correlation analyses across pre-defined ROIs within cerebellar and cortical regions demonstrate the relationship between brain activity and adapted hand at 
each block including the baseline. The x-axis represents the degree of compensation for each rotation on a group average, while the y-axis shows the group average of 
predicted brain activity. Each point denotes the group average, with 2D error bars displaying the SEM. The solid line illustrates the best linear relationship between 
brain activity and adaptation, with gray shading indicating the 95% confidence interval. Spearman correlation coefficients (r) and uncorrected p-values are pre-
sented. PMd, dorsal premotor cortex; SPL, superior parietal lobule; IPS, intraparietal sulcus; M1, primary motor cortex; VIIIb, cerebellum lobule VIIIb; VI, cerebellum 
lobule VI.

increased brain activation was associated with larger changes in hand 
perception,  a  metric  of  forward  model  recalibration.  This  correlation 
suggests  that  subjects  with  higher  neural  activation  levels  during  the 
localization trials experienced larger change in perceived hand position. 
Interestingly, we found a similar significant correlation for thalamic sub- 
regions,  including  the  left  medial  pulvinar,  left  VL,  and  left  MD. 
Consistent with our voxel-wise GLM analysis, our correlation analysis 
revealed a similar trend within the left ventral lateral nucleus and left 
medial dorsal nucleus, two major regions that jointly formed a cluster in 
the parametric regressor analysis. However, the statistical significance 
of left VL and MD did not meet the criteria after multiple comparisons 
correction (Supplementary Fig. S7).

4. Discussion

4.1. Summary of results

In this study, we investigated the neural correlates associated with 
sensorimotor adaptation and perceived hand position through a visuo-
motor  adaptation  task  adopted  to  an  fMRI  setting.  The  visuomotor 
rotation task served to examine participants’ ability to adjust the rela-
tionship between motor action and perturbed visual feedback, with the 
rotation  being  introduced  incrementally.  Our  behavioral  findings  un-
derscore  the  active  engagement  of  participants  in  the  task  and  show 
significant  adjustments  in  hand  trajectory  to  counteract  the  visual 

12 

perturbations followed by strong aftereffects. Our neuroimaging results 
highlight  the  recruitment  of  distributed  brain  regions,  including  the 
frontal cortex, parietal lobe, cerebellum, and thalamic nuclei at different 
time points of adaptation. Specifically, by focusing on the initiation of 
adaptation,  we  found  that  adaptation  was  characterized  by  increased 
activation  in  the  cerebellum,  parietal  lobe,  and  frontal  regions.  In 
addition,  we  found  that  as  participants’  adaptation  accounted  for 
increasing levels of feedback rotation, the parietal lobe, premotor cor-
tex, and thalamus exhibited an enhanced BOLD response. Notably, our 
analysis revealed that parietal regions (IPS, SPL), the premotor cortex, 
and bilateral MD nuclei increased their level of activation with the de-
gree of motor adaptation.

Importantly, using participants’ behavioral reports on the expected 
visual movement consequences, we identified brain regions associated 
with changes in hand perception. We found that recalibration of these 
estimates  led  to  an  increase  in  neural  responses,  recruiting  multiple 
regions  of  the  cerebellum,  thalamus,  and  motor  cortex.  Additionally, 
further  ROI  analyses  showed  that  these  changes  were  related  to 
behavioral outcomes, such that an increase in activation level was linked 
to a larger change in perception.

4.2. Whole brain analysis of the adaptation

Our neuroimaging results from the motor adaptation process suggest 
that  adaptation  to  visual  discrepancy  between  the  hand  and  cursor 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

Fig.  6. Correlation  analyses  within  thalamic  nuclei,  demonstrating  the  relationship  between  thalamic  activity  and  hand  adaptation  across  all  blocks,  including 
baseline. The display conventions follow the same format as shown in Fig. 5. Within thalamic sub-regions, bilateral MD showed the strongest correlation between 
adaptation level and increased neural response. MD, medial dorsal nucleus; VL, ventral lateral nucleus; PuM, medial pulvinar.

◦

resulted in increased activation in the bilateral posterior 
position by 5
cerebellum  mainly  Crus  II  and  lobule  VII,  intraparietal  sulcus,  and 
frontal regions. Previous neuroimaging studies have consistently shown 
dynamic  changes  in  brain  activation  associated  with  sensorimotor 
adaptation,  reporting  increases  and  decreases  in  neural  activity 
depending on the stage of adaptation (Graydon et al., 2005; Krakauer 
et al., 2004; Nezafat et al., 2001; Seidler & Noll, 2008; Tzvi et al., 2020). 
The activation patterns observed in our study align with previous studies 
showing  greater  activation  during  the  early  phase  of  learning,  when 
participants were establishing the acquisition of adaptation, namely in 
the cerebellum (Floyer-Lea & Matthews, 2004; Ruitenberg et al., 2018; 
Tzvi et al., 2020), parietal lobe (B´edard & Sanes, 2014; Tzvi et al., 2020), 
and frontal lobe (Ruitenberg et al., 2018; Tzvi et al., 2020). Decreasing 
activity within the cerebellum has been associated with the automaticity 
of adaptation during later stages of learning (Floyer-Lea &  Matthews, 
2004; Tzvi et al., 2020). However, we did not observe changes in the 
activity  of  the  cerebellum  in  our  pairwise  comparisons  of  adaptation 
steps. One explanation for this discrepancy might stem from methodo-
logical differences in studying adaptation, which make the direct com-
parison of our findings with those studies difficult. In contrast to abrupt 

adaptation  paradigms  employed  by  these  earlier  studies,  typically 
engaging both implicit as well as explicit modes of adaptation (Taylor 
et  al.,  2014;  Taylor  &  Ivry,  2014),  our  study  applied  only  minor  ad-
justments of feedback rotation, which were increased in multiple small 
steps that were hardly noticeable. As a result, participants in our task 
were perhaps more readily resorting to an implicit recalibration of their 
internal models. A more direct comparison of results can be done when 
considering a study in which the adaptation was also imposed gradually 
◦
by 2
rotation (Werner et al., 2014). 
Contrasting  adaptation  to  the  baseline,  this  study  revealed  increased 
activity  in  the  left  cerebellum  and  frontal  lobe,  similar  to  what  we 
observed here. The activations in the frontal lobe (Inferior and middle 
frontal gyri) could thereby be associated with spatial working memory 
during  visuomotor  adaptation  (Anguera  et  al.,  2010)  and  with  faster 
adaptation (Ruitenberg et al., 2018).

◦
every 15 trials until reaching 60

Our  investigation  of  the  neural  correlates  of  increasing  levels  of 
◦
feedback  rotation,  namely  by  contrasting  rotations  of  30
, 
revealed increased activation in a different set of areas, namely within 
the bilateral dorsal premotor cortex, bilateral superior parietal lobule, 
and left medial pulvinar as adaptation advanced. What could be the role 

◦
and  5

13 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

Krakauer, 2008).

4.3. Thalamus recruitment during the adaptation

◦
and 5

In addition to cerebellum and cortical regions recruited during the 
visuomotor adaptation, our findings revealed increased activity within 
thalamic sub-regions at different times of adaptation. Specifically, we 
found a significant activation increase within the bilateral medial dorsal 
nuclei that positively correlated with the adapted state of hand position. 
Additionally, as discussed in the previous section, contrasting the rota-
◦
revealed that the level of activation in the medial pul-
tion 30
vinar was modulated by the degree of rotation. Thalamus activity has 
been reported in previous neuroimaging studies of motor learning with 
increased activation during consolidation phase (Graydon et al., 2005), 
decreased activation in transfer of learning (Seidler, 2010), and corre-
lation with faster learning during early  adaptation (Ruitenberg et  al., 
2018). However, the main focus of these studies has been on the cortical 
and cerebellar involvement in motor learning and the exact functional 
role  of  the  thalamus  has  remained  elusive.  Our  findings  regarding 
bilateral MD nuclei align with its anatomical connection with the cer-
ebellum and premotor cortex. The cerebellar ascending projection to the 
thalamus targets the lateral MD (Sakai, 2022), which in turn projects to 
the  dorsal premotor  cortex (Prevosto  &  Sommer, 2013;  Sakai,  2022). 
Structural connectivity studies of the cerebellar dentate nucleus as the 
major output of cerebellum to thalamus have delineated a bilateral tract 
with non-decussating tract to target medial thalamus (Petersen et al., 
2018). Through the lens of anatomical communication of MD with both 
cerebellum and prefrontal cortex, increased activation in MD and PMd 
with adaptation may reflect a distributed thalamo-cortical network that 
facilitates the adaptation. What we cannot determine with our results is 
that the observed pattern is a direct result of learning-induced changes 
due to an updated internal model that are mediated by the cerebellum or 
represents  more  cognitive  aspects  of  motor  adaptation  (e.g.,  strategic 
motor  planning)  through  its  reciprocal  connectivity  with  premotor 
cortex (top down cortical connectivity).

4.4. Change in perceived hand movement

When  training  under  altered  visual  feedback,  the  discrepancy  be-
tween the predicted outcome of an action, derived from the efference 
copy, and the actual sensory information is leveraged to improve per-
formance  (Wolpert  et  al.,  1995).  Through  such  training,  these  pre-
dictions  become  recalibrated,  which  in  turn  updates  the  motor 
command  generator  and  leads  to  adaptation  (Krakauer  et  al.,  2019; 
Shadmehr,  2017).  To  understand  how  the  predicted  sensory  conse-
quence of movement is recalibrated, previous studies have behaviorally 
measured hand localization in the absence of other sensory cues before 
and after adaptation (Izawa et al., 2012; ‘t Hart & Henriques, 2016). In 
this study, we employed a similar task to assess how hand perception 
changes as participants adapt to visually altered feedback. Our findings 
revealed that the cerebellum, thalamus, and motor cortex showed in-
creases in overall activation as a result of prediction-based recalibration 
of hand movement estimation. Furthermore, BOLD activity within the 
cerebellum, thalamus, and motor cortex was correlated with the total 
amount of change in perception. Studies involving patients with cere-
bellar damage have shown impairments in accurately localizing hand 
position compared to a control group (Izawa et al., 2012; Synofzik et al., 
2008) and learning from sensory prediction error (Butcher et al., 2017; 
Taylor et al., 2010). Our findings regarding cerebellar involvement in 
forward  model  recalibration  corroborate  the  previous  studies.  More 
specifically, if sensory prediction error during adaptation drives adap-
tive responses to control the visual cursor in the intended direction, the 
motor  commands  need  to  be  adjusted  to  generate  a  command  that 
matches the sensory consequences (Shadmehr, 2017). A pattern that we 
observed in our correlation analysis supports this process. The greater 
the change in perception by the participants, the more activation was 

Fig. 7. Brain regions positively associated with hand perception. (A) Result of 
whole brain voxel-wise GLM analysis with a parametric regressor modulating 
the hand perception for trials spanning the baseline through the final adapta-
tion phase. The activation map was thresholded at p < 0.001 with a minimum 
cluster extent of 10 voxels. The hand perception was modulated by activities in 
the right cerebellum, thalamus, and basal ganglia. (B) The lower panel displays 
two slices illustrating a zoomed view of thalamic activity: the left image dis-
plays a coronal view, and the right image is an axial view. Overlays on these 
slices demarcate thalamic sub-regions according to the Morel Atlas. The activity 
within the thalamus encompasses the left VL and MD. The color bar indicates 
group-level T-values. The slice number in the top left of each image indicates 
MNI  coordinates.  Abbreviations:  PUT,  putamen;  GP,  globus  pallidus;  CN, 
caudate nucleus; MD, medial dorsal nucleus; VL, ventral lateral nucleus.

of these areas in adaptation? A recent study has shown that the explicit 
component  of  adaptation  can  be  suppressed  in  gradual  adaptation 
compared  to  abrupt  adaptation  (Yin  &  Wei,  2020),  but  scales  within 
gradual adaptation such that with increasing rotation size both explicit 
and  implicit  components  increase  (Albert  et  al.,  2022).  Hence,  we 
cannot  rule  out  that  the  performance  remains  completely  implicit.  A 
contribution  of  explicit  adaptation  is  indirectly  suggested  by  the  fact 
that the size of the aftereffect (a measure of sensorimotor recalibration) 
and the perceptual change in localization trials account only partially for 
the  total  performance  by  the  end  of  adaptation.  This  is  likewise  sug-
gested by the presence of a labile component of motor adaptation at the 
onset of each block (Fig. 2A), which occurred due to interleaved local-
ization trials without feedback. Importantly, this labile effect becomes 
increasingly pronounced in later phases of the adaptation phase. It has 
been  previously  suggested  that  this  temporarily  labile  component  of 
adaptation  corresponds  to  explicit  learning  (Krakauer  et  al.,  2019; 
Morehead  &  Orban  de  Xivry,  2021).  It  thus  seems  possible  that  the 
increased  activation  in  the  aforementioned  areas  is  also  due  to  the 
increased weight of explicit learning, reflecting strategic motor planning 
in PMd and SPL. The overall activity in these areas might also refer to the 
integration of the forward model and sensory information. If the sensory 
information (in visual space) does not match the predicted state of the 
forward model due to both the decay of adaptation seen at the beginning 
of the block and the novel applied rotation, the forward model should 
integrate the new sensory information with its prediction (Shadmehr & 

14 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

Fig. 8. Brain activity in the motor cortex, cerebellum, and medial pulvinar correlates with the overall perception change. The y-axis denotes the extracted beta values 
from the parametric regressor modulating the hand perception during the baseline and adaptation phase for pre-defined ROIs. The x-axis denotes the changes in hand 
perception, calculated as the difference between hand perception during the baseline blocks and the last adaptation phase (rotation 30
). Positive values reflect the 
degree of change in perception. Each data point represents an individual participant. The solid line represents the line of best fit, with gray shading indicating the 
95% confidence interval. Correlation coefficients (R) and p values are presented. M1, primary motor cortex; PuM, medial pulvinar. For an analogous figure using 
other ROIs, see Supplementary Fig. S7.

◦

observed in M1, possibly indicating an updated efference copy as a result 
of adaptation. Although, to our knowledge, there are no imaging and 
behavioral  studies specifically assessing  hand localization in  the thal-
amus, the patient study by Chen et al. (2006) has provided evidence that 
cerebellar projections to the thalamus influence motor learning in force 
field  adaptation.  However,  it  remains  unclear  to  what  extent  the 
impairment in adaptation affected updating the predicted consequences 
of hand movement or if other learning deficits hindered full adaptation. 
Here, we demonstrated through an fMRI analysis that subregions of the 
thalamus, including medial nuclei (MD), VL, and medial pulvinar might 
facilitate learning by providing an updated forward model. Within this 
framework and as discussed previously, the VL and MD as well-known 
cerebellar  recipients  of  the  thalamus  might  provide  an  efficient 
pathway with their reciprocal connectivity to motor cortical regions to 
update the inverse internal model. Notably, our ROI analysis revealed a 
positive  correlation  between  the  activity  of  the  medial  pulvinar  and 

changes in hand perception. However, this pattern of modulation was 
not observed in our GLM analysis that captured the incremental changes 
in hand perception. While this finding does not directly establish a role 
of the medial pulvinar in updating of the forward model, it suggests a 
functional  role  in  this  mechanism,  e.g.  by  providing  a  transthalamic 
route  for  direct  cortico-cortical  communication  through  its  reciprocal 
connectivity  with  fronto-parietal  cortices  (Kastner  et  al.,  2020).  The 
positive  correlation  may  reflect  maintaining  the  ultimate  updated 
adaptation, which has been linked to the function of the posterior pa-
rietal cortex (Della-Maggiore et al., 2004; Krakauer et al., 2004; Shad-
mehr & Krakauer, 2008).

Finally, we would like to stress that the adaptation of perceived hand 
localization to a visuomotor perturbation involves distinct but concur-
rent  processes  that  include  the  recalibration  of  both  efference  copy- 
based sensory predictions and proprioceptive recalibration due to the 
additional  visual-proprioceptive  mismatch  (Cressman  &  Henriques, 

15 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

2009; Rossi et al., 2021). This has, for instance, been demonstrated by 
decoupling these components using passive localization (proprioceptive 
estimate of hand position) and active localization (proprioceptive and 
sensory  prediction),  with  the  difference  reflecting  the  shift  in 
efference-based  predictions  (‘t  Hart  &  Henriques,  2016).  It  remains 
unclear  whether  the  recalibration  of  efference-based  predictions  and 
proprioceptive recalibration rely on the same neural network, operate 
through  distinct  networks,  or  engage  a  combination  of  both  mecha-
nisms. For instance, active reaching studies of cerebellar patients have 
shown significant mislocalization of hand position following adaptation 
(Block & Bastian, 2012; Izawa et al., 2012; Synofzik et al., 2008), while 
proprioceptive  recalibration  after  motor  adaptation  and  exposure 
training seemingly remained intact (Block & Bastian, 2012; Henriques 
et al., 2014). This suggests that proprioceptive recalibration likely relies 
on a network outside the cerebellum. Localization trials in our experi-
ment  consisted  of  self-generated  fast  out-and-back  movements;  thus, 
sensory  afferents  (muscle  spindles,  Golgi  tendons,  etc.)  were  not 
completely eliminated. Importantly, to mitigate its compounding effect, 
participants were instructed to return the hand back to the home posi-
tion after movement completion. Hence, the directional estimate could 
at least not be influenced by any static proprioceptive information that 
could  be  collected  in  studies  where  the  hand  was  residing  at  the 
endpoint  of  the  outbound  reach  while  subjects  estimated  their  hand 
localization  (Cressman  &  Henriques,  2009;  Henriques  et  al.,  2014). 
Furthermore,  we  would  like  to  point  out  that  for  our  estimate  of 
perceived hand position, subjects in any case (both for proprioception 
and  efference  copy)  had  to  “predict”  the  visual  consequence  of  their 
movement  based  on  an  “internal”  movement-related  signal.  Future 
research could investigate correlated neural activity by independently 
assessing efferent and afferent perceptual changes alongside concurrent 
motor adjustments.

4.5. Conclusion

In  conclusion,  we  present  neural  changes  observed  during  visuo-
motor adaptation and its impact on hand position estimation. To the best 
of our knowledge, this is the first investigation of stepwise adaptation 
and  continuous  assessment  of  predicted  hand  position  as  a  proxy  for 
implicit motor learning using fMRI. We found that adaptation to small 
incremental  errors  elicited  activation  in  the  cerebellum,  parietal,  and 
frontal lobes. Moreover, the change in hand state estimation recruited a 
network comprising the cerebellum, thalamus (including classical motor 
but  also  ‘higher-order’  nuclei  such  as  MD  and  pulvinar),  and  motor 
cortex. The overall change in hand perception, as a result of recalibra-
tion of the forward model, was associated with increased brain activity 
in  the  left  medial  pulvinar,  left  motor  cortex,  and  right  cerebellum. 
These  results  provide  fMRI  evidence  for  the  thalamic  contribution 
beyond the classical ‘motor thalamus’ to motor learning and offer a basis 
for future research to better understand how the thalamus interacts with 
the rest of the brain to facilitate the optimization of behavior.

Data and code availability statement

Data and Code are available on request.

Funding

This  research  was  supported  by  the  Hermann  and  Lilly  Schilling 

Foundation and the Volkswagen Foundation (to M.W.).

CRediT authorship contribution statement

Shirin  Mahdavi:  Writing  –  review  &  editing,  Writing  –  original 
draft,  Visualization,  Software,  Methodology,  Investigation,  Formal 
analysis, Conceptualization. Axel Lindner: Writing – review & editing, 
Methodology,  Conceptualization.  Carsten  Schmidt-Samoa:  Writing  – 

16 

review  &  editing,  Methodology.  Anna-Lena  Müsch:  Investigation, 
Formal analysis. Peter Dechent: Writing – review &  editing, Method-
ology. Melanie Wilke: Writing – review & editing, Supervision, Project 
administration, Methodology, Funding acquisition, Conceptualization.

Declaration of competing interest

The  authors  declare  no  competing  financial  or  non-financial 

interests.

Acknowledgments

We  thank  Kristin  K¨otz  and  Britta  Perl  for  assistance  with  neuro-
imaging data collection; Severin Heumüller for providing IT support and 
resolving technical issues throughout the study. We thank Mitra Azhdari 
for the illustration of the experimental setup. We thank Igor Kagan and 
Alexander Gail for helpful discussions.

Supplementary materials

Supplementary material associated with this article can be found, in 

the online version, at doi:10.1016/j.neuroimage.2024.120927.

Data availability

Data will be made available on request. 

References

Albert, S.T., Jang, J., Modchalingam, S., ’T Hart, B.M., Henriques, D., Lerner, G., Della- 
Maggiore, V., Haith, A.M., Krakauer, J.W., Shadmehr, R., 2022. Competition 
between parallel sensorimotor learning systems. Elife 11, e65361. https://doi.org/ 
10.7554/eLife.65361.

Andersson, J.L.R., Skare, S., Ashburner, J., 2003. How to correct susceptibility 

distortions in spin-echo echo-planar images: Application to diffusion tensor imaging. 
Neuroimage 20 (2), 870–888. https://doi.org/10.1016/S1053-8119(03)00336-7.
Anguera, J.A., Reuter-Lorenz, P.A., Willingham, D.T., Seidler, R.D., 2010. Contributions 
of Spatial Working Memory to Visuomotor Learning. J. Cogn. Neurosci. 22 (9), 
1917–1930. https://doi.org/10.1162/jocn.2009.21351.

Arcaro, M.J., Pinsk, M.A., Chen, J., Kastner, S., 2018. Organizing principles of pulvino- 
cortical functional coupling in humans. Nat. Commun. 9 (1), 5382. https://doi.org/ 
10.1038/s41467-018-07725-6.

B´edard, P., Sanes, J.N., 2014. Brain representations for acquiring and recalling 

visual–motor adaptations. Neuroimage 101, 225–235. https://doi.org/10.1016/j. 
neuroimage.2014.07.009.

Behzadi, Y., Restom, K., Liau, J., Liu, T.T., 2007. A component based noise correction 

method (CompCor) for BOLD and perfusion based fMRI. Neuroimage 37 (1), 90–101. 
https://doi.org/10.1016/j.neuroimage.2007.04.042.

Benson, B.L., Anguera, J.A., Seidler, R.D., 2011. A spatial explicit strategy reduces error 
but interferes with sensorimotor adaptation. J. Neurophysiol. 105 (6), 2843–2851. 
https://doi.org/10.1152/jn.00002.2011.

Block, H.J., Bastian, A.J., 2012. Cerebellar involvement in motor but not sensory 
adaptation. Neuropsychologia 50 (8), 1766–1775. https://doi.org/10.1016/j. 
neuropsychologia.2012.03.034.

Brainard, D.H., 1997. The psychophysics toolbox. Spat. Vis. 10 (4), 433–436. https://doi. 

org/10.1163/156856897X00357.

Butcher, P.A., Ivry, R.B., Kuo, S.H., Rydz, D., Krakauer, J.W., Taylor, J.A., 2017. The 

cerebellum does more than sensory prediction error-based learning in sensorimotor 
adaptation tasks. J. Neurophysiol. 118 (3), 1622–1636. https://doi.org/10.1152/ 
jn.00451.2017.

Chai, X.J., Casta˜n´on, A.N., 

¨
Ongür, D., Whitfield-Gabrieli, S., 2012. Anticorrelations in 

resting state networks without global signal regression. Neuroimage 59 (2), 
1420–1428. https://doi.org/10.1016/j.neuroimage.2011.08.048.

Chen, H., Hua, S.E., Smith, M.A., Lenz, F.A., Shadmehr, R., 2006. Effects of human 

cerebellar thalamus disruption on adaptive control of reaching. Cereb. Cortex 16 
(10), 1462–1473. https://doi.org/10.1093/cercor/bhj087.

Cressman, E.K., Henriques, D.Y.P., 2009. Sensory recalibration of hand position 

following visuomotor adaptation. J. Neurophysiol. 102 (6), 3505–3518. https://doi. 
org/10.1152/jn.00514.2009.

Della-Maggiore, V., Malfait, N., Ostry, D.J., Paus, T., 2004. Stimulation of the posterior 
parietal cortex interferes with arm trajectory adjustments during the learning of new 
dynamics. J. Neurosci. 24 (44), 9971–9976. https://doi.org/10.1523/ 
JNEUROSCI.2833-04.2004.

Diedrichsen, J., Balsters, J.H., Flavell, J., Cussans, E., Ramnani, N., 2009. A probabilistic 
MR atlas of the human cerebellum. Neuroimage 46 (1), 39–46. https://doi.org/ 
10.1016/j.neuroimage.2009.01.045.

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

Eickhoff, S.B., Paus, T., Caspers, S., Grosbras, M.H., Evans, A.C., Zilles, K., Amunts, K., 
2007. Assignment of functional activations to probabilistic cytoarchitectonic areas 
revisited. Neuroimage 36 (3), 511–521. https://doi.org/10.1016/j. 
neuroimage.2007.03.060.

Floyer-Lea, A., Matthews, P.M., 2004. Changing brain networks for visuomotor control 
with increased movement automaticity. J. Neurophysiol. 92 (4), 2405–2412. 
https://doi.org/10.1152/jn.01092.2003.

Friston, K.J., Holmes, A.P., Worsley, K.J., Poline, J.-P., Frith, C.D., Frackowiak, R.S.J., 

1994. Statistical parametric maps in functional imaging: A general linear approach. 
Hum. Brain Mapp. 2 (4), 189–210. https://doi.org/10.1002/hbm.460020402.
Froesel, M., Cappe, C., Ben Hamed, S., 2021. A multisensory perspective onto primate 
pulvinar functions. Neurosci. Biobehav. Rev. 125, 231–243. https://doi.org/ 
10.1016/j.neubiorev.2021.02.043.

Galea, J.M., Vazquez, A., Pasricha, N., Orban de Xivry, J.J., Celnik, P., 2011. Dissociating 

the roles of the cerebellum and motor cortex during adaptive learning: the motor 
cortex retains what the cerebellum learns. Cereb. Cortex 21 (8), 1761–1770. https:// 
doi.org/10.1093/cercor/bhq246.

Graydon, F.X., Friston, K.J., Thomas, C.G., Brooks, V.B., Menon, R.S., 2005. Learning- 

related fMRI activation associated with a rotational visuo-motor transformation. 
Cogn. Brain Res. 22 (3), 373–383. https://doi.org/10.1016/j. 
cogbrainres.2004.09.007.

Hardwick, R.M., Rottschy, C., Miall, R.C., Eickhoff, S.B., 2013. A quantitative meta- 

analysis and review of motor learning in the human brain. Neuroimage 67, 283–297. 
https://doi.org/10.1016/j.neuroimage.2012.11.020.

Henriques, D.Y.P., Filippopulos, F., Straube, A., Eggert, T., 2014. The cerebellum is not 

necessary for visually driven recalibration of hand proprioception. 
Neuropsychologia 64, 195–204. https://doi.org/10.1016/j. 
neuropsychologia.2014.09.029.

Hwang, K., Bertolero, M.A., Liu, W.B., D’Esposito, M., 2017. The human thalamus is an 
integrative hub for functional brain networks. J. Neurosci. 37 (23), 5594–5607. 
https://doi.org/10.1523/JNEUROSCI.0067-17.2017.

Izawa, J., Criscimagna-Hemminger, S.E., Shadmehr, R., 2012. Cerebellar contributions to 
reach adaptation and learning sensory consequences of action. J. Neurosci. 32 (12), 
4230–4239. https://doi.org/10.1523/JNEUROSCI.6353-11.2012.

Jenkinson, M., Beckmann, C.F., Behrens, T.E.J., Woolrich, M.W., Smith, S.M., 2012. FSL. 

Neuroimage 62 (2), 782–790. https://doi.org/10.1016/j.neuroimage.2011.09.015.

Kagerer, F.A., Contreras-Vidal, J.L., Stelmach, G.E., 1997. Adaptation to gradual as 

compared with sudden visuo-motor distortions. Exp. Brain Res. 115 (3), 557–561. 
https://doi.org/10.1007/PL00005727.

Kassambara A. (2023a). ggpubr: “ggplot2” Based Publication Ready Plots [Computer 

software]. https://CRAN.R-project.org/package=ggpubr.

Kassambara A. (2023b). rstatix: Pipe-Friendly Framework for Basic Statistical Tests 

[Computer software]. https://CRAN.Rproject.org/package=rstatix.

Kastner, S., Fiebelkorn, I.C., Eradath, M.K., 2020. Dynamic pulvino-cortical interactions 
in the primate attention network. Curr. Opin. Neurobiol. 65, 10–19. https://doi.org/ 
10.1016/j.conb.2020.08.002.

Kim, H.E., Avraham, G., Ivry, R.B., 2021. The psychology of reaching: action selection, 
movement implementation, and sensorimotor learning. Annu. Rev. Psychol. 72 (1), 
61–95. https://doi.org/10.1146/annurev-psych-010419-051053.

Krakauer, J.W., Ghilardi, M.F., Mentis, M., Barnes, A., Veytsman, M., Eidelberg, D., 

Ghez, C., 2004. Differential cortical and subcortical activations in learning rotations 
and gains for reaching: A PET study. J. Neurophysiol. 91 (2), 924–933. https://doi. 
org/10.1152/jn.00675.2003.

Krakauer J.W., Hadjiosif A.M., Xu J., Wong A.L., & Haith A.M. (2019). Motor learning. In 
R. Terjung (Ed.), Comprehensive Physiology (1st ed., pp. 613–663). Wiley. 10.1 
002/cphy.c170043.

Krauth, A., Blanc, R., Poveda, A., Jeanmonod, D., Morel, A., Sz´ekely, G., 2010. A mean 

three-dimensional atlas of the human thalamus: Generation from multiple 
histological data. Neuroimage 49 (3), 2053–2062. https://doi.org/10.1016/j. 
neuroimage.2009.10.042.

Kumar, V.J., Beckmann, C.F., Scheffler, K., Grodd, W., 2022. Relay and higher-order 

thalamic nuclei show an intertwined functional association with cortical-networks. 
Commun. Biol. 5 (1), 1187. https://doi.org/10.1038/s42003-022-04126-w.
Miall, R.C., Wolpert, D.M., 1996. Forward models for physiological motor control. 

Neural Netw. 9 (8), 1265–1279. https://doi.org/10.1016/S0893-6080(96)00035-4.
Modchalingam, S., Ciccone, M., D’Amario, S., ’T Hart, B.M., Henriques, D.Y.P., 2023. 
Adapting to visuomotor rotations in stepped increments increases implicit motor 
learning. Sci. Rep. 13 (1), 5022. https://doi.org/10.1038/s41598-023-32068-8.
Moeller, S., Pisharady, P.K., Ramanna, S., Lenglet, C., Wu, X., Dowdle, L., Yacoub, E., 
U˘gurbil, K., Akçakaya, M., 2021. Noise reduction with distribution corrected 
(NORDIC) PCA in dMRI with complex-valued parameter-free locally low-rank 
processing. Neuroimage 226, 117539. https://doi.org/10.1016/j. 
neuroimage.2020.117539.

Nezafat, R., Shadmehr, R., Holcomb, H., 2001. Long-term adaptation to dynamics of 

reaching movements: A PET study. Exp. Brain Res. 140 (1), 66–76. https://doi.org/ 
10.1007/s002210100787.

Nieto-Castanon, A., 2020. Handbook of Functional Connectivity Magnetic Resonance 

Imaging methods in CONN. Hilbert Press. https://doi.org/10.56441/ 
hilbertpress.2207.6598.

Nieto-Castanon, A., Whitfield-Gabrieli, S., 2022. CONN Functional Connectivity toolbox: 

RRID SCR_009550, Release 22. Hilbert Press. https://doi.org/10.56441/ 
hilbertpress.2246.5840, 22nd ed. 

Oldfield, R.C., 1971. The assessment and analysis of handedness: the Edinburgh 

inventory. Neuropsychologia 9 (1), 97–113. https://doi.org/10.1016/0028-3932 
(71)90067-4.

Passarelli, L., Gamberini, M., Fattori, P., 2021. The superior parietal lobule of primates: A 
sensory-motor hub for interaction with the environment. J. Integr. Neurosci. 20 (1), 
157. https://doi.org/10.31083/j.jin.2021.01.334.

Petersen, K.J., Reid, J.A., Chakravorti, S., Juttukonda, M.R., Franco, G., Trujillo, P., 
Stark, A.J., Dawant, B.M., Donahue, M.J., Claassen, D.O., 2018. Structural and 
functional connectivity of the nondecussating dentato-rubro-thalamic tract. 
Neuroimage 176, 364–371. https://doi.org/10.1016/j.neuroimage.2018.04.074.
Prevosto, V., Sommer, M.A., 2013. Cognitive control of movement via the cerebellar- 

recipient thalamus. Front. Syst. Neurosci. 7. https://doi.org/10.3389/ 
fnsys.2013.00056.

R Core Team, R. C. T, 2023. R: A Language and Environment for Statistical Computing 
[Computer Software]. R Foundation for Statistical Computing. https://www.R-pro 
ject.org/.

Rossi, C., Bastian, A.J., Therrien, A.S., 2021. Mechanisms of proprioceptive realignment 
in human motor learning. Curr. Opin. Physiol. 20, 186–197. https://doi.org/ 
10.1016/j.cophys.2021.01.011.

Roth, M.M., Dahmen, J.C., Muir, D.R., Imhof, F., Martini, F.J., Hofer, S.B., 2016. 

Thalamic nuclei convey diverse contextual information to layer 1 of visual cortex. 
Nat. Neurosci. 19 (2), 299–307. https://doi.org/10.1038/nn.4197.

Ruitenberg, M.F.L., Koppelmans, V., De Dios, Y.E., Gadd, N.E., Wood, S.J., Reuter- 

Lorenz, P.A., Kofman, I., Bloomberg, J.J., Mulavara, A.P., Seidler, R.D., 2018. Neural 
correlates of multi-day learning and savings in sensorimotor adaptation. Sci. Rep. 8 
(1), 14286. https://doi.org/10.1038/s41598-018-32689-4.

Sakai, S.T., 2022. Cerebellar thalamic and thalamocortical projections. Eds.. In: 

Manto, M.U., Gruol, D.L., Schmahmann, J.D., Koibuchi, N., Sillitoe, R.V. (Eds.), 
Handbook of the Cerebellum and Cerebellar Disorders. Springer International 
Publishing, pp. 661–680. https://doi.org/10.1007/978-3-030-23810-0_24.

Schaefer, S.Y., Haaland, K.Y., Sainburg, R.L., 2009. Dissociation of initial trajectory and 
final position errors during visuomotor adaptation following unilateral stroke. Brain 
Res. 1298, 78–91. https://doi.org/10.1016/j.brainres.2009.08.063.

Schauberger P., & Walker A. (2023). Openxlsx: read, write and edit xlsx files (Version 
4.2.5.2) [Computer software]. https://CRAN.Rproject.org/package=openxlsx.
Seidler, R.D., 2010. Neural correlates of motor learning, transfer of learning, and 
learning to learn. Exerc. Sport Sci. Rev. 38 (1), 3–9. https://doi.org/10.1097/ 
JES.0b013e3181c5cce7.

Seidler, R.D., Noll, D.C., 2008. Neuroanatomical correlates of motor acquisition and 
motor transfer. J. Neurophysiol. 99 (4), 1836–1845. https://doi.org/10.1152/ 
jn.01187.2007.

Shadmehr, R., 2017. Learning to predict and control the physics of our movements. 
J. Neurosci. 37 (7), 1663–1671. https://doi.org/10.1523/JNEUROSCI.1675- 
16.2016.

Shadmehr, R., Holcomb, H.H., 1997. Neural correlates of motor memory consolidation. 
Science 277 (5327), 821–825. https://doi.org/10.1126/science.277.5327.821 
(1979). 

Shadmehr, R., Krakauer, J.W., 2008. A computational neuroanatomy for motor control. 
Exp. Brain Res. 185 (3), 359–381. https://doi.org/10.1007/s00221-008-1280-5.
Shadmehr, R., Smith, M.A., Krakauer, J.W., 2010. Error correction, sensory prediction, 
and adaptation in motor control. Annu. Rev. Neurosci. 33 (1), 89–108. https://doi. 
org/10.1146/annurev-neuro-060909-153135.

Singmann H., Bolker B., Westfall J., Aust F., & Ben-Shachar M.S. (2023). afex: analysis of 

factorial experiments [Computer software]. https://CRAN.Rproject.org/ 
package=afex.

Smith, S.M., Jenkinson, M., Woolrich, M.W., Beckmann, C.F., Behrens, T.E.J., Johansen- 
Berg, H., Bannister, P.R., De Luca, M., Drobnjak, I., Flitney, D.E., Niazy, R.K., 
Saunders, J., Vickers, J., Zhang, Y., De Stefano, N., Brady, J.M., Matthews, P.M., 
2004. Advances in functional and structural MR image analysis and implementation 
as FSL. Neuroimage 23, S208–S219. https://doi.org/10.1016/j. 
neuroimage.2004.07.051.

Synofzik, M., Lindner, A., Thier, P., 2008. The cerebellum updates predictions about the 
visual consequences of one’s behavior. Curr. Biol. 18 (11), 814–818. https://doi.org/ 
10.1016/j.cub.2008.04.071.

Morehead, J.R., Orban de Xivry, J.J., 2021. A synthesis of the many errors and learning 
processes of visuomotor adaptation [Preprint]. Neuroscience. https://doi.org/ 
10.1101/2021.03.14.435278.

‘t Hart, B.M., Henriques, D.Y.P., 2016. Separating predicted and perceived sensory 
consequences of motor learning. PLoS One 11 (9), e0163556. https://doi.org/ 
10.1371/journal.pone.0163556.

Morel, A., Magnin, M., Jeanmonod, D., 1997. Multiarchitectonic and stereotactic atlas of 
the human thalamus. J. Comp. Neurol. 387 (4), 588–630. https://doi.org/10.1002/ 
(SICI)1096-9861(19971103)387:4<588::AID-CNE8>3.0.CO;2-Z.

Müller, R.A., Kleinhans, N., Pierce, K., Kemmotsu, N., Courchesne, E., 2002. Functional 
MRI of motor sequence acquisition: Effects of learning stage and performance. Cogn. 
Brain Res. 14 (2), 277–293. https://doi.org/10.1016/S0926-6410(02)00131-3.
Mutha, P.K., Sainburg, R.L., Haaland, K.Y., 2011. Left parietal regions are critical for 
adaptive visuomotor control. J. Neurosci. 31 (19), 6972–6981. https://doi.org/ 
10.1523/JNEUROSCI.6432-10.2011.

Taylor, J.A., Ivry, R.B., 2014. Cerebellar and prefrontal cortex contributions to 

adaptation, strategies, and reinforcement learning. Progress in Brain Research 210, 
217–253. https://doi.org/10.1016/B978-0-444-63356-9.00009-1.

Taylor, J.A., Klemfuss, N.M., Ivry, R.B., 2010. An explicit strategy prevails when the 

cerebellum fails to compute movement errors. Cerebellum 9 (4), 580–586. https:// 
doi.org/10.1007/s12311-010-0201-x.

Taylor, J.A., Krakauer, J.W., Ivry, R.B., 2014. Explicit and implicit contributions to 

learning in a sensorimotor adaptation task. J. Neurosci. 34 (8), 3023–3032. https:// 
doi.org/10.1523/JNEUROSCI.3619-13.2014.

17 

S. Mahdavi et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120927 

The MathWorks Inc, 2015b. MATLAB version: 8.6.0 (R2015b) [Computer Software]. The 

Wickham, H., 2016. ggplot2: Elegant Graphics For Data Analysis. Springer-Verlag New 

MathWorks Inc. https://www.mathworks.com.

York. https://ggplot2.tidyverse.org.

The MathWorks Inc, 2019b. MATLAB version: 9.7.0 (R2019b) [Computer Software]. The 

MathWorks Inc. https://www.mathworks.com.

Torchiano, M., 2016. Effsize—A package for efficient effect size computation [Computer 

software]. Zenodo. https://doi.org/10.5281/ZENODO.1480624.

Tseng, Y., Diedrichsen, J., Krakauer, J.W., Shadmehr, R., Bastian, A.J., 2007. Sensory 

Prediction Errors Drive Cerebellum-Dependent Adaptation of Reaching. 
J. Neurophysiol. 98 (1), 54–62. https://doi.org/10.1152/jn.00266.2007.

Tzvi, E., Koeth, F., Karabanov, A.N., Siebner, H.R., Kr¨amer, U.M., 2020. Cerebellar – 
Premotor cortex interactions underlying visuomotor adaptation. Neuroimage 220, 
117142. https://doi.org/10.1016/j.neuroimage.2020.117142.

Werner, S., Schorn, C.F., Bock, O., Theysohn, N., Timmann, D., 2014. Neural correlates of 
adaptation to gradual and to sudden visuomotor distortions in humans. Exp. Brain 
Res. 232 (4), 1145–1156. https://doi.org/10.1007/s00221-014-3824-1.

Whitfield-Gabrieli, S., Nieto-Castanon, A., 2012. Conn: A functional connectivity toolbox 
for correlated and anticorrelated brain networks. Brain Connect. 2 (3), 125–141. 
https://doi.org/10.1089/brain.2012.0073.

Wickham H., François R., Henry L., Müller K., & Vaughan D. (2023). dplyr: A grammar of 
data manipulation [Computer software]. https://CRAN.Rproject.org/package=dp 
lyr.

Wilke, M., Schneider, L., Dominguez-Vargas, A.U., Schmidt-Samoa, C., Miloserdov, K., 
Nazzal, A., Dechent, P., Cabral-Calderin, Y., Scherberger, H., Kagan, I., B¨ahr, M., 
2018. Reach and grasp deficits following damage to the dorsal pulvinar. Cortex 99, 
135–149. https://doi.org/10.1016/j.cortex.2017.10.011.

Wolpert, D.M., Ghahramani, Z., Jordan, M.I., 1995. An internal model for sensorimotor 

integration. Science 269 (5232), 1880–1882. https://doi.org/10.1126/ 
science.7569931 (1979). 

Wolpert, D.M., Miall, R.C., Kawato, M., 1998. Internal models in the cerebellum. Trends 
Cogn. Sci. 2 (9), 338–347. https://doi.org/10.1016/S1364-6613(98)01221-2.
Yin, C., Wei, K., 2020. Savings in sensorimotor adaptation without an explicit strategy. 
J. Neurophysiol. 123 (3), 1180–1192. https://doi.org/10.1152/jn.00524.2019.

18 

