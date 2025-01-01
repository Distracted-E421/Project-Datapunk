NeuroImage 303 (2024) 120941 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Control energy detects discrepancies in good vs. poor readers’
structural-functional coupling during a rhyming task

Chenglin Lou a,b,c,*, Marc F. Joanisse b,c,d
a Department of Special Education, Peabody College of Education, Vanderbilt University, Nashville, TN, USA
b Department of Psychology, The University of Western Ontario, London, Canada
c Brain and Mind Institute, The University of Western Ontario, London, Canada
d Haskins Laboratories, New Haven CT, USA

A R T I C L E I N F O

A B S T R A C T

Keywords:
Rhyming task
Control energy
DTI
fMRI
Reading

Neuroimaging studies have identified functional and structural brain circuits that support reading. However,
much less is known about how reading-related functional dynamics are constrained by white matter structure.
Network control theory proposes that cortical brain dynamics are linearly determined by the white matter
connectome, using control energy to evaluate the difficulty of the transition from one cognitive state to another.
Here we apply this approach to linking brain dynamics with reading ability and disability in school-age children.
A total of 51 children ages 8.25 -14.6 years performed an in-scanner rhyming task in visual and auditory mo-
dalities, with orthographic (spelling) and phonological (rhyming) similarity manipulated across trials. White
matter structure and fMRI activation were used conjointly to compute the control energy of the reading network
in each condition relative to a null fixation state. We then tested differences in control energy across trial types,
finding higher control energy during non-word trials than word trials, and during incongruent trials than
congruent trials. ROI analyses further showed a dissociation between control energy of the left fusiform and
superior temporal gyrus depending on stimulus modality, with higher control energy for visual modalities in
fusiform and higher control energy for auditory modalities in STG. Together, this study highlights that control
theory can explain variations on cognitive demands in higher-level abilities such as reading, beyond what can be
inferred from either functional or structural MRI measures alone.

1. Introduction

Reading is a complex cognitive function in which readers must
derive the sound and meaning of a visual input using both language-
specific information as well as more general perceptual and executive
resources. Unsurprisingly then, a widespread set of brain areas are
involved in reading, forming a recognized reading network (Price, 2012;
Pugh et al., 2000) with activation states of this network changing as a
function of reading processes (Fiez and Petersen, 1998). In addition,
white matter connections within the reading network are also associated
with reading functions (Vandermosten et al., 2012), assisting in passing
information among its component cortical and subcortical regions
(Ben-Shachar Dougherty and Wandell, 2007).

Within the reading network,

the structure-function linkage in
reading has been represented as correlations between white matter

connectivity and reading performance at a cognitive level, measured by
standardized reading scores that
index various reading subskills
(Stienbrink et al., 2008; Vandermosten et al., 2012; Yeatman et al.,
2012; Zhao et al., 2016; Cross et al., 2023; Sihvonen et al., 2021).
Likewise, regional functional activity within this reading network could
also represent the neural correlates of various reading sub-processes
(Bolger et al., 2008; Cross et al., 2021; Xia et al., 2018). That said,
there is somewhat more limited evidence demonstrating direct associ-
ations between structural white matter connectivity and functional
activation within the grey matter. Thus, our understanding of how the
neural representation of reading processes is constrained by the struc-
ture of the brain remains somewhat limited. There have been studies
that explored associations between structural and functional connec-
tions in learning-related systems, such as attention and memory (Bells
et al., 2017; Alonso et al., 2024). However, the anatomical and

* Corresponding author at: Peabody College of Education and Human Development, Vanderbilt University, 230 Appleton Place, PMB 328, Nashville, Tennessee TN

37203, USA

E-mail address: chenglin.lou@vanderbilt.edu (C. Lou).

https://doi.org/10.1016/j.neuroimage.2024.120941
Received 29 April 2024; Received in revised form 8 November 2024; Accepted 16 November 2024
Available online 17 November 2024 
1053-8119/© 2024 The Authors.  Published by Elsevier Inc.  This is an open access article under the CC BY-NC license ( http://creativecommons.org/licenses/by- 
nc/4.0/ ). 

C. Lou and M.F. Joanisse

NeuroImage 303 (2024) 120941 

functional phenomena are generally studied in isolation from each
other, leaving under-explored the specific ways that structural connec-
tions constrain the state dynamics of those areas.

It is generally understood that the organization of the brain’s struc-
tural wiring pattern generally manipulates structure-function relation-
ships (Hermundstad et al., 2013; Honey et al., 2009) and constrains the
neural reconfiguration for state changes (Cabral et al., 2017; Her-
mundstad et al., 2014; Shine et al., 2019; Tang et al., 2017). In some
cases this is straightforward, with studies showing that functional con-
nectivity within specific systems (e.g., default mode network), is asso-
ciated with the strength of its component white matter connections
(Khalsa, Mayhew et al., 2014; Teipel et al., 2010; Van Den Heuvel et al.,
2008). However, the whole brain is sparsely connected by white matter
tracts, with most apparent functional connections having no direct
physical basis. Therefore, a functional activation pattern may arise via
indirect structural connectivity, meaning the structure-function inter-
play unfolds at the complex network level (Su´arez et al., 2020; Wang
et al., 2015).

To this end, studies examining white matter connections in the
background of the whole-brain network have found reading skills are
associated with not only the white matter network (Bathelt et al., 2018;
T. Liu et al., 2021; Lou et al., 2021,2024; Lou et al., 2019), but also the
functional network in both resting-state and specific reading tasks
(Bailey et al., 2018; Finn et al., 2014; X. Liu et al., 2018; Vogel et al.,
2013; Zhou et al., 2021). Network-wise brain activity patterns represent
distinct modes of information processing (Barch et al., 2013), observed
both at rest and during specific cognitive processing (Karahano˘glu and
Van De Ville, 2017; Saggar et al., 2018).

Recently, control theory has been applied to model the functional
reconfiguration of the brain as a linear function of the white matter
network and regional control energy, which evaluates network-
constrained changes of fMRI activity via a set of control regions (Gu
et al., 2015; Kim et al., 2018). Therefore, functional MRI contrast maps
for various cognitive loadings or tasks can be explained based on static
anatomical determinants, and the amount of effort that the connectome
must exert to complete the transition is control energy (Parkes et al.,
2024). In addition, the amount of control energy may also reflect a
corresponding cognitive load and the change of functional activation
that is constrained by a whole-brain white matter network. For example,
in a study investigating control energy for working memory tasks, Braun
et al. (2021) revealed that state transition from cognitively less
demanding to more demanding tasks required more control energy than
the reverse transition. It suggested that brain states of high cognitive
effort were harder to access.

That said, it is less clear how such findings apply to more complex
multisensory cognitive tasks such as those implicated in oral and written
language processing. In the present work we focus on reading, which
involves the coordination of multiple types of auditory and visual in-
formation. We hypothesize that moment-by-moment functional recon-
figuration for varying task demands may be a consequence of the effect
of control, and the amount of control energy could be an indicator of
task complexity. To test this, the present study estimated control energy
among various conditions of an in-scanner rhyming judgment task in a
sample of school age children of varying reading abilities (Lytle et al.,
2019).

The present study chose a rhyming task because it captures phono-
logical processing, as well as orthography-to-phonology mapping pro-
cesses in visual word recognition.
Importantly, the rhyming task
included multiple conditions that placed higher demands on the reading
system, which could potentially be reflected on the control process in the
brain. Specifically, orthographic and phonological similarity are pro-
posed to play a priming effect in which a word is more easily accessed
when immediately preceded by a rhyme, thanks to spreading activation
among words that share a rhyming relationship (Desroches et al., 2009).
Likewise, spelling-sound conflict among rhyming words (coat-note) is
proposed to interfere with a phonological rhyme judgement due to

(spoken) phonology is

top-down visual information that makes it more difficult to correctly
associate rhyming words with one another (Coch et al., 2008). Critically,
auditory and visual rhyming has emerged as an important measures of
reading skill, given that it captures important variance in skilled reading
development (e.g., Treiman et al., 1995). There are two reasons for this:
first,
to forming accurate
letter-sound associations during reading development, and this can be
especially important for rhymes, which extend above the level of indi-
vidual segments. Second, orthographic learning in an alphabetic code
requires associating not just individual letters and sounds, but also
discovering how multi-letter orthographic units can be consistently
associated with phonological rhymes (e.g., words ending in EEL gener-
ally map onto the /il/ rhyme pattern).

foundational

There is

likewise a well-established neuroimaging literature
exploring the privileged role of rhymes in children’s spoken and written
language (see Enge et al., 2020) for a review. Results demonstrate that
rhyme processing activates key perisylvian regions including IFG, STG
and MTG involved in phonological processing, that children show
developmental effects in how these activation patterns emerge, and that
this mirroring their reading development (e.g., Cone et al., 2008,
Welcome and Joanisse., 2018; Coch et al., 2008). Of particular note,
manipulating spelling-sound congruency during rhyme judgment re-
veals automatic activation of visual-orthographic brain regions during
spoken language recognition in children, and the strength of such effects
again appears to reflect their reading achievement (Desroches et al.,
2010).

(e.g.,

In addition to examining how control energy can explain structure-
function coupling during rhyming, we also focused on how region-
wise control energy might vary as a function of task demands. If con-
trol theory explains functional reconfiguration of specific cognitive
abilities, the control energy of functional activation changes for different
reading task loads should be distinct. Specifically, psycholinguistically
more complex rhyme judgments
trials when incongruent
phonology and orthography such as coat-note or dough-rough) should
require more control energy to achieve a required functional activation
state. In addition, the amount of required control energy in specific re-
gions of interest (ROIs) may be different depending on types of cognitive
demands being engaged by specific tasks (Braun et al., 2021; Cui et al.,
2020; Gu et al., 2015). Hence, the present study selected two ROIs in the
left hemisphere known to contribute to different aspects of reading: the
left fusiform, which engages in processing visual-orthographic infor-
mation (McCandliss et al., 2003; Price, 2012) and the left superior
temporal gyrus (STG), which is involved in auditory-phonological pro-
cessing (Booth et al., 2001; Jobard et al., 2003; Martin et al., 2015). We
examined potential dissociations in the required energy of the two
functionally specific ROIs across the rhyming judgment task, supporting
a region-specific model in which energy costs in different ROIs reflect
functionally distinct reading processes.

2. Methods

2.1. Participants

Data from this study were drawn from an open-access dataset (Lytle
et al., 2019) of task-based fMRI and diffusion-weighted (DW) scans ac-
quired longitudinally from 188 children. All procedures and protocols
for this dataset were approved by the Institutional Review Board at
Northwestern University. Our analyses considered Time 1 data from 112
children for which both fMRI and DW datasets were available (only
Time 1 data were examined as we are not considering longitudinal ef-
fects). All datasets were quality-checked including removal of
movement-laden DW and fMRI scans, as detailed in Lytle et al. (2019).
As an additional step, we applied motion corrections for DW and fMR
images wherein any volumes that showed head motion amplitude higher
◦
than 3 mm translation or 3
rotation along any of the six dimensions
were removed; on this basis 16 participants were excluded due to more

2 

C. Lou and M.F. Joanisse

NeuroImage 303 (2024) 120941 

than 10 DW volumes being removed and no participants were excluded
due to more than 25 % of fMRI volumes were removed. Regarding the
fMRI, we removed 15 individuals for whom scans omitted portions of
the cerebrum, as the present study aimed to investigate the whole-brain
connectome and activation. Also, since the present study focused on
accurately answered trials, 22 participants for whom no response ac-
curacy was recorded were excluded. Another 8 participants were
excluded from analyses, as at least one of their in-scanner task runs were
not completed. After this screening, 51 participants remained for in-
clusion. These participants ranged in age from 8.25 to 14.25 years (M =
11.06, SD = 1.75), with 24 boys and 27 girls. All were right-handed
native English speakers. None had a history of psychiatric illness,
neurological disease, attention deficit hyperactivity disorder (ADHD),
prematurity of fewer than 36 weeks, significant hearing loss, medication
affecting central nervous system processing, or contraindications for
MRI as reported by their parent/guardian.

2.2. Behavioral measurement

Participants completed a series of standardized psycho-educational
assessments to measure a variety of cognitive abilities at the time of
scanning. Although multiple assessments were acquired, the present
study focused on two subtests of the Test of Word Reading Efficiency
(TOWRE) (Torgesen et al., 1999), Sight Word Efficiency and Phonemic
Decoding Efficiency, for brain-behavior analyses. These were selected as
they evaluated the ability to read aloud familiar words (TOWRE SWE)
and nonwords (TOWRE PDE), which matched the materials of the fMRI
tasks. In addition, the selection ensures consistency for evaluating
reading abilities that were included in prior studies.

2.3. Imaging acquisition

Before the actual scanning session, participants completed a training
session in a mock scanner to familiarize to the scanning environment.
For the actual scanning session, images were collected using a 3T
Siemens Tim Trio scanner with a 16-channel head coil, Siemens Syngo
software version MR B17, at the Northwestern University Center for
Advanced Magnetic Resonance Imaging (CAMRI). Participants laid in-
side the MRI scanner with foam pads around the head to minimize
movement. A right-hand response box was provided to participants to
respond to in-scanner tasks. Visual stimuli were presented on a screen
behind the scanner, viewed in a mirror attached to the head coil. Audio
stimuli were delivered through sound-attenuating headphones to mini-
mize noise from the scanner. A movie was presented while performing
structural MRI and DTI scanning.

Blood oxygen level-dependent signal (BOLD) was acquired using a
T2*-weighted susceptibility-weighted single-shot echo-planar imaging
(EPI) (TR = 2000 ms, TE = 20 ms, matrix size = 128 × 120, bandwidth
= 1302 Hz/Px, slice thickness = 3 mm (0.48 mm gap), number of slices
◦
= 32, voxel size = 1.7 × 1.7 × 3.0 mm, flip angle = 80
, GRAPPA ac-
celeration factor = 2). Slices were acquired interleaved from bottom to
top with even slices acquired first. 202 vol were acquired in each run and
the first 6 were removed to allow for equilibration.

Whole-brain anatomical

imaging was conducted using a T1-
weighted MPRAGE sequence (TR = 2300 ms, TE = 3.36 ms, matrix
size = 256 × 256, bandwidth = 240 Hz/Px, slice thickness = 1 mm,
◦
number of slices = 160, voxel size = 1 mm isotropic, flip angle = 9
). DW
images were collected using echo-planar spin echo imaging sequence
(TR = 9400, 9500, or 9512 ms, TE = 89 ms, matrix size = 128 × 128,
band- width = 1346 Hz/Px, slice thickness = 2 mm, number of slices =
72, voxel size = 2 mm isotropic, flip angle = 90
, GRAPPA acceleration
factor = 2, 1 b = 0 s/mm2, 64 non-collinear diffusion-encoding di-
rections b = 1000 s/mm2).

◦

2.4. fMRI task

The in-scanner rhyming judgment task consisted of six conditions.
Participants completed two separate runs of each task condition, with
each run taking about 6.5 min. If the participant only completed one
run, the completed run was included for analyses representing the cor-
responding condition. The task conditions were categorized based on
two dimensions. One was lexicality, containing pairs of either words (e.
g., stool) or pronounceable pseudo-words (e.g., sterb). The other
dimension was the stimulus modality: auditory (AA), visual (VV) or with
the first item presented auditorily and the second visually (AV).
Therefore, the six task conditions contained AA Pseudoword, AA Word,
VV Pseudoword, VV Word, AV Pseudoword, and AV Word.

et

(Balota

The stimuli in each run consisted of 96 word or non-word pairs
categorized into four similarity conditions. Pairs of words or non-words
in each trial were either orthographically and phonologically similar
(O+P+:
row-blow), orthographically similar and phonologically
different (O+P-: row-now), orthographically different and phonologi-
cally similar (O-P+: row-dough), or orthographically and phonologically
different (O-P-: row-beat). Each similarity condition contained 24 pairs.
The stimuli were monosyllabic without either homophones or homo-
graphs. They were also matched across conditions for written word
frequency in children (Zeno et al., 1995), and English Lexicon Project
measures of written bigram frequency, naming mean accuracy, and
lexical decision mean accuracy
al., 2007). The
word/non-word pairs were repeatedly applied across the six task con-
ditions. Each item was presented for 800 ms with a 200 ms inter-item
interval. Visual stimuli were presented in the center of the screen, and
stimuli
through
sound-attenuating headphones while a fixation cross was visually pre-
sented. A red fixation cross was presented after the second stimulus of
each trial to notify the participant to respond, with a random jittered
inter-trial duration of 2200, 2600, or 3000 ms. Participants needed to
respond before the red cross disappeared. To control sensory activation
and motor response, each run also contained 24 perceptual trials and 48
fixation trials. The perceptual trials were presented as symbol sets for
visual modality and tones for the auditory modality. Fixation trials
included two black crosses each presented for the same duration as
rhyming tasks, followed by a blue fixation cross for the same duration as
the red fixation cross. Participants were instructed to press a button
when they saw the blue cross. Each run contained 84 trials (12 rhyming,
24 perception, and 48 fixation trials), so there were 168 trials for each
task condition. Trials were presented in a fixed pseudo-randomized
order. The trial presentation order within in each run was counter-
balanced across participants.

auditory modality were

presented

the

in

2.5. Image processing

2.5.1. DTI

Processing of DW images was performed using the ExploreDTI
(Leemans et al., 2009, http://www.exploredti.com) toolbox for Matlab.
Head motion and eddy current correction were applied to raw DW im-
ages. Each DW volume was nonlinearly registered to the T1 image to
correct EPI distortions.

Each participant’s T1-weighted image was parcellated into separate
brain regions representing each node of the connectome. The images
were skull-stripped using the FSL Brain Extraction Tool (Smith, 2002)
and parcellated into 90 gray matter regions based on the Automated
Anatomical Labelling template (Tzourio-Mazoyer et al., 2002). The
FMRIB’s Nonlinear Image Registration Tool (FNIRT, FSL; Jenkinson
et al., 2012, http://www.fmrib.ox.ac.uk/fsl/) was then used to register
images to the MNI (Montreal Neurological Institute) 152 template. All
analyses were performed in each participant’s native space by applying
the inverse of the transforming matrices to the AAL template.

To obtain the edges of the connectome, whole-brain probabilistic
tractography was performed to reconstruct white matter fibers between

3 

C. Lou and M.F. Joanisse

NeuroImage 303 (2024) 120941 

each pair of nodes based on corrected DW images, using bedpost_gpu and
probtrackx_gpu in FSL (Hernandez-Fernandez et al., 2019; Hern´andez
et al., 2013). This probabilistic tractography algorithm evaluates the
probability and strength of the most likely location of a pathway. The
present study applied the default fiber tracking parameters (step size =
0.5 mm, maximum 2000 steps, maximum turning angle = 0.2 rads, 5000
tracks generated from each seed voxel). For each pair of nodes, a
normalized index of connectivity was computed based on the number of
voxels in the seed region:

I = log(waytotal)/log(5000 ∗ Vseed)

where waytotal indicates the total number of streamlines from seed to
target regions after the permutation, and Vseed refers to the number of
voxels in the seed region.

2.5.2. fMRI

fMRI data were preprocessed and analyzed using FEAT in FSL. Before
preprocessing, image volumes from incorrectly answered trials were
excluded. Functional images were co-registered with the anatomical
image. Images were smoothed using a 6 mm isotropic Gaussian kernel.
As mentioned in Lytle et al. (2019), the dataset in the present study has
excluded scans that had greater than 25 % of volumes with > 1.5 mm
volume-to-volume motion. In the further motion clearing step, volumes
showing severe head motion parameters, with the same criteria for the
DW images, were left out from following analyses of any levels. For each
participant, a general linear model (GLM) was applied to each run. As
the current study was designed to investigate effects of orthographic
similarity and spelling-sound similarity separately, the four similarity
conditions were grouped to represent
interest
including orthographically similar rhymes (O+, combining O+P+ and
O+P-), orthographically different rhymes (O-, combining O-P+ and
O-P-), congruent (C+, combining O+P- and O-P+) and incongruent (C-,
O+P+ and O-P-). The fixation condition was used as the baseline, and
the perceptual conditions were included as conditions of non-interest.
Initial analyses were applied to each run, with separate contrasts
comparing each of the six similarity conditions versus the baseline ac-
tivations within each task modality. Subsequent analyses merged two
runs of the same task condition for each participant.

the conditions of

2.6. Control energy

Based on network control theory, the present study defined the
process of control as the change in BOLD activity evoked by the external
task and stimuli (Gu et al., 2015). A linear model was applied to describe
the connectome-constrained neural dynamics:

S(t + 1) = AS(t) + Bκuκ(t)

where A is a symmetric weighted matrix representing the white matter
connectome, S describes the state of each brain node over time as
captured by task-based fMRI activation, and Bκ indicates the control
points. In the current study, the reading network analyses defined
reading network regions, which were the primary brain areas for
reading tasks, as control nodes. As the dataset this study used included
children with a wide range of reading abilities, the selection of reading
network nodes was based on a meta-analysis of studies of fMRI studies in
typical-reading (Martin et al., 2015) and dyslexic children (Maisog et al.,
2008), and a study of white matter connectome in dyslexic children
which reported differences within one subnetwork (Lou et al., 2019). As
shown in Fig. 1, the control nodes were restricted to the left hemisphere,
including pars triangularis and pars opercularis of inferior frontal gyrus
(IFG),
insula, fusiform gyrus, supramarginal gyrus, angular gyrus,
Heschl’s gyrus, superior temporal gyrus (STG), middle temporal gyrus
(MTG),
inferior temporal gyrus, superior temporal pole, Rolandic
operculum, and the thalamus. For subsequent functionally specific ROI
analyses, all these brain regions were defined as control nodes and the

Fig. 1. Parcellation of the whole brain. Gray matter was divided into 90 regions
following the AAL atlas. Nodes colored in green represent reading network
areas which are defined as control nodes in the analyses.

left fusiform gyrus and STG were selected as ROIs.

The model indicates the change of brain states from S(t) to S(t +1) is
linearly determined by the white matter connectome A and initiated by
control input uκ(t) which is deployed onto control points Bκ. The uκterm
refers to the control strategy which contains information about the
minimum required amount of control energy Emin, which is required by
control points Bκ, driving the network from S(t) to S(t + 1):
(cid:0)
(T)

S(T) (cid:0) eA⊺

S(T) (cid:0) eA⊺

Emin =

S(0)

S(0)

W

)⊺

)

(cid:0)

(cid:0) 1
r

(cid:0) 1
where the W
r

(T) refers to the reachability Gramian:

(cid:0) 1
W
r

(T) =

∫T

t=0

eA(T(cid:0) t)

BB

⊺

eA⊺ (T(cid:0) t)

dt

The present study focused on the energy required for the change of
brain activation from baseline to each task condition. Therefore, the
computation only considered two discrete timepoints: t = 0 as the fix-
ation baseline state and t = T as similarity condition. The minimum
control energy for each similarity condition (O+, O-, P+, P-, C+, and C-)
in the six task conditions was then computed based on these equations.

2.7. Statistical analyses

The reading network analyses included a series of

three-way
repeated measures ANOVAs, which were applied to investigate if the
required control energy of the entire reading network regions is different
across various task and similarity conditions. Two independent variables
were included in all ANOVAs, modality (AA, AV, and VV) and lexicality
(word and pseudoword). The other independent variable was similarity.
As three similarity conditions were extracted based on the first-level
analysis, three ANOVAs were performed investigating the effect of
orthographic similarity (O+ vs. O-), phonological similarity (P+ vs. P-),
and conflict similarity (C+ vs. C-) respectively.

For the functionally specific ROI analyses, the same series of three-
way repeated measures ANOVAs were applied to investigate the
required control energy of fusiform gyrus and STG. In addition, another

4 

C. Lou and M.F. Joanisse

NeuroImage 303 (2024) 120941 

three-way repeated measure ANOVA was performed to examine if the
required control energy was different between the two ROIs. ROI, mo-
dality and lexicality were the three independent variables. Bonferroni
corrections were applied to any pairwise comparisons.

3. Results

3.1. Demographic and behavioral measures

Descriptive statistics for demographic and behavioral measures are
shown in Table 1. In addition, age has no significant correlations with
any control energy measures (all |r|s 〈 0.22, ps 〉 0.09)

3.2. Orthographic similarity

Two participants whose control energy value of in the AA pseudo-
word condition were outliers were excluded from the orthographic
similarity ANOVA (Figure S1A and S1B). The ANOVA with the rest of
participants showed significant main effect of lexicality (F(1,48) = 5.08,
p = .029), with pseudoword trials requiring more energy than word
trials. While the main effects of modality and similarity did not reach
significance, there was a significant similarity * modality interaction (F
(2,96) = 5.79, p = .004). As shown in Fig. 2A, pairwise comparisons
indicated that the similarity effect was significant only in AA modality,
with higher control energy for O- than O+ (t(49) = 4.38, p < .001). In-
scanner task accuracy was also lower in orthographically dissimilar
trials (Fig. 2B).

3.3. Congruency

Two outlier participants were removed (Figure S1C). The ANOVA
showed a significant main effect of lexicality (F(1,49) = 13.26, p <
.001), with pseudoword trials requiring more energy than word trials. In
addition, the significant lexicality * modality interaction (F(2,98) =
3.14, p = .048) demonstrated high control energy for the pseudoword
condition compared to the word condition (t(49) = 4.53, p < .001) in VV
modality only (Fig. 3A). In addition, the congruency * modality inter-
action effect was significant (F(2,98) = 8.28, p < .001). Pairwise com-
parisons showed that the required energy for the C- condition was higher
than C+ (t(49) = 3.51, p = .001) for the VV modality. The lexicality *
congruency interaction effect was also significant (F(1,49) = 6.4, p =
.012). Pairwise comparisons on lexicality under the significant lexicality
* congruency interaction showed that the pseudowords required higher
control energy than words in both congruent and incongruent trials,
while the effect was higher for congruent trials. However, pairwise
comparisons showed no significant similarity effect in either word or
pseudoword conditions. For the in-scanner task accuracy, the interac-
tion was also observed, where the largest accuracy difference between
word and nonword trials was shown in the VV modality (Fig. 3C). In
addition, incongruent trials showed significant lower accuracy than
congruent trials, with the largest effect in the VV modality (Fig. 3D).

3.4. Functionally specific ROI analyses

(1,50) = 112.91, p < .001) and modality (F(2100) = 9.84, p < .001)
main effects were identified. In addition, there was a ROI * modality
interaction (F(2100) = 53.31, p < .001). Pairwise comparisons showed
that the fusiform gyrus required less energy than STG in the AA (t(50) =
(cid:0) 10.31, p < .001) and AV (t(50) = (cid:0) 8.75, p < .001) conditions, but
required higher control energy than STG in the VV condition (t(50) =
2.73, p = .009) . By comparing modality differences in different ROIs,
the pairwise comparisons indicated that the fusiform gyrus required less
control energy in the AA condition compared to the AV and VV condi-
tions, while STG required less control energy in the VV condition
compared to the AA and AV conditions (Fig. 4).

For the ANOVA evaluating the orthographic similarity effect (which
compared control energy between O+ and O- conditions), both the
fusiform gyrus (F(2100) = 10.73, p < .001) and STG (F(2100) = 40.93, p
< .001) showed significant main effects of modality. The pattern of
differences across the three modalities in each ROI were same with the
differences in the mean control energy ANOVA. The fusiform gyrus (F
(1,50) = 8.34, p = .006) and STG (F(2100) = 56.02, p < .001) also
exhibited significant main effects of similarity, with higher control en-
ergy in the O- than O+ condition. Meanwhile, there was a modality *
similarity interaction only in STG (F(2100) = 14.00, p < .001). Pairwise
comparisons showed that STG required higher control energy in the O-
than O+ condition at AA (t(50) = 7.35, p < .001) and VV (t(50) = 2.99, p
= .005) (Fig. 5), but there was no similarity difference at AV condition.
For the ANOVA evaluating the congruency effect, both the fusiform
gyrus (F(2100) = 10.53, p < .001) and STG (F(2100) = 41.82, p < .001)
showed significant modality main effects. The pattern of differences
across the three modalities in each ROI was the same as the differences
in the mean control energy ANOVA. No other main effects or in-
teractions were significant.

3.5. Validation

The data so far suggest control energy provides useful insights into
neural organization of letter-sound knowledge in children. A question
that arises is whether such effects provide information beyond what can
be simply inferred from region-wise fMRI activation levels for each sub-
task. To examine this, the same three-way repeated measures ANOVAs
were applied as above, but using the average condition-wise fMRI beta
values across 1) all the reading network control nodes and 2) all nodes of
the connectome. Results showed that beta values across the reading
network nodes exhibited significant main effects of orthographic simi-
larity, with higher activation for O- than O+ condition (Fig. 6). How-
ever, no other main effects or interactions were found.

4. Discussion

It has been previously demonstrated that reading performance is
associated with both white matter connectivity and functional activa-
tion in the brain. However, there is little evidence describing how the
white matter network constrains brain activation during reading tasks.
To examine the structural-functional coupling in support of reading, this
study examined how control theory explains the dynamics of functional
activation during visual and auditory word rhyming.

For the ANOVA evaluating mean control energy across all individual
similarity conditions (O+P+, O+P-, O-P+ and O-P-), significant ROI (F

4.1. Process of control in the reading network

Table 1
Demographic and behavioral measures.

Age (years)
Sex (boys/girls)

Sight Word Efficiency (raw score)
Phonemic Decoding (raw score)

N

51
24/
27
50
50

Mean

SD

Range (min/max)

11.06

1.75

8.25/14.60

63.96
27.78

16.14
12.78

25/104
4/60

Overall, the present study validated the hypothesis that there are
associations between levels of control energy in the brain’s reading
network and cognitive load during rhyming tasks in either the written or
spoken domains. Rhyming has been a focus of reading and language
research as it taps underlying phonological representations essential to
visual word recognition (Goswami, 1993). Task conditions demanding
more effort or additional cognitive processes were associated with
higher control energy of the reading network. In addition, this associa-
tion could be reflected in the engagement of functionally specified brain

5 

​
​
​
C. Lou and M.F. Joanisse

NeuroImage 303 (2024) 120941 

Fig. 2. A) Control energy required by reading network nodes and its differences between levels of conditions. Showing interaction effect between modality and
orthographical similarity. B) Interaction effect between modality and orthographic similarity for in-scanner rhyming accuracy. Note. * indicates significant difference
(p < .05). AA: auditory-auditory modality; AV: auditory-visual modality; VV: visual-visual modality; O+: orthographically similar; O-: orthographically different.

regions, where the degree of engagement was also determined by the
task requirements. Concordant with earlier findings with regard to
working memory (Braun et al., 2021), these findings demonstrated that
control energy is a useful measure for evaluating complex cognitive
processes in the brain such as reading. It also indicates the importance of
understanding the neural substrate of reading functions in a network
view given that the specific interactions observed here do not simply
recapitulate task-based region-wise fMRI signal levels.

The present study further demonstrated that the control energy effect
was specific to the reading network, while no effects were observed
across the whole-brain network. The results highlight the importance of
the reading circuit, but also extend our understanding of it by demon-
strating how control processes in those areas support reading. The
required control energy was determined by the structure of the white
matter connectome (Betzel et al., 2016), indicating that reading network
areas control the brain activation based on the topology of the
connectome.

In addition, control energy could be an indicator of neural engage-
ment, such as what is required during a cognitively demanding task,
where neural activity must be repeatedly shifted from a resting state (the
relaxation period between trials) toward a cognitively demanding task
(Braun et al., 2021). One source of control inputs is issued directly from
brain regions which act as local processors responding to cognitive task
demands (Betzel et al., 2016; Gu et al., 2015). This seems concordant
with our findings of dissociation between STG and fusiform gyrus across
modalities. Recent studies have also demonstrated the effectiveness of

regional control energy as an indicator of
functional activation
(Cornblath et al., 2020; Cui et al., 2020). Specifically, Cui et al. (2020)
reported the largest control energy in the fronto-parietal
lobe for
pushing the brain into an activation state for executive functions, indi-
cating that the most related area to a function would contribute more
energetic cost to reach the target brain state. Likewise, the control en-
ergy of reading network regions also reflects the extent of engagement
during the reading task. Further, the differences in control energy of the
reading network also suggested distinct activation states across various
task conditions, which was in parallel with previous fMRI studies using
the same rhyming task (Bitan et al., 2007; Bolger et al., 2008; McNorgan
et al., 2013).

More specific to reading and language, the control energy analyses
reveal key insights into how rhyming tasks influence neural dynamics,
and specifically how this is influenced by lexicality and stimulus mo-
dality. First, we found that pseudoword trials required more control
energy than word trials in a visual-only condition. Second, we observed
higher control energy for orthographically dissimilar trials than similar
trials. In addition, incongruent trials (visual and phonological forms
mismatched, e.g., dough/cough) required higher control energy than
congruent trials in the visual-only condition. A functionally specific ROI
analysis also found dissociation where control energy for visual and
auditory rhyming were differentially modulated in brain regions sensi-
tive to auditory and visual features of words (left STG and fusiform
gyrus, respectively).

By applying the control theory framework, this study validates

6 

C. Lou and M.F. Joanisse

NeuroImage 303 (2024) 120941 

Fig. 3. Control energy required by reading network nodes and its differences between levels of conditions. A) interaction effect between modality and lexicality; B)
interaction effect between modality and congruency. C) Interaction effect between modality and lexicality for in-scanner rhyming accuracy. D) Interaction effect
between modality and congruency for in-scanner rhyming accuracy. Note: * highlights significant difference (p < .05). AA: auditory-auditory modality; AV: auditory-
visual modality; VV: visual-visual modality; C+: congruency condition; C-: incongruency condition.

Fig. 4. Interaction effect of control energy between modality and ROI with
comparisons between each pair of the three modalities in the fusiform gyrus
and STG. Note: * highlights significant difference (p < .05); comparisons be-
tween fusiform and STG were all significant in each modality. AA: auditory-
auditory modality; AV: auditory-visual modality; VV: visual-visual modality;
STG: superior temporal gyrus.

control energy as an indicator of functional activation during in-scanner
reading. Moreover, it extends our current understanding of how the
white matter connection profile at a macroscale level can explain
functional reconfigurations occurring during different cognitive tasks.

Fig. 5. Interaction effect of control energy between modality and ortho-
graphical similarity in STG. Note: * highlights significant difference (p < .05).
AA: auditory-auditory modality; AV: auditory-visual modality; VV: visual-visual
modality; STG: superior temporal gyrus; O+: orthographically similar; O-:
orthographically different.

Previous studies have typically examined structure-function coupling by
exploring nodal similarity between structural and functional connec-
tivity profiles (Su´arez et al., 2020). The network control theory used
here evaluates these dynamics concurrently by merging white matter
structure with the dynamics of evoked functional activation, thereby
extending our model of structure-function coupling during a complex

7 

C. Lou and M.F. Joanisse

NeuroImage 303 (2024) 120941 

Regarding the rhyming task, higher activation has been found in the
left inferior occipito-temporal junction and left posterior prefrontal re-
gions for pseudowords than words rhyming, while no brain regions have
shown higher activation for word rhyming (Xu et al., 2001). The present
study applied a rhyming task that restricted the extent of involvement of
lexical decision and semantic processing, suggesting that the control
energy differences reflected the additional effort for phonological
decoding. Weiss and Booth (2017) applied the same rhyming task and
fMRI design as the present study. However, their study reported higher
activation for words
inferior
than pseudowords
occipito-temporal area, and no areas were activated more for pseudo-
words than words. The opposite lexical effect may be due to the analyses
in their study not including incongruent trials (O+P- and O-P+), nar-
rowing the discrepancy in difficulties with words vs. pseudowords, since
the semantics of words could ease the conflict between orthographic and
phonological similarities. In our study, pairwise comparisons of lexi-
cality under the significant lexicality by congruency interaction showed
that the lexical effect was higher in the incongruent condition, while the
control energy was still higher for pseudowords than words in the
congruent condition.

in the

left

4.3. Congruency effects

The congruency effect was shown as higher control energy for
incongruent than congruent trials. The rhyming decision is more diffi-
cult for incongruent than for congruent pairs (e.g., row-know vs. row-
dough), consistent with the classic finding that spelling-sound conflict
interferes with phonological judgment (Johnston and McDermott, 1986;
Kramer and Donchin, 1987; Levinthal and Hornung, 1992; Polich et al.,
1983; Rugg and Barrett, 1987; Seidenberg and Tanenhaus, 1979).
Therefore, rhyming judgments for incongruent trials require more effort,
and the congruent effect on control energy could be a neural represen-
tation of an additional cognitive workload for incongruent trials.

was

activation

considered

In fMRI studies, the incongruent > congruent effect has been
revealed in reading-related regions (Bitan et al., 2007; Cone et al.,
2008). Such findings reflect stronger activation of task-relevant pro-
cesses to override interference from the nonrelevant dimension.
Regarding the rhyming task, the highlighted brain clusters were mainly
localized in the left inferior frontal gyrus and left inferior parietal lobe,
whose
to
orthography-phonology mapping (Booth et al., 2002a; Xu et al., 2001),
and segmentation and manipulation of phonological and articulatory
representations (Fiebach et al., 2002; Fiez and Petersen, 1998; Mechelli
et al., 2003). Bitan et al. (2007) suggest that the congruency effect
identified in these regions reflects orthography-phonology mapping and
phonological segmentation when incongruent pairs are encountered.
Control energy captured the additional workload in the visual-visual
(VV) condition compared to the other two conditions, which is consis-
tent with the assumption that the VV condition provides the most
straightforward measure of an orthographic similarity effect.

related

be

to

4.4. Orthographic effects

For the orthographic effects, the present study identified higher
control energy for orthographically dissimilar trials. Many prior studies
have demonstrated the influence of orthography on spoken word pro-
cessing tasks (Ch´ereau et al. 2007; Landerl et al., 1996; Perre et al.,
2009; Taft, 1986; Ziegler and Muneaux, 2007). For instance, auditory
rhyme judgment tasks that only explicitly require phonological infor-
mation processing still show orthographic similarity influences reaction
times, suggesting automated access to orthographic representations
during phonological processing (Booth et al., 2002a; Donnenwerth--
Nolan et al., 1981; Petrova et al., 2011; Seidenberg and Tanenhaus,
1979). While there are event-related brain potential (ERP) studies
demonstrating other cognitive processing under the orthographic effect
in auditory rhyming tasks (Lafontaine et al., 2012; Pattamadilok et al.,

8 

Fig. 6. The significant difference in the mean beta value across all reading
network nodes between orthographically similar (+) and dissimilar (-) trials.

task like reading.

4.2. Lexicality

The lexicality effect was reflected via higher control energy for
pseudoword than word trials. In the view of the contemporary models of
reading, the translation from orthography to phonology is completed via
decoding, the translation of letters to sounds, or a lexically or semanti-
cally mediated “whole word” pathway (Coltheart et al., 2001; Seiden-
berg and McClelland, 1989). On this view the pronunciation of
pseudowords can only be acquired based on orthography-to-phonology,
thus requiring more effort compared to familiar words that benefit from
the support of a lexical/semantic route. The contrast between pseudo-
words and words could reflect a more involved decoding process
including grapheme-phoneme mapping and phonological output
(Coltheart et al., 2001; Harm and Seidenberg, 2004; Taylor et al., 2013),
or assistance of the semantic route during reading (Plaut et al., 1996).
The lexical effect identified in the present study suggests that reading
network regions needed higher control energy to successfully move the
brain into a functional state that supported pseudoword rhyming, as
compared to word rhyming. This is in line with the cognitive models: it
reflects either the lack of a lexical representation, which would affect the
rhyming task less when the auditory input was presented, or less assis-
tance from the semantic route when participants read pseudowords that
are low-frequency inconsistent materials but have no semantic
representations.

In fMRI studies investigating lexical effects, however, the activation
contrast map could be observed in both directions. Specifically, pseu-
dowords have shown greater activation than words in regions including
the supramarginal gyrus, inferior occipito-temporal area, and superior
temporal gyrus (Jobard et al., 2003; Mechelli et al., 2003; Richlan et al.,
2011), while words showed greater activation than pseudowords in the
fusiform gyrus and ventral inferior frontal gyrus (Fiebach et al., 2002;
Jobard et al., 2003). As the discrepancies in highlighted regions indicate
particular cognitive mechanisms of pseudoword and word reading
respectively, it is difficult to conclude the decoding process is the
exclusive origin of observed differences in control energy between word
and pseudoword rhyming. In several meta-analyses of lexical effects in
fMRI, significant clusters for word > pseudoword contrast have been
identified which are related to semantics (Cattinelli et al., 2013;
McNorgan et al., 2015; Taylor et al., 2013). Moreover, McNorgan et al.
(2015) suggest that the lexical effect in fMRI activation could be
modulated by the type of reading task.

C. Lou and M.F. Joanisse

NeuroImage 303 (2024) 120941 

2011; Welcome and Joanisse, 2018), a common finding is an additional
effort for orthographically dissimilar pairs of words. The present study
identified higher control energy for orthographically dissimilar trials in
the auditory-only condition,
reading network
engagement when the spelling pattern is mis-matched between the two
stimuli.

indicating greater

One surprising result is that the orthographic effect was not signifi-
cant in the visual-only modality, while studies at the behavioral level
reported longer reaction time for orthographically inconsistent pairs of
words during lexical decision and naming tasks in the visual modality
(Lacruz and Folk, 2004; Massaro and Jesse, 2005; Stone et al., 1997;
Ziegler et al., 1997). A possible cause is that the orthographic effect was
interrupted by the significant congruency (C+ vs C-) effect in the visual
condition. Specifically, control energy for C- (O+P- and O-P+) was
higher than for C+ (O+P+ and O-P-). When examining the difference in
control energy across the four similarity conditions in the visual-only
modality, control energy for O-P+ was significantly higher than for
O+P+ (p = .037). While the control energy difference between O+P-
and O-P- was not significant, the direction of the difference was identical
to the congruency effect. However, the combination for comparing O+
(O+P+ and O+P-) to O- (O-P+ and O-P-) would diminish the difference
as the mean of O+P+ was lower than O-P+ while the mean of O+P- was
higher than O-P-. As shown in an fMRI study using the same rhyming
task in the visual modality, a significant difference between O+P- and
O-P- was identified at both behavioral and neural levels, suggesting
more effort for O+P- condition (Cone et al., 2008). Combined with
findings in the present study, it suggested that the orthographic effect
may be dominated by the congruency effect at the visual-only modality.

4.5. ROI dissociation

The present data further corroborate the separate roles that the left
fusiform gyrus and left STG play in reading and language. Prior work has
found that left fusiform gyrus responds to words specifically in written
form, suggesting its unique function in orthographic processing
(Dehaene and Cohen, 2011; Dehaene et al., 2002; McCandliss et al.,
2003). On the other hand, the left STG is responsible for multiple
functions including phonological processing in auditory word process-
ing (Buchsbaum et al., 2001; Graves et al., 2008; Mesgarani et al., 2014;
Price, 2012). Findings in the present study paralleled this dissociation.
Specifically, the STG was more engaged in the rhyming task when it
required participants to focus on the phonological features (AA/AV >
VV). In addition, there are differences in control energy of the two re-
gions between conditions with and without auditory/visual
input,
which is in accordance with their functions. As shown in Fig. 4, the left
fusiform gyrus contributed less control energy when there were no
visually presented stimuli, whereas the left STG was contributed less
control energy when there were no auditorily presented stimuli. This is
congruent with Booth et al. (2002), who reported modality-specific ac-
tivations in the left fusiform for written words and the left STG for
spoken words during a rhyming task. The authors accordingly proposed
that visual and auditory word input are encoded in modality-specific
association areas before being relayed to hetero-modal cortices in su-
perior temporal and inferior frontal
language areas (Booth et al.,
2002b). As control energy is also related to the process of inducing
functional activation changes in other brain regions (Gu et al., 2015),
the present study provides an alternative approach to describe how the
two ROIs are involved in reading functions in different modalities,
where these regions are also actively involved in modulating activation
in other reading network sub-regions.

Another aspect of this dissociation was the observed orthographic
congruency * modality interaction. While both left STG and fusiform
gyrus showed significant main effects of orthographic congruency and
modality, only the left STG exhibited an orthographic by modality
interaction. The interaction was originated from a non-significant
orthographic effect in the auditory-visual modality, which may be due

9 

to left STG involvement in audiovisual integration in reading (Blau et al.,
2009; Hashimoto and Sakai, 2004; Van Atteveldt et al., 2004). There-
fore, the orthographic effect in AV could be covered by the additional
working load on audiovisual integration in the left STG. As shown in
Fig. 5, the control energy of left STG in the AV condition was higher than
the AA condition for O+ trials. It reflected additional load in AV con-
dition even with less auditory input, indicating integration processing
during the task (Booth et al., 2001).

On top of corroborating previous findings in fMRI studies, our work
also emphasizes the critical roles of white matter connectivity in high-
lighting ROI-specific activation levels. Specifically, we found no ROI
effect in any conditions in the validation test that only applied changes
of beta values to quantify functional reconfiguration between condi-
tions. It suggested that the network control model could better reveal the
differences on functional activation changes between two different re-
gions, and white matter connection map is critical to capture this effect
as it provides the structural connectivity pattern that restricts neural
signal transmission.

5. Conclusion

The current findings provide a framework for understanding neural
activity during complex task processing as the interaction of static white
matter connectivity and dynamic functional activity in cortex. While
many prior studies have sought to link reading to white matter and
functional activity separately, it has been challenging to integrate these
into a single framework. Here we have shown how the brain’s under-
lying network topology influences dynamics during reading tasks at the
network level, highlighting the role that white matter structure plays in
the communication abilities among functional brain nodes, modulating
the difficulty with which different target states can be reached.

We validated control theory as a framework to capture functional
activation changes during a reading task, as constrained by white matter
connectome. This framework explained differences in functional acti-
vation changes within reading network regions between various levels
of reading task conditions, which could not be observed with fMRI
activation data alone (as shown in the Validation section). The white
matter connectome thus influences brain dynamics, and the necessity for
investigating
pinpointed
accordingly.

network-wise

connections

been

has

CRediT authorship contribution statement

Chenglin Lou: Writing – review & editing, Writing – original draft,
Methodology, Formal analysis, Data curation, Conceptualization. Marc
F. Joanisse: Writing – review & editing, Supervision.

Declaration of competing interest

The authors declare that they have no known competing financial
interests or personal relationships that could have appeared to influence
the work reported in this paper.

Supplementary materials

Supplementary material associated with this article can be found, in

the online version, at doi:10.1016/j.neuroimage.2024.120941.

Data availability

Neuroimaging and phenotypic data are taken from a publicly avail-
able dataset at https://openneuro.org/datasets/ds001894/versions/
1.4.2/metadata.

C. Lou and M.F. Joanisse

References

Alonso, Katie Wade, et al., 2024. Network connectivity underlying episodic memory in
children: application of a pediatric brain tumor survivor injury model. Dev. Sci. 27
(1), e13413.

Bailey, S.K., Aboud, K.S., Nguyen, T.Q., Cutting, L.E., 2018. Applying a network

framework to the neurobiology of reading and dyslexia. J. Neurodev. Disord. 10 (1),
1–9.

Balota, D.A., Yap, M.J., Hutchison, K.A., Cortese, M.J., Kessler, B., Loftis, B., Treiman, R.,

2007. The English lexicon project. Behav. Res. Methods 39 (3), 445–459.

Barch, D.M., Burgess, G.C., Harms, M.P., Petersen, S.E., Schlaggar, B.L., Corbetta, M.,
Feldt, C., 2013. Function in the human connectome: task-fMRI and individual
differences in behavior. Neuroimage 80, 169–189.

Bathelt, J., Gathercole, S.E., Butterfield, S., team, C., Astle, D.E., 2018. Children’s
academic attainment is linked to the global organization of the white matter
connectome. Dev. Sci. 21 (5), e12662.

Bells, S., Lefebvre, J., Prescott, S.A., Dockstader, C., Bouffet, E., Skocic, J., Mabbott, D.J.,

2017. Changes in white matter microstructure impact cognition by disrupting the
ability of neural assemblies to synchronize. J. Neurosci. 37 (34), 8227–8238.
Ben-Shachar, M., Dougherty, R.F., Wandell, B.A., 2007. White matter pathways in

reading. Curr. Opin. Neurobiol. 17 (2), 258–270.

Betzel, R.F., Gu, S., Medaglia, J.D., Pasqualetti, F., Bassett, D.S., 2016. Optimally

controlling the human connectome: the role of network topology. Sci. Rep. 6 (1),
1–14.

Bitan, T., Burman, D.D., Chou, T.L., Lu, D., Cone, N.E., Cao, F., Booth, J.R., 2007. The
interaction between orthographic and phonological information in children: an fMRI
study. Hum. Brain Mapp. 28 (9), 880–891.

Blau, V., van Atteveldt, N., Ekkebus, M., Goebel, R., Blomert, L., 2009. Reduced neural
integration of letters and speech sounds links phonological and reading deficits in
adult dyslexia. Curr. Biol. 19 (6), 503–508.

Bolger, D.J., Hornickel, J., Cone, N.E., Burman, D.D., Booth, J.R., 2008. Neural correlates
of orthographic and phonological consistency effects in children. Hum. Brain Mapp.
29 (12), 1416–1429.

Booth, J.R., Burman, D.D., Meyer, J.R., Gitelman, D.R., Parrish, T.B., Mesulam, M.M.,
2002a. Functional anatomy of intra-and cross-modal lexical tasks. Neuroimage 16
(1), 7–22.

Booth, J.R., Burman, D.D., Meyer, J.R., Gitelman, D.R., Parrish, T.B., Mesulam, M.M.,
2002b. Modality independence of word comprehension. Hum. Brain Mapp. 16 (4),
251–261.

Booth, J.R., Burman, D.D., Santen, F.W.V., Harasaki, Y., Gitelman, D.R., Parrish, T.B.,

Mesulam, M.M., 2001. The development of specialized brain systems in reading and
oral-language. Child Neuropsychol. 7 (3), 119–141.

Braun, U., Harneit, A., Pergola, G., Menara, T., Sch¨afer, A., Betzel, R.F., Schwarz, K.,

2021. Brain network dynamics during working memory are modulated by dopamine
and diminished in schizophrenia. Nat. Commun. 12 (1), 1–11.

Buchsbaum, B.R., Hickok, G., Humphries, C., 2001. Role of left posterior superior

temporal gyrus in phonological processing for speech perception and production.
Cogn. Sci. 25 (5), 663–678.

Cabral, J., Vidaurre, D., Marques, P., Magalh˜aes, R., Silva Moreira, P., Miguel Soares, J.,
Kringelbach, M.L., 2017. Cognitive performance in healthy older adults relates to
spontaneous switching between states of functional connectivity during rest. Sci.
Rep. 7 (1), 1–13.

Cattinelli, I., Borghese, N.A., Gallucci, M., Paulesu, E., 2013. Reading the reading brain: a
new meta-analysis of functional imaging data on reading. J Neurolinguistics 26 (1),
214–238.

Ch´ereau, C., Gaskell, M.G., Dumay, N., 2007. Reading spoken words: orthographic effects

in auditory priming. Cognition 102 (3), 341–360.

Coltheart, M., Rastle, K., Perry, C., Langdon, R., Ziegler, J., 2001. DRC: a dual route

cascaded model of visual word recognition and reading aloud. Psychol. Rev. 108 (1),
204.

Coch, D., George, E., Berger, N., 2008. The case of letter rhyming: an ERP study.

Psychophysiology 45 (6), 949–956.

Cone, N.E., Burman, D.D., Bitan, T., Bolger, D.J., Booth, J.R., 2008. Developmental
changes in brain regions involved in phonological and orthographic processing
during spoken language processing. Neuroimage 41 (2), 623–635.

Cornblath, E.J., Ashourvan, A., Kim, J.Z., Betzel, R.F., Ciric, R., Adebimpe, A., Moore, T.
M., 2020. Temporal sequences of brain activity at rest are constrained by white
matter structure and modulated by cognitive demands. Commun. Biol. 3 (1), 1–12.

Cross, A.M., Lammert, J.M., Peters, L., Frijters, J.C., Ansari, D., Steinbach, K.A.,

Joanisse, M.F., 2023. White matter correlates of reading subskills in children with
and without reading disability. Brain Lang. 241, 105270.

Cross, A.M., Ramdajal, R., Peters, L., Vandermeer, M.R., Hayden, E.P., Frijters, J.C.,

Joanisse, M.F., 2021. Resting-state functional connectivity and reading subskills in
children. Neuroimage 243, 118529.

Cui, Z., Stiso, J., Baum, G.L., Kim, J.Z., Roalf, D.R., Betzel, R.F., He, X., 2020.

Optimization of energy state transition trajectory supports the development of
executive function during youth. eLife 9, e53060.

Dehaene, S., Cohen, L., 2011. The unique role of the visual word form area in reading.

Trends Cogn. Sci. (Regul. Ed.) 15 (6), 254–262.

Dehaene, S., Le Clec’H, G., Poline, J.-B., Le Bihan, D., Cohen, L, 2002. The visual word

form area: a prelexical representation of visual words in the fusiform gyrus.
Neuroreport 13 (3), 321–325.

Desroches, A.S., Cone, N.E., Bolger, D.J., Bitan, T., Burman, D.D., Booth, J.R., 2010.

Children with reading difficulties show differences in brain regions associated with
orthographic processing during spoken language processing. Brain Res. 1356, 73–84.

NeuroImage 303 (2024) 120941 

Desroches, A.S., Newman, R.L., Joanisse, M.F., 2009. Investigating the time course of
spoken word recognition: electrophysiological evidence for the influences of
phonological similarity. J. Cogn. Neurosci. 21 (10), 1893–1906.

Donnenwerth-Nolan, S., Tanenhaus, M.K., Seidenberg, M.S., 1981. Multiple code

activation in word recognition: evidence from rhyme monitoring. J. Exp. Psychol.
[Hum. Learn.] 7 (3), 170.

Enge, A., Friederici, A.D., Skeide, M.A., 2020. A meta-analysis of fMRI studies of

language comprehension in children. Neuroimage 215, 116858.

Fiebach, C.J., Friederici, A.D., Müller, K., Von Cramon, D.Y., 2002. fMRI evidence for

dual routes to the mental lexicon in visual word recognition. J. Cogn. Neurosci. 14
(1), 11–23.

Fiez, J.A., Petersen, S.E., 1998. Neuroimaging studies of word reading. Proc. Natl. Acad.

Sci. 95 (3), 914–921.

Finn, E.S., Shen, X., Holahan, J.M., Scheinost, D., Lacadie, C., Papademetris, X.,

Constable, R.T., 2014. Disruption of functional networks in dyslexia: a whole-brain,
data-driven analysis of connectivity. Biol. Psychiatry 76 (5), 397–404.

Graves, W.W., Grabowski, T.J., Mehta, S., Gupta, P., 2008. The left posterior superior
temporal gyrus participates specifically in accessing lexical phonology. J. Cogn.
Neurosci. 20 (9), 1698–1710.

Goswami, U., 1993. Toward an interactive analogy model of reading development:
decoding vowel graphemes in beginning reading. J. Exp. Child. Psychol. 56 (3),
443–475.

Gu, S., Pasqualetti, F., Cieslak, M., Telesford, Q.K., Yu, A.B., Kahn, A.E., Grafton, S.T.,
2015. Controllability of structural brain networks. Nat. Commun. 6 (1), 1–10.
Harm, M.W., Seidenberg, M.S., 2004. Computing the meanings of words in reading:

cooperative division of labor between visual and phonological processes. Psychol.
Rev. 111 (3), 662.

Hashimoto, R., Sakai, K.L., 2004. Learning letters in adulthood: direct visualization of
cortical plasticity for forming a new link between orthography and phonology.
Neuron 42 (2), 311–322.

Hermundstad, A.M., Bassett, D.S., Brown, K.S., Aminoff, E.M., Clewett, D., Freeman, S.,
Miller, M.B., 2013. Structural foundations of resting-state and task-based functional
connectivity in the human brain. Proc. Natl. Acad. Sci. 110 (15), 6169–6174.
Hermundstad, A.M., Brown, K.S., Bassett, D.S., Aminoff, E.M., Frithsen, A., Johnson, A.,
Carlson, J.M., 2014. Structurally-constrained relationships between cognitive states
in the human brain. PLoS Comput. Biol. 10 (5), e1003591.

Hern´andez, M., Guerrero, G.D., Cecilia, J.M., García, J.M., Inuggi, A., Jbabdi, S.,

Behrens, T.E., Sotiropoulos, S.N., 2013. Accelerating fibre orientation estimation
from diffusion weighted magnetic resonance imaging using GPUs. PLoS One 8 (4),
e61892.

Hernandez-Fernandez, M., Reguly, I., Jbabdi, S, Giles, M, Smith, S., Sotiropoulos, S.N.,
2019. Using GPUs to accelerate computational diffusion MRI: From microstructure
estimation to tractography and connectomes. NeuroImage 188, 598–615.
Honey, C.J., Sporns, O., Cammoun, L., Gigandet, X., Thiran, J.-P., Meuli, R.,

Hagmann, P., 2009. Predicting human resting-state functional connectivity from
structural connectivity. Proc. Natl. Acad. Sci. 106 (6), 2035–2040.

Jenkinson, M., Beckmann, C.F., Behrens, T.E., Woolrich, M.W., Smith, S.M., 2012. FSL.

Neuroimage 62 (2), 782–790.

Jobard, G., Crivello, F., Tzourio-Mazoyer, N., 2003. Evaluation of the dual route theory
of reading: a metanalysis of 35 neuroimaging studies. Neuroimage 20 (2), 693–712.
Johnston, R.S., McDermott, E.A., 1986. Suppression effects in rhyme judgement tasks.

The Quarterly J. Experim. Psychol. Section A 38 (1), 111–124.

Karahano˘glu, F.I., Van De Ville, D., 2017. Dynamics of large-scale fMRI networks:

deconstruct brain activity to build better models of brain function. Current Opinion
in Biomedical Engineering 3, 28–36.

Khalsa, S., Mayhew, S.D., Chechlacz, M., Bagary, M., Bagshaw, A.P., 2014. The structural
and functional connectivity of the posterior cingulate cortex: comparison between
deterministic and probabilistic tractography for the investigation of
structure–function relationships. Neuroimage 102, 118–127.

Kim, J.Z., Soffer, J.M., Kahn, A.E., Vettel, J.M., Pasqualetti, F., Bassett, D.S., 2018. Role
of graph architecture in controlling dynamical networks with applications to neural
systems. Nat. Phys. 14 (1), 91–98.

Kramer, A.F., Donchin, E., 1987. Brain potentials as indices of orthographic and

phonological interaction during word matching. J. Experim. Psychol.: Learn.,
Memory, and Cognition 13 (1), 76.

Lacruz, I., Folk, J.R., 2004. Feedforward and feedback consistency effects for high-and
low-frequency words in lexical decision and naming. The Quarterly Journal of
Experimental Psychology Section A 57 (7), 1261–1284.

Lafontaine, H., Chetail, F., Colin, C., Kolinsky, R., Pattamadilok, C., 2012. Role and
activation time course of phonological and orthographic information during
phoneme judgments. Neuropsychologia 50 (12), 2897–2906.

Landerl, K., Frith, U., Wimmer, H., 1996. Intrusion of orthographic knowledge on
phoneme awareness: strong in normal readers, weak in dyslexic readers. Appl
Psycholinguist 17 (1), 1–14.

Leemans, A., Jeurissen, B., Sijbers, J., Jones, D.K., 2009. ExploreDTI: a graphical toolbox

for processing, analyzing, and visualizing diffusion MR data. Proc. Intl. Soc. Mag.
Reson. Med. 17 (1), 3537.

Levinthal, C.F., Hornung, M., 1992. Orthographic and phonological coding during visual
word matching as related to reading and spelling abilities in college students. Read
Writ 4 (3), 231–243.

Liu, T., de Schotten, M.T., Altarelli, I., Ramus, F., Zhao, J., 2021. Maladaptive

compensation of right fusiform gyrus in developmental dyslexia: a hub-based white
matter network analysis. Cortex 145, 57–66.

Liu, X., Gao, Y., Di, Q., Hu, J., Lu, C., Nan, Y., Liu, L., 2018. Differences between child
and adult large-scale functional brain networks for reading tasks. Hum. Brain Mapp.
39 (2), 662–679.

10 

C. Lou and M.F. Joanisse

NeuroImage 303 (2024) 120941 

Lou, C., Cross, A.M., Peters, L., Ansari, D., Joanisse, M.F., 2021. Rich-club structure

Smith, S.M., 2002. Fast robust automated brain extraction. Hum. Brain Mapp. 17 (3),

contributes to individual variance of reading skills via feeder connections in children
with reading disabilities. Dev Cogn Neurosci 49, 100957.

Lou, C., Duan, X., Altarelli, I., Sweeney, J.A., Ramus, F., Zhao, J., 2019. White matter

network connectivity deficits in developmental dyslexia. Hum. Brain Mapp. 40 (2),
505–516.

Lytle, M.N., McNorgan, C., Booth, J.R., 2019. A longitudinal neuroimaging dataset on
multisensory lexical processing in school-aged children. Sci. Data 6 (1), 1–12.
Maisog, J.M., Einbinder, E.R., Flowers, D.L., Turkeltaub, P.E., Eden, G.F., 2008. A meta-
analysis of functional neuroimaging studies of dyslexia. Ann. N. Y. Acad. Sci. 1145
(1), 237–259.

Martin, A., Schurz, M., Kronbichler, M., Richlan, F., 2015. Reading in the brain of

children and adults: a meta-analysis of 40 functional magnetic resonance imaging
studies. Hum. Brain Mapp. 36 (5), 1963–1981.

Massaro, D.W., Jesse, A., 2005. The magic of reading: too many influences for quick and

easy explanations. From Orthography to pedagogy: Essays in Honor of Richard L.
Venezky, pp. 37–61.

McCandliss, B.D., Cohen, L., Dehaene, S., 2003. The visual word form area: expertise for
reading in the fusiform gyrus. Trends Cogn. Sci. (Regul. Ed.) 7 (7), 293–299.
McNorgan, C., Chabal, S., O’Young, D., Lukic, S., Booth, J.R., 2015. Task dependent

lexicality effects support interactive models of reading: a meta-analytic
neuroimaging review. Neuropsychologia 67, 148–158.

McNorgan, C., Randazzo-Wagner, M., Booth, J.R., 2013. Cross-modal integration in the
brain is related to phonological awareness only in typical readers, not in those with
reading difficulty. Front Hum Neurosci 7, 388.

Mechelli, A., Gorno-Tempini, M.L., Price, C.J., 2003. Neuroimaging studies of word and

pseudoword reading: consistencies, inconsistencies, and limitations. J. Cogn.
Neurosci. 15 (2), 260–271.

Mesgarani, N., Cheung, C., Johnson, K., Chang, E.F., 2014. Phonetic feature encoding in

human superior temporal gyrus. Science 343 (6174), 1006–1010.

Parkes, L., Kim, J.Z., Stiso, J., Brynildsen, J.K., Cieslak, M., Covitz, S., Bassett, D.S., 2024.
A network control theory pipeline for studying the dynamics of the structural
connectome. Nat. Protoc. 1–29.

Pattamadilok, C., Perre, L., Ziegler, J.C., 2011. Beyond rhyme or reason: eRPs reveal
task-specific activation of orthography on spoken language. Brain Lang. 116 (3),
116–124.

Perre, L., Midgley, K., Ziegler, J.C., 2009. When beef primes reef more than leaf:

143–155.

Steinbrink, C., Vogt, K., Kastrup, A., Müller, H.P., Juengling, F.D., Kassubek, J.,
Riecker, A., 2008. The contribution of white and gray matter differences to
developmental dyslexia: insights from DTI and VBM at 3.0 T. Neuropsychologia 46
(13), 3170–3178.

Stone, G.O., Vanhoy, M., Van Orden, G.C., 1997. Perception is a two-way street:

feedforward and feedback phonology in visual word recognition. J Mem Lang 36 (3),
337–359.

Su´arez, L.E., Markello, R.D., Betzel, R.F., Misic, B., 2020. Linking structure and function
in macroscale brain networks. Trends Cogn. Sci. (Regul. Ed.) 24 (4), 302–315.
Taft, M., 1986. Lexical access codes in visual and auditory word recognition. Lang Cogn

Process 1 (4), 297–308.

Tang, E., Giusti, C., Baum, G.L., Gu, S., Pollock, E., Kahn, A.E., Gur, R.C., 2017.

Developmental increases in white matter network controllability support a growing
diversity of brain dynamics. Nat. Commun. 8 (1), 1–16.

Taylor, J., Rastle, K., Davis, M.H., 2013. Can cognitive models explain brain activation
during word and pseudoword reading? A meta-analysis of 36 neuroimaging studies.
Psychol. Bull. 139 (4), 766.

Teipel, S.J., Bokde, A.L., Meindl, T., Amaro Jr, E., Soldner, J., Reiser, M.F., Hampel, H.,
2010. White matter microstructure underlying default mode network connectivity in
the human brain. Neuroimage 49 (3), 2021–2032.

Torgesen, J.K., Rashotte, C.A., Wagner, R.K., 1999. TOWRE: Test of Word Reading

efficiency: Pro-ed Austin, TX.

Treiman, R., Mullennix, J., Bijeljac-Babic, R., Richmond-Welty, E.D., 1995. The special
role of rimes in the description, use, and acquisition of English orthography.
J. Experim. Psychol.: General 124 (2), 107.

Tzourio-Mazoyer, N., Landeau, B., Papathanassiou, D., Crivello, F., Etard, O.,

Delcroix, N., Joliot, M., 2002. Automated anatomical labeling of activations in SPM
using a macroscopic anatomical parcellation of the MNI MRI single-subject brain.
Neuroimage 15 (1), 273–289.

Van Atteveldt, N., Formisano, E., Goebel, R., Blomert, L., 2004. Integration of letters and

speech sounds in the human brain. Neuron 43 (2), 271–282.

Van Den Heuvel, M., Mandl, R., Luigjes, J., Pol, H.H, 2008. Microstructural organization

of the cingulum tract and the level of default mode functional connectivity.
J. Neurosci. 28 (43), 10844–10851.

Vandermosten, M., Boets, B., Wouters, J., Ghesqui`ere, P., 2012. A qualitative and

orthographic information affects phonological priming in spoken word recognition.
Psychophysiology 46 (4), 739–746.

quantitative review of diffusion tensor imaging studies in reading and dyslexia.
Neurosci. Biobehav. Rev. 36 (6), 1532–1552.

Petrova, A., Gaskell, M.G., Ferrand, L., 2011. Orthographic consistency and word-

frequency effects in auditory word recognition: new evidence from lexical decision
and rime detection. Front Psychol 2, 263.

Plaut, D.C., McClelland, J.L., Seidenberg, M.S., Patterson, K., 1996. Understanding
normal and impaired word reading: computational principles in quasi-regular
domains. Psychol. Rev. 103 (1), 56.

Vogel, A.C., Church, J.A., Power, J.D., Miezin, F.M., Petersen, S.E., Schlaggar, B.L., 2013.
Functional network architecture of reading-related regions across development.
Brain Lang. 125 (2), 231–243.

Wang, Z., Dai, Z., Gong, G., Zhou, C., He, Y., 2015. Understanding structural-functional
relationships in the human brain: a large-scale network perspective. Neuroscientist
21 (3), 290–305.

Polich, J., McCarthy, G., Wang, W.S., Donchin, E., 1983. When words collide:

Weiss, Y., Booth, J.R., 2017. Neural correlates of the lexicality effect in children. Brain

orthographic and phonological interference during word processing. Biol. Psychol.
16 (3–4), 155–180.

Price, C.J., 2012. A review and synthesis of the first 20 years of PET and fMRI studies of

heard speech, spoken language and reading. Neuroimage 62 (2), 816–847.

Pugh, K.R., Mencl, W.E., Jenner, A.R., Katz, L., Frost, S.J., Lee, J.R., Shaywitz, B.A., 2000.
Functional neuroimaging studies of reading and reading disability (developmental
dyslexia). Ment. Retard. Dev. Disabil. Res. Rev. 6 (3), 207–213.

Richlan, F., Kronbichler, M., Wimmer, H., 2011. Meta-analyzing brain dysfunctions in

dyslexic children and adults. Neuroimage 56 (3), 1735–1742.

Rugg, M.D., Barrett, S.E., 1987. Event-related potentials and the interaction between

orthographic and phonological information in a rhyme-judgment task. Brain Lang.
32 (2), 336–361.

Saggar, M., Sporns, O., Gonzalez-Castillo, J., Bandettini, P.A., Carlsson, G., Glover, G.,
Reiss, A.L., 2018. Towards a new approach to reveal dynamical organization of the
brain using topological data analysis. Nat. Commun. 9 (1), 1–14.

Seidenberg, M.S., McClelland, J.L., 1989. A distributed, developmental model of word

recognition and naming. Psychol. Rev. 96 (4), 523.

Lang. 175, 64–70.

Welcome, S.E., Joanisse, M.F., 2018. ERPs reveal weaker effects of spelling on auditory

rhyme decisions in children than in adults. Dev. Psychobiol. 60 (1), 57–66.
Xia, Z., Zhang, L., Hoeft, F., Gu, B., Gong, G., Shu, H., 2018. Neural correlates of oral
word reading, silent reading comprehension, and cognitive subcomponents. Int. J.
Behav. Dev. 42 (3), 342–356.

Xu, B., Grafman, J., Gaillard, W.D., Ishii, K., Vega-Bermudez, F., Pietrini, P.,

Theodore, W., 2001. Conjoint and extended neural networks for the computation of
speech codes: the neural basis of selective impairment in reading words and
pseudowords. Cereb. Cortex 11 (3), 267–277.

Yeatman, J.D., Dougherty, R.F., Ben-Shachar, M., Wandell, B.A., 2012. Development of
white matter and reading skills. Proc. Natl. Acad. Sci. 109 (44), E3045–E3053.
Zeno, S., Ivens, S.H., Millard, R.T., Duvvuri, R., 1995. The Educator’s Word Frequency

Guide. Touchstone Applied Science Associates.

Zhao, J., de Schotten, M.T., Altarelli, I., Dubois, J., Ramus, F., 2016. Altered hemispheric

lateralization of white matter pathways in developmental dyslexia: evidence from
spherical deconvolution tractography. Cortex 76, 51–62.

Seidenberg, M.S., Tanenhaus, M.K., 1979. Orthographic effects on rhyme monitoring.

Zhou, W., Cui, X., Shi, B., Su, M., Cao, M., 2021. The development of brain functional

J. Exp. Psychol. [Hum. Learn.] 5 (6), 546.

connectome during text reading. Dev. Cogn. Neurosci. 48, 100927.

Shine, J.M., Breakspear, M., Bell, P.T., Ehgoetz Martens, K.A., Shine, R., Koyejo, O.,

Ziegler, J.C., Montant, M., Jacobs, A.M., 1997. The feedback consistency effect in lexical

Poldrack, R.A., 2019. Human cognition involves the dynamic integration of neural
activity and neuromodulatory systems. Nat. Neurosci. 22 (2), 289–296.

Sihvonen, A.J., Virtala, P., Thiede, A., Laasonen, M., Kujala, T., 2021. Structural white

matter connectometry of reading and dyslexia. Neuroimage 241, 118411.

decision and naming. J. Mem. Lang. 37 (4), 533–554.

Ziegler, J.C., Muneaux, M., 2007. Orthographic facilitation and phonological inhibition
in spoken word recognition: a developmental study. Psychon. Bull. Rev. 14 (1),
75–80.

11 

