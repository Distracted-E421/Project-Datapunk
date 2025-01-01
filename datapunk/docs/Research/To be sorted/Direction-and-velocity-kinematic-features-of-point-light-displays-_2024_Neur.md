NeuroImage 303 (2024) 120939 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Direction and velocity kinematic features of point-light displays grasping
actions are differentially coded within the action observation network

Settimio Ziccarelli a, Antonino Errante a,b, Leonardo Fogassi a,*
a Department of Medicine and Surgery, University of Parma, Parma 43125, Italy
b Neuroradiology unit, University Hospital of Parma, Parma 43125, Italy.

A R T I C L E I N F O

A B S T R A C T

Keywords:
Biological motion
Speed
Trajectory
Mirror neuron system
Decoding
fMRI

The processing of kinematic information embedded in observed actions is an essential ability for understanding
others’ behavior. Previous research showed that the action observation network (AON) may encode some action
kinematic features. However, our understanding of how direction and velocity are encoded within the AON is
still limited. In this study, we employed event-related fMRI to investigate the neural substrates specifically
activated during observation of hand grasping actions presented as point-light displays, performed with different
directions (right, left) and velocities (fast, slow). Twenty-three healthy adult participants took part in the study.
To identify brain regions differentially recruited by grasping direction and velocity, univariate and multivariate
pattern analysis (MVPA) were performed. The results of univariate analysis demonstrate that direction is
encoded in occipito-temporal and posterior visual areas, while velocity recruits lateral occipito-temporal, su-
perior parietal and intraparietal areas. Results of MVPA further show: a) a significant decoding accuracy of both
velocity and direction at the network level; b) the possibility to decode within lateral occipito-temporal and
parietal areas both direction and velocity; c) a contribution of bilateral premotor areas to velocity decoding
models. These results indicate that posterior parietal nodes of the AON are mainly involved in coding grasping
direction and that premotor regions are crucial for coding grasping velocity, while lateral occipito-temporal
cortices play a key role in encoding both parameters. The current findings could have implications for
observational-based rehabilitation treatments of patients with motor disorders and artificial intelligence-based
hand action recognition models.

1. Introduction

The human ability to process kinematic information conveyed dur-
for understanding others’
ing action observation can be crucial
behavior. Indeed, kinematic parameters, such as duration, velocity and
direction, provide crucial information about the features of the observed
action. The neural encoding of such kinematic parameters starts with the
analysis of biological motion in high-order visual areas (Caspers et al.,
2010), which then provide key information to further cortical areas
involved in action processing. In order to study biological motion ki-
nematic properties of the observed action it is necessary to isolate them
from pictorial and contextual aspects. To this aim, a useful technique is
that of point-light displays (PLDs), originally introduced by Johansson
(1973) and then employed by several researchers for studying primarily
the perception of whole body motion (Blake & Shiffrar, 2007; Johans-
son, 1973; Pavlova, 2012; Thornton, 2006). Noteworthy, it has been

* Corresponding author.

E-mail address: leonardo.fogassi@unipr.it (L. Fogassi).

shown that this information, although visually impoverished, is suffi-
cient to allow observers to understand various types of actions (e.g.,
walking, dancing, biking, jumping), as well as one’s emotional state
(Chouchourelou et al., 2006), or the effort exerted when an observed
agent lifts a weight (Shim et al., 2004). More specifically, PLDs tech-
nique allow observers recognize hand intransitive and transitive actions
performed with the upper limb (Bidet-Ildei et al., 2023; Zaini et al.,
2013).

It is well known that observation of actions performed by others in
full vision activates several cortical areas belonging to the so-called
action observation network (AON). The main nodes of this system in
humans include ventral premotor cortex (PMv), inferior frontal gyrus
(IFG) and inferior parietal lobule (IPL), that are endowed with mirror
properties (Molenberghs et al., 2012), and a more extended set of areas
including lateral occipito-temporal cortex (LOTC; hMT/V5), posterior
(SPL) and
superior

superior parietal

temporal

(pSTS),

sulcus

https://doi.org/10.1016/j.neuroimage.2024.120939
Received 5 May 2024; Received in revised form 31 October 2024; Accepted 15 November 2024
Available online 17 November 2024 
1053-8119/© 2024 The Authors. Published by Elsevier Inc. This is an open access article under the CC BY-NC-ND license ( http://creativecommons.org/licenses/by- 
nc-nd/4.0/ ). 

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

intraparietal (IPS) areas, primary somatosensory cortex (SI), and dorsal
premotor cortex (PMd) (Filimon et al., 2007; Gazzola & Keysers, 2009;
Hardwick et al., 2018). Recently, also the lateral part of cerebellum
(Lobule VI) has been included in this network (Abdelgabar et al., 2019;
Errante & Fogassi, 2020; Filimon et al., 2007; Gazzola & Keysers, 2009;
Hardwick et al., 2018). It has been proposed that the areas of the AON
can specifically encode several aspects of observed actions in fully
including kinematic features
visible conditions (Kemmerer, 2021),
(Errante et al., 2021a; Grafton & Hamilton, 2007). In neuroimaging and
electrophysiological studies in which kinematic information was
conveyed only by PLDs of whole body or effector-specific actions, acti-
vation of AON was reported (Peelen et al., 2006; Saygin et al., 2004;
Ulloa & Pineda, 2007; van Kemenade et al., 2012; Ziccarelli et al., 2022).
A previous study from our group (Ziccarelli et al. 2022) compared the
recruitment of AON during observation of fully visible or PLDs grasping
actions, showing that the two conditions, after controlling for con-
founding effects such as amount of basic visual information, motion and
contextual information, elicited similar activations, although some dif-
ferential distribution of the activated clusters was evident in premotor
and parietal areas. However, this latter study did not address the issue of
whether specific kinematic aspects of observed PLDs actions can be
differentially decoded within the AON. To demonstrate this decoding
capability is crucial because it can explain what are the neural mecha-
nisms that allows an observer to process, beyond the action goal, also the
details of the observed action. This process is very relevant in situations
in which it is necessary to exploit such information for social interaction
or imitation learning.

Thus, the aim of the present fMRI study, conducted on healthy par-
ticipants, was to verify in which areas of the AON it is possible to decode
two specific kinematics aspects that characterize the way in which an
observed hand grasping action is performed, i.e., velocity and direction.
Since in our previous study (Ziccarelli et al., 2022) we demonstrated that
observation of biological actions produces a stronger activation of the
AON with respect to non-biological stimuli moving with similar velocity
in the same direction, here we limited our investigation on the decoding
of these parameters to the former. Previous evidence is limited to studies
on the velocity of observed arm reaching movements (Di Dio et al. 2013)
or on the trajectories of reaching-grasping actions (Hamilton and Graf-
ton, 2007), investigated by employing fully-visible stimuli and the
repetition-suppression technique. In order to isolate kinematic aspects
from other confounding factors, we used PLDs versions of different
grasping actions, performed with two different velocities (fast and slow)
and two different directions (right and left), in a passive action obser-
vation task. We hypothesized that, beyond occipito-temporal high-order
visual areas, also other nodes of AON can contribute to the decoding of
either direction or velocity, or both.

To test these hypotheses, we combined both univariate and multi-
variate analyses to evaluate, respectively, whether: a) differences in
direction and velocity kinematic parameters activate different areas of
the AON; b) specific AON regions give a major contribution to the
decoding of action kinematic features.

2. Materials and methods

2.1. Participants

Twenty-three healthy human volunteers (11 female; mean age 23
years; range 20 - 30 years) with no history of neurological or psychiatric
disorders, and of drug or alcohol abuse, participated in the study. All
participants were right-handed according to the Edinburgh Handedness
Inventory (Oldfield, 1971). Informed consent was obtained in accor-
dance with Helsinki declaration. The study was approved by the local
ethics committee (Comitato Etico Area Vasta Emilia Nord – AVEN; code
NEUROIMAGE_UNIPR).

2.2. Stimuli

Experimental stimuli consisted in 2 seconds videos of PLDs grasping
actions performed by an actor with the right hand with two different
velocities (fast and slow) in right and left directions (Fig. 1a). In order to
use a diverse set of stimuli, grasping actions were performed with four
different grips (whole hand, five-finger, three-finger, and precision).
◦
Videos were recorded from a frontal perspective (180
angle) in a well-
lit environment on a black background by means of an HD camera with a
frame rate of 240 fps and a resolution of 1080 × 720p. PLDs were
realized using 20 small green spheres (1 cm diameter) attached to the
hand, wrist and arm joints. Videos were post-processed in Final Cut Pro
X (v10.6.1, Apple Inc.) using the chroma key technique performing in-
verse keying, so that the spheres appeared as white dots on a black
background. In order to avoid lateralized effects, the presented action
started at the center of the screen and ended in the medial portion of the
left or right hemifield (depending on the direction), no more than 8
degrees from fixation. Furthermore, in order to avoid a lateralization of
the brain activation dependent on the stimulation of only one visual
hemifield, we presented the stimuli keeping the forelimb mostly in the
screen center.

In order to assess velocity differences between the fast and slow
grasping stimuli, a 2D kinematic analysis was performed (Tracker
v6.0.3, 2021, Douglas Brown) by calculating, in each video, the velocity
profile of the wrist (Fig. 1b). Values were smoothed using a gaussian-
weighted moving average filter provided in MATLAB R2021a (The
Mathworks, Inc.) to account for the noise in the recorded data. Plotting
the velocity data over the movement time percentage, allowed for
comparisons between trials that differed in durations. The percentage of
acceleration and deceleration of each action was further calculated
(Fig. 1c). The percentage of the action acceleration phase was computed
starting from the beginning of the movement until the maximum ve-
locity peak, while the percentage of deceleration from the velocity peak
to the end of the grasping action. Furthermore, averaged velocity curves
were generated for each specific combination of direction and velocity
allowing for a more straightforward comparison of the differences be-
tween stimuli velocities, as indicated by the descriptive statistics in
Table 1.

2.3. fMRI task

Participants were informed about the fMRI scanning process in order
to familiarize them with the experimental setting. During MR scanning,
they laid supine in the bore of the scanner in a dimly lit environment.
The experiment was conducted in a single imaging session. It was
divided into five functional runs, each lasting 6 minutes (with 180
volumes). During each run, participants were required to observe video
stimuli presented on digital goggles (Resonance Technology, North-
ridge, CA) with a 60 Hz refresh rate, a resolution of 800 horizontal pixels
◦
× 600 vertical pixels, and a horizontal eye field of 30
. Sound-
attenuating (30 dB) headphones were employed in order to dampen
scanner noise. Participants were instructed to fixate a white cross pre-
sented in the center of the screen on a black background for the entire
duration of the imaging session. Each run was acquired with an event-
related design in which stimuli were presented using a randomized
sequence. A total of 208 video stimuli were presented during the whole
experiment. More specifically, we presented 16 distinct grasping videos,
grouped according to each combination of direction and velocity, each
repeated 52 times. Grasping videos were randomly interleaved by null
events (Friston et al., 1999), consisting in a white cross in the center of a
black background. These events ranged in duration from a minimum of 2
seconds to a maximum of 14 seconds, in steps of 2 seconds.

In order to monitor participants’ attention to the visual stimuli, catch
trials were randomly presented during each run. During the catch trial,
participants observed a 2 second color filtered video stimulus (red, blue,
green, yellow, magenta) after which they had to indicate, by pressing a

2 

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

Fig. 1. Stimuli and experimental paradigm. From (A) to (C), in left-to-right order each graph represents data from each specific combination of direction and velocity
as follows: i) RIGHT FAST; ii) RIGHT SLOW; iii) LEFT FAST; iv) LEFT SLOW. (A) Examples of static frames of PLDs grasping stimuli. In left-to-right order the
presented grips are as follows: i) whole hand; ii) three finger; iii) precision; iv) five finger. (B) Velocity curves of the four types of grips presented in the videos. Note
that the scale of the ordinate (stimulus velocity) for the fast stimuli is different from that for the slow stimuli. (C) Horizontal bar graphs showing the acceleration (red)
and deceleration (blue) phases, expressed as percentages of movement time of each type of grip. (D) Event related experimental paradigm consisting in video events
interleaved by an interstimulus interval (ISI). Catch trials were followed by a post-catch denoising period to allow BOLD signal to reach baseline.

Table 1
Descriptive statistics of averaged velocity curves for each specific combination of direction and velocity.

RIGHT FAST
RIGHT SLOW
LEFT FAST
LEFT SLOW

Mean velocity
cm/s (SD)

71.76 (44.66)
8.09 (7.47)
62.32 (48.03)
10.59 (8.07)

Range

Velocity Peak cm/s (SD

Range

41.6 – 84.56
5.97 – 9.49
52.39 – 67.85
9.36 – 12.89

140.48 (32.65)
23.09 (5.58)
142.84 (17.05)
24.45 (4.21)

92.24 – 164.50
17.08 – 27.09
118.87 – 156.83
18.95 – 29.21

button on a response pad, the main color of the stimulus by selecting one
of the two options presented on the screen (4 seconds time window). The
average performance of correct responses was 94%. In order to remove
potential signal artifacts due to the hand movement, after this attention
task, a 12 second signal denoising period (post-catch) was introduced,
during which participant had to remain still while fixating the white
cross on the center of the black screen (Fig. 1d).

2.4. fMRI data acquisition

Anatomical T1-weighted and functional T2*-weighted MR images
were acquired with a 3T General Electric scanner (MR750 Discovery)
equipped with an 8-channel receiver head-coil. Functional volumes
acquisition parameters were the following: 40 axial slices of functional
images covering the whole brain acquired in an interleaved bottom-up
order using a gradient-echo echo-planar imaging (EPI) pulse sequence,
slice thickness = 3.0 mm, interslice gap = 0.5 mm, 64 × 64 × 37 matrix

3 

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

with a spatial resolution of 3.5 × 3.5 × 3.5 mm, TR = 2000 ms, TE = 30
◦
ms, FOV = 205 × 205 mm2, flip angle = 90
, in plane resolution = 3.2 ×
3.2 mm2. A morphological 3D T1-weighted (Bravo_Mik) volume was
acquired as anatomical reference. Its acquisition parameters were: 192
slices, 512 × 512 matrix, spatial resolution 0.9 × 0.5 × 0.5 mm, TR =
◦
9700 ms, TE = 4 ms, FOV = 252 × 252 mm, flip angle 90

.

2.5. fMRI data analysis

2.5.1. Data preprocessing and analysis

SPM12 (Wellcome Department of Imaging Neuroscience, University
College, London, UK; http://www.fil.ion.ucl.ac.uk/spm) on MATLAB
R2021a (The Mathworks, Inc.) was used to process the acquired MRI
data. To allow T1 equilibration so that the magnetic field could reach a
steady state, the first four volumes of each run were discarded. The
participant’s volumes were preprocessed using the same pipeline. Im-
ages were spatially realigned to the first volume of the first functional
run, un-warped to correct for between scan motion and slice timing
corrected considering slice acquisition order. Spatial transformation
parameters derived from the segmentation and spatial normalization of
the anatomical T1-weighted images to the Montreal Neurological
Institute (MNI) space were then applied to the realigned EPIs and re-
sampled in 2 × 2 × 2 mm3 voxels using a 4th degree B-spline interpo-
lation in space. A 4-mm full-width half-maximum isotropic Gaussian
kernel (FWHM) smoothing was applied to all functional T2*-weighted
volumes.

Data were analysed using a random-effects model (Friston et al.,
1999), implemented in a two-level procedure. Single-subject fMRI time
series were modelled using the general linear model in the first level
analysis and the design-matrix included the onsets and the durations of
all conditions modelled as events as well as the response of catch trial
conditions modelled as an event comprising the video observation (2
seconds), response selection (4 seconds) and post-catch denoise period
(12 seconds) for each of the five functional runs. Null events were
considered as implicit baseline. Conditions resulting from the combi-
nation of 2 velocities × 2 directions × 4 grips, were computed for each
subject and contrasted with the implicit baseline. Differences in duration
of the movement in fast and slow videos, were taken into account by
explicitly modelling them as a regressor. Head motion parameters were
also entered as multiple regressors. Specific effects were tested using t
statistical parametric maps, with degrees of freedom corrected for
non-sphericity at each voxel.

In the group-analysis, corresponding t-contrast images of the first-
level conditions for each participant, except for Catch-Trial, were
entered into a flexible ANOVA with sphericity-correction for repeated
measures (Friston et al., 2002). In order to highlight the areas mainly
involved in coding each combination of the experimental conditions,
namely direction and velocity, t-contrasts were generated (RIGHT FAST,
RIGHT SLOW, LEFT FAST, LEFT SLOW). Furthermore, F-contrasts were
performed in order to examine brain regions that exhibited significant

Table 2
Anatomically defined ROIs (defined bilaterally) from Anatomy toolbox v3.0
toolbox matched with the anatomical reference (Eickhoff et al., 2005)

Anatomy Toolbox Nomenclature

Anatomical Reference

Visual hOc5
PO1 PIP
SPL 7PC
SPL 7A
hIP3 IPS
hIP2 IPS
hIP1 IPS
IPL PF
IPL PFt
Premotor 6d1
Premotor 6d2
BA 44

MT/V5
SPOC
SPL
SPL
mIPS
aIPS
vIPS
IPL
IPL
PMd
PMd
PMv/IFG

4 

activity related to differences in direction, or velocity.

2.6. Regions of interest definition

Bilateral anatomically defined regions of

interest (ROIs) were
selected from Anatomy toolbox v3.0 (Eickhoff et al., 2005) (Table 2).
ROIs used in this study were selected based on both anatomical and
functional criteria since they have also been described as part of the
AON (Hardwick et al., 2018). Table 2 reports the correspondence be-
tween anatomy toolbox nomenclature and the anatomical reference we
use throughout the manuscript. The selected ROIs were subsequently
combined into an ad-hoc atlas created using ImCalc SPM12 toolbox
(Wellcome Department of Imaging Neuroscience, University College,
London, UK; http://www.fil.ion.ucl.ac.uk/spm).

2.7. Multivoxel pattern analysis

In order to make a fine-grained analysis of fMRI data patterns, we
performed a multivoxel pattern analysis (MVPA) on linear combination
of first-level beta estimates, using Pattern Recognition for Neuroimaging
Toolbox (PRoNTo) (Schrouff et al., 2016), running on MATLAB (The
MathWorks Inc.)

For each participant the experimental design elements, that is the
fMRI data, onsets and condition labels were specified. To exclude voxels
outside the brain that carry non-relevant information, a first level whole
brain binary mask was employed. The ad-hoc atlas was used for the
computation of the feature set as a second level mask and employed in
this analysis in order to jointly analyse the neural pattern of relevant
brain areas.

A multi-kernel learning (MKL) classifier with L1 regularization was
used to classify between neural patterns in the AON ROIs simulta-
neously. The idea behind MKL was to combine each ROI feature set by
assigning different weights to each kernel function. Each kernel corre-
sponded to a different subset of features, that is the ROIs neural pattern
distribution. The L1 regularization, also known as LASSO (Least Abso-
lute Shrinkage and Selection Operator), was incorporated into the MKL
framework to promote sparsity in the model which allowed the selection
of relevant features both at the feature and kernel level. By imposing a
penalty on the sum of the absolute values of the model’s coefficients, L1
regularization allowed for smaller weights for less important features,
effectively driving some coefficients to zero. This resulted in feature
selection, where only a subset of the most relevant features was used in
the model, that is a subset of regions and voxels that carried predictive
information. Thanks to this approach, it was possible to rank the ROIs
according to their contribution to each classification model, excluding
those with zero contribution. Furthermore, an L1 multiclass SVM algo-
rithm (L1 MCL) was employed, allowing to find the optimal hyperplanes
that separate more than two different classes in a high-dimensional
feature space. A total of two L1 MKL (Direction and Velocity) models
and one L1 MCL (each specific combination of direction and velocity)
model was created. For the Direction model, class one and two corre-
spond to RIGHT and LEFT respectively, while for the Velocity model, to
FAST and SLOW. Regarding the L1 MCL model, the different classes
were RIGHT FAST (class one), RIGHT SLOW (class two), LEFT FAST
(class three), LEFT SLOW (class four).

To increase the predictive models performance, we optimized the
hyperparameter using a k fold on subject out nested cross-validation (k
= 5) which was used only to estimate the value of the hyperparameter
leading to the highest performance. A leave one condition out cross
validation scheme was used to assess the performance of the classifier
and its ability to generalize the results of its computations on a part of
the dataset on which it was not trained. The entire dataset was separated
into a set used for training and the other for test. The number of folds in
which data were partitioned was equal to the number of conditions so
that the training set was equal to the number of conditions minus one.
Further computations consisted in mean centring the features using

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

training data and dividing the data vectors by their Euclidean norm. The
latter is particularly important in order to take into account the different
ROIs size for a more accurate comparison. One thousand permutations
were run to estimate the model p-value, retraining it for the specified
number of times with permuted labels and targets. Another measure of
the model performance is the area under curve (Beauchamp et al., 2003)
which was computed for each L1 MKL model. Weight contribution was
calculated both at a region level to investigate the contribution of each
ROI to the decision function, and at a voxel level providing insights on
the discriminative patterns within the areas. Furthermore, the compu-
tation of the reproducibility of the regions ranking was performed in
order
the
cross-validation folds (Schrouff et al., 2018).

to examine the consistency of

the ranking across

MVPA analyses on single ROIs were also carried out to provide re-
sults that isolate the role of each AON area in the coding of direction and
velocity parameters. Binary SVM classifiers for the direction model
(RIGHT vs LEFT) and for the velocity model (FAST vs SLOW) were run
using a leave one subject out (LOSO) cross validation. To assess statis-
tical significance, permutation testing with one hundred iterations was
conducted to estimate the p-value for each model and ROI. Multiclass
gaussian process classifications (GPC) were performed on each combi-
nation of direction and velocity (RIGHT FAST vs RIGHT SLOW vs LEFT
FAST vs LEFT SLOW) to evaluate the decoding of both kinematic fea-
tures altogether. These multiclass classifiers were also assessed using a
LOSO cross-validation approach, and using permutation testing with
one hundred iterations, similar to the binary SVM models.

3. Results

3.1. Univariate analysis

Fig. 2 shows brain activation maps on an MNI brain template with a
significance threshold of p = 0.01 FWE corrected at a voxel level. Fig. 2a
shows bilateral significant activation clusters resulting from the t-
contrast between RIGHT FAST conditions against baseline in posterior
occipital (pOC), lateral occipito-temporal (LOTC), superior parieto-
occipital cortex (SPOC) and posterior fusiform gyrus (pFG), posterior
sector of the superior temporal sulcus (pSTS), superior parietal (SPL)
and intraparietal (IPS) areas as well as dorsal and ventral premotor areas
(PMd, PMv). Other significantly activated clusters are present in the pre-
supplementary motor area (preSMA), posterior sector of the middle
cingulate cortex (pMCC), posterior sector of the somatosensory cortex
(Area 2) and anterior insula (aI). Subcortical clusters are located in the
anterior sector of the putamen, pulvinar and in the cerebellar lobules VI
and left VIIb. Activation patterns in both cortex and cerebellum, similar
to those previously described, result from the contrast between RIGHT
SLOW conditions against baseline (Fig. 2b), although less extended and
with no clusters in the putamen and anterior insula. In both conditions,
left LOTC cluster is more activated as compared to the contralateral
sector. The LEFT FAST and LEFT SLOW conditions, when contrasted
against baseline (Fig. 2c, d), activate the same cortical and cerebellar
areas as the RIGHT FAST and RIGHT SLOW conditions. However, the
activation in the LOTC area is stronger on the right side for both LEFT

Fig. 2. Cortical activations projected onto a 3D Brain template (Surfice; https://www.nitrc.org/projects/surfice/). (A) Contrast between RIGHT FAST and baseline.
(B) Contrast between RIGHT SLOW and baseline. (C) Contrast between LEFT FAST and baseline. (D) Contrast between LEFT SLOW and baseline. (E) F-Contrast of
DIRECTION effect. (F) F-Contrast of VELOCITY effect.

5 

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

conditions. Furthermore, in LEFT FAST brain activations, as compared
to the LEFT SLOW condition, there is a small significant cluster in the
anterior left putamen.

To investigate the main effects of direction and velocity, F-contrasts
were employed. Activation maps are overlaid on an MNI brain template
and with a significance threshold of p = 0.01 FWE corrected at a cluster
level. F-contrast for direction (Fig. 2e) shows bilateral activation in pOC,
pFG and in the SPOC as well as in the cerebellar lobule VI. The F-contrast
for velocity shows bilateral activations in LOTC areas bilaterally and SPL
as well as the medial IPS (mIPS). In the right hemisphere, the parietal
activation cluster was more extended rostrally including also a small
posterior portion of Area 2 (Fig. 2f) (Supplementary Table 1).

3.2. Multivoxel pattern analysis

The analysis revealed that both L1 MKL models were significantly
accurate in discriminating between Direction and Velocity as well as L1
MCL in discriminating between each specific combination of these two
kinematic parameters. Details about each model performance is listed in
Table 3.

The L1 MKL Direction model revealed significant model decoding
accuracy (84.01%, p = 0.001, AUC = 0.92, p = 0.001) in classifying
between linear combination of beta images belonging to RIGHT and
LEFT conditions for each subject. ROIs contributing to the L1 MKL Di-
rection classification model are listed in Table 4.

The L1 MKL Velocity model computed on the linear combination of
beta images of FAST and SLOW conditions for each subject, was
significantly accurate in discriminating the neural patterns belonging to
these conditions (model accuracy = 74.31%, p = 0.001, AUC = 0.79, p =
0.001). L1 MKL Velocity ROIs contribution to the classification model are
listed in Table 5.

To investigate the stability of the selection of regions across folds of
the L1 MKL models, we also computed the reproducibility measure for
both Direction (model reproducibility = 0.97) and Velocity model (model
reproducibility = 0.98). Contribution to the Direction and Velocity
models, both at a ROI and voxel level, is represented in Figs. 3 and 4
respectively.

L1 MCL model which classified between RIGHT FAST, RIGHT SLOW,
LEFT FAST and LEFT SLOW conditions altogether, where chance level is
25%, showed significant decoding accuracy (55.61%, p = 0.001).
Furthermore, each class achieved an above threshold significant
decoding accuracy (RIGHT FAST model accuracy = 56.88%, p = 0.001;
RIGHT SLOW model accuracy = 59.38%, p = 0.002; LEFT FAST model
accuracy = 46.88%, p = 0.004; LEFT SLOW model accuracy = 59.38%,
p = 0.001).

Binary SVM classification analysis on the direction model, which
classified between linear combinations of beta images belonging to
RIGHT and LEFT conditions for each subject, revealed significant
decoding accuracy in the following ROIs: Left hIP3 IPS (model accuracy
= 58.15%, p = 0.01), Left PO1 PIP (model accuracy = 55.16%, p =
0.04), Left Visual hOc5 (model accuracy = 57.34%, p = 0.01), Right PO1
PIP (model accuracy = 57.88%, p = 0.02), Right Visual hOc5 (model
accuracy = 55.98%, p = 0.02) (Fig. 5).

No significant above threshold model accuracy was found in the

remaining ROIs (for details see Table 6).

The binary SVM analysis on the velocity model, classifying between

Table 4
L1 MKL direction model weights computation.

L1 MKL Direction model weights

ROI Label

Left Visual
hOc5

Left PO1 PIP

Left hIP3 IPS

Left Premotor

6d2

Left hIP1 IPS
Left SPL 7A
Left BA 44
Left IPL PF
Left Premotor

6d1

Left IPL PFt
Left hIP2 AIP
Left SPL 7PC

ROI weight
(%)

ROI size
(vox)

Expected
Ranking

Right PO1 PIP

Right Visual
hOc5

Right hIP3 IPS
Right BA 44
Right Premotor
6d1
Right SPL 7PC
Right SPL 7A

Right Premotor
6d2
Right hIP1 IPS
Right IPL PFt
Right hIP2 IPS

Right IPL PF

18.84
18.28

14.88
9.78

8.46
4.02
3.86
3.71

2.83
2.71
2.55

2.33

2.10
1.69
1.11
0.96
0.84
0.40
0.28
0.14

0.12
0.10
0.02
0

182
87

223
88

441
478
479
691

343
413
329

322

340
416
226
437
624
540
245
528

492
438
300
160

23.69
23.31

22.00
20.75

20.00
16.81
17.19
16.81

14.50
14.69
13.56

13.06

12.94
11.31
9.69
8.44
7.56
1.25
0.75
0.56

0.50
0.44
0.19
0

images part of FAST and SLOW conditions, showed significant classifi-
cation accuracy in: Left hIP1 IPS (model accuracy = 54.89%, p = 0.05),
Left hIP3 IPS (model accuracy = 55.98%, p = 0.01), Left IPL PFt (model
accuracy = 58.15%, p = 0.01), Left Visual hOc5 (model accuracy =
57.88%, p = 0.01), Right hIP1 IPS (model accuracy = 54.89%, p =
0.05), Right hIP3 IPS (model accuracy = 58.42%, p = 0.01), Right
Premotor 6d1 (model accuracy = 55.16%, p = 0.04), Right Visual hOc5
(model accuracy = 54.89%, p = 0.01) (Fig. 6).

The remaining ROIs did not show model accuracy above significance

threshold (Table 7).

The Multiclass GPC multivoxel analyses performed on single ROIs,
decoding between RIGHT FAST, RIGHT SLOW, LEFT FAST and LEFT
SLOW conditions altogether, with a chance level set at 25%, revealed
significant decoding accuracy in: Left hIP1 IPS (model accuracy =
29.62%, p = 0.01), Left hIP3 IPS (model accuracy = 33.97%, p = 0.01),
Left IPL PFt (model accuracy = 29.89%, p = 0.03), Left PO1 PIP (model
accuracy = 30.98%, p = 0.01), Left SPL7A (model accuracy = 29.89%, p
= 0.01), Left SPL 7PC (model accuracy = 28.80%, p = 0.01), Left Visual
hOc5 (model accuracy = 34.78%, p = 0.01), Right hIP2 IPS (model
accuracy = 28.80%, p = 0.05), Right hIP3 IPS (model accuracy =
29.35%, p = 0.01), Right IPL PFt (model accuracy = 32.34%, p = 0.01),
Right PO1 PIP (model accuracy = 34.51%, p = 0.01), Right SPL7A
(model accuracy = 29.62%, p = 0.01), Right SPL 7PC (model accuracy =
30.98%, p = 0.01), Right Visual hOc5 (model accuracy = 32.61%, p =

Table 3
MVPA classification models performance summary. For the L1 MKL Direction model class 1 corresponds to RIGHT and class 2 to LEFT. For the L1 MKL Velocity model
class 1 corresponds to FAST and class 2 to SLOW. For the L1 MCL model classes from 1 to 4 correspond to RIGHT FAST, RIGHT SLOW, LEFT FAST and LEFT SLOW
respectively. AUC = Area under curve; Acc = Accuracy.

Model name

Accuracy (%)

Accuracy (p)

L1 MKL Direction
L1 MKL Velocity
L1 MCL Dir * Vel

84.01
74.31
55.61

< 0.001
< 0.001
< 0.001

AUC

0.92
0.79
-

AUC (p)

< 0.001
< 0.001
-

Class 1 acc (%)

Class 2 acc (%)

Class 3 acc (%)

Class 4 acc (%)

83.59
72.74
58.88

84.38
75.78
59.38

-
-
46.88

-
-
59.38

6 

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
S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

Table 5
L1 MKL velocity model weights computation

L1 MKL Velocity model weights

ROI Label

Right Visual
hOc5

Left BA 44
Left SPL 7A
Left SPL 7PC
Left Visual
hOc5

Left hIP2 IPS

Left IPL PFt
Left Premotor

6d1

Left Premotor

6d2

Left hIP1 IPS
Left IPL PF
Left PO1 PIP
Left hIP3 IPS

0.01) (Fig. 7).

Right hIP1 IPS
Right Premotor
6d1
Right BA 44

Right Premotor
6d2
Right SPL 7PC
Right IPL PFt
Right hIP2 IPS
Right IPL PF
Right hIP3 IPS

Right PO1 PIP
Right SPL 7A

ROI weight
(%)

ROI size
(vox)

Expected
Ranking

13.12

11.55
8.76
7.68
7.56

7.34
6.78
6.42

5.41
4.81
4.04

3.60

3.55

2.54
2.43
2.02
0.68
0.46
0.42
0.21
0.19
0.16
0.12
0.12

88

540
624
160
87

300
340
691

479
438
528

329

322

343
416
226
492
478
437
245
223
441
182
413

23.62

23.06
20.94
19.56
19.38

19.38
17.88
17.44

16.12
14.75
13.56

12.81

12.88

11.06
10.38
9.50
3.94
3.88
3.25
0.75
1.81
0.75
0.38
0.31

Model performance in the remaining ROIs was below the signifi-

cance threshold (Table 8).

4. Discussion

In the present fMRI study, healthy participants observed grasping
actions presented as PLDs, performed with two velocities, fast and slow,
in two different directions, right and left. The results confirm that the
kinematic information conveyed by the observation of PLDs grasping
actions elicits activation of the AON. Univariate analyses reveal that
bilateral posterior occipital and posterior parietal areas of this network
are mainly recruited in coding differences in stimulus direction, while
velocity is mainly coded in occipito-temporal and parietal areas, bilat-
erally. By means of multivariate analyses we further demonstrate that
both direction and velocity, as well as their combinations, are signifi-
cantly decoded at the network level. More specifically, AON regions
contribute differently to the classification models. Multivariate ROI
analysis confirms this differential contribution. In particular: for the
direction, coding is demonstrated in the same areas considered relevant
for the decoding at the network level; for the velocity, coding is partially
confirmed in areas also relevant for network level analysis, such as MT/
V5, IPS and PMd.

4.1. Differences in action direction are decoded in posterior nodes of the
AON

A distributed network of areas within the AON, including bilateral
MT/V5 and SPOC codes differences in direction of the observed PLDs
grasping actions. In addition, multivariate analysis expands these find-
ings by showing that the areas that mostly contribute to the direction
multikernel model are not limited to the aforementioned regions but
include also sectors of the mIPS bilaterally. The analysis of voxel weights
distribution further suggests that areas of the left hemisphere mostly

contribute to the decoding of actions performed towards the contralat-
eral, right portion of space, while those of the right hemisphere to those
performed leftwards. Multivariate single ROI analysis demonstrates that
it is possible to classify the direction in the same set of areas, taken
independently from each other, revealed by network level analysis.

These results are in line with previous neuroimaging studies in
humans, which showed that MT/V5 plays a key role in coding motion
direction (Kamitani & Tong, 2006; Zeki et al., 1991). This has also been
confirmed by TMS studies showing that stimulation of this area impairs
motion perception (Beckers & Zeki, 1995; Sack et al., 2006). It is worth
noting that studies on the role of this area mainly used gratings or
clockwise and counterclockwise dots rotary motion as visual stimuli. In
contrast, our stimuli, although conveying exclusively kinematic infor-
mation, provide not only clues about motion but also about hand shape,
which could contribute to a stronger activation of MT/V5. This is in line
with a previous study (Ziccarelli et al., 2022) in which, using a similar
paradigm, we demonstrated that MT/V5 exhibits a stronger response to
PLDs grasping actions as compared to the motion of a PLDs arm-shaped
geometrical object moving in the same direction. In addition to this
latter study, the present work demonstrates that from the activation
pattern of this area it is possible to decode more complex information
about action kinematics, such as differences in the observed grasping
direction.

Concerning SPOC, which has been suggested to be homologue of V6/
V6A complex of the monkey (Gallivan et al., 2009; Monaco et al., 2011;
Pitzalis et al., 2013), it is known that many neurons of this latter com-
plex respond to visual stimuli (Pitzalis et al., 2015), but there is no ev-
idence of direction preference for PLDs biological stimuli. In humans,
neuroimaging studies showed that this area is involved in visual motion
perception (Cardin et al., 2012; Pitzalis et al., 2010) and in both
observation (Filimon et al., 2007) and execution (Cavina-Pratesi et al.,
2010; Gallivan et al., 2009) of arm reaching actions. Previous data
(Pitzalis et al., 2013) indicate that SPOC can be important for encoding
egomotion, when individuals navigate through a virtual space, going in
a forward direction rather than backwards. Interestingly, Hamilton and
Grafton (2006), using an fMRI repetition-suppression paradigm in which
participants observed reaching-grasping of different objects performed
with two different trajectories (to the left or to the right), found an effect
in occipito-parietal cortex, involving a series of areas mostly belonging
to the dorsal stream, among which a region corresponding to SPOC.

Data on patients with lesions of this region show that they were
completely unable to discriminate the direction of motion of visual
stimuli such as random dots (Blanke et al., 2003). Previous data from our
lab showed a stronger recruitment of this area during observation of
grasping actions as compared to that of an arm-shaped geometrical
object (Ziccarelli et al., 2022). The findings of the present study add
additional pieces of evidence, by demonstrating that this region also
significantly contributes to the decoding of differences in direction of
observed grasping actions when only kinematic information is available,
not only when considered as part of a network, but also when investi-
gated at the single ROI level.

Our results show that it is possible to decode differences in grasping
direction within the activation pattern of mIPS during passive obser-
vation. Several investigations aimed at identifying homologous brain
regions in humans and monkeys (Grefkes & Fink, 2005; Grefkes et al.,
2004; Grefkes et al., 2002; Prado et al., 2005; Scheperjans, Eickhoff,
et al., 2008; Scheperjans, Hermann, et al., 2008) support the idea that
human mIPS is homologous to monkey MIP, particularly in relation to
the functions of visuomotor integration and action planning (Filimon,
2010; Grefkes & Fink, 2005). However, there is also one study chal-
lenging this view (Orban et al., 2006), by proposing that the medial
sector of the intraparietal sulcus in humans may represent a distinct
area, rather than being a direct homologue of MIP.

Previous studies in monkeys demonstrated that MIP neurons activate
during reaching actions performed towards a target (Cohen and
Andersen, 2002; Andersen et al., 2007). In particular, in a study in which

7 

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
S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

Fig. 3. Direction model weights distribution at a Region of Interest and voxel level of direction multi-kernel model. (A) L1 MKL Direction weight distribution at a ROI
level. Weight computation at a ROI level is represented as a bar graph with dark yellow ones, leftward of the vertical dotted line, showing the ROIs that collectively
contributed to explain 75% of the model. The red line shows the cumulative percentage of the total weight contribution to the classification. (B) Upper panel shows
the weight distribution at a voxel level within AON areas as a bar graph, with red bars indicating the percentage of weights most discriminative for RIGHT class and
blue ones for LEFT class. Bottom panel shows the results of the weight computation at a voxel level projected on an inflated brain template (Surfice; https://www.nitr
c.org/projects/surfice/) with the same color coding previously described.

8 

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

Fig. 4. Velocity model weights distribution at a Region of Interest and voxel level of velocity multi-kernel model. (A) L1 MKL Velocity weight distribution at a ROI
level. Weight computation at a ROI level is represented as a bar graph with dark yellow ones, leftward of the vertical dotted line, showing the ROIs that collectively
contributed to explain 75% of the model. The red line shows the cumulative percentage of the total weight contribution to the classification. (B) Upper panel shows
the weight distribution at a voxel level within AON areas as a bar graph, with red bars indicating the percentage of weights most discriminative for FAST class and
blue ones for SLOW class. Bottom panel shows the results of the weight computation at a voxel level projected on an ICBM152 inflated brain template (Surfice; https
://www.nitrc.org/projects/surfice/) with the same color coding previously described.

9 

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

Fig. 5. Results of the binary SVM MVPA on single ROIs for the DIRECTION model. Histograms show the percentage of model accuracy (% ACC) in each region of
◦
interest. Red colored bars show the ROIs with a significant (*p < .05, **p < .01, ***p < .001) model accuracy assessed by means of a permutation testing (n
permutation = 100).

Table 6
Results of binary SVM MVPA on single ROIs for the DIRECTION model (ACC =
accuracy; pval = p-value; AUC = area under curve). Areas with significant p-
values are in bold.

ROI

ACC

Left hIP1 IPS
Left hIP2 IPS
Left hIP3 IPS
Left Broca 44
Left IPL PF
Left IPL PFt
Left PO1 PIP
Left Premotor

6d1

50.00
49.18
58.15
47.55
43.48
52.17
55.16
49.18

ACC
pval

0.44
0.6
0.01
0.83
0.99
0.25
0.04
0.76

class 1
acc

47.83
43.48
67.61
40.76
39.67
52.17
47.83
51.02

class 2
acc

52.17
54.89
58.7
54.35
47.28
52.17
62.5
48.3

AUC

0.5
0.49
0.61
0.48
0.43
0.53
0.68
0.51

AUC
pval

0.49
0.54
0.01
0.7
0.94
0.28
0.01
0.50

Left Premotor

46.200

0.89

500

42.39

0.45

0.86

6d2

Left SPL 7A
Left SPL 7PC
Left Visual
hOc5

Right hIP1 IPS
Right hIP2 IPS
Right hIP3 IPS
Right Broca 44
Right IPL PF
Right IPL PFt
Right PO1 PIP
Right Premotor

6d1

53.26
52.72
57.34

47.55
50.27
52.99
50.82
50.82
51.63
57.88
51.63

0.08
0.18
0.01

0.79
0.48
0.15
0.36
0.33
0.28
0.02
0.25

52.72
53.80
53.80

47.28
46.74
53.80
49.46
45.65
47.83
67.39
46.74

53.8
51.63
60.87

47.83
53.8
52.17
52.17
55.98
55.43
48.37
56.52

0.59
0.55
0.75

0.50
0.50
0.53
0.53
0.51
0.52
0.71
0.51

0.04
0.15
0.01

0.56
0.59
0.28
0.27
0.28
0.31
0.01
0.35

Right Premotor

51.63

0.25

53.26

50.00

0.55

0.01

6d2

Right SPL 7A
Right SPL 7PC
Right Visual

hOc5

50.27
48.91
55.98

0.38
0.71
0.02

49.46
48.91
60.87

51.09
48.91
51.09

0.56
0.49
0.68

0.07
0.49
0.01

monkeys used a joystick to control the movement of a dot on a screen, it
has been shown that neurons in MIP become active not only during the
reaching act but also during passive observation of the resulting dot
movement, that presents the same kinematics of the arm movement

(Eskandar and Assad, 2002). Interestingly, in both tasks, neurons ac-
tivity was modulated by the same, specific direction. Although previous
research in humans demonstrated a differential recruitment of mIPS
during upper limb actions performed in different directions (Davare
et al., 2012), to our knowledge, evidence for its specific role in direction
encoding during passive observation of fully visible actions has not been
reported. Considering the above reported evidence and research
demonstrating that mIPS is recruited during both execution and obser-
vation of upper limb actions (Filimon et al., 2009), one can hypothesize
that differences in direction of an observed action can be plausibly
encoded in this area. Thus, the current study provides a novel finding
that allows to better understand the mIPS specific involvement in the
encoding of differences in the direction of an observed action.

4.2. Velocity is decoded in the AON parietal and premotor areas

Taken together, univariate and multivariate network analyses
revealed that velocity information is represented in a distributed
network of AON areas such as bilateral MT/V5, IPS, and both PMd and
PMv/IFG cortex, as well as in the left SPL. Weights distribution within
these regions show that most of them contributed similarly to the
decoding of the two employed velocities except MT/V5, which greatly
contributed to the classification of actions performed with a slow ve-
locity. This could be attributable to the fact that slow grasping actions
might provide, regardless of stimulus duration, more distinct and clear
motion cues which can be elaborated and classified with greater accu-
racy. When considering multivariate single ROI analysis, some areas
(MT/V5, IPS, PMd) correspond to those revealed by network level
analysis, thus demonstrating that they can encode velocity.

Single neuron recording monkey studies performed in MT and MST
showed that these areas are sensitive not only to stimulus direction but
also to its velocity (Maunsell and Van Essen, 1983; Priebe et al., 2003).
In line with this, also neuroimaging studies on humans demonstrated
that LOTC, which likely comprises MT/V5, is not only a motion direction
sensitive area but also plays a crucial role in several other aspects, such
as the dissociation between shape and category (Bracci & de Beeck,

10 

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

Fig. 6. Results of the binary SVM MVPA on single ROIs for the VELOCITY model. Histograms show the percentage of model accuracy (% ACC) in each region of
◦
interest. Red colored bars show the ROIs with a significant (*p < .05, **p < .01, ***p < .001) model accuracy assessed by means of a permutation testing (n
permutation = 100).

Table 7
Results of binary SVM MVPA on single ROIs for the VELOCITY model (ACC =
accuracy; pval = p-value; AUC = area under curve). Areas with significant p-
values are in bold.

ROI

Left hIP1 IPS
Left hIP2 IPS
Left hIP3 IPS
Left Broca 44
Left IPL PF
Left IPL PFt
Left PO1 PIP
Left Premotor

6d1

ACC

54.89
53.26
55.98
52.72
51.63
58.15
54.08
53.80

ACC
pval

0.05
0.14
0.01
0.16
0.35
0.01
0.06
0.09

class 1
acc

56.52
51.09
61.96
54.89
53.8
60.87
64.67
51.63

class 2
acc

53.26
55.43
50.00
50.54
49.46
55.43
43.48
55.98

AUC

0.57
0.60
0.53
0.57
0.51
0.62
0.50
0.56

AUC
pval

0.04
0.02
0.22
0.06
0.43
0.01
0.52
0.08

Left Premotor

49.46

0.57

46.74

52.17

0.50

0.5

6d2

Left SPL 7A
Left SPL 7PC
Left Visual
hOc5

Right hIP1 IPS
Right hIP2 IPS
Right hIP3 IPS
Right Broca 44
Right IPL PF
Right IPL PFt
Right PO1 PIP
Right Premotor

6d1

52.17
55.16
57.88

54.89
54.08
58.42
47.83
49.18
47.83
51.90
55.16

0.16
0.08
0.01

0.05
0.10
0.01
0.78
0.69
0.78
0.18
0.04

62.50
63.04
69.02

57.07
52.17
63.59
52.72
55.98
52.72
59.78
54.35

41.85
47.28
46.74

52.72
55.98
53.26
42.93
42.39
42.93
44.02
55.98

0.50
0.58
0.66

0.59
0.59
0.66
0.49
0.48
0.47
0.59
0.62

0.49
0.06
0.01

0.01
0.03
0.01
0.69
0.74
0.68
0.02
0.01

Right Premotor

50.54

0.43

53.26

47.83

0.52

0.28

6d2

Right SPL 7A
Right SPL 7PC
Right Visual

hOc5

52.17
52.99
54.89

0.17
0.13
0.01

65.22
57.61
53.80

39.13
48.37
55.98

0.55
0.54
0.72

0.09
0.18
0.01

2016), slant and size of random dot stereograms (Ban & Welchman,
2012), as well as in the perception of the speed of gratings or dartboard
patterns (Gaglianese et al., 2023; Lingnau et al., 2009). This latter evi-
dence is also confirmed by studies using both repetitive and single-pulse

TMS, showing that after the stimulation of these areas, deficits in speed
perception emerge (Matthews et al., 2001; McKeefry et al., 2008). This
evidence, combined with the recruitment of this area in coding biolog-
ical motion (Peuskens et al., 2005; Saygin et al., 2004) and the fact that
MT/V5 in our study can encode distinct velocities of PLDs grasping
actions, suggests a role of this area in the elaboration of the velocity of
the observed biological movement.

In addition to visual areas, both multivariate network and single ROI
analyses show that premotor and parietal areas are involved in coding
stimulus velocity. However, the comparison of these two analyses also
reveals some differences. In fact, network analyses show a contribution
of PMv/IFG and SPL, which binary classification model accuracy is not
significant at a single ROI level. Note, however, that when single ROI
analysis is performed with a multiclass classification model, the accu-
racy of SPL is significant. This result on premotor and parietal cortex is
in line with previous literature showing that both superior parietal and
dorsal premotor areas modulate their activity during the observation of
a visible arm reaching a target with different velocities (Di Dio et al.,
2013). The present study extends these latter findings by showing that
premotor and parietal areas are also modulated by differences in the
velocity of reaching-grasping acts. Previous literature reported that ki-
nematics of observed arm movements is mainly encoded in dorsal pre-
motor cortex (Casile et al., 2010). Our data demonstrate that also
PMv/IFG contributes to the multikernel classification model. This
finding is not confirmed at ROI level. However, considering the evidence
that the whole premotor cortex is involved in grip configuration (Errante
et al., 2021a; Grafton & Hamilton, 2007), it is possible to suggest that
this sector plays a role in the encoding of action kinematic parameters,
such as velocity, within the AON. Notably, monkey studies focusing on
action execution demonstrated that muscimol injection in ventral pre-
motor cortex causes an impairment in grip configuration (Fogassi et al.,
2001) and a decrease of movement velocity (Fogassi et al., 2001; Kurata
& Hoffman, 1994).

Concerning parietal cortex, our data show that also the anterior and
ventral sectors of the IPS, which are connected with PMv/IFG both
anatomically (Borra et al., 2008; Luppino et al., 1999; Thiebaut de
Schotten et al., 2012) and functionally (Davare et al., 2011), play a role

11 

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

Fig. 7. Results of the multiclass GPC MVPA on single ROIs for the DIRECTION model. Histograms show the percentage of model accuracy (% ACC) in each region of
◦
interest. Red colored bars show the ROIs with a significant (*p < .05, **p < .01, ***p < .001) model accuracy assessed by means of a permutation testing (n
permutation = 100).

Table 8
Results of the multiclass GPC model classification analyses on single ROIs (ACC
= accuracy; pval = p-value; AUC = area under curve). Areas with significant p-
values are in bold.

ROI

ACC

Left hIP1 IPS
Left hIP2 IPS
Left hIP3 IPS
Left Broca 44
Left IPL PF
Left IPL PFt
Left PO1 PIP
Left Premotor

6d1

29.62
25.82
33.97
23.10
24.46
29.89
30.98
25.27

ACC
pval

0.01
0.39
0.01
0.77
0.61
0.03
0.01
0.68

class 1
acc

class 2
acc

class 3
acc

class 4
acc

26.09
31.52
20.65
27.17
18.48
27.17
19.57
15.22

41.30
23.91
41.30
10.87
44.57
23.91
42.39
47.83

42.39
35.87
57.60
29.35
6.52
46.74
51.09
32.61

8.70
11.96
16.30
25.00
28.26
21.74
10.87
5.43

Left Premotor

23.91

0.87

18.48

20.65

27.17

29.35

6d2

Left SPL 7A
Left SPL 7PC
Left Visual
hOc5

29.89
28.80
34.78

Right hIP1 IPS
Right hIP2

23.64
28.80

IPS

0.01
0.01
0.01

0.98
0.05

14.13
13.04
9.78

33.70
38.04

29.35
44.57
56.52

50.00
25

44.57
47.83
68.48

4.35
17.39

31.52
9.78
4.35

6.52
34.78

Right hIP3

29.35

0.01

42.39

11.96

17.39

45.65

27.45
26.63
32.34
34.51

0.18
0.19
0.01
0.01

54.35
43.48
41.30
53.26

31.52
8.70
7.61
15.22

16.30
41.30
38.04
15.22

7.61
13.04
42.39
54.35

26.90

0.24

34.78

18.48

26.09

28.26

23.37

0.71

29.35

31.52

19.57

13.04

IPS

Right Broca 44
Right IPL PF
Right IPL PFt
Right PO1

PIP
Right

Premotor
6d1
Right

Premotor
6d2

Right SPL 7A
Right SPL
7PC

Right Visual

hOc5

in coding differences in action velocity both at the network and ROI
level. Thus, the circuit connecting IPS with PMv/IFG may suggest that
these two areas within the AON can code not only type of grip and action
goal (Errante et al., 2021b), but also velocity kinematic features of
observed actions.

4.3. Representation of action kinematic features in parietal and premotor
areas of the AON

It is well known that areas belonging to the lateral occipito-temporal
cortex are involved in processing several features of biological move-
ment (Peuskens et al., 2005), thus one can hypothesize that they also
code differences in direction and velocity of grasping movement. The
findings of the present study that parieto-premotor AON areas could
code this type of kinematic features raises the question on the role of the
motor system in contributing to this elaboration during grasping
observation. Considering that these premotor and parietal areas are
nodes of the mirror neuron system, one can suggest that a kind of
matching mechanism occurs not only at the level of the goal of the motor
act or of the whole action, but also at the kinematic level. Programming
of motor acts also includes the setting of several kinematic parameters;
for example, for reaching an object, the direction and velocity of the arm
movement has to be correctly programmed. Thus, if individuals know
and employ these motor parameters for action execution, it is reasonable
that during observation of actions performed by another agent with the
same kinematic characteristics, they are able to recognize them because
these very same characteristics are matched on their own motor reper-
toire. Although in the present study we did not directly test the role of
direction and velocity in action recognition, future studies could address
this issue by investigating the role of AON areas during observation of
biological versus non biological stimuli characterized by different ki-
nematic parameters.

29.62
30.98

0.01
0.01

44.57
60.87

15.22
6.52

10.87
9.78

47.83
46.74

32.61

0.01

69.57

32.61

2.17

58.7

4.4. Limitations of the study

Some limitations must be considered in the interpretation of the
present results. First, since the focus of this work was on biological

12 

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

stimuli, in a future study we could try to also introduce non-biological
stimuli with different velocities and directions in order to verify
whether parietal and premotor cortex selectively process the kinematic
differences of biological versus non-biological movements.

Second, in this work we chose to manipulate the velocity rather than
the other parameters such as acceleration since the former was easier to
be varied in a naturalistic setting. Of course, since differences in velocity
profiles are intrinsically related to differences in acceleration profiles,
these latter could be coded within the AON.

Third, despite the central presentation of the stimuli and a general
bilateral activation of visual areas, a certain degree of lateralization was
observed. Future investigations could better clarify the role of AON in
coding action direction kinematic feature by introducing control con-
ditions aimed at investigating direction effect with stimuli completely
lateralized to the left or right hemifield.

Fourth, the L1 MKL classification method, by integrating information
from multiple brain regions, reveals how these regions collectively and
individually contribute to the decoding of stimuli features. On the one
hand, this is an advantage with respect to other techniques, such as local
multivariate searchlight approaches or post-hoc summarization of re-
gions weights. On the other hand, differences in the results can depend on
the selected regions with high correlated pattern of information. Other
limitations are related to the MKL classification technique. In fact, this
model does not include, at present, the possibility to use a criterion for
optimizing the hyperparameter, based on the expected ranking of brain
regions. Furthermore, as compared to MKL, a single ROI classification
approach is easier to interpret, but overemphasize the importance of a
single area while ignoring equally relevant regions. Thus, in this study,
we used a combination of both approaches to provide a more compre-
hensive picture of the contributions given by several brain regions.

5. Conclusions

Kinematic information conveyed by PLDs grasping actions activates
a wide set of occipito-temporal, parietal and premotor areas within the
action observation network. Using multivariate approaches based on
it was
both single ROI and multi-kernel classification algorithms,
possible to identify multiple sets of areas, within the AON, playing a
different role in decoding direction and velocity. Starting from these
data, it is possible to plan studies aimed at investigating how this in-
formation is exploited when individuals are required to imitate actions
based only on the kinematic parameters of the observed action.
Furthermore, the design of rehabilitation programs based on action
observation/imitation (Buccino, 2014; Errante et al., 2024; Franceschini
et al., 2012; Pelosin et al., 2010; Sgandurra et al., 2013; Verzelloni et al.,
2021) might be shaped by these findings as well. Finally, the present
results could also be exploited for improving hand actions recognition
and classification models based on machine learning (Zhang et al.,
2020), by extracting the most relevant kinematic features from the
analysis of the observed actions. These features could then be used to
develop artificial intelligence systems capable of understanding and
generating actions in a realistic and natural way.

Ethics approval statement

The study was approved by the local ethics committee (Comitato
Etico Area Vasta Emilia Nord - AVEN; code NEUROIMAGE_UNIPR). This
study was carried out in accordance with The Code of Ethics of the
World Medical Association (Declaration of Helsinki).

CRediT authorship contribution statement

Settimio Ziccarelli: Writing – review & editing, Writing – original
draft, Visualization, Investigation, Formal analysis, Conceptualization.
Antonino Errante: Writing – review & editing, Conceptualization.
Leonardo Fogassi: Writing – review & editing, Conceptualization.

Declaration of competing interest

The authors declare no competing financial or non-financial

interests.

Acknowledgements

This work was supported by a grant of the Italian Ministry of Uni-
versity and Research (MIUR) [code: PRIN2020, Prot. 20208RB4N9] and
#NEXTGENERATIONEU (NGEU) and funded by the Ministry of Uni-
versity and Research (MUR), National Recovery and Resilience Plan
(NRRP), project MNESYS (PE0000006) – A Multiscale integrated
approach to the study of the nervous system in health and disease [code:
DN.1553, 11.10.2022].

Supplementary materials

Supplementary material associated with this article can be found, in

the online version, at doi:10.1016/j.neuroimage.2024.120939.

Data availability

The data of the present study can be made available on request from

the corresponding author, with a formal data sharing agreement.

References

Abdelgabar, A.R., Suttrup, J., Broersen, R., Bhandari, R., Picard, S., Keysers, C., De
Zeeuw, C.I., Gazzola, V., 2019. Action perception recruits the cerebellum and is
impaired in patients with spinocerebellar ataxia. Brain 142 (12), 3791–3805.
https://doi.org/10.1093/brain/awz337.

Andersen, R.A., Snyder, L.H., Batista, A.P., Buneo, C.A., Cohen, Y.E., 2007. Posterior
Parietal Areas Specialized for Eye Movements (Lip) and Reach (PRR) Using a
Common Coordinate Frame. Novartis Foundation Symposium 218 - Sensory
Guidance of Movement, pp. 109–128. https://doi.org/10.1002/9780470515563.
ch7.

Ban, H., Welchman, A.E., 2012. Distributed representations for 3D perceptual judgments

in human visual cortex. J. Vis. 12 (9), 1040-1040.

Beauchamp, M.S., Lee, K.E., Haxby, J.V., Martin, A., 2003. FMRI responses to video and
point-light displays of moving humans and manipulable objects. J. Cogn. Neurosci.
15 (7), 991–1001. https://doi.org/10.1162/089892903770007380.

Beckers, G., Zeki, S., 1995. The consequences of inactivating areas V1 and V5 on visual
motion perception. Brain 118 (Pt 1), 49–60. https://doi.org/10.1093/brain/
118.1.49.

Bidet-Ildei, C., Francisco, V., Decatoire, A., Pylouster, J., Blandin, Y., 2023. PLAViMoP
database: a new continuously assessed and collaborative 3D point-light display
dataset. Behav. Res. Methods 55 (2), 694–715. https://doi.org/10.3758/s13428-
022-01850-3.

Blake, R., Shiffrar, M., 2007. Perception of human motion. Annu. Rev. Psychol. 58,

47–73. https://doi.org/10.1146/annurev.psych.57.102904.190152.

Blanke, O., Landis, T., Mermoud, C., Spinelli, L., Safran, A.B., 2003. Direction-selective
motion blindness after unilateral posterior brain damage. Eur. J. Neurosci. 18 (3),
709–722. https://doi.org/10.1046/j.1460-9568.2003.02771.x.

Borra, E., Belmalih, A., Calzavara, R., Gerbella, M., Murata, A., Rozzi, S., Luppino, G.,

2008. Cortical connections of the macaque anterior intraparietal (AIP) area. Cereb.
Cortex. 18 (5), 1094–1111. https://doi.org/10.1093/cercor/bhm146.

Bracci, S., de Beeck, H.O., 2016. Dissociations and associations between shape and

category representations in the two visual pathways. J. Neurosci. 36 (2), 432–444.

Buccino, G., 2014. Action observation treatment: a novel tool in neurorehabilitation.
Philos. Trans. R. Soc. Lond. B Biol. Sci. 369 (1644), 20130185. https://doi.org/
10.1098/rstb.2013.0185.

Cardin, V., Sherrington, R., Hemsworth, L., Smith, A.T., 2012. Human V6: functional
characterisation and localisation. PLoS. One 7 (10), e47685. https://doi.org/
10.1371/journal.pone.0047685.

Casile, A., Dayan, E., Caggiano, V., Hendler, T., Flash, T., Giese, M.A., 2010. Neuronal
encoding of human kinematic invariants during action observation. Cereb. Cortex 20
(7), 1647–1655. https://doi.org/10.1093/cercor/bhp229.

Caspers, S., Zilles, K., Laird, A.R., Eickhoff, S.B., 2010. ALE meta-analysis of action
observation and imitation in the human brain. Neuroimage 50 (3), 1148–1167.
https://doi.org/10.1016/j.neuroimage.2009.12.112.

Cavina-Pratesi, C., Monaco, S., Fattori, P., Galletti, C., McAdam, T.D., Quinlan, D.J.,

Goodale, M.A., Culham, J.C., 2010. Functional magnetic resonance imaging reveals
the neural substrates of arm transport and grip formation in reach-to-grasp actions in
humans. J. Neurosci. 30 (31), 10306–10323. https://doi.org/10.1523/
JNEUROSCI.2023-10.2010.

Chouchourelou, A., Matsuka, T., Harber, K., Shiffrar, M., 2006. The visual analysis of

emotional actions. Soc. Neurosci. 1 (1), 63–74. https://doi.org/10.1080/
17470910600630599.

13 

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

Cohen, Y.E., Andersen, R.A., 2002. A common reference frame for movement plans in the
posterior parietal cortex. Nat. Rev. Neurosci. 3 (7), 553–562. https://doi.org/
10.1038/nrn873.

Davare, M., Kraskov, A., Rothwell, J.C., Lemon, R.N., 2011. Interactions between areas of
the cortical grasping network. Curr. Opin. Neurobiol. 21 (4), 565–570. https://doi.
org/10.1016/j.conb.2011.05.021.

Davare, M., Zenon, A., Pourtois, G., Desmurget, M., Olivier, E., 2012. Role of the medial
part of the intraparietal sulcus in implementing movement direction. Cereb. Cortex
22 (6), 1382–1394. https://doi.org/10.1093/cercor/bhr210.

Di Dio, C., Di Cesare, G., Higuchi, S., Roberts, N., Vogt, S., Rizzolatti, G., 2013. The
neural correlates of velocity processing during the observation of a biological
effector in the parietal and premotor cortex. Neuroimage 64, 425–436. https://doi.
org/10.1016/j.neuroimage.2012.09.026.

Eickhoff, S.B., Stephan, K.E., Mohlberg, H., Grefkes, C., Fink, G.R., Amunts, K., Zilles, K.,
2005. A new SPM toolbox for combining probabilistic cytoarchitectonic maps and
functional imaging data. Neuroimage 25 (4), 1325–1335. https://doi.org/10.1016/j.
neuroimage.2004.12.034.

Hamilton, A.F., Grafton, S.T., 2006. Goal representation in human anterior intraparietal
sulcus. J. Neurosci. 26 (4), 1133–1137. https://doi.org/10.1523/JNEUROSCI.4551-
05.2006.

Hamilton, A., Grafton, S.T., 2007. The motor hierarchy: from kinematics to goals and
intentions. Sensorimotor foundations of higher cognition, 22, pp. 381–408.
Hardwick, R.M., Caspers, S., Eickhoff, S.B., Swinnen, S.P., 2018. Neural correlates of

action: Comparing meta-analyses of imagery, observation, and execution. Neurosci.
Biobehav. Rev. 94, 31–44. https://doi.org/10.1016/j.neubiorev.2018.08.003.
Johansson, G., 1973. Visual perception of biological motion and a model for its analysis.
Percept. Psychophys. 14 (2), 201–211. https://doi.org/10.3758/BF03212378.
Kamitani, Y., Tong, F., 2006. Decoding seen and attended motion directions from activity
in the human visual cortex. Current biol. 16 (11), 1096–1102. https://doi.org/
10.1016/j.cub.2006.04.003.

Kemmerer, D., 2021. What modulates the mirror neuron system during action

observation?: multiple factors involving the action, the actor, the observer, the
relationship between actor and observer, and the context. Prog. Neurobiol. 205,
102128. https://doi.org/10.1016/j.pneurobio.2021.102128.

Errante, A., Fogassi, L., 2020. Activation of cerebellum and basal ganglia during the

Kurata, K., Hoffman, D.S., 1994. Differential effects of muscimol microinjection into

observation and execution of manipulative actions. Sci. Rep. 10 (1), 12008. https://
doi.org/10.1038/s41598-020-68928-w.

dorsal and ventral aspects of the premotor cortex of monkeys. J. Neurophysiol. 71
(3), 1151–1164. https://doi.org/10.1152/jn.1994.71.3.1151.

Errante, A., Ziccarelli, S., Mingolla, G.P., Fogassi, L., 2021a. Decoding grip type and

action goal during the observation of reaching-grasping actions: A multivariate fMRI
study. Neuroimage 243, 118511. https://doi.org/10.1016/j.
neuroimage.2021.118511.

Errante, A., Ziccarelli, S., Mingolla, G., Fogassi, L., 2021b. Grasping and manipulation:
neural bases and anatomical circuitry in humans. Neuroscience 458, 203–212.
https://doi.org/10.1016/j.neuroscience.2021.01.028.

Errante, A., Beccani, L., Verzelloni, J., Maggi, I., Filippi, M., Bressi, B., Ziccarelli, S.,

Bozzetti, F., Costi, S., Ferrari, A., 2024. Effectiveness of action observation treatment
based on pathological model in hemiplegic children: a randomized-controlled trial.
Eur. J. Phys. Rehabil. Med. 60 (4), 643. https://doi.org/10.23736/S1973-
9087.24.08413-2.

Eskandar, E.N., Assad, J.A., 2002. Distinct nature of directional signals among parietal
cortical areas during visual guidance. J. Neurophysiol. 88 (4), 1777–1790. https://
doi.org/10.1152/jn.2002.88.4.1777.

Filimon, F., 2010. Human cortical control of hand movements: parietofrontal networks
for reaching, grasping, and pointing. Neuroscientist. 16 (4), 388–407. https://doi.
org/10.1177/1073858410375468.

Lingnau, A., Ashida, H., Wall, M.B., Smith, A.T., 2009. Speed encoding in human visual
cortex revealed by fMRI adaptation. J. Vis. 9 (13). https://doi.org/10.1167/9.13.3, 3
1-14.

Luppino, G., Murata, A., Govoni, P., Matelli, M., 1999. Largely segregated parietofrontal
connections linking rostral intraparietal cortex (areas AIP and VIP) and the ventral
premotor cortex (areas F5 and F4). Exp. Brain Res. 128 (1-2), 181–187. https://doi.
org/10.1007/s002210050833.

Matthews, N., Luber, B., Qian, N., Lisanby, S.H., 2001. Transcranial magnetic stimulation
differentially affects speed and direction judgments. Exp. Brain Res. 140 (4),
397–406. https://doi.org/10.1007/s002210100837.

Maunsell, J.H., Van Essen, D.C., 1983. Functional properties of neurons in middle

temporal visual area of the macaque monkey. I. Selectivity for stimulus direction,
speed, and orientation. J. Neurophysiol. 49 (5), 1127–1147. https://doi.org/
10.1152/jn.1983.49.5.1127.

McKeefry, D.J., Burton, M.P., Vakrou, C., Barrett, B.T., Morland, A.B., 2008. Induced

deficits in speed perception by transcranial magnetic stimulation of human cortical
areas V5/MT+ and V3A. J. Neurosci. 28 (27), 6848–6857. https://doi.org/10.1523/
JNEUROSCI.1287-08.2008.

Filimon, F., Nelson, J.D., Hagler, D.J., Sereno, M.I., 2007. Human cortical

Molenberghs, P., Cunnington, R., Mattingley, J.B., 2012. Brain regions with mirror

representations for reaching: mirror neurons for execution, observation, and
imagery. Neuroimage 37 (4), 1315–1328. https://doi.org/10.1016/j.
neuroimage.2007.06.008.

properties: a meta-analysis of 125 human fMRI studies. Neurosci. Biobehav. Rev. 36
(1), 341–349. https://doi.org/10.1016/j.neubiorev.2011.07.004.

Monaco, S., Cavina-Pratesi, C., Sedda, A., Fattori, P., Galletti, C., Culham, J.C., 2011.

Filimon, F., Nelson, J.D., Huang, R.S., Sereno, M.I., 2009. Multiple parietal reach regions

in humans: cortical representations for visual and proprioceptive feedback during
on-line reaching. J. Neurosci. 29 (9), 2961–2971. https://doi.org/10.1523/
JNEUROSCI.3211-08.2009.

Fogassi, L., Gallese, V., Buccino, G., Craighero, L., Fadiga, L., Rizzolatti, G., 2001.

Cortical mechanism for the visual guidance of hand grasping movements in the
monkey: a reversible inactivation study. Brain 124 (Pt 3), 571–586. https://doi.org/
10.1093/brain/124.3.571.

Franceschini, M., Ceravolo, M.G., Agosti, M., Cavallini, P., Bonassi, S., Dall’Armi, V.,

Massucci, M., Schifini, F., Sale, P., 2012. Clinical relevance of action observation in
upper-limb stroke rehabilitation: a possible role in recovery of functional dexterity.
A randomized clinical trial. Neurorehabil. Neural Repair. 26 (5), 456–462. https://
doi.org/10.1177/1545968311427406.

Friston, K.J., Glaser, D.E., Henson, R.N., Kiebel, S., Phillips, C., Ashburner, J., 2002.

Classical and Bayesian inference in neuroimaging: applications. Neuroimage 16 (2),
484–512. https://doi.org/10.1006/nimg.2002.1091.

Friston, K.J., Holmes, A.P., Price, C.J., Buchel, C., Worsley, K.J., 1999. Multisubject fMRI
studies and conjunction analyses. Neuroimage 10 (4), 385–396. https://doi.org/
10.1006/nimg.1999.0484.

Gaglianese, A., Fracasso, A., Fernandes, F.G., Harvey, B., Dumoulin, S.O., Petridou, N.,

2023. Mechanisms of speed encoding in the human middle temporal cortex
measured by 7T fMRI. Hum. Brain Mapp. 44 (5), 2050–2061. https://doi.org/
10.1002/hbm.26193.

Functional magnetic resonance adaptation reveals the involvement of the
dorsomedial stream in hand orientation for grasping. J. Neurophysiol. 106 (5),
2248–2263. https://doi.org/10.1152/jn.01069.2010.

Oldfield, R.C., 1971. The assessment and analysis of handedness: the Edinburgh

inventory. Neuropsychologia 9 (1), 97–113. https://doi.org/10.1016/0028-3932
(71)90067-4.

Orban, G.A., Claeys, K., Nelissen, K., Smans, R., Sunaert, S., Todd, J.T., Wardak, C.,

Durand, J.B., Vanduffel, W., 2006. Mapping the parietal cortex of human and non-
human primates. Neuropsychologia 44 (13), 2647–2667.

Pavlova, M.A., 2012. Biological motion processing as a hallmark of social cognition.

Cereb. Cortex. 22 (5), 981–995. https://doi.org/10.1093/cercor/bhr156.

Peelen, M.V., Wiggett, A.J., Downing, P.E., 2006. Patterns of fMRI activity dissociate

overlapping functional brain areas that respond to biological motion. Neuron 49 (6),
815–822. https://doi.org/10.1016/j.neuron.2006.02.004.

Pelosin, E., Avanzino, L., Bove, M., Stramesi, P., Nieuwboer, A., Abbruzzese, G., 2010.
Action observation improves freezing of gait in patients with Parkinson’s disease.
Neurorehabil. Neural Repair. 24 (8), 746–752. https://doi.org/10.1177/
1545968310368685.

Peuskens, H., Vanrie, J., Verfaillie, K., Orban, G.A., 2005. Specificity of regions

processing biological motion. Eur. J. Neurosci. 21 (10), 2864–2875. https://doi.org/
10.1111/j.1460-9568.2005.04106.x.

Pitzalis, S., Fattori, P., Galletti, C., 2015. The human cortical areas V6 and V6A. Vis.

Neurosci. 32, E007. https://doi.org/10.1017/S0952523815000048.

Gallivan, J.P., Cavina-Pratesi, C., Culham, J.C., 2009. Is that within reach? fMRI reveals

Pitzalis, S., Sereno, M.I., Committeri, G., Fattori, P., Galati, G., Patria, F., Galletti, C.,

that the human superior parieto-occipital cortex encodes objects reachable by the
hand. J. Neurosci. 29 (14), 4381–4391. https://doi.org/10.1523/JNEUROSCI.0377-
09.2009.

Gazzola, V., Keysers, C., 2009. The observation and execution of actions share motor and

somatosensory voxels in all tested subjects: single-subject analyses of unsmoothed
fMRI data. Cereb. Cortex. 19 (6), 1239–1255. https://doi.org/10.1093/cercor/
bhn181.

Grafton, S.T., Hamilton, A.F., 2007. Evidence for a distributed hierarchy of action
representation in the brain. Hum. Mov. Sci. 26 (4), 590–616. https://doi.org/
10.1016/j.humov.2007.05.009.

Grefkes, C., Fink, G.R., 2005. The functional organization of the intraparietal sulcus in
humans and monkeys. J. Anat. 207 (1), 3–17. https://doi.org/10.1111/j.1469-
7580.2005.00426.x.

Grefkes, C., Ritzl, A., Zilles, K., Fink, G.R., 2004. Human medial intraparietal cortex

subserves visuomotor coordinate transformation. Neuroimage 23 (4), 1494–1506.
https://doi.org/10.1016/j.neuroimage.2004.08.031.

Grefkes, C., Weiss, P.H., Zilles, K., Fink, G.R., 2002. Crossmodal processing of object

features in human anterior intraparietal cortex: an fMRI study implies equivalencies
between humans and monkeys. Neuron 35 (1), 173–184. https://doi.org/10.1016/
s0896-6273(02)00741-9.

2010. Human v6: the medial motion area. Cereb. Cortex. 20 (2), 411–424. https://
doi.org/10.1093/cercor/bhp112.

Pitzalis, S., Sereno, M.I., Committeri, G., Fattori, P., Galati, G., Tosoni, A., Galletti, C.,
2013. The human homologue of macaque area V6A. Neuroimage 82, 517–530.
https://doi.org/10.1016/j.neuroimage.2013.06.026.

Prado, J., Clavagnier, S., Otzenberger, H., Scheiber, C., Kennedy, H., Perenin, M.T., 2005.
Two cortical systems for reaching in central and peripheral vision. Neuron 48 (5),
849–858. https://doi.org/10.1016/j.neuron.2005.10.010.

Priebe, N.J., Cassanello, C.R., Lisberger, S.G., 2003. The neural representation of speed in
macaque area MT/V5. J. Neurosci. 23 (13), 5650–5661. https://doi.org/10.1523/
JNEUROSCI.23-13-05650.2003.

Sack, A.T., Kohler, A., Linden, D.E.J., Goebel, R., Muckli, L., 2006. The temporal
characteristics of motion processing in hMT/V5+: combining fMRI and
neuronavigated TMS. Neuroimage 29 (4), 1326–1335. https://doi.org/10.1016/j.
neuroimage.2005.08.027.

Saygin, A.P., Wilson, S.M., Hagler Jr., D.J., Bates, E., Sereno, M.I, 2004. Point-light

biological motion perception activates human premotor cortex. J. Neurosci. 24 (27),
6181–6188. https://doi.org/10.1523/JNEUROSCI.0504-04.2004.

Scheperjans, F., Eickhoff, S.B., Homke, L., Mohlberg, H., Hermann, K., Amunts, K.,

Zilles, K., 2008. Probabilistic maps, morphometry, and variability of

14 

S. Ziccarelli et al.

NeuroImage 303 (2024) 120939 

cytoarchitectonic areas in the human superior parietal cortex. Cereb. Cortex. 18 (9),
2141–2157. https://doi.org/10.1093/cercor/bhm241.

Scheperjans, F., Hermann, K., Eickhoff, S.B., Amunts, K., Schleicher, A., Zilles, K., 2008.
Observer-independent cytoarchitectonic mapping of the human superior parietal
cortex. Cereb. Cortex. 18 (4), 846–867. https://doi.org/10.1093/cercor/bhm116.
Schrouff, J., Monteiro, J.M., Portugal, L., Rosa, M.J., Phillips, C., Mourao-Miranda, J.,
2018. Embedding anatomical or functional knowledge in whole-brain multiple
kernel learning models. Neuroinformatics. 16 (1), 117–143. https://doi.org/
10.1007/s12021-017-9347-8.

Schrouff, J., Mourao-Miranda, J., Phillips, C., Parvizi, J., 2016. Decoding intracranial

EEG data with multiple kernel learning method. J. Neurosci. Methods 261, 19–28.
https://doi.org/10.1016/j.jneumeth.2015.11.028.

Sgandurra, G., Ferrari, A., Cossu, G., Guzzetta, A., Fogassi, L., Cioni, G., 2013.

Randomized trial of observation and execution of upper extremity actions versus
action alone in children with unilateral cerebral palsy. Neurorehabil. Neural Repair.
27 (9), 808–815. https://doi.org/10.1177/1545968313497101.

Shim, J., Carlton, L.G., Kim, J., 2004. Estimation of lifted weight and produced effort

through perception of point-light display. Perception. 33 (3), 277–291. https://doi.
org/10.1068/p3434.

Thiebaut de Schotten, M., Dell’Acqua, F., Valabregue, R., Catani, M., 2012. Monkey to
human comparative anatomy of the frontal lobe association tracts. Cortex 48 (1),
82–96. https://doi.org/10.1016/j.cortex.2011.10.001.

Thornton, I.M., 2006. Biological motion: point-light walkers and beyond. Human Body
Perception from the Inside out: Advances in Visual Cognition. Oxford University
Press, pp. 271–303.

Ulloa, E.R., Pineda, J.A., 2007. Recognition of point-light biological motion: mu rhythms
and mirror neuron activity. Behav. Brain Res. 183 (2), 188–194. https://doi.org/
10.1016/j.bbr.2007.06.007.

van Kemenade, B.M., Muggleton, N., Walsh, V., Saygin, A.P., 2012. Effects of TMS over
premotor and superior temporal cortices on biological motion perception. J. Cogn.
Neurosci. 24 (4), 896–904. https://doi.org/10.1162/jocn_a_00194.

Verzelloni, J., Errante, A., Beccani, L., Filippi, M., Bressi, B., Cavuto, S., Ziccarelli, S.,

Bozzetti, F., Costi, S., Pineschi, E., Fogassi, L., Ferrari, A., 2021. Can a pathological
model improve the abilities of the paretic hand in hemiplegic children? The PAM-
AOT study protocol of a randomised controlled trial. BMJ Open. 11 (12). https://doi.
org/10.1136/bmjopen-2021-053910. ARTN e053910.

Zaini, H., Fawcett, J.M., White, N.C., Newman, A.J., 2013. Communicative and

noncommunicative point-light actions featuring high-resolution representation of
the hands and fingers. Behav. Res. Methods 45 (2), 319–328. https://doi.org/
10.3758/s13428-012-0273-2.

Zeki, S., Watson, J.D., Lueck, C.J., Friston, K.J., Kennard, C., Frackowiak, R.S., 1991.
A direct demonstration of functional specialization in human visual cortex.
J. Neurosci. 11 (3), 641–649. https://doi.org/10.1523/JNEUROSCI.11-03-
00641.1991.

Zhang, F., Bazarevsky, V., Vakunov, A., Tkachenka, A., Sung, G., Chang, C.L.,

Grundmann, M., 2020. Mediapipe hands: On-device real-time hand tracking. arXiv
preprint arXiv:2006.10214.

Ziccarelli, S., Errante, A., Fogassi, L., 2022. Decoding point-light displays and fully

visible hand grasping actions within the action observation network. Hum. Brain
Mapp. 43 (14), 4293–4309. https://doi.org/10.1002/hbm.25954.

15 

