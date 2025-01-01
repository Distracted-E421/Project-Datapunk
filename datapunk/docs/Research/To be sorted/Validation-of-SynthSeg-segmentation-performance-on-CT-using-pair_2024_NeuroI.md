NeuroImage 303 (2024) 120922 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Validation of SynthSeg segmentation performance on CT using paired MRI
from radiotherapy patients
Selena Huisman a,b,∗, Matteo Maspero b,c, Marielle Philippens b, Joost Verhoeff a,b,
Szabolcs David a,b
a Department of Radiation Oncology, Amsterdam UMC, De Boelelaan 1117, 1081 HV Amsterdam, The Netherlands
b Department of Radiation Oncology, UMC Utrecht, Heidelberglaan 100, 3508 GA Utrecht, The Netherlands
c Computational Imaging Group for MR Diagnostics & Therapy, UMC Utrecht, Heidelberglaan 100, 3508 GA Utrecht, The Netherlands

A R T I C L E I N F O

A B S T R A C T

Dataset link: https://zenodo.org/doi/10.5281/
zenodo.7260704, https://doi.org/10.7937/E1Q
P-D183, https://doi.org/10.7937/TCIA.T905-Z
Q20

Keywords:
Deep learning
Validation
Clinical brain MRI
Clinical brain CT

Introduction: Manual segmentation of medical images is labor intensive and especially challenging for images
with poor contrast or resolution. The presence of disease exacerbates this further, increasing the need for
an automated solution. To this extent, SynthSeg is a robust deep learning model designed for automatic
brain segmentation across various contrasts and resolutions. This study validates the SynthSeg robust brain
segmentation model on computed tomography (CT), using a multi-center dataset.
Methods: An open access dataset of 260 paired CT and magnetic resonance imaging (MRI) from radiotherapy
patients treated in 5 centers was collected. Brain segmentations from CT and MRI were obtained with SynthSeg
model, a component of the Freesurfer imaging suite. These segmentations were compared and evaluated using
Dice scores and Hausdorff 95 distance (HD95), treating MRI-based segmentations as the ground truth. Brain
regions that failed to meet performance criteria were excluded based on automated quality control (QC) scores.
Results: Dice scores indicate a median overlap of 0.76 (IQR: 0.65-0.83). The mean volume difference is 7.79%
(CI: 6.41%–9.18%), with CT segmentations typically smaller than MRI-based. The median HD95 is 2.95 mm
(IQR: 1.73-5.39). QC score based thresholding improves median dice by 0.1 and median HD95 by 0.05 mm.
Morphological differences related to sex and age, as detected by MRI, were also replicated with CT, with an
approximate 17% difference between the CT and MRI results for sex and 10% difference between the results
for age.
Conclusion: SynthSeg can be utilized for CT-based automatic brain segmentation, but only in applications
where precision is not essential. CT performance is lower than MRI based on the integrated QC scores, but
low-quality segmentations can be excluded with QC-based thresholding. Additionally, performing CT-based
neuroanatomical studies is encouraged, as the results show correlations in sex- and age-based analyses similar
to those found with MRI.

1.  Introduction

Segmentation of the human brain can be used to measure regional
volumetric differences between healthy subjects and patients, aiding in
visualizing and quantifying brain structures (Despotović et al., 2015).
Manual segmentation requires extensive labor while providing variable
performance between observers, with median Dice scores falling be-
tween 0.46 and 0.89 and median HD95 between 2.8 and 3.3 depending
on the brain region (Lorenzen et al., 2021). Consequently, automatic
and  reproducible  segmentation  models  have  been  developed,  which
usually require high quality T1-weighted magnetic resonance imaging
(MRI) free of noise and other artifacts. Due to acquisition imperfections
and subject motion, the latter of which is more prevalent in young (e.g.:

infant)  or  general  patient  population  compared  to  healthy  subjects,
some sort of preprocessing of the scans is necessary to improve image
quality  before  the  subsequent  tissue  segmentation.  Moreover,  when
images are only available from computed tomography (CT), the task of
tissue segmentation becomes challenging due to the inferior soft tissue
contrast of CT compared to MRI.

Early brain segmentation methods in CT have relied on a variety
of  traditional  image  processing  techniques.  Intensity  thresholding  is
one of the simplest methods, where specific intensity values are used
to  distinguish  between  brain  tissues  and  non-brain  areas.  However,
this  approach  is  highly  sensitive  to  noise  and  variations  in  image

∗ Corresponding author at: Department of Radiation Oncology, Amsterdam UMC, De Boelelaan 1117, 1081 HV Amsterdam, The Netherlands.

E-mail address: s.i.huisman@amsterdamumc.nl (S. Huisman).

https://doi.org/10.1016/j.neuroimage.2024.120922
Received 28 June 2024; Received in revised form 5 November 2024; Accepted 7 November 2024
Available online 16 November 2024 
1053-8119/© 2024 The Authors. Published by Elsevier Inc. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ). 

S. Huisman et al.

NeuroImage 303 (2024) 120922 

quality (Gonzalez and Woods, 2018). Region growing techniques ex-
pand from a seed point by adding neighboring pixels that meet certain
criteria, such as intensity similarity, but their effectiveness is heavily
dependent on the initial seed selection, which can be challenging in
heterogeneous brain tissues (Adams and Bischof, 1994). Edge detection
methods, like the Canny edge detector, identify boundaries between dif-
ferent tissues based on intensity gradients, but they often struggle with
low-contrast tissue borders, leading to incomplete or inaccurate seg-
mentations (Canny, 1986). Active contour models use evolving curves
to minimize energy based on image gradients and internal smoothness,
but they may converge to local minima, especially in the presence of
noise or weak edges (Kass et al., 1988). The work of Irimia et al. (2019)
combined  probabilistic,  atlas-based  classification  with  topologically-
constrained tissue boundary refinement to delineate grey matter, white
matter,  and  cerebrospinal  fluid  from  head  CT.  The  effectiveness  of
this  approach  is  validated  through  a  comparison  of  MRI-only  and
CT-only segmentations in elderly patients who underwent both types
of  scans.  While  the  results  are  promising  with  a  Dice  score  of  0.85
in grey matter, 0.86 in white matter when compared to MRI, tissue
boundaries are incorrectly identified and the fine sulcal-gyral structure
is mostly omitted. Deep learning has significantly advanced CT brain
segmentation,  offering  improvements  in  accuracy  and  robustness  in
recent years. The U-Net architecture, known for its encoder–decoder
structure,  has  been  particularly  successful  in  all  kind  of  biomedical
image segmentation, including brain CT, as it captures both local and
global features (Ronneberger et al., 2015). Cai et al. (2020) utilized
the Ronneberger U-Net architecture to automate the segmentation of
11 neuroanatomical structures in head CT. Their model incorporated
advanced normalization techniques and class weighting to address class
imbalance, achieving a Dice coefficient of 0.84. However, the model’s
performance varied across different structures, with lower accuracy ob-
served in smaller or less prominent anatomical features. Additionally,
while the model demonstrated robustness on external datasets, it may
still struggle with scans exhibiting significant anatomical variations or
pathologies not represented in the training data.

In  practice,  most  researchers  use  specialized  software  packages
for  brain  image  analysis.  Popular  choices  include  FSL  (FMRIB  Soft-
ware  Library)  (Woolrich  et  al., 2009),  SPM  (Statistical  Parametric
Mapping)  (Friston, 2007)  and  Freesurfer  (Fischl, 2012)  among  oth-
ers.  Freesurfer  has  become  one  of  the  most  widely  used  toolboxes
for calculating neuroanatomical features, such as cortical volume or
thickness measurements. Its applications span various clinical and basic
science investigations related to brain imaging, including studies on
normal aging (Salat et al., 2009), neurodegenerative diseases (Desikan
et  al., 2009),  and  psychiatric  disorders  (Makris  et  al., 2006).  Given
FreeSurfer’s role in brain research, it is necessary that any new tools
or  features  integrated  into  the  software  undergo  independent  test-
ing  upon  their  publication  to  ensure  the  reliability  and  accuracy  of
these additions. The neuroimaging community has been continuously
assessing  the  performance  of  FreeSurfer  and  similar  tools.  This  on-
going  evaluation  is  important  because  the  impact  of  new  features,
such as noise-agnostic segmentation options, on group comparison or
any other results can be significant and complex. Gronenschild et al.
(2012) demonstrated that even changes in processing conditions, such
as FreeSurfer version updates or changes in operating system (OSX 10.5
vs OSX 10.6), can lead to significant differences in volume and cortical
thickness measurements. They found that upgrading from FreeSurfer
version 4.3.1 or 4.5.0 to version 5.0.0 resulted in volume differences
of about 8.8% (range 1.3-64.0%) and cortical thickness differences of
about 2.8% (range 1.1-7.7%). Haddad et al. (2022) performed an anal-
ysis of the reliability and compatibility of brain metrics derived from
FreeSurfer versions 7.1, 6.0, and 5.3. They used test-retest data from
three public datasets to assess within- and between-version reliability
and compatibility across regional outputs. Their findings showed that
cortical thickness measurements from version 7.1 were less compatible
with those of older versions, specifically in the cingulate gyrus, where

the lowest version compatibility was observed (intraclass correlation
coefficient 0.37-0.61). Surface area measurements of certain regions,
such as the temporal pole, frontal pole, and others also showed low
to moderate version compatibility. The study also found that age as-
sociations have version differences in results of downstream statistical
analysis. Seiger et al. (2018) compared cortical thickness estimations
between FreeSurfer and the CAT12 toolbox in patients with Alzheimer’s
disease and healthy controls. They found significant differences in cor-
tical thickness measurements between the two software packages, with
CAT12 producing typically higher thickness estimates. Guo et al. (2018)
examined  the  repeatability  and  reproducibility  of  brain  volumetric
measurements using FreeSurfer (version 6.0.0), FSL-SIENAX (version
5.0.), SPM and CAT12 in patients with multiple sclerosis and healthy
controls. They also investigated the effect of lesion filling via the Lesion
Segmentation Toolbox (version 2.0.10) on neuroanatomical measure-
ments derived from the different tools . Results from Freesurfer were
the  least  affected  by  multiple  sclerosis  lesions. Hedges  et  al. (2022)
investigated the reliability of structural MRI measurements, examining
the effects of scan session, head tiltness, inter-scan interval, acquisition
sequence, FreeSurfer version (v5.3.0 vs 6.0.0 vs 7.1.0), and processing
stream. The differences observed between versions and scanning con-
ditions are comparable in magnitude to effect sizes reported in studies
of neurodegenerative diseases and psychiatric disorders, highlighting
the impact of software updates and acquisition settings or hardware
changes on research outcomes. These studies emphasize the importance
of testing neuroimaging tools as they evolve. The findings show that
researchers need to consider potential biases in these tools, especially
when studying different populations or brain regions. Therefore, the
continued evaluation of image analysis methods is necessary to advance
neuroimaging research and ensure valid results.

To circumvent the need of data preprocessing and to increase the
general applicability of various images regardless of the acquisition se-
quence or method, machine learning-based contrast-agnostic tools have
been trained on artificially downsampled MRIs. Such models enable
automatic and reproducible segmentation of brain images regardless
of  contrast  and  resolution,  effectively  enabling  CT-based  soft-tissue
segmentation  with  similar  performance  to  MRI  without  the  need  of
any  image  preparation.  Recently,  SynthSeg,  part  of  FreeSurfer,  has
been proposed as a promising contrast and resolution agnostic, whole-
brain segmentation model (Billot et al., 2023a). This model, trained
through exclusively on synthetic images with randomized contrasts and
resolutions,  exemplifies  this  robust  approach,  suggesting  satisfactory
segmentation performance even on CT (Billot et al., 2023b). SynthSeg
achieves this performance with a 3D U-net architecture that predicts the
corresponding segmentation from a brain image of any contrast. Direct
comparative validation of SynthSeg is challenging, due to the need for
paired CT and MRI, while paired image availability is usually limited.
However, in radiotherapy (RT) patients with brain tumors routinely
undergo both CT and MRI for radiation planning purposes, making this
setting ideal for validation. Usually, a large part of the patient’s brain
is not affected by tumors, allowing us to compare the performance of
CT and MRI-based segmentation of such regions. Additionally, Synth-
Seg incorporates automatic quality control (QC) scores to assess the
accuracy of segmented brain regions, enabling the exclusion of diseased
areas from the analysis.

We have assembled a benchmark dataset from three open sources,
comprising 260 paired oncological brain CT and MRI images sourced
from  a  total  of  five  medical  centers.  This  diverse  dataset  offers  a
comprehensive resource for validating the SynthSeg model. While the
comparison  of  CT  and  MRI  segmentation  performance  is  valuable,
tissue  segmentations  ultimately  serve  as  tools  for  exploring  various
medical and scientific questions. For example, they can facilitate the
analysis of volumetric differences based on sex or age, which have been
extensively studied in the human brain (Armstrong et al., 2019; Ruigrok
et al., 2014; Peters, 2006).

2 

S. Huisman et al.

NeuroImage 303 (2024) 120922 

Table 1
An overview of the data used. Age and sex are included for the UMC Utrecht cohort from SynthRAD2023, but were not available for the other
cohorts.

In this work, we compared the segmentation performance of Synth-
Seg on CT and MRI of patients with primary or metastatic brain tumors.
Additionally, we examined the volumes of various brain regions be-
tween males and females using both imaging techniques. Furthermore,
we assessed how the brain volumes of patients change with age and
investigated whether the results obtained from MRI segmentation are
reproducible using CT-based segmentation.  Although our study does
not primarily investigate these well-documented differences, we em-
ploy both MRI and CT-based segmentation to replicate such findings.
This approach allows us to test the viability of CT-based segmentation
in neuroscience studies, which have predominantly relied on MRI. Ul-
timately, this comparison aims to expand the methodologies available
for research and validate the effectiveness of CT in capturing relevant
brain differences, when MRI is not available.

2.  Methods

Data was sourced from three openly accessible datasets, contain-
ing  patients  with  primary  or  metastatic  brain  tumor  for  a  total  of
260  paired  CT  and  MRI.  The  first  dataset  was  the  SynthRAD2023
Grand Challenge (https://SynthRAD2023.grand-challenge.org/) train-
ing dataset,1 comprising a subset of 180 brain CT and T1w 3D gradi-
ent echo MRI and are available for public access (Thummerer et al.,
2023). These images were collected from three Dutch hospitals: UMC
Utrecht, UMC Groningen, and Radboud Nijmegen. The SynthRAD study
was approved by the local Institutional Review and Ethics Board on
04/03/2022, with approval number 22/474. Furthermore, we utilized
similar CT-T1w paired subsets from the GLIS-RT (Shusharina and Bort-
feld, 2021) and Burdenko-GBM-Progression projects (Zolotova et al.,
2023),  from  the  TCIA  database  (Clark  et  al., 2013),  which  are  also
available  openly.  We  obtained  these  datasets  with  a  research-only
license under the license number TH-55218 on 26/03/2024, which is
required  since  personal  information  such  as  visible  faces  on  MRI  is
included.  The  GLIS-RT  data  was  collected  at  Massachusetts  General
Hospital,  while  the  Burdenko  data  is  from  the  Burdenko  National
Medical Research Center of Neurosurgery. All CT and T1 images have
been co-registered, spatially aligned and rescaled to 1 mm isotropic res-
olution, no additional processing was applied to the data. An overview
of the datasets and demographics can be found in Table 1. GLIS-RT
provides contrast-enhanced 3D-T1 weighed MRI and radiotherapy plan-
ning CT. Meanwhile, Burdenko-GBM-Progression includes T1-weighed
MRI and topometric CT, in which the MRIs were obtained from four
vendors with varying scanning protocols and the CTs were obtained
with a single scanning protocol. The available information on scanning
protocols for each dataset can be found in supplementary Table 1, split
by MRI and CT protocols. In principle, our analysis could be replicated
by  many  radiotherapy  departments  with  access  to  similar  data,  the

1 Retrieved on 08-09-2023 from https://zenodo.org/doi/10.5281/zenodo.

7260704

open  nature  of  our  sources  and  the  mixture  of  contributing  centers
enhancing the transparency and reproducibility of our results.

Next,  we  used  the  SynthSeg  tool  within  the  Freesurfer  software
suite, version 7.4.1 (Billot et al., 2023b) to perform automatic brain
segmentation based on 95 brain regions. The model was run in robust
mode, with the integrated QC score and volume options enabled. The
QC scores evaluate the reliability of each segmentation by comparing
the  segmented  output  against  a  learned  model  of  what  constitutes
a high-quality segmentation. These scores are generated by assessing
features  of  the  segmentation  against  the  predicted  values  from  the
’regressor R’ of the SynthSeg model, providing a numerical indication
of segmentation quality. For CTs, the corresponding option was enabled
to  facilitate  CT-specific  processing.  The  QC  scores  are  divided  into
eight  categories:  general  white  matter,  general  grey  matter,  general
cerebrospinal fluid (csf), cerebellum, brainstem, thalamus, putamen &
pallidum, and hippocampus & amygdala. The resulting data was exam-
ined using Rstudio version 2023.9.1.494 (Posit team, 2023), applying
a manual region-specific threshold for QC score exclusion instead of
the static 0.65 threshold suggested by the SynthSeg manuscript (Billot
et al., 2023b). This manual thresholding approach was chosen to ac-
count for variations in QC score averages across different brain regions.
In some cases the 0.65 threshold is too lenient resulting in unacceptable
segmentations being included. Our manual thresholds correspond with
the  range  of  0.55-0.75  found  in  the  SynthSeg  manuscript,  and  can
be  found  in  supplementary  table  2.  Brain  regions  with  inadequate
QC scores were selectively removed from each image, preserving the
remaining regions for subsequent analysis. The analysis included cal-
culating the percentage mean volume difference for each brain region,
visualized using violin plots and percentage-based Bland-Altmann plots,
also known as Giavarina plots (Giavarina, 2015). Dice scores and Haus-
dorff 95 distances (HD95) for each brain region were computed using
the  segmentation_metrics  python  package,  based  on  the  segmented
outputs (Jia et al., 2024). Non-overlapping regions were excluded from
the analyses as they resulted in 0 Dice score and physically implausible
HD95. Also, when a label was missing for a patient from either the
CT or the MRI, that particular label was excluded from analyses. Note,
that only CT-based segmentations resulted in any missing regions. Upon
visual inspection, all missing labels in the CT or the non-overlapping
regions only occurred in the tumor affected areas, for which regions
SynthSeg is not meant to produce brain segmentation labels. In short,
brain regions were excluded if either of the following was true: (A)
The QC score was below the threshold or (B) There was no overlap
between the brain regions. The amount of included patients per QC
score  category  can  be  found  in  supplementary  table  2,  with  white
matter  having  the  most  inclusions  at  241,  and  grey  matter  having
the  least  inclusions  at  78  patients.  The  segmentations  were  visually
inspected using FSLeyes from FSL version 6.0 (McCarthy, 2023). For
visualization purposes, the brainstem, left thalamus, left hippocampus
and left cerebellum white matter were highlighted in the figures.

A sex and age-based analysis was conducted using the 60 patients
from UMC Utrecht. These analysis considered eight regions namely the

3 

S. Huisman et al.

NeuroImage 303 (2024) 120922 

Fig. 1. Pipeline of data processing and analyses. From left to right: First, the patient’s CT (A) and MRI (B) are co-registered and then processed by (C) SynthSeg, which outputs
QC scores (F) and segmented volumes for both image modalities (D and E). The resulting segmentations are then filtered by a QC-based threshold (G), after which (H) statistical
analyses are performed, resulting in (I) Dice scores and HD95 distance and (J) volume comparisons.

left-thalamus, -insula cortex, -superior frontal cortex, -hippocampus, -
putamen, -pallidum, -lateral ventricle, and the brainstem. Density plots
and regression lines were obtained using ggplot2 (Wickham, 2016). Re-
gression coefficients were calculated with R’s default linear model (lm)
function. The demographic details for these patients are not publicly
available due to privacy regulations and were retrieved in accordance
with the institutional review boards (nWMO research number 22-474).
Fig. 1 provides a full overview of the analysis pipeline.

3.  Results

To visualize the difference between a CT that received a low QC
versus a high QC score, Figs. 2 and 3 showcase CT and MRI segmen-
tations  in  two  example  patients. Fig.  2 shows  a  patient  with  a  low
mean CT QC score of 0.364 and a high MRI QC score of 0.813. While
the segmentation in both image modalities fails around the tumor and
treatment  affected  area  of  the  brain,  the  CT  segmentation  also  fails
to capture accurately non-affected areas, for example the brainstem,
the cerebellum and even the contralateral cortical areas relative to the
tumor cavity.

Fig.  3 shows  an  example  segmentation  with  high  QC  scores  for
both MRI and CT, with a mean of 0.851 and 0.839, respectively. Both
segmentations capture nearly all normal-appearing parts of the brain.
MRI QC scores show low variability (SD = 0.025, 0.019 excluding
CSF),  for  CSF,  which  exhibits  a  higher  SD  of  0.072,  while  CT  QC
scores show high variability (SD = 0.139). Fig. 4 shows the comparison
of  CT-based  and  MRI-based  QC  scores  from  all  260  patients.  Brain
regions  with  CT  QC  scores  below  the  corresponding  threshold  were
subsequently  excluded  from  the  analysis,  which  results  in  a  SD  of
0.036.  Most  data  points  lie  above  the  unity  line  (in  blue)  in  the
figures, meaning that MRI-based segmentations yield higher QC scores
than  those  from  CT-based  segmentations.  In  all  categories,  MRI  QC
scores  are  significantly  higher  than  CT  QC  scores.  Furthermore,  no
brain  regions  were  excluded  based  on  low  MRI-based  QC  scores  if
they were not already excluded due to low CT QC scores. A detailed
breakdown of filtered and unfiltered mean QC scores along with the
amount of included patients for each brain region is available in the
supplementary materials, table 2. The remaining four QC score plots
can be found in supplementary materials, figure 1.

The distribution of volumes per brain region is shown in Fig. 5.
On  average,  the  CT  volumes  are  significantly  smaller  than  the  MRI

volumes, with an average of 7.79% (CI: 6.41%–9.18%) absolute differ-
ence, although the shape of the distributions is similar. 73 regions have
significantly lower volume for CT compared to MRI, with differences
ranging from 3% to 38%. However, the two largest differences are in
the left and right lateral ventricles with 38% and 35% respectively,
while the largest differences in a tissue area are the left and right palla-
dia with 23% and 24%. 16 regions show no statistical difference, while
6 regions (parahippocampal cortex in both hemispheres, both thalami;
posteriorcingulate and paracentral cortex in the left hemispheres) have
a significantly larger volume for CT compared to MRI, with differences
ranging from 2% to 5%. There is no preference among the volume dif-
ferences between the hemispheres, with a median difference of 1%–1%
among cortical and subcortical regions between the left and right side.
Detailed data on each region’s numerical percentage differences and
total volumes are provided in supplementary table 3. If the confidence
interval of the difference between regions includes 0, it indicates no
significant difference. A visualization of these percentage differences
can be found in supplementary figure 1.

To illustrate the bias in the distribution of the volume differences
between image modalities, Fig. 6 shows the percentage differences of
volumes  plotted  against  the  mean  volume  for  four  of  the  95  brain
regions. The distribution tends to vary more for regions with smaller
mean volumes. Similarly as shown in Fig. 4, CT segmentation volumes
are generally smaller than those from MRI, except in the thalamus and
ventricles.

A median Dice score of 0.76 (IQR: 0.65-0.83) was found from all
regions, calculated from the overlap of each region between MRI and
CT. Before applying a threshold for QC, the median overall Dice score
was 0.66 (IQR: 0.50-0.78). The highest Dice scores are in the thalami
with 0.9–0.9, while the lowest are in the left and right frontal pole
cortical regions with 0.52 and 0.53, respectively. Fig. 7/A shows the
distribution of Dice scores for four brain regions. White matter regions
generally have higher Dice scores than regions of grey matter. Fig. 7/B
shows the HD95 distances with a median HD95 distance of 2.95 mm
(IQR: 1.73–6.16) across all regions. Before QC thresholding the median
HD95 was 3. The Dice scores and HD95 distances for all regions are
available in supplementary table 3.

To consider the effects of sex on brain region volume, density plots
of the brainstem and the hippocampus volume are shown in Fig. 8. The
distributions are shown separately for the MRI and CT volumes, while
the 𝑥 axes are scaled identically within the regions. The differences
in  the  distributions  between  sexes  established  in  MRI  are  similar  to

4 

S. Huisman et al.

NeuroImage 303 (2024) 120922 

Fig. 2. An example of a failed segmentation, demonstrating patient 1BB177 from the SynthRAD2023 cohort, with segmentation boundaries represented by colored lines. The
MRI-derived segmentation, depicted at the top, successfully delineated most anatomical features, including the intricate sulcal structure. In contrast, the CT-derived segmentation,
presented at the bottom, failed to accurately capture any discernible anatomical detail. (For interpretation of the references to color in this figure legend, the reader is referred to
the web version of this article.)

those based-on CT. The quantitative overview of the sex-based analysis
is  located  in  supplementary  table  4.  For  all  sex  based  analyses,  the
direction  of  the  volume  differences  are  identical  with  both  CT  and
MRI based comparisons, with a mean 17% difference overall. Of the
selected regions, the brainstem shows the most considerable percentage
difference of 52% between the MRI and CT.

The  results  for  the  age-based  analysis  are  shown  in Fig.  9.  Sim-
ilarly  to  the  sex-based  analysis,  most  of  the  MR-based  results  and
relationships are preserved in the CT-based analyses. In four selected
regions, the volume of the brain areas are plotted against patient age.
A linear regression slope with confidence intervals is used to visualize
the effect of aging on brain region volumes, separately for CT and MRI-
segmented volumes. All regions, except the brainstem, show the same
direction in the volume change-age relationship. For these regions, the
mean absolute difference between the regression slopes is 10%. The
brainstem show non-significant regressions in both CTs and MRIs with
different  slope  directions.  However,  these  differences  are  negligible
when adjusted for the brainstem’s size. The quantitative summary of
the age-based analysis is also located in supplementary table 3.

4.  Discussion

In this work, we evaluated the performance of the SynthSeg 2.0
model for CT brain segmentations compared to MRI-based ones. While
the debut SynthSeg work included testing on 6 pairs of CT-MRI (Billot
et al., 2023a), the work discussing the robust version of SynthSeg omits
such analyses (Billot et al., 2023b). Here, the we extended the investiga-
tion to 260 subjects with paired samples from different sites and clinical
conditions, exclusively from open sources. The fact that SynthSeg can

perform segmentation on CT is – in our view – an unintentional, but
useful by-product of its novel learning and training strategy, in which
the network was exposed to a wide variety of synthetic contrasts. This
resulted in the network learning features that are ultimately contrast-
and resolution-agnostic, surpassing the domain of any reasonable MRI
contrasts and de facto enabling the segmentation of images even with
CT-like contrasts.

Our quantitative analysis suggests that SynthSeg delivers CT seg-
mentation performance similar to the range of inter observer variability
in manual segmentation, particularly in scenarios with minimal anoma-
lies  or  data  censoring.  This  level  of  performance  could  potentially
reduce the need for time-consuming manual segmentations, enable and
accelerate  analysis  pipelines,  and  improve  the  consistency  of  brain
structure measurements across different studies or clinical assessments
using  a  CT.  Should  segmentation  failure  occur  for  any  reason,  it  is
reflected  in  the  QC  score,  allowing  for  the  rejection  of  unreliable
segmentations.  The  availability  of  the  QC  score  is  a  novel  feature
as  most  existing  segmentation  solution  does  not  offer  any  kind  of
quality control and hence the user have to post-hoc conclude if the
segmentations  could  be  trusted  or  not.  Current  analysis  shows  that
applying QC score thresholds improved the median Dice score from
0.66 to 0.76 and reduced the median HD95 from 3.0 mm to 2.95 mm,
demonstrating that the exclusion of low-quality segmentations signif-
icantly enhances overall accuracy, particularly in regions affected by
tumors or surgical cavities where segmentation is inherently unfeasible.
Additionally, some regions, for example the lateral ventricles and grey
matter  exhibit  highly  variable  Dice  scores  and  regions  that  do  not
overlap despite adequate QC scores. This may suggest that QC scores
are  not  always  reliable  indicators  of  segmentation  quality  in  some

5 

S. Huisman et al.

NeuroImage 303 (2024) 120922 

Fig. 3. An example of a high-quality segmentation, demonstrating patient 1BA014 from the SynthRAD2023 cohort, with segmentation boundaries represented by colored lines. The
MRI-derived segmentation, depicted at the top, successfully delineated the anatomical features with high accuracy. Similarly, the CT-derived segmentation, shown at the bottom,
accurately captured the anatomical details. Both modalities exhibit remarkable concordance in their segmentation results, as evidenced by the closely aligned colored contours
representing the respective segmentations. (For interpretation of the references to color in this figure legend, the reader is referred to the web version of this article.)

brain regions, though they are generally effective. However, the HD95
distance indicates that segmented regions are always relatively close to
each other, unless a certain region is not segmented at all.

Overall,  CT  QC  scores  are  lower  than  those  for  MRI,  implying
superior performance in MRI segmentations, as evidenced by the Dice
score. The difference between CT-QC and MRI-QC is marginal in certain
brain regions, such as the brainstem or the thalamus (0.037 and 0.022,
respectively).  However,  the  disparity  is  more  pronounced  in  others,
such as general grey and white matter, with mean filtered QC score
differences of 0.098 and 0.077, respectively. However, these regions
occupy large portion of the brain and are nearly always affected by
lesions. This observation aligns with the expectation of lower soft tissue
contrast in CT.

Correlations between demographic factors such as sex or age and
brain volume remain consistent in MRI and CT segmentations, with
a  13%  mean  absolute  difference  for  age-based  analyses,  suggesting
that the CT-derived conclusions are very close to MRI-based results.
The  ability  of  SynthSeg  to  perform  CT  segmentation  with  accuracy
comparable to inter-observer variability in manual segmentation rep-
resents a significant advancement in applying neuroimaging method
for  CT,  potentially  enabling  more  widespread  use  of  CT  for  brain
volumetry in clinical and research settings where MRI is unavailable
or  contraindicated.  As  a  consequence,  SynthSeg’s  robustness  could
enable the applicability of CT databases for research purposes, which
datasets are typically not utilized. In emergency settings, where rapid
assessment is necessary and MRI may not be immediately available,
CT-based segmentation could provide valuable structural information
to guide treatment decisions (Chu et al., 2023). For patients with gen-
eral MRI contraindications, such as those with certain metal implants
or severe claustrophobia, CT-based segmentation offers an alternative
method for assessing brain structure. In brain radiation treatment, cone

beam CTs (CBCTs) are acquired during treatment for accurate patient
position verification, resulting in multiple images for a patient with a
primary brain tumor. While CBCTs generally have lower quality than
the planning CT, the application of SynthSeg on CBCT can effectively
turn every multi fraction brain RT into a longitudinal study. Also, it has
been observed that tumors can undergo changes during the course of
treatment, which may result in the initially developed RT plan failing
to provide sufficient volume coverage throughout the entire treatment
period (Stewart et al., 2021; Tsien et al., 2005; Champ et al., 2012).
Recent  advances  in  CBCT  image  quality  improvement  have  opened
new possibilities for adaptive radiotherapy (RT). Adaptive RT involves
modifying or adapting treatment plans in response to tumor and normal
tissue  changes  observed  during  the  treatment  period  (Robar  et  al.,
2024; Tseng et al., 2024; Matsuyama et al., 2022). With enhanced CBCT
image quality, the widespread application of adaptive RT could be fur-
ther accelerated through the implementation of CT-segmentation-based
solutions.

Current work, while comprehensive, has certain limitations. It pri-
marily utilizes 260 paired images from radiotherapy patients, which
cannot fully represent the general population or other patient groups.
Despite this, the ability to exclude diseased and censored brain regions
using QC scores suggests that our findings could have broader applica-
bility in settings requiring brain region segmentation. It is anticipated
that segmentation performance would be enhanced in the absence of
diseased brain areas. To the best of our knowledge, there are no open
datasets of paired CT-MRI datasets available from a healthy population,
however, acquiring such data raises ethical considerations regarding ra-
diation exposure to healthy volunteers. One limitation regarding using
MRI as a basis for comparison is that MRI contain distortions, which
are not present in CT. This could cause a discrepancy in the Dice scores
and HD95 distances between MRI and CT. Keeping in mind that current

6 

S. Huisman et al.

NeuroImage 303 (2024) 120922 

Fig. 4. Scatterplot of CT and MRI QC scores. The 𝑥-axis represents the CT QC scores, while the 𝑦-axis depicts the MRI-derived scores. Each data point corresponds to an individual
patient’s score. A blue diagonal line with a slope of unity is included to indicate the equal scores between modalities. The red line demarcates the threshold established for the
exclusion of suboptimal segmentations. (For interpretation of the references to color in this figure legend, the reader is referred to the web version of this article.)

Fig. 5. Four violin plots with enclosed boxplots show the volume distribution of between the MRI and CT segmentation volumes for four brain regions. The 𝑥-axis shows the
volume in mm3, while the imaging modality is listed on the 𝑦-axis. CT is colored red, while MRI is colored blue. (For interpretation of the references to color in this figure legend,
the reader is referred to the web version of this article.)

7 

S. Huisman et al.

NeuroImage 303 (2024) 120922 

Fig. 6. Four Giavarina (or scaled Bland–Altman) plots for different brain regions between MRI and CT-based volumes. The 𝑥-axis shows the mean volume in mm3, while the
𝑦-axis shows the percentage difference for each segmentation. The bias and standard deviations are shown within each plot. Negative bias means smaller CT segmentation and
vice versa.

Fig. 7. Two sets of boxplots show (A) the Dice scores and (B) the HD95 distance for four brain regions on the 𝑦 axis, while the 𝑥 axis shows the selected regions. The data points
represent outliers for each brain region. HD95 was cut off at 8 mm for visual clarity, which removed some outliers for the brainstem.

investigations did not correct for MRI distortions, our expectation is
that if we correct for MRI distortions beforehand, segmentation perfor-
mance would improve and HD95 and Dice would be lower. However,
since  the  Dice  scores  and  HD95  still  fall  within  a  similar  range  as
the interobserver variation, we believe that CT performance will still
be similar to the interobserver variability with these distortions taken
into account. Finally, HD95 and Dice scores have certain limitations,
especially concerning segmentations with small surface areas (Reinke
et al., 2023). Utilizing alternative metrics to Dice scores and HD95 such
as Intersection over Union and Normalized Surface Distance might give
differing results based on the specific aspect of the segmentation each
metric evaluates.

This  work  confirms  that  SynthSeg  provides  a  valuable  tool  for
utilizing  CT  data  in  research  applications.  Due  to  the  multi-center,

international nature of the data used in the study, the results should be
generalizable to other datasets. Except for the sex and age data for the
UMC Utrecht cohort, the rest of the data is publicly available, allowing
for full transparency over the majority of the analysis. For future work,
validating  SynthSeg’s  robustness  with  generally  low  quality  images,
including CBCT, could determine if the model can effectively extract
data from a wide-range of applications and even archived datasets.

5.  Conclusion

The robust version of SynthSeg demonstrates segmentation of brain
CT  performance  comparable  to  ranges  found  in  interobserver  varia-
tion. While CT-based segmentation typically underperforms compared
to  MRI-based  segmentation,  the  model’s  automated  provision  of  QC

8 

S. Huisman et al.

NeuroImage 303 (2024) 120922 

Fig. 8. Four density plots comparing the volume distributions in the brainstem and hippocampus across sexes for both CT and MRI. The density is shown on the 𝑥 axis, while the
region volume in mm3 is shown on the 𝑦 axis. The left figures contain volumes for CT, while the right figures contain volumes for MRI. The red area under the curve represents
females, while the blue area represents males. (For interpretation of the references to color in this figure legend, the reader is referred to the web version of this article.)

Fig. 9. The figure presents four plots, each illustrating the relationship between brain region volume and age in four different brain regions. Orange points and lines denote CT
data, whereas blue points and lines represent MRI data. The data points mark the volumes from individual segmentation, and the lines indicate the linear regression trajectories
for each imaging modality, complete with their respective confidence intervals. (For interpretation of the references to color in this figure legend, the reader is referred to the web
version of this article.)

9 

S. Huisman et al.

NeuroImage 303 (2024) 120922 

scores is a valuable feature. It allows for the exclusion of regions with
substandard quality, whether due to low image quality or abnormal
tissue, such as tumors. The relationships between sex, age, and brain
region volumes are preserved when performed using CT compared to
MRI, suggesting that the segmentations offer comparable insights. As
a  conclusion,  our  findings  suggest  that  SynthSeg  can  be  effectively
utilized  to  obtain  segmentation  data  from  CT,  enhancing  research
capabilities.

CRediT authorship contribution statement

Selena Huisman: Writing – original draft, Visualization, Software,
Methodology, Investigation, Formal analysis. Matteo Maspero: Writing
– review & editing, Validation, Resources. Marielle Philippens: Writ-
ing – review & editing, Resources. Joost Verhoeff: Writing – review
&  editing,  Supervision,  Resources,  Project  administration. Szabolcs
David: Writing  –  review  &  editing,  Supervision,  Resources,  Project
administration, Methodology, Data curation, Conceptualization.

Declaration of competing interest

The  authors  declare  that  they  have  no  known  competing  finan-
cial  interests  or  personal  relationships  that  could  have  appeared  to
influence the work reported in this paper.

Appendix A.  Supplementary data

Supplementary material related to this article can be found online

at https://doi.org/10.1016/j.neuroimage.2024.120922.

Data availability

The data from the SynthRAD challenge is available from: https:/
/zenodo.org/doi/10.5281/zenodo.7260704. The data from Burdenko-
GBM-Progression is available from: https://doi.org/10.7937/E1QP-D1
83. The data from GLIS-RT is available from: https://doi.org/10.7937
/TCIA.T905-ZQ20.Code for the statistical analysis is not provided.

References

Adams, R., Bischof, L., 1994. Seeded region growing. IEEE Trans. Pattern Anal. Mach.

Intell. 16 (6), 641–647. http://dx.doi.org/10.1109/34.295913.

Armstrong,  N.M.,  An,  Y.,  Beason-Held,  L.,  Doshi,  J.,  Erus,  G.,  Ferrucci,  L.,  Da-
vatzikos, C., Resnick, S.M., 2019. Sex differences in brain aging and predictors
of  neurodegeneration  in  cognitively  healthy  older  adults.  URL https://www.
sciencedirect.com/science/article/abs/pii/S0197458019301769.

Billot, Benjamin, Greve, Douglas N., Puonti, Oula, Thielscher, Axel, Van Leemput, Koen,
Fischl, Bruce, Dalca, Adrian V., Iglesias, Juan Eugenio, 2023a. Synthseg: Segmen-
tation of brain mri scans of any contrast and resolution without retraining. Med.
Image Anal. 86, 102789. http://dx.doi.org/10.1016/j.media.2023.102789.

Billot,  Benjamin,  Magdamo,  Colin,  Cheng,  You,  Arnold,  Steven  E.,  Das,  Sudeshna,
Iglesias, Juan Eugenio, 2023b. Robust machine learning segmentation for large-
scale analysis of heterogeneous clinical brain mri datasets. Proc. Natl. Acad. Sci.
120 (9), http://dx.doi.org/10.1073/pnas.2216399120.

Cai,  Jason  C.,  Akkus,  Zeynettin,  Philbrick,  Kenneth  A.,  Boonrod,  Arunnit,  Hood-
eshenas,  Safa,  Weston,  Alexander  D.,  Rouzrokh,  Pouria,  Conte,  Gian  Marco,
Zeinoddini, Atefeh, Vogelsang, David C., et al., 2020. Fully automated segmentation
of head ct neuroanatomy using deep learning. Radiol. Artif. Intell. 2 (5), http:
//dx.doi.org/10.1148/ryai.2020190183.

Canny, John, 1986. A computational approach to edge detection. IEEE Trans. Pattern
Anal. Mach. Intell. PAMI-8 (6), 679–698. http://dx.doi.org/10.1109/tpami.1986.
4767851.

Champ, Colin E., Siglin, Joshua, Mishra, Mark V., Shen, Xinglei, Werner-Wasik, Maria,
Andrews, David W., Mayekar, Sonal U., Liu, Haisong, Shi, Wenyin, 2012. Evaluating
changes in radiation treatment volumes from post-operative to same-day planning
mri in high-grade gliomas. Radiat. Oncol. 7 (1), http://dx.doi.org/10.1186/1748-
717x-7-220.

Chu, Kevin, Kelly, Anne-Maree, Keijzers, Gerben, Kinnear, Frances, Kuan, Win Sen,
Graham,  Colin,  Laribi,  Said,  Roberts,  Tom,  Karamercan,  Mehmet,  Cardozo-
Ocampo,  Alejandro,  et  al.,  2023.  Computed  tomography  brain  scan  utilization
in patients with headache presenting to emergency departments: A multinational
study. Eur. J. Emerg. Med. http://dx.doi.org/10.1097/mej.0000000000001055.

10 

Clark, Kenneth, Vendt, Bruce, Smith, Kirk, Freymann, John, Kirby, Justin, Koppel, Paul,
Moore, Stephen, Phillips, Stanley, Maffitt, David, Pringle, Michael, et al., 2013.
The cancer imaging archive (tcia): Maintaining and operating a public information
repository. J. Digit. Imaging 26 (6), 1045–1057. http://dx.doi.org/10.1007/s10278-
013-9622-7.

Desikan, R.S., Cabral, H.J., Hess, C.P., Dillon, W.P., Glastonbury, C.M., Weiner, M.W.,
Schmansky, N.J., Greve, D.N., Salat, D.H., Buckner, R.L., et al., 2009. Automated
mri measures identify individuals with mild cognitive impairment and alzheimer’s
disease. Brain 132 (8), 2048–2057. http://dx.doi.org/10.1093/brain/awp123.
Despotović,  Ivana,  Goossens,  Bart,  Philips,  Wilfried,  2015.  Mri  segmentation  of  the
human brain: Challenges, methods, and applications. Comput. Math. Methods Med.
2015, 1–23. http://dx.doi.org/10.1155/2015/450341.

Fischl,  Bruce,  2012.  Freesurfer.  NeuroImage  62  (2),  774–781. http://dx.doi.org/10.

1016/j.neuroimage.2012.01.021.

Friston, Karl J., 2007. Friston Statistical Parametric Mapping the Analysis of Functional

Brain Images. Academic.

Giavarina, Davide, 2015. Understanding bland altman analysis. Biochem. Med. 25 (2),

141–151. http://dx.doi.org/10.11613/bm.2015.015.

Gonzalez, Rafael C., Woods, Richard E., 2018. Digital Image Processing. Pearson.
Gronenschild, Ed H., Habets, Petra, Jacobs, Heidi I., Mengelers, Ron, Rozendaal, Nico,
van Os, Jim, Marcelis, Machteld, 2012. The effects of freesurfer version, workstation
type, and macintosh operating system version on anatomical volume and cortical
thickness measurements. PLoS ONE 7 (6), http://dx.doi.org/10.1371/journal.pone.
0038234.

Guo, Chunjie, Ferreira, Daniel, Fink, Katarina, Westman, Eric, Granberg, Tobias, 2018.
Repeatability and reproducibility of freesurfer, fsl-sienax and spm brain volumetric
measurements and the effect of lesion filling in multiple sclerosis. Eur. Radiol. 29
(3), 1355–1364. http://dx.doi.org/10.1007/s00330-018-5710-x.

Haddad, Elizabeth, Pizzagalli, Fabrizio, Zhu, Alyssa H., Bhatt, Ravi R., Islam, Tasfiya,
Gari,  Iyad  Ba,  Dixon,  Daniel,  Thomopoulos,  Sophia  I.,  Thompson,  Paul  M.,  Ja-
hanshad, Neda, 2022. Multisite test–retest reliability and compatibility of brain
metrics derived from freesurfer versions 7.1, 6.0, and 5.3. Hum. Brain Mapp. 44
(4), 1515–1532. http://dx.doi.org/10.1002/hbm.26147.

Hedges, Emily P., Dimitrov, Mihail, Zahid, Uzma, Vega, Barbara Brito, Si, Shuqing,
Dickson,  Hannah,  McGuire,  Philip,  Williams,  Steven,  Barker,  Gareth  J.,  Kemp-
ton, Matthew J., 2022. Reliability of structural mri measurements: The effects of
scan session, head tilt, inter-scan interval, acquisition sequence, freesurfer version
and  processing  stream.  NeuroImage  246,  118751. http://dx.doi.org/10.1016/j.
neuroimage.2021.118751.

Irimia, Andrei, Maher, Alexander S., Rostowsky, Kenneth A., Chowdhury, Nahian F.,
Hwang, Darryl H., Meng Law, E., 2019. Brain segmentation from computed to-
mography of healthy aging and geriatric concussion at variable spatial resolutions.
Front. Neuroinform. 13, http://dx.doi.org/10.3389/fninf.2019.00009.

Jia, Jingnan, Staring, Marius, Stoel, Berend C., 2024. seg-metrics: a python package to

compute segmentation metrics. medRxiv 2024–02.

Kass,  Michael,  Witkin,  Andrew,  Terzopoulos,  Demetri,  1988.  Snakes:  Active  con-
tour  models.  Int.  J.  Comput.  Vis.  1  (4),  321–331. http://dx.doi.org/10.1007/
bf00133570.

Lorenzen,  Ebbe  Laugaard,  Kallehauge,  Jesper  Folsted,  Byskov,  Camilla  Skinnerup,
Dahlrot,  Rikke  Hedegaard,  Haslund,  Charlotte  Aaquist,  Guldberg,  Trine  Lignell,
Lassen-Ramshad, Yasmin, Lukacova, Slávka, Muhic, Aida, Nyström, Petra Witt, et
al., 2021. A national study on the inter-observer variability in the delineation of
organs at risk in the brain. Acta Oncol. 60 (11), 1548–1554. http://dx.doi.org/10.
1080/0284186x.2021.1975813.

Makris, Nikos, Goldstein, Jill M., Kennedy, David, Hodge, Steven M., Caviness, Verne S.,
Faraone, Stephen V., Tsuang, Ming T., Seidman, Larry J., 2006. Decreased volume
of left and total anterior insular lobule in schizophrenia. Schizophr. Res. 83 (2–3),
155–171. http://dx.doi.org/10.1016/j.schres.2005.11.020.

Matsuyama, Tomohiko, Fukugawa, Yoshiyuki, Kuroda, Junichiro, Toya, Ryo, Watak-
abe, Takahiro, Matsumoto, Tadashi, Oya, Natsuo, 2022. A prospective comparison
of adaptive and fixed boost plans in radiotherapy for glioblastoma. Radiat. Oncol.
17 (1), http://dx.doi.org/10.1186/s13014-022-02007-4.

McCarthy, Paul., 2023. Fsleyes, Vol. 9. URL https://zenodo.org/record/7038115.
Peters,  R.,  2006.  Ageing  and  the  brain.  Postgrad.  Med.  J.  82  (964),  84–88. http:

//dx.doi.org/10.1136/pgmj.2005.036665.

Posit  team,  2023.  Rstudio:  Integrated  development  environment  for  R.  In:  Posit

Software. PBC, Boston, MA, URL http://www.posit.co/.

Reinke, Annika, Tizabi, Minu D., Sudre, Carole H., Eisenmann, Matthias, Rädsch, Tim,
Baumgartner, Michael, Acion, Laura, Antonelli, Michela, Arbel, Tal, Bakas, Spyri-
don, et al., 2023. Common limitations of image processing metrics: A picture story.
URL https://arxiv.org/abs/2104.05642.

Robar,  James  L.,  Cherpak,  Amanda,  MacDonald,  Robert  Lee,  Yashayaeva,  Abi-
gail,  McAloney,  David,  McMaster,  Natasha,  Zhan,  Kenny,  Cwajna,  Slawa,
Patil,  Nikhilesh,  Dahn,  Hannah,  2024.  Novel  technology  allowing  cone  beam
computed tomography in 6 seconds: A patient study of comparative image quality.
Pract. Radiat. Oncol. 14 (3), 277–286. http://dx.doi.org/10.1016/j.prro.2023.10.
014.

Ronneberger, Olaf, Fischer, Philipp, Brox, Thomas, 2015. U-Net: Convolutional Net-
works for Biomedical Image Segmentation. In: Lecture Notes in Computer Science,
pp. 234–241. http://dx.doi.org/10.1007/978-3-319-24574-4_28.

S. Huisman et al.

NeuroImage 303 (2024) 120922 

Tseng,  Chia-Lin,  Zeng,  K.  Liang,  Mellon,  Eric  A.,  Soltys,  Scott  G.,  Ruschin,  Mark,
Lau, Angus Z., Lutsik, Natalia S., Chan, Rachel W., Detsky, Jay, Stewart, James,
et al., 2024. Evolving concepts in margin strategies and adaptive radiotherapy for
glioblastoma: A new future is on the horizon. Neuro-Oncol. 26, http://dx.doi.org/
10.1093/neuonc/noad258.

Tsien, Christina, Gomez-Hassan, Diana, Haken, Randall K. Ten, Tatro, Daniel, Junck, L.,
Chenevert, T.L., Lawrence, T., 2005. Evaluating changes in tumor volume using
magnetic resonance imaging during the course of radiotherapy treatment of high-
grade gliomas: Implications for conformal dose-escalation studies. Int. J. Radiat.
Oncol.  Biol.  Phys.  62  (2),  328–332. http://dx.doi.org/10.1016/j.ijrobp.2004.10.
010.

Wickham, Hadley, 2016. ggplot2: Elegant Graphics for Data Analysis. Springer-Verlag,

New York, ISBN: 978-3-319-24277-4, URL https://ggplot2.tidyverse.org.

Woolrich, Mark W., Jbabdi, Saad, Patenaude, Brian, Chappell, Michael, Makni, Salima,
Behrens,  Timothy,  Beckmann,  Christian,  Jenkinson,  Mark,  Smith,  Stephen  M.,
2009.  Bayesian  analysis  of  neuroimaging  data  in  fsl.  NeuroImage  45  (1), http:
//dx.doi.org/10.1016/j.neuroimage.2008.10.055.

Zolotova,  S.V.,  Golanov,  A.V.,  Pronin,  I.N.,  Dalechina,  A.V.,  Nikolaeva,  A.A.,
Belyashova,  A.S.,  Usachev,  D.Y.,  Kondrateva,  E.A.,  Druzhinina,  P.V.,  Shi-
rokikh, B.N., et al., 2023. Burdenko-gbm-progression. http://dx.doi.org/10.7937/
E1QP-D183.

Ruigrok, Amber N.V., Salimi-Khorshidi, Gholamreza, Lai, Meng-Chuan, Baron-Cohen, Si-
mon, Lombardo, Michael V., Tait, Roger J., Suckling, John, 2014. A meta-analysis
of sex differences in human brain structure. Neurosci. Biobehav. Rev. 39, 34–50.
http://dx.doi.org/10.1016/j.neubiorev.2013.12.004.

Salat, D., Greve, D., Pacheco, J., Quinn, B., Helmer, K., Buckner, R., Fischl, B., 2009.
Regional white matter volume differences in nondemented aging and alzheimer’s
disease. NeuroImage 44 (4), 1247–1258. http://dx.doi.org/10.1016/j.neuroimage.
2008.10.030.

Seiger, Rene, Ganger, Sebastian, Kranz, Georg S., Hahn, Andreas, Lanzenberger, Rupert,
2018. Cortical thickness estimations of freesurfer and the cat12 toolbox in patients
with  alzheimer’s  disease  and  healthy  controls.  J.  Neuroimag.  28  (5),  515–523.
http://dx.doi.org/10.1111/jon.12521.

Shusharina,  N.,  Bortfeld,  T.,  2021.  Glioma  image  segmentation  for  radiotherapy:
Rt  targets,  barriers  to  cancer  spread,  and  organs  at  risk  (glis-rt). https://wiki.
cancerimagingarchive.net/pages/viewpage.action?pageId=95224486.

Stewart, James, Sahgal, Arjun, Lee, Young, Soliman, Hany, Tseng, Chia-Lin, Detsky, Jay,
Husain,  Zain,  Ho,  Ling,  Das,  Sunit,  Maralani,  Pejman  Jabehdar,  et  al.,  2021.
Quantitating interfraction target dynamics during concurrent chemoradiation for
glioblastoma: A prospective serial imaging study. Int. J. Radiat. Oncol. Biol. Phys.
109 (3), 736–746. http://dx.doi.org/10.1016/j.ijrobp.2020.10.002.

Thummerer,  Adrian,  van  der  Bijl,  Erik,  Galapon,  Jr.,  Arthur,  Verhoeff,  Joost  J.C.,
Langendijk,  Johannes  A.,  Both,  Stefan,  van  den  Berg,  Cornelis  (Nico)  A.T.,
Maspero, Matteo, 2023. Synthrad2023 grand challenge dataset: Generating syn-
thetic ct for radiotherapy. Med. Phys. 50 (7), 4664–4674. http://dx.doi.org/10.
1002/mp.16529,  URL https://aapm.onlinelibrary.wiley.com/doi/abs/10.1002/mp.
16529.

11 

