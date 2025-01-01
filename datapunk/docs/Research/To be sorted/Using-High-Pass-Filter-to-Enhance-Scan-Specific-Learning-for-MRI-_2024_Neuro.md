NeuroImage 303 (2024) 120926 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

Using High-Pass Filter to Enhance Scan Specific Learning for MRI 
Reconstruction without Any Extra Training Data

Zhaoyang Jin a,*, Jiuwen Cao a, Mei Zhang a, Qing-San Xiang b
a Machine Learning and I-health International Cooperation Base of Zhejiang Province, School of Automation, Hangzhou Dianzi University, Hangzhou, Zhejiang, PR China
b Department of Radiology, University of British Columbia, Vancouver, BC, Canada

A R T I C L E  I N F O

A B S T R A C T

Key words:
convolutional neural network
high-pass filter
deep learning
fast MRI
RAKI
HP-RAKI

In accelerated MRI, the robust artificial-neural-network for k-space interpolation (RAKI) method is an attractive 
learning-based reconstruction that does not require additional training data. This study was focused on obtaining 
high quality MR images from regular under-sampled multi-coil k-space data using a high-pass filtered RAKI (HP- 
RAKI) reconstruction without any extra training data. MRI scan from human subjects was under-sampled with a 
regular pattern using skipped phase encoding and a fully sampled k-space center. A high-pass (HP) filter was 
applied in k-space to reduce image support to facilitate linear prediction. The HP filtered k-space center was used 
to train the RAKI network without any extra training data. The unacquired k-space data can be predicted from a 
trained RAKI network with optimized parameters. Final reconstruction was obtained after performing an inverse 
HP  filtering  for the  predicted  k-space  data. This  HP-RAKI  method can  be  extended  to  corresponding  residual 
structure (HP-rRAKI). HP-RAKI was compared with GRAPPA, HP-GRAPPA, RAKI and MW-RAKI algorithms, and 
HP-rRAKI was compared with corresponding residual extensions, including rRAKI and MW-rRAKI, all qualita-
tively and quantitatively using visual inspection and such metrics as SSIM and PSNR. HP-RAKI and HP-rRAKI 
were  found  to  be  effective  in  reconstructing  MR  images  even  at  high  acceleration  factors.  HP-RAKI  and  HP- 
rRAKI  compared  favorably  with  other  algorithms.  Using  high-pass  filtered  central  k-space  data  for  training, 
HP-RAKI offers higher reconstruction quality for regularly under-sampled multi-coil k-space data without any 
extra training data. It has shown promising capabilities for fast MRI applications, especially those lacking fully 
sampled training data.

1. Introduction

Although  many  fast  techniques  have  been  proposed,  MRI  is  still 
limited  by  its  long  scan  time  (Bernstein  et  al.,  2004;  Haldar  and  Set-
sompop, 2020; Liang et al., 1992). In recent years, deep learning (DL) 
methods have attracted interest of researchers in fast MRI, since they can 
reconstruct  MR  images  with  high  quality  by  effectively  training  pa-
rameters of convolutional neural networks (LeCunY et al., 2017; Wang 
et al., 2016).

DL-based  MRI reconstruction  methods  usually  require  collecting a 
large  set  of  fully  sampled  data  for  training  (Aggarwal  et  al.,  2019; 
Hammernik  et  al.,  2018;  Han  et  al.,  2019;  Jin  and  Xiang,  2023;  Min 
et  al.,  2018;  Wang  et  al.,  2016).  However,  such  requirement  may  be 
difficult to meet for many MRI applications. Moreover, it is often very 
time  consuming  to  train  a  convolutional  neural  network  (CNN), 

depending on the complexity of the network, epoch number, batch size, 
or  size  of  training  data,  etc.  For  example,  it  often  took  about  several 
hours, even several days, to train a CNN. Retraining is often required 
after  changing  acquisition  parameters  in  fast  MRI  with  DL-based 
reconstructions.

Considering the above factors, researchers began to ask whether the 
amount of training data could be largely reduced, and the possibility for 
training with only the acquired under-sampled data, without any extra 
training data.

It is well known that the traditional GRAPPA algorithm reconstructs 
images for multi-coil fast MRI by recovering unacquired k-space data 
using linear interpolation (Griswold et al., 2002). Fully sampled k-space 
center  is  used  as  auto-calibration  signal  (ACS)  for  GRAPPA  re-
constructions.  Benefitting  from  linear  predictability  theory  (Haacke 
et al., 1989; Haldar and Setsompop, 2020; Liang et al., 1989) that there 

* Address correspondence to: Zhaoyang Jin, Ph.D., School of Automation, Hangzhou Dianzi University, Hangzhou, Zhejiang, PR China, Tel: 86-571-86919131, Fax: 

86-571-86878566

E-mail address: jinzhaoyang@hdu.edu.cn (Z. Jin). 

https://doi.org/10.1016/j.neuroimage.2024.120926
Received in revised form 25 September 2024; Accepted 11 November 2024  
Available online 14 November 2024 
1053-8119/© 2024 The Author(s).  Published by Elsevier Inc.  This is an open access article under the CC BY-NC license ( http://creativecommons.org/licenses/by- 
nc/4.0/ ). 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

exist  shift-invariant  linear  interpolation  relationships  in  k-space, 
weights  obtained  from  linear  fitting  process  can  be  used  to  generate 
missing  lines  for  each  coil  from  the  acquired  multi-coil  k-space  data. 
GRAPPA used data from multiple lines of all coils to fit ACS lines in a 
single  coil  to  produce  interpolation  weights  for  corresponding  coil. 
Several  other  well-known  linear  interpolation  techniques,  such  as 
SPIRiT  (Lustig  and  Pauly,  2010),  PRUNO  (Zhang  et  al.,  2011),  and 
AC-LORAKS  (Haldar,  2015a)  were  proposed  to  further  improve  the 
GRAPPA algorithm.

GRAPPA  can  also  be  equivalently  viewed  as  a  single-layer  CNN 
without  bias  terms  or  activation  functions.  Inspired  by  GRAPPA  and 
deep learning methods, a scan specific robust artificial neural network 
for non-linear k-space interpolation (RAKI) reconstruction was proposed 
(Akçakaya  et  al.,  2019),  which  extends  GRAPPA  by  using  multiple 
convolution  layers  along  with  rectified  linear  unit  (ReLU)  activation 
functions. RAKI trains the CNN by using only the fully sampled k-space 
center and does not require any extra training data.

Several extension methods of RAKI have been proposed to further 
improve its reconstruction quality. An alternative CNN architecture was 
proposed to interpolate all output channels jointly for specific skipped k- 
space  lines.  Computational  time  was  reduced  by  using  CPU  multi- 
processing  and  process  pooling  to  maximize  the  utility  of  GPU  re-
sources  (Zhang  C.  et  al.,  2019).  LORAKI  offered  a  deep-learning 
approach  to  MRI  reconstruction  based  on  convolutional  RNNs  in 
k-space and enhanced sampling flexibility (Kim et al., 2019). The image 
quality of LORAKI reconstruction has shown better quantitative evalu-
ation, and moderate visual improvement. RAKI was further extended for 
simultaneous  multi-slice  MRI  reconstruction,  followed  by  hyper-
parameter study for corresponding network (Nencka et al., 2020). An 
iterative RAKI method based on complex convolutional neural networks 
was  proposed,  where  each  iteration  extracts  the  enhanced  ACS  data 
from  the  previous  step  for  further  iterative  training  (Dawood  et  al., 
2023). A method of scan-specific artifact reduction in k-space (SPARK) 
estimates and corrects k-space errors for CNN by back-propagating from 
the  mean-squared-error  loss  between  ACS  and  the  input  technique’s 
reconstructed  ACS  (Arefeen  et  al.,  2022).  A  residual  RAKI  (rRAKI) 
network combines the advantages of linear convolution and nonlinear 
convolution by using a skip connection (Zhang et al., 2022). RAKI based 
methods  can  obtain  higher 
reconstruction  quality  by  using 
self-supervised CNN training with fully sampled k-space center. How-
ever,  the  reconstruction  quality  of  RAKI  may  be  further  improved, 
especially at high accelerations.

It is well known that sparsity has played a key role in many fast MRI 
algorithms  (Cand`es  et  al.,  2006;  Haldar,  2015b;  Jin  et  al.,  2013;  Jin 
et al., 2016; Lustig et al., 2007; Xiang 2005). When MRI data are natu-
rally  sparse, highly efficient  reconstruction can be achieved. This  has 
been demonstrated by simple spectroscopic imaging, better known as 
the Dixon method (Dixon, 1984), where the chemical shift spectrum is 
very  sparse,  with  only  two  dominating  peaks  of  water  and  fat.  MR 
angiography  also  has  very  sparse  signals,  therefore  can  be  directly 
accelerated  (Chang  and  Xiang,  2007).  If  in  general  sparsity  is  not 
naturally available, data can be sparsified by transformations to improve 
reconstruction  efficiency.  Actually,  as  early  as  the  1980s, a  high-pass 
filter  was  used  to  transform  the  non-linear  solution  for  a  localized 
polynomial  approximation  method  to  a  linear  predictive  problem  for 
MRI  reconstruction,  which  relies  on  a  concept  of  transform-domain 
sparsity  constraints  (Liang  et  al.,  1989).  The  high-pass  filtering  idea 
has ebbed and flowed in its various incarnations since these early con-
tributions. Similar idea appears in recent GRAPPA-like methods (Haldar, 
2015b; Haldar and Setsompop, 2020; Jin et al., 2016; Ongie and Jacob, 
2016).  High-pass  (HP)  filter  was  used  in  structured  low-rank  matrix 
modeling (Haldar, 2015b; Ongie and Jacob, 2016; Jin et al., 2016) to 
make it easy to construct good annihilation functions, since the effective 
support of HP filtered data is generally much smaller than the effective 
support  of  original  data  (Haldar,  2015b).  Sparsifying  transform  can 
reduce  image  support  and  help  focus  on  the  important  features  for 

various  reconstruction  algorithms.  For  example,  difference  transform 
(DT) or discrete wavelet transform are often used to obtain sparsity for 
Compressed  Sensing  (CS)  (Lustig  et  al.,  2007)  or  SPEED  based  re-
constructions (Jin et al., 2013; Jin et al., 2016; Xiang 2005). Huang et al 
used  a k-space  high-pass filter to  reduce  image support  and  achieved 
significantly improved reconstruction quality for GRAPPA (Huang et al., 
2008). SCUNET improved image quality for DL-based reconstruction by 
using a complex sparsifying transform for training data (Jin and Xiang, 
2023). MW-RAKI methods focus on the recovery of different characters 
in RAKI reconstructions by using two HP filters in k-space with different 
values  of  parameters,  resulting  in  more  iterations  of  channel  training 
and much longer training time than that of original RAKI (Tao et al., 
2023).

Since sparsity has not been fully considered in RAKI reconstruction, 
and the RAKI algorithm performs nonlinear interpolations directly in k- 
space,  a  simple  HP  filter  in  k-space  was  used  in  this  study  to  further 
optimize RAKI reconstructions and to improve the training efficiency. 
HP-RAKI method was proposed by using a k-space HP filter to reduce 
image  support  both  for  training  and  for  prediction.  This  HP  filter  is 
equivalent to a sparsifying operator in image space. The unacquired k- 
space data can be predicted from the trained HP-RAKI network using the 
optimized  parameters.  Signals  with  true  contrast  can  be  restored  by 
performing an inverse HP filter on the predicted k-space data. Compared 
with other algorithms, HP-RAKI and its extended residual method (HP- 
rRAKI)  were  found  to  be  generally  more  effective  in  reconstructing 
images, particularly at high acceleration factors. HP-RAKI and HP-rRAKI 
offer higher reconstruction quality for regularly under-sampled k-space 
data without any extra training data. These algorithms are promising for 
fast MRI applications, especially those lacking of fully sampled training 
data.

2. Methods

2.1. Linear Predictability Theory

It was reported that if the support of the image is smaller than the 
Field-of-View (FOV), for example, most body parts are more ellipsoidal 
than rectangular and the corners of an MR image are often empty for 
rectangular FOV, then the unacquired k-space data can be interpolated 
by  weighting  the  neighboring  acquired  k-space  data  based  on  linear 
predictability theory (Haldar and Setsompop, 2020).

To avoid complicated notation, description in this part will focus on a 
simplified  one-dimensional  version  of  MRI,  generalizations  to  higher- 
dimensional  scenarios  are  straightforward.  Let  variable  B  define  an 
upper  bound  of  the  image  size,  then  the  interval  [(cid:0) B /2, B /2]⊂R  is 
known as the FOV. Define I(x) as a continuous one-dimensional com-
plex-valued image, x ∈ R. The image is assumed to have finite spatial 
support, such that I(x) = 0 for x ∕∈ [ (cid:0) B /2, B /2](Haldar, 2014; Haldar 
and Setsompop, 2020).

Classical MRI acquisition is usually modeled as sampling the Fourier 

transform at the Nyquist rate, i.e., 

̃
S[n] =

∫B/2

(cid:0) B/2

I(x)e

(cid:0) i2πnx/Bdx,

(1) 

̃
S[n] is  the  nth  sample  in  the  Fourier  domain  (n ∈ Z),  and  con-
where 
ventional sampling theory tells us that we can recover the original image 
from infinite samples by, 

I(x) = 1
B

∑∞

n=(cid:0) ∞

̃
S[n]ei2πnx/B,

for x ∈ [ (cid:0) B /2, B /2].

(2) 

The interpolation form assumes that, for all integers n, the sample 
̃
S[n] can  be  approximated  as  a  linear  combination  of  neighboring 

2 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

samples, e.g., 

̃
S[n] ≈

∑P

k=(cid:0) L

̃
S[n (cid:0) k] ,

ak

for ∀n ∈ Z.

(

HP = 1(cid:0)
(

(3) 

1+exp

√

(( ̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅
2
2 +ky
kx
(( ̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅
2
2 +ky
kx

√

+c

)/

))(cid:0) 1

(cid:0) c
)/

w
))(cid:0) 1

+

1+exp

w

,

(6) 

̃
S[n] is approximately linearly predictable in the sense of 
If the signal 
n=(cid:0) Lwith  ̃H[0] = (cid:0) 1, such 

Eq. [3], there must exist coefficients {̃H[n]} P
that, 

0 ≈

∑P

k=(cid:0) L

H[k]̃
̃

S[n (cid:0) k], for ∀n ∈ Z.

(4) 

The relationship in Eq. [4] is shift-invariant and implies that P + L +
1 consecutive samples are approximately linearly dependent, such that 
any one missing sample can be predicted as the weighted sum of the 
others (Haldar, 2014; Haldar and Setsompop, 2020). Eq. [4] was also 
called  as  an  approximate  annihilating  filter  relationship  because  the 
̃
S[n] is being approximately annihilated by convolution with the 
̃
H[n] (Haldar, 2014; Haldar and Setsompop, 2020; Jin K. 

signal 
“filter” function 
H. 2016, Ongie and Jacob, 2016.).

Approximate linear prediction relationships will exist if I(x) is image 
support-limited, and there are linearly independent bandlimited func-
h(x) =
h(x)
̃
H[n]ei2πnx/B  (Haldar, 2014; Haldar and Setsompop, 2020; Jin K. 

I(x)h(x) ≈ 0,  where 

satisfy 

that 

can 

tions 
∑
P
1
n=(cid:0) L
B
H. et al., 2016).

In  this  study, high-pass filter  in  k-space  is  proposed  to reduce  the 
image  support  for  the  data.  The  potential  benefit  of  this  data  trans-
formation  is  that  high-pass  filtered  data  often  has  its  energy  concen-
trated  near  image  edges.  This  can  make  it  easier  to  construct  good 
annihilation functions h(x), since the effective image support of high- 
pass filtered image is generally much smaller than the original image 
support of I(x).

2.2. High-Pass Filter in k-Space

Many  of  the  published  approaches  define  HP  filters  based  on  dif-
ferential operators in image domain (Cand`es et al., 2006; Haldar, 2015b, 
Liang et al.,1989; Lustig et al., 2007; Ongie and Jacob, 2016; Jin et a., 
2016;  Jin  and  Xiang,  2023;  Zhang  et  al.,  2019),  for  example,  spatial 
derivative operator ∂/∂x acts as a high-pass filter (Haldar, 2015b).

Several other studies define HP filters in k-space (Huang et al., 2008; 
Tao et al., 2023). For example, the HP filter of MW-RAKI is defined as, 

(cid:0)
HPMW = M

2 + ky
1 + kx
D0

)P

2

,

(5) 

where  M and  D0  denote the amplitude parameter  and the  cut-off fre-
quency, P determines the smoothness of the filter boundary (Tao et al., 
2023). There are three parameters used in the HP filters for MW-RAKI, 
all  based  on  experience  value,  without  any  optimization  in  the  re-
ported  study.  In  addition,  MW-RAKI  uses  multiple  HP  filters  with 
different values of parameters, resulting in more iterations of channel 
training and much longer training time.

Considering  the RAKI  algorithm performs nonlinear  interpolations 
directly in k-space, HP-filter in k-space was chosen in this study. In order 
to simplify the architecture of HP filtered RAKI and to further improve 
the training efficiency, a simple HP filter in k-space with only two pa-
rameters was used. By using this simple k-space HP filter, the energy of 
low-frequency components is significantly reduced and the filtered ACS 
lines can still provide enough information for training.

In  this  study,  an  HP  filter  was  constructed  following  a  previous 
)

(cid:0)

publication on HP enhanced GRAPPA (Huang et al., 2008). Let 
be the coordinates in 2D k-space, then an HP filter in k-space can be 
formatted as, 

kx, ky

(7) 
)

is 

(cid:0)

kx, ky

where  c  sets  the  cutoff  spatial  frequency,  and  w  determines  the 
smoothness of boundary. Image support can be reduced by multiplying 
an HP filter in k-space as shown in Fig. 1. The HP filtered k-space data 
SHP
(cid:0)

can be formulated as, 
)

kx, ky
)

)

(cid:0)

SHP

kx, ky

kx, ky

⋅HP,

(cid:0)
= S

where the symbol “⋅”  means point-by-point multiplication, S
the two-dimensional k-space data.

As shown in Fig. 1D, there was a “dark hole” at k-space center after 
applying the HP filter, resulting in an image support reduced magnitude 
image  after  performing  an  Inverse  Discrete  Fourier  Transform  (IDFT) 
reconstruction. It can be seen from Fig. 1E that the IDFT reconstructed 
images for the high-pass filtered data has its energy concentrated near 
sparse image edges. Reduced image support helps construct an annihi-
lation function ̃H[k] in Eq. [4].

2.3. Regular Under-Sampling and Training data

)
kx, ky, z
)
kx, ky, z

data Su
(cid:0)

SHPu

(cid:0)

For multi-coil data acquisition, the under-sampled k-space multi-coil 
can be HP filtered in k-space as described by Eq. [8], 

(cid:0)

kx, ky, z

)

⋅HP,

(8) 

= Su

where z is the index of coil number.

Similar to GRAPPA (Griswold et al., 2002), a regular under-sampling 
pattern was applied in k-space to yield under-sampled data Su(kx, ky, z) 
from full data S(kx, ky, z), where kx  and ky  are coordinates along fre-
quency encoding (FE) and phase encoding (PE) directions respectively. 
Fig. 2A illustrates an example of such a regular under-sampling pattern 
in k-space, where solid and dotted lines indicate acquired and skipped 
PE data, respectively. This pattern can be described by PE skip size N =
5, and fully sampled data lines near k-space center, known as the ACS 
lines (marked in orange). In the example case of N = 5, there are N-1 = 4 
labels marked in blue (Fig. 2C-F) used for training error calculations. 
These labels were produced by shifting the selected ACS lines. The PE 
lines of each label (for example, oy  in Fig. 2C) were calculated based on 
the dimension of ACS lines, the size of convolutional kernels, and the 
skip size N (Akçakaya et al., 2019). An acceleration factor R was defined 
as the total number of PE lines divided by the acquired number of PE 
lines.

In this study, ACS lines will be HP filtered before training. The HP 

filtered ACS data from multi-coil acquisition can be formatted as, 

(cid:0)

)
kx, ky, z

= Sacs

(cid:0)

)
kx, ky, z

⋅HP.

SHPacs

(9) 

2.4. HP-RAKI architecture

HP-RAKI  use  the  same  feedforward  neural  network  as  RAKI 
(Akçakaya  et  al.,  2019).  The  main  difference  between  RAKI  and 
HP-RAKI  is  the  training  data.  The  training  data  of  RAKI  are  original 
under-sampled k-space data, while the training data of HP-RAKI are the 
same data after high-pass filtering. As shown in Fig. 3A, the structure of 
HP-RAKI includes three layers: the first layer consists of a convolution 
layer,  followed  by  an  ReLU layer.  The kernel  of  the  first  convolution 
layer is ω1, sized to ωkx × ωky × 2Nz × n1 = 5 × 2 × 2Nz × n1, where 
ωkx  and  ωky  denote  the  sizes  of  convolution  window  along  kx  and  ky 
dimensions  respectively,  Nz  is  the  number  of  multi-coils,  n1  is  the 
number of convolution channels. The second layer includes a convolu-
tion layer  with kernel ω2, sized  to 1 × 1 × n1 × n2, followed by an 

3 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

Fig. 1. Illustration of high-pass filter and corresponding inverse filter in k-space. Low spatial frequency signals near k-space center were suppressed after applying a 
high-pass filter, resulting in sparsity in reconstructed magnitude images with reduced image support. The original image contrast can be restored after performing 
corresponding inverse high-pass filtering.

Fig. 2. An example of a regular under-sampling pattern in k-space, where solid and dotted lines indicate acquired and skipped data, respectively. This regular pattern 
can be described by a PE skip size N = 5, and fully-sampled ACS lines near k-space center (A). The fully sampled central lines (ACS) marked in orange are used for 
training (B). (C-F) are training labels (marked in blue) selected from ACS lines by using shift operations.

ReLU layer as well, where n2 is the number of convolution channels. The 
third layer includes only a convolution layer with kernel ω3, sized to 3 
× 2 × n2 × Nout, where Nout = N (cid:0) 1.

(cid:0)

)
kx, ky, z

There are Nz complex-valued channels (Nz coils) for the HP filtered 
ACS data SHPacs
. Traditional RAKI and many of its extensions 
treat  the  real  and  imaginary  components  as  two  separate  real-valued 
channels.  Similar  to  RAKI,  in  this  study,  real  and  imaginary  parts  of 
each channel are concatenated together to produce 2 × Nz  real-valued 
channels  (Nz  channels  from  real  parts,  followed  by  Nz  channels  from 
imaginary parts). Thus, the dimension of SHPacs
was doubled in 
coil direction with z = 1, …, 2 × Nz. The network was trained channel by 
channel for each coil, resulting in 2 × Nz channels of training for Nz coils.
There are N-1 sets of k-space lines unacquired due to a PE skip size N. 
For uth (u= 1,…, 2 × Nz) channel training, as shown in Figs. 2C-F, with 

kx, ky, z

)

(cid:0)

(cid:0)

)
kx, ky, z = u, N (cid:0) 1

(cid:0)

(cid:0)

)
kx, ky, z = u

)
kx, ky, z = u, N (cid:0) 1

skip size N = 5, N-1 = 4 sets of output data SPacs
can 
be  obtained  from  HP-RAKI  architecture  after  inputting  HP  filtered 
SHPacs
data.  Correspondingly,  totally  N-1  sets  of  labelled 
)
kx, ky, z = u
data SLacs
data using a varied index range as Figs. 2C-F shown. Thus, mean square 
the  output  data 
error 
(cid:0)
)
kx, ky, z = u, N (cid:0) 1
SPacs
. 
Adaptive  moment  estimation  (ADAM)  method  (Diederik  and  Jimmy, 
2015)  is  used  to  optimize  the  parameters  θz  of  HP-RAKI  for  each 
channel.

calculated  between 
and the labelled data SLacs

can be selected from SHPacs

kx, ky, z = u, N (cid:0) 1

can  be 
)

loss 

(cid:0)

(cid:0)

Based on the optimized parameters of HP-RAKI for each channel, the 
N-1 sets of missing k-space data can be predicted for each channel, as Eq. 
[10] shown for uth channel prediction,  

4 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

Fig. 3. An illustration of the proposed HP-RAKI (A) and HP-rRAKI (B) architecture. The RAKI net is illustrated in the dotted rectangular area in (A). The input 
training signal of HP-RAKI is processed by using a high-pass filter in k-space, resulting in a suppressed low frequency signal as a dark hole near the k-space center 
shown. The difference between HP-RAKI and HP-rRAKI is the skipped connection between input and output as shown in (B). There is only one convolution layer 
placed in the skip connection for residual calculation.

SHPpredict

(cid:0)

)
kx, ky, z = u

=

⎧
⎨

⎩

(cid:0)

(cid:0)

)
, θz
kx, ky, z = u

HP (cid:0) RAKI
SHPu
SHPacs

SHPu
(cid:0)
)
kx, ky, z = u
(cid:0)
)
kx, ky, z = u

)

, (N (cid:0) 1)sets of missing lines
, acquired lines
, k (cid:0)
space center

.

(10) 

Complex-valued data SHP
real-valued channels data SHPpredict
which can be formulated as, 

(cid:0)

)
kx, ky, z
(cid:0)

were formed by ordering 2 × Nz 
to Nz complex-valued data, 

)
kx, ky, z

(cid:0)

)
kx, ky, z

SHP

= SHPpredict

(cid:0)

)

kx, ky, a

+ j⋅SHPpredict

(cid:0)

)
.

kx, ky, b

(11) 

5 

where b = a + Nz, a ∈ previous Nz channels, b ∈ latter Nz channels.

2.5. Inverse High-Pass Filtering & Data Consistency Replacement

Since the predicted k-space data are still HP filtered data, an inverse 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

high-pass (iHP) filtering should be performed as shown in Fig. 1F, which 
can be formulated as,  

for each method. ADAM (Diederik and Jimmy, 2015) was selected as an 
optimizer  with  a  learning  rate  of  0.0003.  The  filter  parameters  of 

[

(

=

1 (cid:0)

iHP = 1
HP

√

(( ̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅
2
2 + ky
kx

1 + exp

)/

))(cid:0) 1

(

(cid:0) c

w

+

1 + exp

√

(( ̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅
2
2 + ky
kx

)/

))(cid:0) 1](cid:0) 1

+ c

w

.

(12) 

The inverse filtered k-space data SiHP
(cid:0)

)

(cid:0)

SiHP

kx, ky, z

= SHP

kx, ky, z

)
⋅iHP.

(cid:0)

)
kx,ky,z

can be formulated as, 

(13) 

The center values of the HP filter were very close to “zero” as shown 
in Fig. 1D and may result in numerical instabilities in the inverse HP 
filtering process. Fortunately, this problem of divided by “zero” in Eq. 
[12-13] can be easily avoided by replacing the k-space center with fully 
sampled ACS lines.

Moreover,  data  consistency  replacement  was  performed  to  further 

improve the reconstruction quality, as shown in Eq. [14], 
)
, wherever data are acquired,
)
,

)
kx, ky, z

kx, ky, z

⎧
⎨

Sacq

Srec

⎩

=

(cid:0)

(cid:0)

(cid:0)

SiHP

kx, ky, z

(14) 

otherwise.
)
kx, ky, z

Finally, an IDFT was applied on Srec

(cid:0)

to recover final multi- 

coil images with normal contrast channel by channel for Nz channels, 

Irec(x, y, z) = 1
NxNy

∑Nx(cid:0) 1

∑Ny(cid:0) 1

kx=0

ky=0

(cid:0)

Srec

kx, ky, z

)
exp

[
j2π

(

xkx
Nx

+ yky
Ny

)]
.

(15) 

2.6. Experiments

Multi-coil  k-space  raw  datasets  were  downloaded  from  the  NYU 
fastMRI  Initiative  database  (https://fastmri.med.nyu.edu/)  including 
axial T1-weighted, T2-weighted, and FLAIR brain images from human 
subjects (Knoll et al., 2020; Zbontar et al., 2019) provided after approval 
of the Institutional Review Board. The Field-of-View (FOV) was 220 mm 
× 440 mm. The raw data were acquired from various scanner models 
from SIEMENS, including Skyra 3T, Prisma_fit 3T, Biograph_mMR 3T, 
Aera 1.5T. These data were all anonymized and their use complies with 
our institutional ethical guidelines. A total of 60 sets of multi-coil images 
from 60 different subjects were used in the experiment. An IDFT oper-
ation was performed on 60 multi-coil k-space datasets (320 × 640 × 16) 
to reconstruct MR images, which were resized to 320 × 320 × 16 after 
excluding air region. The dimensions of the reconstructed images were 
320 × 320 per slice, all acquired with 16 coils. The DFT transform were 
applied on 320 × 320 images to obtain fully sampled k-space data, and 
various  skip  sizes  N  were  used  to  obtain  under-sampled  k-space  data 
with ACS lines fully sampled near k-space center.

In  order  to  comparatively  evaluate  the  performance  of  HP-RAKI, 
reconstructions  of  RAKI  (Akçakaya  et  al.,  2019)  and  MW-RAKI  (Tao 
et  al.,  2023)  were  also  performed.  Since  the  RAKI  and  the  MW-RAKI 
algorithms  can  be  extended  to  residual  structures  (named  as  rRAKI, 
and MW-rRAKI, respectively) to further improve the reconstructions, the 
proposed  HP-RAKI  algorithm  was  extended  to  a  residual  structure 
(HP-rRAKI) as well by adding a skip connection between the input and 
the output channels as shown in Fig. 3B. The reconstruction results from 
rRAKI,  MW-rRAKI,  and  HP-rRAKI  were  also  compared.  The  network 
architecture,  the  number  of  layers,  the  number  of  channels,  and  the 
training parameters were all the same for RAKI, rRAKI, MW-RAKI, and 
MW-rRAKI, HP-RAKI, and HP-rRAKI. The size of the convolution kernels 
in RAKI, rRAKI, MW-RAKI, MW-rRAKI, HP-RAKI, and HP-rRAKI were 5 
× 2, 1 × 1, and 3 × 2 sequentially. A total of 1000 epochs were trained 

6 

MW-RAKI  and  MW-rRAKI  was  set  to  previously  reported  values  (Tao 
et al., 2023). The input real and imaginary parts were organized as 2 ×
Nz (Nz = 16 for 16 coils) separated channels, followed by 32, 8, and N-1 
channels  respectively  for  each  training  layer.  The  output  of  RAKI, 
MW-RAKI  and  HP-RAKI  were  2  × Nz  separate  real  and  imaginary 
channels,  to  represent  complex  images.  GRAPPA,  HP-GRAPPA  were 
performed for comparison as well, using a kernel size of 5 × 5.

RAKI, rRAKI, MW-RAKI, MW-rRAKI, HP-RAKI, and HP-rRAKI were 
implemented  using  Python  and  Pytorch  programming  language  on  a 
personal  computer  with  16  GB  RAM,  2.21  GHz  CPU,  and  NVIDIA 
RTX2070 GPU. GRAPPA and HP-GRAPPA were implemented by using 
MATLAB language, on the same personal computer. All algorithms were 
implemented  with  the  same  acceleration  factors  for  comparison.  The 
reconstructed  k-space  data  were  finally  replaced  by  the  actually  ac-
quired k-space data wherever available for all reconstruction methods 
for  fair  comparison,  including  GRAPPA,  HP-GRAPPA,  RAKI,  rRAKI, 
MW-RAKI,  MW-rRAKI,  HP-RAKI,  and  HP-rRAKI  algorithms.  Since  re-
ported GRAPPA, HP-GRAPPA, RAKI, rRAKI, MW-RAKI, and MW-rRAKI 
all used rSOS to combine the multi-coil images into a single one, in this 
study, rSOS was also used to combine the reconstructed 16-coil images 
into a single image for all algorithms, including GRAPPA, HP-GRAPPA, 
RAKI, rRAKI, MW-RAKI, MW-rRAKI, HP-RAKI, and HP-rRAKI. Similarly, 
the same coil combination was performed on reference images directly 
reconstructed from full k-space data. The image quality was quantita-
tively  evaluated  using  structural  similarity  index  (SSIM)  and  peak  to 
noise ratio (PSNR), all calculated in the brain region (Zhou et al., 2004).
Generally,  smaller  c  or  larger  w  in  the  HP  filter  will  result  in  less 
image support reduction, and larger c or smaller w will have more image 
support  reduction.  However,  larger  c  or  smaller  w  will  also  suppress 
useful information in the ACS. Huang et al provided predefined values of 
c and w for varied number of channels and varied number of ACS lines by 
calculating the relative error (Huang et al., 2008). It was reported that 
the  reconstruction  result  cannot  be  improved  significantly  by  using 
parameters other than the predefined values (Huang et al., 2008). In this 
study, the c and w values were initially selected from the suggested range 
in  the  paper  by  Huang  et  al  (Huang  et  al.,  2008)  and  were  further 
optimized by calculating the mean SSIM and PSNR values of multi-coil 
data.  ACS  lines  were  selected  as  20,  30,  and  40  for  the  k-space  data 
with 320 × 320 matrix size, and 16 multi-coils. The skip size was chosen 
to be N = 3, 4, 5, 6, 7, respectively. The two parameters of the HP filter 
varied as w = 2, 4, 6, 8, and c = 6, 10, 14, 18, 22, respectively.

3. Results

Figs. 4, 6, 7 present the resulting images in which the PE direction 
was  from  left  to  right.  The  maximum  magnitude  error  values  were 
normalized  to  “1”,  with  color  bar  showing  the  percentage  errors 
accordingly.

Fig.  4 shows  reconstruction  results  of  a  representative  slice  from 
multi-coil FLAIR brain testing data at 3T using under-sampling with ACS 
= 40, N = 4 and ACS = 40, N = 6, resulting in an acceleration factor R =
2.91 (Fig. 4A) and R = 3.64 (Fig. 4B), respectively.

As  shown  in  Fig.  4,  there  were  obvious  noise-like  artifacts  in  the 
magnitude  image  from  GRAPPA  at  N  = 4  (Fig.  4A).  These  noise-like 
artifacts  were  suppressed  in  HP-GRAPPA  N  = 4  (Fig.  4A).  From 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

Fig. 4. Reconstruction results of a representative slice from FLAIR brain testing data at 3T with (N = 4, ACS = 40, R = 2.91) (A) and (N = 6, ACS = 40, R = 3.64) (B) 
under-sampling scheme, respectively. The “gold-standard” magnitude image was reconstructed from fully sampled k-space data. GRAPPA, HP-GRAPPA, RAKI, and 
HP-RAKI reconstructions were respectively performed on the under-sampled data. The error maps at (A) suggest that the reconstruction quality of HP-GRAPPA, RAKI, 
and  HP-RAKI  are  all  much  higher  than  that  of  GRAPPA.  The  error  maps  at  (B)  suggest  that  HP-RAKI  produced  the  least  artifacts  as  indicated  by  arrows.  The 
quantitative SSIM and PSNR values indicated that HP-RAKI had the highest performance at N = 4 and N = 6.

subjective  evaluation,  all  methods  produce  reasonable  high  quality 
reconstruction images at N = 4. The error maps in (Fig. 4A) suggest that 
the reconstruction quality of HP-GRAPPA, RAKI, and HP-RAKI are all 
higher than that of GRAPPA.

There are obvious artifacts in all reconstructions at N = 6 in (Fig. 4B). 
The  GRAPPA  produced  noise-like  artifacts.  There  were  obviously 
remaining strip-like artifacts in the images from HP-GRAPPA, RAKI, and 
HP-RAKI, respectively. HP-RAKI produced the least artifacts as indicated 
by the arrows.

The  values  of (SSIM,  PSNR)  for  GRAPPA,  HP-GRAPPA, RAKI,  and 
HP-RAKI at N = 4 were (0.906, 33.99), (0.949, 37.02), (0.949, 38.04), 
and  (0.955,  38.44),  respectively.  The  values  of  (SSIM,  PSNR)  for 
GRAPPA,  HP-GRAPPA,  RAKI,  and  HP-RAKI  at  N  = 6  were  (0.794, 
28.58), (0.917, 30.83), (0.886, 30.45), and (0.922, 33.57), respectively. 
Both SSIM and PSNR values of HP-RAKI were significantly higher than 
that  of  the  other  comparators,  suggesting  higher  quality  of  HP-RAKI 
reconstruction at a skip size of N = 4 and N = 6.

Fig. 5 shows the mean (including 60 sets of multi-coil images from 60 

different  subjects,  acquired  from  various  SIEMENS  scanner  models) 
SSIM and PSNR values of HP-RAKI for varied ACS = 20 (Fig. 5A), 30 
(Fig. 5B), and 40 (Fig. 5C), respectively. Skip size N was varied as 3, 4, 5, 
6 and 7, respectively for selected ACS values, corresponding to accel-
eration factors R of 2.67, 3.37, 4.00, 4.57, and 5.08 for ACS = 20, 2.52, 
3.11, 3.64, 4.05, and 4.44 for ACS = 30, 2.39, 2.91, 3.33, 3.64, and 4.00 
for ACS = 40. The two parameters of the HP filter varied as w = 2, 4, 6, 8, 
and c = 6, 10, 14, 18, 22, respectively. It can be seen from the quanti-
tative values in Fig. 5 that the distribution of SSIM and PSNR values of 
HP-RAKI for ACS = 20 were flat for most of the combinations of the two 
parameters,  especially  for  c  <14.  The  distribution  of  SSIM  and  PSNR 
values of HP-RAKI for ACS = 30 were also pretty flat, except for N = 7. 
The co-optimal of SSIM and PSNR values can be obtained at w = 2, and c 
in  the  range  of  6  -  10  for  all  skip  size  N  if  ACS  = 30.  The  optimal 
parameter selection for ACS = 40 is similar to that of ACS = 30. The 
optimal  reconstruction  quality  of  HP-RAKI  with  varied  ACS  was  sug-
gested with w = 2, c in the range of 6 - 10 according to different ACS 
values, based on the co-optimal observation and analysis. In this study, 

7 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

Fig. 5. Mean (including 60 sets of multi-coil images from 60 different subjects, acquired from various SIEMENS scanner models) SSIM and PSNR values of HP-RAKI 
for varied ACS = 20 (A), 30 (B), and 40 (C), respectively. Skip size N was varied as 3, 4, 5, 6 and 7, respectively for selected ACS values. The two parameters of the HP 
filter varied as w = 2, 4, 6, 8, and c = 6, 10, 14, 18, 22, respectively. From the quantitative values, the optimal reconstruction quality of HP-RAKI with varied ACS was 
achieved with w = 2, c in the range of (6, 10) according to different ACS values, based on the co-optimal observation and analysis.

8 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

Fig. 6. Reconstruction results of a T1-weighted data at 3 T with ACS = 40, N = 3 (A) and N = 5 (B) under-sampling schemes, respectively. The “gold-standard” 
magnitude  image  was  reconstructed  with  fully  sampled  k-space  data.  GRAPPA,  HP-GRAPPA,  RAKI,  rRAKI,  MW-RAKI,  MW-rRAKI,  HP-RAKI,  and  HP-rRAKI  re-
constructions were performed on the under-sampled  data, respectively. From subjective evaluation, all methods obtain high quality images at N = 3 (A). From 
quantitative evaluation, MW-RAKI, MW-rRAKI, HP-RAKI, and HP-rRAKI methods obtained higher SSIM and PSNR values than those of GRAPPA, HP-GRAPPA, RAKI, 
and rRAKI at N = 3 (A). The quantitative SSIM and PSNR values indicated the highest performance of HP-RAKI compared with GRAPPA, HP-GRAPPA, RAKI, rRAKI, 
and MW-RAKI algorithms at N = 5 (B). Similar performance can be found in the corresponding residual extensions group in the right column at N = 5 (B).

9 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

Fig. 7. Reconstruction results of a T2-weighted scan at 1.5 T with ACS = 40, N = 4 (A) and N = 7 (B) under-sampling schemes, respectively. The “gold-standard” 
magnitude  image  was  reconstructed  with  fully  sampled  k-space  data.  GRAPPA,  HP-GRAPPA,  RAKI,  rRAKI,  MW-RAKI,  MW-rRAKI,  HP-RAKI,  and  HP-rRAKI  re-
constructions  were  performed  on  the  under-sampled  data,  respectively.  The  quantitative  SSIM  and  PSNR  values  indicated  the  highest  performance  of  HP-RAKI 
compared with GRAPPA, HP-GRAPPA, RAKI, rRAKI, and MW-RAKI algorithms at N = 4 (A). Similar performance can be found in the corresponding residual ex-
tensions group in the right column at N = 4 (A). There were obvious strip artifacts in all reconstructions at N = 7 (B).

10 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

Table 1 
Mean SSIM and PSNR values and corresponding SD values for testing data with ACS = 40 but various skip sizes N = 3, 4, 5, 6, 7, corresponding to acceleration factors R 
of 2.39, 2.91, 3.33, 3.64, and 4.00, respectively.

N

R

Criteria

GRAPPA mean 
(SD)

HP-GRAPPA mean 
(SD)

RAKI mean 
(SD)

MW-RAKI mean 
(SD)

HP-RAKI mean 
(SD)

3

4

5

6

7

2.39

SSIM

0.957(1.88e-2)

0.965(1.76e-2)

PSNR
SSIM

PSNR
SSIM

PSNR
SSIM

PSNR
SSIM

2.91

3.33

3.64

4.00

38.77(3.19)
0.894(3.78e-2)

39.47(3.2)
0.945(2.38e-2)

33.93(2.98)
0.819(6.10e-2)

37.02(3.21)
0.928(2.85e-2)

29.84(3.10)
0.816(6.07e-2)

35.19(2.95)
0.919(3.08e-2)

29.45(2.97)
0.816(5.99e-2)

33.48(2.98)
0.909(3.24e-2)

PSNR

29.11(2.53)

31.84(2.68)

0.965(1.78e- 
2)
39.46(3.09)
0.943(2.41e- 
2)
36.92(3.10)
0.921(3.04e- 
2)
34.69(3.19)
0.900(3.71e- 
2)
32.81(3.35)
0.875(4.42e- 
2)
30.90(3.45)

0.968(1.73e-2)

0.966(1.86e-2)

39.54(3.32)
0.952(2.22e-2)

39.56(3.31)
0.950(2.31e-2)

37.15(3.37)
0.938(2.67e-2)

37.41(3.17)
0.937(2.77e-2)

35.29(3.46)
0.928(3.00e-2)

35.49(3.31)
0.929(2.99e-2)

33.97(3.64)
0.914(3.39e-2)

34.20(3.52)
0.918(3.23e-2)

32.29(3.61)

32.63(3.40)

Corresponding Residual Structure

rRAKI mean 
(SD)

MW-rRAKI mean 
(SD)

HP-rRAKI mean 
(SD)

0.965(1.80e- 
2)
39.64(3.16)
0.944(2.39e- 
2)
37.06(3.04)
0.922(3.01e- 
2)
34.87(3.17)
0.901(3.67e- 
2)
33.13(3.37)
0.877(4.37e- 
2)
31.29(3.30)

0.967(1.77e-2)

0.965(1.91e-2)

39.58(3.35)
0.950(2.25e-2)

39.49(3.23)
0.950(2.34e-2)

37.29(3.26)
0.935(2.73e-2)

37.38(3.11)
0.936(2.80e-2)

35.44(3.38)
0.925(3.08e-2)

35.52(3.38)
0.929(3.01e-2)

34.04(3.60)
0.911(3.45e-2)

34.51(3.40)
0.918(3.26e-2)

32.46(3.61)

33.08(3.40)

w = 2, c = 10 was selected for HP-RAKI and HP-rRAKI reconstructions, 
considering Fig. 4, Fig. 6-7, and Table 1.

Fig.  6 shows  reconstruction  results  of  a  representative  slice  from 
multi-coil T1-weighted brain data at 3T using under-sampling with ACS 
= 40, N = 3 and ACS = 40, N = 5, resulting in an acceleration factor R =
2.39 (Fig. 6A) and R = 3.33 (Fig. 6B), respectively.

As shown in Fig. 6A, the results from GRAPPA, HP-GRAPPA, RAKI, 
rRAKI, MW-RAKI, MW-rRAKI, HP-RAKI, and HP-rRAKI were all visually 
reasonable at N = 3. From the enlarged areas of magnitude images and 
corresponding error maps, the difference between comparators is very 
little as indicated by the white errors. The SSIM and PSNR values of all 
methods  were reasonably  high,  namely, GRAPPA  (0.916, 34.35),  HP- 

Fig. 8. The magnitude value of a reconstructed line from all comparative algorithms in Fig. 4, 6-7 (ACS = 40), (A) the line was reconstructed from the FLAIR brain 
testing data at 3T, with N = 4 and N = 6 under-sampling scheme, (B) the line was reconstructed from the T1-weighted data at 3T, with N = 4 and and N = 7 under- 
sampling scheme, (C) the line was reconstructed from the T2-weighted data at 1.5 T, with N = 4 and N = 7 under-sampling scheme.

11 

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
Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

GRAPPA  (0.923,  34.85),  RAKI  (0.926,  34.89),  rRAKI  (0.925,  35.11), 
MW-RAKI (0.930, 35.45), MW-rRAKI (0.923, 35.46), HP-RAKI (0.924, 
35.47), and HP-rRAKI (0.925, 35.44), respectively.

As shown in Fig. 6B, there were obvious noise-like artifacts in the 
magnitude image from GRAPPA at N = 5. These noise-like artifacts were 
suppressed  well  in  other  comparators,  including  HP-GRAPPA,  RAKI, 
rRAKI,  MW-RAKI,  MW-rRAKI,  HP-RAKI,  and  HP-rRAKI.  The  enlarged 
error maps in Fig. 6B suggest that the reconstruction quality of HP-RAKI 
and HP-rRAKI is all higher than that of other competitors. The quanti-
tative SSIM and PSNR values indicated the highest performance of HP- 
RAKI  (0.898,  33.10)  compared  with  GRAPPA  (0.758,  27.26),  HP- 
GRAPPA  (0.886,  32.03),  RAKI  (0.882,  31.77),  and  MW-RAKI  (0.902, 
32.16) algorithms at N = 5 (Fig. 6B). Similar performance can be found 
for HP-rRAKI in the corresponding residual extensions group in the right 
column  at  N  = 5,  including  rRAKI  (0.880,  31.92),  and  MW-rRAKI 

(0.895, 32.74), and HP-rRAKI (0.900, 33.23), respectively.

Fig. 7 shows partial reconstruction results of a representative slice 
from  the  multi-coil  T2-weighted  data  at  1.5T  using  regular  under- 
sampling with ACS = 40, N = 4 and ACS = 40, N = 7, resulting in the 
acceleration  factors  R  = 2.91  (Fig.  7A)  and  R  = 4.00  (Fig.  7B), 
respectively.

As shown in Fig. 7A, the results from GRAPPA, HP-GRAPPA, RAKI, 
rRAKI, MW-RAKI, MW-rRAKI, HP-RAKI, and HP-rRAKI were all visually 
reasonable  in  magnitude  maps  at  N  = 4.  The  enlarged  areas  of  error 
maps showed noise-like artifacts of GRAPPA and HP-GRAPPA, and strip- 
like artifacts of RAKI, rRAKI, MW-RAKI, MW-rRAKI, HP-RAKI, and HP- 
rRAKI. Strip-like artifacts of MW-RAKI and MW-rRAKI are more intense 
at N = 4. The quantitative SSIM and PSNR values indicated the highest 
performance of HP-RAKI (0.951, 35.96) compared with GRAPPA (0.910, 
32.99), HP-GRAPPA (0.941,35.39), RAKI (0.943, 35.20), and MW-RAKI 

Fig. 9. Training loss (RMSE) values for 1000 epochs of RAKI, MW-RAKI, and HP-RAKI algorithms, respectively (ACS = 40), (A) loss plots for the FLAIR brain testing 
data at 3T, with N = 4 and N = 6 under-sampling scheme, (B) loss plots for the T1-weighted data at 3T, with N = 4 and N = 7 under-sampling scheme, (C) loss plots 
for the T2-weighted data at 1.5 T, with N = 4 and N = 7 under-sampling scheme.

12 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

(0.952, 35.45) at N = 4. Similar performance can be found in the cor-
responding residual extensions group in the right column at N = 4, that 
is HP-rRAKI (0.951, 35.87), rRAKI (0.945, 35.50), MW-rRAKI (0.951, 
35.75), respectively.

As shown in Fig. 7B, the SSIM and PSNR values of all algorithms are 
GRAPPA  (0.836,  28.39),  HP-GRAPPA  (0903,  30.91),  RAKI  (0903, 
30.91),  rRAKI  (0903,  30.91),  MW-RAKI  (0.912,  31.12),  MW-rRAKI 
(0.908, 31.13), HP-RAKI (0.908, 31.33), and HP-rRAKI (0.907, 31.45), 
respectively.  There  were  obvious  strip  artifacts  in  all  of  the  re-
constructions  at  N  = 7.  The  aliasing  artifacts  in  the  center  of  the 
magnified  images  were  not  well  suppressed  in  all  the  approaches,  as 
indicated by the white arrows. Although HP-RAKI has somewhat higher 
SSIM and PSNR values compared with other methods, this difference can 
be  hardly  appreciated  visually  due  to  the  strong  remaining  artifacts. 
Similar performance can be found in the corresponding residual exten-
sions group in the right column, including rRAKI, MW-rRAKI, and HP- 
rRAKI, respectively.

Fig.  8 shows the  magnitude  value  plot  of  a  line selected  from the 
reconstructed  images  of  Fig.  4,  6-7 (ACS  = 40),  respectively.  The 
selected line was marked in red. Fig. 8A is from the FLAIR brain testing 
data at 3T, with N = 4 and N = 6 under-sampling scheme, respectively 
(according to the reconstructed images in Fig. 4). Fig. 8B is from the T1- 
weighted data at 3T,  with N = 4 and N = 7 under-sampling scheme, 
respectively (according to the reconstructed images in Fig. 6). Fig. 8C is 
from  the  T2-weighted  data  at  1.5  T,  with  N  = 4  and  N  = 7  under- 
sampling scheme, respectively (according to the reconstructed images 
in  Fig.  7).  As  shown  by  the  dark  arrows  in  Fig.  8,  the  noise  in  the 
background area of all HP-based algorithms is much lower than that of 
the referenced magnitude values reconstructed from fully sampled data. 
This suggests that the noise is not enhanced by using a high pass filter. 
The deviations from the referenced values are very small for all com-
parators  at  a  low  acceleration  factor  using  skip  size  N  = 3.  The  de-
viations from the referenced values for all comparators increased with 
the increase of the acceleration factor. Obvious deviations can be found 
in  GRAPPA  reconstruction  using  a  relatively  low  acceleration  factor 
with  skip  size  N  = 4.  The  deviations  of  HP-RAKI  and  HP-rRAKI  re-
constructions are smaller than those of other comparators, especially at 
high accelerations with N ≧5.

Fig.  9 depicts  the  iterative  tendency  of  the  reconstruction  RMSE 
curve for RAKI, MW-RAKI, and HP-RAKI. There are two HP filters used 
in  sequence  for  the  MW-RAKI  method.  Each  HP  filter  of  MW-RAKI 
differed in HP parameters, resulting in two loss curves in the subplots 
of Fig. 9, named MW-RAKI-Filter1 and MW-RAKI-Filter2, respectively. 
RAKI with HP filters converges faster with the curve drops quickly at 
early iterations. It has already converged after about 250 iterations for 
HP-RAKI  and  MW-RAKI-Filter2,  about  500  iterations  for  MW-RAKI- 
Filter1, while RAKI has a slower convergence rate until about 1000 it-
erations. In this study, total 1000 epochs were used for each learning- 
based  method  considering  the  convergence  condition  for  fair 
comparison.

Table 1 shows the mean SSIM and PSNR values and corresponding 
standard deviation (SD) values for 60 slices of testing brain data from 
GRAPPA, HP-GRAPPA, RAKI, MW-RAKI, HP-RAKI, and corresponding 
residual  algorithms  (rRAKI,  MW-rRAKI,  and  HP-rRAKI),  respectively. 
Various skip size N of (3, 4, 5, 6, and 7) were used with a fixed ACS = 40, 
corresponding to acceleration factors R of 2.39, 2.91, 3.33, 3.64, and 
4.00. In Table 1, bold values indicate the best SSIM and PSNR results 
among all methods being compared. As shown, at N = 3, the mean SSIM 
and  PSNR  values  of  all  algorithms  were  reasonably  high,  suggesting 
good reconstruction quality of all algorithms. The mean SSIM and PSNR 
values of MW-RAKI and HP-RAKI were both higher than those of RAKI at 
N  > 3,  suggesting  that  high-pass  filters  can  help  improve  the  re-
constructions of RAKI. The mean PSNR values of HP-RAKI were higher 
than those of MW-RAKI at N >3. The mean SSIM values of HP-RAKI were 
higher than those of MW-RAKI at N >5, although a bit lower than that of 
MW-RAKI at N = 4 and 5, suggesting higher performance of HP-RAKI 

than  that  of  MW-RAKI.  For  corresponding  residual  algorithms,  the 
mean SSIM and PSNR values of HP-rRAKI were the highest among all 
algorithms, including rRAKI, MW-rRAKI and HP-rRAKI at N >3, except 
the SSIM value of HP-rRAKI was equal to that of MW-rRAKI at N = 4. 
These quantitative results of SSIM PSNR suggested superior performance 
of HP-rRAKI among all algorithms for N > 3.

It took about 120 seconds for training by using RAKI and rRAKI al-
gorithms, and only about 90 seconds by using HP-RAKI and HP-rRAKI 
algorithms.  The  use  of  HP  filter  actually  helps  reducing  the  training 
time. In contrast, under the same convergence condition and setting the 
same epoch number, the training time for MW-RAKI and MW-rRAKI was 
much longer, taking about 14 minutes for each image (matrix size of 320 
× 320, using 1000 epochs) from 16 coils in this study, resulting in 14 
hours for a total of 60 under-sampled slices.

4. Discussion

DL-based reconstructions for fast MRI often need to acquire a large 
set of training data. In this paper, a simple three-layers CNN architecture 
was used for recovering unacquired k-space data. The training data of 
the proposed HP-RAKI method was produced from the fully sampled k- 
space  center  of  the  under-sampled  data,  with  no  extra  training  data 
acquired. The proposed HP-RAKI and HP-rRAKI methods were suitable 
for more general fast MRI applications, especially those short of training 
data.

Sparsification was demonstrated to be a simple but effective addi-
tional  step  that  can  offer  higher  quality  images  for  DL-based  re-
constructions  (Jin  and  Xiang,  2023).  The  majority  of  sparsifying 
transforms were applied on image space, for example, spatial derivative 
operator in structured low-rank matrix modeling (Haldar, 2015b; Liang 
et al.,1989, Ongie and Jacob, 2016; Jin et al., 2016), difference trans-
form or wavelet transform for compressed sensing (Cand`es et al., 2006; 
Lustig et al., 2007) or SPEED reconstructions (Jin et al., 2013; Jin et al., 
2016; Xiang 2005). Considering the RAKI algorithm performs nonlinear 
interpolations directly in k-space, HP filter in k-space was considered in 
this study to reduce the image support and partly sparsify the training 
data  for  improved  nonlinear  fitting  in  k-space  to  recover  unacquired 
data. After using a simple HP filter in k-space with only two parameters, 
the energy of low-frequency components is significantly reduced, and 
the filtered ACS lines can still provide enough information for calibra-
tion  of  convolution  kernels.  Since  the  parameters  of  HP-RAKI  were 
optimized using the HP filtered k-space training data, the predicted data 
was HP filtered as well. Inverse high-pass filtering in k-space should be 
performed  on  the  predicted  data  to  recover  the  suppressed  low  fre-
quency information. Final multi-coil images can be obtained after per-
IDFT 
forming  data 
reconstructions.  In this study, HP filter was also applied in rRAKI ar-
chitecture with a residual connection between in the input and output. 
From  statistical  comparison,  HP-rRAKI  and  HP-RAKI  obtain  similar 
quality at low accelerations, but the residual connection improved the 
image quality at N > 4. The potential reason may be further sparsifi-
cation due to a residual connection.

followed  by 

replacement, 

consistency 

The parameters c and w of the k-space HP filter can adjust the amount 
of  image  support  reduction.  Large  c  and  small  w  will  result  in  more 
reduction, while small c and large w will reserve more calibration in-
formation (Huang et al., 2008). In this study the parameters c and w of 
k-space  HP  filter were  further  optimized  based  on  the  joint  consider-
ations of SSIM and PSNR values. As shown by the quantitative values in 
Fig. 5, the PSNR values for different ACS values were not very sensitive 
to the selection of w. However, the SSIM values for ACS = 30 and ACS =
40 decreased obviously when setting w value larger than 2. After fixing 
parameter w = 2, the quantitative values for ACS = 20 differed slightly if 
c was set to be smaller than 18, and there were flat quantitative areas 
near c = 10 for ACS = 30 and 40. Considering the mean quantitative 
values analysis, parameters c and w can be predefined. The parameter w 
was suggested to be 2, and the parameter c was suggested to be in the 

13 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

range of 6 - 10. The results of HP-RAKI were not very sensitive to the 
selection of w and c in the predefined range.

This study used a high-pass filter in k-space to reduce image support 
and  focused  on  the  more  important  features.  The  HP-RAKI  and  HP- 
rRAKI  algorithms  can  both  obtain  higher  reconstruction  quality  than 
that  of  corresponding  RAKI  and  rRAKI,  respectively.  The  MW-RAKI 
method  used  two  high-pass  filters  in  k-pace  for  RAKI  to  extend  the 
training data by weighting the high-pass filtered data, which can help 
recover signals of different frequency bands. The MW-RAKI and MW- 
rRAKI  algorithms obtained  improved  reconstruction  quality  than that 
of corresponding RAKI and rRAKI algorithms. The input of the proposed 
HP-RAKI algorithm is the HP filtered data (input data were all image 
support  reduced),  however  the  input  of  MW-RAKI  includes  both  the 
multi-weighted HP filtered data (reduced image support) and the orig-
inal under-sampled data (image support was not reduced). As appreci-
ated  in  the  compressed  sensing  community,  the  training  data  of  HP- 
RAKI  was  much  sparser than that  of MW-RAKI.  An  image  with small 
image support means fewer unknowns to solve. The HP filters used in 
HP-RAKI and MW-RAKI were not the same. There are two parameters 
used in the high-pass filter for HP-RAKI, as shown in Eq.[6], they were 
optimized for brain data in this study. There are three parameters used 
in high-pass filters for MW-RAKI as reported (amplitude parameter, cut- 
off frequency parameter, and the parameter used to adjust smoothness) 
(Tao et al., 2023), these parameters have not been optimized in the re-
ported  study.  The  subjective  image  quality  evaluation  and  objective 
quantitative values demonstrated higher performance of the proposed 
HP-RAKI than that of MW-RAKI, as summarized in Figs. 6, 7 and Table 1. 
Moreover, the training time of MW-RAKI is much longer than that of the 
proposed  HP-RAKI  algorithm.  Under  the  same  convergence  condition 
and setting the same epoch number for MW-RAKI and HP-RAKI, it took 
about 14 minutes for MW-RAKI to train each dataset. However, it took 
only about 1.5 minutes for that using the HP-RAKI algorithm. The po-
tential reasons for the relatively long training time of MW-RAKI may be 
the multiplicated network parameters and multiplicated training itera-
tions for using multiple filters. In addition, programming language and 
style may be another reason. Since training should be repeated for each 
set of multi-coil data, the training time difference between MW-RAKI 
and  HP-RAKI can be very  significant, suggesting HP-RAKI as a  favor-
able algorithm for practical fast MRI applications.

HP-GRAPPA used a HP filter to improve GRAPPA reconstruction. HP- 
GRAPPA can reconstruct higher quality images than that of GRAPPA as 
shown in Fig. 4, 6-7. However, due to intrinsic noise amplification by 
GRAPPA, the noise level of HP-GRAPPA is higher than that of HP-RAKI 
at high acceleration factors, for example, using N = 6, as shown by the 
line analysis in Fig. 8A. From the PSNR values and the line analysis in 
Fig. 8, the potential noise amplification of HP-RAKI is not as serious as 
other comparative algorithms. However, obvious under-sampling arti-
facts still remain in HP-RAKI reconstructions at high acceleration fac-
tors, as shown in Fig. 4B and Fig. 7B. Further study will focus on this 
limitation of HP-RAKI to suppress the under-sampling artifacts at high 
acceleration factors. HP filter assisted reconstruction can be more useful 
in practical applications after conquering strip artifacts at high accel-
eration factors.

HP filters were very useful in many reconstruction algorithms, such 
as early polynomial approximation reconstruction (Liang et al.,1989), 
reconstruction  with  structured  low-rank  matrix  modeling  (Haldar, 
2015b; Ongie and Jacob, 2016; Jin et al., 2016), HP-GRAPPA (Huang 
et al., 2008), CS (Cand`es et al., 2006; Lustig et al., 2007), SPEED (Jin 
et  al.,  2013;  Jin  et  al.,  2016;  Xiang  2005),  SCUNET  (Jin  and  Xiang, 
2023), and MW-RAKI (Tao et al., 2023). HP filters can be applied flex-
ibly in image space (Cand`es et al., 2006; Haldar, 2015b, Liang et al., 
1989; Lustig et al., 2007; Ongie and Jacob, 2016; Jin et a., 2016; Jin and 
Xiang,  2023; Zhang et  al., 2019) or  k-space  (Huang et  al., 2008; Tao 
et al., 2023). Although there are many kinds of HP filters, almost all of 
them are simple and effective for MRI reconstructions. In this study, HP 
in k-space was demonstrated to improve the reconstruction quality of 

including  deep 

in  other  reconstructions, 

RAKI  and  rRAKI,  respectively.  Theoretically,  HP  filters  can  be  easily 
applied 
learning  re-
constructions, either in k-space or in image space, since only HP filtering 
and inverse filtering need to be performed before and after training. In 
addition, there are many autoregressive reconstruction methods, each 
has  its  own  distinct  advantages  and  limitations.  Inspired  by  the 
ensemble-based approach (Kim and Haldar, 2019), future studies will 
try to combine HP-RAKI with other state of the art methods to further 
improve the reconstruction.

In summary, this study introduced an HP filtered k-space machine 
learning method for accelerated MRI without extra training data. High- 
pass filter was applied in k-space to obtain image support reduced data. 
HP filtered central fully sampled k-space signals were used to train the 
parameters for HP-RAKI and HP-rRAKI. Inverse HP filtering in k-space 
can recover the suppressed low spatial frequency signals before the final 
IDFT  reconstruction.  The  proposed  algorithms  provided  significantly 
higher  image  quality  for  under-sampled  MRI  data  without  any  extra 
training data.

Data and Code Availability Statements

Multi-coil  k-space  raw  datasets  were  downloaded  from  the  NYU 
(https://fastmri.med.nyu.edu/)  after 

fastMRI 
Initiative  database 
approval of the Institutional Review Board.

The  code  will  be  publicly  accessible  at:  https://github.com/ZhyJi 

n/HP-RAKI.

CRediT authorship contribution statement

Zhaoyang  Jin:  Writing  –  original  draft,  Visualization,  Validation, 
Software, Methodology, Investigation, Conceptualization. Jiuwen Cao: 
Writing – review & editing, Supervision, Project administration, Formal 
analysis,  Conceptualization.  Mei  Zhang:  Validation,  Software,  Meth-
odology.  Qing-San  Xiang:  Writing  –  review  &  editing,  Methodology, 
Investigation, Formal analysis, Conceptualization.

Declaration of competing interest

none

Acknowledgements

The authors are grateful to the grant support from Zhejiang Provin-
cial  Natural  Science  Foundation  of  China  (LZ24F030010),  National 
Natural  Science  Foundation  of  China  (61372024,  U1909209)  and 
financial support from Children’s & Women’s Health Centre of British 
Columbia.

References

Aggarwal, H.K., Mani, M.P., Jacob, M., 2019. MoDL: model-based deep learning 

architecture for inverse problems. IEEE Trans. Med. Imaging 38 (2), 394–405.
Akçakaya, M., Moeller, S., Weing¨artner, S., U˘gurbil, K., 2019. Scan-specific robust 

artificial-neural-networks for k-space interpolation (RAKI) reconstruction: Database- 
free deep learning for fast imaging. Magn. Reson. Med. 81 (1), 439–453.

Arefeen, Y., Beker, O., Cho, J., Yu, H., Adalsteinsson, E., Bilgic, B., 2022. Scan-specific 
artifact reduction in k-space (SPARK) neural networks synergize with physics-based 
reconstruction to accelerate MRI. Magn. Reson. Med. 87, 764–780.

Bernstein, M.A., King, K.F., Zhou, X.J., 2004. Handbook of MRI Pulse Sequences. Elsevier 

Academic Press, Oxford. 

Cand`es, E.J., Romberg, J., Tao, T., 2006. Robust uncertainty principles: exact signal 

reconstruction from highly incomplete frequency information. IEEE Trans. Inform. 
Theory 52, 489–509.

Chang, Z., Xiang, Q.-S., 2007. Simplified skipped phase encoding and edge deghosting 
(SPEED) for imaging sparse objects with applications to MRA. Medical Physics 34 
(8), 3173–3182.

Dawood, P., Blaimer, M., Stebani, J., Burd, P., Homolya, I., Oberberger, J., Jakob, P.M., 
Blaimer, M., 2023. Iterative training of robust k-space interpolation networks for 
improved image reconstruction with limited scan specific training samples. Magn. 
Reson. Med. 89, 812–827.

14 

Z. Jin et al.                                                                                                                                                                                                                                       

NeuroImage 303 (2024) 120926 

Diederik, K., Jimmy, B., 2015. Adam: A method for stochastic optimization. In: the 3rd 
International Conference for Learning Representations. San Diego arXiv:1412.6980. 

Dixon, W.T., 1984. Simple spectroscopic imaging. Radiology 153, 189–194.
Griswold, M.A., Jakob, P.M., Heidemann, R.M., Nittka, M., Jellus, V., Wang, J., Kiefer, B., 

Liang, Z.P., Boada, F.E., Constable, R.T., Haacke, E.M., Lauterbur, P.C., Smith, M.R., 
1992. Constrained reconstruction methods in MR imaging. Magn. Reson. Med. 4, 
67–185.

Liang, Z.P., Haacke, E.M., Thomas, C.W., 1989. High-resolution inversion of finite 

Haase, A., 2002. Generalized autocalibrating partially parallel acquisitions 
(GRAPPA). Magn. Reson. Med. 47, 1202–1210.

Hammernik, K., Klatzer, T., Kobler, E., Recht, M.P., Sodickson, D.K., Pock, T., Knoll, F., 
2018. Learning a variational network for reconstruction of accelerated MRI data. 
Magn. Reson. Med. 79 (6), 3055–3071.

Haacke, E.M., Liang, Z.P., Izen, S.H., 1989. Superresolution reconstruction through 
object modeling and parameter estimation. IEEE Trans. Acoust. Speech Signal 
Process. 37, 592–595.

Han, Y., Sunwoo, L., Ye, J.C., 2019. k-Space deep learning for accelerated MRI. IEEE 

Trans. Med. Imaging 39 (2), 377–386.

Haldar, J.P., 2014. Low-rank modeling of local k-space neighborhoods (LORAKS) for 

constrained MRI. IEEE Trans. Med. Imaging 33 (3), 668–681.

Haldar, J.P., 2015a. Autocalibrated LORAKS for fast constrained MRI reconstruction. 

IEEE ISBI 2015, 910–913.

Fourier transform data through a localised polynomial approximation. Inverse Probl 
5, 831–847.

Lustig, M., Donoho, D.L., Pauly, J.M., 2007. Sparse MRI: The application of compressed 

sensing for rapid MR imaging. Magn. Reson. Med. 58, 1182–1195.

Lustig, M., Pauly, J.M., 2010. SPIRiT: Iterative self-consistent parallel imaging 
reconstruction from arbitrary k-space. Magn Reson Med 64 (2), 457–471.
Min, H.C., Pyung, K.H., Min, L.S., Sungchul, L., Keun, S.J., 2018. Deep learning for 
undersampled MRI reconstruction. Phys. Med. Biol. 63 (13). https://doi.org/ 
10.1088/1361-6560/aac71a.

Nencka, A.S., Arpinar, V.E., Bhave, S., Yang, B., Banerjee, S., McCrea, M., Mickevicius, N. 
J., Muftuler, L.T., Koch, K.M., 2020. Split slice training and hyperparameter tuning 
of RAKI networks for simultaneous multi-slice reconstruction. Magn. Reson. Med. 
85, 3272–3280. https://doi.org/10.1002/mrm.28634.

Ongie, G., Jacob, M., 2016. Off-the-grid recovery of piecewise constant images from few 

Haldar, J.P., 2015b. Low-rank modeling of local k-space neighborhoods: from phase and 

Fourier samples. SIAM J. Imag. Sci 9, 1004–1041.

support constraints to structured sparsity. In: Wavelets and Sparsity XVI, 
Proceedings of SPIE 9597, 2015. San Diego, 959710.

Haldar, J.P., Setsompop, K., 2020. Linear predictability in magnetic resonance imaging 
reconstruction: Leveraging shift-invariant Fourier structure for faster and better 
imaging. IEEE Signal Proc. Mag. 37, 69–82.

Huang, F., Li, Y., Vijayakumar, S., Hertel, S., Duensing, G.R., 2008. High-Pass GRAPPA: 
An Image Support Reduction Technique for Improved Partially Parallel Imaging. 
Magn. Reson. Med. 59, 643–649.

Jin, K.H., Lee, D., Ye, J.C., 2016. A general framework for compressed sensing and 

parallel MRI using annihilating filter based low-rank Hankel matrix. IEEE Trans. 
Comput. Imag. 2, 480–495.

Jin, Z., Xiang, Q.S., 2013. Accelerated MRI by SPEED with generalized sampling 

schemes. Magn. Reson. Med. 70, 1674–1681.

Jin, Z., Ye, H., Du, Y.P., Xiang, Q.S., 2016. Improving image quality for skipped phase 
encoding and edge deghosting (SPEED) by exploiting several sparsifying transforms. 
Magn. Reson. Med. 75, 2031–2040.

Jin, Z., Xiang, Q.S., 2023. Improving accelerated MRI by deep learning with sparsified 
complex data. Magn. Reson. Med. 89, 1825–1838. https://doi.org/10.1002/ 
mrm.29556.

Kim, T.H., Haldar, J.P., 2019. Learning how to interpolate Fourier data with unknown 
autoregressive structure: an ensemble-based approach. In: 2019 53rd Asilomar 
Conference on Signals, Systems, and Computers. Pacific Grove, CA, USA, 
pp. 1471–1475.

Kim T.H., Garg P., Haldar J.P.,2019. LORAKI: autocalibrated recurrent neural networks 

for autoregressive MRI reconstruction in k-space. https://arxiv.org/abs/1 
904.09390.

LeCun, Y., Bengio, Y., Hinton, G., 2017. Deep learning. Nature 521 (7553), 436–444.

Knoll, F., Zbontar, J., Sriram, A., Muckley, M.J., Lui, Y.W., 2020. fastMRI: a publicly 

available raw k-Space and DICOM dataset of knee images for accelerated MR image 
reconstruction using machine learning. Radiol. Artif. Intell. 2 (1), e190007. https:// 
doi.org/10.1148/ryai.2020190007.

Tao, H., Zhang, W., Wang, H., Wang, S., Liang, D., Xu, X., Liu, Q., 2023. Multi-weight 
respecification of scan-specific learning for parallel imaging. Magn. Reson. Imaging. 
97, 1–12. https://doi.org/10.1016/j.mri.2022.12.009.

Wang, S., Su, Z., Ying, L., Xi, P., Zhu, S., Liang, F., Feng, D., Liang, D., 2016. Accelerating 
magnetic resonance imaging via deep learning. In: IEEE International Symposium on 
Biomedical Imaging, pp. 514–517.

Xiang, Q.S., 2005. Accelerating MRI by skipped phase encoding and edge deghosting 

(SPEED). Magn. Reson. Med. 53, 1112–1117.

Zbontar J., Knoll F., Sriram A., Muckley M.J., Murrell T., 2019. fast MRI: an open dataset 

and benchmarks for accelerated MRI. arXiv:1811.08839.

Zhang, C., Hosseini, S.A.H, Weing¨artner, S., U˘gurbil, K., Moeller, S., Akçakaya, M., 2019. 
Optimized fast GPU implementation of robust artificial-neural-networks for k-space 
interpolation (RAKI) reconstruction. PLoS ONE 14 (10), e0223315. https://doi.org/ 
10.1371/journal.pone.0223315.

Zhang, C., Moeller, S., Demirel, O.B., Ugurbil, K., Akçakaya, M., 2022. Residual RAKI: A 
hybrid linear and non-linear approach for scan-specific k-space deep learning. Neuro 
Image 256, 119248.

Zhang, J., Liu, C., Moseley, M.E., 2011. Parallel reconstruction using null operations. 

Magn Reson Med 66 (5), 1241–1253.

Zhang, J., Chu, Y., Ding, W., Kang, L., Xia, L., Jaiswal, S., Wang, Z., Chen, Z., 2019. HF- 
SENSE: an improved partially parallel imaging using a high-pass filter. BMC medical 
imaging 19 (27), 1–10.

Zhou, W., Bovik, A.C., Sheikh, H.R., Simoncelli, E.P., 2004. Image quality assessment: 
from error visibility to structural similarity. IEEE Trans. Image Process. 13 (4), 
600–612.

15 

