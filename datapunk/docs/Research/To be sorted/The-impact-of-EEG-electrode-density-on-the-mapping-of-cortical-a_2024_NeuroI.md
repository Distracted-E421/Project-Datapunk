NeuroImage 303 (2024) 120932 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

The impact of EEG electrode density on the mapping of cortical activity 
networks in infants

Amirreza Asayesh a,b,*, Sampsa Vanhatalo a,b, Anton Tokariev a,b,*
a BABA Center, Pediatric Research Center, Children’s Hospital, University of Helsinki and Helsinki University Hospital, Helsinki, Finland
b Department of Physiology, University of Helsinki, Helsinki, Finland

A R T I C L E  I N F O

A B S T R A C T

Keywords:
Electroencephalography
Electrode density
Infant cortical networks
Functional connectivity
Source reconstruction

Objective: Electroencephalography (EEG) is widely used for assessing infant’s brain activity, and multi-channel 
recordings  support  studies  on  functional  cortical  networks.  Here,  we  aimed  to  assess  how  the  number  of 
recording electrodes affects the quality and level of details accessible in studying infant’s cortical networks.
Methods: Dense array EEG recordings with 124 channels from N=20 infants were used as the reference, and lower 
electrode numbers were subsampled to simulate recording setups with 63, 31, and 19 electrodes, respectively. 
Cortical activity networks were computed for each recording setup and different frequencies using amplitude and 
phase correlation measures. The effects of the recording setup were systematically assessed on global, nodal, and 
edge levels.
Results:  Compared  to  the  reference  124-channel  recording  setup,  lowering  electrode  density  affected  network 
measures in a modality- and frequency-specific manner. The global network features were essentially comparable 
with 63 or 31 channels. However, the analytic reliability of the local network measures, both at nodal and edge 
levels, was proportional to the electrode density. The low-frequency amplitude correlations were most robust to 
the number of recording electrodes, whereas higher frequency phase correlation networks were most sensitive to 
the density of recording electrodes.
Conclusions:  Our  findings  suggest  strong  and  predictable  effects  of  recording  setup  on  the  network  analyses. 
Higher  electrode  number  supports  studies  on  networks  with  phase  correlations,  higher  frequency,  and  finer 
spatial details.
Significance: The relationship between the recording setup and reliability of network analyses is essential for the 
prospective  design  of  research  data  collection,  as  well  as  for  guiding  analytic  strategies  when  using  already 
collected EEG data from infants.

1. Introduction

Electroencephalography (EEG) has become an indispensable tool in 
studying brain dynamics, offering a non-invasive method to capture the 
brain’s electrical activity with exceptional temporal resolution. Despite 
its  potential,  the  spatial  resolution  of  EEG  has  been  a  longstanding 
limitation, prompting the development of high-density electrode arrays 
and  advanced  computational  algorithms  to  enhance  the  accuracy  of 
source  reconstruction.  The  integration  of  detailed  anatomical  head 
models  with  these  technological  advances  has  significantly  improved 
EEG’s ability to map cortical networks, offering finer insights into brain 
dynamics.  Such  progress  underscores  EEG’s  growing  significance  in 

studying  developmental  disorders  and  conditions,  highlighting  its 
transition from a simple clinical tool to a comprehensive neuroscience 
platform for a better understanding of the functional dynamics of the 
human brain across the life span (Liu et al., 2018; Michel and Brunet, 
2019; Michel and He, 2019).

The human cortical networks undergo substantial organizational and 
other developmental changes during pregnancy, perinatal period, and 
early infancy (Keunen et al., 2017; Kostovi´c et al., 2021). This period is 
characterized  by  rapid  changes  in  neural  connectivity,  making  it  a 
critical window for studying the establishment and maturation of brain 
networks (França et al., 2024; Karolis et al., 2023; Omidvarnia et al., 
2014;  Tokariev,  Videman,  et  al.,  2016).  Analytically,  neural  activity 

* Corresponding authors at: Department of Physiology, Biomedicum 1, BABA center, room B129b, University of Helsinki, P.O. Box 63 (Haartmaninkatu 8), 00014 

University of Helsinki, Finland.

E-mail addresses: amirreza.asayesh@helsinki.fi (A. Asayesh), anton.tokariev@helsinki.fi (A. Tokariev). 

https://doi.org/10.1016/j.neuroimage.2024.120932
Received 13 June 2024; Received in revised form 3 October 2024; Accepted 12 November 2024  
Available online 13 November 2024 
1053-8119/© 2024 The Author(s). Published by Elsevier Inc. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ). 

A. Asayesh et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120932 

measured  by  EEG  can  be  viewed  as  functional  network  with  cortical 
areas as ’nodes’  and functional interactions between them as ’edges.’ 
This  graph-theoretical  approach  is  effectively  used  in  infants,  whose 
brain networks exhibit increasing specialization and segregation as they 
develop (Wig, 2017; Wylie et al., 2014; Zhao et al., 2019). Such insights 
are  pivotal  in  unraveling  the  neural  basis  of  cognition  and  behavior 
during early development, as well as for identifying the early markers of 
neurological disorders (Hu et al., 2022; Johnson, 2011; Seguin et al., 
2023; Wylie et al., 2014).

Source reconstruction improves cortical network analysis beyond the 
detail  that  can  be  seen  with  the  recorded  scalp  EEG  alone,  because 
volume conduction may effectively obscure the spatial specificity of the 
sensor-level  signals.  Reliable  source  reconstruction  is  sensitive  to 
interindividual variability in head anatomy (Lew et al., 2013; Wendel 
et al., 2010). This may be particularly pronounced in infants, because of 
higher skull conductivity and rapid developmental changes in the cra-
nial  anatomy  during  the  first  years  of  life.  Such  situation  calls  for 
tailored approaches of EEG source reconstruction to ensure sufficiently 
accurate  mapping  of  brain  activity  (Ermer  et  al.,  2001;  Fuchs  et  al., 
1998; Gilmore et al., 2018; McCann et al., 2019; Vanrumste et al., 2001; 
Zhang et al., 2006).

The  spatial  resolution  of  EEG,  a  critical  factor  for  source  recon-
struction,  is  significantly influenced by  the  number and  placement  of 
scalp electrodes. High-density EEG systems (Marino and Mantini, 2024) 
offer improved spatial resolution. Still, their utility may be challenged 
by practical and technical challenges, especially the need for specialized 
expertise for data collection and analysis. These issues are particularly 
pronounced in neonatal settings, where infants are often recorded as a 
part of medical care, emphasizing the need to maximize comfort and 
safety (Acharya and Acharya, 2020; Asayesh et al., 2022; Lantz et al., 
2003; Soler et al., 2022; Song et al., 2015).

This study aims to examine the impact of EEG electrode density on 
source reconstruction accuracy and cortical network mapping in infants, 
seeking an optimal balance between the recording setup and the accu-
racy of details in the network analysis. Our experience has shown that 
the recording setup is often a compromise between practical feasibility 
and  technical  ideal.  Therefore,  we  hypothesized  that  each  recording 
setup may imply a prespecified set of achievable analytic details. Thus, 
the results could provide empirical evidence to guide the optimization of 
EEG setups for neonatal populations, enhancing the utility of the exist-
ing EEG datasets and guiding future design of research protocols.

2. Methods

2.1. Overview of research methodology

The  study  used  5-minute-long  empirical  124-channel  EEG  data 
collected  during  infant  active  sleep,  which  were  subsequently  down- 
sampled into three sparser clinical sub-sets with 63/31/19 electrodes. 
All  EEG  signals  were  band-pass  filtered  into  five  commonly  used  fre-
quency bands of interest (Tokariev et al., 2022; Tokariev et al., 2019), 
and the sources were reconstructed using a realistic infant head model 
(Tokariev et al., 2019). Next, we compared cortical signals computed 
from different EEG subsets on the level of individual sources and cortical 
parcels  for  each  frequency  band.  Subsequently,  frequency-specific 
functional  brain  networks  were  assessed  by  computing  phase-phase 
correlation (PPC) and amplitude-amplitude correlation (AAC) between 
cortical  parcels.  The  local  and  global  features  of  these  networks 
computed from the sparser EEG caps were contrasted to the 124-channel 
cap used as a benchmark standard. The overall study design is shown in 
Fig. 1.

2.2. Data collection and pre-processing

The high-density EEG recordings used in this work were collected at 
Columbia  University  Medical  Center  (New  York,  USA)  as  part  of  the 
Family  Nurture  Intervention  trial  (Welch  et  al.,  2012;  Welch  et  al., 
2014).  For  this  study,  we  selected  N  = 20  infant  recordings  around 
full-term age measured during active sleep. The EEG data was initially 
recorded using a 128-electrode system produced by Electrical Geodesics 
Inc. However, four facial electrodes were excluded from further analysis, 
leading to 124 EEG channels. EEG signals were recorded from each lead 
with a vertex reference, band-pass-filtered within 0.1-400 Hz frequency 
range, and sampled at Fs = 1 kHz. After that, the data were re-referenced 
to the average montage.

From  each  EEG  recording,  we  selected  5-minute  epochs  without 
substantial  artifacts.  All  the  epochs  were  visually  inspected  to  detect 
artifacts  caused  by  loose  electrode  contacts,  electrical  interference, 
excessive muscle activity, or motion artifacts. Epochs with such anom-
alies were excluded from further analysis. The EEG data were band-pass 
filtered within a 0.4-40 Hz frequency range and then down-sampled to 
Fs = 100 Hz to optimize computational time in further analyses. The 
original 124-electrode EEG data (recorded with an EGI cap) were sub-
sampled  to  63,  31,  and  19  electrode  sets  corresponding  to  standard 
clinical caps (we used layouts for Waveguard ANT caps as a reference) 
by removing corresponding channels. Later, the pre-processed data was 

Fig. 1. Study pipeline and the analysis approaches. (A) Data acquisition using a 124 channel EEG (cap-124) and subsampling into 63 channels (cap-63), 31 
channels (cap-31), and 19 channels (cap-19). (B) Filtering EEG signals from all caps into 5 frequency bands of interest. (C) Correlations between source or parcel 
signals computed from empirical data and benchmarks using simulated activity. (D) Cortical parcellation shows the locations of parcels (nodes of the network), color- 
coded according to anatomical lobes: frontal areas – orange, central – magenta, temporal – green, and occipital – black. Functional interactions between nodes (edges 
of the network) were estimated by computing phase-phase correlations (PPC) and amplitude-amplitude correlations (AAC). (E) These networks were used to compute 
global (mean strength, modularity, and efficiency) and local (clustering coefficient and nodal strength) properties.

2 

A. Asayesh et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120932 

filtered into five different frequency bands of interest that are typically 
used in most EEG analyses (Jennekens et al., 2012; Pernet et al., 2018; 
Tokariev et al., 2019): low delta (ẟL, 0.4-1.5 Hz), high delta (ẟH, 1.5-4 
Hz), theta (θ, 4-8 Hz), alpha (α, 8-13 Hz), and beta (β, 13-22 Hz) using 
a  combination  of  low-  and  high-pass  Butterworth  filters  with  corre-
sponding cut-off frequencies.

2.3. Computing of cortical activity

We opted to use a model with a fixed orientation of the dipoles, where 
each  dipole  had  coordinates  of  the  corresponding  vertex  and  was 
orthogonal to the surface. The forward solution was computed using the 
symmetric boundary element method (Gramfort et al., 2010a), and the 
inverse  solution  was  computed  with  dynamic  Statistical  Parametric 
Mapping (Dale et al., 2000) as it is implemented in Brainstorm software 
(Tadel et al., 2011). We used an identity matrix as the noise covariance 
matrix.  After  the  reconstruction  step,  each  cortical  source  obtained  a 
5-minute-long time series for each frequency band of interest.

The pre-processed band-filtered EEG data for each cap were recon-
structed from the sensor to the source level. We used a realistic 3-shell 
head  model  (Tokariev  et  al.,  2019;  Tokariev  et  al.,  2016)  generated 
from full-term infant magnetic resonance imaging (MRI) data. The tissue 
conductivities in the model for the main compartments were set to the 
following values: 0.43 S/m for the scalp, 0.2 S/m for the skull, and 1.79 
S/m  for  intracranial volume  (Despotovic et  al., 2013;  Odabaee et  al., 
2014). Electrodes for 19/31/63/124-channel caps were placed on the 
surface  of  the  scalp according  to  the  International 10-20  system. The 
cortical surface that comprised 8014 vertices was used as a source space. 

2.4. Evaluation of source reconstruction fidelity

To  estimate  the  fidelity  of  63/31/19-channel  caps  for  the  recon-
struction  of  cortical  activity  at  the  level  of  individual  sources,  we 
correlated (Pearson test) corresponding source signals with the results 
from the 124-channel cap, which was taken as a benchmark standard 
(Fig.  2A).  Next,  to  assess  the  performance  of  the  caps  for  the  recon-
struction of parcel-level signals, we first clustered all sources into N = 58 
regions using infant  parcellation scheme (Tokariev et al., 2019). This 

Fig. 2. Reconstruction quality maps at the level of individual sources and parcels. A, The average (across subjects) correlation coefficients between the source- 
level signals for cap-63, cap-31, and cap-19 versus cap-124. B, The average correlation coefficients between parcel signals (computed using the collapse operator) for 
cap-63, cap-31, and cap-19 versus cap-124. C, Spatial distribution of normalized collapse operator weights for different caps. The weights were computed as cor-
relations  between  simulated  cortical  source  signals  and  the  corresponding  reconstructed  signals  after  forward-inverse  modelling.  They  were  further  normalized 
within each parcel by dividing by the maximum of their absolute values. Dark colors show sources that contribute most to the signal of the ʹhostʹ parcel. A similarity 
index (SI) was computed as the correlation between whole maps for cap-19, cap-31, and cap-63 versus cap-124 (reference): SI (19-124) = 0.64; SI (31-124) = 0.8; SI 
(63-124) = 0.94.

3 

A. Asayesh et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120932 

scheme  was  initially  developed  to  compute  infant  cortical  networks 
from low-density clinical EEG setups. The locations of the parcels were 
aligned relative to the standard electrode positions and anatomical brain 
lobes. The sizes of the parcels (125 ± 26 sources; mean ± STD) were 
optimized to ensure a balance between the reliability of parcel signal 
reconstruction and spatial resolution. We computed parcel signals as the 
weighted mean of the underlying sources (Tokariev et al., 2019). Source 
weights  (collapse  operators)  were  obtained  from  simulations  where 
generated  cortical  signals  were  correlated  with  their  copies  after  the 
forward-inverse transform (Tokariev et al., 2019) using the head model 
with the defined electrode subset. Similar to the source-level test, parcel 
signals  from  subsampled  models  were  correlated  with  parcel  signals 
obtained  using  the  124-channel  cap.  Correlation  coefficients  were 
averaged across the group (Fig. 2B). Finally, to define the sources that 
contain  the  most  reliable  information  for  each  parcel,  we  computed 
normalized  collapse  operator  weights for  each  parcel,  where  the  best 
sources have weights ±1 and the worst are close to zero (Fig. 2C).

2.5. Computation of the functional connectivity

Further,  we  computed  functional  interactions  between  all  pairs  of 
cortical  parcels  for  two  intrinsic  brain  communication  modes:  phase- 
phase  correlation  (PPC)  and  amplitude-amplitude  correlation  (AAC). 
As  a  measure  of  PPC,  we  used  a  debiased  weighted  phase  lag  index 
(dwPLI) (Vinck et al., 2011) because it is robust to volume conduction 
effects (Cohen, 2015; Palva et al., 2018; Palva and Palva, 2012). In turn, 
to assess AAC, we computed Pearson correlation coefficients between 
amplitude envelopes of mutually orthogonalized signals (oCC) (Brookes 

et  al.,  2012;  Hipp  et  al.,  2012).  Orthogonalization  was  done  in  both 
directions: signal X relative to signal Y and vice versa. Envelopes were 
computed using the Hilbert transform. Two oCC values for the same pair 
of  signals  were  averaged  for  further  analysis.  For  contrast,  we  also 
computed AAC networks without the orthogonalization step to test how 
volume  conduction  influences  the  network  properties  computed  from 
different  caps  (see  Supplemental  Information).  PPC  and  AAC  connec-
tivity networks were calculated separately for different combinations of 
caps and frequencies. Each parcel was considered a network node, and 
the PPC or AAC interaction strength was an edge of the network.

2.6. Comparison of the network features

To test the resolution of the EEG caps in mapping underlying cortical 
functional connectivity, we compared network features at three spatial 
levels:  global,  regional  (nodal),  and  individual  pairwise  interactions 
(edges). As global features, we computed mean connectivity strength, 
global efficiency, which reflects integration, and Newman’s modularity 
coefficient (Newman, 2006) which shows network segregation (Cohen 
and  D’Esposito,  2016;  Rubinov  and  Sporns,  2010;  Sporns  and  Betzel, 
2016).  These  metrics  were  computed  from  fully  connected  weighted 
networks using the Brain Connectivity Toolbox (Rubinov et al., 2009). 
They were also calculated for all four caps, both coupling modes, and 
five frequency bands. Further, we used Kruskal-Wallis test to compare 
the performance of the caps for each case (four caps per case, see Fig. 3), 
followed  by  Benjamini-Hochberg  procedure  for  multiple  comparisons 
(five frequencies per each metric).

We  tested  clustering  coefficients  and  mean  nodal  strengths 

Fig. 3. Comparison of global network properties. Plots show mean connectivity strength, modularity, and global efficiency values for each of four caps as a 
function of frequency. The upper panel corresponds to phase-phase correlation (PPC) networks, whereas the bottom panel shows amplitude-amplitude correlation 
(AAC) networks. The lines represent the average values of the corresponding metrics at each frequency across the group. The Kruskal-Wallis test was performed to 
assess whether there were differences in the global measures between any caps across frequencies. For the significantly different cases, we performed follow-up 
pairwise comparisons (Wilcoxon rank-sum test) between all combinations of EEG caps to identify which were different from the rest. EEG caps that deviate from 
the rest are marked with circles of the corresponding colour. Note that for PPC metrics, cap-19 differed from all others, while for AAC modularity, it was cap-124.

4 

A. Asayesh et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120932 

(calculated  as  the  average  of  all  connected  edges)  as  local  network 
measures. The weighted clustering coefficient measures the strength of 
interconnectivity between all neighboring brain regions to the node of 
interest. In turn, nodal strength reflects the region’s importance and role 
in the network (how strongly it is connected to the rest of the network). 
In our functional networks, each node was linked to 57 other regions. 
For this test, we used only high delta (1.5-4 Hz) and alpha (8-13 Hz) 
networks.  All  four  caps  were  compared  using  the  Kruskal-Wallis  test 
across  N  = 58  parcels,  followed  by  post  hoc  correction  with  the 
Benjamini-Hochberg method.

Finally,  we  compared  the  performance  of  the  caps  in  capturing 
network  properties  at  the  level  of  individual  edges  (or  the  ’granular’ 
level). To assess the performance of cortical activity networks, cap-124 
was used as a reference, and the networks computed from the other caps 
were compared to it across all frequency bands. We used a two-tailed 
Wilcoxon  rank-sum  test  to  compare  networks  in  an  edge-by-edge 
manner.  For  63/31/19-channel  caps,  we  measured  the  degree  of  the 
deviation  from  the  cap-124  as  the  fraction  of  significantly  different 
connections.

2.7. Analysis software

The analysis of the data was carried out using custom scripts devel-
oped in MATLAB software (Version R2021b, MathWorks, Natick, MA, 
USA)  supplemented  with  open-source  toolboxes  such  as  Brainstorm 
(Tadel  et  al.,  2019)  (http://neuroimage.usc.edu/brainstorm)  and 
openMEEG (Gramfort et al., 2010b) (http://openmeeg.github.io). The 
global and local network metrics were calculated using the Brain Con-
nectivity Toolbox (Rubinov et al., 2009) (https://sites.google.com/site/ 
bctnet).

2.8. Statistical analysis

We  used  Pearson  correlation  coefficient  to  estimate  similarity  of 
source and parcel signals between down-sampled caps versus reference 
cap-124 as well as to compare simulated versus reconstructed signals. To 
test  for  differences  in  global  and  local  network  metrics,  the  Krus-
kal–Wallis test was applied to all four caps simultaneously across each 
frequency and modality. If a significant difference was found, pairwise 
comparisons (Wilcoxon rank-sum test) were performed to compare caps. 
Finally, pairwise group differences in the individual edges of the func-
tional PPC and AAC networks were assessed using the Wilcoxon rank- 
sum test. An initial significance level was set at a p-value of less than 
0.05.  Results  from  multiple  comparisons  (N  = 5  frequency  bands  for 
global measures, N = 58 parcels for local measures, and N = 1653 for 
edges) were post hoc corrected using the Benjamini-Hochberg approach.

3. Result

Analyses  were  conducted  on  five-minute  epochs  across  five  fre-
quency bands, ranging from 0.4 to 22 Hz, from 20 subjects during active 
sleep. The source analysis for infant EEG in this research was extended 
from (Tokariev et al., 2019) and utilizes both empirical and simulated 
data across the frequency domain to evaluate the performance of EEG 
caps with different densities in mapping of cortical networks. Moreover, 
we  evaluated  the  reconstruction  performance  in  estimating  network 
features  at  different  spatial  scales  and  for  two  distinct  connectivity 
modes: phase-phase correlation (PPC) and amplitude-amplitude (AAC) 
correlation networks.

3.1. Comparison of cortical signals reconstruction quality

Our results expectedly show that the overall quality of the cortical 
source reconstruction at the level of individual sources is proportional to 
the number of recording EEG sensors (Fig. 2A). The global mean cor-
relation coefficients (across all cortical sources) between caps-19/31/63 

versus cap-124 were r = 0.64/0.71/0.80 correspondingly. However, this 
relation  was  also  region-specific,  with  the  mean  correlation  between 
sources (19/31/63 vs. 124 channels) in the four major anatomical lobes 
(see Fig. 1) equal to: frontal r = 0.31/0.44/0.62, central r = 0.31/0.4/ 
0.65, occipital r = 0.27/0.51/0.73, and temporal r = 0.22/0.47/0.57. 
The most sensitive to the spatial down-sampling of the cap were tem-
poral  and  orbitofrontal  areas  because  of  the  remoteness  of  recording 
sensors to the nasion-inion circumference line. Notably, the reduction of 
the recording electrodes to a more significant extent caused the drop in 
the quality of source reconstruction in the sulcus. This aligns with pre-
vious  studies  on  adults showing  the  importance  of  high-density  mon-
tages for reconstructing deep sources (Seeber et al., 2019).

The fidelity at the parcel level mainly depended on the scalp area 
coverage and the gyration of the underlying parcel (Fig. 2B). Weighting 
of  the  source  signals  when  computing  parcel  signals  aimed  to  rely 
mainly  on  the  good  sources  while  suppressing  bad  ones.  Thus,  the 
quality of the parcel activity was defined by the balance between good/ 
bad sources in the first place. The global mean correlation coefficients 
(across all parcels) for the 19/31/63-channel caps versus reference cap- 
124  were  r  = 0.57/0.71/0.83,  correspondingly.  The  cap-63  showed 
comparable  performance  to  cap-124,  while  the  fidelity  of  parcels 
computed from cap-19 was linked to their proximity to the sensors on 
the scalp (parcels with lower correlations were rather not beneath but 
in-between the sensors or in ’blind spots’). The distribution of normal-
ized weights in the collapse operator (Fig. 2C) within parcels indicates 
that despite the increase of electrode density and the expected signifi-
cant  improvement  in  reconstructing  individual sources,  the  spatial fi-
delity profiles of contributing sources are comparable. We computed the 
Similarity  Index  (SI)  between  cap-19,  cap-31,  and  cap-63  versus  the 
ʹgold  standardʹ  cap-124  by  correlating  the  corresponding  normalized 
collapse operators: SI (19-124) = 0.64; SI (31-124) = 0.8; SI (63-124) =
0.94. However, using more electrodes allows for a more accurate esti-
mation of signal polarity and decreases the risk of signal cancellation 
effects  (Ahlfors  et  al.,  2010;  Irimia  et  al.,  2012)  which  is  especially 
important for cortical surfaces with a higher degree of gyration.

3.2. The effect of electrode number on the representing global network 
metrics

The  analysis  of  global  PPC  network  measures  revealed  that  group 
differences  between  EEG  caps  were  frequency-dependent  (see  Fig.  3, 
upper row). Notably, significant differences (Kruskal–Wallis test) were 
observed only for the highest frequency range: at alpha-beta for mean 
connectivity strength (α: p = 0.009, pFDR = 0.023; β: p = 0.004, pFDR =
0.02) and for global efficiency (p = 0.003, pFDR = 0.008, for both fre-
quencies). In turn, modularity values between caps were different only 
in the beta frequency (β: p = 0.0014, pFDR = 0.007). Follow-up pairwise 
comparisons between caps in these bands showed that cap-19 signifi-
cantly deviated from each of the others in all cases (p < 0.025 for all 
network measures and versus all other caps; Wilcoxon rank-sum test). At 
the same time, higher-density caps (with 31/63/124 channels) showed 
no significant differences among themselves. These results suggest that 
caps  with  the  number  of  channels  ≥ 31  show  comparable  results  in 
estimation  of  global  PPC  metrics  across  the  whole  frequency  range. 
However, at the high frequencies lower-density caps (like cap-19) show 
worse performance.

In contrast, the analysis of AAC measures found almost no significant 
differences between the EEG caps (see Fig. 3, bottom row). Mean con-
nectivity strength and global efficiency did not differ across the entire 
frequency  range.  Nevertheless,  modularity  values  at  alpha  and  beta 
frequencies  showed  statistically  significant  differences  (α:  p  = 0.018, 
pFDR = 0.045; and β: p = 0.007, pFDR = 0.036; Kruskal-Wallis test). In 
case of AAC, pairwise comparison detected that it was cap-124 which 
deviated significantly from the rest of the caps (p ≤ 0.023 in alpha-beta 
range versus caps-19/31/63; Wilcoxon rank-sum test). There were no 
significant differences between any pairwise combinations of the other 

5 

A. Asayesh et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120932 

EEG  caps.  These  findings  suggest  that  global  AAC  measures  are  less 
sensitive  to  the  reduction  of  the  recording  EEG  electrodes.  However, 
AAC  networks  computed  without  the  orthogonalization  step  (and 
therefore more sensitive to volume conduction) showed robust differ-
ences between caps in strength and efficiency in the alpha-beta range 
(see  Supplementary  Fig.1).  Remarkably,  modularity  values  at  the 
highest frequencies were sensitive to the number of electrodes in both 
modalities (PPC and AAC).

3.3. The effect of electrode number on the representing local network 
metrics

Next,  we  compared  local  metrics  computed  from  all  caps  for  the 
alpha band (Fig. 4A), as it showed differences at the global level for both 
modalities. We found that PPC measures were particularly sensitive to 
the down sampling of electrodes (Fig. 4A, left). For both local clustering 

and  nodal  strength,  cap-19  showed  systematically  lower  values 
compared  to  other  caps.  The  Kruskal-Wallis  test  followed  by  FDR 
correction  revealed  that  22%  of  parcels  showed  a  difference  in  local 
clustering (p ≤ 0.01, pFDR ≤ 0.046) and 40% in nodal strength (p ≤
0.016, pFDR ≤ 0.041). Post hoc pairwise comparisons (Wilcoxon rank- 
sum  test, p  < 0.05)  between  caps-63/31/19  and  cap-124  highlighted 
that  the  major  driver  of  these  differences  was  cap-19:  17%  for  local 
clustering and 31% for nodal strength (out of N = 58 parcels). However, 
cap-63  and  cap-31  also  significantly  deviated  from  cap-124  in  nodal 
strength values for 7% and 5% of the parcels, respectively. The observed 
differences  in  PPC  local  measures  as  a  function  of  electrode  density 
uniformly affected all anatomical lobes. In turn, AAC local metrics did 
not show any statistically significant differences between caps (Fig. 4A, 
right). Notably, in the case of amplitude interactions, cap-124 showed 
lower values across most parcels compared to the other caps. In line with 
the global measures, avoiding the orthogonalization step for AAC led to 

Fig. 4. Effects of electrode density on the local network metrics. A, Comparison of the nodal properties (clustering coefficient and strength) for alpha band (8-13 
Hz) network between caps. Left side shows phase-phase correlation (PPC), while right side represents amplitude-amplitude correlation (AAC) networks. Lines depict 
the mean values across subjects computed for 58 parcels reconstructed from four caps. The colored circles on the x-axis indicate the anatomical location of each 
parcel (see Fig. 1D): frontal (orange), central (purple), temporal (green), and occipital (black). Group differences at the parcel level were assessed using the Kruskal- 
Wallis test, followed by the Benjamini-Hochberg false discovery rate (FDR) correction procedure (grey asterisks indicate rejected cases). B, Pairwise comparisons of 
all caps vs. cap-124 in representing individual edges. Group differences were estimated using a two-tailed Wilcoxon rank-sum test (p < 0.05) followed by FDR. The y- 
axis shows the percentage of different edges: dotted lines indicate non-corrected results, while solid lines represent FDR-corrected results. The orange lines show PPC 
networks, and blue lines – AAC networks. Note that as the frequency increases, the deviation from the cap-124 also increases in all cases with this effect being more 
pronounced for PPC networks.

6 

A. Asayesh et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120932 

strong and widespread differences in nodal measures (see Supplemen-
tary Fig. 2). We did not find any differences for PPC and orthogonalized 
AAC  networks  computed  for  high  delta  frequency  (Supplementary 
Fig. 3).

Finally,  we  compared  network  edges  between  caps-63/31/19  and 
’gold standard’ cap-124 (Wilcoxon rank-sum test). We found that both 
modalities were affected by the reduction in the number of electrodes, 
with PPC showing greater sensitivity (see Fig. 4B). Moreover, the devi-
ation  of  the  networks  computed  from  the  sparser  caps  was  also 
frequency-specific: at lower frequencies (delta-theta) deviations in FDR- 
corrected networks were negligible for all caps; however, at the highest 
frequency (beta) cap-19 showed up to 20% differences for both PPC and 
AAC.  Increasing  the  number  of  electrodes  significantly  improves  the 
situation for AAC (β: less than 3% differences for caps-63/31), but more 
pronounced deviations remain in PPC (β: 13% for cap-63 and 7% for 
cap-31). The observed differences between modalities are more likely 
because  PPC  interactions  in  the  brain  are  spatially  more  constrained 
(require high resolution for detection), while AAC communication in-
volves more widespread networks (thus more robust to electrode num-
ber). Overall, the differences at the node and edge levels are determined 
by  the  initial  fidelity  of  source  reconstruction,  which  is  mitigated  to 
some  extent  (but  not  fully  compensated)  by  the  weighting  of  sources 
within parcels. High-density montages (caps 63/31) show an acceptable 
deviation from cap-124 for computing infant cortical networks. In turn, 
cap-19 offers lower performance, and thus, cortical networks should be 
evaluated  in  terms  of  the  reliability  of  reconstructed  networks,  for 
example,  by  using  simulation-based  correction  procedures  (Tokariev 
et al., 2019).

4. Discussion

Our results, in line with adult literature, show that high-density EEG 
recordings of an infant will substantially improve the analysis of local 
cortical activity, and thereby support more detailed assessment of the 
large-scale  cortical  activity  networks  (Allouch  et  al.,  2023;  Brodbeck 
et al., 2011; Hatlestad-Hall et al., 2023; Liu et al., 2018). It is intuitively 
clear that too sparse EEG caps have larger inter-electrode distances and 
more  constrained  coverage  of  the  underlying  brain,  leading  to  many 
’blind  spots’  with  poor  quality  of  the  reconstructed  sources 
(Hatlestad-Hall et al., 2023). From another point of view, high-density 
caps  both  capture  a  certain  amount  of  redundant  information  (espe-
cially  in  the  context  of  infants)  and  are  associated  with  a  range  of 
practical issues such as electrical bridges caused by gel, difficulties in 
controlling good electrode-skin contact in all electrodes, more motion, 
and technical artifacts (Noreika et al., 2020; Stoyell et al., 2021). Our 
analysis suggests that depending on the research question and required 
resolution  (single  source  vs.  global  metrics)  of  the  analysis,  ’golden 
middle’ caps like 31/63 channels could be a quite universal solution. On 
the level of the single sources, cap-124 outperforms all the rest. How-
ever, 31/63-channel caps show comparable results only when analyzing 
nodal or global measures.

Notably, global network metrics are less affected by electrode den-
sity. We found only a significant deviation of 19-channel PPC networks 
at the highest frequencies from the rest of the caps. In turn, among global 
measures for AAC metrics, only modularity at higher frequencies was 
different  between  caps.  It  is  worth  noting  that  these  effects  are  fre-
quency- and modality-specific, meaning that high-density caps are more 
critical  for  the  reliable  analysis  of  high-frequency  networks  and  PPC 
networks. These findings align with the idea that lower frequencies can 
spread over longer distances and support interactions within large-scale 
networks, while higher frequencies are primarily associated with local 
processing (Buzs´aki and V¨or¨oslakos, 2023; Hipp et al., 2012; Moran and 
Hong,  2011;  Von  Stein  and  Sarnthein,  2000).  Thus,  denser  EEG  caps 
improve the spatial resolution of cortical mapping, allowing the capture 
of more constrained high-frequency networks and better reconstruction 
of  the  local  properties  of  global  networks.  Additionally,  comparing 

network  strengths  across  frequencies  suggests  that  lower  frequencies, 
which typically carry more signal power, are less prone to noise inter-
ference,  affirming  the  stability  of  PPC  and  AAC  at  these  frequencies 
(Engel et al., 2013; Gerner et al., 2020; Palva and Palva, 2011; Zelmann 
et al., 2014).

Shape,  number  of  sources  per  parcel,  and  relative  location  of  the 
parcels to the recording electrodes may affect the computing of cortical 
networks  (Tokariev  et  al.,  2016).  For  example,  measures  that  reflect 
network organization (like modularity) are linked to the overall quality 
of the source reconstruction (that affects individual edges). The quality 
of  the  reconstruction  of  the individual  sources  directly  influences the 
quality  of  the  parcel  signals.  The overall  fidelity  of  the  reconstructed 
sources decreases as the number of electrodes is reduced. To compensate 
for  this,  when  computing  parcel  signals,  there  could  be  different  po-
tential strategies like weighting all sources within the parcel, rejecting 
the  bad  sources  before  computing  the  parcel  signal,  or  adaptive  par-
cellation procedures (Farahibozorg et al., 2018; Korhonen et al., 2014; 
Tokariev et al., 2019).

Despite  cap-19  expectedly  showing  worse  results  than other  high- 
density caps, it remains a commonly used EEG montage in many clin-
ical applications, including infant brain monitoring. Analysis of cortical 
networks reconstructed from this cap is still possible, but after a thor-
ough check of the reliability of the reconstructed sources (Miraglia et al., 
2021). One of the potential strategies could be simulations that estimate 
the fidelity of the reconstructed sources and reject unreliable informa-
tion  in  the  ’blind  ’spots’  (Tokariev  et  al.,  2019).  Another  possible 
strategy  is  initially  using  only  cortical  parcels  below  the  recording 
electrodes. This approach will not allow estimation of the whole-brain 
network properties, but it will enable cortical-level connectivity anal-
ysis between brain areas that can be reliably reconstructed.

Our study was focused specifically on infants and the results can’t be 
directly projected onto older populations. First, inter-electrode distances 
on the scalp and their distances relative to cortical sources will increase 
with  the  growth  of  the  head.  Thus,  the  differences  in  the  fidelity  of 
cortical network mapping between electrode constellations (ʹcapsʹ) will 
become  more  pronounced.  Second,  the  geometry  of  anatomical  com-
partments (gyration of the cortex, thickness of the skull, etc.) and tissue 
conductivities  (McCann  and  Beltrachini,  2022;  Odabaee  et  al.,  2014; 
Wendel  et  al.,  2010)  will  change  substantially  during  early  develop-
ment.  This  developmental  change 
focal 
scalp-recorded EEG signal in the newborn to a spatially smeared scalp 
EEG signal seen in the older populations (Odabaee et al., 2013; Odabaee 
et  al.,  2014;  Tokariev,  Vanhatalo,  et  al.,  2016).  Third,  the  functional 
cortical networks are known to develop towards more complex organi-
zation (Cao et al., 2014; Sporns et al., 2004; Tooley et al., 2022; Wig, 
2017)  with  gradually  changing  balance  between  segregation  (local 
processing)  and  integration  (global  connectivity).  Our  present  study 
highlights  the  importance  of  considering  the  electrode  number  as  an 
essential determinant of the model as early as the newborn period, and 
this  request  becomes 
important  when  the  spatial 
complexity  of  the  network  activity  increases  with  age.  Notably,  our 
present  work  (see  also  Tokariev  et  al.,  2019)  provides  an  analytical, 
simulation-based approach for this purpose.

increasingly 

the  highly 

renders 

The present work was performed on EEG data from infants at term 
age, and the overall idea is likely to apply for preterm born infants as 
well.  However,  the  cranial  anatomy  of  the  preterm  infants  differs  in 
many ways: their head is smaller, the cortex is smoother (though gyra-
tion evolves rapidly), and their pathways of electrical conduction are 
substantially different (at least shorter). In addition, the early cortical 
activity is dominated by highly intermittent bursting activity with low- 
frequency dominance, which could suggest that high-density electrode 
constellation is redundant. However, the spatial structure of the cortical 
activity may be even higher than that of a full-term infant, and there are 
no spatial source activity models to provide an accurate modelling. A 
further  clinical  consideration  is  that  very  high-density  caps  are  less 
practical in the small preterm heads. However, longitudinal studies are 

7 

A. Asayesh et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120932 

needed  from  early  preterm  to  term  age  to  explore  these  changes 
analytically,  and  such  studies  should  preferably  include  consistent 
electrode  constellation  to  support  systematic  comparisons  across 
different ages.

In  conclusion,  the  different  tests  performed  in  this  study  of  how 
electrode configurations influence brain network analyses offer multiple 
views of employing EEG connectivity measures in infants for researchers 
and clinicians. Through comprehensive comparisons among EEG caps of 
varying densities, it is evident that higher-density caps, particularly 124- 
channel  configurations,  offer  superior  reliability  in  mapping  cortical 
networks. Despite the practical challenges associated with their appli-
cation, particularly on infants, high-density caps offer to capture deeper 
neural  sources  and  provide  valuable  insights  into  brain  activity. 
Furthermore,  the  study also highlights  a  practical equilibrium, recog-
nizing  that  mid-density  caps  (31/63  channels)  can  offer  comparable 
results  for  global  network  analyses.  However,  the  effect  of  electrode 
density on phase and amplitude correlations has been observed, indi-
cating the necessity for thoughtful electrode density selection in phase- 
related  studies,  especially  while  analyzing  the  higher  frequencies. 
Overall, these observations call for further exploration of these dynamics 
and their broader implications, marking a step forward in this field of 
research.

CRediT authorship contribution statement

Amirreza Asayesh: Writing – review &  editing, Writing –  original 
draft,  Visualization,  Validation,  Software,  Resources,  Methodology, 
Investigation,  Formal  analysis,  Data  curation.  Sampsa  Vanhatalo: 
Writing – review & editing, Project administration, Funding acquisition, 
Conceptualization. Anton Tokariev: Writing – review & editing, Vali-
dation,  Supervision,  Software,  Methodology,  Data 
curation, 
Conceptualization.

Declaration of competing interest

Authors declare no conflict of interest.

Funding

This work was supported by the European Union under the (H2020- 
EU.1.3.1)  Program  (European  Training  Networks  Funding  Scheme; 
INFANS  Project  nr.  813483)  Research  and  Innovation  Programme 
(Marie  Skłodowska-Curie  grant  agreement),  the  Finnish  Academy 
(335788, 332017), Finnish Pediatric Foundation (Lastentautiens¨a¨ati¨o), 
Aivos¨a¨ati¨o,  Sigrid  Juselius  Foundation,  and  HUS  Children’s  Hospital. 
Open access funded by Helsinki University Library.

Ethics Statement

Ethical  statement.  Infant  EEG  data  analyzed  in  this  work  were 
collected  as  part  of  a  randomized  controlled  trial  conducted  at  the 
Columbia University Medical Center. (CUMC; New York, USA). This trial 
was registered at ClinicalTrials.gov (#NCT01439269). All recruitment, 
consent,  and  study  procedures  were  preliminarily  approved  by  the 
Institutional Review Board at CUMC.

Supplementary materials

Supplementary material associated with this article can be found, in 

the online version, at doi:10.1016/j.neuroimage.2024.120932.

Data availability

The  datasets  presented  in  this  article  are  not  readily  available 
because  they  were  provided  by  a  third  party  (Columbia  University 
Medical Center, New York, USA). EEG can be made available via data 

8 

sharing agreement with Columbia University Medical Center. 

References

Acharya, V.J., Acharya, J.N., 2020. Localization with high-density EEG: complexity of 

analysis versus accuracy. Clin. Neurophysiol. Pract. 5, 10.

Ahlfors, S.P., Han, J., Lin, F.H., Witzel, T., Belliveau, J.W., H¨am¨al¨ainen, M.S., 

Halgren, E., 2010. Cancellation of EEG and MEG signals generated by extended and 
distributed sources. Hum. Brain Mapp. 31 (1), 140–149.

Allouch, S., Kabbara, A., Duprez, J., Khalil, M., Modolo, J., Hassan, M., 2023. Effect of 
channel density, inverse solutions and connectivity measures on EEG resting-state 
networks reconstruction: a simulation study. Neuroimage 271, 120006.

Asayesh, A., Ilen, E., Mets¨aranta, M., Vanhatalo, S., 2022. Developing disposable EEG cap 
for infant recordings at the neonatal intensive care unit. Sensors 22 (20), 7869.

Brodbeck, V., Spinelli, L., Lascano, A.M., Wissmeier, M., Vargas, M.-I., Vulliemoz, S., 
Pollo, C., Schaller, K., Michel, C.M., Seeck, M., 2011. Electroencephalographic 
source imaging: a prospective study of 152 operated epileptic patients. Brain 134 
(10), 2887–2897.

Brookes, M.J., Woolrich, M.W., Barnes, G.R., 2012. Measuring functional connectivity in 
MEG: a multivariate approach insensitive to linear source leakage. Neuroimage 63 
(2), 910–920.

Buzs´aki, G., V¨or¨oslakos, M., 2023. Brain rhythms have come of age. Neuron 111 (7), 

922–926.

Cao, M., Wang, J.-H., Dai, Z.-J., Cao, X.-Y., Jiang, L.-L., Fan, F.-M., Song, X.-W., Xia, M.- 
R., Shu, N., Dong, Q., 2014. Topological organization of the human brain functional 
connectome across the lifespan. Dev. Cogn. Neurosci. 7, 76–93.

Cohen, J.R., D’Esposito, M, 2016. The segregation and integration of distinct brain 

networks and their relationship to cognition. J. Neurosci. 36 (48), 12083–12094.

Cohen, M.X., 2015. Effects of time lag and frequency matching on phase-based 

connectivity. J. Neurosci. Methods 250, 137–146.

Dale, A.M., Liu, A.K., Fischl, B.R., Buckner, R.L., Belliveau, J.W., Lewine, J.D., 

Halgren, E., 2000. Dynamic statistical parametric mapping: combining fMRI and 
MEG for high-resolution imaging of cortical activity. Neuron 26 (1), 55–67.
Despotovic, I., Cherian, P.J., De Vos, M., Hallez, H., Deburchgraeve, W., Govaert, P., 

Lequin, M., Visser, G.H., Swarte, R.M., Vansteenkiste, E., 2013. Relationship of EEG 
sources of neonatal seizures to acute perinatal brain lesions seen on MRI: a pilot 
study. Hum. Brain Mapp. 34 (10), 2402–2417.

Engel, A.K., Gerloff, C., Hilgetag, C.C., Nolte, G., 2013. Intrinsic coupling modes: 
multiscale interactions in ongoing brain activity. Neuron 80 (4), 867–886.
Ermer, J.J., Mosher, J.C., Baillet, S., Leahy, R.M., 2001. Rapidly recomputable EEG 

forward models for realistic head shapes. Phys. Med. Biol. 46 (4), 1265.

Farahibozorg, S.-R., Henson, R.N., Hauk, O., 2018. Adaptive cortical parcellations for 

source reconstructed EEG/MEG connectomes. Neuroimage 169, 23–45.

França, L.G., Ciarrusta, J., Gale-Grant, O., Fenn-Moltu, S., Fitzgibbon, S., Chew, A., 

Falconer, S., Dimitrova, R., Cordero-Grande, L., Price, A.N., 2024. Neonatal brain 
dynamic functional connectivity in term and preterm infants and its association with 
early childhood neurodevelopment. Nat. Commun. 15 (1), 16.

Fuchs, M., Drenckhahn, R., Wischmann, H., Wagner, M., 1998. An improved boundary 
element method for realistic volume-conductor modeling. IEEE Trans. Biomed. Eng. 
45 (8), 980–997.

Gerner, N., Thomschewski, A., Marcu, A., Trinka, E., H¨oller, Y., 2020. Pitfalls in scalp 
high-frequency oscillation detection from long-term EEG monitoring. Front. Neurol. 
11, 432.

Gilmore, J.H., Knickmeyer, R.C., Gao, W., 2018. Imaging structural and functional brain 

development in early childhood. Nature Rev. Neurosci. 19 (3), 123–137.
Gramfort, A., Papadopoulo, T., Olivi, E., Clerc, M., 2010a. OpenMEEG: opensource 
software for quasistatic bioelectromagnetics. Biomed. Eng. Online 9, 1–20.
Gramfort, A., Papadopoulo, T., Olivi, E., Clerc, M., 2010b. OpenMEEG: opensource 

software for quasistatic bioelectromagnetics. Biomed. Eng. Online 9 (1), 45. https:// 
doi.org/10.1186/1475-925X-9-45.

Hatlestad-Hall, C., Bru˜na, R., Liljestr¨om, M., Renvall, H., Heuser, K., Taubøll, E., 

Maestú, F., Haraldsen, I.H., 2023. Reliable evaluation of functional connectivity and 
graph theory measures in source-level EEG: How many electrodes are enough? Clin. 
Neurophysiol. 150, 1–16.

Hipp, J.F., Hawellek, D.J., Corbetta, M., Siegel, M., Engel, A.K., 2012. Large-scale 

cortical correlation structure of spontaneous oscillatory activity. Nat. Neurosci. 15 
(6), 884–890.

Hu, D.K., Goetz, P.W., To, P.D., Garner, C., Magers, A.L., Skora, C., Tran, N., Yuen, T., 
Hussain, S.A., Shrey, D.W., 2022. Evolution of Cortical Functional Networks in 
Healthy Infants. Front. Netw. Physiol. 2, 893826.

Irimia, A., Van Horn, J.D., Halgren, E., 2012. Source cancellation profiles of 

electroencephalography and magnetoencephalography. Neuroimage 59 (3), 
2464–2474.

Jennekens, W., Niemarkt, H.J., Engels, M., Pasman, J.W., van Pul, C., Andriessen, P., 
2012. Topography of maturational changes in EEG burst spectral power of the 
preterm infant with a normal follow-up at 2 years of age. Clin. Neurophysiol. 123 
(11), 2130–2138.

Johnson, M.H., 2011. Interactive specialization: a domain-general framework for human 

functional brain development? Dev. Cogn. Neurosci. 1 (1), 7–21.

Karolis, V.R., Fitzgibbon, S.P., Cordero-Grande, L., Farahibozorg, S.-R., Price, A.N., 

Hughes, E.J., Fetit, A.E., Kyriakopoulou, V., Pietsch, M., Rutherford, M.A., 2023. 
Maturational networks of human fetal brain activity reveal emerging connectivity 
patterns prior to ex-utero exposure. Commun. Biol. 6 (1), 661.

Keunen, K., Counsell, S.J., Benders, M.J., 2017. The emergence of functional architecture 

during early brain development. Neuroimage 160, 2–14.

A. Asayesh et al.                                                                                                                                                                                                                                

NeuroImage 303 (2024) 120932 

Korhonen, O., Palva, S., Palva, J.M., 2014. Sparse weightings for collapsing inverse 

solutions to cortical parcellations optimize M/EEG source reconstruction accuracy. 
J. Neurosci. Methods 226, 147–160.

Kostovi´c, I., Radoˇs, M., Kostovi´c-Srzenti´c, M., Krsnik, ˇZ., 2021. Fundamentals of the 
development of connectivity in the human fetal brain in late gestation: from 24 
weeks gestational age to term. J. Neuropathol. Experiment. Neurol. 80 (5), 393–414.

Lantz, G., De Peralta, R.G., Spinelli, L., Seeck, M., Michel, C., 2003. Epileptic source 
localization with high density EEG: how many electrodes are needed? Clin. 
Neurophysiol. 114 (1), 63–69.

Lew, S., Sliva, D.D., Choe, M.-s., Grant, P.E., Okada, Y., Wolters, C.H., H¨am¨al¨ainen, M.S., 
2013. Effects of sutures and fontanels on MEG and EEG source analysis in a realistic 
infant head model. Neuroimage 76, 282–293.

Liu, Q., Ganzetti, M., Wenderoth, N., Mantini, D., 2018. Detecting large-scale brain 
networks using EEG: Impact of electrode density, head modeling and source 
localization. Front. Neuroinform. 12, 4.

Marino, M., Mantini, D., 2024. Human brain imaging with high-density 
electroencephalography: techniques and applications. J. Physiol.

channel subsets. In: Proceedings of the 15th International Joint Conference on 
Biomedical Engineering Systems and Technologies (BIOSTEC 2022)-Volume 1.
Song, J., Davey, C., Poulsen, C., Luu, P., Turovets, S., Anderson, E., Li, K., Tucker, D., 

2015. EEG source localization: sensor density and head surface coverage. 
J. Neurosci. Methods 256, 9–21.

Sporns, O., Betzel, R.F., 2016. Modular brain networks. Annu. Rev. Psychol. 67, 

613–640.

Sporns, O., Chialvo, D.R., Kaiser, M., Hilgetag, C.C., 2004. Organization, development 
and function of complex brain networks. Trends. Cogn. Sci. 8 (9), 418–425.

Stoyell, S.M., Wilmskoetter, J., Dobrota, M.-A., Chinappen, D.M., Bonilha, L., Mintz, M., 
Brinkmann, B.H., Herman, S.T., Peters, J.M., Vulliemoz, S., 2021. High-density EEG 
in current clinical practice and opportunities for the future. J. Clin. Neurophysiol. 38 
(2), 112–123.

Tadel, F., Baillet, S., Mosher, J.C., Pantazis, D., Leahy, R.M., 2011. Brainstorm: a user- 

friendly application for MEG/EEG analysis. Comput. Intell. Neurosci. 2011, 1–13.
Tadel, F., Bock, E., Niso, G., Mosher, J.C., Cousineau, M., Pantazis, D., Leahy, R.M., 
Baillet, S., 2019. MEG/EEG group analysis with brainstorm. Front. Neurosci. 76.

McCann, H., Beltrachini, L., 2022. Impact of skull sutures, spongiform bone distribution, 
and aging skull conductivities on the EEG forward and inverse problems. J. Neural 
Eng. 19 (1), 016014.

Tokariev, A., Breakspear, M., Videman, M., Stjerna, S., Scholtens, L.H., Van Den 
Heuvel, M.P., Cocchi, L., Vanhatalo, S, 2022. Impact of in utero exposure to 
antiepileptic drugs on neonatal brain function. Cerebral Cortex 32 (11), 2385–2397.

McCann, H., Pisano, G., Beltrachini, L., 2019. Variation in reported human head tissue 

Tokariev, A., Roberts, J.A., Zalesky, A., Zhao, X., Vanhatalo, S., Breakspear, M., 

electrical conductivity values. Brain Topogr. 32, 825–858.

Michel, C.M., Brunet, D., 2019. EEG source imaging: a practical review of the analysis 

steps. Front. Neurol. 10, 325.

Michel, C.M., He, B., 2019. EEG source localization. Handb. Clin. Neurol. 160, 85–101.
Miraglia, F., Tomino, C., Vecchio, F., Alù, F., Orticoni, A., Judica, E., Cotelli, M., 

Rossini, P.M., 2021. Assessing the dependence of the number of EEG channels in the 
brain networks’ modulations. Brain Res. Bull. 167, 33–36.

Moran, L.V., Hong, L.E., 2011. High vs low frequency neural oscillations in 

schizophrenia. Schizophr. Bull. 37 (4), 659–663.

Newman, M.E., 2006. Modularity and community structure in networks. Proc. Nat. Acad. 

Sci. 103 (23), 8577–8582.

Noreika, V., Georgieva, S., Wass, S., Leong, V., 2020. 14 challenges and their solutions 
for conducting social neuroscience and longitudinal EEG research with infants. 
Infant Behav. Develop. 58, 101393.

Odabaee, M., Freeman, W.J., Colditz, P.B., Ramon, C., Vanhatalo, S., 2013. Spatial 

patterning of the neonatal EEG suggests a need for a high number of electrodes. 
Neuroimage 68, 229–235. https://doi.org/10.1016/j.neuroimage.2012.11.062.

Odabaee, M., Tokariev, A., Layeghy, S., Mesbah, M., Colditz, P.B., Ramon, C., 
Vanhatalo, S., 2014. Neonatal EEG at scalp is focal and implies high skull 
conductivity in realistic neonatal head models. Neuroimage 96, 73–80.

Omidvarnia, A., Fransson, P., Mets¨aranta, M., Vanhatalo, S., 2014. Functional bimodality 
in the brain networks of preterm and term human newborns. Cerebral Cortex 24 
(10), 2657–2668.

Palva, J.M., Palva, S., 2011. Roles of multiscale brain activity fluctuations in shaping the 
variability and dynamics of psychophysical performance. Prog. Brain Res. 193, 
335–350.

Palva, J.M., Wang, S.H., Palva, S., Zhigalov, A., Monto, S., Brookes, M.J., Schoffelen, J.- 
M., Jerbi, K., 2018. Ghost interactions in MEG/EEG source space: A note of caution 
on inter-areal coupling measures. Neuroimage 173, 632–643.

Palva, S., Palva, J.M., 2012. Discovering oscillatory interaction networks with M/EEG: 

challenges and breakthroughs. Trends. Cogn. Sci. 16 (4), 219–230.

Pernet, C., Garrido, M., Gramfort, A., Maurits, N., Michel, C. M., Pang, E., Salmelin, R., 
Schoffelen, J. M., Valdes-Sosa, P. A., & Puce, A. (2018). Best practices in data 
analysis and sharing in neuroimaging using MEEG.

Rubinov, M., K¨otter, R., Hagmann, P., Sporns, O., 2009. Brain connectivity toolbox: a 
collection of complex network measurements and brain connectivity datasets. 
Neuroimage 47, S169.

Rubinov, M., Sporns, O., 2010. Complex network measures of brain connectivity: uses 

and interpretations. Neuroimage 52 (3), 1059–1069.

Cocchi, L., 2019. Large-scale brain modes reorganize between infant sleep states and 
carry prognostic information for preterms. Nat. Commun. 10 (1), 2619.

Tokariev, A., Stjerna, S., Lano, A., Mets¨aranta, M., Palva, J.M., Vanhatalo, S., 2019. 

Preterm birth changes networks of newborn cortical activity. Cerebral Cortex 29 (2), 
814–826.

Tokariev, A., Vanhatalo, S., Palva, J.M., 2016. Analysis of infant cortical synchrony is 

constrained by the number of recording electrodes and the recording montage. Clin. 
Neurophysiol. 127 (1), 310–323.

Tokariev, A., Videman, M., Palva, J.M., Vanhatalo, S., 2016. Functional brain 

connectivity develops rapidly around term age and changes between vigilance states 
in the human newborn. Cerebral Cortex 26 (12), 4540–4550.

Tooley, U.A., Park, A.T., Leonard, J.A., Boroshok, A.L., McDermott, C.L., Tisdall, M.D., 
Bassett, D.S., Mackey, A.P., 2022. The age of reason: functional brain network 
development during childhood. J. Neurosci. 42 (44), 8237–8251.

Vanrumste, B., Van Hoey, G., Van de Walle, R., D’Hav`e, M.R., Lemahieu, I.A., Boon, P.A., 
2001. The validation of the finite difference method and reciprocity for solving the 
inverse problem in EEG dipole source analysis. Brain Topogr. 14 (2), 83–92.
Vinck, M., Oostenveld, R., Van Wingerden, M., Battaglia, F., Pennartz, C.M., 2011. An 
improved index of phase-synchronization for electrophysiological data in the 
presence of volume-conduction, noise and sample-size bias. Neuroimage 55 (4), 
1548–1565.

Von Stein, A., Sarnthein, J., 2000. Different frequencies for different scales of cortical 
integration: from local gamma to long range alpha/theta synchronization. Int. J. 
Psychophysiol. 38 (3), 301–313.

Welch, M.G., Hofer, M.A., Brunelli, S.A., Stark, R.I., Andrews, H.F., Austin, J., Myers, M. 
M., 2012. Family nurture intervention (FNI): methods and treatment protocol of a 
randomized controlled trial in the NICU. BMC. Pediatr. 12 (1), 1–17.

Welch, M.G., Myers, M.M., Grieve, P.G., Isler, J.R., Fifer, W.P., Sahni, R., Hofer, M.A., 
Austin, J., Ludwig, R.J., Stark, R.I., 2014. Electroencephalographic activity of 
preterm infants is increased by Family Nurture Intervention: a randomized 
controlled trial in the NICU. Clin. Neurophysiol. 125 (4), 675–684.

Wendel, K., V¨ais¨anen, J., Seemann, G., Hyttinen, J., Malmivuo, J., 2010. The influence of 
age and skull conductivity on surface and subdermal bipolar EEG leads. Comput. 
Intell. Neurosci. 2010.

Wig, G.S., 2017. Segregated systems of human brain networks. Trends. Cogn. Sci. 21 

(12), 981–996.

Wylie, K.P., Rojas, D.C., Ross, R.G., Hunter, S.K., Maharajh, K., Cornier, M.-A., 

Tregellas, J.R., 2014. Reduced brain resting-state network specificity in infants 
compared with adults. Neuropsychiatr. Dis. Treat. 1349–1359.

Seeber, M., Cantonas, L.-M., Hoevels, M., Sesia, T., Visser-Vandewalle, V., Michel, C.M., 
2019. Subcortical electrophysiological activity is detectable with high-density EEG 
source imaging. Nat. Commun. 10 (1), 753.

Zelmann, R., Lina, J.-M., Schulze-Bonhage, A., Gotman, J., Jacobs, J., 2014. Scalp EEG is 
not a blur: it can see high frequency oscillations although their generators are small. 
Brain Topogr. 27, 683–704.

Seguin, C., Sporns, O., Zalesky, A., 2023. Brain network communication: concepts, 

Zhang, Y., Ding, L., van Drongelen, W., Hecox, K., Frim, D.M., He, B., 2006. A cortical 

models and applications. Nature Rev. Neurosci. 24 (9), 557–574.

Soler, A., Giraldo, E., Lundheim, L.M., Molinas Cabrera, M.M., 2022. Relevance-based 

potential imaging study from simultaneous extra-and intracranial electrical 
recordings by means of the finite element method. Neuroimage 31 (4), 1513–1524.

channel selection for EEG source reconstruction: an approach to identify low-density 

Zhao, T., Xu, Y., He, Y., 2019. Graph theoretical modeling of baby brain networks. 

Neuroimage 185, 711–727.

9 

