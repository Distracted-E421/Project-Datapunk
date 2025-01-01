NeuroImage 303 (2024) 120928 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Differential neural representations of syntactic and semantic information 
across languages in Chinese-English bilinguals

Zeqi Hou #, Hehui Li #, Lin Gao , Jian Ou , Min Xu *

Center for Brain Disorders and Cognitive Sciences, School of Psychology, Shenzhen University, Shenzhen 518060, China

A R T I C L E  I N F O

A B S T R A C T

Keywords:
Bilingualism
Syntactic representation
Semantic representation
Neural adaptation
fMRI
Multivariate pattern analysis

Bilingual  individuals  manage  multiple  languages  that  align  in  conceptual  meaning  but  differ  in  forms  and 
structures. While prior research has established foundational insights into the neural mechanisms in bilingual 
processing, the extent to which the first (L1) and second language (L2) systems overlap or diverge across different 
linguistic components remains unclear. This study probed the neural underpinnings of syntactic and semantic 
processing for L1 and L2 in Chinese-English bilinguals (N = 44) who performed sentence comprehension tasks 
and an N-back working memory task during functional MRI scanning. We observed that the increased activation 
for L2 processing was within the verbal working memory network, suggesting a greater cognitive demand for 
processing  L2.  Crucially,  we  looked  for brain  regions  showing  adaptation  to  the  repetition  of  semantic infor-
mation  and  syntactic  structure,  and  found  more  robust  adaptation  effects  in  L1  in  the  middle  and  superior 
temporal cortical areas. The differential adaptation effects between L1 and L2 were more pronounced for the 
semantic condition. Multivariate pattern analysis further revealed distinct neural sensitivities to syntactic and 
semantic representations between L1 and L2 across frontotemporal language regions. Our findings suggest that 
while L1 and L2 engage similar neural systems, finer representation analyses uncover distinct neural patterns for 
both  semantic  and  syntactic  aspects  in  the  two  languages.  This  study  advances  our  understanding  of  neural 
representations involved in different language components in bilingual individuals.

1. Introduction

Bilingualism  is  a  valuable  skill  with  practical  applications  in  both 
personal and professional aspects of life. Bilingual individuals manage 
multiple languages that share conceptual meanings yet diverge in forms 
and  structures.  Exploring  how  the  brain  represents  and  processes  the 
first (L1) and second language (L2) not only holds the potential to illu-
minate  the  specialized  cognitive  functions  involved  in  language  pro-
cessing  but  could  also  contribute  to  a  broader  understanding  of  the 
complexities in human cognitive abilities.

Numerous behavioral and neuroimaging studies have indicated that 
multiple  languages  share  conceptual  and  semantic  representations  in 
bilinguals  (Crinion  et  al.,  2006;  Klein  et  al.,  2006;  Kroll  et  al.,  2015; 
Perani and Abutalebi, 2005; Yang et al., 2017). At the conceptual level, 
resemblances often exist among various languages, allowing for refer-
ence  to  the  same  concepts  and  their  translation  between  languages. 
Thus, a considerable degree of commonality in semantic representation 

can be observed across different languages (Chee, 2009; Correia et al., 
2014;  Van  de  Putte  et  al.,  2018;  Vargas  &  Just,  2022).  Furthermore, 
studies utilizing refined multivariate analysis have also revealed that as 
proficiency in a second language improves, there is a notable conver-
gence  in  the  semantic  representations  across  both  languages  within 
bilingual individuals (Buchweitz et al., 2012).

However,  the  degree  of  similarity  between  language  components 
such as syntax, phonology, and orthography can vary, influencing how 
L1 and L2 are neurally represented (Bick et al., 2011; Chan et al., 2008; 
Jeong et al., 2007; Kim et al., 2016; Li et al., 2014; Liu and Cao, 2016; 
Meschyan  and  Hernandez,  2006;  Nelson  et  al.,  2009;  Połczy´nska  and 
Bookheimer, 2021; Tan et al., 2003; Wagley et al., 2024; Xu et al., 2021; 
Zhan et al., 2023). According to the accommodation and assimilation 
hypothesis  (Perfetti  et  al.,  2007;  Nelson  et  al.,  2009),  if  the  brain 
network used for L1 is adequate to process a newly acquired language 
(L2), it reflects an assimilation pattern; if the L1 brain network cannot 
fully  support  the  processing  of  the  new  language,  leading  to  the 

* Corresponding author at: Center for Brain Disorders and Cognitive Sciences, School of Psychology, Shenzhen University, Nanhai Ave 3688, Shenzhen, Guang-

dong, 518060, China.

E-mail address: xumin@szu.edu.cn (M. Xu). 
# Z.H. and H.L. contributed equally to this work.

https://doi.org/10.1016/j.neuroimage.2024.120928
Received 21 February 2024; Received in revised form 7 November 2024; Accepted 11 November 2024  
Available online 17 November 2024 
1053-8119/© 2024 The Author(s).  Published by Elsevier Inc.  This is an open access article under the CC BY-NC license ( http://creativecommons.org/licenses/by- 
nc/4.0/ ). 

Z. Hou et al.                                                                                                                                                                                                                                     

NeuroImage 303 (2024) 120928 

recruitment of novel procedures or additional regions for L2 processing, 
this  is  considered  an  accommodation  pattern.  Previous  neuroimaging 
studies have shown that when the linguistic distance between L1 and L2 
is  small,  L2  processing  tends  to  rely  on  similar  brain  regions  as  L1, 
indicating more assimilation, but when the linguistic distance is large, 
L2  processing  often  activates  distinct  brain  regions  from  L1,  demon-
strating more accommodation (Liu et al., 2007; Kim et al., 2016). For 
instance, Jeong et al. (2007) investigated the impact of syntactic simi-
larity  on  the  neural  basis  of  bilingual  processing  by  comparing  L1 
(Korean)  with  syntactically  similar  L2  (Japanese)  and  dissimilar  L2 
(English).  Their  findings  showed  that  English,  being  syntactically 
different  from  Korean,  elicited  greater  activation  in  the  left  inferior 
frontal  and  right  superior  temporal  gyri.  In  contrast,  no  significant 
language  difference  was  observed between  Korean  and  Japanese  sen-
tence  processing,  suggesting  that  syntactic  similarities  between  lan-
guages  may  influence  neural  activation  patterns.  A  more  recent 
functional imaging study by Wang et al. found that while brain regions 
activated by L1 (Chinese) and L2 (English) are intertwined, there are 
distinct  spatial  patterns  for  specific  grammatical  meanings  between 
languages (Wang et al., 2023).

While existing research has laid the groundwork for understanding 
the  neural  mechanisms  underlying  bilingual  processing,  a  significant 
gap exists in understanding whether L1 and L2 commonality or disso-
ciation differ between different language components. This is particu-
larly  evident  in  languages  with  substantial  differences  in  specific 
components.  A  prime  example  is  Chinese-English  bilinguals,  whose 
handling of syntax and semantics warrants closer examination. Unlike 
English and other Indo-European languages, Chinese lacks verb conju-
gation and noun declension, resulting in fewer syntactic variations. This 
fundamental difference suggests that Chinese-English bilinguals might 
process  syntax differently in  each language,  possibly relying  more on 
semantic  cues  in  Chinese  and  explicit  syntactic  markers  in  English, 
reflecting  adaptations  to  the  unique  linguistic  characteristics  of  each 
language (Luke et al., 2002; Wang et al., 2023; Zhu et al., 2022). This 
distinct characteristic raises a critical and underexplored question: How 
are syntax and semantics represented in the Chinese-English bilingual 
brain?

In  addition  to  the  inherent  linguistic  differences  between  the  two 
languages, the disparities in how L1 and L2 are processed may also arise 
from  the  varying  cognitive  efforts  required.  Bilingual  individuals  not 
only process the content and the grammatical rules of one language in 
use but also suppress interference from the other language and flexibly 
switch between them (Abutalebi, 2008; Calabria et al., 2018; Guttentag 
et al., 1984; McDonald, 2006; Van Heuven et al., 2008). This process is 
particularly  taxing  for  those  with  lower  proficiency  in  L2,  as  L2  pro-
cessing is less automatic, demanding greater neural resource allocation 
towards lexical retrieval, articulatory processing, and cognitive control 
(Leonard et al., 2010; Liu et al., 2010; Liu and Cao, 2016; Saur et al., 
2009; Sulpizio et al., 2020). Compared to other cognitive factors such as 
attention or inhibitory control, a critical factor in this context is working 
memory,  which  plays  a  pivotal  role  in  sentence  comprehension  as  it 
serves as a temporary storage and processing system for linguistic in-
formation  during  language  processing  (Baddeley,  2017;  Chee  et  al., 
2004; Perani and Abutalebi, 2005), yet its limited capacity poses con-
straints (Just and Carpenter, 1992; Lewis et al., 2006). The relationship 
between  syntactic representation  and  working  memory,  in  particular, 
has been emphasized in the literature (King, 1991; Lewis et al., 2006). 
Some prior studies have suggested the stronger activation for L2 than L1 
is  due  to  the  greater  involvement  of  working  memory,  based  on  the 
observation that similar regions showing language differences, such as 
bilateral  inferior  and  middle  frontal  cortices  and  posterior  parietal 
cortices, are also engaged during verbal working memory tasks reported 
in the literature (e.g., Buchweitz et al., 2009).

In this fMRI study, we sought to investigate the neural representa-
tions of syntactic and semantic information between L1 (Chinese) and L2 
(English).  We  had  two  principal  aims.  The  first  aim  was  to  examine 

whether the differential activation between L1 and L2 overlapped with 
those brain regions engaged in a working memory task. Previous studies 
have  rarely  examined  neural activities  within  the  same group  of par-
ticipants for both language-related and verbal working memory tasks. 
Our study addresses this gap by examining the same cohort of partici-
pants. We adopted an N-back paradigm to probe the neural system of 
verbal  working  memory  and  utilized  conjunction  analysis  to  identify 
spatial overlap between areas showing language differences and those 
activated during the verbal working memory task. We hypothesized that 
L2  sentence  processing  would  engage  a  broader  set  of  brain  regions 
associated with working memory compared to L1. The overlapping re-
gions imply that processing sentences in L2 places a higher demand on 
the neural substrates of working memory than L1 processing.

Our second aim was to compare the neural patterns associated with 
L1 and L2 representation while minimizing differences in cognitive ef-
forts during performing the tasks. Previous studies have utilized various 
experimental paradigms, such as syntactic or semantic violation para-
digm, sentence and word sequence comparisons, and so on (Fedorenko 
et al., 2012; Fodor et al., 1996; Friederici, 2002; Friederici et al., 2000; 
Humphries et al., 2001, 2005, 2006; Luke et al., 2002; Vandenberghe 
et al., 2002). While these methodologies shed light on various aspects of 
sentence  processing,  they  might  inadvertently  engage  differential 
attentional and executive control across L1 and L2. Given the interplay 
of these factors, the implications of bilingualism cannot be exclusively 
linked to language processing per se (Hagoort and Indefrey, 2014; Kaan 
and Swaab, 2002). We employed an adaptation paradigm, which has the 
advantage of being able to detect neuronal populations that are sensitive 
to properties that are shared by consecutive stimuli (Chee, 2009; Dap-
retto and Bookheimer, 1999; Santi and Grodzinsky, 2010; Weber and 
Indefrey,  2009).  Specifically,  the  adaptation  paradigm  represents  an 
experimental  approach  wherein  stimuli  with  consistent  attributes  are 
presented sequentially to elicit and observe neuroadaptive effects within 
the  brain  specific  to  those  attributes.  As  these  stimuli  are  repeatedly 
administered, a typical diminishment in the response magnitude of the 
associated neural pathways is noted, indicative of a sensory adaptation 
to that particular attribute (Sawamura et al., 2006). The intralanguage 
comparison  was  conducted  prior  to  cross-linguistic  comparisons, 
thereby reducing the variations in cognitive load across different lan-
guages. We looked for brain regions showing adaptation to the repeti-
tion of semantic information and syntactic structure and compared these 
adaptation effects between L1 and L2.

Furthermore, even for the commonly activated brain areas, the finer 
representation patterns within these brain areas might still be distinctive 
between  different  languages.  We  used  multivariate  pattern  analysis 
(MVPA) to examine whether the activation patterns in the classic lan-
guage  regions  exhibited  distinct  sensitivity  to  syntactic  or  semantic 
representations and whether these patterns varied between L1 and L2. 
MVPA constitutes  an advanced computational approach that employs 
machine  learning algorithms  to  analysize and  interpret  neuroimaging 
data, enabling the quantitative assessment of how specific brain regions 
encode distinct informational content (Haxby, 2012). Unlike univariate 
analysis,  which  treats  each  voxel  independently,  MVPA  extracts  the 
signal  in  the  response  pattern  across  multiple  voxels  and  can  detect 
fine-grained  pattern  differences  (Kriegeskorte  et  al.,  2006;  Norman 
et  al.,  2006).  Our  approach  involved  a  comparative  analysis  of 
between-vs-within-categories  correlations  (Haxby  et  al.,  2001;  Mah-
moudi et al., 2012), which reveals how L1 and L2 are represented across 
distributed  brain  regions  and  determines  whether  there  are  specific 
neural activity patterns uniquely associated with each language.

2. Methods

2.1. Participants

Forty-four adults were recruited in the experiment (19 males and 25 
females; 19 - 26 yrs, mean age = 22.68 yrs). All were native Chinese 

2 

Z. Hou et al.                                                                                                                                                                                                                                     

NeuroImage 303 (2024) 120928 

speakers who acquired English as a second language. Among them, one 
participant failed to complete the verbal working memory task. There-
fore, the final sample size was 44 for the language task and 43 (18 males 
and 25 females; aged 19 - 26 years, mean age = 22.63 yrs) for the verbal 
working memory task. All were right-handed with normal or corrected- 
to-normal vision. The participants were physically healthy and free of 
neurological disease, head injury, and psychiatric disorders. The study 
was  approved  by  the  Ethic  and  Human  Protection  Committee  of 
Shenzhen  University  in  accordance  with  the  Declaration  of  Helsinki. 
Written informed consent was obtained from each participant prior to 
the experiment. Monetary compensation was paid for participation.

The participants completed a language background questionnaire, i. 
e.,  the  Language  History  Questionnaire  (LHQ3),  which  provides  an 
overall evaluation of proficiency based on participants’ self-ratings for 
different  language  components,  including  reading,  writing,  speaking, 
and listening (Li et al., 2020). They self-assessed their language profi-
ciency in Chinese and English using a 7-point scale, where a score of one 
indicated "very unskilled" and a score of seven signified "very proficient." 
Based on the scoring approach provided by LHQ3, participants reported 
an  average  self-assessed  proficiency  in  Mandarin  of  0.804  (Standard 
Deviation  [SD]  = 0.166)  and  in  English  of  0.714  (SD  = 0.126).  The 
participants acquired English as a second language between the ages of 4 
and 13 years, with an average age of acquisition (AoA) of 8 years (SD =
2.326).  Previous  studies  have  distinguished  between  three  types  of 
bilingual acquisition (Meisel, 2006): simultaneous bilingual acquisition 
(AoA < 3 or 4), child L2 acquisition (AoA between 5-10), and adult L2 
acquisition (AoA > 10). Based on these criteria, 2 out of the 44 partic-
ipants were classified as simultaneous bilinguals, 36 as child L2 learners, 
and 6 as adult L2 learners.

In addition, the participants’ English proficiency was evaluated using 
an  English  proficiency  grading  test  developed  by  Oxford  University 
Press and Cambridge English for Speakers of Other Languages (ESOL). 
This 30-minute test measures English learners’  reading skills, vocabu-
lary, and grammatical ability. Scores were derived from the percentage 
of correct answers. The participants’  average score was 66.856 (SD =

10.919). The average score corresponded to a B2 (upper intermediate) 
level  on  the  scale  of  the  Association  of  Language  Testers  of  Europe 
(ALTE), indicating that the average English proficiency of the partici-
pants was intermediate and they could understand complex sentences 
and passages.

2.2. Task design of fMRI experiments

2.2.1. Sentence comprehension task

We used an adaptation paradigm during a sentence comprehension 
task to look for brain regions showing adaptation to the repetition of 
semantic  information  and  syntactic  structure.  Participants  were 
required  to  read  and  comprehend  sentences  in  both  languages.  The 
experimental  design  was  consistent  across  the  two  languages.  Specif-
ically, the language experiment consisted of five conditions: same sen-
tence  (SSen),  same  syntax  (SSyn),  same  semantics  (SSem),  different 
sentence (DSen), and same pseudo-word sequence (SPW; see Table 1 for 
stimulus  samples).  Each  condition  involved  presenting  a  sequence  of 
three stimulus items in a miniblock. In the SSen condition, participants 
were presented with the same sentences successively. The SSyn condi-
tion  displayed  sentences  with  the  same  syntactic  structure.  We  used 
three types of syntactic structures that naturally occur in both languages, 
including  active,  passive,  and  emphatic  sentences.  For  the  emphatic 
sentences,  we  maintained  consistency  in  the  syntactic structure using 
the "It was…  that" structure. The SSem condition contained sentences 
with  equivalent semantic  content. The  DSen condition  presented sen-
tences that differed in both syntactic structure and sentence meaning. 
SPW served as a control condition, presenting repetitions of false font 
stimuli generated by rearranging characters’ strokes or the sequence of 
English letters from the experimental sentences. This condition was used 
to control for basic visual processing (see Table 1 for stimulus samples of 
each condition). The final set of experimental stimuli consisted of 200 
sentences, each in Chinese and English. There were sixty sentences for 
SSyn, SSem, and DSen conditions and twenty for the SSen condition. The 
average  number  of  characters  or  words  was  8  ± 0.86  for  Chinese 

Table 1 
Stimulus samples for the five conditions in the sentence comprehension task. The translations provided aim to convey the meaning rather than a direct lexical match.

condition

order

Chinese stimuli (English translations)

English stimuli

same sentence  

(SSen)

same syntax  
(SSyn)

same semantic  

(SSem)

different sentence  

(DSen)

same 

pseudo-word  
(SPW)

1

2

3

1

2

3

1

2

3

1

2

3

1

2

3

小李弄丢了三件白色的衬衫.( 
Xiao Li has lost three white shirts.)
小李弄丢了三件白色的衬衫.( 
Xiao Li has lost three white shirts.)
小李弄丢了三件白色的衬衫.( 
Xiao Li has lost three white shirts.)
他拉开了两个在吵架的阿姨.( 
He pulled away two aunts who were arguing.)
她剪烂了一套很漂亮的婚纱.( 
She cut up a beautiful wedding dress.)
她插上了两束刚醒好的玫瑰.( 
She planted two roses that had just woken up.)
妹妹用布盖住了电脑显示屏.( 
My sister covered the computer screen with a cloth.)
妹妹用布盖住的是电脑显示屏.( 
What my sister covered with a cloth is the computer screen.)
布被妹妹用来盖住了电脑显示屏.( 
The cloth was used by my sister to cover the computer screen.)
我们打败了那个厉害的对手.( 
We defeated the formidable opponent.)
猎人激怒的是两只凶猛的狮子.( 
What the hunter provoked were two fierce lions.)
那辆刚买的推车被师妹拉走了.( 
The cart I just bought was pulled away by my sister.)

3 

All the animals in this zoo eat vegetables.

All the animals in this zoo eat vegetables.

All the animals in this zoo eat vegetables.

It was the boy’s arm that the little brother hurt.

It was her vision that blocked her long curly hair.

It was the sandy beach that big waves splashed.

He finished his meal in ten minutes.

It was in ten minutes that he finished his meal.

His meal was finished by him in ten minutes.

The company fired the pregnant woman quickly.

It is robots that can sweep the floor very efficiently.

The red paint cans were tightly closed by Mike.

Ihdh nc i hcnjc scbsjcxc bdgc ncncjdnv.

Ihdh nc i hcnjc scbsjcxc bdgc ncncjdnv.

Ihdh nc i hcnjc scbsjcxc bdgc ncncjdnv.

Z. Hou et al.                                                                                                                                                                                                                                     

NeuroImage 303 (2024) 120928 

sentences and 9 ± 1.69 for English sentences. Because verb repetition 
could induce semantic and syntactic adaptation, we carefully avoided 
repeating verbs in the SSyn and DSen conditions. In this study, we did 
not  match  word  frequency  across  the  whole  sentences.  Since  the  fre-
quency  values  were  extracted  from  different  language  corpora,  it  is 
challenging to match the materials in terms of frequency. Instead, we 
focused on selecting high-frequency verbs for both languages, consid-
ering  that  verbs  play  a  critical  role  in  sentence  comprehension  (e.g., 
Pickering and Ferreira, 2008). We obtained the frequency class of verbs 
in the sentences based on the Leipzig Corpora Collection: for Chinese 
verbs, the frequency class is 12.8 ± 3.7, and for English is 20.0±2.6. The 
full list of stimuli is available at https://bit.ly/44qcEOw.

The task procedure was shown in Fig. 1A and Fig. 1B. In each trial, a 
black fixation "+" first appeared in the center of a gray background for 
1s, followed by a sentence lasting for 3s. There were three sentences in 
each miniblock. The random interval between every five miniblocks is 4, 
6, or 8s. In each run, the cumulative interval time was 134s. Each run 

consisted of five conditions, and each condition consisted of five mini-
blocks.  Five  probing  questions  were  interspersed  in  a  pseudo-random 
order  during  each  run  to  keep  the  participants  engaged  in  the  task. 
The participants needed to judge whether the sentence on the screen was 
shown in the preceding miniblock. The instruction was: "Please press the 
left-hand  key if  the  stimulus appeared  previously, and  the right-hand 
key if it did not." The duration of each run was 7 min and 40 s. Tasks 
for each language were performed for four runs, with the order of the 
Chinese and English tasks balanced among the participants. Before the 
MRI scan, the participants practiced with ten mini-blocks (five in each 
language) and  one  probe question  to  ensure that  the participants  un-
derstood  the  task.  After  the  fMRI  scanning,  participants  underwent  a 
sentence recognition task, in which they judged whether the sentences 
on the screen had appeared previously during the scanning section.

2.2.2. Verbal working memory task

We  employed  a  widely  used  N-back  paradigm  to  probe  neural 

Fig. 1. Procedure for the sentence comprehension and N-back tasks. (A) Stimulus presentations of Chinese sentence comprehension task. (B) Stimulus presentations 
of English sentence comprehension task. (C) Stimulus presentations of 0-back, 2-back, and 3-back conditions in the verbal working memory task.

4 

Z. Hou et al.                                                                                                                                                                                                                                     

NeuroImage 303 (2024) 120928 

activity for verbal working memory. The "n" refers to how many previ-
ous stimuli must be remembered. The experiment used digit numbers as 
stimuli and included 0-back, 2-back, and 3-back conditions. In the 0- 
back  condition,  the  participant  matched  the  current  stimulus  with  a 
pre-specified target number. In the 2-back and 3-back conditions, they 
determined whether the current stimulus corresponded to the one from 
two or three steps back, respectively.

Fig. 1C depicts the experimental procedure. The task consisted of two 
runs,  each  comprising  five  blocks  for  each  condition.  The  condition 
presentation  was  balanced  using  the  Latin  square  design.  Each  block 
started with a 2-second instruction and was followed by 11 trials. In each 
trial, a number was presented for 1 s, followed by a blank screen for 1 s. 
There was an 8-second rest after every three blocks. Each run lasted 6 
min and 38 s.

2.3. MRI data acquisition

Brain imaging data were acquired using a 3T Siemens Prisma system 
at the Magnetic Resonance Brain Imaging Center of Shenzhen Univer-
sity. A fast gradient echo sequence and a multi-band accelerated inter-
leaved scan were used to collect imaging data (repetition time [TR] =
1000 ms; echo time [TE] = 30 ms; flip angle = 35 deg; slice thickness = 2 
mm; slice number = 78; field of view (FOV) = 192 × 192 mm2; voxel 
size = 2 × 2 × 2 mm3). T1-weighted MPRAGE sequence structural im-
ages were also collected (FOV = 256 × 256 mm2; TR = 2300 ms; TE =
2.26 ms; sagittal slices number = 192; voxel size =1 × 1 × 1 mm3; flip 
angle = 8 deg).

2.4. MRI data analysis

2.4.1. Data preprocessing

The  fMRI  data  were  preprocessed  using  SPM12.  Slice  timing 
correction  was  first  performed  to  correct  the  acquisition  time  delay 
between slices within the same volume. The data were then realigned to 
correct head motion and obtained the six motion parameters. The T1 
structural image was segmented after coregistered to a mean functional 
image.  This  step  produced  deformation  fields,  which  were  used  to 
spatially  normalize  all  functional  images  onto  Montreal  Neurological 
Institute  (MNI)  space  and  resampled  with  2  × 2  × 2  resolution.  The 
normalized images were then spatially smoothed using a 6 mm FWHM 
Gaussian kernel to reduce spatial noise. For the MVPA, normalized but 
unsmoothed images were used to detect the information about the fine- 
grained pattern. The preprocessed data were used for statistical analysis 
at individual and group levels.

2.4.2. Univariate analysis for sentence processing: activation levels and 
adaptation effects

For  the  sentence  comprehension  task,  the  first-level  analysis 
involved constructing a general linear model of each subject’s data for 
each language to estimate the effect of the experimental conditions. The 
design matrix included two factors of interest: sentence order and sen-
tence  condition.  Sentence  order  contained  three  levels  (sentence  1, 
sentence  2,  sentence  3),  and  sentence  condition  contained  five  levels 
(SSen, SSyn, SSem, DSen, SPW). Realignment parameters were included 
as covariates in the model to regress out movement-related variance. A 
linear comparison of weights (1/4, 1/4, 1/4, 1/4, -1) was employed to 
estimate the activation of sentence processing for each subject relative to 
false font sequences. Adaptation effects were estimated by the reduction 
of brain signal from the first to the third sentences in the miniblocks, 
using the contrast of sentence 1 > sentence 3. A paired t-test was con-
ducted in the second-level analysis to examine differential adaptation 
effects  for  L1  and  L2.  In  addition,  based  on  the  results  of  parameter 
changes at the first level, we also examined the differences between the 
‘same conditions’ (SSen, SSyn, and SSem) and the ‘different condition’ 
(DSen)  to  identify  brain  areas  showing  more  adaptation  than  in  the 
‘‘different-sentences’’  condition.  Then,  t-tests  were  conducted  to 

examine activation differences across conditions at the second level.

2.4.3. Conjunction analysis of L1-L2 activation difference and verbal 
working memory

For the N-back verbal working memory task, univariate analysis was 
conducted across the whole brain to identify brain regions associated 
with changes in working memory load. At the individual level, a para-
metric  design  analysis  was  applied  to  quantify  the  varying  cognitive 
loads (assuming 0-back < 2-back < 3-back in terms of task demand). The 
group-level analysis was performed to generate a brain activation map, 
delineating areas that increased in activation as the working memory 
load increased.

To explore the relationship between L2-L1 activation differences and 
verbal  working  memory,  a  conjunction  analysis  was  performed  to 
identify overlaps between the L2-L1 activation differences and the brain 
activation associated with verbal working memory tasks. Overlapping 
regions may suggest that the processing of one language leans more on 
areas  associated  with  verbal  working  memory  compared  to  the  other 
language.  In  addition,  we  performed  Pearson  correlation  analyses  to 
assess  the  relationship  between  working  memory  performance  and 
extent of L2-L1 differential activation. We focused on the overlapping 
brain  regions,  including  bilateral  pars  triangularis  of  inferior  frontal 
gyrus (LIFGtri/RIFGtri), bilateral pars opercularis of inferior frontal gyrus 
(LIFGoper/RIFGoper),  left  superior  and  inferior  parietal  lobule  (LSPL/ 
LIPL),  left  middle  frontal  gyrus  (LMFG),  and  left  precentral  gyrus 
(Lprecentral). We extracted average beta values for each of the regions 
of interest, obtained contrast values for L2 > L1 in sentence processing, 
and then conducted Pearson correlation analyses with the accuracy rates 
for each of the three levels of the N-back task.

2.4.4. Multivariate pattern analyses

We used MVPA to examine whether different brain regions engaged 
in sentence processing differed in how robustly they represented L1 vs. 
L2 semantic/syntactic information. Correlation-based MVPA was used 
to  contrast  within-language  and  between-language  correlations.  This 
analysis was based on the assumption that if a brain region exhibits a 
stable  representation  of  specific  information,  neural  activation  from 
different runs would show high similarity of activation pattern in this 
region (e.g., Haxby et al., 2001). The following analysis was carried out 
separately for syntactic and semantic conditions. We divided each sub-
ject’s  data  into  two  subsets,  namely  odd  runs  and  even  runs,  and 
examined the similarity between the patterns of response evoked by the 
adaptation  effect  on  even  and  odd  runs.  Specifically,  contrast  values 
pertaining to the adaptation effect were extracted for each language, and 
the  similarity  of  activation  patterns  across  odd  and  even  runs  was 
assessed for the same language condition (within-language correlation) 
and different language conditions (between-language correlation). We 
then conducted paired t-tests to examine whether there were significant 
differences  between  within-language  and  between-language  correla-
tions.  If  a  within-language  correlation  is  significantly  greater  than  a 
between-languages correlation, it indicates a specific neural activation 
pattern in this region to a given language (for a similar rationale, see 
Fedorenko et al., 2012; Wang et al., 2021).

We applied MVPA to examine whether there were neural response 
patterns specific to L1 or L2 in the language-related regions. Based on 
the  activation  maps  in  our  study  and  the  neuroanatomical  model  of 
language  processing  (e.g.,  Friederici,  2012),  we  defined  15  canonical 
language-related brain regions as regions of interest (ROIs; as shown in 
Fig. S1). Within the frontal lobe, targeted areas included the left/right 
middle frontal gyrus (LMFG/RMFG), LIFGoper/RIFGoper, LIFGtri/RIFGtri, 
and the orbital part of left inferior frontal gyrus (LIFGorb). In the tem-
poral lobe, we focused on the bilateral superior temporal pole (LTPOsup 
and RTPOsup), left superior temporal gyrus (LSTG), left middle temporal 
gyrus (LMTG), and left inferior temporal gyrus (LITG). Additionally, the 
parietal  lobe  ROIs  encompassed  the  LSPL/LIPL  and  the  left  angular 
gyrus (LAG). To create ROI masks for our analysis, we first generated a 

5 

Z. Hou et al.                                                                                                                                                                                                                                     

NeuroImage 303 (2024) 120928 

group-level functional activation map for both the Chinese and English 
sentences  (FDR  correction  at  p  < 0.05).  This  allowed  us  to  identify 
common activated areas for the two languages, providing a consistent 
basis for subsequent comparisons of representation patterns. We then 
employed the AAL atlas within the WFU_Pick_Atlas tool (http://www. 
nitrc.org/projects/wfu_PickAtlas) to construct an anatomical ROI tem-
plate. We then integrated the activation map of L1 and L2 with the AAL 
templates. The ROI analysis results were Bonferroni-corrected to control 
for the false positive error rate due to multiple comparisons, with the 
significance  level  set  at  0.003  (calculated  by  dividing  0.05  by  the 
number of tested ROIs).

3. Results

3.1. Behavioral results

To ensure that the participants were actively engaged in the tasks, 
they were asked to perform an in-scanning sentence detection task and a 
post-scanning  sentence  recognition  task.  For  the  detection  task,  the 
omission rates for the Chinese and English tasks were 2.9% and 2.3%, 
respectively. For the post-scanning sentence recognition task, the par-
ticipants  achieved  accuracy  rates  of  72.9%  for  the  Chinese  task  and 
74.6% for the English task.

For  the  verbal  working  memory  task,  we  failed  to  record  the 
behavioral data of two participants due to a technical problem, such that 
the analysis of behavioral data for this task was based on 41 participants. 
Repeated measure ANOVA revealed significant differences in the accu-
racy rates (F (2,80) = 105.187, p < 0.001, η² = 0.724) and the response 
time (F (2, 80) = 145.539, p < 0.001, η² = 0.784) across the three levels of 

working  memory  load  (0-back,  2-back,  and  3-back).  Post-hoc  tests 
showed that the 0-back condition (mean accuracy = 98.8 ± 2.2%, mean 
reaction  time  = 483  ± 66  ms)  had  significantly  higher  accuracy  and 
shorter reaction time than the 2-back condition (mean accuracy = 89.3 
± 9.7%, mean reaction time = 668 ± 124 ms; p < 0.001) and 3-back 
condition (mean accuracy = 75.4 ± 12.7%, mean reaction time = 728 
± 120 ms; p < 0.001). The 2-back condition had higher accuracy and 
faster response time than the 3-back condition (both p < 0.001).

3.2. Activation levels in Chinese (L1) and English (L2) sentence 
comprehension

We conducted a whole-brain analysis to reveal the general activation 
patterns for Chinese (L1) and English (L2) by comparing brain activation 
associated  with  sentence  comprehension  relative  to  the  pseudo-word 
sequence conditions. The results showed that both L1 and L2 sentence 
processing activated extensive brain areas in the frontotemporal areas 
(Fig. 2A and Fig. 2B), including the left inferior and middle frontal gyri, 
bilateral superior and middle temporal gyri, left inferior parietal lobules, 
which are part of a broader network of brain regions involved. Notably, 
the  activation  patterns  in  the  prefrontal  and  temporal  regions  were 
predominantly  left-lateralized  in  both  languages.  When  directly 
comparing L1 and L2, we observed more pronounced activation during 
L2 processing, particularly in the left lateral prefrontal cortex extending 
into the primary motor cortex, bilateral posterior parietal cortex, and 
bilateral  occipitotemporal  cortices  (Fig.  2C).  However,  the  reverse 
contrast  of  L1  > L2  did  not  reveal  any  areas  of  significantly  greater 
activation during L1 processing.

Fig. 2. Brain activation of sentence processing and verbal working memory. (A) Brain activation of Chinese sentences (L1) relative to the pseudo-word sequence. (B) 
Brain activation of English sentences (L2) relative to the pseudo-word sequence. (C) Greater activation for English (L2) than Chinese (L1) sentence comprehension. 
The  reverse  contrast  showed  no  significant  greater  activation.  (D)  Brain  activation  associated  with  verbal  working  memory.  (E)  Conjunction  analysis  showing 
overlapping areas of C and D. The significant threshold is p < 0.05 FDR-corrected, cluster size ≥ 10. LMFG/RMFG: the left/right middle frontal gyrus; LIFG/RIFG: the 
left/right inferior frontal gyrus; LPL/RPL: the left/right parietal lobules.

6 

Z. Hou et al.                                                                                                                                                                                                                                     

NeuroImage 303 (2024) 120928 

3.3. Conjunction analysis of L1-L2 differences and verbal working 
memory

During the verbal working memory task, increasing processing load 
(0-back < 2-back < 3-back) was associated with activation mainly in 
bilateral superior frontal/middle frontal/inferior frontal gyrus, bilateral 
posterior parietal cortices, left posterior middle temporal gyrus, bilateral 
inferior temporal gyri, and sensorimotor areas (Fig. 2D).

We then conducted a conjunction analysis to identify common brain 
regions associated with L2 > L1 and verbal working memory. Results 
revealed  that  the  brain  areas  showing  greater  activation  for  L2 
compared to L1 were predominantly within the brain network activated 
during the verbal working memory task. Specifically, these overlapping 
areas included bilateral inferior and middle frontal gyri and superior/ 
inferior  parietal lobules (see  Fig. 2E). These  findings suggest  that the 
increased activation for L2 over L1, a phenomenon commonly reported 
in prior studies and observed in our research, may be due to the higher 
cognitive demands associated with L2 processing. Furthermore, corre-
lation  analyses  showed  that  the  extent  of  the  L2-L1  difference  was 
negatively correlated with accuracy on the 2-back working memory task 
in the inferior frontal and precentral gyri (see supplementary material, 
Fig. S2). The results suggested that participants who performed better in 
the 2-back working memory task also exhibited less differential activa-
tion for the two languages.

3.4. Syntactic and semantic adaptation effects in L1 and L2

We  first  compared  the  adaptation  effects  across  DSen  and  other 
conditions to identify brain areas that were specific to the adaptation 
effect. When SSen and DSen were compared, significant differences were 
observed  mainly  in  the  frontotemporal  cortices  in  both  Chinese  and 
English sentence processing (see supplementary material, Fig. S3).

We  then  examined  syntactic  and  semantic  adaptation  effects  by 
identifying brain regions where neural activities gradually decreased in 
response to syntactic and semantic repetition. The results are shown in 
Fig. 3A and Fig. 3B. Brain regions exhibiting repetition suppression were 
relatively consistent across syntactic and semantic conditions and across 
L1  and  L2,  mainly  including  the  bilateral  lateral  prefrontal  cortices 
extending  from  inferior  to  middle  frontal  gyri,  bilateral  superior  and 
middle  temporal  cortices,  and  bilateral  occipitotemporal  cortices. 
However, the extent of brain areas showing adaptation effects was more 
pronounced for L1 than L2.

We further directly compared the syntactic and semantic adaptation 
effects between L1 and L2. The results are shown in Fig. 3C. In contrast 
to the results of the direct comparison of activation level in section 3.2, 
we found greater adaptation effects for L1 than L2 for both syntactic and 
semantic  conditions,  mainly  in  the  middle  and  superior  temporal 

regions. However, we did not identify any regions where L2 exhibited 
greater repetition suppression than L1 for either syntactic or semantic 
conditions. Specifically, for syntactic processing, L1 demonstrated more 
pronounced adaptation in a few localized areas in the left superior and 
middle  temporal  gyri  and  the  right  inferior  frontal  gyrus.  Regarding 
semantic adaptation, L1 showed notably stronger effects than L2, pri-
marily in bilateral superior and middle temporal gyri, bilateral angular 
gyri, the left superior frontal gyrus, and the right middle/inferior frontal 
gyri.

3.5. Results of multivariate pattern analysis

The univariate analysis results indicated that activation and adap-
tation  patterns  were  largely  consistent  between  the  L1  and  L2,  with 
some variations observed across languages. We further used ROI-based 
MVPA to examine at a finer level whether the language brain regions 
exhibited  distinct  sensitivity  to  syntactic  or  semantic  representations 
and whether these patterns varied between L1 and L2. For the syntactic 
condition,  LITG  showed  significantly  higher  within-L1  correlations 
compared to between-language correlation (t(43)  = 3.917, p < 0.001), 
suggesting a stable and specific syntactic representation for L1 in this 
region. In contrast, the LIFGoper (t(43) = 3.704, p < 0.001), bilateral IFGtri 
(left: t(43) = 3.194, p = 0.001; right: t(43) = 3.159, p = 0.001), LTPOsup 
(t(43)  = 4.795,  p  < 0.001),  and  LSTG  (t(43)  = 4.928,  p  < 0.001) 
demonstrated  significantly  higher  within-L2  correlations  compared to 
between-language  correlations.  Particularly,  the  LSTG  also  showed 
higher  sensitivity  to  syntactic  representation  for  L2  than  L1  (t(43)  =
2.833,  p  = 0.003),  indicating  that  this  region  was  more  sensitive  to 
syntactic representation of L2 compared to L1 (see Fig. 4A).

For  the  semantic  condition,  the  within-L1  correlation  was  signifi-
cantly greater than the  between-language correlation  in the  temporal 
regions, including LSTG (t(43) = 3.256, p = 0.001), MTG (t(43) = 3.407, p 
= 0.001),  and  ITG  (t(43)  = 3.771,  p  < 0.001).  In  contrast,  within-L2 
correlations were significantly higher than the between-language cor-
relation in prefrontal and parietal regions, including the LIFGoper (t(43) =
4.764, p < 0.001), LIFGtri (t(43) = 3.623, p < 0.001), the LMFG (t(43) =
4.399, p < 0.001), the LSPL (t(43) = 3.111, p = 0.002), and the LIPL(t(43) 
= 3.955, p < 0.001). Besides, within-L2 correlations was significantly 
larger  than  within-L1  in  the  LMFG  (t(43)  = 3.195,  p  = 0.001)  and 
LIFGoper (t(43) = 2.936, p = 0.003; Fig. 4B).

4. Discussion

This study explored the neural representations of syntactic and se-
mantic information for L1 and L2 in Chinese-English bilinguals. We first 
examined the activation levels during sentence processing in both lan-
guages.  Although  similar  brain  regions  were  recruited  for  L1  and  L2 

Fig. 3. Results of univariate analysis for syntactic and semantic repetition suppression. Syntactic and semantic repetition suppression of (A) Chinese and (B) English. 
(C) Greater syntactic and semantic repetition suppression for L1 than L2. The significant threshold is p < 0.05 FDR-corrected, cluster size ≥ 10.

7 

Z. Hou et al.                                                                                                                                                                                                                                     

NeuroImage 303 (2024) 120928 

Fig. 4. Results of ROI-based multivariate pattern analyses. (A) Brain regions specific to L1 and L2 in syntactic representations. (B) Brain regions specific to L1 and L2 
in semantic representations. *p < 0.05, **p < 0.01, ***p < 0.001. The ROIs depicted in the figure are approximate representations.

8 

Z. Hou et al.                                                                                                                                                                                                                                     

NeuroImage 303 (2024) 120928 

sentence processing, L2 showed increased activation in the left lateral 
prefrontal cortex and bilateral posterior parietal cortices. Conjunction 
analysis indicated that this heightened activation for L2 predominantly 
occurred  within  the  brain  network  involved  in  the  verbal  working 
memory  task.  This  suggests  that  the  increased  L2  activation  over  L1 
might  stem  from  higher  cognitive  demands  in  processing  L2.  Our 
research  focused  on  using  adaptation  and  MVPA  methods  to  explore 
how neural representations may provide an interpretive framework for 
understanding  the  differences  between  L1  and  L2  in  bilinguals.  The 
analysis revealed a more pronounced adaptation for L1 than L2 for both 
syntactic and semantic conditions, primarily in the middle and superior 
temporal  regions.  Finally,  our  ROI-based  MVPA  further  revealed  that 
some ROIs in the language network displayed differential sensitivities to 
syntactic and semantic representations between L1 and L2. These find-
ings suggest that while L1 and L2 engage similar neural systems, finer 
representation analyses uncover distinct neural patterns for both syn-
tactic and semantic aspects in the two languages.

The  adaptation  approach  identified  brain  regions  that  exhibited 
neural  adaptation  in  response  to  repeated  syntactic  structures  or  se-
mantic content (Dufor and Rapp, 2013; Ma et al., 2014). Unlike tradi-
tional  subtraction  analyses,  which  compare  experimental  and  control 
conditions with varying amounts of linguistic information, the adapta-
tion approach allows for the detection of neuronal populations sensitive 
to the linguistic properties shared by consecutive stimuli (Chee, 2009; 
Devauchelle  et  al.,  2009;  Weber  and  Indefrey,  2009).  Although  the 
precise  physiological  mechanisms  underlying adaptation  in  the  BOLD 
signal are not yet fully understood, repetition suppression is generally 
believed to reflect either the facilitation of processing or the sharpening 
of an existing neural representation (Grill-Spector et al., 2006; Larsson 
et al., 2016). This phenomenon suggests that repeated stimuli can lead 
to  a  more  efficient  neural  response,  possibly  through  focusing  more 
precisely  on  the  essential  features  of  the  stimulus,  thereby  reducing 
overall  neural  activity.  We  found  that  both  L1  and  L2  sentence  pro-
cessing, whether it involved syntactic or semantic repetition, was asso-
ciated with reduced activation in brain regions of the bilateral lateral 
prefrontal and middle and superior temporal cortices. These areas are 
integral  to  the  classic  frontal-temporal  language  network  related  to 
sentence processing (Arana et al., 2020; Devauchelle et al., 2009; Dong 
et  al.,  2005;  Fedorenko  et  al.,  2010;  Friederici,  2012;  Menenti  et  al., 
2011; Tan et al., 2000, 2001).

Crucially,  when  comparing  the  syntactic  and  semantic  repetition 
suppression between L1 and L2, the results differ from previous research 
and those obtained from directly comparing activation levels between 
L1 and L2 in our study. While the direct comparison between the two 
languages revealed greater activation for L2 than L1 in the left lateral 
prefrontal cortex and bilateral posterior parietal cortices, the repetition 
suppression was consistently more robust for L1 than L2 in both syn-
tactic and semantic conditions. This heightened adaptation in L1 was 
particularly evident in the middle and superior temporal regions that are 
crucial  for  sentence  processing  (Friederici  et  al.,  2003;  Turker  et  al., 
2023).  These  findings  suggest  a  more  robust  neural  activation  in 
response  to  repetitive  linguistic  materials  in  the  native  language, 
potentially due to the deeper and more intuitive grasp of syntactic and 
semantic  information  in  L1.  Previous  studies  have  provided  evidence 
supporting this interpretation, indicating that the amount of adaptation 
effects  is  related  to  language  ability  across  normal  and  dyslexic  in-
dividuals  (Perrachione  et  al.,  2016),  as  well  as  the  extent  of  prior 
exposure  to  and  familiarity  with  the  language  stimuli  (Weber  et  al., 
2012, 2016). For example, Weber et al. (2012) showed that syntactic 
repetition effects in the left middle temporal gyrus varied with famil-
iarity with Dutch syntactic structures in non-native Dutch speakers. In 
another study (Weber et al., 2016) found that encountering a new syn-
tactic structure results in a gradual increase in neural activity in the left 
frontotemporal cortex as the structure is repeatedly stimulated, while 
for the repetition of familiar syntactic structures, the brain activity ex-
hibits  neuroadaptation.  This  differentiation  in  neural  responses 

indicates that repetition neural enhancement may be representative of 
the brain’s assimilation of novel syntactic structures, whereas repetition 
suppression  may  reflect  the  brain’s  efficiency  in  processing  familiar 
structures. In this study, participants had  an intermediate proficiency 
level  in  L2.  While  they  were  capable  of  understanding  complex  sen-
tences and passages in L2, their native language was likely more deeply 
ingrained, making it more responsive to repetitive linguistic stimuli.

We  initially  hypothesized  that  the  distinct  linguistic  features  of 
syntactic  structures  between  Chinese  and  English  may  result  in  more 
significant language differences in syntactic than semantic representa-
tions. However, the results of repetition suppression suggest a different 
scenario.  While  both  syntactic  and  semantic  processing  are  more 
robustly primed in the native language, it is the representation of se-
mantic information that shows a greater disparity between L1 and L2. 
One  explanation  for  this  result  is  that  semantic  information  is  more 
deeply rooted in the native linguistic framework than L2 and, thus, more 
sensitive and responsive to repeated linguistic stimuli during the task. 
Indeed, supporting evidence from Fedorenko et al. (2012) indicates that 
lexical-semantic information is more robustly represented than syntactic 
information  across  various  language  regions  during  native  language 
processing. An alternative explanation for the greater disparity between 
L1 and L2 in the semantic component is related to the specific charac-
teristics of the Chinese language, which belongs to a non-inflected lan-
guage  and  depends  extensively  on  contextual  semantics  to  convey 
meaning  (Li  and  Thompson,  1989).  Consequently,  native  Chinese 
speakers  who  learn  English  as  an  L2  might  depend  more  on 
lexical-semantic  information  to  understand  sentences  in  their  native 
language compared to English. Further comparative studies with varied 
language  pairings  are  necessary  to  determine  which  of  these  in-
terpretations holds more validity.

Our MVPA results revealed a finer brain response pattern of sensi-
tivity and specificity for L1 and L2. MVPA offers a sophisticated means of 
extracting information from brain imaging data by identifying patterns 
of brain activity across voxels or channels rather than merely capturing 
average responses (Kriegeskorte et al., 2006). This approach not only 
enhances sensitivity but also proved valuable in detecting the intricate 
and  distributed  neural  patterns  associated  with  complex  language 
functions (Fedorenko et al., 2012; Kim et al., 2020; Wang et al., 2021; Xu 
et al., 2017). Our study observed different patterns of L1-L2 comparison 
using  univariate  versus  multivariate  analysis  approaches.  While  uni-
variate  analysis  revealed  greater  activation  for  L2  than  L1,  which  is 
consistent with many prior neuroimage studies (Leonard et al., 2010; Liu 
et al., 2010; Liu and Cao, 2016; Saur et al., 2009; Sulpizio et al., 2020), 
the  MVPA analysis  revealed  more sophisticated  and intricative  repre-
sentation differences between the two languages. Although many of the 
ROIs demonstrated no clear preference for either L1 or L2, certain re-
gions did exhibit a greater sensitivity to one language over the other. 
This suggests that in some areas, the spatial patterns of neural activity 
represented L1 information more robustly, while in other areas, L2 in-
formation was more robustly represented.

Notably,  the  left  posterior  middle  and  superior  temporal  regions 
displayed stronger within-language correlations for semantic represen-
tations  in  L1  than  between-language  correlations.  This  pattern  aligns 
with the observed increase in semantic adaptation for L1 within these 
temporal regions. These brain areas are crucial for language processing, 
facilitating both lexical-level processing and sentence-level integration 
(Binder  et  al.,  2009;  Dronkers  et  al.,  2004;  Jefferies,  2013;  Matchin 
et al., 2019). They are involved in storing lexical information, semantic 
integration, and the construction of sentence structures (Binder et al., 
2009;  Fedorenko  et  al.,  2016;  Hagoort,  2017;  Matchin  and  Hickok, 
2020). Impairments in these regions can lead to significant deficits in 
language  comprehension  (Dronkers  et  al.,  2004).  A  recent  study  on 
aphasia underscored the importance of these posterior temporal areas in 
sentence comprehension over other areas, such as the inferior frontal 
gyrus (Wilson et al., 2023). Our findings suggest that there may be more 
efficient  storage  and  integration  of  semantic  information  during  L1 

9 

Z. Hou et al.                                                                                                                                                                                                                                     

NeuroImage 303 (2024) 120928 

sentence comprehension. This specialization could facilitate faster ac-
cess and more coherent semantic information integration in L1 than in 
L2,  contributing  to  smoother  and  more  efficient  language  processing. 
Additionally, the left inferior temporal region was more sensitive to L1 
for both semantic and syntactic representations. Previous studies have 
linked  this  area  to  the  processing  of  the  complex  visual  orthographic 
structure of Chinese characters (Bolger et al., 2005; Cao et al., 2013), 
indicating  that  the  inferior  temporal  region  may  have  specialized 
functions for processing the visual forms of Chinese characters, which 
are integral to accessing their semantic and syntactic properties.

In contrast, the within-language correlations for L2 were more pro-
nounced  in  the  prefrontal  and  posterior  parietal  regions  for  semantic 
representation  and  in  the  frontotemporal  regions  for  syntactic  repre-
sentation, indicating that these regions are more sensitive and adept at 
representing L2 information compared to L1. The findings provide a new 
perspective on the accommodation and assimilation patterns (Perfetti 
et al. 2007; Nelson et al., 2009), illustrating how neural representation 
patterns can encompass the subtle ways in which neural circuits respond 
to  linguistic  information  beyond  regional  activation  differences.  To 
some  extent,  the  Chinese-English  bilinguals  are  employing an  accom-
modation pattern for L2, relying on neural patterns different from those 
used for L1 processing. However, it is unclear whether this preferential 
pattern  is  specific  to  English  processing  in  Chinese-English  bilinguals 
due to typological differences, or if it reflects a general preference for L2, 
regardless  of  the  first  language.  Future  studies  with  English  speakers 
learning  Chinese  as  a  second language  could  help  clarify  these  possi-
bilities.  In  our  study,  it  is  still  possible  that  an  enhanced  level  of 
cognitive  control  is  required  during  L2  processing,  potentially  aug-
menting  the  within-language  correlations  observed  in  the  brain  areas 
associated  with  cognitive  control.  Nonetheless,  the  brain  regions  that 
exhibited preferential sensitivity to L2 do not completely overlap with 
those engaged in the verbal working memory task. These observations 
suggest that the greater sensitivity of L2 revealed in MVPA cannot be 
solely attributed to the increased effort or cognitive control mechanisms. 
Instead, they underscore the brain’s dynamic adaptation to the demands 
of language processing and representations (Kinno et al., 2008).

It should be noted that the preferential representations of a specific 
language in any region, as revealed by MVPA, do not indicate that the 
region  is  exclusively  recruited  for  that  language.  The  core  language 
systems  within  the  frontotemporal  cortices  are  engaged  for  both  lan-
guages  (Malik-Moraleda  et  al., 2022),  but the  finer patterns  could  be 
modulated by language features (Li et al., 2022; Xu et al., 2017). Pre-
vious studies using cross-language decoding methods have revealed that 
linguistic  distance  between  languages  could  affect  how  successfully  a 
model trained based on one language could be applied to predict the 
other language (see Xu et al., 2021, for a review). Therefore, while the 
overlapping  core  language  systems  are  involved  in  processing,  the 
dedicated neural representation of specific languages can be shaped by 
unique  features, 
individual  experiences 
(Połczy´nska and Bookheimer, 2021).

linguistic  distance,  and 

Although this study offers new insights into the neural representa-
tions in bilinguals, it is important to acknowledge certain limitations and 
directions for future studies. The first one concerns the generalizability 
of  our  findings.  Our  research  focused  on  Chinese-English  bilinguals, 
which may not fully capture the diversity of bilingual experiences and 
language  proficiency  levels  encountered  in  the  broader  population. 
Future studies should include a wider range of bilingual individuals with 
varying language backgrounds to better understand how these factors 
influence neural representations between different languages. A second 
limitation  is  that  the  experimental  materials  were  not  optimally 
matched between languages regarding word frequency, familiarity, and 
sentence length. Additionally, there was inconsistency in the syntactic 
structures used for the same syntax condition. While our focus was on 
emphatic  sentences  with the  "It was…  that"  structure,  we did  not ac-
count for whether the highlighted elements acted as the subject or object 
of  the  sentence.  Although  this  inconsistency  was  present  in  both  the 

10 

Chinese and English sentences, potentially reducing its impact on the 
comparative results, it could still have affected the amount of adaptation 
produced  by  syntactic  repetition  with  this  structure.  Thirdly,  our 
investigation  explored  the  neural  mechanisms  involved  in  language 
processing  and  working  memory,  but  did  not address  other  cognitive 
factors. The complexity of distinguishing cognitive from language pro-
cessing demands poses a challenge when interpreting our results. Future 
studies should consider additional cognitive factors, such as attention 
and inhibitory control, to disentangle the interplay between cognitive 
and linguistic factors in bilingual language processing.

To conclude, this study offers new insight into the neural represen-
tations  of  syntactic  and  semantic  information  in  Chinese-English  bi-
linguals.  Our  investigation  into  syntactic  and  semantic  adaptation 
effects  revealed  that  L1  demonstrated  stronger  adaptation  effects, 
particularly in the middle and superior temporal regions. This suggests a 
more entrenched and automatic neural response to repetitive linguistic 
structures in the native language. Furthermore, the application of MVPA 
revealed neural sensitivities for L1 and L2 across the classical language 
regions, highlighting that each language is characterized by distinctive 
finer neural representation patterns that can be influenced by the spe-
cific attributes of the syntactic and semantic components. Our research 
contributes to the existing body of knowledge on bilingualism and un-
derscores the complex relationships between language processing and 
working memory. It also suggests that the neural representations of se-
mantic and syntactic information for L2 could differ significantly from 
those of L1, highlighting the brain’s flexibility in adapting to different 
linguistic systems and underscoring the potential influence of the fea-
tures of different language components on neural representations.

CRediT authorship contribution statement

Zeqi  Hou:  Writing  –  review  &  editing,  Writing  –  original  draft, 
Visualization,  Validation, Project administration,  Methodology, Inves-
tigation,  Conceptualization.  Hehui  Li:  Writing  –  review  &  editing, 
Writing – original draft, Investigation, Formal analysis, Conceptualiza-
tion.  Lin  Gao:  Writing  –  review  &  editing,  Writing  –  original  draft, 
Visualization,  Validation,  Project  administration,  Methodology.  Jian 
Ou:  Project  administration,  Methodology,  Investigation.  Min  Xu: 
Writing  –  review  &  editing,  Writing  –  original  draft,  Visualization, 
Validation,  Supervision,  Methodology,  Investigation, Funding  acquisi-
tion, Conceptualization.

Declaration of competing interest

The authors declare that they have no conflict of interest.

Acknowledgment

for 

The 

Excellent 

This work was supported by the National Natural Science Foundation 
of China (32171054), Shenzhen Innovation in Science and Technology 
Scholars 
Foundation 
(RCYX20210706092043066),  Shenzhen-Hong  Kong  Institute  of  Brain 
Science-Shenzhen 
Institutions 
(2023SHIBS0003), Shenzhen Higher Institution Stability Support Plan 
(20220812111141001,  20231123133926001),  Guangdong  Basic  and 
Applied  Basic  Research  Foundation  (2024A1515011572).  We  would 
like to acknowledge the Magnetic Resonance Imaging Center at Shenz-
hen University.

Fundamental 

Research 

Youth 

Supplementary materials

Supplementary material associated with this article can be found, in 

the online version, at doi:10.1016/j.neuroimage.2024.120928.

Z. Hou et al.                                                                                                                                                                                                                                     

NeuroImage 303 (2024) 120928 

Data availability

Data will be made available on request. 

References

Abutalebi, J., 2008. Neural aspects of second language representation and language 
control. Acta Psychol. (Amst) 128 (3), 466–478. https://doi.org/10.1016/j. 
actpsy.2008.03.014.

Arana, S., Marquand, A., Hult´en, A., Hagoort, P., Schoffelen, J.M., 2020. Sensory 

modality-independent activation of the brain network for language. Journal of 
Neuroscience 40 (14), 2914–2924. https://doi.org/10.1523/JNEUROSCI.2271- 
19.2020.

Baddeley, A.D., 2017. Modularity, working memory and language acquisition. Second. 

Lang. Res. 33 (3), 299–311. https://doi.org/10.1177/0267658317709852.
Bick, A.S., Goelman, G., Frost, R., 2011. Hebrew brain vs. English brain: language 
modulates the way it is processed. J. Cogn. Neurosci. 23 (9), 2280–2290.
Binder, J.R., Desai, R.H., Graves, W.W., Conant, L.L., 2009. Where is the semantic 

system? A critical review and meta-analysis of 120 functional neuroimaging studies. 
Cerebral Cortex 19 (12), 2767–2796. https://doi.org/10.1093/cercor/bhp055.
Bolger, D.J., Perfetti, C.A., Schneider, W., 2005. Cross-cultural effect on the brain 

revisited: Universal structures plus writing system variation. Hum. Brain Mapp. 25 
(1), 92–104. https://doi.org/10.1002/hbm.20124.

Buchweitz, A., Mason, R.A., Hasegawa, M., Just, M.A., 2009. Japanese and English 

sentence reading comprehension and writing systems: An fMRI study of first and 
second language effects on brain activation. Bilingualism 12 (2), 141–151. https:// 
doi.org/10.1017/S1366728908003970.

Buchweitz, A., Shinkareva, S.V., Mason, R.A., Mitchell, T.M., Just, M.A., 2012. 

Identifying bilingual semantic neural representations across languages. Brain Lang. 
120 (3), 282–289. https://doi.org/10.1016/j.bandl.2011.09.003.

Calabria, M., Costa, A., Green, D.W., Abutalebi, J., 2018. Neural basis of bilingual 

language control. Ann. N. Y. Acad. Sci. 1426 (1), 221–235. https://doi.org/10.1111/ 
nyas.13879.

Cao, F., Tao, R., Liu, L., Perfetti, C.A., Booth, J.R., 2013. High Proficiency in a Second 
Language is Characterized by Greater Involvement of the First Language Network: 
Evidence from Chinese Learners of English. J. Cogn. Neurosci. 25 (10), 1649–1663. 
https://doi.org/10.1162/jocn_a_00414.

Chan, A.H.D., Luke, K.K., Li, P., Yip, V., Li, G., Weekes, B., Tan, L.H., 2008. Neural 

correlates of nouns and verbs in early bilinguals. Ann. N. Y. Acad. Sci. 1145, 30–40. 
https://doi.org/10.1196/annals.1416.000.

Chee, M.W., 2009. fMR-Adaptation and the bilingual brain. Brain Lang. 109 (2–3), 

75–79. https://doi.org/10.1016/j.bandl.2008.06.004.

Chee, M.W., Soon, C.S., Lee, H.L., Pallier, C., 2004. Left insula activation: a marker for 
language attainment in bilinguals. Proceedings of the National Academy of Sciences 
101 (42), 15265–15270. https://doi.org/10.1073/pnas.0403703101.

Correia, J., Formisano, E., Valente, G., Hausfeld, L., Jansma, B., Bonte, M., 2014. Brain- 

based translation: fMRI decoding of spoken words in bilinguals reveals language- 
independent semantic representations in anterior temporal lobe. Journal of 
Neuroscience 34 (1), 332–338. https://doi.org/10.1523/JNEUROSCI.1302-13.2014.
Crinion, J., Turner, R., Grogan, A., Hanakawa, T., Noppeney, U., Devlin, J.T., Aso, T., 
Urayama, S., Fukuyama, H., Stockton, K., Usui, K., Green, D.W., Price, C.J., 2006. 
Language Control in the Bilingual Brain. Science 312 (5779), 1537–1540. https:// 
doi.org/10.1126/science.1127761.

Dapretto, M., Bookheimer, S.Y., 1999. Form and content: Dissociating syntax and 

semantics in sentence comprehension. Neuron 24 (2), 427–432. https://doi.org/ 
10.1016/S0896-6273(00)80855-7.

Devauchelle, A.D., Oppenheim, C., Rizzi, L., Dehaene, S., Pallier, C., 2009. Sentence 
syntax and content in the human temporal lobe: An fMRI adaptation study in 
auditory and visual modalities. J. Cogn. Neurosci. 21 (5), 1000–1012. https://doi. 
org/10.1162/jocn.2009.21070.

Dong, Y., Nakamura, K., Okada, T., Hanakawa, T., Fukuyama, H., Mazziotta, J.C., 

Shibasaki, H., 2005. Neural mechanisms underlying the processing of Chinese words: 
An fMRI study. Neurosci. Res. 52 (2), 139–145. https://doi.org/10.1016/j. 
neures.2005.02.005.

Dronkers, N.F., Wilkins, D.P., Van Valin, R.D., Redfern, B.B., Jaeger, J.J., 2004. Lesion 
analysis of the brain areas involved in language comprehension. Cognition 92 (1–2), 
145–177. https://doi.org/10.1016/j.cognition.2003.11.002.

Dufor, O., Rapp, B., 2013. Letter representations in writing: an fMRI adaptation 

approach. Front. Psychol. 4, 1–14. https://doi.org/10.3389/fpsyg.2013.00781. 
October. 

Fedorenko, E., Hsieh, P.J., Nieto-Casta˜n´on, A., Whitfield-Gabrieli, S., Kanwisher, N., 

2010. New method for fMRI investigations of language: defining ROIs functionally in 
individual subjects. J. Neurophysiol. 104 (2), 1177–1194. https://doi.org/10.1152/ 
jn.00032.2010.

Fedorenko, E., Nieto-Casta˜non, A., Kanwisher, N., 2012. Lexical and syntactic 

representations in the brain: An fMRI investigation with multi-voxel pattern 
analyses. Neuropsychologia 50 (4), 499–513. https://doi.org/10.1016/j. 
neuropsychologia.2011.09.014.

Fedorenko, E., Scott, T.L., Brunner, P., Coon, W.G., Pritchett, B., Schalk, G., 

Kanwisher, N., 2016. Neural correlate of the construction of sentence meaning. 
Proceedings of the National Academy of Sciences 113 (41), E6256–E6262. https:// 
doi.org/10.1073/pnas.1612132113.

Fodor, J.D., Ni, W., Crain, S., Shankweiler, D., 1996. Tasks and Timing in the Perception 
of Linguistic Anomaly. J. Psycholinguist. Res. 25 (1), 25–57. https://doi.org/ 
10.1007/BF01708419.

Friederici, A.D., 2002. Towards a neural basis of auditory sentence processing. Trends. 

Cogn. Sci. 6 (2), 78–84. https://doi.org/10.1016/S1364-6613(00)01839-8.
Friederici, A.D., 2012. The cortical language circuit: From auditory perception to 
sentence comprehension. Trends. Cogn. Sci. 16 (5), 262–268. https://doi.org/ 
10.1016/j.tics.2012.04.001.

Friederici, A.D., Meyer, M., Von Cramon, D.Y., 2000. Auditory language comprehension: 
An event-related fMRI study on the processing of syntactic and lexical information. 
Brain Lang. 74 (2), 289–300. https://doi.org/10.1006/brln.2000.2313.

Friederici, A.D., Rüschemeyer, S.A., Hahne, A., Fiebach, C.J., 2003. The role of left 

inferior frontal and superior temporal cortex in sentence comprehension: Localizing 
syntactic and semantic processes. Cerebral Cortex 13 (2), 170–177. https://doi.org/ 
10.1093/cercor/13.2.170.

Grill-Spector, K., Henson, R., Martin, A., 2006. Repetition and the brain: neural models of 
stimulus-specific effects. Trends. Cogn. Sci. 10 (1), 14–23. https://doi.org/10.1016/ 
j.tics.2005.11.006.

Guttentag, R.E., Haith, M.M., Goodman, G.S., Hauch, J., 1984. Semantic processing of 
unattended words by bilinguals: A test of the input switch mechanism. J. Verbal. 
Learning. Verbal. Behav. 23 (2), 178–188. https://doi.org/10.1016/S0022-5371(84) 
90126-9.

Hagoort, P., 2017. The core and beyond in the language-ready brain. Neuroscience & 

Biobehavioral Reviews 81, 194–204. https://doi.org/10.1016/j. 
neubiorev.2017.01.048.

Hagoort, P., Indefrey, P., 2014. The neurobiology of language beyond single words. Annu 
Rev. Neurosci. 37, 347–362. https://doi.org/10.1146/annurev-neuro-071013- 
013847. May. 

Haxby, J.V., 2012. Multivariate pattern analysis of fMRI: the early beginnings. 

Neuroimage 62 (2), 852–855. https://doi.org/10.1016/j.neuroimage.2012.03.016.

Haxby, J.V., Gobbini, M.I., Furey, M.L., Ishai, A., Schouten, J.L., Pietrini, P., 2001. 

Distributed and overlapping representations of faces and objects in ventral temporal 
cortex. Science 293 (5539), 2425–2430. https://doi.org/10.1126/science.1063736.
Humphries, C., Binder, J.R., Medler, D.A., Liebenthal, E., 2006. Syntactic and semantic 
modulation of neural activity during auditory sentence comprehension. J. Cogn. 
Neurosci. 18 (4), 665–679. https://doi.org/10.1162/jocn.2006.18.4.665.

Humphries, C., Love, T., Swinney, D., Hickok, G., 2005. Response of anterior temporal 

cortex to syntactic and prosodic manipulations during sentence processing. Hum. 
Brain Mapp. 26 (2), 128–138. https://doi.org/10.1002/hbm.20148.

Humphries, C., Willard, K., Buchsbaum, B., Hickok, G., 2001. Role of anterior temporal 
cortex in auditory sentence comprehension: An fMRI study. Neuroreport 12 (8), 
1749–1752. https://doi.org/10.1097/00001756-200106130-00046.

Jefferies, E., 2013. The neural basis of semantic cognition: Converging evidence from 

neuropsychology, neuroimaging and TMS. Cortex 49 (3), 611–625. https://doi.org/ 
10.1016/j.cortex.2012.10.008.

Jeong, H., Sugiura, M., Sassa, Y., Haji, T., Usui, N., Taira, M., Horie, K., Sato, S., 

Kawashima, R., 2007. Effect of syntactic similarity on cortical activation during 
second language processing: A comparison of English and Japanese among native 
Korean trilinguals. Hum. Brain Mapp. 28 (3), 194–204. https://doi.org/10.1002/ 
hbm.20269.

Just, M.A., Carpenter, P.A., 1992. A capacity theory of comprehension: Individual 

differences in working memory. Psychol. Rev. 99 (1), 122–149. https://doi.org/ 
10.1037/0033-295X.99.1.122.

Kaan, E., Swaab, T.Y., 2002. The brain circuitry of syntactic comprehension. Trends. 
Cogn. Sci. 6 (8), 350–356. https://doi.org/10.1016/S1364-6613(02)01947-2.
Kim, S.Y., Liu, L., Liu, L., Cao, F., 2020. Neural representational similarity between L1 
and L2 in spoken and written language processing. Hum. Brain Mapp. 41 (17), 
4935–4951. https://doi.org/10.1002/hbm.25171.

Kim, S.Y., Qi, T., Feng, X., Ding, G., Liu, L., Cao, F., 2016. How does language distance 

between L1 and L2 affect the L2 brain network? An fMRI study of 
Korean–Chinese–English trilinguals. Neuroimage 129, 25–39. https://doi.org/ 
10.1016/j.neuroimage.2015.11.068.

King, J., 1991. Individual differences in syntactic processing:The role of working 

memory. J. Mem. Lang. 580–602.

Kinno, R., Kawamura, M., Shioda, S., Sakai, K.L., 2008. Neural correlates of noncanonical 
syntactic processing revealed by a picture-sentence matching task. Hum. Brain 
Mapp. 29 (9), 1015–1027. https://doi.org/10.1002/hbm.20441.

Klein, D., Zatorre, R.J., Chen, J.K., Milner, B., Crane, J., Belin, P., Bouffard, M., 2006. 

Bilingual brain organization: A functional magnetic resonance adaptation study. 
Neuroimage 31 (1), 366–375. https://doi.org/10.1016/j.neuroimage.2005.12.012.
Kriegeskorte, N., Goebel, R., Bandettini, P., 2006. Information-based functional brain 
mapping. Proc. Natl. Acad. Sci. u S. a 103 (10), 3863–3868. https://doi.org/ 
10.1073/pnas.0600244103.

Kroll, J.F., Dussias, P.E., Bice, K., Perrotti, L., 2015. Bilingualism, Mind, and Brain. Annu. 
Rev. Linguist. 1, 377–394. https://doi.org/10.1146/annurev-linguist-030514- 
124937.

Larsson, J., Solomon, S.G., Kohn, A., 2016. fMRI adaptation revisited. Cortex 80, 

154–160. https://doi.org/10.1016/j.cortex.2015.10.026.

Leonard, M.K., Brown, T.T., Travis, K.E., Gharapetian, L., Hagler, D.J., Dale, A.M., 
Elman, J.L., Halgren, E., 2010. Spatiotemporal dynamics of bilingual word 
processing. Neuroimage 49 (4), 3286–3294. https://doi.org/10.1016/j. 
neuroimage.2009.12.009.

Lewis, R.L., Vasishth, S., Van Dyke, J.A., 2006. Computational principles of working 

memory in sentence comprehension. Trends. Cogn. Sci. 10 (10), 447–454. https:// 
doi.org/10.1016/j.tics.2006.08.007.

11 

Z. Hou et al.                                                                                                                                                                                                                                     

NeuroImage 303 (2024) 120928 

Li, C.N., Thompson, S.A., 1989. Mandarin Chinese: A functional reference grammar. 

University of California Press, Berkeley. 

Li, P., Legault, J., Litcofsky, K.A., 2014. Neuroplasticity as a function of second language 
learning: Anatomical changes in the human brain. Cortex 58, 301–324. https://doi. 
org/10.1016/j.cortex.2014.05.001.

Li, P., Zhang, F., Yu, A., Zhao, X., 2020. Language History Questionnaire (LHQ3): An 

enhanced tool for assessing multilingual experience. Bilingualism 23 (5), 938–944. 
https://doi.org/10.1017/S1366728918001153.

Li, X., Huang, L., Yao, P., Hy¨on¨a, J., 2022. Universal and specific reading mechanisms 
across different writing systems. Nat. Rev. Psychol. 1 (3), 133–144. https://doi.org/ 
10.1038/s44159-022-00022-6.

Liu, H., Cao, F., 2016. L1 and L2 processing in the bilingual brain: A meta-analysis of 

neuroimaging studies. Brain Lang. 159, 60–73. https://doi.org/10.1016/j. 
bandl.2016.05.013.

Liu, H., Hu, Z., Guo, T., Peng, D., 2010. Speaking words in two languages with one brain: 
Neural overlap and dissociation. Brain Res. 1316, 75–82. https://doi.org/10.1016/j. 
brainres.2009.12.030.

Sawamura, H., Orban, G.A., Vogels, R., 2006. Selectivity of neuronal adaptation does not 
match response selectivity: A single-cell study of the fMRI adaptation paradigm. 
Neuron 49 (2), 307–318. https://doi.org/10.1016/j.neuron.2005.11.028.
Sulpizio, S., Del Maschio, N., Fedeli, D., Abutalebi, J., 2020. Bilingual language 

processing: A meta-analysis of functional neuroimaging studies. Neurosci. Biobehav. 
Rev. 108, 834–853. https://doi.org/10.1016/j.neubiorev.2019.12.014. December 
2019. 

Tan, L.H., Liu, H., Perfetti, C.A., Spinks, J.A., Fox, P.T., Gao, J., 2001. The Neural System 
Underlying Chinese Logograph Reading. Neuroimage 13 (5), 836–846. https://doi. 
org/10.1006/nimg.2001.0749.

Tan, L.H., Spinks, J.A., Feng, C.M., Siok, W.T., Perfetti, C.A., Xiong, J., Fox, P.T., Gao, J. 
H., 2003. Neural systems of second language reading are shaped by native language. 
Hum. Brain Mapp. 18 (3), 158–166. https://doi.org/10.1002/hbm.10089.

Tan, L.H., Spinks, J.A., Gao, J.-H., Liu, H.-L., Perfetti, C.A., Xiong, J., Stofer, K.A., Pu, Y., 
Liu, Y., Fox, P.T., 2000. Brain activation in the processing of Chinese characters and 
words: A functional MRI study. Hum. Brain Mapp. 10 (1), 16. https://doi.org/ 
10.1002/(sici)1097-0193(200005)10:1<16::aid-hbm30>3.3.co;2-d.

Liu, Y, Dunlap, S, Fiez, J, Perfetti, C., 2007. Evidence for neural accommodation to a 

Turker, S., Kuhnke, P., Eickhoff, S.B., Caspers, S., Hartwigsen, G., 2023. Cortical, 

writing system following learning. Hum. Brain Mapp. 28, 1223–1234.

Luke, K.K., Liu, H.L., Wai, Y.Y., Wan, Y.L., Tan, L.H., 2002. Functional anatomy of 

syntactic and semantic processing in language comprehension. Hum. Brain Mapp. 16 
(3), 133–145. https://doi.org/10.1002/hbm.10029.

Ma, N., Baetens, K., Vandekerckhove, M., Kestemont, J., Fias, W., Van Overwalle, F., 
2014. Traits are represented in the medial prefrontal cortex: An fMRI adaptation 
study. Soc. Cogn. Affect. Neurosci. 9 (8), 1185–1192. https://doi.org/10.1093/scan/ 
nst098.

Mahmoudi, A., Takerkart, S., Regragui, F., Boussaoud, D., Brovelli, A., 2012. Multivoxel 
pattern analysis for fMRI data: A review. Comput. Math. Methods Med. https://doi. 
org/10.1155/2012/961257. 2012. 

Malik-Moraleda, S., Ayyash, D., Gall´ee, J., Affourtit, J., Hoffmann, M., Mineroff, Z., 

Fedorenko, E., 2022. An investigation across 45 languages and 12 language families 
reveals a universal language network. Nat. Neurosci. 25 (8), 1014–1019. https://doi. 
org/10.1038/s41593-022-01114-5.

Matchin, W., Brodbeck, C., Hammerly, C., Lau, E., 2019. The temporal dynamics of 

structure and content in sentence comprehension: Evidence from fMRI-constrained 
MEG. Hum. Brain Mapp. 40 (2), 663–678. https://doi.org/10.1002/hbm.24403.
Matchin, W., Hickok, G., 2020. The cortical organization of syntax. Cerebral Cortex 30 

(3), 1481–1498. https://doi.org/10.1093/cercor/bhz180.

McDonald, J.L., 2006. Beyond the critical period: Processing-based explanations for poor 

grammaticality judgment performance by late second language learners. J. Mem. 
Lang. 55 (3), 381–401. https://doi.org/10.1016/j.jml.2006.06.006.

Meisel, J.M., 2006. The bilingual child. In: Bhatia, T.K., Ritchie, W.C. (Eds.), The 
handbook of bilingualism. Blackwell Publishing Ltd, Malden, MA, pp. 91–113.
Menenti, L., Gierhan, S.M.E., Segaert, K., Hagoort, P., 2011. Shared language: Overlap 
and segregation of the neuronal infrastructure for speaking and listening revealed by 
functional MRI. Psychol. Sci. 22 (9), 1173–1182. https://doi.org/10.1177/ 
0956797611418347.

Meschyan, G., Hernandez, A.E., 2006. Impact of language proficiency and orthographic 
transparency on bilingual word reading: An fMRI investigation. Neuroimage 29 (4), 
1135–1140. https://doi.org/10.1016/j.neuroimage.2005.08.055.

Nelson, J.R., Liu, Y., Fiez, J., Perfetti, C.A., 2009. Assimilation and accommodation 
patterns in ventral occipitotemporal cortex in learning a second writing system. 
Hum. Brain Mapp. 30 (3), 810–820. https://doi.org/10.1002/hbm.20551.

Norman, K.A., Polyn, S.M., Detre, G.J., Haxby, J.V., 2006. Beyond mind-reading: multi- 
voxel pattern analysis of fMRI data. Trends. Cogn. Sci. 10 (9), 424–430. https://doi. 
org/10.1016/j.tics.2006.07.005.

Perani, D., Abutalebi, J., 2005. The neural basis of first and second language processing. 

Curr. Opin. Neurobiol. 15 (2), 202–206. https://doi.org/10.1016/j. 
conb.2005.03.007.

Perfetti, CA, Liu, Y, Fiez, J, Nelson, J, Bolger, DJ, Tan, L-H., 2007. Reading in two writing 

systems: Accommodation and assimilation of the brain’s reading network. 
Bilingualism: Language and Cognition 10, 131–146. https://doi.org/10.1017/ 
S1366728907002891.

Perrachione, T.K., Del Tufo, S.N., Winter, R., Murtagh, J., Cyr, A., Chang, P., Gabrieli, J. 

D., 2016. Dysfunction of rapid neural adaptation in dyslexia. Neuron 92 (6), 
1383–1397. https://doi.org/10.1016/j.neuron.2016.11.020.

Pickering, M.J., Ferreira, V.S., 2008. Structural Priming: A Critical Review. Psychol. Bull. 

134 (3), 427–459. https://doi.org/10.1037/0033-2909.134.3.427.

Połczy´nska, M.M., Bookheimer, S.Y., 2021. General principles governing the amount of 

neuroanatomical overlap between languages in bilinguals. Neuroscience & 
Biobehavioral Reviews 130, 1–14. https://doi.org/10.1016/j. 
neubiorev.2021.08.005.

Santi, A., Grodzinsky, Y., 2010. fMRI adaptation dissociates syntactic complexity 
dimensions. Neuroimage 51 (4), 1285–1293. https://doi.org/10.1016/j. 
neuroimage.2010.03.034.

Saur, D., Baumgaertner, A., Moehring, A., Büchel, C., Bonnesen, M., Rose, M., Musso, M., 
Meisel, J.M., 2009. Word order processing in the bilingual brain. Neuropsychologia 
47 (1), 158–168. https://doi.org/10.1016/j.neuropsychologia.2008.08.007.

subcortical, and cerebellar contributions to language processing: A meta-analytic 
review of 403 neuroimaging experiments. Psychol. Bull. 149 (11–12), 699–723. 
https://doi.org/10.1037/bul0000403.

Van de Putte, E., De Baene, W., Price, C.J., Duyck, W., 2018. Neural overlap of L1 and L2 

semantic representations across visual and auditory modalities: a decoding 
approach. Neuropsychologia 113, 68–77. https://doi.org/10.1016/j. 
neuropsychologia.2018.03.037.

Van Heuven, W.J.B., Schriefers, H., Dijkstra, T., Hagoort, P., 2008. Language conflict in 
the bilingual brain. Cerebral Cortex 18 (11), 2706–2716. https://doi.org/10.1093/ 
cercor/bhn030.

Vandenberghe, R., Nobre, A.C., Price, C.J., 2002. The response of left temporal cortex to 

sentences. J. Cogn. Neurosci. 14 (4), 550–560. https://doi.org/10.1162/ 
08989290260045800.

Vargas, R., Just, M.A., 2022. Similarities and differences in the neural representations of 

abstract concepts across English and Mandarin. Hum. Brain Mapp. 43 (10), 
3195–3206. https://doi.org/10.1002/hbm.25844.

Wagley, N., Hu, X., Satterfield, T., Bedore, L.M., Booth, J.R., Kovelman, I., 2024. Neural 
specificity for semantic and syntactic processing in Spanish-English bilingual 
children. Brain Lang. 250, 105380. https://doi.org/10.1016/j.bandl.2024.105380.
Wang, J., Lin, H., Cai, Q., 2023. How Grammar Conveys Meaning: Language-Specific 

Spatial Encoding Patterns and Cross-Language Commonality in Higher-Order Neural 
Space. The Journal of Neuroscience 43 (46), 7831–7841. https://doi.org/10.1523/ 
jneurosci.0599-23.2023.

Wang, J., Wagley, N., Rice, M.L., Booth, J.R., 2021. Semantic and syntactic specialization 
during auditory sentence processing in 7-8-year-old children. Cortex 145, 169–186. 
https://doi.org/10.1016/j.cortex.2021.09.006.

Weber, K., Christiansen, M.H., Petersson, K.M., Indefrey, P., Hagoort, P., 2016. fMRI 
syntactic and lexical repetition effects reveal the initial stages of learning a new 
language. Journal of Neuroscience 36 (26), 6872–6880. https://doi.org/10.1523/ 
JNEUROSCI.3180-15.2016.

Weber, K., Indefrey, P., 2009. Syntactic priming in German-English bilinguals during 

sentence comprehension. Neuroimage 46 (4), 1164–1172. https://doi.org/10.1016/ 
j.neuroimage.2009.03.040.

Weber, K.M., 2012. The language learning brain: Evidence from second language and 
bilingual studies of syntactic processing. Nijmegen, The Netherlands: Radboud 
University Nijmegen.

Wilson, S.M., Entrup, J.L., Schneck, S.M., Onuscheck, C.F., Levy, D.F., Rahman, M., 

Kirshner, H.S., 2023. Recovery from aphasia in the first year after stroke. Brain 146 
(3), 1021–1039. https://doi.org/10.1093/brain/awac129.

Xu, M., Baldauf, D., Chang, C.Q., Desimone, R., Tan, L.H., 2017. Distinct Distributed 

patterns of neural activity are associated with two languages in the bilingual brain. 
Sci. Adv. (7), 3. https://doi.org/10.1126/sciadv.1603309.

Xu, M., Li, D., Li, P., 2021. Brain decoding in multiple languages: Can cross-language 
brain decoding work? Brain Lang. 215, 104922. https://doi.org/10.1016/j. 
bandl.2021.104922.

Yang, Y., Wang, J., Bailer, C., Cherkassky, V., Just, M.A., 2017. Commonalities and 
differences in the neural representations of English, Portuguese, and Mandarin 
sentences: When knowledge of the brain-language mappings for two languages is 
better than one. Brain Lang. 175, 77–85. https://doi.org/10.1016/j. 
bandl.2017.09.007.

Zhan, M., Pallier, C., Agrawal, A., Dehaene, S., Cohen, L., 2023. Does the visual word 
form area split in bilingual readers? A millimeter-scale 7-T fMRI study. Sci. Adv. 9 
(14), eadf6140.

Zhu, Y., Xu, M., Lu, J., Hu, J., Kwok, V.P.Y., Zhou, Y., Yuan, D., Wu, B., Zhang, J., Wu, J., 

Tan, L.H., 2022. Distinct spatiotemporal patterns of syntactic and semantic 
processing in human inferior frontal gyrus. Nat. Hum. Behav. 6 (8), 1104–1111. 
https://doi.org/10.1038/s41562-022-01334-6.

12 

