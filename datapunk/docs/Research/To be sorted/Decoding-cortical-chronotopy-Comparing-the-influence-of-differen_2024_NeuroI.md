NeuroImage 303 (2024) 120914 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Decoding cortical chronotopy—Comparing the influence of different
cortical organizational schemes

Falko Mecklenbrauck a,b,*, Jorge Sepulcre c, Jana Fehring b,d, Ricarda I. Schubotz a,b
a Department of Psychology, Biological Psychology, University of Münster, Germany
b Otto Creutzfeldt Center for Cognitive and Behavioral Neuroscience, University of Münster, Germany
c Department of Radiology and Biomedical Imaging, Yale PET Center, Yale School of Medicine, Yale University, New Haven, CT, USA
d Institute for Biomagnetism and Biosignal Analysis, Münster, Germany

A R T I C L E I N F O

A B S T R A C T

Keywords:
Bayesian model comparison
Cortical timescales
DWI
fMRI
Nested hierarchies
Inter-subject correlation
Cortical hierarchies

The brain’s diverse intrinsic timescales enable us to perceive stimuli with varying temporal persistency. This
study aimed to uncover the cortical organizational schemes underlying these variations, revealing the neural
architecture for processing a wide range of sensory experiences. We collected resting-state fMRI, task-fMRI, and
diffusion-weighted imaging data from 47 individuals. Based on this data, we extracted six organizational
schemes: (1) the structural Rich Club (RC) architecture, shown to synchronize the connectome; (2) the structural
Diverse Club architecture, as an alternative to the RC based on the network’s module structure; (3) the functional
uni-to-multimodal gradient, reflected in a wide range of structural and functional features; and (4) the spatial
posterior/lateral-to-anterior/medial gradient, established for hierarchical levels of cognitive control. Also, we
explored the effects of (5) structural graph theoretical measures of centrality and (6) cytoarchitectural differ-
ences. Using Bayesian model comparison, we contrasted the impact of these organizational schemes on (1)
intrinsic resting-state timescales and (2) inter-subject correlation (ISC) from a task involving hierarchically
nested digit sequences. As expected, resting-state timescales were slower in structural network hubs, hierar-
chically higher areas defined by the functional and spatial gradients, and thicker cortical regions. ISC analysis
demonstrated hints for the engagement of higher cortical areas with more temporally persistent stimuli. Finally,
the model comparison identified the uni-to-multimodal gradient as the best organizational scheme for explaining
the chronotopy in both task and rest. Future research should explore the microarchitectural features that shape
this gradient, elucidating how our brain adapts and evolves across different modes of processing.

1. Introduction

The discovery that different brain regions vary in terms of their
processing rhythms or intrinsic timescales (Murray et al., 2014; Ogawa
and Komatsu, 2010; Raut et al., 2020) sparked the investigation of the
possible function of these timescales (for reviews see Cavanagh et al.,
2020; Soltani et al., 2021). One exciting idea is that cortical processes
are organized according to a hierarchy of timescales (Chen et al., 2015;
Hasson et al., 2015; Jeon, 2014; Manea et al., 2022). The different
intrinsic timescales make our brain perfectly adapted for the processing
and representation of the different external nested rhythms in nature
(Golesorkhi et al., 2021b; Wolff et al., 2022). Thus, different areas of the
brain can segregate and integrate incoming stimuli depending on their

own intrinsic timescale and the temporal structure of the stimulus
(Baldassano et al., 2017; Cavanagh et al., 2020; Golesorkhi et al.,
2021b).

of

levels

temporally

persistency

Using hierarchically nested stimuli, previous studies were able to
distinguish cortical areas according to their specific response to hierar-
chical
stimulus
(Aberbach-Goodman and Mukamel, 2023; Farbood et al., 2015; Hasson
et al., 2008; Lerner et al., 2011). For each region, a so-called temporal
receptive window (TRW) was determined (Hasson et al., 2008). Analog-
ical to spatial receptive windows, TRWs describe the specific time frame
of an area in which information of the ongoing stimulus is integrated
(Hasson et al., 2015). Appropriately, areas with longer TRWs were also
found to have slower intrinsic timescales (Chaudhuri et al., 2015; Gao

the

of

* Corresponding author at: University of Münster, Institute of Psychology, Fliednerstr. 21, D-48149 Münster, Germany.

E-mail addresses: f_meck01@uni-muenster.de (F. Mecklenbrauck), jorge.sepulcre@yale.edu (J. Sepulcre), fehringj@uni-muenster.de (J. Fehring), rschubotz@uni-

muenster.de (R.I. Schubotz).

https://doi.org/10.1016/j.neuroimage.2024.120914
Received 15 July 2024; Received in revised form 22 October 2024; Accepted 1 November 2024
Available online 2 November 2024 
1053-8119/© 2024 The Authors. Published by Elsevier Inc. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ). 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

et al., 2020; Honey et al., 2012; Moraczewski et al., 2020; Stephens
et al., 2013).

The origin of different intrinsic cortical timescales and TRWs how-
ever has yet to be determined. The current paper aims to explore and
evaluate multiple alternative cortical foundations of this chronotopy. To
this end, we compared the congruity of different, established cortical
organizational schemes with the chronotopy of the cortex at rest and
during a task.

For the chronotopy at rest, we collected resting-state functional
magnetic resonance imaging (rs-fMRI) and applied a model-free
approach (Raut et al., 2020) to calculate the autocorrelation decay of
each area, which is a valid and direct measure to estimate the intrinsic
cortical timescales (Zilio et al., 2021). The variance of timescales con-
tains meaningful information to distinguish between different cortical
areas (Murray et al., 2014; Ogawa and Komatsu, 2010).

To investigate the chronotopy in a task-setting, we used hierar-
chically nested stimuli to ascertain the distribution of TRWs across the
cortex. Based on previous TRW studies (Farbood et al., 2015; Hasson
et al., 2008; Lerner et al., 2011), we designed digit sequences of four
different, nested levels of temporal persistency. We used inter-subject
correlation (ISC; Hasson et al., 2004, 2010) to determine the reli-
ability of the cortical signal for the four hierarchically structured levels
of the stimulus and thus identified areas that integrate information over
shorter or longer periods of time.

Regarding potential cortical foundations of the chronotopy, we
considered in total six commonly reported organizational schemes and
features:

(1) The structural Rich Club (RC) is a set of highly interconnected
network nodes (Colizza et al., 2006), topologically organized in
resonant network motifs that are particularly efficient in syn-
chronizing neighbouring nodes via their slow intrinsic timescales
(Aguilar-Vel´azquez and Guzm´an-Vargas, 2019; Gollo et al., 2015;
G´omez-Garde˜nes et al., 2010; Senden et al., 2017; Watanabe,
2013). This finding was recently supported by studies showing
that the intrinsic cortical timescales correlate with the connec-
tivity of a node (Fallon et al., 2020; Lurie et al., 2024; Sethi et al.,
2017). Due to its particular architecture of connections, the RC
organization was previously proclaimed as the prime candidate
to shape the brain’s diverse temporal dynamics (Gollo et al.,
2015; Zamora-L´opez et al., 2016).

(2) The structural Diverse Club (DC) was discussed as a competing
topological concept to the RC and possibly might be even more
meaningful for the communication of the network (Bertolero
et al., 2017). Instead of the nodal degree the DC is based on the
structural participation coefficient which describes the member-
ship of a node to multiple network modules (Guimer`a and Nunes
Amaral, 2005) and recently was found to relate to the cortical
timescales as well (Lurie et al., 2024).

(3) Prior studies on the temporal organization of the brain made a
distinction between unimodal and multimodal cortices, finding
timescales to be faster in unimodal as compared to multimodal
cortical areas (Golesorkhi et al., 2021a; Ito et al., 2020; Shafiei
et al., 2020; Wolff et al., 2022). This gradient of cortical hierarchy
was also reflected in functional connectivity (Margulies et al.,
2016), electrophysiological responses (Gao et al., 2020; Honey
et al., 2012), cortical thickness (Burt et al., 2018; Wagstyl et al.,
2015), neural development (Sydnor et al., 2021, 2023), and brain
evolution (Xu et al., 2020). Also, the topological distribution of
TRWs follows a progression from sensory to higher order areas,
with the longest TRWs in frontal and parietal association cortices
(Hasson et al., 2015; J¨a¨askel¨ainen et al., 2021). We defined this
gradient in two different ways: data-driven, based on the stepwise
functional connectivity (Sepulcre et al., 2012) and atlas-based
using the previously introduced functional differentiation (Ito
et al., 2020) in the atlas by Ji et al. (2019).

(4) Cortical frequencies were furthermore found to progress along a
posterior-to-anterior gradient, with the slowest frequencies being
detected towards the frontal cortex (Mahjoory et al., 2020). This
gradient is part of many classical theories of cognitive control
(Fuster, 2001; Kiebel et al., 2008; Koechlin and Summerfield,
2007). Moreover, it was reflected in the expression of genes
(Hansen et al., 2021; Hawrylycz et al., 2012) as well as the
covariance of cortical thickness (Valk et al., 2020) and correlated
with the degree of myelinisation, the brain’s metabolism and
certain frequencies of the electrophysiological power spectrum
(Markello et al., 2022). Lately, the posterior-to-anterior trend was
extended by a lateral-to-medial aspect (Alexander and Brown,
2018) forming a posterior/lateral-to-anterior/medial gradient
that is also mirrored in the intrinsic cortical dynamics (Mahjoory
et al., 2020).

(5) Additionally, we explored how of measures of structural network
centrality relate to the cortical chronotopy. These graph theo-
retical measures classify nodes that are important for an intact
communication throughout the network (Hagmann et al., 2008)
and were recently found to relate the cortical timescales as well
(Fallon et al., 2020; Lurie et al., 2024; Sethi et al., 2017).

(6) Lastly, studies have suggested that an interaction between
microstructural and macro-level connectivity patterns affect the
temporal layout of the cortex (Huntenburg et al., 2018). More
specifically, cytoarchitectonic differences between areas may
shape intrinsic timescales at the microscale (Gao et al., 2020),
reflecting a relationship between myelinisation and timescales
(Ito et al., 2020). Consequently, we also considered cortical
thickness, which can approximate microstructural differences
(Wagstyl et al., 2015).

We modelled the distribution of intrinsic timescales as well as ISC
values across these different, commonly found organizational schemes
and comprehensively contrasted their significance using Bayesian model
comparison (Vehtari et al., 2017). It has to be noted, that the afore-
mentioned organizational schemes and features of the cortex are not
independent of each other (Burt et al., 2018; van den Heuvel et al., 2015;
van den Heuvel and Sporns, 2013b). By directly comparing the organi-
zational schemes, this paper seeks to find the model that best explains
the emergence of different intrinsic timescales and TRWs across the
brain and thus resembles the true cortical organization the closest.

2. Materials & methods

The following method section is divided into five segments: firstly,
general information on the data acquisition and first processing steps;
secondly, a section on the resting-state data, including preprocessing
and the estimation of the intrinsic timescales using autocorrelation
decay; thirdly, an explanation of the preprocessing of the task data and
calculation of the ISC values; fourthly, we describe the identification of
the six organizational schemes of interest, whose influence on the
cortical chronotropy we compared; and lastly, we outline all conducted
statistical analyses and tests.

2.1. General methods

2.1.1. Participants

Data of 47 participants was collected for this study. One participant
was excluded due to movement during the rs-fMRI measurement that
exceeded 1.5 times the voxel size. The remaining NRS = 46 (32 female, M
= 21.76, SD = 2.75 years, range = 18–28 years) were all right-handed
(M = 85.15, SD = 16.46; range = 30–100) as assessed by the Edin-
burgh Handedness Inventory (Oldfield, 1971) and had (corrected-to-)
normal vision. Additionally to the analysis of rs-fMRI data and their
intrinsic timescales, we also collected task data of the same participants.
The task-data was analyzed before using a classic contrast-based fMRI

2 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

analysis (Mecklenbrauck et al., 2024). The present paper reanalyzed the
data using ISC (Hasson et al., 2004, 2010). From the task-fMRI data we
had to exclude a further seven participants because of movement during
the task session (three participants), sub-par attention to the task (one)
and technical difficulties (three). So, the data of NISC = 39 participants
(29 female, M = 21.67, SD = 2.77 years, range = 18–28) entered the ISC
analysis. None reported any history of neurological or psychiatric dis-
eases or any ferromagnetic material inside their bodies. The participants
received money or course credit as renumeration on completion of the
experiment.

2.1.2. Procedure and stimuli

The task-fMRI and the rs-fMRI together with the diffusion-weighted
imaging (DWI) data were acquired in two sessions on separate days
(Fig. 1). The order of the two session was counterbalanced across par-
ticipants with MRS = 7.02 days (SDRS = 5.93 days) or MISC = 6.73 days
(SDISC = 4.70 days) passing between sessions, respectively.

Starting with the DWI-Rest Day, the MRI measurements included an
anatomical T1-weighted image (5 min), multiple sequences for DWI (15
min) and rs-fMRI (8 min). The participants were instructed to lie as still
as possible during the anatomical and DW imaging but could leave their
eyes opened or closed. The experimenters informed the participants via
an intercom system about the start of the rs-fMRI measurement during
which participants looked at a fixation cross (Agcaoglu et al., 2019;
Patriat et al., 2013; Van Dijk et al., 2010). In total 480 rs-fMRI volumes
were acquired.

In the scanning session on the fMRI-Task Day participants completed
a task presenting them with sequences of digits. A detailed description of
the stimuli and their creation was reported before (Mecklenbrauck et al.,
2024). To summarize, we created abstract stimuli (hierarchically nested
sequences of digits) that were inspired by the structure of the hierar-
chically nested natural stimuli previously used to identify TRW (e.g.,
Lerner et al., 2011). The sequences were made up from the digits 4
through 9. Digits 1 to 3 were excluded due to their representation as
quantities (Dehaene, 2001). The sequences were presented one digit at a
time. The hierarchically nested structure of the sequences created four

chucks

experimental conditions:
(1) Single, where the digits appeared
pseudo-randomly (equal transition probabilities between all digits. (2)
In the Triplet condition the digits were presented in predefined chunks of
three (4-5-6, 6-5-4, 7-8-9 and 9-8-7). (3) The Nonet condition then
contained chunks of nine digits with each chunk consisting of three
(4-5-6–4-5-6–4-5-6, 6-5-4–6-5-4–6-5-4,
repeating Triplet
7-8-9–7-8-9–7-8-9 and 9-8-7–9-8-7–9-8-7). (4) Finally, the Complete
condition displayed the entire sequence of 36 digits in which all other
conditions were nested in (4-5-6–4-5-6–4-5-6–-6-5-4–6-5-4–6-5-
4–-9-8-7–9-8-7–9-8-7—7-8-9–7-8-9–7-8-9) (Fig. 2A). We generated de
Bruijn sequences (Brimijoin and O’Neill, 2010; de Bruijn, 1946) to
ideally pseudo-randomize (Aguirre et al., 2011) not only the transition
between single digits and chunks but also the occurrence of the different
blocks in the blocked presentation of the experimental conditions. In
deviation to the passive watching paradigms usually applied in the
context of TRW (e.g., Hasson et al., 2008), we included a task during the
watching of the digit sequences. All sequences were pseudo-randomly
interrupted by inserted zeros. The zeros acted as targets for the partic-
ipants, who had to press a button upon seeing a zero, to keep their
attention on the digits. The zero was chosen specifically due to its
particular role among other numbers (Brysbaert, 1995; Nieder, 2016;
Pinhas and Tzelgov, 2012). We included 18 targets per block of each
experimental condition, so 360 zeros were presented during the entire
fMRI experiment. The zeros were inserted in a way that we could control
how often they interrupted a transition within and between chucks of
the sequence.

The task consisted of 24 blocks, so that the subjects completed each
experimental condition six times. Four blocks (each condition once)
were presented outside the scanner as a training, while the remaining 20
blocks were then part of the main fMRI experiment in the scanner. We
counterbalanced the first condition participants saw. Before each block
subjects were presented with a fixation cross for a jittered duration of
6370–7950 ms. The fixation cross flashed three times to signal the start
of the next block. The blocks themselves were then made up from se-
quences of 162 digits including the 18 targets. The sequences were
presented in trials, one digit at a time. Each trial was 700 ms long. Digits

Fig. 1. Diagram of procedure during the scanning sessions DWI-Rest- and fMRI-Task-Day.
Note. MPRAGE = Magnetization prepared rapid acquisition gradient echo, TR = Time of repetition, TE = Echo time, FOV = Field of view, DWI = Diffusion-weighted
imaging, EPI = Echo planar imaging, MB = Multiband. Note that the order of the two sessions was counterbalanced across participants.

3 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Fig. 2. Experimental paradigm on the fMRI-Task Day.
Note. (A) Example sequences for the four experimental conditions. Colors show nested hierarchical structure. (B) Presentation of digit sequence. Participants had to
press a button when a 0 was presented.

were presented for 400 ms and followed by 300 ms of blank screen. The
participants had the entire 700 ms to react if they saw a zero by pressing
a button with their right index finger (Fig. 2B). As further motivation,
the participants could win additional course credit or money on top of
their standard renumeration based on their performance in the task.
Lastly, we included a one-minute break after five blocks in the scanner in
which the participants were informed about their progress in the
experiment. In total, participants spent approximately 60 min in the
scanner on the fMRI-Task-Day.

All digits and fixation crosses in both scanning sessions were dis-
played on a screen positioned behind the scanner bore and were viewed
◦
by the subjects through an adjustable 45
mirror at a visual angle of
◦
approximately 1.29
. Movements were minimized with form-fitting
cushions. Subjects wore ear plugs and noise-cancelling headphones to
reduce scanner noise.

2.1.3. MRI data acquisition

Brain images were recorded with a 3T Siemens Magnetom scanner
(Siemens, Erlangen) using a 20-channel head coil. Functional blood-
oxygen-level-dependent (BOLD) images during rs-fMRI and task-fMRI
were acquired parallel to the anterior commissure/posterior commis-
sure line. We used a T2*-weighted simultaneous multislice echo-planar
imaging (SMS-EPI; 94 × 94 data acquisition matrix; 210 mm field of
◦
flip angle; time of repetition (TR) = 1000 ms; echo time
view (FOV); 57
(TE) = 34 ms). Each volume consisted of 66 adjacent axial slices with a
slice thickness of 2.2 mm, a gap of 0.11 mm (5 %), and a voxel size of 2.2
× 2.2 × 2.2 mm3. Slice acquisition and multislice mode were inter-
leaved. The acceleration factor was 6.

T1-weigthed anatomical images were acquired using a standard
Siemens 3D MPRAGE sequence for a detailed reconstruction of anatomy
with isotropic voxel size (1 × 1 × 1 mm) in a 256-mm FOV (256 × 256
◦
matrix; 192 slices; 8

flip angle; TR = 2130 ms; TE = 2.28 ms).

For DWI, we applied the parameters of the imaging sequences used in
the Marburg-Münster Affective Disorders Cohort Study (Vogelbacher
et al., 2018). Imaging started with a gradient echo field map (320 mm
◦
flip angle; TR = 616 ms; TE1 = 5.19 ms; TE2 = 7.65 ms; 56
FOV; 60
slices, slice thickness = 2.5 mm; 0 mm gap; voxel size 2.5 × 2.5 × 2.5
mm3; interleaved slice acquisition). This was followed by two times 30
DW images with a b-value of 1000 s/mm2 and in total five non-DW
images (b = 0 s/mm2), that had the same parameters except for their
◦
b-value (320 mm FOV; initial rotation (cid:0) 90
; TR = 7300 ms; TE = 90 ms;
56 slices, slice thickness = 2.5 mm; 0 mm gap; voxel size = 2.5 × 2.5 ×

2.5 mm3; interleaved slice acquisition; GRAPPA acceleration factor = 2).
DWI was completed by a Reverse Phase Encoding sequence (320 mm
◦
FOV; initial rotation (cid:0) 90
; TR = 7300 ms; TE = 90 ms; 56 slices, slice
thickness = 2.5 mm; 0 mm gap; voxel size = 2.5 × 2.5 × 2.5 mm3;
interleaved slice acquisition; GRAPPA acceleration factor = 2).

2.1.4. Cortical parcellation

Parcellating the cortex allowed us to investigate and compare the
cortical organizational schemes across different modalities in a common
reference frame (Eickhoff et al., 2018; Glasser et al., 2016; Tzour-
io-Mazoyer et al., 2002). We applied recon-all from FreeSurfer (v7.2.0;
Fischl, 2012) as well as functions from the Connectivity Analysis
Toolbox (CATO, v3.1.2.; de Lange et al., 2023) on the individual
T1-weigthed anatomical images to reconstruct and parcel the brain’s
surface. The quality of the individually parcellated cortical surfaces was
controlled according to the ENIGMA protocols (https://enigma.ini.usc.
edu/) by one of the authors (FM) and three student assistants. No data
had to be excluded based on the quality control. CATO extends on the
classical Desikan-Killiany parcellation (Desikan et al., 2006) that is
included in FreeSurfer by the Lausanne sub-parcellations (Cammoun
et al., 2012) which divide the larger parcel from the Desikan–Killiany
atlas into equally sized smaller parcels for a higher resolution. For our
analyses we specifically chose the lausanne250 parcellation scheme as it
showed exceptional reliability (Cammoun et al., 2012) and portrays a
meaningful meso-level parcellation of the cortex (Amunts and Zilles,
2015). The application of the lausanne250 parcellation divided the
brain into 219 cortical regions. Note that we did not include subcortical
regions in the analysis as the DWI resolution would not have allowed for
reliable estimation of streamlines (Kai et al., 2022).

2.2. Resting-state fMRI and intrinsic timescales

2.2.1. Preprocessing

For preprocessing the rs-fMRI data we made use of FSL (v6.0; Jen-
kinson et al., 2012) tools also within CATO (de Lange et al., 2023). For
this we discarded the first five volumes as recommended for signal
stabilization (Buxton, 2009; Caballero-Gaudes and Reynolds, 2017). The
functional preprocessing in CATO included slice timing correction using
FSL’s sliceTimer and the application of FSL’s MCFLIRT (Jenkinson et al.,
2002) for the motion correction. The six estimated rigid motion
correction parameters were used to calculate the framewise displace-
ment and change in signal intensity between frames. The calculation of

4 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

both motion metrics was based on Power et al. (2012). Additionally, an
average of all motion corrected volumes was calculated and aligned with
the individual T1-weigthed anatomical image. This alignment enables
the registration of the functional data with the anatomical parcellation
based on the structural data.

The slice time and motion corrected rs-fMRI data was then passed
through a nuisance regression model (Ciric et al., 2017) to remove any
unwanted influences on the data. To this end, we first extracted three
masks from the individual anatomical images using the cortex parcel-
lation from CATO: a whole brain, a white matter and a ventricle mask.
For the regressors of nuisance we extracted the average time series from
the white matter and the ventricles for each subject using these masks.
Also, we calculated the first derivative of the six rigid motion correction
parameters. Lastly, the rs-fMRI time series of each participant was
de-meaned and de-trended. The nuisance regression model
then
removed the influence of the six rigid motion correction parameters and
their six first derivatives as well as the quadratics of all variables. For
noise reduction, a component-based method (CompCor; Behzadi et al.,
2007) was applied on the extracted white matter and ventricle time
series. The top five components of both the white matter and ventricle
signals as well as their derivatives and quadratics were thus also
removed as nuisance from the rs-fMRI data. Lastly, as recommended
(Ciric et al., 2017), we included a spike regression according to Sat-
terthwaite et al. (2013) in the model, removing every spike based on its
framewise displacement.

Returning to CATO, we used the whole brain mask to extract the
nuisance-corrected signal from cortical voxels. This signal was then
bandpass filtered between 0.01 Hz and 0.1 Hz using a standard zero-
phase Butterworth bandpass filter.

2.2.2. Calculation of intrinsic timescales

To analyze the distribution of intrinsic timescales across the cortex
we first needed to extract the time series. Using CATO, we could obtain
the individual, averaged time series from of the 219 cortical parcels from
the lausanne250 parcellation (see Section 2.1.4). Based on these time
series, we estimated the intrinsic timescale of each parcel via the decay
of the autocorrelation function (ACF). We applied a model-free pro-
cedure (Raut et al., 2020) to determine the decay of the ACF. Applying
the published code from Raut et al. (2020) we first de-meaned the
nuisance-corrected rs-fMRI signal of every participant. We then deter-
mined the ACF by first calculating the lagged covariance in 24-s window
for all lag Δ ϵ [(cid:0) 12,12],

cx(Δ) =

∑T(cid:0) |Δ|

1

T (cid:0)

|Δ|

t=1

x(t + Δ) ∗ x(t)

(1)

before normalizing the results by the covariance at lag 0, so that rx(0) =
1,
rx(Δ) = cx(Δ)
cx(0)

(2)

The resulting rx(Δ) can be interpreted as the lagged autocorrelation
rather than covariance. The intrinsic timescale for each individual par-
cel was then determined as the precise abscissa of the ACF at rx(Δ) = 0.5,
which describes the half of the full width at half maximum of the
function. This calculation was achieved with the fnzeros function in
MATLAB which computes the zeros of a spline fit of a function.

2.3. Task-fMRI

2.3.1. Preprocessing

Processing of the task data for the ISC analysis was based on the
procedure described in Nastase et al. (2019). Preprocessing was
completed using Statistical Parametric Mapping software (SPM12; FIL
Methods Group, 2017) implemented in MATLAB (Version 9.10.0
[R2021a]; The MathWorks Inc., 2021) and included slice time

correction to the spatially and temporally middle slice, realignment,
co-registration to anatomical data, normalization to MNI space and
smoothing using a 6 × 6 × 6 mm3 Gaussian smoothing kernel. The signal
was further high-pass filtered at 1/160 s based on previous results
(Mecklenbrauck et al., 2024). The nuisance regression in accordance
with the recommendation (Nastase et al., 2019) included the six motion
parameters estimated during realignment as well as the averaged white
matter and cerebral-spinal-fluid signal. Additionally, we included all
button presses of the subjects as a regressor of nuisance which was
convolved with the canonical hemodynamic response function. For
modelling, we applied the FAST algorithm to correct for autocorrelation
as recommended for TR ≤ 1.4 s (Corbin et al., 2018). The following ISC
analysis was performed on the residuals of the nuisance regression. In
preparation of the ISC analysis, the residuals were z-scaled and masked
with an average grey matter mask before concatenating the blocks of
each experimental condition in the same order
into a single
four-dimensional file for each condition, synchronizing the digit pre-
sentation across subjects.

2.3.2.

Inter-subject correlation

ISC is a measure of neural synchrony or reliability (Redcay and
Moraczewski, 2020). The method requires a synchronized presentation
of the same stimuli across subjects (Nastase et al., 2019). A high ISC
value in a voxel then suggests that this voxel holds information about the
presented stimulus as the synchronized stimulus is the only common-
ality between all participants which creates this correlation (Nastase
et al., 2019). In the context of hierarchically structured stimuli, partic-
ipants are presented with different hierarchically nested levels of the
stimuli (e.g., Lerner et al., 2011). These levels differ by their temporal
persistency, with hierarchically higher levels of the stimulus being more
persistent (Uithol et al., 2012). Voxels that only depict higher ISC values
in conditions that present more temporally persistent levels of the
stimulus, have longer TRWs to process the longer persistence in the
stimulus. Voxels with shorter TRWs on the other hand already have
higher ISC values for more transient levels of the stimulus, but also show
increased values for hierarchically higher levels, as the more transient
levels are nested within the more persistent levels of the stimulus
structure.

For the calculation of the ISC, we opted for the leave-one-out-method
of ISC calculation to allow us later to apply classical statistical methods
(Nastase et al., 2019; Thomas et al., 2018). Therefore, we adjusted
available code (Nastase et al., 2019) to calculate individual ISC maps for
each experimental condition. Finally, the ISC values were Fisher
z-transformed to help with the normal distribution of the correlation
values (Bond and Richardson, 2004). Based on these maps we extracted
the average ISC value for each cortical parcel in the lausanne250 par-
cellation scheme. Therefore, we parcellated the individual normalized
brains of each subject using the Multi-Scale Brain Parcellator (Tourbier
et al., 2019), extracted the parcels as binary maps and dilated these
maps three-dimensionally by one voxel size using functions from the
WFU pick atlas toolbox (Maldjian et al., 2003) to accommodate for the
smoothing of the data. These individual averaged ISC values for each
parcel in each experimental condition were the basis of the following
analyses.

2.4. The six organizational schemes of interest

As outlined in the introduction, our goal was to find a cortical
organizational principle that best explains the distribution of intrinsic
timescales and ISC values. We considered the following six candidate
organizational schemes: (1) the RC architecture, (2) the DC architecture,
(3) the uni-to-multimodal gradient, and (4) the posterior/lateral-to-
anterior/medial gradient. Additionally, we explored the relationship
of the chrontopy with (5) different graph theoretical measures of the
individual structural networks as well as (6) cortical thickness as an
approximation of cytoarchitectural differences (Wagstyl et al., 2015).

5 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

The extraction all organizational schemes will be described in the
following sections.

2.4.1. Rich Club architecture

For the individual RC architecture (as well as the DC architecture
(see Section 2.4.2) and graph theoretical measures of network centrality
(see Section 2.4.5)), we first had to reconstruct the structural network
from the estimated white matter streamlines.

2.4.1.1. Structural network reconstruction. To reconstruct the structural
white matter network, we used the same pipeline as in Mecklenbrauck
et al. (2024). Thus, we applied the structural pipeline from CATO (de
Lange et al., 2023) which calls upon FreeSurfer (Fischl, 2012) and FSL
(Jenkinson et al., 2012) for the structural (pre-)processing steps.
Building on the reconstruction and parcellation of the cortical surface
(see Section 2.1.4), the structural pipeline started by applying fslmerge,
topup (Andersson et al., 2003; Smith et al., 2004) and eddy (Andersson
and Sotiropoulos, 2016) of the FSL package to merge the DWI data and
correct susceptibly as well as movement and eddy current artefacts. We
then continued using CATO to reconstruct the white matter network
using a combined diffusion tensor imaging (DTI) and generalized
Q-sampling imaging (GQI; Yeh et al., 2010) model. This model showed
the best benchmark results in respect to false positive and false negative
streamlines (de Lange et al., 2023). GQI helps with solving the issue of
multiple diffusion peaks in the case of crossing or kissing fibers. Thus,
the combined method applied the classical informed RESTORE algo-
rithm (Chang et al., 2005, 2012) for DTI modelling in cases of single
diffusion peaks and opted for the GQI algorithm in more complex cases.
The white matter tracts were then reconstructed deterministically using
the FACT algorithm (Mori et al., 1999) adjusted for multiple diffusion
peaks. The creation of connectivity matrices used the standard settings
of CATO which are derived from van den Heuvel et al. (2013). There-
fore, the algorithm started with eight seeds from each voxel included in
the whole brain mask and followed the main diffusion direction to the
next voxel until one of five stop cases occurred: (1) The algorithm
reached a voxel with a low fractional anisotropy value (FA < 0.1), which
often represents a grey matter voxel. (2) The reconstructed streamline
exited the brain mask. (3) The streamline turned at an angle larger than
45
. (4) The reconstruction reentered a previously visited voxel. (5) The
streamline reached the cerebellum. Only streamlines that fully con-
nected two brain regions were considered for the connectivity matrices.
The connectivity matrix of each subject was subsequently generated by
combining these estimated streamlines with individual parcellated
anatomical images. In accordance with the lausanne250 parcellation
scheme we ended up with 219 × 219 connectivity matrices for each
subject. Lastly, we controlled the individual structural connectivity
matrices for outliers (van den Heuvel et al., 2019). No connectivity
matrix showed any outliers, so all matrices were suitable for graph
theoretical analysis.

◦

2.4.1.2. Rich Club hub classification. The general procedure of the RC
identification (Fig. 4A) was reported in Mecklenbrauck et al. (2024) and
was inspired by Riedel et al. (2022). To summarize, we calculated the RC
coefficient ϕ(k) in binarized structural connectivity matrices. The RC
coefficient was then normalized based on the mean of 2500 random
networks. The random networks were created by rewiring each
connection of the empirical network ten times. Using the formula re-
ported by van den Heuvel and Sporns (2011) we identified a range of
degrees k, for which the empirical RC coefficient was significantly (α =
0.05) larger than in the random networks. Significant evidence for this
so-called RC regime (van den Heuvel and Sporns, 2011) indicated the
presence of RC organization in the network. Based on this RC regime we
used the previously described criteria (Mecklenbrauck et al., 2024;
Riedel et al., 2022) to identify nodes of the network as possible hubs: (a)
A node was in the top 15 % of highest degrees. (b) The degree of a node

closeness

centrality,

betweenness

calculation of

was at least as large as the start degree of the RC regime. (c) A node’s
degree was at least as large as the degree k with the largest normalized
RC coefficient within the RC regime. (d) The node was within the top 33
% in four of five measures of node centrality: nodal degree/degree
centrality,
centrality,
between-module participation coefficient, and within-module degree
z-score. The
the participation coefficients and
within-module degree z-degree requires the determination the module
partition. Like Riedel et al. (2022), we identified this partition in a 60 %
prevalence-based group-average network using the Louvain algorithm
(Blondel et al., 2008). For this purpose, we first determined the optimal
module resolution γ (Lurie et al., 2024). A higher resolution, so a larger
value of γ, leads to a more nuanced module differentiation. We varied γ
between the values of 0.5 and 3.5 (in increments of 0.1) using the
Louvain algorithm (community_louvain.m) for module identification
1000 times per value of resolution γ. We then found the agreement
between these 1000 partitions at each resolution γ (agreement.m). Using
consensus-based clustering 100 times (consensus_und.m; τ = 0.6), we
identified a stable module partition at every level of resolution. To find
the best resolution as describes by Lurie et al. (2024) we calculated the
variation of information (Meilǎ, 2003), i.e., the similarity between the
partition across all levels of resolution. The most representative module
partition then was determined by the lowest median variation of in-
formation thus identifying the optimal module resolution γ. This most
representative module partition was ultimately used for the calculation
of the between-module participation coefficient and the within-module
degree z-score. For the group-wise matrix in this case we determined the
optimal γ = 2.3 (10 communities).

Importantly, the four hub definition criteria (a–d) introduced above
do not necessarily result in a single consistent hub definition. To achieve
this congruent definition, we applied additional criteria. Firstly, we only
considered nodes that were labelled as hubs in at least three of the four
criteria. Secondly and most vitally, we compared the proportions of
edges between the identified hubs in the empirical structural with the
inter-hub connections in the 2500 random networks. As the RC is
defined by a particularly high connectivity between hub regions (Colizza
et al., 2006), we used false discovery rate (FDR)-corrected Wilcoxon
signed-rank test to test whether the possible hubs were more likely to
connect to each other in the empirical network than in the 2500 random
networks. The final set of RC hubs only contained nodes that were
significantly more interconnected in the empirical network. We then
classified nodes as Feeder nodes if they were directly connected to an RC
hub but not part of the RC, and as Local nodes all nodes that were neither
part of the RC nor connected to it.

In deviation to the previously applied identification (Mecklenbrauck
et al., 2024), we classified the parcels as RC hub, Feeder node or Local
node not in a group-averaged network but individual binarized con-
nectivity matrices. Therefore, we binarized the individual matrices by
setting every edge with at least three streamlines (Number of Stream-
lines ≥ 3) to one and all others to zero, as recommended for individual
binarized connectivity matrices to correct for false positive edges
(Brown et al., 2011). As described, following previous practice (Lurie
et al., 2024; Riedel et al., 2022) only the module partition was based on
the group-averaged binary connectivity matrix. This resulted in indi-
vidual classifications of RC hubs, Feeder nodes and Local nodes. At this
point, we had to exclude two participants from further analyses, as they
did not depict RC architecture, reducing the sample size for the time-
scale analysis to NRS = 44 and the ISC analysis to NISC = 37.

2.4.2. Diverse Club architecture

The procedure to identify DC hubs was in large parts similar to the
RC hub identification (Fig. 5A). To determine if a DC architecture was
present, we applied the modified clubness coefficient, that can calculate
clubness not just on basis of the degree centrality but based on any nodal
measure (Bertolero et al., 2017). Here we used the between-module
participation coefficient as the nodal measure to identify a club of

6 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

nodes which are particularly well connected with the modules of the
network. As the module structure is central to the participation coeffi-
cient, we determined the optimal modularity not in a group-average
network, like in the RC identification, but in each subject’s network
individually. As for the RC, we then normalized the DC coefficient on the
basis of 2500 random networks using the same individual module
classification for all random networks. We validated the presence of DC
architecture in each subject by identifying a range of participation co-
efficients for which the empirical DC coefficient was significantly (α =
0.05) larger than on average in the random networks; thus, mirroring
the procedure for RC coefficients (van den Heuvel and Sporns, 2011).
Furthermore, only one criterion was used to determine possible hubs:
Following Bertolero et al. (2017) the top 20 % of the participation co-
efficient distribution was considered as a hub. Finally, to identify the DC
hubs, we compared the proportions of inter-hub connections between
the empirical and random networks, as we did for RC hubs. We only
classified hubs as DC hubs if they connected to significantly more other
hubs in the empirical network than in the random networks. Again, we
used an FDR-corrected Wilcoxon signed-rank test to validate this com-
parison. Further, we also classified Feeder nodes and Local nodes based
on the connections to the identified DC.

2.4.3. Uni-to-multimodal gradient

To identify parcels that are functionally classified as multimodal we
used two different strategies: a data-driven approach using SFC
(Fig. 6A1; Sepulcre et al., 2012) and an atlas-based approach employing
the classification of functional modules introduced in Ji et al. (2019)
(Fig. 6A2; Golesorkhi, Gomez-Pilar, Tumati, et al., 2021; Ito et al.,
2020). Both approaches were validated by correlating the resulting
uni-to-multimodal gradient maps with other previously established
uni-to-multimodal gradients (Margulies et al., 2016; Sydnor et al., 2021;
see Supplemental Material 1).

2.4.3.1. Stepwise functional connectivity. The SFC analysis calculates
paths through the functional network starting at a seed region. It then
maps the connectivity pattern of that seed region or multiple seed re-
gions at different so-called link-step distances, so progressions of the
connectivity along the calculated paths. In their seminal paper Sepulcre
et al. (2012) demonstrated that when starting the paths in the primary
visual, auditory and somatosensory cortices the paths reach a steady
state after seven link-steps. The stable pattern of SFC converged in re-
gions of the brain that can be described as cortical hubs or multimodal
areas (e.g., Sepulcre et al., 2010). To capture the full spectrum of the
uni-to-multimodal gradient from the SFC maps, we extracted the
normalized SFC pattern at link-step one, which specifies the unimodal
areas (Sepulcre et al., 2012), as well as the normalized SFC map at
link-step seven to locate the multimodal hubs. Subtracting the SFC maps
at the first step from the maps at link-step seven combines the topog-
raphies to portray the extent of the uni-to-multimodal gradient in one
single map. The resulting values are higher for multimodal and lower for
unimodal areas.

Therefore, we first aligned the individual, preprocessed and
nuisance-regressed rs-fMRI data (see Section 2.2.1) to the MNI standard
space using SPM12. In doing so, images were downsampled to a voxel
resolution of 8 × 8 × 8 mm3. This downsampling rendered the voxel-
wise connectivity matrices computationally manageable (Pretus et al.,
2019; Sepulcre et al., 2012). We again used functions from CATO (de
Lange et al., 2023) to extract the time course signal of 475 resting-state
acquisition timepoints. The signal was extracted on the voxel level from
a whole brain mask, which included 4575 8 × 8 × 8 mm3 voxels. This
signal was then filtered between 0.01 Hz and 0.1 Hz using a standard
zero-phase Butterworth bandpass filter. For the SFC analysis we firstly
calculated the individual 4575 × 4575 connectivity matrices using
product-moment correlation. Only positive correlations were consid-
ered. Additionally, the correlations were Fisher z-transformed and then

normalized between 0 and 1. To correct the adjacency matrix for false
positive connections, we applied a conservative Bonferroni-correction at
a significance level of α = 0.001. Coherent with recent publications
using SFC (Bueichekú et al., 2020; Diez and Sepulcre, 2018; Ortiz-Ter´an
et al., 2017), we used these filtered weighted adjacency matrices for the
analysis instead of binarizing them. We determined the normalized SFC
at each link-step distance up to seven steps for each individual subject.
As seed regions, we used the following MNI coordinates (x, y, z), iden-
tified based on the coordinated reported in Sepulcre et al. (2012) and
further consultation of the SPM Anatomy Toolbox (Eickhoff et al.,
2005): left visual ((cid:0) 8, (cid:0) 85, 4), right visual (8, (cid:0) 83, 4), left auditory
((cid:0) 47, (cid:0) 19, 8), right auditory (43, (cid:0) 32, 11), left somatosensory ((cid:0) 42,
(cid:0) 29, 65) and right somatosensory (38, (cid:0) 29, 65). Each of these seeds was
comprised of a single 8 × 8 × 8 mm3 voxel. To have a single SFC map per
subject at each link-step we averaged the stepwise maps of all six seeds.
We then subtracted the averaged, individual SFC maps at the first step
from the maps at the seventh link-step to estimate the topography of the
uni-to-multimodal gradient for each subject. Finally, we extracted the
individual, averaged results from of uni-to-multimodal gradient maps
for each parcel of the lausanne250 parcellation to arrive at a continuous
representation of multimodality that can be related to the cortical
chronotopy.

2.4.3.2. Ji atlas-based multimodality. The functional atlas introduced by
Ji et al. (2019) is based on the Glasser atlas (Glasser et al., 2016). Each
parcel in the surface-based Glasser atlas is assigned to one of twelve
functional networks: Auditory, Visual1, Visual2, Somatomotor,
Cingulo-Opercular, Default, Dorsal-Attention, Frontoparietal, Language,
Orbito-Affective, Posterior-Multimodal, Ventral-Multimodal.
In the
distinction of unimodal and multimodal areas, previous papers labeled
all parcels belonging to Auditory, Visual1, Visual2 and Somatomotor
networks as unimodal or “periphery”, and all others as multimodal or
“core” (Golesorkhi et al., 2021a; Ito et al., 2020). To also assign the
parcels of the lausanne250 parcellation to these categories, we deter-
mined the overlap between a parcellation of the MNI standard brain
according to the Lausanne atlas (Cammoun et al., 2012) and a
voxel-wise version of the Glasser atlas published by Horn (2016) and
adjusted by Gorgolewski (2016). The comparison gave us a percentage
for each parcel of the Lausanne atlas describing how much of its volume
belonged to a multimodal area according to the definition by Ito et al.
(2020). These percentages also described a continuous way of oper-
ationalizing multimodality to be related to the cortical timescales and
ISC values.

2.4.4. Posterior/lateral-to-anterior/medial gradient

For the approximation of the posterior-to-anterior and lateral-to-
medial gradients which are part of many theories on cortical organiza-
tion (e.g., Alexander and Brown, 2018), we considered the average MNI
coordinates of each parcel of a subject’s cortex (Fig. 7A). Thus, we
averaged the x-, y- and z- coordinates in FreeSurfer reference space
(MNI305/fsaverage space; Fischl, 2012) of each parcel for each indi-
vidual parcellation. We used the absolute values of the x-coordinate to
model the lateral-to-medial trend, while an effect of the y-coordinate on
the cortical chronotopy might signal a posterior-to-anterior trend, as
was indicated previously (Mahjoory et al., 2020). The z-coordinates
were used as control variables in all models.

2.4.5. Graph theoretical measures of network centrality

Furthermore, we considered graph theoretical measures of centrality
of the parcels as explanatory variables. Therefore, we included the five
the RC
nodal measures that were used in the identification of
(Mecklenbrauck et al., 2024; Riedel et al., 2022): degree centrality,
betweenness centrality, closeness centrality, participation coefficient,
and within-module degree z-score (Fig. 8A). For participation coefficient
and within-module degree z-score we however used the individual

7 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

optimal module distribution that was
identification.

calculated for

the DC

2.4.6. Cortical thickness

The surface-based morphometry measures were calculated based on
the surface tessellation using FreeSurfer (Dale et al., 1999). The cortical
thickness can be calculated from the distance of the white matter surface
and the pial surface, while the surface is described by the area of the
vertices spanning the cortex (Fig. 9A; Goto et al., 2022). As a possible
organizational scheme, we only explored the average cortical thickness
(in mm) as it can be seen as an approximation for cytoarchitectural
differences between the areas (Wagstyl et al., 2015) which were previ-
ously suggested to shape the cortical dynamics (Gao et al., 2020). The
surface area (in mm2) on the other hand was used as a control variable in
all models of both the timescale and ISC analyses.

2.5. Statistical data analysis

2.5.1. Spin test analysis

To identify similarities between the six organizational schemes as
well as the intrinsic timescales cortical and ISC values per experimental
condition prior to the formal analysis we calculated Pearson correlation
between all variables averaged over all subjects. As the RC and DC
classifications are categorial variables we used the mode for each parcel
instead of the mean. Also, we did not determine a correlation but used
the Kruskal–Wallis-test and the χ²-test of independence, respectively, to
assess their relationship with the other continuous variables and be-
tween each other. Finally, we calculated the effect sizes of the test sta-
tistics (η2 and Cramer’s V; Tomczak and Tomczak, 2014) to compare
them with the correlations. We tested the significance of these correla-
permutations
tions
(Alexander-Bloch et al., 2018) implemented in the neuromaps toolbox
(Markello et al., 2022). The spin test accounts for the spatial autocor-
relation of the cortical maps by rotating their spherical surface projec-
tion and thus creating a null distribution of the maps whilst keeping
spatial features of the original map intact. The p-values of the test are
then calculated by comparing how many of the permutated correlations,
based on rotated maps, are equal or larger than the original correlation
coefficient based on the initial orientation (Alexander-Bloch et al.,
2018). Finally, we applied FDR correction (Benjamini and Hochberg,
1995) to correct the spin test results for multiple testing.

via 100,000 spin test

and effect

sizes

2.5.2. Resting-state timescale analysis

Data analyses were performed using R (Version 4.2.2.; R Core Team,
2022) and RStudio (Version 2022.7.2.576; RStudio Team, 2022).
Bayesian hierarchical generalized linear modelling was executed using
the brms library in R (Bürkner, 2017). All model equations were con-
structed from the same base formula:

Resting-state timescales ~ 1 + ORGANIZATIONAL SCHEME + Surface area + z-
Coordinate + ICV + (1|Subject)
(3)

For the ORGANIZATIONAL SCHEME we were first interested in (1) the in-
dividual RC architecture of each subject. Second, the timescales were
modelled by (2) the individual DC classification. The next set of models
concerned in the effect of (3) the uni-to-multimodal gradient on the
timescales. One model looked at the individually determined gradient
calculated from SFC and the other uni-to-multimodal model included
the percentage of each area that was part of a multimodal area according
to the Ji atlas-based classification by (Golesorkhi et al., 2021a; Ito et al.,
2020). Fourth, one model included the average x- and y-coordinates of
each parcel, as well as
the
posterior/lateral-to-anterior/medial gradient. Note that the absolute
values of the x-coordinates were calculated to model a lateral-to-medial
rather than a left-to-right gradient. Fifth, we built a model that included
(5) all five centrality measures we considered. Finally, a model used (6)

interaction to model

their

(4)

the areas’ average cortical thickness as organization of interest. Addi-
tionally, all models controlled for the surface area and average z-coor-
dinate of an area as well as the intracranial volume (ICV) of each
participant and included a random intercept for each subject. All
continuous independent variables were z-scaled for better interpret-
ability of the intercepts.

We prepared the data by taking the natural logarithm of the time-
scales and excluded outliers (below Q1 (cid:0) 1.5 × IQR or above Q3 + 1.5 ×
IQR). The following inspection of the Cullen-Frey plots to judge the
skewness and kurtosis of the data revealed that we could assume a
distribution from the gaussian family for all models (Cullen and Frey,
1999). For estimating the models in brms we used uninformative priors
as it is recommended for multilevel modelling (Bürkner, 2017). For β
coefficients we used a flat prior and for the standard deviation a Stu-
dent’s t(3, 0, 2.5) distribution was applied. All models were then
calculated with ten chains, each with 4000 iterations, from which the
first 1000 were warmups, setting the target average proposal acceptance
probability (adapt_delta) to 0.99. Convergence within and between
chains was examined through the improved convergence diagnostic ̂R,
with values under 1.05 indicating successful convergence (Vehtari et al.,
2021). Further, we used posterior predictive checks to evaluate whether
the models captured the observed data (Kruschke, 2011). We tested the
effects of the different organizational schemes of interest on the intrinsic
timescales using the hypothesis function from the brms library (Bürkner,
2017). Bayes factors for one-sided hypotheses are defined by the evi-
dence ratio (Bürkner, 2018). Generally, evidence ratios >10 are
considered strong evidence for the tested hypothesis (van Doorn et al.,
2021).

(1) For the RC architecture, we expected that the areas classified as
RC would show slower timescales than the areas classified as Feeder and
Local nodes, while Feeder nodes also have slower timescales than in
Local nodes (Gollo et al., 2015). (2) Likewise, for the DC architecture, we
would envision the areas classified as DC to be the slowest, followed by
Feeder nodes and then Local nodes. (3) Based on previous results (e.g.,
Ito et al., 2020), we assumed slower timescales with increasing multi-
modality for both uni-to-multimodal gradient approaches. (4) In the
posterior/lateral-to-anterior/medial gradient model, we predicted the
slowest timescales to be located to the medial frontal lobe (Mahjoory
et al., 2020). So, we expected a positive trend for y-coordinates and
negative trend for x-coordinates as well as negative interaction effect on
the timescales. Based on prior findings related, a positive relationship
between (5) the centrality measures (Fallon et al., 2020; Lurie et al.,
2024) as well as (6) thicker cortical areas (Gao et al., 2020) and slower
intrinsic cortical timescales could be suggested.

As it was the purpose of this study to find the best fitting organiza-
tional schemes, we did not specify a preferred model in advance, to not
bias the analysis. However, judging from previous studies we expected
the RC architecture to play a major role in shaping the intrinsic time-
scales of the cortex (e.g., Gollo et al., 2015).

2.5.3.

Inter-subject correlation analysis

After inspection of the Cullen–Frey plots, we excluded outlier values
(below Q1 (cid:0) 1.5 × IQR or above Q3 + 1.5 × IQR) to reduce kurtosis of
the distribution (Cullen and Frey, 1999). In the same way as with the
intrinsic timescales we modelled the distribution of ISC values by the
interest. Now we additionally
different organization schemes of
included the CONDITION in interaction with the ORGANIZATIONAL SCHEME as
an independent variable:

ISCFisher z ~ 1 + CONDITION × ORGANIZATIONAL SCHEME + Surface area + z-
Coordinate + ICV + (1|Subject)
(4)

The factor CONDITION included four levels: Single, Triplet, Nonet, and
Complete. For the ORGANIZATIONAL SCHEME we focused on the same six
organizational schemes of interest as for the resting-state timescales (see
Section 2.5.2). The models further again included the surface area of

8 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

each parcel in mm2, the area’s z-coordinates in MNI space, the inter-
cranial volume of each participant in liters and a random intercept on
the level of subjects as control. The continuous independent variables
were again z-scaled.

The estimation of all models in brms used uninformative priors as it
is recommended for multilevel modelling (Bürkner, 2017). For β co-
efficients we used a N(0, 5) distributed priors while Student’s t(3, 0, 5)
distribution was applied as prior for the standard deviations. We made
use of the skewed normal family for the models. All models were then
calculated with ten chains, each with 4000 iterations, with 1000
warmups. We left the target average proposal acceptance probability
(adapt_delta) at the default of 0.8 but increased the maximal treedepth
to 15. Convergence of the chains was monitored using the improved

̂
convergence diagnostic
R (Vehtari et al., 2021). Applying posterior
predictive checks, we assessed the coherence between the modelled and
observed data (Kruschke, 2011). We tested the effects of the different
organizational schemes of interest on the ISC values across experimental
conditions using the hypothesis function from the brms library (Bürkner,
2017).

Based on previous investigations on TRWs (Farbood et al., 2015;
Hasson et al., 2015; Lerner et al., 2011), we generally expected that
higher order structures in the organizational schemes are more involved
in the processing of hierarchically higher structures in the stimuli, i.e., in
the conditions Nonet and Complete. Specifically, we thus expected for
the (1) RC and (2) DC classification that the ISC values in Local nodes do
not differ across the experimental conditions, as the Local nodes handle
the processing of more transient stimuli which are included in all hier-
archically nested levels (Gollo et al., 2015). Further we assumed that the
hubs in both classifications then show increased ISC values for hierar-
chically higher stimulus structures as hubs of the structural core are
engaged by more persistent stimuli (Gollo et al., 2015). If the tested
gradients better explained the processing of hierarchically structured
stimuli we would expect
the uni-to-multimodal and (4)
posterior/lateral-to-anterior/medial trends to be more pronounced for
the processing of hierarchically higher stimuli structures, as the higher
order regions only show an increase in ISC values with these more
persistent stimuli (Wolff et al., 2022). In line with the timescale hy-
potheses, we would also expect that the effects of (5) the graph theo-
retical measures of centrality as well as (6) cortical thickness on the ISC
values would be more pronounced for hierarchically higher conditions.

(3)

2.5.4. Bayesian model comparison

Finally, we compared the models using Bayesian statistics to find out
which cortical organizational scheme best explains the respective dis-
tributions of resting-state timescales and ISC values across the cortex.
Bayesian model comparison, in contrast to its frequentist counterpart,
does not require the compared models to be nested and thus is ideal to
evaluate different competing theories (Geweke, 2007; Hollenbach and
Montgomery, 2020; Rouder et al., 2018). We ran leave-one-out-cross
validations (LOO-CV) and used the results to estimate the expected log
pointwise predictive density (elpdloo) for each model. The elpdloo describes
a model’s accuracy in predicting future, out-of-sample data and thus
captures the goodness of fit of the model while also controlling for
overfitting (Gelman et al., 2014). The elpdloo value can be both positive
or negative, with higher values (meaning closer to zero in the case of
negative values) indicating a better predictive performance (Vehtari,
2024).
of
high
cross-validations, LOO-CV can be approximated using Pareto smoothed
importance sampling (Vehtari et al., 2017). When comparing models
using elpdloo, a model is considered better when the absolute difference
in elpdloo between the compared models is larger than one standard
error (se(elpdloo); Mohor et al., 2021).

computational

To mitigate

demands

the

3. Results

3.1. Spin test

The spin test results reporting the similarity between organizational
schemes as well as the chronotopy are depicted in Fig. 3. A Krus-
kal–Wallis-test revealed that
the intrinsic resting-state timescales
differed significantly between the classifications as Local, Feeder or DC
hub according to the DC architecture, H(2) = 31.99, ηH² = 0.14, pspin =
0.018. Appropriately, also the participation coefficient correlated
significantly with the resting-state-timescales, r = 0.27, pspin = 0.039.
Moreover, a χ²-test showed that the DC classification and the RC clas-
sification in Local, Feeder and RC hub were significantly dependent,
χ²(2, N = 219) = 195.97, V = 0.67, pspin = 0.003. We also found that the
SFC-based uni-to-multimodal gradient correlated significantly with the
resting-state timescales, r = 0.48, pspin = 0.003, and the Ji atlas-based
estimation of the uni-to-multimodal gradient, r = 0.52, pspin = 0.002.
Additionally, the uni-to-multimodal-gradient based on SFC correlated
negatively with the ISC values in the Single condition, r = (cid:0) 0.31, pspin =
0.027, Triplet condition, r = (cid:0) 0.31, pspin = 0.006, Nonet condition, r =
(cid:0) 0.31, pspin = 0.012, and Complete condition, r = (cid:0) 0.43, pspin = 0.003.
Furthermore, the spin test revealed that the percentage of overlap with a
multimodal area in the Ji atlas (Ji et al., 2019) correlated significantly
negatively with the ISC values in the Complete conditions, r = (cid:0) 0.43,
pspin = 0.006.

Beyond that, we found several significant correlations between the
graph theoretical measures of centrality. The degree centrality corre-
lated significantly with closeness centrality, r = 0.72, pspin = 0.001,
betweenness centrality, r = 0.79, pspin = 0.001, participation coefficient,
r = 0.59, pspin = 0.002, and within-module degree z-score, r = 0.79, pspin
= 0.001. Closeness centrality correlated also with betweenness cen-
trality, r = 0.79, pspin = 0.001, the participation coefficient, r = 0.76,
pspin = 0.002, and the within-module degree z-score, r = 0.33, pspin =
0.001. Lastly, the correlations of betweenness centrality with the
participation coefficient, r = 0.76, pspin = 0.002, and the within-module
degree z-score, r = 0.46, pspin = 0.001, were also significant.

Finally, all the ISC values of the different experimental conditions
were significantly correlated with each other. The ISC values of the
Single condition shared correlations with the Triplet, r = 0.76, pspin =
0.002, Nonet, r = 0.83, pspin = 0.002, and Complete conditions, r = 0.79,
pspin = 0.002. The values of the Triplet condition correlated with the
values in the Nonet, r = 0.82, pspin = 0.002, and Complete conditions, r =
0.81, pspin = 0.003. Also, the ISC values of the Nonet and Complete
conditions were significantly correlated, r = 0.84, pspin = 0.002. Note,
reported p-values of the spin tests are FDR-corrected.

3.2. Results of the six organizational schemes

All models successfully converged as evaluated by the convergence

̂
R (Vehtari et al., 2021; for more details see Supplemental
diagnostic
Tables S2.1 & S2.2). Graphical assessment affirmed that the predictive
posterior distributions reasonably replicated the distributions as well as
the means of the observed data (Supplemental Figs. S3.1–S4.8). Exam-
ining the multicollinearity resulted in no variance inflation factors over
the threshold of ten (Wooldridge, 2013; Supplemental Figs. S3.1–S3.8).
To test our hypotheses about the different organizational schemes we
drew posteriors from the estimated models (Supplemental Tables S2.1 &
S2.2).

3.2.1. Rich Club architecture

Beginning with the resting-state timescales, for the RC architecture
the hypothesis tests revealed a significance increase in timescales be-
tween Local nodes and Feeder nodes as well as a significantly slower
timescales in RC hubs than Local nodes, while RC hubs did not differ
from Feeder nodes (Fig. 4B).

9 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Fig. 3. Results of the exploratory spin tests.
Note. For Rich Club and Diverse Club effect sizes (η2 and Cramer’s V) are reported instead of Pearson correlation coefficient. RC = Rich Club, DC = Diverse Club, SFC
= Stepwise functional connectivity, ISC = Inter-subject correlation, * pFDR < 0.05.

Looking at the results for the ISC values, the tests revealed no sig-
nificant differences between RC hubs, Feeder nodes and Local nodes in
any experimental condition. Only testing for equal ISC values between
conditions showed significant results, which suggests that we could not
find an increase of ISC values of the temporal persistency of hierar-
chically structured stimulus in neither RC hubs nor Feeder nodes
(Fig. 4C).

3.2.2. Diverse Club architecture

Regarding the resting-state timescales, we found a significant in-
crease in the estimated mean timescale between Local nodes and DC
hubs and between Feeder nodes and DC hub, while Local nodes did not
differ from Feeder nodes (Fig. 5B).

The task data revealed a very similar pattern to the RC architecture.
The Local nodes, Feeder nodes and DC hubs did not differ in their ISC
values. Also, no significant increase of ISC values was found between the
experimental conditions for any of the node classification (Fig. 5C).

3.2.3. Uni-to-multimodal gradient

For the resting-state timescales both approaches at modelling this
gradient revealed a significant increase of intrinsic timescales with a
higher value of multimodality (Fig. 6B).

Also, in the analysis of ISC values the two approaches at modelling
multimodality produced largely similar results. The hypothesis test for
both models revealed significantly negative effects of multimodality on
the ISC values, in the Single, Triplet and Complete conditions, while the

effect in the Nonet condition was only significantly negative for the
model using the Ji atlas (Ji et al., 2019). So, an increase in multimodality
predicted a decrease in the ISC value. When comparing the effects be-
tween the conditions, both approaches identified an increase in the in-
fluence of multimodality on the ISC value between the Single and Triplet
conditions. Additionally, only for the SFC model the test also showed a
significantly larger effect of multimodality in the Nonet compared to the
Triplet condition (Fig. 6C).

3.2.4. Posterior/lateral-to-anterior/medial gradient

The resting-state timescales model

for the posterior/lateral-to-
anterior/medial gradient did not reveal an effect of the absolute x-co-
ordinate but displayed significantly longer timescales with an increase
in the y-coordinate as well as significant negative interaction between
the absolute x-coordinate and the y-coordinate (Fig. 7B).

Looking at the task data, the results depicted a significantly negative
effect of the absolute x-coordinate in all experimental conditions but the
Triplet condition. Also, the effect of the y-coordinate was significantly
negative in all conditions except for Triplet while the interaction effect
on the ISC values was only significantly negative in the Single and
Complete conditions. When comparing the effects between the experi-
mental conditions, we found a significant decrease of the effect of the
absolute x-coordinate on the ISC value between the Triplet and Nonet
conditions. Also, the interaction effect decreased significantly between
these two experimental conditions. The effect of the y-coordinate how-
ever increased between the Single and Triplet conditions (Fig. 7C).

10 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Fig. 4. Methods for extraction and results of intrinsic resting-state timescale and inter-subject correlation analyses for Rich Club architecture.
Note. (A) Rich Club (RC) identification was performed on individual binarized structural connectivity matrices with 219 cortical nodes according to the lausanne250
parcellation scheme (Cammoun et al., 2012). A combination of four different nodal cutoffs (top 15 % of degree distribution, start of RC regime, maximum of RC
regime, top 33 % in at least four of five hubscores/nodal measures of centrality) resulted in a set of candidate hub. The final RC hubs were determined by testing if
hub connections were more likely than expected at random in compliance with the RC definition (Colizza et al., 2006). (B) Density plots of the posterior distributions
of node classifications according to Rich Club architecture with mean point estimate, 50 % and 95 % highest probability density areas marked. (C) Plots are arranged
according to CONDITION. Density plots of the posterior distributions of node classifications according to Rich Club architecture with mean point estimate, 50 % and 95
% highest probability density areas marked. RC = Rich Club, BF = Bayes factor.

3.2.5. Graph theoretical measures of network centrality

In the resting-state model including all considered graph theoretical
measures of centrality we detected a significantly positive effect of
betweenness centrality as well as closeness centrality on the length of
the timescales (Fig. 8B).

For the task-data, none of the effects of any graph measure in any
experimental condition differed from zero. Comparing the conditions on
the other hand revealed a significant increase of the effect of degree
centrality on the ISC value between the Single and Triplet as well as an
increase of the effect of the participation coefficient between the Nonet
and Complete conditions (Fig. 8C).

3.2.6. Cortical thickness

Finally, modelling the effect of cortical thickness on the resting-state
timescales revealed a significant increase of intrinsic cortical timescales
with the average cortical thickness of an area (Fig. 9B).

Analyzing the ISC values, the two-sided hypothesis tests for the
model using cortical thickness as the explanatory variable unveiled
significant decreases of ISC values with the area’s average cortical
thickness in all conditions. In the comparison of the experimental con-
ditions however we could not identify any increase in the influence of
the cortical thickness on the ISC values between any of the tested con-
ditions (Fig. 9C).

3.3. Model comparison

Additionally to the hypothesis tests, we compared the estimated

11 

models to find the organizational schemes that best explain the distri-
bution of intrinsic timescales as well as ISC values across the cortex.

3.3.1. Resting-state timescales

Comparing the elpdloo (Vehtari et al., 2017) of the intrinsic cortical
timescale models identified that modelling the uni-to-multimodal
gradient using the overlap of each parcel with a multimodal area ac-
cording to the Ji atlas (Ji et al., 2019) as an estimation of multimodality
as the best fitting model (Table 1). Inspecting the differences in elpdloo
showed that this model performed significantly better than the null
model only containing the control variables as well as the models for the
RC and DC architectures, as the difference was larger than one standard
error (Mohor et al., 2021). All other models however did not perform
significantly worse than the Ji atlas model (Fig. 10A).

3.3.2.

Inter-subject correlation values from task-fMRI data

We also examined the elpdloo to compare the models of the ISC values
across the four experimental conditions. The results revealed that
modelling the uni-to-multimodal gradient using the Ji atlas (Ji et al.,
2019) approach most accurately predicted the distribution of ISC values
(Table 2). The elpdloo of this model was significantly larger compared
the
with
posterior/lateral-to-anterior/medial gradient modelled via the MNI
space coordinates which still fitted the data significantly better than the
other organizational schemes. The model using the cortical thickness as
an approximation for cytoarchitectural differences came in third and
than the models
fitted the ISC values also significantly better

second-best model was

other models.

The

all

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Fig. 5. Methods for extraction and results of intrinsic resting-state timescale and inter-subject correlation analyses for Diverse Club architecture.
Note. (A) Diverse Club (DC) identification was performed on individual binarized structural connectivity matrices with 219 cortical nodes according to the lau-
sanne250 parcellation scheme (Cammoun et al., 2012). Using the top 20 % of the participation coefficient distribution resulted in a set of candidate hubs. The final
DC hubs were determined by testing if hub connections were more likely than expected at random like in the Rich Club identification. (B) Density plots of the
posterior distributions of node classifications according to Diverse Club architecture with mean point estimate, 50 % and 95 % highest probability density areas
marked. (C) Plots are arranged according to CONDITION. Density plots of the posterior distributions of node classifications according to Diverse Club architecture with
mean point estimate, 50 % and 95 % highest probability density areas marked. DC = Diverse Club, BF = Bayes factor.

representing the RC and DC architectures, the model including the graph
theoretical measures of centrality as well as the null model. All other
models did not significantly differ from the null model that contained no
explanatory organizational scheme (Fig. 10B).

4. Discussion

Intrinsic timescales of the human brain may underly our capacity to
process the complex temporal structure of our environment (Golesorkhi
et al., 2021b; Wolff et al., 2022), but we do not know how they actually
arise. In this paper we examined six different cortical organizational
schemes and features of the cortical areas to investigate their role in
shaping the cortical timescales at rest as well as during a task presenting
stimuli of varying temporal persistence. The following discussion will
highlight the key findings while also discussing the individual organi-
zation schemes more in depth.

4.1. The uni-to-multimodal gradient best explains the cortical chronotopy

The aim of this paper was to find the organizational scheme that best
explains the chronotopy of the cortex. The Bayesian model comparison
of all considered organizational
identified the uni-to-
multimodal gradient modelled by the Ji atlas-based classification to be
the best fitting model for both the resting-state timescales and the dis-
tribution of ISC values in the task-based fMRI data. This corroborates
previous results finding the uni-to-multimodal gradient for the distri-
bution of timescales (Gao et al., 2020; Golesorkhi et al., 2021a; Ito et al.,
2020; Raut et al., 2020) as well as for TRWs (Farbood et al., 2015;

schemes

Hasson et al., 2004, 2008; Lerner et al., 2011). A gradient from the
primary sensory cortices to multimodal association cortices is a
well-established concept in neuroscience (Huntenburg et al., 2018;
Margulies et al., 2016; Mesulam, 1998; Sepulcre et al., 2012). Traversing
from unimodal over supramodal to multimodal cortices (Zamora-L´opez
et al., 2011), the gradient’s apex is assumed to be located within the
limbic system (Chanes and Feldman Barrett, 2016; Margulies et al.,
2016; Mesulam, 1998). In functional terms, the multimodal cortices are
considered particularly important for the integration of information and
for the retention and retrieval of past information (Murphy et al., 2019;
Wang, 2020). Moreover, the activity of areas higher on the gradient is
less
and
domain-general processes (Taylor et al., 2015; Yeo et al., 2015), while it
was proposed that these areas perform similar tasks among various
domains (Goldman-Rakic, 1988). Besides the cortical timescales (e.g.,
Raut et al., 2020), many other, especially microarchitectural features
like cortical thickness, neuron density (Burt et al., 2018; Wagstyl et al.,
2015) and myelinization (Demirtas¸ et al., 2019; Huntenburg et al., 2017;
Ito et al., 2020) as well as gene expression gradients (Burt et al., 2018;
Hansen et al., 2021; Shafiei et al., 2020) were found to follow an
uni-to-multimodal axis (for more information see Huntenburg et al.,
2018; Markello et al., 2022; Sydnor et al., 2021).

stimulus-determined

relates more

abstract

and

to

Despite the consistency and comprehensiveness of previous findings,
the question remains how exactly timescales are shaped along this
gradient. Previous modelling work was able to establish, that timescales
are driven by both local excitatory connections as well as by long-range
connections of an area (Chaudhuri et al., 2015; Schmidt et al., 2016; for
reviews see Cavanagh et al., 2020; Duarte et al., 2017). On the local

12 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Fig. 6. Methods for extraction and results of intrinsic resting-state timescale and inter-subject correlation analyses for uni-to-multimodal gradient.
Note. Two approaches at modelling the uni-to-multimodal gradient as a constant measure of multimodality: (A1) First, stepwise functional connectivity follows
network path through individual voxel-wise functional connectivity networks starting in seeds in the primary auditory, somatosensory and visual cortices. Paths
converge in multimodal areas after seven link-steps. Individual uni-to-multimodal gradients were estimated by subtracting the stepwise functional connectivity
values at first link-step from the values at the seventh link-step. Results were extracted using the lausanne250 parcellation scheme to model multimodality. (A2)
Second, we considered the Ji atlas (Ji et al., 2019) based classification assorting cortex into uni- and multimodal areas. The overlap of classification in the Ji atlas and
lausanne250 parcellation scheme was used as the second approach at modelling multimodality. (B) Fixed effect predictions of stepwise functional connectivity and Ji
atlas approaches to model uni-to-multimodal gradient with 95 % credibility interval marked. (C) Plots are arranged according to CONDITION. Fixed effect predictions of
stepwise functional connectivity and Ji atlas approaches to model uni-to-multimodal gradient with 95 % credibility interval marked. SFC = Stepwise functional
connectivity, BF = Bayes factor.

scale, the ratio of excitatory pyramidal interneurons was found to in-
crease with the cortical hierarchy (Torres-Gomez et al., 2020). These
interconnected excitatory pyramidal cells in granular level III were also
proposed to possess different ratios of neuronal receptors across the
cortex (Cavanagh et al., 2020; Wang, 2001). Thereby, especially the
density of glutaminergic NMDA receptors plays a crucial role for slower
and maintained cortical dynamics of these pyramidal cells (Wang,
2001). Interestingly, the distribution of NMDA receptors was suggested
to increase along the uni-to-multimodal gradient as well (Burt et al.,
2018; Wang et al., 2012). Based on these findings, Wang (2020)
concisely illustrated that the association cortices have more excitatory
inter-neuronal connections as well as more input controlling inhibitory
connections, while sensory cortices have more output-controlling con-
nections. Similar to Gollo et al.’s (2015) proposal for RC architecture,
this connectivity pattern enables the association cortices to produce
slower intrinsic timescales while also having the ability of integrate
information over longer periods of time. As these results clearly indicate
the importance of the dynamics on the neuronal level, investigating the
timescales on the microscale promises fruitful results to aid in the deeper
understanding of the biological and connective mechanisms behind the
temporal hierarchy of the cortex.

While we identified the Ji atlas approach as the best fitting model, we
also examined the SFC approach to the uni-to-multimodal gradient.
Using SFC, previous studies could show that paths starting from unim-
odal seed regions converge in multimodal areas after seven steps (Diez

and Sepulcre, 2018; Pretus et al., 2019; Sepulcre, 2014; Sepulcre et al.,
2012). To determine a gradient from the unimodal seeds to the multi-
modal cortices, we subtracted the initial SFC pattern at link-step one,
which determines the unimodal areas, from the pattern at link-steps
seven, which localizes the multimodal cortices. In contrast, the Ji atlas
describes the classification of twelve functional networks based on
neurobiological data, defining multimodality by these networks (Ji
et al., 2019). Despite these considerable differences in approaching the
concept of the uni-to-multimodal gradient, we were able to confirm the
resulting
validity of both these methods by comparing the
uni-to-multimodal gradients with previously discovered gradients (see
Supplemental Material 1; Margulies et al., 2016; Sydnor et al., 2021).
Moreover, we also find largely coherent results between the two ap-
proaches. Both models predicted an increase of the intrinsic resting-state
timescales with a higher multimodality and generally showed a decrease
of ISC values with an increase in multimodality across the experimental
conditions. Also, when exploring the relationship between the organi-
zational schemes using the spin test approach (Alexander-Bloch et al.,
2018) we found a significant correlation between the group average
patterns of the two multimodality approaches. Therefore, the question
remains as to why the SFC model did not perform as well as the Ji atlas
approach in the model comparison. Based on the presented results, we
speculate that there are still some methodological differences between
the two approaches that could explain remaining divergences between
the SFC approach we determined
the gradients. Firstly,

for

13 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Fig. 7. Methods for extraction and results of intrinsic resting-state timescale and inter-subject correlation analyses for posterior/lateral-to-anterior/medial gradient.
Note. (A) The lateral-to-medial and posterior-to-anterior gradients were modelled by using the averaged, individual x- and y-coordinates of each parcel, respectively.
Absolute x-coordinates were used to model a lateral-to-medial rather than a left-to-right trend. (B) Fixed effect predictions of |x|- and y-coordinates to model lateral-
to-medial and posterior-to-anterior gradients with 95 % credibility interval marked. (C) Plots are arranged according to CONDITION. Fixed effect predictions of |x|- and
y-coordinates to model lateral-to-medial and posterior-to-anterior gradients with 95 % credibility interval marked. BF = Bayes factor.

multimodality values for each individual subject while the Ji atlas-based
multimodality scores were the same for the entire group. The group-wise
approach might have the advantage that global patterns of cortical or-
ganization are better revealed in group average networks (Hagmann
et al., 2008). Secondly, the different spatial resolution of the two
modelling approaches can be critical. The SFC approach requires the
creation of downsampled voxel-wise connectivity matrices, which is a
significant but computationally necessary limitation (Pretus et al.,
2019). The Ji atlas on the other hand was originally based on state-of-the
art parcellation of the data (Glasser et al., 2016). Thirdly, the definition
of multimodality differs between the two approaches: Multimodal areas
in the SFC approach describe the final step in the functional hierarchy
(Sepulcre et al., 2012), while the Ji atlas-based classification defines all
but the purely sensory networks as multimodal (Golesorkhi et al., 2021a;
Ito et al., 2020). As the deployed task may not have been able to engage
the apex of the processing hierarchy (as discussed in more detail in
Section 4.3), the broader classification of multimodality in the Ji
atlas-based gradient might have been more fitting especially to the
distribution of ISC values.

On a different note, we only investigated two of many possible ways
to define the uni-to-multimodal gradient. In validating the two here
applied approaches we performed an additional analysis comparing the
group-average uni-to-multimodal maps from the described analysis with
two previously established gradients (see Supplemental Material S1).
For this we used the gradients from Margulies et al. (2016), that are
based on the decomposition of functional connectivity data into prin-
cipal gradients, and Sydnor et al. (2021), who integrated multiple
measures defining the gradient into one converging uni-to-multimodal
map. We found that both our approaches to the uni-to-multimodal

gradient significantly correlated with these two established gradients,
that were previously also related to the chronotopy of the cortex
(Fehring et al., 2024; Huntenburg et al., 2018). Therefore, the results not
only validate the chosen approaches but further highlight the impor-
tance of the uni-to-multimodal gradient as a cortical organizational
scheme. Beyond these four different approaches there is still a multitude
of other functional and structural features can be used to define the
uni-to-multimodal gradient (Sydnor et al., 2021). Thus, also the selec-
tion of six organizational schemes we investigated in this study only
makes up a fraction of possible organizations. Moreover, we used
Bayesian model comparison to find the best organizational scheme.
While Bayesian model comparison in general allows for the comparison
of non-nested models and thus is perfectly suited for comparing different
theories or competing organizational schemes like in this paper
(Geweke, 2007; Hollenbach and Montgomery, 2020; Rouder et al.,
2018), model comparison is not able to detect the “true” model for the
data. It is bound to the model space and will only identify the best fitting
among the evaluated models (Alston et al., 2004). There could be a
plethora of other organizational patterns and structures that could
explain cortical timescales at various spatial scales (Betzel and Bassett,
2017; Hansen et al., 2022; Keller et al., 2023; Markello et al., 2022;
Sydnor et al., 2021). Nevertheless, the consistency of our findings with
previous investigations gives us confidence in the assessment that the
uni-to-multimodal gradient best explains the chronotopy across the
cortex at rest and during task.

4.2. Resting-state timescales relate to all organizational schemes

Our second major finding concerns the resting-state timescales. We

14 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Fig. 8. Methods for extraction and results of intrinsic resting-state timescale and inter-subject correlation analyses for the graph theoretical measures of network
centrality.
Note. (A) Individual nodal measures of centrality were calculated for each of the 219 nodes. We considered degree centrality, closeness centrality, betweenness
centrality, participation coefficient and within-module degree z-score. (B) Fixed effect predictions of all investigated graph measures of centrality with 95 %
credibility interval marked. (C) Plots are arranged according to CONDITION. Fixed effect predictions of all investigated graph measures of centrality with 95 %
credibility interval marked. Degree c. = Degree centrality, Parti. coef. = Participation coefficient, BF = Bayes factor.

hypothesized for each organizational scheme that the resting-state
timescales as estimated by the decay of the ACF (Raut et al., 2020)
would increase, thus being slower, in hierarchically higher areas. Before
discussing the individual organizational schemes, we can summarize
that by and large we found this trend for all organizational schemes.

4.2.1. Rich Club architecture

Starting with the RC architecture, we discovered the resting-state
timescales increase from Local nodes to Feeder nodes and RC hubs,
while the timescales in Feeder nodes and RC hubs did not differ signif-
icantly. Thus, we could in large parts corroborate our hypothesis and
replicate previous findings (Gollo et al., 2015; Senden et al., 2017). The
non-significant differences between hubs and Feeder nodes could be
caused by the synchronization of neighbouring nodes by the RC. As
Gollo et al. (2015) described, the resonant network motifs that connect
RC hubs with their direct neighbours are perfectly suited to accommo-
date such synchronization. Thus, our findings can be seen as further
indication
synchronization
(Aguilar-Vel´azquez and Guzm´an-Vargas, 2019; Senden et al., 2014,
2017; Watanabe, 2013) .

previously

suggested

this

of

4.2.2. Diverse Club architecture

For the DC architecture, our findings resembled those for the RC
architecture and largely followed the predicted trends. DC hubs in
comparison to both Local and Feeder nodes had slower intrinsic time-
scales. Additionally, we could find a non-significant trend for slower
timescales in Feeder nodes compared with Local nodes. Thus, the results
rather depict a slow increase in timescales from one level of node clas-
synchronization between directly
sification to the next. The

15 

neighbouring nodes that was shown for the RC (Gollo et al., 2015) is not
as prevalent in DC nodes. This finding corresponds to previous studies
suggesting that the DC might be more involved in tasks rather than in
synchronization (Bertolero et al., 2017; Keller et al., 2023). Thus, our
resting-state results also slightly favor the RC architecture in explaining
the cortical timescales in absence of a task, hinting at the importance of
the RC for complex resting-state dynamics (Zamora-L´opez et al., 2016).

4.2.3. Rich or Diverse Club?

The reported similarities between DC and RC architectures are likely
caused by the similarity of the architectures in their classification of
nodes. As our spin χ²-test between the group-wise classifications indi-
cated, the two architectures are highly dependent (Lee, 2016). Thus,
naturally the question remains, what distinguishes RC and DC. In its
initial proposal the DC was directly compared with the RC, but, in
contrast to our results, no substantial overlap between DC and RC hubs
was reported (Bertolero et al., 2017). Beyond that, it was suggested that
the DC lays at a lower level in the cortical hierarchy than the RC (Keller
et al., 2023). However, we used a refined identification of the RC hubs
(Mecklenbrauck et al., 2024; Riedel et al., 2022) in this study that not
only adheres closer to the original definition of RC (Colizza et al., 2006)
but also uses multiple combined measures of the RC regime and cen-
trality as previously recommended (van den Heuvel and Sporns, 2013a).
This differed from the definition in Bertolero et al. (2017) that used a
nodal strength cutoff. The overlap between DC and RC thereby will
certainly also be influenced by the inclusion of the participation coef-
ficient as well as other centrality measures that focus more on efficiency
and communication (Hagmann et al., 2008; Jung et al., 2017) in our
definition of RC. Furthermore, we also adjusted the classification of the

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Fig. 9. Methods for extraction and results of intrinsic resting-state timescale and inter-subject correlation analyses for cortical thickness as an approximation of
cytoarchitectural differences.
Note. (A) Cortical thickness can be used as an approximation for cytoarchitectural differences (Wagstyl et al., 2015). It was calculated as the average distance between
the gray matter and white matter for each parcel (Goto et al., 2022). (B) Fixed effect prediction of cortical thickness as approximation of cytoarchitectural differences
with 95 % credibility interval marked. (C) Plots are arranged according to CONDITION. Fixed effect prediction of cortical thickness as approximation of cytoarchi-
tectural differences with 95 % credibility interval marked. BF = Bayes factor.

Table 1

Comparison of

Organizational scheme

̂
elpdloo of the models for the investigated organizational schemes in the intrinsic resting-state timescale analysis.
(

̂
elpdloo

se( ̂

elpdloo)

̂
elpddiff

)

̂
elpddiff

se

Uni-to-multimodal gradient

(Ji atlas)

Posterior/lateral-to-anterior/medial gradient
Uni-to-multimodal gradient

(SFC)

Graph measures of centrality
Cytoarchitecture

(Cortical thickness)
Rich Club architecture
Null model/No scheme
Diverse Club architecture

(cid:0) 11789.63

(cid:0) 11808.58
(cid:0) 11843.28

(cid:0) 11852.35
(cid:0) 11854.55

(cid:0) 11866.26
(cid:0) 11866.79
(cid:0) 11866.89

69.01

68.92
68.89

68.84
68.84

68.82
68.79
68.80

0.00

(cid:0) 18.95
(cid:0) 53.65

(cid:0) 62.71
(cid:0) 64.92

(cid:0) 76.63
(cid:0) 77.16
(cid:0) 77.26

0.00

10.77
13.93

13.16
10.99

12.33
12.38
12.36

Note. Models are considered to be better if the absolute elpdloo difference is larger than one standard error (Mohor et al., 2021).
expected log pointwise predictive density for a new dataset

̂
elpdloo =
calculated using Pareto smoothed importance sampling
̂
elpdloo of a model and the best performing model, se =

leave-one-out-cross-validation (PSIS-LOO-CV),
standard error of the variable, SFC = Stepwise functional connectivity.

̂
elpddiff = difference between the

DC hubs according to the original definition of clubness (Colizza et al.,
2006) but still based the identification of candidate hubs just on the
participation coefficient, as proposed by Bertolero et al. (2017). How-
ever, the exclusive usage of the participation coefficient to identify hubs
has recently been questioned as it could lead to misleading results if not
carefully controlled (Oldham and Fornito, 2023). Nevertheless, the
participation coefficient in general captures additional information
about the centrality of a node other measures do not contain (Oldham

et al., 2019). Recent results have even shown that RC and DC can capture
complementary properties of the network (Lohia et al., 2024; Xue et al.,
2020). Ultimately, more research and a revised and standardized defi-
nition of RC and especially DC are necessary to settle the debate between
the RC and DC architectures.

4.2.4. Uni-to-multimodal gradient

As discussed in detail in Section 4.1, we used two approaches that

16 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Fig. 10. Results of Bayesian model comparison.

̂
elpdloo = expected log pointwise
Note. (A) Model comparison for resting-state timescale analysis. (B) Model comparison for Inter-subject correlation analysis.
predictive density for new dataset using Pareto smoothed importance sampling leave-one-out-cross-validation criterion; Null = Null model (no organizational
scheme); RC = Rich Club architecture; DC = Diverse Club architecture; SFC = Uni-to-multimodal gradient (stepwise functional connectivity); Ji = Uni-to-multimodal
gradient (Ji atlas classification); PLAM = Posterior/lateral-to-anterior/medial gradient; GM = Graph measures of centrality; CT = Cytoarchitecture (cortical

thickness); * model has significantly higher

̂
elpdloo than models coded in respective color.

Table 2

Comparison of
in the inter-subject correlation analysis.

̂
elpdloo of the models for the investigated organizational schemes

Organizational scheme

̂
elpdloo

se( ̂

elpdloo) ̂

elpddiff

(

se

̂
elpddiff

)

Uni-to-multimodal gradient

(Ji atlas)

91045.48

124.18

0.00

0.00

Posterior/lateral-to-

90908.07

125.30

(cid:0) 137.41

28.04

anterior/medial gradient

Cytoarchitecture

(Cortical thickness)

90752.00

124.14

(cid:0) 293.48

25.85

Uni-to-multimodal gradient

90667.29

124.37

(cid:0) 378.19

30.19

(SFC)

Rich Club architecture
Null model/No scheme
Diverse Club architecture
Graph measures of

centrality

90626.95
90618.35
90617.87
90609.78

124.32
124.25
124.27
124.28

(cid:0) 418.53
(cid:0) 427.13
(cid:0) 427.61
(cid:0) 435.70

30.00
29.58
29.93
30.31

Note. Models are considered to be better if the absolute elpdloo difference is
̂
elpdloo = expected log
larger than one standard error (Mohor et al., 2021).
pointwise predictive density for a new dataset calculated using Pareto smoothed
̂
elpddiff =
̂
elpdloo of a model and the best performing model, se =

importance sampling leave-one-out-cross-validation (PSIS-LOO-CV),

difference between the
standard error of the variable, SFC = Stepwise functional connectivity.

address the multimodality as a continuous measure very differently. The
uni-to-multimodal gradient was firstly determined by the difference
between the SFC pattern at the seventh and the first link-step and sec-
ondly by the multimodality percentage based on the overlap between
the Ji atlas (Ji et al., 2019) and the applied lausanne250 parcellation
(Cammoun et al., 2012). Even though we used two different continuous
approaches in modelling multimodality we were able to replicate find-
ings that used dichotomous classification of uni- and multimodal
cortices (Golesorkhi et al., 2021a; Ito et al., 2020). Both modelling ap-
proaches produced the expected, similar results, predicting an increase
of the resting-state timescales with the multimodality of an area.

4.2.5. Posterior/lateral-to-anterior/medial gradient

We found an increase of the resting-state timescales from posterior to
anterior areas, mirroring the results observed for cortical peak fre-
quencies (Mahjoory et al., 2020). Against our prediction, we were not
able to find a general increase of timescales towards more medial

17 

regions. However, we did find the predicted significant interaction be-
tween the poster-to-anterior and lateral-to-medial trends, suggesting
that the lateral-to-medial trend is specifically focused to the frontal lobe.
Indeed, we included the posterior/lateral-to-anterior/medial gradient
because it is a part of many classic theories of cortical control which
mainly concern the frontal lobe (Badre and D’Esposito, 2009; Badre and
Nee, 2018; Fuster, 2001; Ingvar, 1985; Koechlin and Summerfield,
2007). Notably, in their proposal of an additional medial trend Alex-
ander and Brown (2018) also focused on the frontal lobe. Thus, it seems
plausible that we found an interaction effect identifying slower time-
scales not more medial in general but especially when moving towards
frontal areas of the brain. Based on these theoretical, but also structural
that
and functional findings,
medial-frontal areas are involved in higher levels of cognitive processing
(Alexander and Brown, 2018; Badre and Nee, 2018; Chanes and Feld-
man Barrett, 2016; Jobson et al., 2021).

considerable

evidence

there

is

4.2.6. Graph measures of centrality

Since previous studies reported the relationship between nodal
measures of centrality and the chronotopy (Fallon et al., 2020; Lurie
et al., 2024; Sethi et al., 2017) we also explored how the graph measures
we used as hub scores in the RC identification (also see Mecklenbrauck
et al., 2024; Riedel et al., 2022) faired in explaining the differences in
resting-state timescales. We found significantly slower resting-state
timescales with an increasing betweenness centrality and increasing
closeness centrality as well as a non-significant positive trend between
timescales and the participation coefficient of a node. Our results thus
extend upon previous findings which reported on relationships for de-
gree centrality (Fallon et al., 2020; Lurie et al., 2024; Sethi et al., 2017)
as well as the participation coefficient and within module degree z-score
(Lurie et al., 2024) but did not consider the betweenness and closeness
centralities. Modelling all five measures together, we could however not
replicate all these previous findings. One possible explanation for this is
the high correlation between the measures of centrality (Oldham et al.,
2019) we also showed in the spin test using the group average scores.
Since we combined all fives measures into a single model, overlap in the
proportions of explained variance could be a reason for replicating
previous results. However, we examined all models for issues with
multicollinearity and did not identify any violations (Wooldridge,
2013). Still, especially betweenness and closeness centrality describe
similar concepts as both indicate nodes that are important for short
paths in the network (Rubinov and Sporns, 2010) and characterize

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

important integrative hubs (Bassett et al., 2008; de Reus and van den
Heuvel, 2013; Hagmann et al., 2008; Harriger et al., 2012; Jung et al.,
2017; Sepulcre et al., 2010; Whitaker et al., 2016). Moreover, a recent
study showed that both betweenness and closeness centrality negatively
related to the complexity of the signal in task and at rest, which can be
interpreted as a less diverse activity in these nodes (Neudorf et al.,
2020), thus is comparable to the higher autocorrelation, i.e., slower
timescales we found for both centrality measures. Hence, our results
could also imply that highly integrative nodes display slower rhythms.
Beyond that, there are many more centrality measures (Oldham et al.,
2019) indicative of important nodes (i.e., Katz centrality; Fletcher and
Wennekers, 2018). Thus, based on our and other previous results, future
research might be inclined to explore more relationships between
timescales and different centrality measures, especially since it was
already shown for betweenness centrality that variation in centrality
measures can be used as a biomarker (Bassett et al., 2008).

4.2.7. Cortical thickness

Lastly, we also explored the relationship between cytoarchitecture
approximated by cortical thickness and the intrinsic timescales. Previ-
ous studies revealed that areas higher up the cortical hierarchy have a
less laminar pattern but a higher cortical thickness (Chanes and Feldman
Barrett, 2016; Saberi et al., 2023; Wagstyl et al., 2015). Accordingly, we
found that the resting-state timescales increased with a higher cortical
thickness, replicating previous findings (Gao et al., 2020). It should be
noted that the detected relation of the cortical thickness and the cortical
chronotopy strongly depends on the selected parcellation scheme of the
cortex, as the cytoarchitectural differences do not follow gyral and sulcal
boarders (Amunts et al., 2007). This is critical since the applied par-
cellation scheme, lausanne250, is based on the structural margins of the
Desikan-Killiany atlas (Cammoun et al., 2012; Desikan et al., 2006).
Thus, a future deeper investigation of the relation between cytoarchi-
tecture and the temporal scales of the cortex will require a parcellation
based on the cortical microstructure (e.g., Amunts et al., 2020).

4.2.8. Summary of resting-state timescale results

To summarize, we found evidence for the relationship of different
organizational schemes and structural features with the intrinsic cortical
timescales as estimated by the decay of the ACF (Raut et al., 2020). Since
we could corroborate nearly all our hypotheses for the resting-state
analysis and replicated many previous findings, the question remains
how distinct the investigated organizational schemes are. While we
explored the relationships amongst the organizational schemes using
spin tests (Alexander-Bloch et al., 2018) and found significant re-
lationships between the RC and DC architectures and expectedly be-
tween the two approaches to the uni-to-multimodal gradient and the
different centrality measures, previous studies revealed additional, sig-
nificant coherence between several of the here examined features. For
instance, a higher cortical thickness was previously related to multi-
modal cortices (Burt et al., 2018; Wagstyl et al., 2015) and RC hubs
(Scholtens et al., 2014; van den Heuvel et al., 2015). Just based on their
definitions, multimodal cortices and RC hubs describe largely over-
lapping concepts (van den Heuvel and Sporns, 2013b; Zamora-L´opez
et al., 2011) as both organizational patters are proposed to integrate
information across different functional networks (Chaudhuri et al.,
2015; van den Heuvel and Sporns, 2013b, 2013a; Yeo et al., 2015;
Zamora-L´opez et al., 2009, 2010). Therefore, it comes to no surprise that
the uni-to-multimodality gradient and the RC architecture are used
rather synonymously (e.g., Golesorkhi et al., 2021a; Ji et al., 2019;
Murphy et al., 2019). These two patterns thus could describe a func-
tional and a structural view on the same question. Possible remaining
differences between them could relate to the decoupling of functional
and structural features in higher cortical areas (Liu et al., 2023; Preti and
Van De Ville, 2019; V´azquez-Rodríguez et al., 2019). Furthermore, the
RC also is mainly found within midline areas (van den Heuvel and
Sporns, 2011) which could explain an overlap with the spatial

posterior/lateral-to-anterior/medial gradient, even though RC hubs are
usually found in both frontal and parietal areas (e.g., Mecklenbrauck
et al., 2024; Riedel et al., 2022).

To conclude, while we did not find a complete overlap between the
investigated organizational schemes, they are certainly not independent
of each other. Thus, a promising future avenue could focus on the
integration of multiple descriptions of cortical hierarchy into a single
gradient or classification index across imaging modalities and methods.
Recent studies provide positive preliminary evidence for this approach
(Hansen et al., 2022; Shafiei et al., 2023; Sydnor et al., 2021).

4.3. Task effects

We hypothesized that areas higher in the cortical hierarchy should
demonstrate larger ISC values in conditions that contain hierarchically
higher, temporally more persistent structures in the stimuli, as these
areas with longer TRWs should be engaged specifically by more
persistent stimuli (e.g., Hasson et al., 2004). We found that the ISC
values in all four experimental conditions (Single, Triplet, Nonet and
Complete) reduced with higher multimodality in the Ji atlas-based
model and in all but the Nonet condition in the SFC-based model.
Also, for thicker areas in the cortical thickness model the ISC values
decreased, which is further indication for the relationship between these
two organizational schemes (Burt et al., 2018; Wagstyl et al., 2015). This
decrease of ISC towards hierarchically higher areas can be explained by
the less stimulus-determined processes (Ren et al., 2017; Schm¨alzle
et al., 2017) and more diverse functions in these regions (Cui et al.,
2020). When comparing the effects between experimental conditions we
found the predicted increase in the effect of multimodality on the ISC
values between the Single and Triplet condition for both approaches of
the uni-to-multimodal gradient as well as between the Nonet and Triplet
conditions for just the SFC model. Similarly, the posterior-to-anterior
gradient was significantly more pronounced in the Triplet condition
compared to the Single condition. The lateral-to-medial gradient as well
as the interaction of the posterior-to-anterior and lateral-to-medial
gradients however were more pronounced in the Nonet as compared
to the Triplet condition. This could imply the additional engagement of
higher order areas in in medial and especially anterior-medial cortex,
thus providing evidence for the tuning of higher order areas being to
temporally more persistent structures in the stimulus (e.g., Aberbach--
Goodman and Mukamel, 2023; Farbood et al., 2015; Hasson et al., 2015;
Lerner et al., 2011). These results also match our previous findings of a
posterior-to-anterior trend for processing hierarchically higher levels of
the stimulus (Mecklenbrauck et al., 2024). Additionally, the Triplet
compared to the Single condition exhibited a larger effect of degree
centrality on the ISC values. Further, the effect of the participation co-
efficient was larger in the Complete compared to the Nonet condition.
These two findings might conform to previous findings showing that
highly connected nodes are essential for integrating stimuli (Fallon
et al., 2020) while especially diverse nodes that connect between
different modules of the network are more involved in integrative tasks
(Bertolero et al., 2017; Keller et al., 2023; Lurie et al., 2024). However,
looking at the credibility intervals of the effects across models revealed
that specifically the Triplet condition behaved distinctly from all the
other experimental conditions, even though the four conditions were
incrementally nested. This inconsistency demands caution with the
presented interpretations.

Beyond that, the applied paradigm might have restrained our ability
to identify consistent task results across the organizational schemes:
Firstly, the ISC values that were calculated based on task data using the
hierarchically nested but abstract digit sequences were much lower than
in paradigms using more complex, naturalistic stimuli (e.g., Schm¨alzle
et al., 2017). Controllable, abstract stimuli are the standard in neuro-
science (Rust and Movshon, 2005). However, the choice of control over
ecological validity might have limited a reliable and widespread acti-
vation in multimodal areas (Hasson et al., 2010; Sonkusare et al., 2019).

18 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Secondly, in deviation to other ISC studies (e.g., Lerner et al., 2011) we
included a task in our paradigm. Hierarchically nested sequences of
stimuli can be chunked into bigger units to make full use of working
memory capacity (Mathy and Feldman, 2012). Chunking however re-
quires attention to the stimulus to provoke a global activation of hier-
archically higher cortical areas (Dehaene et al., 2015; Mashour et al.,
2020). The addition of a visual task might have prevented the necessary
attention to the sequence, thus impeding the ignition of higher order
areas (Bekinschtein et al., 2009). Finding correlations across partici-
pants could then have been further restricted by the more diverse ac-
tivity in these higher order areas (Cui et al., 2020; Ren et al., 2017;
Schm¨alzle et al., 2017).

4.4. Limitations

In addition to the task paradigm, there are a few other limitations to
consider. As stated above, the relation between the chronotopy of the
cortex and its features is dependent of the applied parcellation scheme
(Amunts et al., 2007). Previous studies further found that the choice of
parcellation scheme has a large effect on the appearance of cortical
network as a whole (Bassett et al., 2011; Bryce et al., 2021; Cammoun
et al., 2012; Qi et al., 2015; Seguin et al., 2020; Sporns, 2011). As most of
the investigated organizational schemes were derived from structural
and functional networks, our choice for the Lausanne parcellation
scheme with 219 cortical parcels certainly had an impact on the results.
We specifically selected this parcellation scheme since it was the most
reliable (Cammoun et al., 2012) and neuroanatomically valid (Amunts
and Zilles, 2015) parcellation scheme of the ones available in the CATO
toolbox (de Lange et al., 2023) we applied for network reconstruction.
However, the Lausanne parcellation scheme is not without its limita-
tions. Firstly, as a sub-parcellation of the Desikan-Killiany atlas (Desikan
et al., 2006) it follows gyral and sulcal boundaries, which not all features
adhere to (Amunts et al., 2007). Secondly, the sub-parcellation was done
by dividing each original parcel in a set of equally sized smaller parcels
to achieve a voxel-level resolution. This procedure is rather arbitrary,
and its anatomical validity is questionable (Qi et al., 2015). There is a
multitude of possible parcellations of the human brain (Eickhoff et al.,
2018) making use of only anatomical (Desikan et al., 2006; Destrieux
et al., 2010; Tzourio-Mazoyer et al., 2002) or only functional guidelines
(Craddock et al., 2012; Gordon et al., 2016; Schaefer et al., 2018; Shen
et al., 2013) or also combining multiple sources of data (Fan et al., 2016;
Glasser et al., 2016). Finding the appropriate parcellation scheme might
be more dependent on the research question (Schaefer et al., 2018).
Faced with this arbitrariness, it can be a common approach to compare
the results across different parcellation schemes (e.g., Riedel et al.,
2022). We have not included this option in the scope of this paper, which
is a limitation. However, the consistency of our main finding that the
uni-to-multimodal gradient shapes the cortical chronotopy with previ-
ous studies using various other parcellation schemes (Gao et al., 2020;
Golesorkhi et al., 2021a; Ito et al., 2020; Raut et al., 2020) gives us
sufficient confidence in this result.

We also have to mention the data quality of the DWI data, that did
not follow current recommendations (Jones et al., 2013). Consequently,
we had to exclude subcortical areas from the analysis, even though the
cortical hierarchy was found to extend also to the subcortex (Alexander
et al., 1986; Badre and Nee, 2018; Siegle et al., 2021). Recent studies
even found a variation of timescales in subcortical areas that mirror that
of the cortex (Raut et al., 2020) and indicated that the thalamus plays a
crucial role in shaping functional dynamics (Harris et al., 2019; Müller
et al., 2020; Shine et al., 2019). However, despite using a combined DTI
and GQI algorithm that performed the best in distinguishing crossing
and kissing fibres (de Lange et al., 2023), the available data would have
limited the interpretability of results from the subcortex (Kai et al.,
2022). The limited data quality also led to our decision to binarize the
structural connectivity matrices since weighted connectivity measure
might be biased (Calamante, 2019; Fornito et al., 2016). Given an

improved data quality, future research could therefore make use of the
entire variability of weighted network measures (Fornito et al., 2016)
and also consider the previously found role of the subcortex in pro-
cessing hierarchically nested stimuli (Graybiel, 2008).

5. Conclusion

To conclude, we investigated the effect of six cortical organizational
schemes and features on the intrinsic resting-state timescales and the ISC
values from a task that presented participants with a hierarchically
nested stimulus sequence of increasing temporal persistency. In both
cases, the uni-to-multimodal gradient, as determined by an atlas clas-
sification, proved to be the best fitting model. In addition, we provide
further evidence for the relationship between the intrinsic timescales
and the functional hierarchy of the cortex, the network structure of the
human connectome as well as cytoarchitectural properties of an area,
corroborating previous results. Future studies investigating the brain’s
microstructural organization are needed to gain deeper insights into
how exactly the uni-to-multimodal gradient shapes the cortex’s chro-
notopy and how different organizational schemes interrelate.

Ethics statement

This study was conducted in accordance with the Declaration of
Helsinki and approved by the Local Ethics Committee of the University
of Münster. Participants
signed an informed consent before
participation.

Funding

The authors received no specific funding for this work.

CRediT authorship contribution statement

Falko Mecklenbrauck: Writing – review & editing, Writing – orig-
inal draft, Visualization, Software, Project administration, Methodology,
Investigation, Formal analysis, Data curation, Conceptualization. Jorge
Sepulcre: Software, Methodology. Jana Fehring: Writing – review &
editing, Software, Methodology. Ricarda I. Schubotz: Writing – review
& editing, Writing – original draft, Supervision, Resources, Project
administration, Methodology, Funding acquisition.

Declaration of competing interest

The authors declare that they have no conflict of interest.

Acknowledgement

The authors thank Monika Mertens and Lena M. Puder for their help
during data collection, Lena M. Puder, Simon Wieczorek, and Maria L.
Hofmann for help in the quality control process, Kristin Stroop and
Simon Wieczorek for help in testing the paradigm, and Sophie Siestrup
for helpful comments on the manuscript.

Supplementary materials

Supplementary material associated with this article can be found, in

the online version, at doi:10.1016/j.neuroimage.2024.120914.

Data availability

All code, one exemplary, minimally processed participant and data
sets to replicate the main analyses are available at https://github.com/
FalkMeck/Decoding_Cortical_Chronotopy.git

19 

F. Mecklenbrauck et al.

References

Aberbach-Goodman, S., Mukamel, R., 2023. Temporal hierarchy of observed goal-
directed actions. Sci. Rep. 13 (1), 1–13. https://doi.org/10.1038/s41598-023-
46917-z.

Agcaoglu, O., Wilson, T.W., Wang, Y.P., Stephen, J., Calhoun, V.D., 2019. Resting state
connectivity differences in eyes open versus eyes closed conditions. Hum. Brain
Mapp. 40 (8), 2488–2498. https://doi.org/10.1002/hbm.24539.

Aguilar-Vel´azquez, D., Guzm´an-Vargas, L., 2019. Critical synchronization and 1/f noise
in inhibitory/excitatory rich-club neural networks. Sci. Rep. 9 (1), 1–13. https://doi.
org/10.1038/s41598-018-37920-w.

Aguirre, G.K., Mattar, M.G., Magis-Weinberg, L., 2011. De Bruijn cycles for neural

decoding. Neuroimage 56 (3), 1293–1300. https://doi.org/10.1016/j.
neuroimage.2011.02.005.

Alexander, G.E., DeLong, M.R., Strick, P.L., 1986. Parallel organization of functionally
segregated circuits linking basal ganglia and cortex. Annu. Rev. Neurosci. 9,
357–381. https://doi.org/10.1146/annurev.ne.09.030186.002041.

Alexander, W.H., Brown, J.W., 2018. Frontal cortex function as derived from hierarchical
predictive coding. Sci. Rep. 8 (1), 1–11. https://doi.org/10.1038/s41598-018-
21407-9.

Alexander-Bloch, A.F., Shou, H., Liu, S., Satterthwaite, T.D., Glahn, D.C., Shinohara, R.T.,
Vandekar, S.N., Raznahan, A., 2018. On testing for spatial correspondence between
maps of human brain structure and function. Neuroimage 178 (February), 540–551.
https://doi.org/10.1016/j.neuroimage.2018.05.070.

Alston, C., Kuhnert, P., Low Choy, S., Mcvinish, R., Mengersen, K., Choy, S.L.,

Mcvinish, R., Mengersen, K., 2004. Bayesian model comparison: review and
discussion. In: ISI 2005: the 55th Session of the International Statistical Institute,
Sydney, 2005, pp. 1–4. http://iase-web.org/documents/papers/isi55/Alston-Kuh
nert-Low_Choy-McVinish-Mengersen.pdf.

Amunts, K., Mohlberg, H., Bludau, S., Zilles, K., 2020. Julich-brain: a 3D probabilistic
atlas of the human brain’s cytoarchitecture. Science 369 (6506), 988–992. https://
doi.org/10.1126/science.abb4588.

Amunts, K., Schleicher, A., Zilles, K., 2007. Cytoarchitecture of the cerebral cortex-more
than localization. Neuroimage 37 (4), 1061–1065. https://doi.org/10.1016/j.
neuroimage.2007.02.037.

Amunts, K., Zilles, K., 2015. Architectonic mapping of the human brain beyond

brodmann. Neuron 88 (6), 1086–1107. https://doi.org/10.1016/j.
neuron.2015.12.001.

Andersson, J.L.R., Skare, S., Ashburner, J., 2003. How to correct susceptibility

distortions in spin-echo echo-planar images: application to diffusion tensor imaging.
Neuroimage 20 (2), 870–888. https://doi.org/10.1016/S1053-8119(03)00336-7.
Andersson, J.L.R., Sotiropoulos, S.N., 2016. An integrated approach to correction for off-
resonance effects and subject movement in diffusion MR imaging. Neuroimage 125,
1063–1078. https://doi.org/10.1016/j.neuroimage.2015.10.019.

Badre, D., D’Esposito, M., 2009. Is the rostro-caudal axis of the frontal lobe hierarchical?

Nat. Rev. Neurosci. 10 (9), 659–669. https://doi.org/10.1038/nrn2667.

Badre, D., Nee, D.E., 2018. Frontal cortex and the hierarchical control of behavior.
Trends Cogn. Sci. 22 (2), 170–188. https://doi.org/10.1016/j.tics.2017.11.005.
Elsevier Ltd.

Baldassano, C., Chen, J., Zadbood, A., Pillow, J.W., Hasson, U., Norman, K.A., 2017.

Discovering event structure in continuous narrative perception and memory. Neuron
95 (3), 709–721.e5. https://doi.org/10.1016/j.neuron.2017.06.041.

Bassett, D.S., Brown, J.A., Deshpande, V., Carlson, J.M., Grafton, S.T., 2011. Conserved
and variable architecture of human white matter connectivity. Neuroimage 54 (2),
1262–1279. https://doi.org/10.1016/j.neuroimage.2010.09.006.

Bassett, D.S., Bullmore, E., Verchinski, B.A., Mattay, V.S., Weinberger, D.R., Meyer-
Lindenberg, A., 2008. Hierarchical organization of human cortical networks in
health and schizophrenia. J. Neurosci. 28 (37), 9239–9248. https://doi.org/
10.1523/JNEUROSCI.1929-08.2008.

Behzadi, Y., Restom, K., Liau, J., Liu, T.T., 2007. A component based noise correction

method (CompCor) for BOLD and perfusion based fMRI. Neuroimage 37 (1), 90–101.
https://doi.org/10.1016/j.neuroimage.2007.04.042.

Bekinschtein, T.A., Dehaene, S., Rohaut, B., Tadel, F., Cohen, L., Naccache, L., 2009.
Neural signature of the conscious processing of auditory regularities. Proc. Natl.
Acad. Sci. USA 106 (5), 1672–1677. https://doi.org/10.1073/pnas.0809667106.
Benjamini, Y., Hochberg, Y., 1995. Controlling the false discovery rate : a practical and
powerful approach to multiple testing. J. R. Stat. Soc. Ser. B (Methodological) 57 (1),
289–300.

Bertolero, M.A., Yeo, B.T.T., D’Esposito, M., 2017. The diverse club. Nat. Commun. 8 (1),

1–10. https://doi.org/10.1038/s41467-017-01189-w.

Betzel, R.F., Bassett, D.S., 2017. Multi-scale brain networks. Neuroimage 160 (November

2016), 73–83. https://doi.org/10.1016/j.neuroimage.2016.11.006.

Blondel, V.D., Guillaume, J.L., Lambiotte, R., Lefebvre, E., 2008. Fast unfolding of

communities in large networks. J. Stat. Mech. 2008 (10), 1–12. https://doi.org/
10.1088/1742-5468/2008/10/P10008.

Bond, C.F., Richardson, K., 2004. Seeing the Fisher Z-transformation. Psychometrika 69

(2), 291–303. https://doi.org/10.1007/BF02295945.

Brimijoin, W.O., O’Neill, W.E., 2010. Patterned tone sequences reveal non-linear

interactions in auditory spectrotemporal receptive fields in the inferior colliculus.
Hear. Res. 267 (1–2), 96–110. https://doi.org/10.1016/j.heares.2010.04.005.
Brown, J.A., Terashima, K.H., Burggren, A.C., Ercoli, L.M., Miller, K.J., Small, G.W.,

Bookheimer, S.Y., 2011. Brain network local interconnectivity loss in aging APOE-4
allele carriers. Proc. Natl. Acad. Sci. USA 108 (51), 20760–20765. https://doi.org/
10.1073/pnas.1109038108.

Bryce, N.V., Flournoy, J.C., Guassi Moreira, J.F., Rosen, M.L., Sambook, K.A., Mair, P.,
McLaughlin, K.A., 2021. Brain parcellation selection: an overlooked decision point

NeuroImage 303 (2024) 120914 

with meaningful effects on individual differences in resting-state functional
connectivity. Neuroimage 243 (March), 118487. https://doi.org/10.1016/j.
neuroimage.2021.118487.

Brysbaert, M., 1995. Arabic number reading: on the nature of the numerical scale and the
origin of phonological recoding. J. Exp. Psychol. 124 (4), 434–452. https://doi.org/
10.1037/0096-3445.124.4.434.

Bueichekú, E., Azn´arez-Sanado, M., Diez, I., Uquillas, F.d.O., Ortiz-Ter´an, L., Qureshi, A.
Y., Su˜nol, M., Basaia, S., Ortiz-Ter´an, E., Pastor, M.A., Sepulcre, J., 2020. Central
neurogenetic signatures of the visuomotor integration system. Proc. Natl. Acad. Sci.
USA 117 (12), 6836–6843. https://doi.org/10.1073/pnas.1912429117.

Bürkner, P.C., 2017. brms: An R package for Bayesian multilevel models using Stan.

J. Stat. Softw. 80 (1). https://doi.org/10.18637/jss.v080.i01.

Bürkner, P.C. (2018). Is the evidence ratio for a one sided hypothesis equivalent to a one sided

bayes factor? https://github.com/paul-buerkner/brms/issues/311.
Burt, J.B., Demirtas¸, M., Eckner, W.J., Navejar, N.M., Ji, J.L., Martin, W.J.,

Bernacchia, A., Anticevic, A., Murray, J.D., 2018. Hierarchy of transcriptomic
specialization across human cortex captured by structural neuroimaging topography.
Nat. Neurosci. 21 (9), 1251–1259. https://doi.org/10.1038/s41593-018-0195-0.
Buxton, R.B., 2009. Introduction to Functional Magnetic Resonance Imaging. Cambridge

University Press. https://doi.org/10.1017/CBO9780511605505.

Caballero-Gaudes, C., Reynolds, R.C., 2017. Methods for cleaning the BOLD fMRI signal.

Neuroimage 154 (December 2016), 128–149. https://doi.org/10.1016/j.
neuroimage.2016.12.018.

Calamante, F., 2019. The seven deadly sins of measuring brain structural connectivity
using diffusion MRI streamlines fibre-tracking. Diagnostics 9 (3). https://doi.org/
10.3390/diagnostics9030115.

Cammoun, L., Gigandet, X., Meskaldji, D., Thiran, J.P., Sporns, O., Do, K.Q., Maeder, P.,
Meuli, R., Hagmann, P., 2012. Mapping the human connectome at multiple scales
with diffusion spectrum MRI. J. Neurosci. Methods 203 (2), 386–397. https://doi.
org/10.1016/j.jneumeth.2011.09.031.

Cavanagh, S.E., Hunt, L.T., Kennerley, S.W., 2020. A diversity of intrinsic timescales

underlie neural computations. Front. Neural Circuits 14 (December), 1–18. https://
doi.org/10.3389/fncir.2020.615626.

Chanes, L., Feldman Barrett, L., 2016. Redefining the role of limbic areas in cortical

processing. Trends Cogn. Sci. 20 (2), 96–106. https://doi.org/10.1016/j.
tics.2015.11.005.

Chang, L.-C., Jones, D.K., Pierpaoli, C., 2005. RESTORE: robust estimation of tensors by
outlier rejection. Magn. Reson. Med. 53 (5), 1088–1095. https://doi.org/10.1002/
mrm.20426.

Chang, L.-C., Walker, L., Pierpaoli, C., 2012. Informed RESTORE: a method for robust
estimation of diffusion tensor from low redundancy datasets in the presence of
physiological noise artifacts. Magn. Reson. Med. 68 (5), 1654–1663. https://doi.org/
10.1002/mrm.24173.

Chaudhuri, R., Knoblauch, K., Gariel, M.A., Kennedy, H., Wang, X.J., 2015. A large-scale
circuit mechanism for hierarchical dynamical processing in the primate cortex.
Neuron 88 (2), 419–431. https://doi.org/10.1016/j.neuron.2015.09.008.

Chen, J., Hasson, U., Honey, C.J., 2015. Processing timescales as an organizing principle

for primate cortex. Neuron 88 (2), 244–246. https://doi.org/10.1016/j.
neuron.2015.10.010.

Ciric, R., Wolf, D.H., Power, J.D., Roalf, D.R., Baum, G.L., Ruparel, K., Shinohara, R.T.,
Elliott, M.A., Eickhoff, S.B., Davatzikos, C., Gur, R.C., Gur, R.E., Bassett, D.S.,
Satterthwaite, T.D., 2017. Benchmarking of participant-level confound regression
strategies for the control of motion artifact in studies of functional connectivity.
Neuroimage 154 (March), 174–187. https://doi.org/10.1016/j.
neuroimage.2017.03.020.

Colizza, V., Flammini, A., Serrano, M.A., Vespignani, A., 2006. Detecting rich-club

ordering in complex networks. Nat. Phys. 2 (2), 110–115. https://doi.org/10.1038/
nphys209.

Corbin, N., Todd, N., Friston, K.J., Callaghan, M.F., 2018. Accurate modeling of temporal
correlations in rapidly sampled fMRI time series. Hum. Brain Mapp. 39 (10),
3884–3897. https://doi.org/10.1002/hbm.24218.

Craddock, R.C., James, G.A., Holtzheimer, P.E., Hu, X.P., Mayberg, H.S., 2012. A whole
brain fMRI atlas generated via spatially constrained spectral clustering. Hum. Brain
Mapp. 33 (8), 1914–1928. https://doi.org/10.1002/hbm.21333.

Cui, Z., Li, H., Xia, C.H., Larsen, B., Adebimpe, A., Baum, G.L., Cieslak, M., Gur, R.E.,

Gur, R.C., Moore, T.M., Oathes, D.J., Alexander-Bloch, A.F., Raznahan, A., Roalf, D.
R., Shinohara, R.T., Wolf, D.H., Davatzikos, C., Bassett, D.S., Fair, D.A.,
Satterthwaite, T.D., 2020. Individual variation in functional topography of
association networks in youth. Neuron 106 (2), 340–353.e8. https://doi.org/
10.1016/j.neuron.2020.01.029.

Cullen, A.C., Frey, H.C., 1999. Probabilistic Techniques in Exposure Assessment: A
Handbook for Dealing with Variability and Uncertainty in Models and Inputs.
Springer Science & Business.

Dale, A.M., Fischl, B., Sereno, M.I., 1999. Cortical surface-based analysis. Neuroimage 9

(2), 179–194. https://doi.org/10.1006/nimg.1998.0395.

de Bruijn, G.N., 1946. A combinatorial problem. Proc. Koninklijke Nederlandse Acad.
van Wetenschappen 49, 758–764. http://ci.nii.ac.jp/naid/10019660672/en/.
de Lange, S.C., Helwegen, K., van den Heuvel, M.P., 2023. Structural and functional
connectivity reconstruction with CATO—A connectivity analysis TOolbox.
Neuroimage 273 (April), 120108. https://doi.org/10.1016/j.
neuroimage.2023.120108.

de Reus, M.A., van den Heuvel, M.P., 2013. Rich club organization and intermodule

communication in the cat connectome. J. Neurosci. 33 (32), 12929–12939. https://
doi.org/10.1523/jneurosci.1448-13.2013.

Dehaene, S., 2001. Pr´ecis of the number sense. Mind Lang. 16 (1), 16–36. https://doi.

org/10.1111/1468-0017.00154.

20 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Dehaene, S., Meyniel, F., Wacongne, C., Wang, L., Pallier, C., 2015. The neural

Gordon, E.M., Laumann, T.O., Adeyemo, B., Huckins, J.F., Kelley, W.M., Petersen, S.E.,

representation of sequences: from transition probabilities to algebraic patterns and
linguistic trees. Neuron 88 (1), 2–19. https://doi.org/10.1016/j.
neuron.2015.09.019.

Demirtas¸, M., Burt, J.B., Helmer, M., Ji, J.L., Adkinson, B.D., Glasser, M.F., Van Essen, D.
C., Sotiropoulos, S.N., Anticevic, A., Murray, J.D., 2019. Hierarchical heterogeneity
across human cortex shapes large-scale neural dynamics. Neuron 101 (6),
1181–1194.e13. https://doi.org/10.1016/j.neuron.2019.01.017.

Desikan, R.S., S´egonne, F., Fischl, B., Quinn, B.T., Dickerson, B.C., Blacker, D.,

Buckner, R.L., Dale, A.M., Maguire, R.P., Hyman, B.T., Albert, M.S., Killiany, R.J.,
2006. An automated labeling system for subdividing the human cerebral cortex on
MRI scans into gyral based regions of interest. Neuroimage 31 (3), 968–980. https://
doi.org/10.1016/j.neuroimage.2006.01.021.

Destrieux, C., Fischl, B., Dale, A., Halgren, E., 2010. Automatic parcellation of human

cortical gyri and sulci using standard anatomical nomenclature. Neuroimage 53 (1),
1–15. https://doi.org/10.1016/j.neuroimage.2010.06.010.

Diez, I., Sepulcre, J., 2018. Neurogenetic profiles delineate large-scale connectivity

dynamics of the human brain. Nat. Commun. 9 (1), 1–10. https://doi.org/10.1038/
s41467-018-06346-3.

Duarte, R., Seeholzer, A., Zilles, K., Morrison, A., 2017. Synaptic patterning and the

timescales of cortical dynamics. Curr. Opin. Neurobiol. 43 (April), 156–165. https://
doi.org/10.1016/j.conb.2017.02.007.

Eickhoff, S.B., Stephan, K.E., Mohlberg, H., Grefkes, C., Fink, G.R., Amunts, K., Zilles, K.,
2005. A new SPM toolbox for combining probabilistic cytoarchitectonic maps and
functional imaging data. Neuroimage 25 (4), 1325–1335. https://doi.org/10.1016/j.
neuroimage.2004.12.034.

Eickhoff, S.B., Yeo, B.T.T., Genon, S., 2018. Imaging-based parcellations of the human
brain. Nat. Rev. Neurosci. 19 (11), 672–686. https://doi.org/10.1002/jmri.27188.

Fallon, J., Ward, P.G.D., Parkes, L., Oldham, S., Arnatkeviˇci¯ut ˙e, A., Fornito, A.,

Fulcher, B.D., 2020. Timescales of spontaneous fMRI fluctuations relate to structural
connectivity in the brain. Netw. Neurosci. 4 (3), 788–806. https://doi.org/10.1162/
netn_a_00151.

Fan, L., Li, H., Zhuo, J., Zhang, Y., Wang, J., Chen, L., Yang, Z., Chu, C., Xie, S., Laird, A.
R., Fox, P.T., Eickhoff, S.B., Yu, C., Jiang, T., 2016. The human brainnetome atlas: a
new brain atlas based on connectional architecture. Cereb. Cortex 26 (8),
3508–3526. https://doi.org/10.1093/cercor/bhw157.

Farbood, M.M., Heeger, D.J., Marcus, G., Hasson, U., Lerner, Y., 2015. The neural

processing of hierarchical structure in music and speech at different timescales.
Front. Neurosci. 9 (APR), 1–13. https://doi.org/10.3389/fnins.2015.00157.

Fehring, J., Balestrieri, E., Focke, N.K., Dannlowski, U., Stier, C., Gross, J., 2024.

Neurophysiological correlates of cortical hierarchy across the lifespan. BioRxiv
Neurosci. 1–28. https://www.biorxiv.org/content/10.1101/2024.07.15.602693v1?
rss=1&utm_source=researcher_app&utm_medium=referral&utm_campaign
=RESR_MRKT_Researcher_inbound.

FIL Methods Group. (2017). SPM12 Manual. 15(3), 1–508. https://www.fil.ion.ucl.ac.

uk/spm/doc/manual.pdf%0Ahttp://www.fil.ion.ucl.ac.uk/spm/.

Fischl, B., 2012. FreeSurfer. Neuroimage 62 (2), 774–781. https://doi.org/10.1016/j.

neuroimage.2012.01.021.

Fletcher, J.M.K., Wennekers, T., 2018. From structure to activity: using centrality

measures to predict neuronal activity. Int. J. Neural Syst. 28 (2). https://doi.org/
10.1142/S0129065717500137.

Fornito, A., Zalesky, A., Bullmore, E., 2016. Fundamentals of Brain Network Analysis.

Elsevier. https://doi.org/10.1016/C2012-0-06036-X.

Fuster, J.M., 2001. The prefrontal cortex—An update: time is of the essence. Neuron 30

(2), 319–333. https://doi.org/10.1016/S0896-6273(01)00285-9.

Gao, R., van den Brink, R.L., Pfeffer, T., Voytek, B., 2020. Neuronal timescales are
functionally dynamic and shaped by cortical microarchitecture. Elife 9, 1–26.
https://doi.org/10.7554/eLife.61277.

Gelman, A., Hwang, J., Vehtari, A., 2014. Understanding predictive information criteria
for Bayesian models. Stat. Comput. 24 (6), 997–1016. https://doi.org/10.1007/
s11222-013-9416-2.

2016. Generation and evaluation of a cortical area parcellation from resting-state
correlations. Cereb. Cortex 26 (1), 288–303. https://doi.org/10.1093/cercor/
bhu239.

Gorgolewski, K.J. (2016). MPM 1.0 asymetrical (improved reconstruction). https://identifie

rs.org/neurovault.image:29489.

Goto, M., Abe, O., Hagiwara, A., Fujita, S., Kamagata, K., Hori, M., Aoki, S., Osada, T.,
Konishi, S., Masutani, Y., Sakamoto, H., Sakano, Y., Kyogoku, S., Daida, H., 2022.
Advantages of using both voxel-and surface-based morphometry in cortical
morphology analysis: a review of various applications. Magn. Reson. Med. Sci. 21
(1), 41–57. https://doi.org/10.2463/mrms.rev.2021-0096.

Graybiel, A.M., 2008. Habits, rituals, and the evaluative brain. Annu Rev. Neurosci. 31,

359–387. https://doi.org/10.1146/annurev.neuro.29.051605.112851.

Guimer`a, R., Nunes Amaral, L.A., 2005. Functional cartography of complex metabolic
networks. Nature 433 (7028), 895–900. https://doi.org/10.1038/nature03288.
Hagmann, P., Cammoun, L., Gigandet, X., Meuli, R., Honey, C.J., Van Wedeen, J.,

Sporns, O., 2008. Mapping the structural core of human cerebral cortex. PLoS Biol. 6
(7), 1479–1493. https://doi.org/10.1371/journal.pbio.0060159.

Hansen, J.Y., Markello, R.D., Vogel, J.W., Seidlitz, J., Bzdok, D., Misic, B., 2021.

Mapping gene transcription and neurocognition across human neocortex. Nat. Hum.
Behav. 5 (9), 1240–1250. https://doi.org/10.1038/s41562-021-01082-z.

Hansen, J.Y., Shafiei, G., Voigt, K., Liang, E.X., Cox, S.M.L., Leyton, M., Jamadar, S.D., &
Misic, B. (2022). Multimodal, multiscale connectivity blueprints of the cerebral
cortex. bioRxiv, 2022.12.02.518906. https://www.biorxiv.org/content/10.1101/20
22.12.02.518906v1%0Ahttps://www.biorxiv.org/content/10.1101/2022.12.02.51
8906v1.abstract.

Harriger, L., van den Heuvel, M.P., Sporns, O., 2012. Rich club organization of macaque
cerebral cortex and its role in network communication. PLoS One 7 (9). https://doi.
org/10.1371/journal.pone.0046497.

Harris, J.A., Mihalas, S., Hirokawa, K.E., Whitesell, J.D., Choi, H., Bernard, A., Bohn, P.,

Caldejon, S., Casal, L., Cho, A., Feiner, A., Feng, D., Gaudreault, N., Gerfen, C.R.,
Graddis, N., Groblewski, P.A., Henry, A.M., Ho, A., Howard, R., Zeng, H., 2019.
Hierarchical organization of cortical and thalamic connectivity. Nature 575 (7781),
195–202. https://doi.org/10.1038/s41586-019-1716-z.

Hasson, U., Chen, J., Honey, C.J., 2015. Hierarchical process memory: memory as an
integral component of information processing. Trends Cogn. Sci. 19 (6), 304–313.
https://doi.org/10.1016/j.tics.2015.04.006.

Hasson, U., Malach, R., Heeger, D.J., 2010. Reliability of cortical activity during natural

stimulation. Trends Cogn. Sci. 14 (1), 40–48. https://doi.org/10.1016/j.
tics.2009.10.011.

Hasson, U., Nir, Y., Levy, I., Fuhrmann, G., Malach, R., 2004. Intersubject

synchronization of cortical activity during natural vision. Science 303 (5664),
1634–1640. https://doi.org/10.1126/science.1089506.

Hasson, U., Yang, E., Vallines, I., Heeger, D.J., Rubin, N., 2008. A hierarchy of temporal
receptive windows in human cortex. J. Neurosci. 28 (10), 2539–2550. https://doi.
org/10.1523/JNEUROSCI.5487-07.2008.

Hawrylycz, M.J., Lein, E.S., Guillozet-Bongaarts, A.L., Shen, E.H., Ng, L., Miller, J.A., van
de Lagemaat, L.N., Smith, K.A., Ebbert, A., Riley, Z.L., Abajian, C., Beckmann, C.F.,
Bernard, A., Bertagnolli, D., Boe, A.F., Cartagena, P.M., Chakravarty, M.M.,
Chapin, M., Chong, J., Jones, A.R., 2012. An anatomically comprehensive atlas of
the adult human brain transcriptome. Nature 489 (7416), 391–399. https://doi.org/
10.1038/nature11405.

Hollenbach, F.M., Montgomery, J.M., 2020. Bayesian Model Selection, Model

Comparison, and Model Averaging. The SAGE Handbook of Research Methods in
Political Science and International Relations, pp. 937–960. https://doi.org/10.4135/
9781526486387.n52.

Honey, C.J., Thesen, T., Donner, T.H., Silbert, L.J., Carlson, C.E., Devinsky, O., Doyle, W.
K., Rubin, N., Heeger, D.J., Hasson, U., 2012. Slow cortical dynamics and the
accumulation of information over long timescales. Neuron 76 (2), 423–434. https://
doi.org/10.1016/j.neuron.2012.08.011.

Horn, A. (2016). HCP-MMP1.0 projected on MNI2009a GM (volumetric) in NIfTI format.

Geweke, J., 2007. Bayesian model comparison and validation. Am. Econ. Rev. 97 (2),

https://doi.org/10.6084/m9.figshare.3501911.v5.

60–64. https://doi.org/10.1257/aer.97.2.60.

Glasser, M.F., Coalson, T.S., Robinson, E.C., Hacker, C.D., Harwell, J., Yacoub, E.,

Ugurbil, K., Andersson, J., Beckmann, C.F., Jenkinson, M., Smith, S.M., Van Essen, D.
C., 2016. A multi-modal parcellation of human cerebral cortex. Nature 536 (7615),
171–178. https://doi.org/10.1038/nature18933.

Goldman-Rakic, P.S., 1988. Topography of cognition: parallel distributed networks in
primate association cortex. Annu Rev. Neurosci. 11, 137–156. https://doi.org/
10.1146/annurev.ne.11.030188.001033.

Golesorkhi, M., Gomez-Pilar, J., Tumati, S., Fraser, M., Northoff, G., 2021a. Temporal
hierarchy of intrinsic neural timescales converges with spatial core-periphery
organization. Commun. Biol. 4 (1), 1–14. https://doi.org/10.1038/s42003-021-
01785-z.

Golesorkhi, M., Gomez-Pilar, J., Zilio, F., Berberian, N., Wolff, A., Yagoub, M.C.E.,

Northoff, G., 2021b. The brain and its time: intrinsic neural timescales are key for
input processing. Commun. Biol. 4 (1), 1–16. https://doi.org/10.1038/s42003-021-
02483-6.

Gollo, L.L., Zalesky, A., Matthew Hutchison, R., van den Heuvel, M.P., Breakspear, M.,
2015. Dwelling quietly in the rich club: brain network determinants of slow cortical
fluctuations. Philos. Trans. R. Soc. B 370 (1668). https://doi.org/10.1098/
rstb.2014.0165.

G´omez-Garde˜nes, J., Zamora-L´opez, G., Moreno, Y., Arenas, A., 2010. From modular to
centralized organization of synchronization in functional areas of the cat cerebral
cortex. PLoS One 5 (8). https://doi.org/10.1371/journal.pone.0012313.

Huntenburg, J.M., Bazin, P.L., Goulas, A., Tardif, C.L., Villringer, A., Margulies, D.S.,
2017. A systematic relationship between functional connectivity and intracortical
myelin in the human cerebral cortex. Cereb. Cortex (New York, NY: 1991) 27 (2),
981–997. https://doi.org/10.1093/cercor/bhx030.

Huntenburg, J.M., Bazin, P.L., Margulies, D.S., 2018. Large-scale gradients in human

cortical organization. Trends. Cogn. Sci. 22 (1), 21–31. https://doi.org/10.1016/j.
tics.2017.11.002.

Ingvar, D.H., 1985. ``Memory of the future”: an essay on the temporal organization of

conscious awareness. Hum. Neurobiol. 4 (3), 127–136.

Ito, T., Hearne, L.J., Cole, M.W., 2020. A cortical hierarchy of localized and distributed
processes revealed via dissociation of task activations, connectivity changes, and
intrinsic timescales. Neuroimage 221 (February), 117141. https://doi.org/10.1016/
j.neuroimage.2020.117141.

J¨a¨askel¨ainen, I.P., Sams, M., Glerean, E., Ahveninen, J., 2021. Movies and narratives as
naturalistic stimuli in neuroimaging. Neuroimage 224 (June 2020), 117445. https://
doi.org/10.1016/j.neuroimage.2020.117445.

Jenkinson, M., Bannister, P., Brady, M., Smith, S., 2002. Improved optimization for the
robust and accurate linear registration and motion correction of brain images.
Neuroimage 17 (2), 825–841. https://doi.org/10.1006/nimg.2002.1132.

Jenkinson, M., Beckmann, C.F., Behrens, T.E.J., Woolrich, M.W., Smith, S.M., 2012. FSL.
Neuroimage 62 (2), 782–790. https://doi.org/10.1016/j.neuroimage.2011.09.015.

Jeon, H.A., 2014. Hierarchical processing in the prefrontal cortex in a variety of

cognitive domains. Front. Syst. Neurosci. 8 (NOV), 1–8. https://doi.org/10.3389/
fnsys.2014.00223. Frontiers Research Foundation.

21 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Ji, J.L., Spronk, M., Kulkarni, K., Repovˇs, G., Anticevic, A., Cole, M.W., 2019. Mapping
the human brain’s cortical-subcortical functional network organization. Neuroimage
185 (October 2018), 35–57. https://doi.org/10.1016/j.neuroimage.2018.10.006.

Jobson, D.D., Hase, Y., Clarkson, A.N., Kalaria, R.N., 2021. The role of the medial

prefrontal cortex in cognition, ageing and dementia. Brain Commun. 3 (3). https://
doi.org/10.1093/braincomms/fcab125.

Jones, D.K., Kn¨osche, T.R., Turner, R., 2013. White matter integrity, fiber count, and
other fallacies: the do’s and don’ts of diffusion MRI. Neuroimage 73, 239–254.
https://doi.org/10.1016/j.neuroimage.2012.06.081.

Jung, J.Y., Cloutman, L.L., Binney, R.J., Lambon Ralph, M.A., 2017. The structural

connectivity of higher order association cortices reflects human functional brain
networks. Cortex 97, 221–239. https://doi.org/10.1016/j.cortex.2016.08.011.
Kai, J., Khan, A.R., Haast, R.A., Lau, J.C., 2022. Mapping the subcortical connectome
using in vivo diffusion MRI: feasibility and reliability. Neuroimage 262 (March),
119553. https://doi.org/10.1016/j.neuroimage.2022.119553.

Keller, A.S., Sydnor, V.J., Pines, A., Fair, D.A., Bassett, D.S., Satterthwaite, T.D., 2023.

Hierarchical functional system development supports executive function. Trends.
Cogn. Sci. 27 (2), 160–174. https://doi.org/10.1016/j.tics.2022.11.005.

Kiebel, S.J., Daunizeau, J., Friston, K.J., 2008. A hierarchy of time-scales and the brain.

PLoS Comput. Biol. 4 (11). https://doi.org/10.1371/journal.pcbi.1000209.

Koechlin, E., Summerfield, C., 2007. An information theoretical approach to prefrontal
executive function. Trends Cogn. Sci. 11 (6), 229–235. https://doi.org/10.1016/j.
tics.2007.04.005.

Kruschke, J.K., 2011. Tutorial: doing Bayesian data analysis with R and BUGS. In:

Expanding the Space of Cognitive Science - Proceedings of the 33rd Annual Meeting
of the Cognitive Science Society, CogSci 2011, pp. 56–57.

Lee, D.K., 2016. Alternatives to P value: confidence interval and effect size. Korean J.

Anesthesiol. 69 (6), 555. https://doi.org/10.4097/kjae.2016.69.6.555.

Müller, E.J., Munn, B., Hearne, L.J., Smith, J.B., Fulcher, B., Arnatkeviˇci¯ut ˙e, A., Lurie, D.
J., Cocchi, L., Shine, J.M., 2020. Core and matrix thalamic sub-populations relate to
spatio-temporal cortical connectivity gradients. Neuroimage 222 (August), 117224.
https://doi.org/10.1016/j.neuroimage.2020.117224.

Murphy, C., Wang, H.T., Konu, D., Lowndes, R., Margulies, D.S., Jefferies, E.,

Smallwood, J., 2019. Modes of operation: a topographic neural gradient supporting
stimulus dependent and independent cognition. Neuroimage 186 (November 2018),
487–496. https://doi.org/10.1016/j.neuroimage.2018.11.009.

Murray, J.D., Bernacchia, A., Freedman, D.J., Romo, R., Wallis, J.D., Cai, X., Padoa-
Schioppa, C., Pasternak, T., Seo, H., Lee, D., Wang, X.J., 2014. A hierarchy of
intrinsic timescales across primate cortex. Nat. Neurosci. 17 (12), 1661–1663.
https://doi.org/10.1038/nn.3862.

Nastase, S.A., Gazzola, V., Hasson, U., Keysers, C., 2019. Measuring shared responses
across subjects using intersubject correlation. Soc. Cogn. Affect. Neurosci. 14 (6),
669–687. https://doi.org/10.1093/scan/nsz037.

Neudorf, J., Ekstrand, C., Kress, S., Borowsky, R., 2020. Brain structural connectivity
predicts brain functional complexity: diffusion tensor imaging derived centrality
accounts for variance in fractal properties of functional magnetic resonance imaging
signal. Neuroscience 438, 1–8. https://doi.org/10.1016/j.
neuroscience.2020.04.048.

Nieder, A., 2016. Representing something out of nothing: the dawning of zero. Trends

Cogn. Sci. 20 (11), 830–842. https://doi.org/10.1016/j.tics.2016.08.008.

Ogawa, T., Komatsu, H., 2010. Differential temporal storage capacity in the baseline

activity of neurons in macaque frontal eye field and area V4. J. Neurophysiol. 103
(5), 2433–2445. https://doi.org/10.1152/jn.01066.2009.

Oldfield, R.C., 1971. The assessment and analysis of handedness: the Edinburgh

inventory. Neuropsychologia1 9, 97–113. https://doi.org/10.1007/978-3-319-
55065-7_301010.

Lerner, Y., Honey, C.J., Silbert, L.J., Hasson, U., 2011. Topographic mapping of a

Oldham, S., Fornito, A., 2023. Hubs and rich clubs. Connectome Analysis:

hierarchy of temporal receptive windows using a narrated story. J. Neurosci. 31 (8),
2906–2915. https://doi.org/10.1523/JNEUROSCI.3684-10.2011.

Liu, Z.Q., Shafiei, G., Baillet, S., Misic, B., 2023. Spatially heterogeneous structure-
function coupling in haemodynamic and electromagnetic brain networks.
Neuroimage 278 (July), 120276. https://doi.org/10.1016/j.
neuroimage.2023.120276.

Lohia, K., Soans, R.S., Saxena, R., Mahajan, K., Gandhi, T.K., 2024. Distinct rich and

diverse clubs regulate coarse and fine binocular disparity processing: evidence from
stereoscopic task-based fMRI. iScience, 109831. https://doi.org/10.1016/j.
isci.2024.109831.

Lurie, D.J., Pappas, I., D’Esposito, M, 2024. Cortical timescales and the modular

organization of structural and functional brain networks. Hum. Brain Mapp. 45 (2).
https://doi.org/10.1002/hbm.26587.

Mahjoory, K., Schoffelen, J.M., Keitel, A., Gross, J., 2020. The frequency gradient of
human resting-state brain oscillations follows cortical hierarchies. Elife 9, 1–18.
https://doi.org/10.7554/ELIFE.53715.

Maldjian, J.A., Laurienti, P.J., Kraft, R.A., Burdette, J.H., 2003. An automated method
for neuroanatomic and cytoarchitectonic atlas-based interrogation of fMRI data sets.
Neuroimage 19 (3), 1233–1239. https://doi.org/10.1016/S1053-8119(03)00169-1.
Manea, A.M.G., Zilverstand, A., Ugurbil, K., Heilbronner, S.R., Zimmermann, J., 2022.

Intrinsic timescales as an organizational principle of neural processing across the
whole rhesus macaque brain. Elife 11, 1–20. https://doi.org/10.7554/eLife.75540.

Characterization, Methods, and Analysis. INC. https://doi.org/10.1016/B978-0-323-
85280-7.00015-4.

Oldham, S., Fulcher, B., Parkes, L., Arnatkevici¯ut ˙e, A., Suo, C., Fornito, A., 2019.

Consistency and differences between centrality measures across distinct classes of
networks. PLoS One 14 (7), 1–23. https://doi.org/10.1371/journal.pone.0220061.

Ortiz-Ter´an, L., Diez, I., Ortiz, T., Perez, D.L., Arag´on, J.I., Costumero, V., Pascual-
Leone, A., El Fakhri, G., Sepulcre, J, 2017. Brain circuit-gene expression
relationships and neuroplasticity of multisensory cortices in blind children. Proc.
Natl. Acad. Sci. USA 114 (26), 6830–6835. https://doi.org/10.1073/
pnas.1619121114.

Patriat, R., Molloy, E.K., Meier, T.B., Kirk, G.R., Nair, V.A., Meyerand, M.E.,

Prabhakaran, V., Birn, R.M., 2013. The effect of resting condition on resting-state
fMRI reliability and consistency: a comparison between resting with eyes open,
closed, and fixated. Neuroimage 78, 463–473. https://doi.org/10.1016/j.
neuroimage.2013.04.013.

Pinhas, M., Tzelgov, J., 2012. Expanding on the mental number line: zero is perceived as
the “smallest’’. J. Exp. Psychol. 38 (5), 1187–1205. https://doi.org/10.1037/
a0027390.

Power, J.D., Barnes, K.A., Snyder, A.Z., Schlaggar, B.L., Petersen, S.E., 2012. Spurious
but systematic correlations in functional connectivity MRI networks arise from
subject motion. Neuroimage 59 (3), 2142–2154. https://doi.org/10.1016/j.
neuroimage.2011.10.018.

Margulies, D.S., Ghosh, S.S., Goulas, A., Falkiewicz, M., Huntenburg, J.M., Langs, G.,

Preti, M.G., Van De Ville, D., 2019. Decoupling of brain function from structure reveals

Bezgin, G., Eickhoff, S.B., Castellanos, F.X., Petrides, M., Jefferies, E., Smallwood, J.,
2016. Situating the default-mode network along a principal gradient of macroscale
cortical organization. Proc. Natl. Acad. Sci. USA 113 (44), 12574–12579. https://
doi.org/10.1073/pnas.1608282113.

Markello, R.D., Hansen, J.Y., Liu, Z.Q., Bazinet, V., Shafiei, G., Su´arez, L.E., Blostein, N.,
Seidlitz, J., Baillet, S., Satterthwaite, T.D., Chakravarty, M.M., Raznahan, A.,
Misic, B., 2022. Neuromaps: structural and functional interpretation of brain maps.
Nat. Methods 19 (11), 1472–1479. https://doi.org/10.1038/s41592-022-01625-w.
Mashour, G.A., Roelfsema, P., Changeux, J.P., Dehaene, S., 2020. Conscious processing
and the global neuronal workspace hypothesis. Neuron 105 (5), 776–798. https://
doi.org/10.1016/j.neuron.2020.01.026.

Mathy, F., Feldman, J., 2012. What’s magic about magic numbers? Chunking and data
compression in short-term memory. Cognition 122 (3), 346–362. https://doi.org/
10.1016/j.cognition.2011.11.003.

Mecklenbrauck, F., Gruber, M., Siestrup, S., Zahedi, A., Grotegerd, D., Mauritz, M.,

Trempler, I., Dannlowski, U., Schubotz, R.I., 2024. The significance of structural rich
club hubs for the processing of hierarchical stimuli. Hum. Brain Mapp. 45 (4), 1–28.
https://doi.org/10.1002/hbm.26543.

Meilǎ, M., 2003. Comparing clusterings by the variation of information. In: Lecture Notes
in Artificial Intelligence (Subseries of Lecture Notes in Computer Science), 2777,
pp. 173–187. https://doi.org/10.1007/978-3-540-45167-9_14.

Mesulam, M.M., 1998. From sensation to cognition. Brain 121 (6), 1013–1052. https://

doi.org/10.1093/brain/121.6.1013.

Mohor, G.S., Thieken, A.H., Korup, O., 2021. Residential flood loss estimated from

Bayesian multilevel models. Nat. Haz. Earth Syst. Sci. 21 (5), 1599–1614. https://
doi.org/10.5194/nhess-21-1599-2021.

Moraczewski, D., Nketia, J., Redcay, E., 2020. Cortical temporal hierarchy is immature in
middle childhood. Neuroimage 216 (June 2019), 116616. https://doi.org/10.1016/
j.neuroimage.2020.116616.

Mori, S., Crain, B.J., Chacko, V.P., van Zilj, P.C.M., 1999. Three-dimensional tracking of
axonal projections in the brain by magnetic resonance imaging. Ann. Neurol. 45 (2),
265–269. https://doi.org/10.1002/1531-8249(199902)45:2<247::AID-
ANA16>3.0.CO;2-U.

regional behavioral specialization in humans. Nat. Commun. 10 (1), 1–7. https://
doi.org/10.1038/s41467-019-12765-7.

Pretus, C., Marcos-Vidal, L., Martínez-García, M., Picado, M., Ramos-Quiroga, J.A.,

Richarte, V., Castellanos, F.X., Sepulcre, J., Desco, M., Vilarroya,
2019. Stepwise functional connectivity reveals altered sensory-multimodal
integration in medication-naïve adults with attention deficit hyperactivity disorder.
Hum. Brain Mapp. 40 (16), 4645–4656. https://doi.org/10.1002/hbm.24727.
Qi, S., Meesters, S., Nicolay, K., ter Haar Romeny, B.M., Ossenblok, P., 2015. The

´
O., Carmona, S.,

influence of construction methodology on structural brain network measures: a
review. J. Neurosci. Methods 253 (500), 170–182. https://doi.org/10.1016/j.
jneumeth.2015.06.016.

R Core Team. (2022). R: A Language and Environment for Statistical Computing. https://

www.r-project.org/.

Raut, R.V., Snyder, A.Z., Raichle, M.E., 2020. Hierarchical dynamics as a macroscopic
organizing principle of the human brain. Proc. Natl. Acad. Sci. USA 117 (34),
20890–20897. https://doi.org/10.1073/pnas.2003383117.

Redcay, E., Moraczewski, D., 2020. Social cognition in context: a naturalistic imaging

approach. Neuroimage 216 (October 2019), 116392. https://doi.org/10.1016/j.
neuroimage.2019.116392.

Ren, Y., Nguyen, V.T., Guo, L., Guo, C.C., 2017. Inter-subject functional correlation

reveal a hierarchical organization of extrinsic and intrinsic systems in the brain. Sci.
Rep. 7 (1), 1–12. https://doi.org/10.1038/s41598-017-11324-8.

Riedel, L., van den Heuvel, M.P., Markett, S., 2022. Trajectory of rich club properties in
structural brain networks. Hum. Brain Mapp. 43 (14), 4239–4253. https://doi.org/
10.1002/hbm.25950.

Rouder, J.N., Haaf, J.M., Aust, F., 2018. From theories to models to predictions: a

Bayesian model comparison approach. Commun. Monogr. 85 (1), 41–56. https://
doi.org/10.1080/03637751.2017.1394581.

RStudio Team. (2022). RStudio: Integrated Development Environment for R. http://www.rst

udio.com/.

Rubinov, M., Sporns, O., 2010. Complex network measures of brain connectivity: uses
and interpretations. Neuroimage 52 (3), 1059–1069. https://doi.org/10.1016/j.
neuroimage.2009.10.003.

22 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Rust, N.C., Movshon, J.A., 2005. In praise of artifice. Nat. Neurosci. 8 (12), 1647–1650.

https://doi.org/10.1038/nn1606.

Saberi, A., Paquola, C., Wagstyl, K., Hettwer, M.D., Bernhardt, B.C., Eickhoff, S.B.,

Valk, S.L., 2023. The regional variation of laminar thickness in the human isocortex
is related to cortical hierarchy and interregional connectivity. PLoS Biol. 21 (11
November), 1–29. https://doi.org/10.1371/journal.pbio.3002365.

Satterthwaite, T.D., Elliott, M.A., Gerraty, R.T., Ruparel, K., Loughead, J., Calkins, M.E.,
Eickhoff, S.B., Hakonarson, H., Gur, R.C., Gur, R.E., Wolf, D.H., 2013. An improved
framework for confound regression and filtering for control of motion artifact in the
preprocessing of resting-state functional connectivity data. Neuroimage 64 (1),
240–256. https://doi.org/10.1016/j.neuroimage.2012.08.052.

Schaefer, A., Kong, R., Gordon, E.M., Laumann, T.O., Zuo, X.-N., Holmes, A.J.,

Eickhoff, S.B., Yeo, B.T.T., 2018. Local-global parcellation of the human cerebral
cortex from intrinsic functional connectivity MRI. Cereb. Cortex 28 (9), 3095–3114.
https://doi.org/10.1093/cercor/bhx179.

Schm¨alzle, R., Imhof, M.A., Grall, C., Flaisch, T., Schupp, H.T., Schm¨alzle, R., Imhof, M.
A., Grall, C., Flaisch, T., & Schupp, H.T. (2017). Reliability of fMRI time series:
similarity of neural processing during movie viewing. bioRxiv, 158188. https://doi.
org/10.1101/158188.

Schmidt, M., Bakker, R., Shen, K., Bezgin, G., Diesmann, M., Van Albada, S.J., & Schmidt,
M. (2016). Full-density multi-scale account of structure and dynamics of macaque visual
cortex correspondence to: https://doi.org/10.48550/arXiv.1511.09364.

Scholtens, L.H., Schmidt, R., de Reus, M.A., van den Heuvel, M.P., 2014. Linking

macroscale graph analytical organization to microscale neuroarchitectonics in the
macaque connectome. J. Neurosci. 34 (36), 12192–12205. https://doi.org/10.1523/
JNEUROSCI.0752-14.2014.

Seguin, C., Tian, Y., Zalesky, A., 2020. Network communication models improve the
behavioral and functional predictive utility of the human structural connectome.
Netw. Neurosci. 4 (4), 980–1006. https://doi.org/10.1162/netn_a_00161.

mechanisms, and implications for psychopathology. Neuron 109 (18), 2820–2846.
https://doi.org/10.1016/j.neuron.2021.06.016.

Sydnor, V.J., Larsen, B., Seidlitz, J., Adebimpe, A., Alexander-Bloch, A.F., Bassett, D.S.,
Bertolero, M.A., Cieslak, M., Covitz, S., Fan, Y., Gur, R.E., Gur, R.C., Mackey, A.P.,
Moore, T.M., Roalf, D.R., Shinohara, R.T., Satterthwaite, T.D., 2023. Intrinsic
activity development unfolds along a sensorimotor–association cortical axis in
youth. Nat. Neurosci. 26 (4), 638–649. https://doi.org/10.1038/s41593-023-01282-
y.

Taylor, P., Hobbs, J.N., Burroni, J., Siegelmann, H.T., 2015. The global landscape of

cognition: hierarchical aggregation as an organizational principle of human cortical
networks and functions. Sci. Rep. 5 (November), 1–18. https://doi.org/10.1038/
srep18112.

The MathWorks Inc., 2021. MATLAB version: 9.10.0 (R2021a). The MathWorks Inc.

https://www.mathworks.com.

Thomas, R.M., De Sanctis, T., Gazzola, V., Keysers, C., 2018. Where and how our brain
represents the temporal structure of observed action. Neuroimage 183 (November
2017), 677–697. https://doi.org/10.1016/j.neuroimage.2018.08.056.

Tomczak, M., Tomczak, E., 2014. The need to report effect size estimates revisited. An
overview of some recommended measures of effect size. Trends Sport Sci. 1 (21),
19–25. http://www.wbc.poznan.pl/Content/325867/5_Trends_Vol21_2014_no1_20.
pdf.

Torres-Gomez, S., Blonde, J.D., Mendoza-Halliday, D., Kuebler, E., Everest, M., Wang, X.-
J., Inoue, W., Poulter, M.O., Martinez-Trujillo, J., 2020. Changes in the proportion of
inhibitory interneuron types from sensory to executive areas of the primate
neocortex: implications for the origins of working memory representations. Cereb.
Cortex 30 (8), 4544–4562. https://doi.org/10.1093/cercor/bhaa056.

Tourbier, S., Aleman-Gomez, Y., Griffa, A., Bach Cuadra, M., & Hagmann, P. (2019).
Sebastientourbier/multiscalebrainparcellator: Multi-Scale Brain Parcellator v1.1.1.
https://doi.org/10.5281/ZENODO.3627097.

Senden, M., Deco, G., De Reus, M.A., Goebel, R., van den Heuvel, M.P., 2014. Rich club

Tzourio-Mazoyer, N., Landeau, B., Papathanassiou, D., Crivello, F., Etard, O.,

organization supports a diverse set of functional network configurations.
Neuroimage 96, 174–182. https://doi.org/10.1016/j.neuroimage.2014.03.066.
Senden, M., Reuter, N., van den Heuvel, M.P., Goebel, R., Deco, G., 2017. Cortical rich
club regions can organize state-dependent functional network formation by engaging
in oscillatory behavior. Neuroimage 146, 561–574. https://doi.org/10.1016/j.
neuroimage.2016.10.044.

Sepulcre, J., 2014. Integration of visual and motor functional streams in the human
brain. Neurosci. Lett. 567, 68–73. https://doi.org/10.1016/j.neulet.2014.03.050.
Sepulcre, J., Liu, H., Talukdar, T., Martincorena, I., Thomas Yeo, B.T., Buckner, R.L.,
2010. The organization of local and distant functional connectivity in the human
brain. PLoS Comput. Biol. 6 (6), 1–15. https://doi.org/10.1371/journal.
pcbi.1000808.

Sepulcre, J., Sabuncu, M.R., Yeo, T.B., Liu, H., Johnson, K.A., 2012. Stepwise

connectivity of the modal cortex reveals the multimodal organization of the human
brain. J. Neurosci. 32 (31), 10649–10661. https://doi.org/10.1523/
JNEUROSCI.0759-12.2012.

Sethi, S.S., Zerbi, V., Wenderoth, N., Fornito, A., Fulcher, B.D., 2017. Structural

connectome topology relates to regional BOLD signal dynamics in the mouse brain.
Chaos 27 (4). https://doi.org/10.1063/1.4979281.

Shafiei, G., Fulcher, B.D., Voytek, B., Satterthwaite, T.D., Baillet, S., Misic, B., 2023.

Neurophysiological signatures of cortical micro-architecture. Nat. Commun. 14 (1).
https://doi.org/10.1038/s41467-023-41689-6.

Shafiei, G., Markello, R.D., De Wael, R.V., Bernhardt, B.C., Fulcher, B.D., Misic, B., 2020.
Topographic gradients of intrinsic dynamics across neocortex. Elife 9, 1–24. https://
doi.org/10.7554/eLife.62116.

Shen, X., Tokoglu, F., Papademetris, X., Constable, R.T., 2013. Groupwise whole-brain

parcellation from resting-state fMRI data for network node identification.
Neuroimage 82, 403–415. https://doi.org/10.1016/j.neuroimage.2013.05.081.

Shine, J.M., Hearne, L.J., Breakspear, M., Hwang, K., Müller, E.J., Sporns, O.,

Poldrack, R.A., Mattingley, J.B., Cocchi, L., 2019. The low-dimensional neural
architecture of cognitive complexity is related to activity in medial thalamic nuclei.
Neuron 104 (5), 849–855.e3. https://doi.org/10.1016/j.neuron.2019.09.002.
Siegle, J.H., Jia, X., Durand, S., Gale, S., Bennett, C., Graddis, N., Heller, G., Ramirez, T.
K., Choi, H., Luviano, J.A., Groblewski, P.A., Ahmed, R., Arkhipov, A., Bernard, A.,
Billeh, Y.N., Brown, D., Buice, M.A., Cain, N., Caldejon, S., Koch, C., 2021. Survey of
spiking in the mouse visual system reveals functional hierarchy. Nature 592 (7852),
86–92. https://doi.org/10.1038/s41586-020-03171-x.

Smith, S.M., Jenkinson, M., Woolrich, M.W., Beckmann, C.F., Behrens, T.E.J., Johansen-
Berg, H., Bannister, P.R., De Luca, M., Drobnjak, I., Flitney, D.E., Niazy, R.K.,
Saunders, J., Vickers, J., Zhang, Y., De Stefano, N., Brady, J.M., Matthews, P.M.,
2004. Advances in functional and structural MR image analysis and implementation
as FSL. Neuroimage 23 (SUPPL. 1), 208–219. https://doi.org/10.1016/j.
neuroimage.2004.07.051.

Soltani, A., Murray, J.D., Seo, H., Lee, D., 2021. Timescales of cognition in the brain.
Curr. Opin. Behav. Sci. 41, 30–37. https://doi.org/10.1016/j.cobeha.2021.03.003.

Sonkusare, S., Breakspear, M., Guo, C., 2019. Naturalistic stimuli in neuroscience:

critically acclaimed. Trends. Cogn. Sci. 23 (8), 699–714. https://doi.org/10.1016/j.
tics.2019.05.004.

Delcroix, N., Mazoyer, B., Joliot, M., 2002. Automated anatomical labeling of
activations in SPM using a macroscopic anatomical parcellation of the MNI MRI
single-subject brain. Neuroimage 15 (1), 273–289. https://doi.org/10.1006/
nimg.2001.0978.

Uithol, S., van Rooij, I., Bekkering, H., Haselager, P., 2012. Hierarchies in action and

motor control. J. Cogn. Neurosci. 24 (5), 1077–1086. https://doi.org/10.1162/jocn_
a_00204.

Valk, S.L., Xu, T., Margulies, D.S., Masouleh, S.K., Paquola, C., Goulas, A., Kochunov, P.,
Smallwood, J., Yeo, B.T.T., Bernhardt, B.C., Eickhoff, S.B., 2020. Shaping brain
structure: genetic and phylogenetic axes of macroscale organization of cortical
thickness. Sci. Adv. 6 (39), 1–14. https://doi.org/10.1126/sciadv.abb3417.

van den Heuvel, M.P., Scholtens, L.H., Barrett, L.F., Hilgetag, C.C., de Reus, M.A., 2015.
Bridging cytoarchitectonics and connectomics in human cerebral cortex. J. Neurosci.
35 (41), 13943–13948. https://doi.org/10.1523/JNEUROSCI.2630-15.2015.
van den Heuvel, M.P., Scholtens, L.H., van der Burgh, H.K., Agosta, F., Alloza, C.,

Arango, C., Auyeung, B., Baron-Cohen, S., Basaia, S., Benders, M.J.N.L., Beyer, F.,
Booij, L., Braun, K.P.J., Filho, G.B., Cahn, W., Cannon, D.M., Chaim-Avancini, T.M.,
Chan, S.S.M., Chen, E.Y.H., de Lange, S.C., 2019. 10kin1day: a bottom-up
neuroimaging initiative. Front. Neurol. 10 (MAY). https://doi.org/10.3389/
fneur.2019.00425.

van den Heuvel, M.P., Sporns, O., 2011. Rich-club organization of the human
connectome. J. Neurosci. 31 (44), 15775–15786. https://doi.org/10.1523/
JNEUROSCI.3539-11.2011.

van den Heuvel, M.P., Sporns, O., 2013a. An anatomical substrate for integration among
functional networks in human cortex. J. Neurosci. 33 (36), 14489–14500. https://
doi.org/10.1523/JNEUROSCI.2128-13.2013.

van den Heuvel, M.P., Sporns, O., 2013b. Network hubs in the human brain. Trends

Cogn. Sci. 17 (12), 683–696. https://doi.org/10.1016/j.tics.2013.09.012.
van den Heuvel, M.P., Sporns, O., Collin, G., Scheewe, T., Mandl, R.C.W., Cahn, W.,
Goni, J., Pol, H.E.H., Kahn, R.S., 2013. Abnormal rich club organization and
functional brain dynamics in schizophrenia. JAMA Psychiatry 70 (8), 783–792.
https://doi.org/10.1001/jamapsychiatry.2013.1328.

Van Dijk, K.R.A., Hedden, T., Venkataraman, A., Evans, K.C., Lazar, S.W., Buckner, R.L.,

2010. Intrinsic functional connectivity as a tool for human connectomics: theory,
properties, and optimization. J. Neurophysiol. 103 (1), 297–321. https://doi.org/
10.1152/jn.00783.2009.

van Doorn, J., van den Bergh, D., B¨ohm, U., Dablander, F., Derks, K., Draws, T., Etz, A.,
ˇ
S., Ly, A., Marsman, M.,

Evans, N.J., Gronau, Q.F., Haaf, J.M., Hinne, M., Kucharský,
Matzke, D., Gupta, A.R.K.N., Sarafoglou, A., Stefan, A., Voelkel, J.G.,
Wagenmakers, E.J., 2021. The JASP guidelines for conducting and reporting a
Bayesian analysis. Psychon. Bull. Rev. 28 (3), 813–826. https://doi.org/10.3758/
s13423-020-01798-5.

V´azquez-Rodríguez, B., Su´arez, L.E., Markello, R.D., Shafiei, G., Paquola, C.,

Hagmann, P., Van Den Heuvel, M.P., Bernhardt, B.C., Spreng, R.N., Misic, B, 2019.
Gradients of structure–function tethering across neocortex. Proc. Natl. Acad. Sci.
USA 116 (42), 21219–21227. https://doi.org/10.1073/pnas.1903403116.

Vehtari, A., 2024. Loo Package Glossary - Loo-Glossary. Loo-Glossary • Loo. https://mc

-stan.org/loo/reference/loo-glossary.html.

Sporns, O., 2011. The human connectome: a complex network. Ann. N. Y. Acad. Sci.

Vehtari, A., Gelman, A., Gabry, J., 2017. Practical Bayesian model evaluation using

1224 (1), 109–125. https://doi.org/10.1111/j.1749-6632.2010.05888.x.
Stephens, G.J., Honey, C.J., Hasson, U., 2013. A place for time: the spatiotemporal
structure of neural dynamics during natural audition. J. Neurophysiol. 110 (9),
2019–2026. https://doi.org/10.1152/jn.00268.2013.

Sydnor, V.J., Larsen, B., Bassett, D.S., Alexander-Bloch, A., Fair, D.A., Liston, C.,

Mackey, A.P., Milham, M.P., Pines, A., Roalf, D.R., Seidlitz, J., Xu, T., Raznahan, A.,
Satterthwaite, T.D., 2021. Neurodevelopment of the association cortices: patterns,

leave-one-out cross-validation and WAIC. Stat. Comput. 27 (5), 1413–1432. https://
doi.org/10.1007/s11222-016-9696-4.

Vehtari, A., Gelman, A., Simpson, D., Carpenter, B., Bürkner, P.-C., 2021. Rank-

normalization, folding, and localization: an improved Rˆfor assessing convergence of
MCMC (with discussion). Bayesian Anal. 16 (2), 667–718. https://doi.org/10.1214/
20-BA1221.

23 

F. Mecklenbrauck et al.

NeuroImage 303 (2024) 120914 

Vogelbacher, C., M¨obius, T.W.D., Sommer, J., Schuster, V., Dannlowski, U., Kircher, T.,
Dempfle, A., Jansen, A., Bopp, M.H.A., 2018. The Marburg-Münster affective
disorders cohort study (MACS): a quality assurance protocol for MR neuroimaging
data. Neuroimage 172 (December 2017), 450–460. https://doi.org/10.1016/j.
neuroimage.2018.01.079.

Wagstyl, K., Ronan, L., Goodyer, I.M., Fletcher, P.C., 2015. Cortical thickness gradients in
structural hierarchies. Neuroimage 111, 241–250. https://doi.org/10.1016/j.
neuroimage.2015.02.036.

Wang, M., Yang, Y., Wang, C., Gamo, N.J., Jin, L.E., Mazer, J.A., Morrison, J.H.,
Wang, X., Arnsten, A.F.T., 2012. Article NMDA receptors subserve persistent
neuronal firing during working memory in dorsolateral prefrontal cortex. Neuron 77
(4), 736–749. https://doi.org/10.1016/j.neuron.2012.12.032.

Wang, X.-J., 2001. Synaptic reverberation underlying mnemonic persistent activity.

Trends Neurosci. 24 (8), 455–463. https://doi.org/10.1016/S0166-2236(00)01868-
3.

Wang, X.-J., 2020. Macroscopic gradients of synaptic excitation and inhibition in the
neocortex. Nat. Rev. Neurosci. 21 (3), 169–178. https://doi.org/10.1038/s41583-
020-0262-x.

Watanabe, T., 2013. Rich-club network topology to minimize synchronization cost due to
phase difference among frequency-synchronized oscillators. Physica A 392 (5),
1246–1255. https://doi.org/10.1016/j.physa.2012.11.041.

Whitaker, K.J., V´ertes, P.E., Romero-Garciaa, R., V´aˇsa, F., Moutoussis, M., Prabhu, G.,
Weiskopf, N., Callaghan, M.F., Wagstyl, K., Rittman, T., Tait, R., Ooi, C., Suckling, J.,
Inkster, B., Fonagy, P., Dolan, R.J., Jones, P.B., Goodyer, I.M., Bullmore, E.T., 2016.
Adolescence is associated with genomically patterned consolidation of the hubs of
the human brain connectome. Proc. Natl. Acad. Sci. USA 113 (32), 9105–9110.
https://doi.org/10.1073/pnas.1601745113.

Wolff, A., Berberian, N., Golesorkhi, M., Gomez-Pilar, J., Zilio, F., Northoff, G., 2022.

Intrinsic neural timescales: temporal integration and segregation. Trends Cogn. Sci.
26 (2), 159–173. https://doi.org/10.1016/j.tics.2021.11.007.

Wooldridge, J.M., 2013. Introductory Econometrics: A Modern Approach, fifth ed. South-

Western Cengage Learning.

Xu, T., Nenning, K.H., Schwartz, E., Hong, S.J., Vogelstein, J.T., Goulas, A., Fair, D.A.,
Schroeder, C.E., Margulies, D.S., Smallwood, J., Milham, M.P., Langs, G., 2020.

Cross-species functional alignment reveals evolutionary hierarchy within the
connectome. Neuroimage 223 (September), 117346. https://doi.org/10.1016/j.
neuroimage.2020.117346.

Xue, C., Sun, H., Hu, G., Qi, W., Yue, Y., Rao, J., Yang, W., Xiao, C., Chen, J., 2020.

Disrupted patterns of rich-club and diverse-club organizations in subjective cognitive
decline and amnestic mild cognitive impairment. Front. Neurosci. 14 (October),
1–14. https://doi.org/10.3389/fnins.2020.575652.

Yeh, F.C., Wedeen, V.J., Tseng, W.Y.I., 2010. Generalized q-sampling imaging. IEEE

Trans. Med. ImAging 29 (9), 1626–1635. https://doi.org/10.1109/
TMI.2010.2045126.

Yeo, B.T.T., Krienen, F.M., Eickhoff, S.B., Yaakub, S.N., Fox, P.T., Buckner, R.L.,

Asplund, C.L., Chee, M.W.L., 2015. Functional specialization and flexibility in
human association cortex. Cereb. Cortex 25 (10), 3654–3672. https://doi.org/
10.1093/cercor/bhu217.

Zamora-L´opez, G., Chen, Y., Deco, G., Kringelbach, M.L., Zhou, C., 2016. Functional

complexity emerging from anatomical constraints in the brain: the significance of
network modularity and rich-clubs. Sci. Rep. 6 (November), 1–18. https://doi.org/
10.1038/srep38424.

Zamora-L´opez, G., Zhou, C., Kurths, J., 2009. Graph analysis of cortical networks reveals
complex anatomical communication substrate. Chaos 19 (1). https://doi.org/
10.1063/1.3089559.

Zamora-L´opez, G., Zhou, C., Kurths, J., 2010. Cortical hubs form a module for

multisensory integration on top of the hierarchy of cortical networks. Front.
Neuroinform. 4 (MAR), 1–13. https://doi.org/10.3389/neuro.11.001.2010.

Zamora-L´opez, G., Zhou, C., Kurths, J., 2011. Exploring brain function from anatomical

connectivity. Front. Neurosci. 5 (JUN), 1–11. https://doi.org/10.3389/
fnins.2011.00083.

Zilio, F., Gomez-Pilar, J., Cao, S., Zhang, J., Zang, D., Qi, Z., Tan, J., Hiromi, T., Wu, X.,
Fogel, S., Huang, Z., Hohmann, M.R., Fomina, T., Synofzik, M., Grosse-Wentrup, M.,
Owen, A.M., Northoff, G., 2021. Are intrinsic neural timescales related to sensory
processing? Evidence from abnormal behavioral states. Neuroimage 226 (November
2020), 117579. https://doi.org/10.1016/j.neuroimage.2020.117579.

24 

