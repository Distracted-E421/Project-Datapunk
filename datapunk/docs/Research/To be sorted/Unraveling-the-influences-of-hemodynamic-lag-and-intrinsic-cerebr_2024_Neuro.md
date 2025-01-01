NeuroImage 303 (2024) 120920 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Unraveling the influences of hemodynamic lag and intrinsic
cerebrovascular reactivity on functional metrics in ischemic stroke

Luoyu Wang a,b,c, Xiumei Wu a,d, Jinyi Song e, Yanhui Fu f, Zhenqiang Ma f, Xiaoyan Wu g,
Yiying Wang h, Yulin Song f, Fenyang Chen i, Zhongxiang Ding b,**,1, Yating Lv a,d,*,1
a Center for Cognition and Brain Disorders, the Affiliated Hospital of Hangzhou Normal University, Hangzhou, Zhejiang, PR China
b Department of radiology, Affiliated Hangzhou First People’s Hospital, School of Medicine, Westlake University, PR China
c School of Biomedical Engineering, ShanghaiTech University, Shanghai, PR China
d Zhejiang Key Laboratory for Research in Assessment of Cognitive Impairments, Hangzhou, Zhejiang, PR China
e Zhejiang University School of Medicine, Hangzhou, Zhejiang, PR China
f Department of Neurology, Anshan Changda Hospital, Anshan, Liaoning, PR China
g Department of Image, Anshan Changda Hospital, Anshan, Liaoning, PR China
h Department of Ultrasonics, Anshan Changda Hospital, Anshan, Liaoning, PR China
i The Fourth school of Medical, Zhejiang Chinese Medical University, Hangzhou, Zhejiang, PR China

A R T I C L E I N F O

A B S T R A C T

Keywords:
Ischemic stroke
Resting-state functional magnetic resonance
imaging
Hemodynamic lags
Cerebrovascular reactivity

Resting-state functional magnetic resonance imaging (rs-fMRI) is a prominent tool for investigating functional
deficits in stroke patients. However, the extent to which the hemodynamic lags (LAG) and the intrinsic cere-
brovascular reactivity (iCVR) may affect the rs-fMRI metrics in different scales needs to be clarified for ischemic
stroke. In this study, 73 ischemic stroke patients and 74 healthy controls (HC) were recruited to investigate how
the correction of the LAG and/or iCVR would influence resting-state functional magnetic resonance imaging (rs-
fMRI) metrics of three different spatial scales (local-scale, meso-scale and global-scale) in ischemic stroke. The
analysis revealed that the Stroke pattern of all functional metrics using different correction strategies resembled
the HC pattern. The highest overlap was observed in the Stroke pattern with correction for both LAG and iCVR,
while the pattern without correction showed the lowest overlap. Most functional metrics after correction showed
higher sensitivity in detecting between-group differences than those without correction. Moreover, our results
were generally reproducible in an independent dataset. Collectively, these findings emphasize the necessity of
considering LAG and iCVR effects to investigate stroke-related functional alterations, and highlight the signifi-
cance of correction strategies for accurately interpreting the findings in rs-fMRI study of ischemic stroke.

1. Introduction

Stroke is the second-leading cause of death and the third-leading
cause of death and disability combined in the world until 2022 (Feigin
et al., 2022; Hankey, 2017). Most of the strokes are ischemic, caused by
blockage of cerebral vessels, resulting in behavioral and functional im-
pairments (Campbell and Khatri, 2020; Collaborators, 2019) which have
a terrible impact on daily activities, quality of life and health costs
(Ekker et al., 2018; Hankey, 2017; Qiu and Xu, 2020).

After ischemic stroke onset, a disruption to the cerebral vascular
supply could lead to infarction and structural damage of cerebral

parenchyma (Hu et al., 2017). The focal lesions in stroke further induce
widespread dysfunctions in brain areas distant from the infarction
(Grefkes and Fink, 2014). As evidence mounted in the past decade, it has
become increasingly apparent that understanding the mental and
behavioral deficits of patients requires a comprehensive description of
functional brain abnormalities after stroke (Brodtmann et al., 2021; Lyu
et al., 2019; Moulton et al., 2023). The developments of resting-state
functional magnetic resonance imaging (rs-fMRI) technology have
made it possible to explore these functional deficits in stroke patients
(Cohen et al., 2021; Fox and Raichle, 2007; Gao et al., 2021; Lv et al.,
2019; Park et al., 2011; Siegel et al., 2016a). According to the spatial

* Corresponding author at: Centre for Cognition and Brain Disorders, The Affiliated Hospital of Hangzhou Normal University, Hangzhou 310015, PR China.
** Corresponding author at: Department of radiology, Affiliated Hangzhou First People’s Hospital, School of Medicine, Westlake University, PR China.

E-mail addresses: hangzhoudzx73@126.com (Z. Ding), lvyating198247@gmail.com (Y. Lv).

1 Equal contribution (senior author)

https://doi.org/10.1016/j.neuroimage.2024.120920
Received 12 August 2024; Received in revised form 4 November 2024; Accepted 6 November 2024
Available online 8 November 2024 
1053-8119/© 2024 The Authors.  Published by Elsevier Inc.  This is an open access article under the CC BY-NC license ( http://creativecommons.org/licenses/by- 
nc/4.0/ ). 

L. Wang et al.

NeuroImage 303 (2024) 120920 

scale at which they characterize brain function, the rs-fMRI-derived
metrics can be categorized into three types, namely the local-scale,
meso-scale, and global-scale. Local-scale metrics involve the examina-
tion of brain function within individual,
localized brain regions;
meso-scale metrics pertain to the connectivity and function of sub-
networks within the brain; global-scale metrics examine the brain as an
entire system, assessing overall brain connectivity and network inte-
gration (Fan et al., 2023; He et al., 2009; Lv et al., 2019; Wu et al., 2023;
Zang et al., 2007, 2004). At each scale, these metrics are used to char-
acterize information segregation and integration in functional con-
nectomics (Chen et al., 2015). Notably, a critical assumption in most
rs-fMRI research is that neurovascular coupling is relatively consistent
across brain areas, over time, and between individuals (Buckner et al.,
2013). With respect to cerebrovascular diseases such as stroke, however,
it is not possible to assume that the hemodynamic response would be
normal (D’Esposito et al., 2003; Siegel et al., 2017).

using

(BOLD)

response

level-dependent

The fMRI signal essentially reflects the level of blood oxygen meta-
bolism which is influenced by cerebral hemodynamics (Amemiya et al.,
2012; Carusone et al., 2002). It has been reported that the vasculature
with impaired hemodynamic function has an increased latency in blood
oxygen
task-fMRI
(Bonakdarpour et al., 2007). A series of studies have consistently
observed temporal delays of the resting-state BOLD signals in the
hypoperfusion areas in patients with ischemic stroke or other cerebro-
vascular diseases (Amemiya et al., 2014; Bauer et al., 2014; Christen
et al., 2015; Lv et al., 2013; Ovadia-Caro et al., 2014; Siegel et al.,
(LAG) were measured by
2016b). These hemodynamic
cross-correlation (i.e., time-shift analysis, TSA) of regional BOLD signal
with the reference time course (Bauer et al., 2014; Christen et al., 2015;
Fan et al., 2023; Lv et al., 2013). The researchers further indicated that
the LAG of BOLD signals in the ischemic stroke could affect the pattern
of functional brain networks, and the LAG correction would partially
correct abnormalities in the measured networks (Chi et al., 2018;
Christen et al., 2015; Jahanian et al., 2018; Siegel et al., 2016b). How-
ever, whether and how the LAG of BOLD signals in ischemic stroke may
affect the other metrics of rs-fMRI needs to be elucidated.

lags

On the other hand, a decrease in the amplitude or a complete loss of
the BOLD response has been observed in the absence of LAG in stroke
patients (Blicher et al., 2012; Krainik et al., 2005; Rossini et al., 2004;
Salinet et al., 2014). Thus, correcting for the LAG may not be a complete
fix for the altered neurovascular coupling in ischemic stroke. Cerebro-
vascular reactivity (CVR), a marker of brain vascular reserve, is defined
as the change in blood flow per unit change in PCO2. The brain tissue
with abnormal CVR indicates microvascular dysfunction and risk of
ischemic stroke (Han et al., 2011; Reinhard et al., 2014). A recent study
has also indicated that CVR and LAG may reflect different aspects of
neurodynamic alterations and are largely independent of each other
(Braban et al., 2023). This underscores the necessity of addressing CVR
variations in BOLD signal analysis, even more important in the context
of studying diseased brains, such as stroke and Alzheimer’s disease
(Braban et al., 2023; Ni et al., 2022). The use of CO2 gas-inhalation fMRI
paradigms is one of the prevalent methods for assessing CVR due to its
effectiveness in evaluating the dilatory function of cerebral blood vessels
(Blicher et al., 2012; Lu et al., 2014). Alternative methods, such as
breath-hold paradigms (Bright et al., 2013; Geranmayeh et al., 2015)
which leverage the body’s natural response to increased CO2 levels
during breath-holding to induce cerebral vasodilation and can be
particularly useful in situations where the administration of exogenous
substances is not possible. Additionally, the injection of vasodilatory
substances represents another method to directly challenge the cere-
brovascular system and measure its reactivity. Golestani et al. intro-
duced an alternative method to quantify CVR by leveraging intrinsic
fluctuations in CO2 levels and the corresponding changes in the
resting-state BOLD signal (Golestani et al., 2016b). This method requires
simultaneous monitoring of end-tidal CO2, cardiac pulsation, and res-
piratory volume. Their findings established the feasibility of extracting

quantitative CVR maps using resting-state fMRI data (termed as
rs-qCVR), aligning closely with results obtained from conventional CVR
assessments involving gas inhalation. Meanwhile, Liu et al. proposed a
novel CVR mapping approach that utilized the natural variations in
respiration over time as an intrinsic vasoactive stimulus, thereby obvi-
ating the need for gas challenges (Liu et al., 2017). This approach esti-
mates voxel-level CVR by monitoring global BOLD signal fluctuations,
particularly within the frequency range of 0.02–0.04 Hz, which are
correlated with natural respiratory variations and arterial CO2 fluctua-
tions, thus eliminating the need for CO2 inhalation during assessments,
which we refer to as intrinsic CVR (iCVR) to prevent misunderstandings.
Ni et al. further validated this approach by demonstrating its application
in a clinical population, providing insights into the potential variations
in iCVR associated with pathological conditions, and showed that iCVR
can significantly influence functional metrics such as amplitude of
low-frequency fluctuation (ALFF) (Ni et al., 2022). However, the extent
to which CVR may affect the rs-fMRI metrics in different scales remains
unclarified for ischemic stroke. Given the involvement of stroke patients
and the prolonged MRI scanning sessions, we chose to employ the iCVR
to explore its effect on rs-fMRI metrics instead of traditional CVR
assessments.

Therefore, in the present study, we systematically investigated how
the correction of the LAG and/or iCVR in the BOLD signal would affect
rs-fMRI metrics of three different spatial scales (local-scale, meso-scale,
and global-scale) in ischemic stroke. Specifically, using different
correction strategies, we first sought to explore the degree of overlap for
the intrinsic patterns of different rs-fMRI metrics between ischemic
stroke patients (Stroke) and healthy controls (HC). Further, we exam-
ined the alterations of between-group differences (i.e., Stroke vs HC) for
different rs-fMRI metrics. At the same time, a stroke-specific indicator,
interhemispheric connectivity, was also calculated for group compari-
son. Finally, the results were validated in an independent dataset. We
hypothesized that stroke patients and healthy individuals have different
intrinsic patterns. After correction, the intrinsic patterns of the two
groups tend to converge, but the inter-group differences may increase.

2. Methods

2.1. Participants

From April 2018 to June 2021, 79 ischemic stroke patients (59.15±
6.63 years, 32 females) and 74 healthy controls (HC) (57.43 ± 6.83, 31
females) were recruited at the Anshan Changda Hospital. The inclusion
criteria for patients were as follows: 1) diagnosis of ischemic stroke by
neurologists; 2) admission <1 month after stroke onset; 3) unilateral
focal brain lesions; 4) subcortical infarction. Patients were excluded if
they had another psychiatric disease history, hemorrhage, epilepsy, or
migraine. The HC were enrolled when they had no history of physical or
psychiatric diseases. All the participants were right-handed. This study
was authorized by the Ethics Committee of the Center for Cognition and
Brain Disorders, Hangzhou Normal University, and conducted in
accordance with the Declaration of Helsinki. Each participant signed
informed consent before joining the current study.

Within 24 hours before the MRI scanning, participants completed the
following assessments: Activity Daily Living Scale (ADL) and Mini-
mental State Examination (MMSE). Additionally, the National In-
stitutes of Health Stroke Scale (NIHSS) was recorded for stroke patients
as well.

2.2. Multimodal MRI data acquisition

The MRI data were acquired with a 3-Tesla scanner (GE MR-750,
Waukesha, WI) at Anshan Changda Hospital. All patients underwent
MRI scanning within one month after stroke onset. All participants were
asked to remain quiet and keep their eyes closed, but not to fall asleep
(Liang et al., 2020; Fan et al., 2023; Wu et al., 2023; Li et al., 2024). The

2 

L. Wang et al.

NeuroImage 303 (2024) 120920 

scanning parameters were as follows: 1) axial rs-fMRI: slice = 43, slice
thickness/gap = 3.2/0 mm, echo time (TE) = 30 ms, repetition time (TR)
= 2000 ms, field of view (FOV) = 220 × 220 mm2, matrix size = 64 ×
◦
64, voxel size = 3.4 mm × 3.4 mm × 3.2 mm, flip angle (FA) = 90
,
volumes = 240, and parallel acceleration = 2; 2) T1-weighted 3D fast
spoiled gradient-recalled (FSPGR): slice = 176, slice thickness/gap =
1/0 mm, TR = 8100 ms, TE = 3.1 ms, FOV = 256 × 256 mm2, matrix size
◦
= 256 × 256, voxel size = 1 mm × 1 mm × 1 mm, FA = 8
, bandwidth =
31.25 kHz and parallel acceleration = 2, the long TR and very short TE,
combined with a low FA, are optimized to enhance the T1 contrast; 3)
axial diffusion-weighted imaging (DWI): slice = 22, slice thickness/gap
= 5/1 mm, TR = 4000 ms, FOV = 240 × 240 mm2, b value = 1000.

2.3. Creation of lesion map

Using

software

ITK-SNAP

(https://www.itksnap.org/pmwiki/
pmwiki.php) (Yushkevich et al., 2006), one radiologist (F.C. with 5
years of neuroimaging diagnostic experience), blinded to the clinical
information of the patients, manually delineated lesions based on sMRI
and DWI images for each patient. The masks were smoothed with a 3
mm full-width half maximum (FWHM) to remove jagged edges created
during the drawing (Rorden et al., 2012). Subsequently, the lesion
masks, DWI, and sMRI images were flipped from right to left for 33
patients with lesions on the right side. The abnormal values within the
lesion, which cause distortions during the segmentation and normali-
zation of the sMRI image, were replaced with normal values in the
contralesional homologous regions using clinicaltbx (https://www.
nitrc.org/plugins/mwiki/index.php/clinicaltbx:MainPage)
(Nachev
et al., 2008)based on Statistical Parametric Mapping (SPM). The cor-
rected sMRI images were then segmented into grey matter (GM), white
matter (WM), and cerebrospinal fluid (CSF) using diffeomorphic
anatomical registration through exponentiated lie algebra (DARTEL)
(Ashburner, 2007). For each patient, the segmented WM and GM
structural images and two lesion masks from sMRI and DWI images were
spatially normalized to Montreal Neurological Institute (MNI) space via
deformation fields derived from tissue segmentation of sMRI images
using the DARTEL algorithm. The union of two normalized masks was
calculated as the lesion map for each patient. The overlap of the lesion
maps for patients in the Stroke group was shown in Fig. 1.

To minimize mixing signal (and noise) components from the WM and
CSF regions due to partial volume effect and individual differences, we
create individual WM and CSF masks for subsequent rs-fMRI data ana-
lyses. Specifically, 95% probability masks of individual WM and CSF
obtained from segmentation of sMRI image were first normalized to MNI
space, and then intersected with WM and CSF template in Data Pro-
cessing & Analysis for Brain Imaging (DPABI) (Yan et al., 2016) and
further removed the lesion to obtain individual WM mask and CSF mask.

2.4. Preprocessing of rs-fMRI data

Preprocessing of rs-fMRI data was performed using the SPM12
toolbox (http://www.fil.ion.ucl.ac.uk/spm) and DPABI and included: 1)
The lesion side was set to the left by flipping the fMRI data from right to
left about the mid-sagittal line for 33 patients with lesions on the right
side in consistent with the previous processing of structural images; 2)
removing the first 10 volumes to allow the MR signal to reach equilib-
rium and to adapt participants to the scanning environment; 3) correc-
tion for intra-volume time delays between slices using Sinc interpolation
algorithm; 4) correction for inter-volume head motion using rigid-body
transformation; 5) spatial normalization to the MNI space via defor-
mation fields derived from tissue segmentation of sMRI images using
DARTEL algorithm and resampled to 3 × 3 × 3mm3; 6) spatial
smoothing was applied using a 6 mm FWHM isotropic Gaussian kernel.
Notably, ReHo and DC metrics were smoothed post-calculation as
described in section 2.6; 7) removal of linear trends; 8) regressing out
nuisance signals including 24-parameter head motion profiles (Friston
et al., 1996), the average time series extracted from individual WM mask
and CSF mask. We did not regress out the global signals as it is contro-
versial for rs-fMRI data (Murphy and Fox, 2017); 9) band-pass filtering
(0.01 - 0.08 Hz) except for ALFF; and 10) making gray matter mask for
all participants: the individual smoothed fMRI image was used to extract
the whole brain mask by the function ‘w_Automask’ in DPABI. The
intersection of all brain masks was further intersected with the
Anatomical Automatic Labeling (AAL) atlas with 8 subcortical regions
(thalamus and basal ganglia), the union of all subjects’ lesion masks and
WM (WM template in DPABI) removed to obtain gray matter mask for
following analyses. This process aims to exclude the non-gray matter
regions such as white matter and lesions from the analysis and focus only
on the gray matter regions. This exclusion is crucial because the pres-
ence of lesions can significantly alter local hemodynamics and neural
activity in stroke patients, potentially confounding the calculation of
functional metrics and the accuracy of relevant results. Although this
process might reduce the sensitivity to detect changes in areas imme-
diately surrounding the smaller lesions, it enhances the specificity of the
results by focusing on unaffected tissue. This trade-off is particularly
crucial in stroke studies, where the primary interest lies in under-
standing the broader impacts of stroke beyond the immediate lesioned
areas.

In the present study, six participants were excluded based on the
head movement criterion of maximal displacement > 3 mm, rotation >
◦
, or mean framewise displacement > 0.5, leaving 73 stroke patients
3
and 74 HC in the final analyses.

2.5. LAG correction

To correct for hemodynamic lags in stroke patients, the time series of

Fig. 1. The overlap mapping of lesions. Lesions were overlapped in the Stroke group involving a total of 73 patients. The color depicts the number of patients with
focal brain lesions at any given location. IL, ipsilesional hemisphere.

3 

L. Wang et al.

NeuroImage 303 (2024) 120920 

each voxel was shifted according to the hemodynamic lags calculated by
the time-shift analysis approach proposed in a previous study (Lv et al.,
2013) using the average time series of the gray matter mask as the
reference time serial. The shifted time series were then used for the
following analyses.

2.6. Functional metrics calculation

The rs-fMRI metrics, which have been commonly employed to un-
derstand the functional mechanisms in the normal and diseased brain,
were calculated at three different scales, i.e., local-scale, meso-scale, and
global-scale. Notably, each metric was calculated using the preprocessed
rs-fMRI data both with and without LAG correction.

2.6.1. Local-scale metrics

Different brain regions have their specialized functions. Therefore, it
is important to understand the functional role of these regions. In order
to understand the alterations of local neural activity, we calculated two
local metrics, including the amplitude of low-frequency fluctuation
(ALFF) and regional homogeneity (ReHo) for each participant.

ALFF measures the amplitude of low-frequency fluctuations in the
BOLD signal, while ReHo calculates the similarity of the time series of a
voxel with its nearest neighbors and reflects the local synchronization of
neural activity (Zang et al., 2004). The calculation of ALFF involved
transforming the time series of rs-fMRI data into the frequency domain
to obtain the power spectrum. The square root of the power spectrum
was then averaged over the low-frequency range (0.01–0.08 Hz) to
derive the ALFF value. For ReHo, Kendall’s coefficient of concordance
(KCC) was computed among the time series of a given voxel and its 26
nearest neighbors to assess local synchronization. The ALFF and ReHo
values were further divided by the individual whole-brain mean for
standardization. Notably, spatial smoothing with an FWHM of 6 mm was
performed after ReHo calculation to maintain consistency with previous
studies (Ge et al., 2024; Hu et al., 2024).

2.6.2. Meso-scale metrics

The functional roles of different brain regions are also related to their
connectivity pattern, as regions that are strongly connected tend to have
similar functions. One important aspect of the functional brain organi-
zation is the presence of functional networks, which comprise groups of
brain regions that work together to perform specific tasks. Meso-scale
metrics were defined as a range of scales situated between two ex-
tremes that reflect the neural activity at the network level. To access
how regions are related to each other within the special neural circuit,
seed-based functional connectivity (FC) was calculated for four func-
tional brain networks: default mode network (DMN, seed in posterior
cingulate/precuneus [0, -52, 27]), dorsal attention network (DAN, seed
in left/ipsilesional posterior intraparietal sulcus [-26, -66, 48] and right/
contralesional posterior intraparietal sulcus [26, -66, 48]), executive
control network (ECN, seed in dorsal medial prefrontal cortex [0, 24,
46]) and salience network (SN, seed in dorsal anterior cingulate [0, 21,
36]). These four networks are part of the large-scale intrinsic brain
networks that are involved in various cognitive processes and are not
primarily concerned with the processing of sensory information from
specific modalities. All the seeds were in Talairach space and taken from
previous studies (Raichle, 2011; Zhang and Raichle, 2010). To integrate
these seeds with our dataset, which was normalized to MNI space,
DPABI was employed to convert Talairach coordinates to MNI co-
ordinates accurately. This conversion allowed us to maintain the
anatomical specificity of our targeted regions while ensuring compati-
bility with our MNI-space data. Once the coordinates were converted,
the Pearson correlation coefficients were calculated between the aver-
aged time course of the spherical region of interest (ROI, radius = 6 mm)
centered at each seed and each time course of brain voxels, and then
converted to z-value using Fisher’s r-to-z transformation.

2.6.3. Global-scale metrics

The overall connectivity pattern within the brain can be represented
as a global network that integrates various information from the in-
teractions between regions within the same network and between
different networks, respectively. Binary degree centrality (DCb) mea-
sures the number of direct connections (edges) a node (brain region) has
with other nodes within a network, without considering the strength of
these connections. This metric is crucial because it reflects the raw
connectivity architecture, highlighting nodes that are critical for the
integration and transfer of information across the brain. Weighted de-
gree centrality (DCw), on the other hand, considers not only the pres-
ence of connections but also their strength, providing a richer, more
detailed picture of network connectivity. This metric is significant
because it quantifies the total connectivity strength of a node, offering
insights into the node’s influence and functional integration within the
network. DCw is essential for our understanding of how strong con-
nections contribute to overall brain function and how disruptions in
these connections might affect brain dynamics.

Therefore, to comprehensively characterize the overall connectivity
of a brain region with other regions in the functional brain network, DCb
and DCw were generated by voxel-based whole-brain correlation anal-
ysis on preprocessed resting-state fMRI data (Lv et al., 2019). The
threshold of DCb was set at p < 0.05, Bonferroni-corrected, resulting in a
correlation coefficient threshold of 0.32 (Lv et al., 2019). It should be
noted that only positive correlations were considered in the DC calcu-
lations. Finally, both the DCb and DCw maps were divided by the global
mean and then spatially smoothed with a smooth kernel of 6 mm for
subsequent analyses.

2.6.4. Stroke-specific metric

Previous studies have consistently reported the reductions in inter-
hemispheric connectivity of different brain circuits in stroke, which
suggest the decreased interhemispheric connectivity may be a reliable
marker for patients after stroke onset (Frías et al., 2018; Lee et al., 2018).
To measure the interhemispheric connectivity at a voxel
level,
voxel-mirrored homotopic connectivity (VMHC) (Anderson et al., 2011;
Zuo et al., 2010) was calculated by correlating the time course of each
voxel in one hemisphere with its corresponding homotopic voxel in the
other hemisphere, and then converted to z-value using Fisher’s r-to-z
transformation.

2.7. ICVR calculation

The rs-fMRI data were analyzed according to the procedures
described in previous studies (Liu et al., 2017; Ni et al., 2022) using
SPM12 including head motion correction, spatial normalization, spatial
smoothing with a 6 mm Gaussian kernel, linear detrending, and band-
pass filtering (0.02–0.04 Hz). A linear regression model was then built in
a voxel-wise manner with the average whole-brain time course as the
independent variable and the time course of each voxel as the dependent
variable, generating the regression coefficient as an iCVR index for each
voxel. It should be noted that in the condition for both iCVR and LAG
correction, after calculating the lag and correcting the reference time
series accordingly, we then used this corrected data to calculate iCVR.
This procedure ensures that the iCVR calculations are not confounded by
any uncorrected lag, providing a more accurate estimation of cerebro-
vascular responsiveness. The iCVR values were further divided by the
individual whole-brain mean to yield relative iCVR maps.

2.8. Statistical analysis

2.8.1. Resting-state pattern of different rs-fMRI metrics

We define the intrinsic pattern of certain metrics as the distribution
where the metrics is statistically significant under a group-level single-
sample t-test. One-sample t-tests were performed on ALFF, ReHo, FC,
(cid:0) 15
DCb, and DCw metrics in stroke patients, with a threshold of p < 10

4 

L. Wang et al.

NeuroImage 303 (2024) 120920 

(a more conservative threshold than the Bonferroni correction which
ensures robust control over false positives and enhances the reliability of
the results) in four conditions (Stroke pattern): no correction, iCVR
correction only, LAG correction only, both iCVR and LAG correction. On
the iCVR correction condition, the iCVR values were treated as the
covariates in the voxel-wise regression (Liu et al., 2017). One sample
t-test was also performed for each metric in the HC group using the same
threshold (HC pattern). For each metric, the Sørensen-Dice coefficients,
which calculate the ratio of the intersection with respect to the union of
each pair of masks, were calculated to estimate the degree of the overlap
between the HC pattern and the Stroke pattern in each condition.

2.8.2. Between-group differences in different rs-fMRI metrics

The between-group differences of ALFF, ReHo, FC, DCb, DCw, and
VMHC values were inferred by two-sample t-tests in four conditions: no
correction, iCVR, LAG, both iCVR and LAG correction. Similarly, the
iCVR values of the two groups were treated as the covariates of no in-
terest in the voxel-wise regression in three correction conditions. The
resultant t-maps were corrected using False Discovery Rate (FDR, q <
0.05) for multiple comparisons. The number of voxels showing signifi-
cant between-group differences was counted to determine the sensitivity
of each condition.

2.9. Validation

The external validation dataset including 29 stroke and 18 healthy
participants was recruited from July 2020 to April 2022 in Affiliated
Hangzhou First People’s Hospital, Zhejiang University School of Medi-
cine. Notably, patients with anterior circulation occlusion exhibited
large, widely distributed lesions, as depicted in Fig. S1. The similar
process was applied to the data above to verify the results of the intrinsic
patterns and between-group differences in different rs-fMRI metrics.

3. Results

3.1. Demographics and clinical characteristics

Demographic and clinical information for the final 73 stroke patients
and (59.45 ± 6.70 years, 28 females, 4.97 ± 3.40 days after stroke
onset) 74 healthy controls (HC, 57.43 ± 6.83 years, 31 females) were
presented in Table 1. There were no significant differences in gender (p
= 0.66), age (p = 0.072), and Mini-Mental State Examination (MMSE, p
= 0.27), while significant differences were observed in ADL scores (p <
0.001) between the two groups.

3.2. Resting-state pattern of different rs-fMRI metrics

Stroke patterns in four correction strategies of BOLD signals, i.e.,
without correction, iCVR-only correction, LAG-only correction, both
iCVR and LAG correction, were similar to that of the HC pattern. After
calculating the Dice coefficient, the Stroke pattern with correction for
both iCVR and LAG showed the highest degree of overlap with the HC
pattern (0.630–0.956), while the Stroke pattern without correction re-
flected the lowest degree of overlap (0.463–0.927, Figs. 2 and 3,
Table 2). Especially, at the local scale, the pattern of ALFF in stroke
patients was mostly affected by the iCVR rather than hemodynamic lag.
Whereas the intrinsic pattern of ReHo in stroke was mainly influenced
by blood flow lag rather than iCVR. At the meso-scale, the intrinsic
pattern of four subnetworks in stroke patients were primarily affected by
LAG rather than iCVR. Additionally, at the global-scale, the intrinsic
pattern of two DC metrics in stroke appears to be primarily influenced by
iCVR rather than LAG.

3.3. Between-group differences in different rs-fMRI metrics

As shown in Figs. 4 and 5 and Supplementary Table S1, the differ-
ences in each functional metric between Stroke and HC groups exhibited
similar pattern in four conditions: no correction, iCVR-only correction.
LAG-only correction, and both iCVR and LAG correction (q < 0.05, FDR
corrected). The number of voxels, which showed significant between-
group differences, was further counted as the sensitivity for each
correction condition. Compared to the metrics calculated without
correction of BOLD signals, the ReHo and four FC metrics obtained after
correction for both iCVR and LAG showed higher sensitivity in the
between-group differences, while the ALFF and DC exhibited lower
sensitivity in the between-group differences in the corrected condition.
Specifically, at the local-scale, the between-group differences in cor-
rected ALFF values had -22% lower sensitivity (4671 voxels) compared
to the uncorrected values (5998 voxels), while the corrected ReHo
values showed 47% higher sensitivity (12,170 voxels) compared to the
uncorrected values (8311 voxels). At the meso-scale, the corrected FC
values showed significantly higher sensitivity in detecting between-
group differences: DMN increased by 173% (7923 voxels vs. 2903
voxels), ECN by 467% (3055 voxels vs. 539 voxels), and SN by 104%
(1745 voxels vs. 854 voxels). For DANi, there was a shift from no sig-
nificant voxels in the uncorrected condition to 42 significant voxels in
the corrected condition. At the global-scale, the corrected DC values had
lower sensitivity, with DCb showing -65% lower sensitivity (655 voxels
vs. 1848 voxels) and DCw showing -50% lower sensitivity (1111 voxels
vs. 2238 voxels). In most of the cases, the same clusters identified in the
uncorrected analysis become more spatially extensive after corrections.
In other cases, such as ReHo, DAN and SN, the corrections allow for the
identification of new clusters of significant differences that were not
detectable in the uncorrected analysis.

As shown in Fig. 2, for each of rs-fMRI metrics, the distribution of all

3.4. Validation

Table 1
Demographics and clinical characteristics.

Stroke
(n = 73)

HC
(n = 74)

Statistical
value

Gender (M/F)
Age (years)
Onset time
(days)
MMSE
ADL

NIHSS

45/28
59.45 ± 6.70
4.97 ± 3.40

29.63 ± 0.95
82.81 ±
16.81
2.51 ± 2.19

43/31
57.43 ± 6.83
–

29.42 ± 1.32
100.00 ±
0.00
–

0.19
1.81
–

1.11
-8.74

–

p value

0.66a
0.07b
–

0.27b
< 0.01b

–

Stroke, stroke patients; HC, healthy controls; M, male; F, female; MMSE, Mini-
Mental State Examination; ADL, Activity Daily Living Scale; NIHSS: National
Institutes of Health Stroke Scale.

a The p-value was obtained by a chi-square test.
b The p-values were obtained by two-sample t-tests.

Our validation analyses, as reported in Supplementary Figs. S1 and S2,
and Tables S2 and S3 demonstrated that the resting-state fMRI metrics
post-correction for both iCVR and LAG generally replicated the resting-
state pattern and between-group differences observed in the main data-
set. That is, after correcting for both iCVR and LAG in stroke patients, the
Stroke pattern of each metric showed highest degree of overlap with the
HC pattern, and the sensitivity of the between-group comparisons for
most metrics has been enhanced. Furthermore, based on the effects of
iCVR and LAG on various metrics, we consistently conclude that ALFF is
particularly vulnerable to iCVR influences, whereas ReHo and FC were
mostly influenced by LAG effects. However, discrepancies exist in global
metrics between our main and validation datasets. Specifically, DCb and
DCw in the main dataset is more susceptible to the influence of iCVR and
exhibited lower sensitivity in the between-group differences, while in the
validation set, it is more sensitive to the effects of LAG and showed higher
sensitivity in the between-group differences.

5 

L. Wang et al.

NeuroImage 303 (2024) 120920 

Fig. 2. The intrinsic patterns of all metrics on the uncorrected and corrected (iCVR or LAG) conditions in stroke and HC groups. In these maps, the color intensity
signifies the t-values obtained from a single-sample t-test. ALFF, the amplitude of low frequency fluctuation; ReHo, regional homogeneity; DMN, default mode
network; DANi, ipsilesional dorsal attention network; DANc, contralesional dorsal attention network; ECN, executive control network; SN, salience network; DCb,
binary degree centrality; DCw, weighted degree centrality; iCVR, intrinsic cerebrovascular reactivity; HC, healthy controls; LAG, hemodynamic lags; IL, ipsile-
sional hemisphere.

4. Discussion

In this study, we systematically investigated how the correction of
the LAG and/or iCVR of the BOLD signal would affect resting-state

functional metrics at different scales in ischemic stroke. We found that
the Stroke pattern of all functional metrics using different correction
strategies resembled the HC pattern. The highest overlap was observed
in the Stroke pattern with correction for both LAG and iCVR, while the

6 

L. Wang et al.

NeuroImage 303 (2024) 120920 

At the local scale, as the LAG correction by shifting the time serials
failed to affect the amplitude of the BOLD signal, the intrinsic pattern of
ALFF in stroke patients was primarily influenced by iCVR, indicating the
significant role of cerebrovascular abnormalities in shaping local neural
activity. Altering the lag of the time series, which primarily adjusts the
timing of the BOLD signal to account for delays in hemodynamic
response, does not affect the amplitude of the signal. This distinction is
crucial for understanding why ALFF is not directly impacted by LAG
correction. Since ALFF focuses on the amplitude rather than the timing
of these fluctuations, adjustments made solely for temporal alignment
(LAG correction) would not alter the calculated power of the signal. And
the impaired cerebrovascular function, particularly the regulation of
blood flow, was identified as a key factor contributing to the observed
changes in ALFF. Previous studies have shown that these non-neuronal
fluctuations account for a significant portion (approximately 30%) of
the variance in gray matter BOLD signal fluctuations (Frederick et al.,
2012). Among these fluctuations, the CVR explained up to approxi-
mately 16% of the variance in the significant voxels (Wise et al., 2004).
A moderate relationship has also been reported between the hemody-
namic impairment and the slow fluctuating BOLD signal, especially the
ALFF (De Vis et al., 2018; Golestani et al., 2016a; Ni et al., 2022). All
these findings together highlighted the necessity of excluding cerebro-
vascular factors, such as iCVR, when using the ALFF to assess the fluc-
tuations of neural activity at the local scale. As compared to healthy
controls, stroke patients exhibited decreased ALFF values in several
brain regions. The between-group differences in ALFF after correcting
for both iCVR and LAG had less significant voxels than that without
correction of BOLD signals, albeit showing similar pattern. This finding
further indicated the confounding roles of the changes in BOLD signal
due to the cerebrovascular impairments in stroke patients. Therefore,
understanding and accounting for cerebrovascular factors are crucial for
accurately interpreting ALFF alterations in stroke patients.

Whereas, unlike ALFF, the influence of hemodynamic lags on ReHo
was more pronounced, suggesting that delayed hemodynamic responses
can disrupt the synchronization of neural activity at the local scale in
stroke patients. Previous studies have shown that hemodynamic lags
would affect the BOLD synchronization (i.e., FC) between remote brain
regions (Khalil et al., 2023; Siegel et al., 2016b). ReHo, which measures
the consistency of the time series of a voxel with its 26 nearest neighbors
(Zang et al., 2004), can be heavily influenced by delays in the hemo-
dynamic response introduced by vascular disruptions from stroke. We
found that even calculating the synchronization among neighboring
voxels, correcting for hemodynamic lags could still
influence the
intrinsic pattern and the between-group differences of ReHo, suggesting
the inconsistency in degrees of hemodynamic lags among local voxels.
Our findings indicated the presence of the voxel-specific characteristics
in hemodynamic lags, which further enriched our understanding of
temporal features of BOLD signals. Furthermore, the between-group
differences in ReHo values obtained after LAG-only correction or both
iCVR and LAG correction had more significant regions when compared
to the uncorrected condition. Our results imply that the correction for
LAG in the BOLD signal could improve the sensitivity to detect the al-
terations of ReHo in stroke patients, possibly by mitigating the effects of
blood flow delays on regional homogeneity. By correcting for these
delays, we align the timing of neuronal activity more accurately across
affected regions, which likely results in a more coherent local signal.
This correction makes the synchronization within a voxel’s neighbor-
hood appear stronger once the confounding influence of delayed he-
modynamic responses is minimized.

At the meso-scale, LAG played a significant role in shaping the
functional connectivity metrics in stroke patients. As would be expected,
the intrinsic pattern of four subnetworks: default mode network (DMN),
dorsal attention network (DAN), executive control network (ECN), and
salience network (SN), in stroke patients, were primarily influenced by
hemodynamic lags rather than iCVR. Hemodynamic lags systematically
influence the measurements of FC (Khalil et al., 2023; Siegel et al.,

7 

Fig. 3. The radar plot of the Dice coefficients of the intrinsic pattern for the
metrics of stroke and the intrinsic pattern for HC. The Dice coefficients were
calculated to evaluate the similarity between the pattern observed in the un-
corrected and corrected (iCVR or LAG) conditions and the HC pattern for all the
metrics. ALFF, the amplitude of low frequency fluctuation; ReHo, regional
homogeneity; DMN, default mode network; DANi, ipsilesional dorsal attention
network; DANc, contralesional dorsal attention network; ECN, executive con-
trol network; SN, salience network; DCb, binary degree centrality; DCw,
weighted degree centrality; iCVR, intrinsic cerebrovascular reactivity; LAG,
hemodynamic lags.

Table 2
The Dice coefficients of four correction strategies of BOLD signals compared
with the HC pattern.

scale

metrics

Stroke

local-

scale
meso-
scale

global-
scale

ALFF
ReHo
DMN
DANi
DANc
ECN
SN
DCb
DCw

0.733
0.834
0.927
0.525
0.797
0.852
0.663
0.506
0.463

Stroke
(iCVR)

0.789
0.858
0.931
0.522
0.800
0.855
0.671
0.654
0.617

Stroke
(LAG)

0.730
0.882
0.954
0.621
0.856
0.896
0.770
0.490
0.444

Stroke
(iCVR+LAG)

0.794
0.908
0.956
0.624
0.861
0.904
0.780
0.656
0.630

ALFF, the amplitude of low frequency fluctuation; ReHo, regional homogeneity;
DMN, default mode network; DANi, ipsilesional dorsal attention network; DANc,
contralesional dorsal attention network; ECN, executive control network; SN,
salience network; DCb, binary degree centrality; DCw, weighted degree cen-
trality; iCVR, intrinsic cerebrovascular reactivity; HC, healthy control; LAG,
hemodynamic lags.

pattern without correction showed the lowest overlap. Further, differ-
ences in each functional metric between the Stroke and HC groups
exhibited similar pattern with both LAG and iCVR correction and
without correction. Most functional metrics after correction showed
higher sensitivity in detecting between-group differences than that
without correction. In this study, we included two independent datasets.
The first dataset features smaller lesions that are more concentrated,
primarily located near the subcortical basal ganglia. The second dataset
(validation set) presents with larger lesions that are more widely
distributed, encompassing almost the entire hemisphere. However, the
intrinsic pattern and the between-group differences were largely
resembled in both datasets. Overall, these findings emphasize the ne-
cessity of considering iCVR and LAG effects to investigate stroke-related
functional alterations and highlight the significance of correction stra-
tegies for accurately interpreting the findings in the rs-fMRI study of
ischemic stroke.

L. Wang et al.

NeuroImage 303 (2024) 120920 

Fig. 4. The between-group differences in different rs-fMRI metrics in four conditions: no correction, iCVR, LAG, both iCVR and LAG correction (q < 0.05, FDR
corrected). In these comparative visualizations, the color intensity corresponds to the t-values derived from a two-sample t-test. ALFF, the amplitude of low frequency
fluctuation; ReHo, regional homogeneity; DMN, default mode network; DANi, ipsilesional dorsal attention network; DANc, contralesional dorsal attention network;
ECN, executive control network; SN, salience network; DCb, binary degree centrality; DCw, weighted degree centrality; VMHC, voxel-mirrored homotopic con-
nectivity; iCVR, intrinsic cerebrovascular reactivity; HC, healthy controls; LAG, hemodynamic lags; IL, ipsilesional hemisphere.

2016b). Specifically, delayed blood flow response changes contributed
to disrupted functional connectivity within these subnetworks, reflect-
ing the consequences of impaired cerebrovascular dynamics in stroke
patients (Siegel et al., 2017). Whereas the influence of iCVR on the

intrinsic patterns of these functional networks in stroke patients was
relatively less significant. As iCVR mainly reflects the ability of blood
vessels to dilate and respond to neural activity, our results suggested that
it may not be the primary driver of connectivity alterations in stroke

8 

L. Wang et al.

NeuroImage 303 (2024) 120920 

patients. These findings provide valuable insights into the complex
interplay between cerebrovascular dynamics and functional connectiv-
ity in stroke patients at the meso-scale. In addition, the between-group
differences in FC values obtained after iCVR and LAG correction
showed higher sensitivity than that without correction. These finding
highlights that incorporating iCVR and LAG correction of BOLD signal
could enhance the ability to capture alterations in functional networks
in stroke patients.

Especially, as a measure characterizing the functional connectivity
between homotopic regions in two hemispheres, VMHC is commonly
used to evaluate stroke-related deficits in interhemispheric connectivity
(Hoptman et al., 2012). Altered VMHC values may indicate disruptions
in interhemispheric communication, which can be attributed to
stroke-induced brain damage or compensatory mechanisms (Tang et al.,
2016). The findings from VMHC analysis can complement and provide
additional insights compared to traditional functional connectivity re-
sults, such as changes in seed-based or network-based connectivity
(Hoptman et al., 2012). Similar to the FC, the sensitivity of the
stroke-specific metric, VMHC, increased after the correction for iCVR
and hemodynamic lags. The finding further implies that accounting for
iCVR and LAG in the connectivity analyses enhances the ability to detect
the specific alterations of functional networks related to stroke.

At the global scale, there are some differences in the sensitivity of
functional metrics between our main and validation datasets. Specif-
ically, degree centrality in the main dataset is more susceptible to the
influence of iCVR, while in the validation set, it is more sensitive to the
effects of LAG. These differences in sensitivity can be attributed to
several factors related to stroke heterogeneity, particularly lesion loca-
tion and size (Pan et al., 2006). The main dataset primarily includes
patients with small lesions located in the subcortical basal ganglia and
surrounding white matter. In contrast, and the validation dataset com-
prises patients with anterior circulation strokes involving larger lesions
(see Figs. 1 and S1). In the main dataset, lesions are concentrated in the
subcortical basal ganglia and its adjacent white matter. As critical hubs,
damage to the basal ganglia can lead to cerebral blood flow reorgani-
zation. This reorganization is largely a compensatory response triggered
by the cerebral autoregulation mechanisms striving to maintain
adequate blood supply to vital functional areas (Krishnamurthy et al.,
2021). This reorganization may cause changes in iCVR across extensive
brain regions as the entire brain attempts to reallocate resources to
support the functionality around the damaged areas. However, under
these conditions, the overall brain LAG may not be significantly affected,
hence making iCVR more impactful in this dataset. Widespread lesions,
on the other hand, may involve multiple key neural pathways and brain
processing centers. This extensive damage can result in the obstruction
or destruction of numerous signal transmission pathways. With the
brain’s autoregulation failing to sustain blood supply to essential func-
tional areas, there is an inevitable increase in the overall delay in neural
transmission across the brain network. This disruption of normal func-
tional connections compels the brain network to adopt longer or more
intricate alternative paths for transmitting information, consequently
escalating LAG. Thus, the validation dataset is more susceptible to the
effects of LAG. Therefore, for assessing such global-scale metrics in
stroke patients, future studies are required to clarify to what extent the
specific factors, such as lesion size, may affect the intrinsic pattern and
the between-group differences of these metrics, and to gain a compre-
hensive understanding of the implications and interpretations of these
metrics.

In our study, we observed an interesting dichotomy: the Dice coef-
ficient, indicating similarity between the resting state pattern of stroke
patients and healthy controls, was higher after correction for both LAG
and iCVR. This finding suggests that the corrections help in aligning the
neural pattern of patients more closely with those of the control group,
potentially unmasking underlying similarities that are obscured by
vascular irregularities inherent in the patient group. Whereas the same
corrections for both LAG and iCVR lead to increased sensitivity in

9 

Fig. 5. Overlap of inter-group differences in various rs-fMRI metrics under
three conditions (correction for iCVR, LAG, and both iCVR and LAG) compared
to the uncorrected scenario. ALFF, the amplitude of low frequency fluctuation;
ReHo, regional homogeneity; DMN, default mode network; DANi, ipsilesional
dorsal attention network; DANc, contralesional dorsal attention network; ECN,
executive control network; SN, salience network; DCb, binary degree centrality;
DCw, weighted degree centrality; VMHC, voxel-mirrored homotopic connec-
tivity; iCVR, intrinsic cerebrovascular reactivity; HC, healthy controls; LAG,
hemodynamic lags; IL, ipsilesional hemisphere.

L. Wang et al.

NeuroImage 303 (2024) 120920 

detecting between-group differences, particularly for ReHo and FC
metrics. This enhanced sensitivity suggests that while the corrections
align the overall pattern more closely, they also amplify the specific
neural discrepancies that differentiate the groups. This could be due to
the fact that once vascular confounds are accounted for, the true neural
deficits or alterations associated with stroke become more pronounced
and detectable. This dichotomy can be attributed to differences in sta-
tistical testing methods. One-sample t-tests for functional metrics, used
to estimate the degree of the overlap between the HC pattern and the
Stroke pattern, reveal deviations within a group by comparing regional
metrics
inter-group comparisons.
Conversely, two-sample t-tests, used to assess the sensitivity, directly
compare metrics between groups (e.g., stroke vs. HC), essential for
identifying unique characteristics. Thus, areas significant in single-
sample analyses within the patient group may not show significant
differences when compared directly to controls, explaining discrep-
ancies between analysis methods. Furthermore, the increase in simi-
larity and sensitivity may indicate two sides of the same coin: enhanced
detection accuracy. On one hand, the correction aligns the overall
functional architecture between groups, enhancing pattern similarity.
On the other hand, it heightens our ability to pinpoint where exactly
these groups diverge on a functional level.

to a baseline, without direct

Collectively, to better guide researchers in applying these correc-
tions, we provided which correction might be most appropriate for each
metric (Table S4). Metrics that are influenced by the amplitude or
strength of BOLD signals, such as ALFF, benefit more from iCVR
correction. This type of correction is crucial for compensating for indi-
vidual variations in vascular response, which can affect the amplitude of
BOLD signals and, consequently, the interpretation of neural activity
levels. ICVR correction is especially important in populations with po-
tential vascular pathology or in aging studies where vascular health may
vary significantly among participants (Damluji et al., 2021). Metrics that
are particularly sensitive to temporal synchronization within the brain,
such as ReHo and FC, show significant improvement after LAG correc-
tion. This correction is essential for metrics where the timing of neural
activity is crucial, as it adjusts for delays in the hemodynamic response
that can mask true neural synchrony. Thus, LAG correction is particu-
larly pertinent for studies focusing on dynamic connectivity or temporal
consistency of neural activities across different brain regions (Hutchison
et al., 2013). Furthermore, the decision to implement these corrections
should also consider the pathological context of the study population,
such as stroke patients, where degree centrality at the whole-brain level
may be influenced by both iCVR and LAG. The variability in sensitivity
to these corrections can be attributed to several factors inherent to
stroke heterogeneity, particularly the location and size of lesions. In
such scenarios, it might be necessary to apply both corrections to
accurately distinguish neural contributions from vascular artifacts in the
observed fMRI signals, or alternatively, tailor the analysis to specific
case requirements. We recommend that future studies explicitly test the
impact of these corrections in a methodologically systematic manner to
establish clearer guidelines for their application across different types of
functional MRI metrics.

Despite the valuable insights provided by this study, several limita-
tions should be acknowledged. Firstly, the relatively small sample size,
the exclusion of patients with severe strokes, and the lack of quantitative
assessment of small vessel disease may limit the generalizability of the
findings. A larger and more diverse sample, accompanied by compre-
hensive clinical evaluations, would provide a stronger foundation for
drawing conclusions about the impact of iCVR and LAG on neuro-
imaging metrics. Secondly, given the particular nature of our study
involving stroke patients and the prolonged MRI scanning sessions, we
chose not to employ breath-holding or invasive methods to assess CVR,
nor did we use additional equipment to monitor CO2 during scans. This
decision was made to ensure the safety and comfort of our patients. We
acknowledged that calculating “intrinsic” CVR using rs-fMRI data, by
leveraging the natural variation in respiration over time as an intrinsic

vasoactive stimulus, could not represent the gold standard for measuring
CVR, which typically involves a hypercapnic challenge. Although this
approach offers safety and practicality in clinical settings, the variability
in spatial correlation with traditional CVR measures, which ranged from
r = 0.32 to 0.85, suggests there may be limitations in the precision and
reliability of the iCVR in certain pathological conditions (Liu et al.,
2017). These considerations highlight the trade-offs involved in adapt-
ing neuroimaging techniques to the specific needs and conditions of the
patients and underscore the need for ongoing evaluation of methodo-
logical choices in CVR assessment. Moving forward, we plan to incor-
porate more established methods for CVR assessment in future studies
where feasible and ethically justifiable, enhancing the robustness and
applicability of our findings. Finally, the study primarily relied on
cross-sectional data, limiting the ability to assess temporal dynamics and
causality. Longitudinal studies that follow stroke patients over time
would provide valuable insights into the changes in CVR, LAG, and
neuroimaging metrics and their relationship to functional recovery and
clinical outcomes.

5. Conclusions

Our findings suggest that intrinsic CVR and hemodynamic lag have
varying impacts on rs-fMRI metrics at different scales. Considering these
effects is crucial for understanding the brain functional changes in stroke
patients. Moreover, applying correction strategies, particularly both
iCVR and LAG correction, enhances the similarity of Stroke pattern to
HC pattern and influences the sensitivity of different rs-fMRI metrics at
various scales, highlighting the importance of accounting for iCVR and
LAG effects in stroke-related functional alterations.

CRediT authorship contribution statement

Luoyu Wang: Writing – review & editing, Writing – original draft,
Visualization, Validation, Software, Methodology, Investigation, Formal
analysis. Xiumei Wu: Writing – review & editing, Investigation, Data
curation. Jinyi Song: Writing – review & editing, Investigation. Yanhui
Fu: Investigation, Data curation. Zhenqiang Ma: Investigation, Data
curation. Xiaoyan Wu: Investigation, Data curation. Yiying Wang:
Project administration, Investigation. Yulin Song: Resources, Project
administration. Fenyang Chen: Validation, Investigation. Zhongxiang
Ding: Supervision, Resources, Data curation. Yating Lv: Writing – re-
view & editing, Visualization, Supervision, Project administration, Data
curation, Conceptualization.

Declaration of competing interest

The authors declare no financial and other conflict of interest.

Funding

This work was supported by grants from the Zhejiang Provincial
Natural Science Foundation of China (no. LGJ22H180001), Zhejiang
Medical and Health Science and Technology Project (no. 2021KY249),
National Key R&D Program of China (no. 2017YFC1310000) and Sci-
ence and Technology Innovation 2030- “Brain Science and Brain-like
Research” Major Project (2022ZD0210800).

Author contributions

YL and ZD: work on concept or design and make important revisions
to the paper. LW: draft paper and data processing. XMW, JS: organize
data. YF, ZM, XYW, YW, YS: collect data. FC: draw the lesions. All au-
thors contributed to the article and approved the final paper for
publication.

10 

L. Wang et al.

Ethics statement

This study was authorized by the Ethics Committee of the Center for
Cognition and Brain Disorders, Hangzhou Normal University. All human
procedures were followed in accordance with the Declaration of Hel-
sinki and all participants provided written informed consent.

Supplementary materials

Supplementary material associated with this article can be found, in

the online version, at doi:10.1016/j.neuroimage.2024.120920.

Data availability

Data will be made available on request.

References

Amemiya, S., Kunimatsu, A., Saito, N., Ohtomo, K., 2014. Cerebral hemodynamic

impairment: assessment with resting-state functional MR imaging. Radiology 270,
548–555. https://doi.org/10.1148/radiol.13130982.

Amemiya, S., Kunimatsu, A., Saito, N., Ohtomo, K., 2012. Impaired hemodynamic

response in the ischemic brain assessed with BOLD fMRI. Neuroimage 61, 579–590.
https://doi.org/10.1016/j.neuroimage.2012.04.001.

Anderson, J.S., Druzgal, T.J., Froehlich, A., DuBray, M.B., Lange, N., Alexander, A.L.,

Abildskov, T., Nielsen, J.A., Cariello, A.N., Cooperrider, J.R., Bigler, E.D.,
Lainhart, J.E., 2011. Decreased interhemispheric functional connectivity in autism.
Cerebr. Cort. (New York, N.Y. : 1991) 21, 1134–1146. https://doi.org/10.1093/
cercor/bhq190.

Ashburner, J., 2007. A fast diffeomorphic image registration algorithm. Neuroimage 38,

95–113. https://doi.org/10.1016/j.neuroimage.2007.07.007.

Bauer, A.Q., Kraft, A.W., Wright, P.W., Snyder, A.Z., Lee, J.M., Culver, J.P., 2014. Optical
imaging of disrupted functional connectivity following ischemic stroke in mice.
Neuroimage 99, 388–401. https://doi.org/10.1016/j.neuroimage.2014.05.051.
Blicher, J.U., Stagg, C.J., O’Shea, J., Østergaard, L., MacIntosh, B.J., JohansenBerg, H.,
Jezzard, P., Donahue, M.J., 2012. Visualization of altered neurovascular coupling in
chronic stroke patients using multimodal functional MRI. J. Cereb. Blood Flow
Metab. 32, 2044–2054. https://doi.org/10.1038/jcbfm.2012.105.

Bonakdarpour, B., Parrish, T.B., Thompson, C.K., 2007. Hemodynamic response function

in patients with stroke-induced aphasia: implications for fMRI data analysis.
Neuroimage 36, 322–331. https://doi.org/10.1016/j.neuroimage.2007.02.035.
Braban, A., Leech, R., Murphy, K., Geranmayeh, F., 2023. Cerebrovascular Reactivity Has

Negligible Contribution to Hemodynamic Lag After Stroke: Implications for
Functional Magnetic Resonance Imaging Studies. Stroke 54, 1066–1077. https://doi.
org/10.1161/STROKEAHA.122.041880.

Bright, M.G., Murphy, K., 2013. Reliable quantification of BOLD fMRI cerebrovascular

reactivity despite poor breath-hold performance. Neuroimage 83, 559–568.
Brodtmann, A., Khlif, M.S., Bird, L.J., Cumming, T., Werden, E., 2021. Hippocampal
volume and amyloid PET status three years after ischemic stroke: A pilot study.
J. Alzheim. Dis. 80, 527–532. https://doi.org/10.3233/JAD-201525.

Buckner, R.L., Krienen, F.M., Yeo, B.T.T., 2013. Opportunities and limitations of intrinsic
functional connectivity MRI. Nat. Neurosci. 16, 832–837. https://doi.org/10.1038/
nn.3423.

Campbell, B.C.V., Khatri, P., 2020. Stroke. Lancet 396, 129–142. https://doi.org/

10.1016/S0140-6736(20)31179-X.

Carusone, L.M., Srinivasan, J., Gitelman, D.R., Mesulam, M.M., Parrish, T.B., 2002.
Hemodynamic response changes in cerebrovascular disease: implications for
functional MR imaging. Am. J. Neuroradiol. 23, 1222–1228.

Chen, B., Xu, T., Zhou, C., Wang, L., Yang, N., Wang, Z., Dong, H.M., Yang, Z., Zang, Y.F.,
Zuo, X.N., Weng, X.C., 2015. Individual variability and test-retest reliability revealed
by ten rep eated resting-state brain scans over one month. PloS one 10, e0144963.
https://doi.org/10.1371/journal.pone.0144963.

Chi, N.F., Ku, H.L., Chen, D.Y.T., Tseng, Y.C., Chen, C.J., Lin, Y.C., Hsieh, Y.C., Chan, L.,
Chiou, H.Y., Hsu, C.Y., Hu, C.J., 2018. Cerebral Motor Functional Connectivity at the
Acute Stage: An Outcome Predictor of Ischemic Stroke. Sci. Rep. 8, 16803. https://
doi.org/10.1038/s41598-018-35192-y.

Christen, T., Jahanian, H., Ni, W.W., Qiu, D., Moseley, M.E., Zaharchuk, G., 2015.

Noncontrast mapping of arterial delay and functional connectivity using resting-
state functional MRI: a study in Moyamoya patients. J. Magn. Reson. Imaging 41,
424–430. https://doi.org/10.1002/jmri.24558.

Cohen, A.L., Ferguson, M.A., Fox, M.D., 2021. Lesion network mapping predicts post-
stroke behavioural deficits and improves localization. Brain 144 (4), e35. https://
doi.org/10.1093/brain/awab002.

Collaborators, G.B.D.S., 2019. Global, regional, and national burden of stroke, 1990-
2016: a systematic analysis for the Global Burden of Disease Study 2016. Lancet
Neurol.. 18, 439–458. https://doi.org/10.1016/S1474-4422(19)30034-1.

Damluji, A.A., Chung, S.E., Xue, Q.L., Hasan, R.K., Moscucci, M., Forman, D.E., Bandeen-
Roche, K., Batchelor, W., Walston, J.D., Resar, J.R., Gerstenblith, G., 2021. Frailty
and cardiovascular outcomes in the National Health and Aging Trends Study. Eur.
Heart J. 42 (37), 3856–3865.

NeuroImage 303 (2024) 120920 

D’Esposito, M., Deouell, L.Y., Gazzaley, A., 2003. Alterations in the BOLD fMRI signal
with ageing and disease: a challenge for neuroimaging. Nat. Rev. Neurosci. 4,
863–872. https://doi.org/10.1038/nrn1246.

De Vis, J.B., Bhogal, A.A., Hendrikse, J., Petersen, E.T., Siero, J.C.W., 2018. Effect sizes
of BOLD CVR, resting-state signal fluctuations and time delay measures for the
assessment of hemodynamic impairment in carotid occlusion patients. Neuroimage
179, 530–539. https://doi.org/10.1016/j.neuroimage.2018.06.017.

Ekker, M.S., Boot, E.M., Singhal, A.B., Tan, K.S., Debette, S., Tuladhar, A.M., de Leeuw, F.
E., 2018. Epidemiology, aetiology, and management of ischaemic stroke in young a
dults. Lancet Neurol. 17, 790–801. https://doi.org/10.1016/S1474-4422(18)30233-
3.

Fan, Y., Wang, L., Jiang, H., Fu, Y., Ma, Z., Wu, X., Wang, Y., Song, Y., Fan, F., Lv, Y.,
2023. Depression circuit adaptation in post-stroke depression. J. Affect. Disord. 336,
52–63. https://doi.org/10.1016/j.jad.2023.05.016.

Feigin, V.L., Brainin, M., Norrving, B., Martins, S., Sacco, R.L., Hacke, W., Fisher, M.,

Pandian, J., Lindsay, P., 2022. World Stroke Organization (WSO): Global Stroke Fact
Sheet 2022. Int. J. Stroke 17, 18–29. https://doi.org/10.1177/
17474930211065917.

Fox, M.D., Raichle, M.E., 2007. Spontaneous fluctuations in brain activity observed with
functional magnetic resonance imaging. Nat. Rev. Neurosci. 8, 700–711. https://doi.
org/10.1038/nrn2201.

Frederick, B.d., Nickerson, L.D., Tong, Y., 2012. Physiological denoising of BOLD fMRI
data using Regressor Interpolation at Progressive Time Delays (RIPTiDe) processing
of concurrent fMRI and near-infrared spectroscopy (NIRS). Neuroimage 60,
1913–1923. https://doi.org/10.1016/j.neuroimage.2012.01.140.

Frías, I., Starrs, F., Gisiger, T., Minuk, J., Thiel, A., Paquette, C., 2018. Interhemispheric

connectivity of primary sensory cortex is associated with motor impairment after
stroke. Sci. Rep. 8, 12601. https://doi.org/10.1038/s41598-018-29751-6.

Friston, K.J., Williams, S., Howard, R., Frackowiak, R.S., Turner, R., 1996. Movement-
related effects in fMRI time-series. Magn. Reson. Med. 35, 346–355. https://doi.org/
10.1002/mrm.1910350312.

Gao, J., Yang, C., Li, Q., Chen, L., Jiang, Y., Liu, S., Zhang, J., Liu, G., Chen, J., 2021.

Hemispheric difference of regional brain function exists in patients with acute stroke
in different cerebral hemispheres: a resting-state fMRI study. Front. Aging Neurosci.
13, 691518. https://doi.org/10.3389/fnagi.2021.691518.

Ge, X., Wang, L., Yan, J., Pan, L., Ye, H., Zhu, X., Feng, Q., Chen, B., Du, Q., Yu, W.,

Ding, Z., 2024. Altered brain function in classical trigeminal neuralgia patients:
ALFF, ReHo, and DC static-and dynamic-frequency study. Cerebr. Cort. 34 (1),
bhad455.

Geranmayeh, F., Wise, R.J., Leech, R., Murphy, K., 2015. Measuring vascular reactivity
with breath-holds after stroke: A method to aid interpretation of group-level BOLD
signal changes in longitudinal f MRI studies. Hum. Brain Mapp. 36 (5), 1755–1771.

Golestani, A.M., Kwinta, J.B., Strother, S.C., Khatamian, Y.B., Chen, J.J., 2016a. The
association between cerebrovascular reactivity and resting-state fMRI functional
connectivity in healthy adults: The influence of basal carbon dioxide. Neuroimage
132, 301–313. https://doi.org/10.1016/j.neuroimage.2016.02.051.

Golestani, A.M., Wei, L.L., Chen, J.J., 2016b. Quantitative mapping of cerebrovascular
reactivity using resting-state BOLD fMRI: Validation in healthy adults. Neuroimage
138, 147–163. https://doi.org/10.1016/j.neuroimage.2016.05.025.

Grefkes, C., Fink, G.R., 2014. Connectivity-based approaches in stroke and recovery of
function. Lancet Neurol. 13, 206–216. https://doi.org/10.1016/S1474-4422(13)
70264-3.

Han, J.S., Mikulis, D.J., Mardimae, A., Kassner, A., Poublanc, J., Crawley, A.P.,

deVeber, G.A., Fisher, J.A., Logan, W.J., 2011. Measurement of cerebrovascular
reactivity in pediatric patients with cerebral vasculopathy using blood oxygen level-
dependent MRI. Stroke 42, 1261–1269. https://doi.org/10.1161/
STROKEAHA.110.603225.

Hankey, G.J., 2017. Stroke. Lancet 389, 641–654. https://doi.org/10.1016/S0140-6736

(16)30962-X.

He, Y., Wang, J., Wang, L., Chen, Z.J., Yan, C., Yang, H., Tang, H., Zhu, C., Gong, Q.,

Zang, Y., Evans, A.C., 2009. Uncovering intrinsic modular organization of
spontaneous brain activity in humans. PloS one 4, e5226. https://doi.org/10.1371/
journal.pone.0005226.

Hoptman, M.J., Zuo, X.N., D’Angelo, D., Mauro, C.J., Butler, P.D., Milham, M.P.,

Javitt, D.C., 2012. Decreased interhemispheric coordination in schizophrenia: a
resting st ate fMRI study. Schizophr. Res. 141, 1–7. https://doi.org/10.1016/j.
schres.2012.07.02.

Hu, H., Wang, L., Abdul, S., Tang, X., Feng, Q., Mu, Y., Ge, X., Liao, Z., Ding, Z., 2024.

Frequency-dependent alterations in functional connectivity in patients with
Alzheimer’s Disease spectrum disorders. Front. Aging Neurosci. 16, 1375836.
Hu, X., De Silva, T.M., Chen, J., Faraci, F.M., 2017. Cerebral vascular disease and

neurovascular injury in ischemic stroke. Circ. Res. 120, 449–471. https://doi.org/
10.1161/CIRCRESAHA.116.308427.

Hutchison, R.M., Womelsdorf, T., Allen, E.A., Bandettini, P.A., Calhoun, V.D.,

Corbetta, M., Della Penna, S., Duyn, J.H., Glover, G.H., Gonzalez-Castillo, J.,
Handwerker, D.A., 2013. Dynamic functional connectivity: promise, issues, and
interpretations. Neuroimage 80, 360–378.

Jahanian, H., Christen, T., Moseley, M.E., Zaharchuk, G., 2018. Erroneous resting-state
fMRI connectivity maps due to prolonged arterial arrival time and how to fix them.
Brain Connect. 8, 362–370. https://doi.org/10.1089/brain.2018.0610.

Khalil, A.A., Tanritanir, A.C., Grittner, U., Kirilina, E., Villringer, A., Fiebach, J.B.,

Mekle, R., 2023. Reproducibility of cerebral perfusion measurements using BOLD
delay. Hum. Brain Mapp. 44, 2778–2789. https://doi.org/10.1002/hbm.26244.

Krainik, A., HundGeorgiadis, M., Zysset, S., von Cramon, D.Y., 2005. Regional

impairment of cerebrovascular reactivity and BOLD signal in a dults after stroke.
Stroke 36, 1146–1152. https://doi.org/10.1161/01.STR.0000166178.40973.a7.

11 

L. Wang et al.

NeuroImage 303 (2024) 120920 

Krishnamurthy, V., Sprick, J.D., Krishnamurthy, L.C., Barter, J.D., Turabi, A., Hajjar, I.
M., Nocera, J.R., 2021. The utility of cerebrovascular reactivity MRI in brain
rehabilitation: a mechanistic perspective. Front. Physiol. 12, 642850.

Lee, J., Park, E., Lee, A., Chang, W.H., Kim, D.S., Kim, Y.H., 2018. Alteration and role of
interhemispheric and intrahemispheric connectivity in motor network after stroke.
Brain Topogr. 31, 708–719. https://doi.org/10.1007/s10548-018-0644-9.

Li, T., Xu, J., Wang, L., Xu, K., Chen, W., Zhang, L., Niu, G., Zhang, Y., Ding, Z., Lv, Y.,
2024. Functional network reorganization after endovascular thrombectomy in
patients with anterior circulation stroke. NeuroImage: Clin., 103648

Liang, L., Hu, R., Luo, X., Feng, B., Long, W., Song, R., 2020. Reduced complexity in
stroke with motor deficits: a resting-state fMRI study. Neuroscience 434, 35–43.
Liu, P., Li, Y., Pinho, M., Park, D.C., Welch, B.G., Lu, H., 2017. Cerebrovascular reactivity
mapping without gas challenges. Neuroimage 146, 320–326. https://doi.org/
10.1016/j.neuroimage.2016.11.054.

Lu, H., Liu, P., Yezhuvath, U., Cheng, Y., Marshall, O., Ge, Y., 2014. MRI mapping of

cerebrovascular reactivity via gas inhalation challenges. J. Vis. Exp. 52306. https://
doi.org/10.3791/52306.

Lv, Y., Li, L., Song, Y., Han, Y., Zhou, C., Zhou, D., Zhang, F., Xue, Q., Liu, J., Zhao, L.,

Zhang, C., Han, X., 2019. The local brain abnormalities in patients with transient
ischemic attack: a resting-state fMRI study. Front. Neurosci. 13, 24. https://doi.org/
10.3389/fnins.2019.00024.

Lv, Y., Margulies, D.S., Cameron Craddock, R., Long, X., Winter, B., Gierhake, D.,

Endres, M., Villringer, K., Fiebach, J., Villringer, A., 2013. Identifying the perfusion
deficit in acute stroke with resting-state functional magnetic resonance imaging.
Ann. Neurol. 73, 136–140. https://doi.org/10.1002/ana.23763.

Lyu, J., Ma, N., Tian, C., Xu, F., Shao, H., Zhou, X., Ma, L., Lou, X., 2019. Perfusion and
plaque evaluation to predict recurrent stroke in symptom atic middle cerebral artery
stenosis. Stroke Vasc. Neurol. 4, 129–134. https://doi.org/10.1136/svn-2018-
000228.

Moulton, E., Valabregue, R., Piotin, M., Marnat, G., Saleme, S., Lapergue, B., Lehericy, S.,
Clarencon, F., Rosso, C., 2023. Interpretable deep learning for the prognosis of long-
term functional outcome post-stroke using acute diffusion weighted imaging.
J. Cereb. Blood Flow Metab. 43, 198–209. https://doi.org/10.1177/
0271678x221129230.

Murphy, K., Fox, M.D., 2017. Towards a consensus regarding global signal regression for

resting state functional connectivity MRI. Neuroimage 154, 169–173. https://doi.
org/10.1016/j.neuroimage.2016.11.052.

Nachev, P., Coulthard, E., J¨ager, H.R., Kennard, C., Husain, M., 2008. Enantiomorphic
normalization of focally lesioned brains. Neuroimage 39, 1215–1226. https://doi.
org/10.1016/j.neuroimage.2007.10.002.

Ni, L., Sun, W., Yang, D., Huang, L., Shao, P., Wang, C., Xu, Y., 2022. The cerebrovascular

reactivity-adjusted spontaneous brain activity abnormalities in white matter
hyperintensities related cognitive impairment: a resting-state functional MRI study.
J. Alzheim. Dis. 86, 691–701. https://doi.org/10.3233/JAD-215216.

OvadiaCaro, S., Margulies, D.S., Villringer, A., 2014. The value of resting-state functional
magnetic resonance imaging in stroke. Stroke 45, 2818–2824. https://doi.org/
10.1161/STROKEAHA.114.003689.

Pan, S.L., Wu, S.C., Wu, T.H., Lee, T.K., Chen, T.H.H., 2006. Location and size of infarct

on functional outcome of noncardioembolic ischemic stroke. Disab. Rehabilit. 28,
977–983.

Park, C.h., Chang, W.H., Ohn, S.H., Kim, S.T., Bang, O.Y., PascualLeone, A., Kim, Y.H.,
2011. Longitudinal changes of resting-state functional connectivity during motor
recovery after stroke. Stroke 42, 1357–1362. https://doi.org/10.1161/
STROKEAHA.110.596155.

Qiu, S., Xu, Y., 2020. Guidelines for acute ischemic stroke treatment. Neurosci. Bull. 36,

1229–1232. https://doi.org/10.1007/s12264-020-00534-2.

Raichle, M.E., 2011. The restless brain. Brain Connect. 1, 3–12. https://doi.org/10.1089/

brain.2011.0019.

Reinhard, M., Schwarzer, G., Briel, M., Altamura, C., Palazzo, P., King, A., Bornstein, N.

M., Petersen, N., Motschall, E., Hetzel, A., Marshall, R.S., Klijn, C.J.M.,
Silvestrini, M., Markus, H.S., Vernieri, F., 2014. Cerebrovascular reactivity predicts
stroke in high-grade carotid artery disease. Neurology 83, 1424–1431. https://doi.
org/10.1212/WNL.0000000000000888.

Rorden, C., Bonilha, L., Fridriksson, J., Bender, B., Karnath, H.O., 2012. Age-specific CT
and MRI templates for spatial normalization. Neuroimage 61, 957–965. https://doi.
org/10.1016/j.neuroimage.2012.03.020.

Rossini, P.M., Altamura, C., Ferretti, A., Vernieri, F., Zappasodi, F., Caulo, M.,

Pizzella, V., Del Gratta, C., Romani, G.L., Tecchio, F., 2004. Does cerebrovascular
disease affect the coupling between neuronal acti vity and local haemodynamics?
Brain 127, 99–110. https://doi.org/10.1093/brain/awh012.

Salinet, A.S.M., Panerai, R.B., Robinson, T.G., 2014. The longitudinal evolution of

cerebral blood flow regulation after acute ischaemic stroke. Cerebrovasc. Dis. Extra
4, 186–197. https://doi.org/10.1159/000366017.

Siegel, J.S., Ramsey, L.E., Snyder, A.Z., Metcalf, N.V., Chacko, R.V., Weinberger, K.,
Baldassarre, A., Hacker, C.D., Shulman, G.L., Corbetta, M., 2016a. Disruptions of
network connectivity predict impairment in multiple behavioral domains after
stroke. Proc. Natl. Acad. Sci. U.S.A. 113, E4367–E4376. https://doi.org/10.1073/
pnas.1521083113.

Siegel, J.S., Shulman, G.L., Corbetta, M., 2017. Measuring functional connectivity in

stroke: Approaches and considerations. J. Cereb. Blood Flow Metab. 37, 2665–2678.
https://doi.org/10.1177/0271678x17709198.

Siegel, J.S., Snyder, A.Z., Ramsey, L., Shulman, G.L., Corbetta, M., 2016b. The effects of
hemodynamic lag on functional connectivity and behavior after stroke. J. Cereb.
Blood Flow Metab. 36, 2162–2176. https://doi.org/10.1177/0271678x15614846.

Tang, C., Zhao, Z., Chen, C., Zheng, X., Sun, F., Zhang, X., Tian, J., Fan, M., Wu, Y.,
Jia, J., 2016. Decreased functional connectivity of homotopic brain regions in
chronic stroke patients: a resting state fMRI study. PloS one 11, e0152875. https://
doi.org/10.1371/journal.pone.0152875.

Wise, R.G., Ide, K., Poulin, M.J., Tracey, I., 2004. Resting fluctuations in arterial carbon
dioxide induce significant low frequency variations in BOLD signal. Neuroimage 21,
1652–1664. https://doi.org/10.1016/j.neuroimage.2003.11.025.

Wu, X., Wang, L., Jiang, H., Fu, Y., Wang, T., Ma, Z., Wu, X., Wang, Y., Fan, F., Song, Y.,
Lv, Y., 2023. Frequency-dependent and time-variant alterations of neural activity in
post-stroke depression: A resting-state fMRI study. Neuroimage Clin. 38, 103445.
https://doi.org/10.1016/j.nicl.2023.103445.

Yan, C.G., Wang, X.D., Zuo, X.N., Zang, Y.F., 2016. DPABI: data processing & analysis for
(resting-state) brain imaging. Neuroinformatics 14, 339–351. https://doi.org/
10.1007/s12021-016-9299-4.

Yushkevich, P.A., Piven, J., Hazlett, H.C., Smith, R.G., Ho, S., Gee, J.C., Gerig, G., 2006.
User-guided 3D active contour segmentation of anatomical structures: significantly
improved efficiency and reliability. Neuroimage 31, 1116–1128. https://doi.org/
10.1016/j.neuroimage.

Zang, Y.F., He, Y., Zhu, C.Z., Cao, Q.J., Sui, M.Q., Liang, M., Tian, L.X., Jiang, T.Z.,

Wang, Y.F., 2007. Altered baseline brain activity in children with ADHD revealed by
resting-state functional MRI. Brain Dev. 29, 83–91. https://doi.org/10.1016/j.
braindev.2006.07.002.

Zang, Y., Jiang, T., Lu, Y., He, Y., Tian, L., 2004. Regional homogeneity approach to fMRI

data analysis. NeuroImage 22, 394–400. https://doi.org/10.1016/j.
neuroimage.2003.12.030.

Zhang, D., Raichle, M.E., 2010. Disease and the brain’s dark energy. Nat. Rev. Neurol. 6,

15–28. https://doi.org/10.1038/nrneurol.2009.198.

Zuo, X.N., Kelly, C., Di Martino, A., Mennes, M., Margulies, D.S., Bangaru, S.,

Grzadzinski, R., Evans, A.C., Zang, Y.F., Castellanos, F.X., Milham, M.P., 2010.
Growing together and growing apart: regional and sex differences in the lifespan
developmental trajectories of functional homotopy. J. Neurosci. 30, 15034–15043.
https://doi.org/10.1523/JNEUROSCI.2612-10.2010.

12 

