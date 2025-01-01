NeuroImage 303 (2024) 120937 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Review

Intermodulation frequency components in steady-state visual evoked 
potentials: Generation, characteristics and applications

Yuzhen Chen a, Jiawen Bai a, Nanlin Shi a, Yunpeng Jiang b, Xiaogang Chen c, Yixuan Ku d,*,  
Xiaorong Gao a,*
a School of Biomedical Engineering, Tsinghua University, Beijing, China
b Key Research Base of Humanities and Social Sciences of the Ministry of Education, Academy of Psychology and Behavior, Tianjin Normal University, Tianjin, China
c Institute of Biomedical Engineering, Chinese Academy of Medical Sciences and Peking Union Medical College, Tianjin, China
d Guangdong Provincial Key Laboratory of Brain Function and Disease, Center for Brain and Mental Well-Being, Department of Psychology, Sun Yat-sen University, 
Guangzhou, China

A R T I C L E  I N F O

A B S T R A C T

Keywords:
Intermodulation frequency
Steady-state visual evoked potentials
Frequency tagging
Neural integration
Brain–computer interface

The steady-state visual evoked potentials (SSVEPs), evoked by dual-frequency or multi-frequency stimulation, 
likely contains intermodulation frequency components (IMs). Visual IMs are products of nonlinear integration of 
neural signals and can be evoked by various paradigms that induce neural interaction. IMs have demonstrated 
many interesting and important characteristics in cognitive psychology, clinical neuroscience, brain–computer 
interface and other fields, and possess substantial research potential. In this paper, we first review the definition 
of IMs and summarize the stimulation paradigms capable of inducing them, along with the possible neural or-
igins of IMs. Subsequently, we describe the characteristics and derived applications of IMs in previous studies, 
and then introduced three signal processing methods favored by researchers to enhance the signal-to-noise ratio 
of IMs. Finally, we summarize the characteristics of IMs, and propose several potential future research directions 
related to IMs.

1. Background and definition

Steady-state  visual  evoked  potentials  (SSVEPs)  refer  to  the  neural 
signal  generated  in  the  cerebral  cortex  in  response  to  periodic  visual 
stimulation (Ramadan and Vasilakos, 2017). In the spectrum of SSVEP, 
peaks would arise at the stimulation frequency (fundamental frequency) 
and  the  multiple  of  the  stimulation  frequency  (harmonic  frequency). 
Moreover,  when  the  stimulation  includes  multiple  frequencies,  the 
SSVEP  spectrum  may  exhibit  additional  peaks  at  the  intermodulation 
frequencies  (IMs),  as  illustrated  in  Fig.  1.  IMs,  also  known  as 
cross-modulation frequencies, are the result of linear combinations of 
multiple  input  frequencies  generated  through  the  nonlinear  neural 
integration process (Gordon et al., 2019a). In most studies, two input 
frequencies (f1 and f2) are used, and the IM can be expressed as mf1 ±
nf2, where m and n are generally positive integers. The sum of m and n 
represents the order of the IM.

As  a  representative  indicator  of  neural  interactions,  IMs  play  a 
crucial  role  in  various  fields  of  neuroscience,  such  as  cognitive 

neuroscience,  clinical  neuroscience,  and  brain-computer  interfaces 
(BCIs). Previous studies have reviewed and summarized the research on 
IMs  from  the  perspective  of  human  sensory  and  cognitive  processing 
(Gordon  et  al.,  2019a;  Norcia  et  al.,  2015).  In  order  to  facilitate  the 
utilization of IMs in experiment design and paradigm development, this 
paper  presents  a  comprehensive  review  and  discussion  of  the  mecha-
nisms and applications of IMs, drawing from research conducted over 
the past fifteen years. Specifically, we begin by categorizing the para-
digms capable of evoking IMs and providing a macroscopic description 
of the neural mechanisms underlying IMs. Furthermore, we separately 
discuss the frequency tagging modality and the selection of stimulation 
frequencies. Next, we organize and summarize several properties of IMs. 
Compared to previous studies, we focus additionally on the application 
of IMs in clinical neuroscience and BCI. Additionally, we introduce three 
efficient signal-processing methods that aim to enhance the SNR of IMs. 
Finally, we summarize the generation and properties of IMs and propose 
potential research directions.

* Corresponding author.

E-mail addresses: chenyz20@tsinghua.org.cn (Y. Chen), baijw20@gmail.com (J. Bai), shinl.thu@gmail.com (N. Shi), jiangyp@tjnu.edu.cn (Y. Jiang), chenxg@ 

bme.cams.cn (X. Chen), kuyixuan@mail.sysu.edu.cn (Y. Ku), gxr-dea@mail.tsinghua.edu.cn (X. Gao). 

https://doi.org/10.1016/j.neuroimage.2024.120937
Received 30 August 2024; Received in revised form 7 November 2024; Accepted 14 November 2024  
Available online 15 November 2024 
1053-8119/© 2024 The Authors. Published by Elsevier Inc. This is an open access article under the CC BY-NC-ND license ( http://creativecommons.org/licenses/by- 
nc-nd/4.0/ ). 

Y. Chen et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120937 

Fig. 1. Generation of the visual IMs.

2. Generation

2.1. Simulation

Gordon et al. (2019a) utilized computer simulations to investigate 
the  generation  principles  of  IMs.  The  simulations  demonstrated  that 
applying nonlinear processing, specifically half-wave rectification, to a 
single input frequency (f1) generates harmonics (mf1). Additionally, the 
linear processing of two square wave signals also induces the generation 
of  harmonic  components.  Nonlinear  interactions  between  two  input 
frequencies  give  rise  to  the  generation  of  IMs,  with  the  specific  com-
ponents  of  the  nonlinear  response,  such  as  higher-order  IMs,  varying 
depending on the type and order of the applied nonlinear operations.

Despite the differences between the simulation and the real neural 
process, the simulation results indicate that IMs can be generated by the 
interaction of two input signals. This finding provides researchers with a 
tool  to  investigate  the  interactive  function  of  the  neural  system. 
Consequently,  researchers  frequently  utilize  different  frequencies  to 
label specific stimulation elements, resulting in distinct SSVEP responses 
for  each  element  or  the  neural  integration.  This  approach,  known  as 
frequency-tagging (Srinivasan et al., 1999; Tononi et al., 1998), enables 
targeted analysis.

2.2. Paradigms

In 1984, Zemon and Ratliff introduced the superimposed and lateral 
paradigms, designed to evoke IMs and investigate nonlinear interactions 
in  the  human  visual  system  (Zemon  and  Ratliff,  1984).  In  the  super-
imposed paradigm, the contrast of all cells of the circular checkerboard 
was adjusted by summing sinusoidal signals of two frequencies, while 
the lateral paradigm employed different frequencies in distinct regions. 
Zemon and Ratliff (1984) concluded that the dual sinusoidal stimulation 
technique had significant potential in uncovering various properties of 
the human visual system. Their pioneering work established the foun-
dation for subsequent extensive research in IMs.

With  the  advancement  of  display  technology  and  neural  signal 
acquisition techniques, a growing variety of paradigms have shown the 
capability to induce distinct IMs. Based on the specificity of the para-
digms, IMs can capture neural integration processes at various levels, 
encompassing interactions within and between low-level, mid-level, and 
high-level visual processing (Gordon et al., 2019a). In the last fifteen 
years, studies on visual IMs have encompassed various domains, such as 
binocular rivalry, perception and consciousness, ophthalmic disorders, 
BCI,  and  others.  These  studies  employ  diverse  paradigms,  which  we 
categorize into four types based on the form and area of input signal 
interaction:  spatial  separation,  spatial  overlap,  dichoptic  vision,  and 
cross-sensory, where the first two types both belong to the situation of 
binocular  synoptic vision. Before introducing different paradigms, we 
present  a  concise  description  of  two  essential  parameters  in  these 
paradigms: 

• Frequency Tagging Method: Frequency tagging method refers to the 
presentation mode to deliver the periodic stimulation, such as the 
“on/off”  mode (the target flickering on and off at a periodic rate), 
contrast  reversal  mode  (the  target  and  the  background  flickering 
conversely  at  a  periodic  rate),  and  sinusoidal  modulation  (the 
luminance  of  the  target  varies  in  a  sine  curve  of  a  frequency). 

Moreover, novel approaches have been developed to generate fre-
quency information in the stimulation, such as target motion, texture 
variations, and pattern changes, among others (Aissani et al., 2011; 
Appelbaum et al., 2008; Davidson et al., 2020; Fesi et al., 2014; Li 
et  al.,  2023;  Pitchaimuthu  et  al.,  2021;  Zhang  et  al.,  2017).  It  is 
important to note that a wide range of conditions can elicit SSVEP in 
the brain. When the information of the stimulation target, such as 
luminance, contrast, color, orientation, location, etc., changes peri-
odically,  the  brain  may  generate  a  periodic  steady-state  response. 
Norcia et al. used the term “periodic visual inputs” to describe visual 
stimulation that induces SSVEP (Norcia et al., 2015).

• Stimulation Frequency Selection: The selection of stimulation fre-
quency  is  crucial  for  studying  IMs  since  the  SSVEP  response  is 
modulated  by  frequency,  manifested  as  the  SSEVP  response 
increasing near 10 Hz and decreasing away from 10 Hz (Ding et al., 
2006; Herrmann et al., 2001; Pastor et al., 2003; Shi et al., 2024; 
Srinivasan et al., 2006; Vialatte et al., 2010). If the stimulation fre-
quency is selected inappropriately, the strength of the fundamental 
frequency,  harmonics,  and  IMs  may  decrease.  However,  though 
some studies on IMs suggest that the selected frequencies and their 
IMs should be outside the alpha band (Mersad and Caristan, 2021), a 
specific  criterion  for  frequency  selection  for  IMs  research  is  still 
lacking. Fig. 2 illustrates the combinations of stimulation frequencies 
(averaged  if  multiple  frequencies  were  used)  and  the  analyzed 
components of IMs studied in the last fifteen years (specific values 
can be found in Table S1 in Supplementary Materials). The distri-
bution of stimulation frequencies spans from 0.2 Hz to 65 Hz, with 
frequencies around 7 Hz frequently employed. The analysis primar-
ily focuses on the second-order component of IMs (f1 ± f2), with a 
comparable number of studies examining only sum terms, only dif-
ference terms, or both. 

Although some studies have suggested that the sum and difference 
of  input  frequencies  reflect  differences  arising  from  the  nonlinear 
neural  processing  of  the  input  information  filtering,  and  the  inte-
gration  and  detection  of  low-level  features  (e.g.,  boundaries  and 
contours) are reflected in the sum term while the integration of in-
dividual stimulation into a whole may be signaled at the difference 
term  (lower  frequencies)  (Boremanse  et  al.,  2013,  2014),  more 
detailed descriptions or evidence on the physiological mechanisms of 
the difference and sum term IMs and their different orders are still 
lacking. Therefore, some studies have considered multiple IMs (sum 
and difference terms, lower and higher orders) simultaneously, such 

Fig. 2. The frequency combinations in the studies involving IMs. The coordi-
nate axis represents two stimulus frequencies (averaged if multiple frequencies 
were used). The gray dash line is equifrequency.

2 

Y. Chen et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120937 

as summing or averaging multiple IMs responses (Alp et al., 2018; 
Boremanse  et  al.,  2014;  Katyal  et  al.,  2016;  Vergeer  et  al.,  2018; 
Zhang et al., 2011). Due to the lack of clarity regarding the physio-
logical mechanisms involved in the production of IMs, it is suggested 
to explore multiple frequency combinations in preliminary experi-
ments and analyze various orders and combinations of IMs.

The following paradigms capable of inducing IMs, shown schemati-
cally in Fig. 3, are described individually. These paradigms are catego-
rized  into  two  broad  groups  based  on  whether  they  are  presented 
binocularly  or  dichoptically  and 
involve  cross-sensory 
processing.

if  they 

2.2.1. Binocular synoptic vision

The binocular synoptic vision paradigm involves both eyes simulta-
neously perceiving the same visual stimuli within the same visual field, 
and it can be further classified based on the distinct methods encoding 
spatial information.

(1). Spatial Overlap: The spatial overlap paradigm refers to a sce-
nario where two input frequencies jointly tag the same stimulation re-
gion. As shown in Fig. 3(a), in this paradigm, the two frequency inputs 
overlap  spatially,  corresponding  to  the  aforementioned  overlap  para-
digm proposed by Zemon and Ratliff (1984). When the two frequencies 
are  presented  simultaneously  and  temporally  congruent,  they  are 
generally presented with different tagging methods, such as luminance 
and  shape  (Giani  et  al.,  2012;  Li  et  al.,  2023),  color  and  luminance 
(Pitchaimuthu et al., 2021), orientation and location (Fesi et al., 2014; 
Thomas  et  al.,  2014),  expansion  and  contraction  movements  (Zhang 
et al., 2017), and the flickering and grasping motion imagery (Chi et al., 
2022).  Different  frequency  tagging  modalities  allow  for  studying  the 
interaction  of  different  pathways  and  regions 
integration  and 

corresponding to different visual stimulation types. Specifically, changes 
in shape and motion can be used to investigate potential interactions 
between  ventral  and  dorsal  pathways,  and  SSVEP  semantic 
wavelet-induced frequency tagging (SWIFT) can be employed to study 
interactions  between  low  and  high  levels  of  cortical  activity  (Gordon 
et al., 2017).

The  two  frequencies  in  the  spatial  overlap  paradigm  can  also  be 
output asynchronously. Due to the introduction of time variables, the 
tagging modality of the two frequencies is typically kept consistent to 
avoid introducing additional interference. Baker et al. (2011) employed 
this  paradigm  to  study  the  directional  tuning  of  the  visual  cortex  by 
presenting interlaced frames with gratings in two different orientations; 
Tsai et al. (2012) utilized this paradigm to study visual masking phe-
nomena by interlacing video lines with two random noise patterns of 
different contrasts; Alp and Ozkan (2022) used odd frames to present 
stimulation of one frequency and even frames to present stimulation of 
another. Alp and Ozkan (2022) rearranged the frame sequence of the 
stimulation video to study the neural correlation of time integration in 
dynamic facial perception. Their results showed that IMs could only be 
generated  by  continuously  processing  even  and  odd  frames  and  per-
forming time integration.

(2). Spatial Separation: The spatial separation paradigm refers to 
the condition that the two input frequencies mark different regions in 
the  stimulation.  As  shown  in  Fig.  3(b),  the  two  frequencies  of  this 
paradigm are arranged in a spatially separated manner, with each pixel 
in  the  stimulation  providing  information  for  only  one  frequency 
throughout  the  entire  duration.  This  arrangement  corresponds  to  the 
aforementioned lateral paradigm proposed by Zemon and Ratliff (1984). 
Since the spatial regions of the two frequencies are different, introducing 
the variable of space, the variable of time of the two frequencies tends to 
be the same.

Fig. 3. Paradigms capable of evoking IMs. (a) Spatial overlap and (b) Spatial separation paradigms under binocular synoptic vision. (c) Dichoptic vision paradigms. 
(d) Cross sensory paradigms.

3 

Y. Chen et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120937 

The stimulation of the two frequencies is symmetrically distributed 
and  of  the  same  tagging  modality  (e.g.,  both  frequencies  are  motion- 
modulated)  in  most  studies.  However,  there  are  also  instances  of 
asymmetrical stimulation designed to address specific study objectives. 
In certain studies, the two input frequencies were presented separately 
in the left and right hemifields (Boremanse et al., 2013, 2014; Cai et al., 
2020; Chen et al., 2022a; Faghel-Soubeyrand et al., 2017; Gundlach and 
Müller, 2013; Mersad and Caristan, 2021; Radtke et al., 2020; Vergeer 
et al., 2018), while in others, the upper and lower hemifields were uti-
lized (Files et al., 2014). During the experiment of these studies, subjects 
were instructed to maintain fixation on the center of the visual field. This 
experimental setup facilitated the separation of the left and right visual 
cortex functions, enabling a more comprehensive investigation of their 
interaction. Conversely, other studies did not strictly isolate frequencies 
within  the  visual  field,  aiming  to  examine  the  perceptual  integration 
across the visual pathway.

2.2.2. Dichoptic vision

As shown in Fig. 3(c), the dichoptic vision paradigm involves pre-
senting  different frequencies  to  each  eye,  with  each  eye  receiving  in-
formation at only one frequency, in contrast to the binocular synoptic 
vision paradigm described above. There are various ways to implement 
the  dichoptic  vision,  including  the  use  of  polarized  glasses  with  two 
polarizing  lenses  that  receive  light  from  different  directions  from  a 
polarized display (Chen et al., 2022b, 2023; Hou et al., 2021; Sun et al., 
2022, 2024); shutter glasses that alternate stimulation frames in the left 
and right lenses (Wenzel et al., 2015); mirror stereoscopes that combine 
several reflectors to project different images to the left and right eyes 
(Katyal et al., 2016, 2018; Sutoyo and Srinivasan, 2009; Zhang et al., 
2011);  and  virtual  reality  or  augmented  reality  glasses  that  present 
different content directly on the displays of their two lenses (Koo et al., 
2015; Zhang et al., 2022). Currently, shutter glasses and extended reality 
technology have not been applied to the study of IMs, while polarized 
glasses  and  mirror  stereoscopes  are  more  commonly  used  by 
researchers.

In  the  dichoptic  vision  paradigm,  distinct  stimulation  received  by 
each eye enters the cerebral cortex through separate neural pathways 
from the retina and the dichoptic information is combined on binocular 
cells in the cerebral cortex (Norcia et al., 2015). In studies on binocular 
rivalry, the images presented to the two eyes are often different, such as 
gratings  with  different  orientations  (Bock  et  al.,  2019;  Katyal  et  al., 
2016, 2018; Sutoyo and Srinivasan, 2009), checkerboards composed of 
various  underlying  images  (Zhang  et  al.,  2011;  Gu  et  al.,  2020)  and 
dichoptic  interleaved  images  (Baker  and  Wade,  2017).  However,  in 
other fields, the dichoptic images can have the same pattern but differ in 
other parameters such as contrast (Chen et al., 2022b, 2023; Hou et al., 
2021; Sun et al., 2022, 2024).

2.2.3. Cross-sensory

As shown in Fig. 3(d), the cross-sensory paradigm utilizes two fre-
quencies to tag stimuli for two different senses, namely the visual and 
auditory  senses,  in  this  article.  Research  on  this  paradigm  is  limited. 
Giani  et  al.  used  two  frequencies  to  tag  visual  stimulation  (size-  or 
luminance-modulated)  and  auditory  stimulation  (frequency-  or 
amplitude-modulated),  and  they  found  no  IM  response  with  simulta-
neous  stimulation  on  the  two  senses  (Giani  et  al.,  2012).  However, 
Drijvers et al. (2021) and Seijdel et al. (2024) employed two frequencies 
to separately tag visual (gesture) and auditory (speech) stimulation of a 
video.  When  the  visual  and  auditory  stimulation  were  matched  (e.g., 
simultaneous presentation of the action of driving and the audio of the 
word “drive”), there was a clear IM response. These findings suggest that 
IMs can potentially reflect not only single-sensory nonlinear integration 
(Gordon  et  al.,  2019a)  but  also  cross-sensory  information  integration 
under the appropriate conditions involving cognition.

2.3. Neural origins

Different  paradigms  are  likely  to  evoke  IMs  at  different  locations. 
Physiologically,  the  spatial  overlap  and  spatial  separation  paradigms 
under binocular synoptic vision can induce IMs at the retina (Brannan 
et al., 1992; Meigen et al., 2005). IMs generated by the dichoptic vision 
paradigm  may  be  recorded  after  the  layer  IVC  of  the  primary  visual 
cortex, where information from dominant columns of the left and right 
eyes  mixes  (Bear  et  al.,  2006;  Sun  et  al.,  2024).  IMs  induced  by  the 
visual-auditory  integration  paradigms  may  occur  in  higher-level  re-
gions, such as the left inferior frontal gyrus, which is involved in the 
integration of speech and gestures (Drijvers et al., 2021; Seijdel et al., 
2024).  However,  due  to  the  recording  technique  limitations,  precise 
localization  of  IMs  might  be  challenging.  Therefore,  we  will  take  a 
macroscopic perspective and describe the possible effects of stimuli on 
the  regions  where  IMs  may  be  generated,  considering  the  types  of 
recording methods.

Studies on visual IMs primarily employ non-invasive electrophysio-
logical methods, such as electroencephalography (EEG) and magneto-
encephalography  (MEG), 
the  relatively  macroscopic 
to  record 
electrophysiological features of the brain. These studies may also sup-
plement  the  electrophysiological  data  with  imaging  techniques  or 
source localization methods to understand the brain regions where IMs 
are  generated.  Based  on  the  results  of  scalp  EEG,  IMs  predominantly 
occur in the occipital lobe or extend towards the temporal and parietal 
lobes (Appelbaum et al., 2008; Vergeer et al., 2018), which is consistent 
with the location of scalp mapping of the visual cortex. Interestingly, IMs 
for facial integration and Chinese character integration are right- and 
left-lateralized in the topography of EEG, respectively (Boremanse et al., 
2014; Cai et al., 2020), while IMs arising from the integration of hem-
ifoveal information under dichoptic vision involve a wider range of re-
gions, such as central and frontal regions (Sutoyo and Srinivasan, 2009).
In terms of source localization, researchers primarily traced the ac-
tivity  of  IMs  in  the  relevant  areas  of  the  visual  cortex,  especially  the 
primary  visual cortex  (V1).  However,  growing  evidence  suggests  that 
IMs may involve a broader range of cortical areas beyond V1. IM  re-
sponses are reduced in visually relevant areas (V1, V3a, hV4, hMT+) of 
strabismus  patients  (Hou  et  al.,  2021),  and  the  neural  sites  of  IMs  in 
achiasma patients are not localized in the early visual cortex (V1-V3) 
(Files et al., 2014). Binocular rivalry involves a specific network con-
sisting of V1, lateral occipital, posterior superior temporal sulcus, ret-
rosplenial,  and  superior  parietal  cortices  (Bock  et  al.,  2019).  IMs 
associated  with  gist  perception  are  linked  to  bilateral  temporal  lobe 
activation (Radtke et al., 2020). IMs associated with motion perception 
can be recorded in the precentral sulcus (Aissani et al., 2011). Moreover, 
IMs generated across visual and auditory sensory stimulation occur in 
the left fronto-temporal lobe (Drijvers et al., 2021; Seijdel et al., 2024).
Regarding invasive methods, an electrocorticography (ECoG) study 
discovered an attention-dependent characteristic of IMs in the frontal 
lobe, indicating that the frontal lobe could generate IMs when simulta-
neously  attending  to  the  stimulation  of  two  frequencies  (Kim  et  al., 
2017).  A  study  on  stereoelectroencephalography  (SEEG)  found  the 
activation of IMs in the temporal lobe under semantic stimulation, while 
no IMs were observed at the occipital contacts (Chen et al., 2022a).

These findings suggest that the location of IMs appears to be asso-
ciated  with  the  stimulation  type  and  the  level  of  neural  integration. 
When the elements of visual stimulation are relatively simple (such as 
the  contrast-modulated  black-and-white  flicker),  there  is  less  need  to 
recruit intermediate and high-level integrated neurons, and the location 
of IMs may be more limited (in V1). In contrast, as the stimulation be-
comes more complex, more advanced cortical functions, such as motion 
perception,  gist  perception,  and  attention  distribution,  need  to  be 
engaged.  In  such  cases,  IMs  may  be  recorded  in  regions  beyond  the 
occipital lobe and may exhibit special characteristics, such as laterality 
and task dependence. Therefore, it should be noted that compared to 
signal recording methods with higher spatial resolution, such as ECoG 

4 

Y. Chen et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120937 

and SEEG, signal recording techniques with limited spatial resolution, 
such as EEG, may integrate the contributions of multiple regions, and 
the underlying neural mechanisms may differ. Therefore, it is advisable 
to incorporate control conditions when designing experiments to pre-
vent  interference  from  multiple  sources  of  IMs.  Alternatively,  experi-
mental data can be modeled, and more advanced analytical techniques 
like multispectral phase coherence (MSPC), which analyzes the source of 
IMs  from  a  phase-driven  perspective  (Gordon  et  al.,  2019b),  can  be 
employed.

3. Characteristics and applications

IMs, as sensitive indicators of nonlinear integration of neural signals, 
have numerous applications in various studies of visual perception and 
exhibit many interesting properties. Fig. 4 schematically illustrates the 
possible  manifestations  of  IMs  in  various  paradigms.  Reviewing  the 
characteristics  and  the  derived  applications  of  IMs  demonstrated  in 
previous studies helps better understand the value of IMs in research.

3.1. Information integration under binocular synoptic vision

When  two  or  more  elements  tagged  with  different  frequencies 
generate an overall perception under specific conditions, IMs will occur 
or be enhanced compared to situations where overall perception is ab-
sent. This property of IMs is observed across diverse contexts:

3.1.1. Shape or facial integration

The intensity of IMs is closely related to the generation of illusory 
surfaces within stimuli. The perception of illusory surfaces, which could 
be induced through specific shapes and control conditions, represents an 
overall  perception  involving  feedback  loops  between  high-level  and 
low-level visual areas (Lee and Nguyen, 2001; Lee and Mumford, 2003; 
Stanley and Rubin, 2003). Gundlach and Müller (2013) presented a pair 
of circles with opposite rectangular notches in the left and right visual 
fields, respectively, and used a central circle with some removable lines 
to control the perception of an illusory rectangle surface. Similarly, Alp 
et  al.  (2016) and  Wittenhagen  et  al.  (2019) presented  four  rotatable 
three-quarters circles in each of the four quadrants of the visual stimu-
lation.  When  the  notches  on  the  circles  are  opposite  diagonally,  the 
perception of an illusory rectangle can be elicited. As shown in Fig. 4(a), 
if shapes in different visual fields are labeled with different frequencies, 
IMs  may  be  generated,  exhibiting  greater  intensity  when  the  illusory 
surface  is  perceived  (Alp  et  al.,  2016;  Gundlach  and  Müller,  2013; 
Wittenhagen et al., 2019).

Overall perception can also be modulated by the degree of binding 
between  different  elements  within  stimuli.  Aissani  et  al.  (2011)
employed two frequencies to tag the vertical movements of two hori-
zontal  rods  and  the  horizontal  movements  of  two  vertical  rods.  By 
adjusting  the  contrast  at  the  ends  of  the  rods,  they  manipulated  the 
overall  perception.  Their  findings  revealed  that  IM  responses  were 
stronger under a unified than separated motion perception. Moreover, 
shapes possessing symmetry are more readily perceived as a whole, and 

Fig. 4. Schematic diagram of IMs manifestation in (a) spatial separation paradigm, (b) spatial overlap paradigm, (c) dichoptic vision paradigm and (d) clinical 
neuroscience. “ 〈 ” or “ 〉 ” indicates the level of IMs response in the two conditions.

5 

Y. Chen et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120937 

the  type  of  symmetry  could  affect  IMs.  Alp  et  al.  (2018) found  that 
stimuli  with  both  rotational  and  reflective  symmetry  induce  stronger 
IMs than those with only rotational symmetry or no symmetry.

In addition to shapes, overall perception of faces can also induce IMs. 
Boremanse et al. (2013, 2014) found that presenting complete (Gestalt) 
facial forms increased IM responses, whereas separating a face into left 
and right halves, misaligning the halves, inverting one half, or replacing 
one half with a different face reduced the formation of IMs (Fig. 4a). 
Furthermore, Faghel-Soubeyran et al. (2017) found that IM responses 
were  stronger  when  the  integration  function  was  useful  for  the 
face-related task being performed, such as in a task to detect whether an 
eye was closed.

3.1.2. Word and Chinese character perception

Montani et al. (2019) used two frequencies to tag different syllables 
within a word. However, they found no significant IM responses, likely 
because  the  syllables  were  perceived  as  distinct  units.  In  contrast, 
Beyersmann  et  al.  (2021) used  a  similar  paradigm  to  study  the  inte-
grated  perception  of  word  stems  and  suffixes,  and  they  were  able  to 
induce  IM  responses.  Importantly,  they  found  that  words  with  true 
suffixes  evoked  IM  responses  significantly  faster  than pseudo-suffixed 
words  and  non-suffixed  words  (Fig.  4(a)).  The  difference  in  results 
may be due to the different levels of integration required for perceiving 
word stems and suffixes versus syllables within a word. Additionally, the 
high frequencies used in the study by Montani et al. (2019) may cause 
the absence of IMs.

Compared  to  English  words,  Chinese  characters  are  generally 
considered to be processed more structurally and holistically due to their 
organized visual structure. Cai et al. (2020) used two frequencies to tag 
the left and right structures of Chinese characters and found that both 
real  and  pseudo-Chinese  characters  elicited  IM  responses,  but  the  IM 
response  was  stronger  for  real  characters  (Fig.  4(a)).  In  a  follow-up 
study,  Chen  et  al.  (2022) were  able  to  classify  real  and  non-Chinese 
characters  through  the  model  based  on  the  difference  term  of  IMs 
from SEEG. These findings suggest that the comprehension of words and 
characters  relies  heavily  on  the  brain’s  integration  functions  and  IM 
responses  tend  to  be  faster  and  stronger  for  learned  or  familiar  real 
words and characters.

3.1.3. Gist and category perception

In a study related to gist perception, Radtke et al. (2020) found that 
gist-related image pairs (e.g., a wine bottle and a wine glass) elicited 
higher IM responses than unrelated image pairs (e.g., a broomstick and a 
haircut) (Fig. 4 (a)). In a separate study, Vergeer et al. (2018) marked 
the left and right sides of specific shapes with different frequencies and 
asked  participants  to  distinguish  between  different  classes  of  images. 
They found that the class of images that had been learned in advance 
elicited  stronger  high-order  IM  responses  than  those  that  were  not 
learned. This suggests that the IM responses may reflect high-level visual 
processing, such as overall shape classification.

Similarly,  Mersad  and  Caristan  (2021) found  that  presenting  two 
human  images  evoked  stronger  IM  responses  than  chair  images.  The 
authors assumed this was because the perceptual visual system tends to 
bundle the perception of spatially close people as a group. However, it is 
important to note that the sizes of the human and chair images in this 
study  may  be  different,  which  could  cause  the  response  difference. 
Overall, the strength of IM responses appears to depend on the percep-
tual familiarity with the stimuli. Images that have been learned previ-
ously or belong to a familiar class of objects with shared features are 
more likely to be perceived holistically by the visual system, resulting in 
stronger  IM  responses.  Additionally,  IMs  induced  by  human-related 
stimuli  may  be  linked  to  people’s  synchronous  activities  (Alp  et  al., 
2017) and social behaviors (Goupil et al., 2023).

3.1.4. Attention modulation

SSVEP is a useful tool for studying attention modulation. Previous 

6 

studies  have  shown  that  the  SSVEP  response  at  the  fundamental  fre-
quency  (or  harmonic)  evoked  by  the  attended  stimulus  is  enhanced 
(Muller  and  Hübner,  2002;  Walter  et  al.,  2012).  IMs  are  also  closely 
related  to  attention  and  perception,  and  differences  in  attention  allo-
cation and perception intensity may lead to various characteristics of 
IMs in different paradigms.

In the paradigm of selective attention, Kim et al. (2017) designed a 
stimulus  with  adjacent  flickering  wedges  labeled  with  different  fre-
quencies  and  static  wedges.  They  found  that  IMs  were  evoked  in  the 
frontal cortex only when two flicker wedges were both attended, sug-
gesting the dependence of the frontal integration function on selective 
attention (Fig. 4(a)). Another interesting paradigm related to attention is 
the perceptual filling-in (PFI) paradigm, in which directing attention to a 
target in the visual periphery contributes to perceptual disappearance. 
The probability of the disappearance of a target increases with attention. 
The PFI paradigm allows for the separation of the neural correlates of 
attention and perception. In a PFI study, Davidson et al. (2020) tagged 
the  target  images  and  their  background  regions  with  different  fre-
quencies and found that the IM responses temporarily peaked before the 
perceptual disappearance. This finding suggests the importance of the 
interaction between stimulation representations for the PFI and reveals 
the sensitivity of IMs to attention modulation.

3.2. Information integration under dichoptic vision

Binocular conflict arises when two different images are presented to 
each eye at the same spatial location. The visual system resolves this 
conflict  through  binocular  rivalry,  in  which  observers  consciously 
perceive spontaneous alternations between the two images (Zhang et al., 
2011).  Dichoptic  SSVEP  serves  as  a  powerful  tool  for  investigating 
binocular rivalry. In the dichoptic paradigm, researchers present grat-
ings or checkerboards of varying colors or orientations to the left and 
right eyes and utilize IMs to characterize the state of binocular rivalry.
Zhang et al. (2011) found that the rivalry mode, where images were 
simultaneously  presented  to  both  eyes,  elicited  stronger  IMs  than the 
replay  mode,  where  images  were  presented  alternately  to  each  eye. 
Additionally, IM responses were stronger during the transition than the 
dominant period and were significantly amplified in a distracting situ-
ation, where fusion perception may occur. Katyal et al. (2016) similarly 
reported  stronger  IMs  during  periods  of  fusion  perception  through  a 
paradigm  with  tilted  gratings.  Through  modeling  analysis,  they 
discovered  that  IM  responses  may  arise  from  the  combined  action  of 
binocular  integration  and  conflict  neurons.  This  modeling  result  was 
further  validated  in  their  subsequent  studies  involving  stimulation 
adaptation (Katyal et al., 2018). However, strong IM responses during 
periods of binocular fusion perception do not apply to all populations. 
Bock et al. found that the increase in IM responses from the monocular 
dominance phase to the fusion perception phase is only evident in in-
dividuals with slow switching perception (Bock et al., 2019).

The research results mentioned above indicate that IM responses can 
reflect the integration of dichoptic information. Furthermore, if images 
presented to each eye are labeled with different frequencies in the left 
and  right  visual  fields,  IM  responses  may  also  reflect  the  type  of 
dichoptic  processing.  Sutoyo  and  Srinivasan  (2009) distinguished  be-
tween left and right hemifields in dichoptic images and employed four 
frequencies to mark gratings presented at different angles within the left 
and right visual regions of the left and right eyes. They found that IMs 
were  generated  only  by  flicker  integration  in  the  complementary 
hemifields. In other words, the ipsilateral visual fields of the two eyes do 
not interact. This phenomenon appears to be associated with the extent 
of completeness in the receptive visual field, suggesting that the visual 
system has a propensity to receive stimulation encompassing the com-
plete visual field.

Y. Chen et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120937 

3.3. Masking effect

The  detectability  of  stimulation  can  be  diminished  when  other 
stimuli overlap with the same region of visual space (Legge and Foley, 
1980). This phenomenon is known as visual masking and occurs in both 
binocular synoptic and dichoptic vision paradigms. The characterization 
of visual masking is frequently achieved through SSVEP (Baker et al., 
2011, D.H. 2015; Baker and Wade, 2017; Chadnova et al., 2017; Lygo 
et al., 2021; Richard et al., 2018; Tsai et al., 2012; Zheng et al., 2019b).
Baker et al. (2011) conducted an experiment where they utilized two 
gratings with different frequencies: a test stimulus with a fixed orien-
tation and a mask stimulus with a variable orientation (Fig. 4(b)). Their 
findings revealed the influence of the relative orientation of the stimuli 
on the IM response. IM responses decrease sharply as the relative angle 
between the two gratings increased. Thus, it can be inferred that IMs are 
more  likely  to  occur  when  there  is  a  greater  similarity  in  the  spatial 
information of the two stimuli. In other words, when the visual system 
perceives  the  front  and  back  frames  of  the  stimulation  as  a  unified 
whole, temporal integration takes place.

Tsai  et  al.  (2012) investigated  the  masking  effect  through  two 
random  noise  stimuli  with  variable  contrast.  The  two  stimuli  were 
presented alternately and labeled by two distinct frequencies (Fig. 4(b)). 
They found that IMs were present when the contrasts of the two stimuli 
were equal. However, when one stimulus (mask stimulus) had greater 
contrast than the other (test stimulus), the SSVEP responses evoked by 
the test stimulus were significantly attenuated, and IMs were reduced to 
the noise level. This phenomenon, referred to as “winner-take-all,” oc-
curs due to the strong inhibition of one input by the other at a precortical 
site,  which  prevents  downstream  excitatory  interactions  (Tsai  et  al., 
2012). This implies that a stronger stimulus may mask another stimulus, 
potentially  interfering  with  the  observation  of  IMs.  Therefore,  unless 
there is a specific research objective, it is advisable to ensure that the 
strength of stimulation tagged by two different frequencies in the SSVEP 
paradigm is similar to avoid the “winner-take-all” phenomenon.

3.4. Clinical neuroscience

SSVEP, known for its high stability and signal-to-noise ratio (SNR), 
holds significant importance in clinical neuroscience research (Vialatte 
et al., 2010). It serves as a sensitive tool for detecting abnormalities in 
visual pathways, and researchers in clinical ophthalmology frequently 
utilized  SSVEP  to  assess  visual  function  such  as  visual  acuity  (Zheng 
et  al.,  2019a,  2020),  amblyopia  or  strabismus  (Baker  et  al.,  2015; 
Chadnova et al., 2017; Hu et al., 2023; Lygo et al., 2021; Zheng et al., 
2019b),  optic  glioma  (Rassi  et  al.,  2017),  visual  field  integrity 
(H´ebert-Lalonde et al., 2014), glaucoma (Nakanishi et al., 2017a), and 
other conditions. Moreover, due to its potential association with visual 
attention  and  higher  levels  of  visual  perception,  researchers  have 
employed SSVEP to investigate mental disorders such as autism (Alsagaf 
et al., 2014; Dickinson et al., 2018; Spiegel et al., 2019; Vilidaite et al., 
2018),  depression  (Moratti  et  al.,  2008;  Woody  et  al.,  2017),  anxiety 
disorder (Kastner-Dorn et al., 2018; Wieser et al., 2012), schizophrenia 
(Calderone  et  al.,  2013),  and  other  similar  conditions.  As  a  sensitive 
indicator  of  neural  interaction  under  SSVEP,  IMs  have  demonstrated 
their significance in clinical neuroscience.

3.4.1. Ophthalmology

Fig.  4(d)  demonstrates  the  potential  performance  of  IMs  in 
ophthalmic research. Specifically, in a binocular synoptic vision para-
digm,  Pitchaimuthu  et  al.  (2021) reported  that,  compared  to  the  sig-
nificant  IM  responses  observed  in  the  later  developing  cataract  and 
normal vision control groups, there was no IM response in the congenital 
cataract group. These findings suggest that the congenital cataract may 
be  associated  with  deficiencies  in  the  interaction  between  different 
pathways of visual perception. Using a dichoptic vision paradigm, Hou 
et al. (2021) found that patients with strabismus amblyopia exhibited a 

significant decrease in IM responses, and the decrease may be related to 
defects  in  stereopsis.  Furthermore,  IM  responses  have  been  shown  to 
improve after perceptual learning training for ophthalmic patients, and 
these improvements were associated with reduced binocular differences 
(Gu et al., 2020), improved binocular balance (Chen et al., 2022b), and 
reduced perceptual eye position (Chen et al., 2023).

3.4.2. Psychiatry

At present, the research on IMs in psychiatry is still relatively pre-
liminary, with only one study conducted on autism. Coll et al. (2020)
developed a hierarchical frequency tagging technique (HFT) that utilizes 
SSVEP and SWIFT to characterize bottom-up and top-down perception 
processes, respectively. By adjusting the proportion of specific images in 
SWIFT, the researchers were able to manipulate the predictability of the 
stimuli. They found that in participants with low levels of autistic traits, 
the increase in expectation resulting from the integration of top-down 
and bottom-up signals (as manifested in IM responses) was correlated 
with an increase in the predictability of the stimulation. Importantly, 
this correlation relationship diminished as the degree of autistic traits 
increased.

In summary, neurological diseases may affect the brain’s integration 
function at different levels, which can influence the performance of IMs. 
On the other hand, IM responses may serve as a potential indicator for 
quantifying  the  progression  of  diseases  related  to  neural  integration 
deficits.

3.5. Dual-frequency SSVEP-BCI

A BCI constructs a direct communication channel between the cen-
tral  nervous  system  and  a  computer  without  assistance  from  the  pe-
ripheral nervous system (Gao et al., 2021). Among numerous types of 
BCIs,  SSVEP-BCI  utilizes  the  frequency  following  effect  of  the  visual 
system to enable the selection of attended targets, thereby assisting users 
in  outputting  instructions  or  intentions.  SSVEP-BCI  based  on  single 
frequency utilizes the fundamental frequency and harmonic response of 
SSVEP or combines features from other modalities (Yin et al., 2013a, 
to  decode,  while  SSVEP-BCI  based  on 
2013b,  2014,  2015) 
dual-frequency  may  also  employ  the  information  provided  by  IMs, 
which can bring information gain to the system and have the potential to 
encode  more  targets  compared  to  the  single-frequency  SSVEP-BCI. 
Table  1 summarizes  previous  studies  on  dual-frequency  SSVEP-BCI 
involving IMs. The paradigms used in these studies span across the three 
previously summarized visual paradigms: spatial overlap (Chen et al., 
2013, 2017; Chi et al., 2022; Li et al., 2023; Zhang et al., 2017; Zhang 
et al., 2021), spatial separation (Liang et al., 2019, 2020), and dichoptic 
vision  (Sun  et  al.,  2022,  2024),  with  varying  frequency  tagging 
modality.

Although IMs have the potential to provide more information and 
improve classification performance in BCI, the individual variability and 
complex composition of IMs present challenges in the design of recog-
nition algorithms for BCIs (Liang et al., 2020; Wong et al., 2023). Some 
studies  have  adopted  canonical  correlation  analysis  (CCA;  Bin  et  al., 
2009)  and  filter  bank  CCA  (FBCCA;  Chen  et  al.,  2015)  algorithms 
without training, specifically incorporating information from IMs. Other 
studies use training algorithms such as task-related component analysis 
(TRCA; Nakanishi et al., 2017b), which may calculate personalized EEG 
patterns containing individual-specific IMs information. Currently, Sun 
et al. (2024) have achieved the best performance of a dual-frequency 
SSVEP-BCI by combining the dichoptic vision paradigm with training 
algorithms, resulting in an information transfer rate (ITR) of approxi-
mately 234 bits/min.

4. Analysis method

Similar  to  the  analysis  of  the  fundamental  or  harmonic  frequency 
responses, the analysis of IMs is also based on two dimensions: frequency 

7 

Y. Chen et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120937 

Table 1 
Studies on Dual Frequency SSVEP-BCI Involving IMs.

Study

Paradigm 
(Number of Targets)

Decoding Method

Performance 
[Accuracy (%), ITR 
(bits/min)]

Offline

Online

Chen et al. 
(2013)

Chen et al. 
(2017)

Zhang et al. 
(2017)

Liang et al. 
(2019)

Spatial Overlap: 
luminance and color 
(8)
Spatial Overlap: 
luminance and color 
(9)
Spatial Overlap: 
expansion and 
contraction (10)
Spatial Separation: 
cells of a 
checkerboard (40)

L. Liang 
et al. 
(2020)

Spatial Separation: 
cells of a 
checkerboard (40)

Zhang et al. 
(2021)
Chi et al. 
(2022)

Sun et al. 
(2022)

Li et al. 
(2023)

Spatial Overlap: 
frame and gait (4)
Spatial Overlap: 
flickering and 
grasping (2)
Dichoptic Vision: 
flickering stripes 
(40)

Spatial Overlap: 
motion and 
luminance (16)

CCA with 2nd- and 
3rd-order IMs

87 (4s), 
31* (2s)

94 (4s), 
34 (4s)

CCA with multi- 
order IMs

96 (4s), 
52 (2s)

96 (4s), 
28 (4s)

CCA with multi- 
order IMs

/

TRCA

TRCA

CCA with 2nd- and 
3rd-order IMs
FBCCA with multi- 
order IMs

TRCA

FBCCA with 2nd- 
and 3rd-order IMs

96 (6s), 
30* 
(6s)
/

96 (1s), 
196 
(1s)

/

92 (2s), 
14* 
(2s)
95* 
(2s), 
130* 
(2s)
94 
(3.5s), 
45 
(3.5s)
90 
(0.6s), 
234 
(0.6s)

95* 
(2s), 
294 
(0.3s)
91* 
(1.8s), 
245* 
(0.2s)
89 (6s), 
12* (4s)
95* 
(4s), 
15* (2s)
/

93 (5s), 
41 
(3.5s)

95 (2s), 
225 
(0.4s)

Sun et al. 
(2024)

Dichoptic Vision: 
flickering (40)

ensemble binocular 
TRCA

Training-free method: CCA, canonical correlation analysis; FBCCA, filter bank 
canonical correlation analysis. Training method: TRCA, task-related component 
analysis. ITR, information transfer rate. The asterisk (*) indicates the value is 
estimated from the graph of the study.

and time. Frequency-domain indexes typically includes the FFT ampli-
tude and phase, power spectrum amplitude, and SNR of the stimulation 
frequency. The time-domain analysis involves extracting the signal en-
velope  and  examining  its  temporal  changes.  However,  due  to  neural 
interactions,  IMs  are  sometimes  less  apparent  than  fundamental  fre-
quency responses. Thus, many studies have employed efficient methods 
to  enhance  the  SNR  of  IMs,  enabling  the  extraction  of  IMs  from  EEG 
background noise or other stimulation responses.

4.1. Adaptive recursive least square filter

Adaptive recursive least square (RLS) filters were introduced to the 
analysis of SSVEP in the 1990s (Tang and Norcia, 1995; Brown et al., 
1997). The method constructs a reference signal: 

̂y(k) = hc(k)r1(k) + hs(k)r2(k),

(1) 

En =

∑n

k=0

λn(cid:0) k[y(k) (cid:0) ̂y(k)]2

(4) 

The expression for the weights can be further simplified when the 
forgetting factor λ is close to 1, n is much larger than fs/f  and the EEG 
background signal (and noise) is not correlated with the SSVEP signal. 
Jamison et al. (2015) described the RLS filter as using a sliding window 
and a pair of sine and cosine matched filters to estimate the magnitude 
and phase of the SSVEP over time, equivalent to a short-time Fourier 
transform computed at a single frequency: 

/

hf (n) = 2

L

∑n

k=n(cid:0) L

y(k)[cos(2πkf / fs) + isin(2πkf / fs)]

(5) 

(cid:0)

)

The complex signal hf (n) can represent the amplitude A = |hf | and 
phase φ = tan
of the SSVEP of any phase, and when the phase of 
the SSVEP is constant (as it is in most applications), hf (n) can be further 
projected onto that phase.

hf

(cid:0) 1

Adaptive RLS filters are commonly used in dichoptic vision studies 
(Baker et al., 2011; Katyal et al., 2016; Zhang et al., 2011) to extract 
time-varying amplitude envelopes and analyze the time-domain char-
acteristics  of  specific  frequency  components.  The  parameter  λ  deter-
mining  the  memory  length  involves  a  trade-off  between  SNR  and 
temporal  resolution  -  a  longer  memory  can  improve  SNR  but  reduce 
temporal  resolution,  potentially  obscuring  temporal  signal  features. 
Therefore,  in  practical  applications,  it  is  important  to  adjust  the  pa-
rameters offline based on the specific analysis objectives.

4.2. Rhythmic entrainment source separation

To overcome the problems of electrode selection, small effect, and 
multi-frequency  signal  separation,  Cohen  et  al.  (2017) proposed  an 
analysis method named rhythmic entrainment source separation (RESS), 
which  has  been  adopted  by  many  teams  in  cognitive  neuroscience 
(Beyersmann  et  al., 2021;  Davidson et  al., 2020;  Mersad and  Carista, 
2021; Montani et al., 2019). RESS, aimed at improving SNR, performs an 
eigenvalue decomposition: 

(cid:0) 1SW = ΛW,
R

(6) 

where S is the covariance matrix of the signal after narrowband band-
pass filtering at a specific frequency f, and R is the covariance matrix of 
the signal after narrowband bandpass filtering at surrounding adjacent 
frequencies f ± Δf. Then W corresponding to the largest eigenvalue is 
applied  as  a  spatial  filter  on  the  original  data  matrix  to  obtain  the 
mapped one-dimensional signal.

RESS  is  highly  effective  in  enhancing  SSVEP  SNR,  even  for  weak 
responses, and separating multiple response signals with simultaneous 
multi-frequency stimulation. However, two limitations exist: First, RESS 
cannot be applied to stimuli with time-varying spatial locations; Second, 
RESS  may  result  in  overfitting  noise,  leading  to  improved  SNR  even 
without SSVEP stimulation. Additionally, Cohen et al. (2017) have made 
other suggestions, such as designing stimulation with spatial separation 
will improve the effectiveness of the spatial filter, and the frequencies 
chosen for R may need to be closer to f at lower frequencies and further 
away from f  at higher frequencies.

where hc(k) and hs(k) are the weights, and r1(k) and r2(k) are the sine 
and cosine signals corresponding to the frequency f: 

4.3. Canonical correlation analysis

r1(k) = sin(2πkf / fs)

r2(k) = cos(2πkf / fs)

(2) 

(3) 

CCA is a widely used analysis method in SSVEP-BCI (Bin et al., 2009; 
Li et al., 2011; Wong et al., 2020) that calculate the correlation between 
two variables: the EEG signal X (channel × time) and a reference signal: 

Then the weights are calculated by minimizing the error between the 

actual signal y(k) and the reference signal ̂y(k): 

Y = [sin(2πft); cos(2πft); ...; sin(2πNhft); cos(2πNhft)],

(7) 

where f is the stimulation frequency and Nh is the number of harmonics. 
CCA maximizes the correlation coefficient ρ of the linear combination 

8 

Y. Chen et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120937 

x = XTwx  and y = YTwy  by finding the weights wx  and wy: 

ρ(x, y) = maxwx, wx

√

[
wT

]

E

x XYT wT
y
̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅
]
[
]
E

y YYTwT
y

x XXTwT
x

[
E

wT

wT

(8) 

Similar to RESS, CCA utilizes a spatial filter to compress a multidi-
mensional signal into a single dimension. In contrast, CCA differs from 
RESS  in  that  it  aims  to  maximize  the  correlation  coefficient  with  the 
template signal, while RESS seeks to maximize the SNR. Furthermore, 
CCA can construct a CCA coefficient spectrum (i.e., a CCA coefficient- 
frequency curve) by modulating the frequency of the template signal. 
This  typically  results  in  peaks  at  the  stimulation  frequency,  its  har-
monics, and IMs, effectively suppressing the frequency components of 
other  non-physiological  response  signals.  Research  has  demonstrated 
the utility of CCA in applications related to visual function assessment 
(Chen et al., 2022b, 2023; Zheng et al., 2019b, 2020), and other algo-
rithms  employed  in  SSVEP-BCI  may  also  apply  to  other  research  do-
mains, such as cognitive neuroscience (Chen et al., 2024).

5. Summary and outlook

Dual-frequency or multi-frequency stimulation can evoke frequency- 
following  neural  response  signals,  where  IMs  are  responses  at  linear 
combinations  of  the  input  frequencies,  resulting  from  the  nonlinear 
integration of neural signals. A range of paradigms can evoke IMs by 
inducing  neural  interaction,  such  as  the  binocular  synoptic  vision 
paradigm,  where  both  eyes  receive  simultaneous  stimulation  at  two 
frequencies, and the dichoptic vision paradigm, where each eye is tag-
ged with a different frequency, and the cross-sensory paradigms, using 
two frequencies to tag distinct senses. Furthermore, based on the dif-
ference in spatio-temporal information of the stimulation, the binocular 
synoptic vision paradigm can be classified into the spatial overlap and 
separation  paradigms.  Regarding  neural  origins,  IMs  are  primarily 
observed in the visual cortex of the occipital region, but they may also 
extend to the temporal lobe, parietal lobe, central region, and even the 
frontal  lobe,  depending  on  the  specificity  of  the  stimulation  and  the 
experimental task.

IMs exhibit several interesting characteristics. Firstly, IM responses 
could  be  enhanced  when  different  stimulation  elements  induce  an 
overall  perception  under  binocular  synoptic  vision.  Secondly,  IM  re-
sponses  vary  with  the  perception  period  and  peak  during  fusion 
perception  under  dichoptic  vision.  Thirdly,  IMs  are  affected  by  the 
relative  orientation  of  the  target  stimulation  and  mask  stimulation. 
Additionally,  when the intensity  of one stimulus is  too strong, IM re-
sponses would decrease due to masking. Fourthly, IM response may be 
reduced under the influence of neurological diseases in clinical neuro-
science. Finally, IMs can provide additional features in dual-frequency 
SSVEP-BCI through appropriate algorithms.

Although IMs are becoming increasingly important in various fields 
as  efficient  representations of  neural  integration,  there  are  still  many 
outstanding  issues.  In  a  previous  review,  Gordon  et  al.  (2019a)
mentioned the limitations of measurement tools and analysis methods, 
as well as potential directions for development, including neuronal level 
origins,  the  relationship  with  sustained  oscillations,  individual  differ-
ences, and the causal relationship between harmonics and IMs, among 
others. These issues have yet to be extensively explored and are poised to 
remain crucial in the future. The present work poses several specific and 
important directions to guide future research on IMs: 

• An  important  direction  for  future  research  is  to  investigate  the 
physiological meanings behind the sum and difference terms of IMs 
and whether there are any differences between them. Additionally, 
the physiological meanings behind different orders and generation 
locations  of  IMs  are  also  important  issues  that  require  further 
investigation.

• The current evidence regarding the generation of IMs through sen-
sory interactions is primarily derived from studies focusing on the 
visual and auditory modalities. However, it remains unclear whether 
other modalities, such as tactile and visual sensation or tactile and 
auditory sensation, can also elicit IMs under appropriate paradigms. 
Furthermore,  if  such  interactions  occur,  the  question  arises  as  to 
where these interactions are localized within the sensory pathways.
• The exploration of IM paradigms in cognitive neuroscience contrib-
utes to the design of more efficient and natural stimuli for SSVEP- 
BCI.  Conversely,  the  development  of  algorithms  in  the  SSVEP-BCI 
aids  cognitive  neuroscience  researchers  in  extracting  IMs.  There-
fore, keeping track of the latest developments in different neurosci-
ence  fields  and  open-sourcing  codes  for  stimulus  paradigms  and 
signal-processing  algorithms  will  significantly  contribute  to  the 
advancement of IM research.

Funding

This  work  was  supported  by  the  Key-Area  Research  and  Develop-
ment Program of Guangdong Province (2018B030339001), the National 
Natural Science Foundation of China (U2241208), the Key Research and 
Development Program of Ningxia (2023BEG02063), the National Nat-
ural Science Foundation of China (32171082), the National Social Sci-
ence Foundation of China (17ZDA323), the Neuroeconomics Laboratory 
of Guangzhou Huashang College (2021WSYS002), and the Science and 
Technology 
Province 
(2023B1212060018)

Guangdong 

Planning 

Project 

of 

CRediT authorship contribution statement

Yuzhen Chen: Writing – original draft, Writing – review & editing, 
Investigation, Visualization, Conceptualization. Jiawen Bai: Writing – 
original draft. Nanlin Shi: Writing – review & editing. Yunpeng Jiang: 
Writing – review & editing. Xiaogang Chen: Writing – review & editing. 
Yixuan Ku: Writing – review &  editing, Supervision, Project adminis-
tration, Conceptualization. Xiaorong Gao: Writing – review & editing, 
Supervision, Project administration, Conceptualization.

Declaration of competing interest

The authors declare no competing interests.

Data Availability

No data was used for the research described in the article.

Supplementary materials

Supplementary material associated with this article can be found, in 

the online version, at doi:10.1016/j.neuroimage.2024.120937.

References

Aissani, C., Cottereau, B., Dumas, G., Paradis, A.L., Lorenceau, J., 2011. 

Magnetoencephalographic signatures of visual form and motion binding. Brain Res 
1408, 27–40. https://doi.org/10.1016/j.brainres.2011.05.051.

Alp, N., Kogo, N., Van Belle, G., Wagemans, J., Rossion, B., 2016. Frequency tagging 
yields an objective neural signature of Gestalt formation. Brain Cogn 104, 15–24. 
https://doi.org/10.1016/j.bandc.2016.01.008.

Alp, N., Kohler, P.J., Kogo, N., Wagemans, J., Norcia, A.M., 2018. Measuring integration 
processes in visual symmetry with frequency-tagged EEG. Sci. Rep. 8 (1), 6969. 
https://doi.org/10.1038/s41598-018-24513-w.

Alp, N., Nikolaev, A.R., Wagemans, J., Kogo, N., 2017. EEG frequency tagging dissociates 
between neural processing of motion synchrony and human quality of multiple 
point-light dancers. Sci. Rep. 7 (1), 44012. https://doi.org/10.1038/srep44012.
Alp, N., Ozkan, H., 2022. Neural correlates of integration processes during dynamic face 
perception. Sci. Rep. 12 (1), 118. https://doi.org/10.1038/s41598-021-02808-9.

Alsaggaf, E.A., Baaisharah, S.S., 2014. Directions of autism diagnosis by 

electroencephalogram based brain computer interface: a review. Life Sci. J. 11 (6), 
298–304. https://doi.org/10.7537/marslsj110614.39.

9 

Y. Chen et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120937 

Appelbaum, L.G., Wade, A.R., Pettet, M.W., Vildavski, V.Y., Norcia, A.M., 2008. 

Figure–ground interaction in the human visual cortex. J. Vis. 8 (9), 8. https://doi. 
org/10.1167/8.9.8, 8. 

Ding, J., Sperling, G., Srinivasan, R., 2006. Attentional modulation of SSVEP power 
depends on the network tagged by the flicker frequency. Cereb. Cortex. 16 (7), 
1016–1029. https://doi.org/10.1093/cercor/bhj044.

Baker, D.H., Wade, A.R., 2017. Evidence for an optimal algorithm underlying signal 

Drijvers, L., Jensen, O., Spaak, E., 2021. Rapid invisible frequency tagging reveals 

combination in human visual cortex. Cereb. Cortex. 27 (1), 254–264. https://doi. 
org/10.1093/cercor/bhw395.

nonlinear integration of auditory and visual information. Hum. Brain Mapp. 42 (4), 
1138–1152. https://doi.org/10.1002/hbm.25282.

Baker, D.H., Simard, M., Saint-Amour, D., Hess, R.F., 2015. Steady-state contrast 

Faghel-Soubeyrand, S., Gosselin, F., 2017. Task-modulated integration of facial features 

response functions provide a sensitive and objective index of amblyopic deficits. 
Invest. Ophthalmol. Vis. Sci. 56 (2), 1208–1216. https://doi.org/10.1167/iovs.14- 
15611.

Baker, T.J., Norcia, A.M., Candy, T.R., 2011. Orientation tuning in the visual cortex of 3- 
month-old human infants. Vis. Res. 51 (5), 470–478. https://doi.org/10.1016/j. 
visres.2011.01.003.

Bear, M., Connors, B., Paradiso, M.A., 2006. Neuroscience-Exploring the Brain, third ed. 

Lippincott Williams & Wilkins, Baltimore. 

Beyersmann, E., Montani, V., Ziegler, J.C., Grainger, J., Stoianov, I.P., 2021. The 

dynamics of reading complex words: evidence from steady-state visual evoked 
potentials. Sci. Rep. 11 (1), 15919. https://doi.org/10.1038/s41598-021-95292-0.

Bin, G., Gao, X., Yan, Z., Hong, B., Gao, S., 2009. An online multi-channel SSVEP-based 
brain–computer interface using a canonical correlation analysis method. J. Neural 
Eng. 6 (4), 046002. https://doi.org/10.1088/1741-2560/6/4/046002.

Bock, E.A., Fesi, J.D., Baillet, S., Mendola, J.D., 2019. Tagged MEG measures binocular 

rivalry in a cortical network that predicts alternation rate. PLoS One 14 (7), 
e0218529. https://doi.org/10.1371/journal.pone.0218529.

Boremanse, A., Norcia, A.M., Rossion, B., 2013. An objective signature for visual binding 
of face parts in the human brain. J. Vis. 13 (11), 6. https://doi.org/10.1167/13.11.6, 
6. 

Boremanse, A., Norcia, A.M., Rossion, B., 2014. Dissociation of part-based and integrated 
neural responses to faces by means of electroencephalographic frequency tagging. 
Eur. J. Neurosci. 40 (6), 2987–2997. https://doi.org/10.1111/ejn.12663.

Brannan, J.R., Bodis-Wollner, I., Storch, R.L., 1992. Evidence for two distinct nonlinear 
components in the human pattern ERG. Vis. Res. 32 (1), 11–17. https://doi.org/ 
10.1016/0042-6989(92)90107-T.

Brown, R.J., Norcia, A.M., 1997. A method for investigating binocular rivalry in real- 
time with the steady-state VEP. Vis. Res. 37 (17), 2401–2408. https://doi.org/ 
10.1016/S0042-6989(97)00045-X.

Cai, Y., Mao, Y., Ku, Y., Chen, J., 2020. Holistic integration in the processing of Chinese 
characters as revealed by electroencephalography frequency tagging. Percept 49 (6), 
658–671. https://doi.org/10.1177/0301006620929197.

Calderone, D.J., Martinez, A., Zemon, V., Hoptman, M.J., Hu, G., Watkins, J.E., Javitt, D. 
C., Butler, P.D., 2013. Comparison of psychophysical, electrophysiological, and fMRI 
assessment of visual contrast responses in patients with schizophrenia. NeuroImage 
67, 153–162. https://doi.org/10.1016/j.neuroimage.2012.11.019.

Chadnova, E., Reynaud, A., Clavagnier, S., Hess, R.F., 2017. Latent binocular function in 

amblyopia. Vis. Res. 140, 73–80.

Chen, J., Meng, X., Liu, Z., Shang, B., Chang, C., Ku, Y., 2022a. Decoding semantics from 
intermodulation responses in frequency-tagged stereotactic EEG. J. Neurosci. 
Methods. 382, 109727. https://doi.org/10.1016/j.jneumeth.2022.109727.
Chen, X., Chen, Z., Gao, S., Gao, X., 2013. Brain–computer interface based on 

intermodulation frequency. J. Neural Eng. 10 (6), 066009. https://doi.org/10.1088/ 
1741-2560/10/6/066009.

Chen, X., Wang, Y., Gao, S., Jung, T.P., Gao, X., 2015. Filter bank canonical correlation 
analysis for implementing a high-speed SSVEP-based brain–computer interface. 
J. Neural Eng. 12 (4). https://doi.org/10.1088/1741-2560/10/6/066009.

Chen, X., Wang, Y., Zhang, S., Gao, S., Hu, Y., Gao, X., 2017. A novel stimulation method 
for multi-class SSVEP-BCI using intermodulation frequencies. J. Neural Eng. 14 (2), 
026013. https://doi.org/10.1088/1741-2552/aa5989.

Chen, Y., Shi, W., Liu, Q., Chu, H., Chen, X., Yan, L., Wu, J., Gao, X., 2022b. EEG 

Measurement for Suppression in Refractive Amblyopia and Push-Pull Perception 
Efficacy. IEEE Trans. Neural Syst. Rehabil. Eng. 30, 1321–1330. https://doi.org/ 
10.1109/TNSRE.2022.3175177.

Chen, Y., Stephani, T., Bagdasarian, M.T., Hilsmann, A., Eisert, P., Villringer, A., 
Nikulin, V.V., 2024. Realness of face images can be decoded from non-linear 
modulation of EEG responses. Sci. Rep. 14 (1), 5683. https://doi.org/10.1038/ 
s41598-024-56130-1.

Chen, Y., You, W., Hu, Y., Chu, H., Chen, X., Shi, W., Gao, X., 2023. EEG measurement for 

the effect of perceptual eye position and eye position training on comitant 
strabismus. Cereb. Cortex 33 (18), 10194–10206. https://doi.org/10.1093/cercor/ 
bhad275.

Chi, X., Wan, C., Wang, C., Zhang, Y., Chen, X., Cui, H., 2022. A novel hybrid brain- 

computer interface combining motor imagery and intermodulation steady-state 
visual evoked potential. IEEE Trans. Neural Syst. Rehabil. Eng. 30, 1525–1535. 
https://doi.org/10.1109/TNSRE.2022.3179971.

Cohen, M.X., Gulbinaite, R., 2017. Rhythmic entrainment source separation: Optimizing 
analyses of neural responses to rhythmic sensory stimulation. NeuroImage 147, 
43–56. https://doi.org/10.1016/j.neuroimage.2016.11.036.

Coll, M.P., Whelan, E., Catmur, C., Bird, G., 2020. Autistic traits are associated with 

atypical precision-weighted integration of top-down and bottom-up neural signals. 
Cogn. 199, 104236. https://doi.org/10.1016/j.cognition.2020.104236.

in the brain. J. Vis. 17 (10), 268. https://doi.org/10.1167/17.10.268, 268. 

Fesi, J.D., Thomas, A.L., Gilmore, R.O., 2014. Cortical responses to optic flow and motion 
contrast across patterns and speeds. Vis. Res. 100, 56–71. https://doi.org/10.1016/j. 
visres.2014.04.004.

Files, B.T., Baluch, F., Bao, P., Purington, C., Tjan, B.S., 2014. Overlapping but non- 

interacting neural populations in early visual cortex of a human subject with no optic 
chiasm. J. Vis. 14 (10), 685. https://doi.org/10.1167/14.10.685, 685. 

Gao, X., Wang, Y., Chen, X., Gao, S., 2021. Interface, interaction, and intelligence in 

generalized brain–computer interfaces. Trends Cogn. Sci. 25 (8), 671–684. https:// 
doi.org/10.1016/j.tics.2021.04.003.

Giani, A.S., Ortiz, E., Belardinelli, P., Kleiner, M., Preissl, H., Noppeney, U., 2012. Steady- 
state responses in MEG demonstrate information integration within but not across 
the auditory and visual senses. NeuroImage 60 (2), 1478–1489. https://doi.org/ 
10.1016/j.neuroimage.2012.01.114.

Gordon, N., Hohwy, J., Davidson, M.J., van Boxtel, J.J., Tsuchiya, N., 2019a. From 
intermodulation components to visual perception and cognition-a review. 
NeuroImage 199, 480–494. https://doi.org/10.1016/j.neuroimage.2019.06.008.
Gordon, N., Koenig-Robert, R., Tsuchiya, N., Van Boxtel, J.J., Hohwy, J., 2017. Neural 

markers of predictive coding under perceptual uncertainty revealed with 
Hierarchical Frequency Tagging. elife 6, e22749. https://doi.org/10.7554/ 
eLife.22749.

Gordon, N., Tsuchiya, N., Koenig-Robert, R., Hohwy, J., 2019b. Expectation and 

attention increase the integration of top-down and bottom-up signals in perception 
through different pathways. PLOS Biol 17 (4), e3000233. https://doi.org/10.1371/ 
journal.pbio.3000233.

Goupil, N., Hochmann, J.R., Papeo, L., 2023. Intermodulation responses show 

integration of interacting bodies in a new whole. Cortex 165, 129–140. https://doi. 
org/10.1016/j.cortex.2023.04.013.

Gu, L., Deng, S., Feng, L., Yuan, J., Chen, Z., Yan, J., Lu, Z.L., 2020. Effects of monocular 

perceptual learning on binocular visual processing in adolescent and adult 
amblyopia. Iscience 23 (2), 100875. https://doi.org/10.1016/j.isci.2020.100875.
Gundlach, C., Müller, M.M., 2013. Perception of illusory contours forms intermodulation 
responses of steady state visual evoked potentials as a neural signature of spatial 
integration. Biol. Psychol. 94 (1), 55–60. https://doi.org/10.1016/j. 
biopsycho.2013.04.014.

H´ebert-Lalonde, N., Carmant, L., Safi, D., Roy, M.S., Lassonde, M., Saint-Amour, D., 
2014. A frequency-tagging electrophysiological method to identify central and 
peripheral visual field deficits. Doc. Ophthalmol. 129, 17–26. https://doi.org/ 
10.1007/s10633-014-9439-9.

Herrmann, C.S., 2001. Human EEG responses to 1–100 Hz flicker: resonance phenomena 

in visual cortex and their potential correlation to cognitive phenomena. 
Experimental Brain Res. 137, 346–353. https://doi.org/10.1007/s002210100682.

Hou, C., Tyson, T.L., Uner, I.J., Nicholas, S.C., Verghese, P., 2021. Excitatory 

contribution to binocular interactions in human visual cortex is reduced in 
strabismic amblyopia. J. Neurosci. 41 (41), 8632–8643. https://doi.org/10.1523/ 
JNEUROSCI.0268-21.2021.

Hu, J., Chen, J., Ku, Y., Yu, M., 2023. Reduced interocular suppression after inverse 
patching in anisometropic amblyopia. Front. Neurosci. 17, 1280436. https://doi. 
org/10.3389/fnins.2023.1280436.

Jamison, K.W., Roy, A.V., He, S., Engel, S.A., He, B., 2015. SSVEP signatures of binocular 
rivalry during simultaneous EEG and fMRI. J. Neurosci. Methods. 243, 53–62. 
https://doi.org/10.1016/j.jneumeth.2015.01.024.

Kastner-Dorn, A.K., Andreatta, M., Pauli, P., Wieser, M.J., 2018. Hypervigilance during 

anxiety and selective attention during fear: Using steady-state visual evoked 
potentials (ssVEPs) to disentangle attention mechanisms during predictable and 
unpredictable threat. Cortex 106, 120–131. https://doi.org/10.1016/j. 
cortex.2018.05.008.

Katyal, S., Engel, S.A., He, B., He, S., 2016. Neurons that detect interocular conflict 
during binocular rivalry revealed with EEG. J. Vis. 16 (3), 18. https://doi.org/ 
10.1167/16.3.18, 18. 

Katyal, S., Vergeer, M., He, S., He, B., Engel, S.A., 2018. Conflict-sensitive neurons gate 

interocular suppression in human visual cortex. Sci. Rep. 8 (1), 1239. https://doi. 
org/10.1038/s41598-018-19809-w.

Kim, Y.J., Tsai, J.J., Ojemann, J., Verghese, P., 2017. Attention to multiple objects 

facilitates their integration in prefrontal and parietal cortex. J. Neurosci. 37 (19), 
4942–4953. https://doi.org/10.1523/JNEUROSCI.2370-16.2017.

Koo, B., Lee, H.G., Nam, Y., Choi, S., 2015. Immersive BCI with SSVEP in VR head- 
mounted display. In: 2015 37th Annual International Conference of the IEEE 
Engineering in Medicine and Biology Society (EMBC), pp. 1103–1106. https://doi. 
org/10.1109/EMBC.2015.7318558.IEEE.

Lee, T.S., Mumford, D., 2003. Hierarchical Bayesian inference in the visual cortex. JOSA 

A 20 (7), 1434–1448. https://doi.org/10.1364/JOSAA.20.001434.

Davidson, M.J., Mithen, W., Hogendoorn, H., Van Boxtel, J.J., Tsuchiya, N., 2020. The 
SSVEP tracks attention, not consciousness, during perceptual filling-in. Elife 9, 
e60031. https://doi.org/10.7554/eLife.60031.

Lee, T.S., Nguyen, M., 2001. Dynamics of subjective contour formation in the early visual 
cortex. Proc. Natl. Acad. Sci. USA 98 (4), 1907–1911. https://doi.org/10.1073/ 
pnas.98.4.1907.

Dickinson, A., Gomez, R., Jones, M., Zemon, V., Milne, E., 2018. Lateral inhibition in the 

Legge, G.E., Foley, J.M., 1980. Contrast masking in human vision. JOSA 70 (12), 

autism spectrum: an SSVEP study of visual cortical lateral interactions. 
Neuropsychologia 111, 369–376. https://doi.org/10.1016/j. 
neuropsychologia.2018.02.018.

1458–1471. https://doi.org/10.1364/JOSA.70.001458.

Li, M., Chen, X., Cui, H., 2023. A High-Frequency SSVEP-BCI System Based on 
Simultaneous Modulation of Luminance and Motion Using Intermodulation 

10 

Y. Chen et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120937 

Frequencies. IEEE Trans. Neural Syst. Rehabil. Eng. 31, 2603–2611. https://doi.org/ 
10.1109/TNSRE.2023.3281416.

Li, Y., Bin, G., Gao, X., Hong, B., Gao, S., 2011. Analysis of phase coding SSVEP based on 

canonical correlation analysis (CCA. In: 2011 5th International IEEE/EMBS 
Conference on Neural Engineering, pp. 368–371. https://doi.org/10.1109/ 
NER.2011.5910563.IEEE.

Liang, L., Lin, J., Yang, C., Wang, Y., Chen, X., Gao, S., Gao, X., 2020. Optimizing a dual- 

frequency and phase modulation method for SSVEP-based BCIs. J. Neural Eng. 17 
(4), 046026. https://doi.org/10.1088/1741-2552/abaa9b.

Liang, L., Yang, C., Wang, Y., Gao, X., 2019. High-frequency SSVEP stimulation paradigm 
based on dual frequency modulation. In: 2019 41st Annual International Conference 
of the IEEE Engineering in Medicine and Biology Society (EMBC), pp. 6184–6187. 
https://doi.org/10.1109/EMBC.2019.8856903.IEEE.

Lygo, F.A., Richard, B., Wade, A.R., Morland, A.B., Baker, D.H., 2021. Neural markers of 
suppression in impaired binocular vision. NeuroImage 230, 117780. https://doi.org/ 
10.1016/j.neuroimage.2021.117780.

Meigen, T., Prüfer, R., Reime, S., Friedrich, A., 2005. Contributions from lateral 

interaction mechanisms to the human ERG can be studied with a two-frequency 
method. Vis. Res. 45 (22), 2862–2876. https://doi.org/10.1016/j. 
visres.2005.06.025.

Mersad, K., Caristan, C., 2021. Blending into the Crowd: Electrophysiological Evidence of 
Gestalt Perception of a Human Dyad. Neuropsychologia 160, 107967. https://doi. 
org/10.1016/j.neuropsychologia.2021.107967.

Montani, V., Chanoine, V., Grainger, J., Ziegler, J.C., 2019. Frequency-tagged visual 

evoked responses track syllable effects in visual word recognition. Cortex 121, 
60–77. https://doi.org/10.1016/j.cortex.2019.08.014.

Moratti, S., Rubio, G., Campo, P., Keil, A., Ortiz, T., 2008. Hypofunction of right 
temporoparietal cortex during emotional arousal in depression. Arch. Gen. 
Psychiatry 65 (5), 532–541. https://doi.org/10.1016/j.cortex.2019.08.014.
Müller, M.M., Hübner, R., 2002. Can the spotlight of attention be shaped like a 

doughnut? Evidence from steady-state visual evoked potentials. Psychol. Sci. 13 (2), 
119–124. https://doi.org/10.1111/1467-9280.00422.

Nakanishi, M., Wang, Y.T., Jung, T.P., Zao, J.K., Chien, Y.Y., Diniz-Filho, A., Fabio, B.D., 
Lin, Y.P., Wang, Y., Medeiros, F.A., 2017a. Detecting glaucoma with a portable 
brain-computer interface for objective assessment of visual function loss. JAMA 
Ophthalmol 135 (6), 550–557. https://doi.org/10.1001/ 
jamaophthalmol.2017.0738.

Nakanishi, M., Wang, Y., Chen, X., Wang, Y.T., Gao, X., Jung, T.P., 2017b. Enhancing 

detection of SSVEPs for a high-speed brain speller using task-related component 
analysis. IEEE Trans. Biomed. Eng. 65 (1), 104–112. https://doi.org/10.1109/ 
TBME.2017.2694818.

Norcia, A.M., Appelbaum, L.G., Ales, J.M., Cottereau, B.R., Rossion, B., 2015. The steady- 
state visual evoked potential in vision research: A review. J. Vis. 15 (6), 4. https:// 
doi.org/10.1167/15.6.4, 4. 

Pastor, M.A., Artieda, J., Arbizu, J., Valencia, M., Masdeu, J.C., 2003. Human cerebral 

activation during steady-state visual-evoked responses. J. Neurosci. 23 (37), 
11621–11627. https://doi.org/10.1523/JNEUROSCI.23-37-11621.2003.

Pitchaimuthu, K., Dormal, G., Sourav, S., Shareef, I., Rajendran, S.S., Ossand´on, J.P., 

Kekunnaya, R., R¨oder, B., 2021. Steady state evoked potentials indicate changes in 
nonlinear neural mechanisms of vision in sight recovery individuals. Cortex 144, 
15–28. https://doi.org/10.1016/j.cortex.2021.08.001.

Radtke, E.L., Sch¨one, B., Martens, U., Gruber, T., 2020. Electrophysiological correlates of 
gist perception: a steady-state visually evoked potentials study. Exp. Brain Res. 238, 
1399–1410.

Ramadan, R.A., Vasilakos, A.V., 2017. Brain computer interface: control signals review. 
Neurocomputing 223, 26–44. https://doi.org/10.1016/j.neucom.2016.10.024.
Rassi, S.Z., Ospina, L., Samson, Y., Saint-Amour, D., Perreault, S., 2017. A. 02 Assessing 
visual functions in children with an optic pathway glioma using steady-state visual 
evoked potentials. Can. J. Neurol. Sci. 44 (S2), S8–S9. https://doi.org/10.1017/ 
cjn.2017.66.

Richard, B., Chadnova, E., Baker, D.H., 2018. Binocular vision adaptively suppresses 

delayed monocular signals. NeuroImage 172, 753–765. https://doi.org/10.1016/j. 
neuroimage.2018.02.021.

Seijdel, N., Schoffelen, J.M., Hagoort, P., Drijvers, L., 2024. Attention drives visual 
processing and audiovisual integration during multimodal communication. 
J. Neurosci. 44 (10), e0870232023. https://doi.org/10.1523/JNEUROSCI.0870- 
23.2023.

Shi, N., Miao, Y., Huang, C., Li, X., Song, Y., Chen, X., Wang, Y., Gao, X., 2024. 

Estimating and approaching the maximum information rate of noninvasive visual 
brain-computer interface. NeuroImage, 120548. https://doi.org/10.1016/j. 
neuroimage.2024.120548.

Spiegel, A., Mentch, J., Haskins, A.J., Robertson, C.E., 2019. Slower binocular rivalry in 
the autistic brain. Curr. Biol. 29 (17), 2948–2953. https://doi.org/10.1016/j. 
cub.2019.07.026.

Srinivasan, R., Bibi, F.A., Nunez, P.L., 2006. Steady-state visual evoked potentials: 

distributed local sources and wave-like dynamics are sensitive to flicker frequency. 
Brain Topogr 18, 167–187. https://doi.org/10.1007/s10548-006-0267-4.

Sun, Y., Liang, L., Sun, J., Chen, X., Tian, R., Chen, Y., Zhang, L., Gao, X., 2022. 

A Binocular Vision SSVEP Brain–Computer Interface Paradigm for Dual-Frequency 
Modulation. IEEE Trans. Biomed. Eng. 70 (4), 1172–1181. https://doi.org/10.1109/ 
TBME.2022.3212192.

Sutoyo, D., Srinivasan, R., 2009. Nonlinear SSVEP responses are sensitive to the 
perceptual binding of visual hemifields during conventional ‘eye’ rivalry and 
interocular ‘percept’ rivalry. Brain Res 1251, 245–255. https://doi.org/10.1016/j. 
cub.2019.07.026.

Tang, Y., Norcia, A.M., 1995. An adaptive filter for steady-state evoked responses. 

Electroencephalogr. Clin. Neurophysiol. Evoked Potentials Sect. 96 (3), 268–277. 
https://doi.org/10.1016/0168-5597(94)00309-3.

Thomas, A., Gilmore, R., 2014. Temporal and Speed Tuning in Brain Responses to Local 

and Global Motion Patterns. J. Vis. 14 (10), 482. https://doi.org/10.1167/ 
14.10.482, 482. 

Tononi, G., Srinivasan, R., Russell, D.P., Edelman, G.M., 1998. Investigating neural 

correlates of conscious perception by frequency-tagged neuromagnetic responses. 
Proc. Natl. Acad. Sci. USA 95 (6), 3198–3203. https://doi.org/10.1073/ 
pnas.95.6.3198.

Tsai, J.J., Wade, A.R., Norcia, A.M., 2012. Dynamics of normalization underlying 

masking in human visual cortex. J. Neurosci. 32 (8), 2783–2789. https://doi.org/ 
10.1523/JNEUROSCI.4485-11.2012.

Vergeer, M., Kogo, N., Nikolaev, A.R., Alp, N., Loozen, V., Schraepen, B., Wagemans, J., 
2018. EEG frequency tagging reveals higher order intermodulation components as 
neural markers of learned holistic shape representations. Vis. Res. 152, 91–100. 
https://doi.org/10.1016/j.visres.2018.01.007.

Vialatte, F.B., Maurice, M., Dauwels, J., Cichocki, A., 2010. Steady-state visually evoked 

potentials: focus on essential paradigms and future perspectives. Progress in 
neurobiology 90 (4), 418–438. https://doi.org/10.1016/j.pneurobio.2009.11.005.
Vilidaite, G., Norcia, A.M., West, R.J., Elliott, C.J., Pei, F., Wade, A.R., Baker, D.H., 2018. 
Autism sensory dysfunction in an evolutionarily conserved system. Proc. R. Soc. B. 
285 (1893), 20182255. https://doi.org/10.1098/rspb.2018.2255.

Walter, S., Quigley, C., Andersen, S.K., Mueller, M.M., 2012. Effects of overt and covert 
attention on the steady-state visual evoked potential. Neurosci. Lett. 519 (1), 37–41. 
https://doi.org/10.1016/j.neulet.2012.05.011.

Wenzel, M.A., Schultze-Kraft, R., Meinecke, F.C., Cardinaux, F., Kemp, T., Müller, K.R., 
Curio, G., Blankertz, B., 2015. EEG-based usability assessment of 3D shutter glasses. 
J. Neural Eng. 13 (1), 016003. https://doi.org/10.1088/1741-2560/13/1/016003.

Wieser, M.J., McTeague, L.M., Keil, A., 2012. Competition effects of threatening faces in 
social anxiety. Emotion 12 (5), 1050–1060. https://doi.org/10.1037/a0027069.
Wittenhagen, L., Mattingley, J.B., 2019. Steady-state visual evoked potentials reveal 

enhanced neural responses to illusory surfaces during a concurrent visual attention 
task. Cortex 117, 217–227. https://doi.org/10.1016/j.cortex.2019.03.014.

Wong, C.M., Wang, B., Wang, Z., Lao, K.F., Rosa, A., Wan, F., 2020. Spatial filtering in 
SSVEP-based BCIs: Unified framework and new improvements. IEEE Trans. Biomed. 
Eng. 67 (11), 3057–3072. https://doi.org/10.1109/TBME.2020.2975552.
Wong, C.M., Wang, Z., Wang, B., Rosa, A., Jung, T.P., Wan, F., 2023. Enhancing 

Detection of Multi-Frequency-Modulated SSVEP Using Phase Difference Constrained 
Canonical Correlation Analysis. IEEE Trans. Neural Syst. Rehabil. Eng. 31, 
1343–1352. https://doi.org/10.1109/TNSRE.2023.3243290.

Woody, M.L., Miskovic, V., Owens, M., James, K.M., Feurer, C., Sosoo, E.E., Gibb, B.E., 
2017. Competition effects in visual cortex between emotional distractors and a 
primary task in remitted depression. Biol. Psychiatry: Cogn. Neurosci. 
Neuroimaging. 2 (5), 396–403. https://doi.org/10.1016/j.bpsc.2016.12.007.
Yin, E., Zeyl, T., Saab, R., Chau, T., Hu, D., Zhou, Z., 2015. A hybrid brain–computer 
interface based on the fusion of P300 and SSVEP scores. IEEE Trans. Neural Syst. 
Rehabil. Eng. 23 (4), 693–701. https://doi.org/10.1109/TNSRE.2015.2403270.
Yin, E., Zhou, Z., Jiang, J., Chen, F., Liu, Y., Hu, D., 2013a. A novel hybrid BCI speller 
based on the incorporation of SSVEP into the P300 paradigm. J. Neural Eng. 10 (2), 
026012. https://doi.org/10.1088/1741-2560/10/2/026012.

Yin, E., Zhou, Z., Jiang, J., Chen, F., Liu, Y., Hu, D., 2013b. A speedy hybrid BCI spelling 
approach combining P300 and SSVEP. IEEE Transactions on Biomedical Engineering 
61 (2), 473–483. https://doi.org/10.1109/TBME.2013.2281976.

Yin, E., Zhou, Z., Jiang, J., Yu, Y., Hu, D., 2014. A dynamically optimized SSVEP 

brain–computer interface (BCI) speller. IEEE transactions on biomedical engineering 
62 (6), 1447–1456. https://doi.org/10.1109/TBME.2014.2320948.

Zemon, V., Ratliff, F., 1984. Intermodulation components of the visual evoked potential: 
responses to lateral and superimposed stimuli. Biol. Cybern. 50 (6), 401–408. 
https://doi.org/10.1007/BF00335197.

Zhang, P., Jamison, K., Engel, S., He, B., He, S., 2011. Binocular rivalry requires visual 
attention. Neuron 71 (2), 362–369. https://doi.org/10.1016/j.neuron.2011.05.035.
Zhang, R., Xu, Z., Zhang, L., Cao, L., Hu, Y., Lu, B., Shi, L., Yao, D., Zhao, X., 2022. The 
effect of stimulus number on the recognition accuracy and information transfer rate 
of SSVEP–BCI in augmented reality. J. Neural Eng. 19 (3), 036010. https://doi.org/ 
10.1088/1741-2552/ac6ae5.

Zhang, X., Xu, G., Ravi, A., Pearce, S., Jiang, N., 2021. Can a highly accurate multi-class 
SSMVEP BCI induce sensory-motor rhythm in the sensorimotor area? J. Neural Eng. 
18 (3), 035001. https://doi.org/10.1088/1741-2552/ab85b2.

Srinivasan, R., Russell, D.P., Edelman, G.M., Tononi, G., 1999. Increased Synchronization 

Zhang, X., Xu, G., Xie, J., Zhang, X., 2017. Brain response to luminance-based and 

of Neuromagnetic Responses during Conscious Perception. J. Neurosci. 19, 
5435–5448. https://doi.org/10.1523/JNEUROSCI.19-13-05435.1999.

Stanley, D.A., Rubin, N., 2003. fMRI activation in response to illusory contours and 
salient regions in the human lateral occipital complex. Neuron 37 (2), 323–331.

Sun, Y., Li, Y., Chen, Y., Yang, C., Sun, J., Liang, L., Gao, X., 2024. Efficient dual- 
frequency SSVEP brain-computer interface system exploiting interocular visual 
resource disparities. Expert Syst. Appl. 252, 124144. https://doi.org/10.1016/j. 
eswa.2024.124144.

11 

motion-based stimulation using inter-modulation frequencies. PLoS One 12 (11), 
e0188073. https://doi.org/10.1371/journal.pone.0188073.

Zheng, X., Xu, G., Wang, Y., Han, C., Du, C., Yan, W., Zhang, S., Liang, R., 2019a. 

Objective and quantitative assessment of visual acuity and contrast sensitivity based 

Y. Chen et al.                                                                                                                                                                                                                                    

NeuroImage 303 (2024) 120937 

on steady-state motion visual evoked potentials using concentric-ring paradigm. 
Doc. Ophthalmol. 139, 123–136. https://doi.org/10.1007/s10633-019-09702-w.
Zheng, X., Xu, G., Zhang, Y., Liang, R., Zhang, K., Du, Y., Xie, J., Zhang, S., 2020. Anti- 
fatigue performance in SSVEP-based visual acuity assessment: A comparison of six 
stimulus paradigms. Front. Hum. Neurosci. 14, 301. https://doi.org/10.3389/ 
fnhum.2020.00301.

Zheng, X., Xu, G., Zhi, Y., Wang, Y., Han, C., Wang, B., Zhang, S., Zhang, K., Liang, R., 

2019b. Objective and quantitative assessment of interocular suppression in 
strabismic amblyopia based on steady-state motion visual evoked potentials. Vis. 
Res. 164, 44–52. https://doi.org/10.1016/j.visres.2019.07.003.

12 

