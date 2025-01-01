NeuroImage 303 (2024) 120921 

Contents lists available at ScienceDirect

NeuroImage

journal homepage: www.elsevier.com/locate/ynimg

ACGRHA-Net: Accelerated multi-contrast MR imaging with adjacency 
complementary graph assisted residual hybrid attention network

Haotian Zhang 1, Qiaoyu Ma 1, Yiran Qiu , Zongying Lai *

School of Ocean Information Engineering, Jimei University, Xiamen, China

A R T I C L E  I N F O

A B S T R A C T

Keywords:
Adjacency complementary graph
Residual hybrid attention
Deep learning
Accelerated multi-contrast MR imaging

Multi-contrast magnetic resonance (MR) imaging is an advanced technology used in medical diagnosis, but the 
long acquisition process can lead to patient discomfort and limit its broader application. Shortening acquisition 
time  by  undersampling  k-space  data  introduces  noticeable  aliasing  artifacts.  To  address  this,  we  propose  a 
method that reconstructs multi-contrast MR images from zero-filled data by utilizing a fully-sampled auxiliary 
contrast MR image as a prior to learn an adjacency complementary graph. This graph is then combined with a 
residual hybrid attention network, forming the adjacency complementary graph assisted residual hybrid atten-
tion  network  (ACGRHA-Net)  for  multi-contrast  MR  image  reconstruction.  Specifically,  the  optimal  structural 
similarity is represented by a graph learned from the fully sampled auxiliary image, where the node features and 
adjacency  matrices  are  designed  to  precisely  capture  structural  information  among  different  contrast  images. 
This  structural  similarity  enables  effective  fusion  with  the  target  image,  improving  the  detail  reconstruction. 
Additionally,  a  residual hybrid  attention  module  is  designed  in  parallel  with  the  graph  convolution  network, 
allowing  it  to  effectively  capture  key  features  and  adaptively  emphasize  these  important  features  in  target 
contrast  MR  images.  This  strategy  prioritizes  crucial  information  while  preserving  shallow  features,  thereby 
achieving  comprehensive  feature  fusion  at  deeper  levels  to  enhance  multi-contrast  MR  image  reconstruction. 
Extensive  experiments  on  the  different  datasets,  using  various  sampling  patterns  and  accelerated  factors 
demonstrate that the proposed method outperforms the current state-of-the-art reconstruction methods.

1. Introduction

Multi-contrast  magnetic  resonance  (MR)  imaging  offers  diverse 
diagnostic information by displaying different contrast types. As shown 
in Fig. 1, (a) clearly shows anatomical morphology, while (c) highlights 
the area of inflammation. Although (b) and (d) differ in visual contrast, 
both share similar structural information. Initially, to accelerate multi- 
contrast  MR  imaging,  several  traditional  techniques  (Lustig  et  al., 
2007; Bilgic et al., 2011; Yaman et al., 2019; Lai et al., 2018; Gungor 
et al., 2017; Yi et al., 2021; Bustin et al., 2018; Esfahani, 2022; Bustin 
et al., 2019; Pingfan et al., 2018; Ehrhardt and Betcke, 2016) have been 
introduced. These include compressed sensing (Lustig et al., 2007; Bilgic 
et al., 2011; Sun et al., 2019), dictionary learning (Gungor et al., 2017; 
Pingfan et al., 2018), structure-guided total variation (Esfahani, 2022; 
Ehrhardt and Betcke, 2016), patch-based algorithms (Bustin et al., 2018; 
Bustin et al., 2019), low-rank (Yaman et al., 2019; Yi et al., 2021), and 
graph representation theory (Lai et al., 2018) reduce the sampling time 

and improve the reconstruction quality of multi-contrast MR imaging 
from different perspectives. For example, Lai et al. (2018) proposed a 
graph-based  redundant  wavelet  transform  (GBRWT)  method  for  joint 
sparse  reconstruction  of  multi-contrast  MR  images.  This  method  en-
hances  image  sparsity  by  capturing  and  leveraging  correlations  and 
structural information between images, thereby improving reconstruc-
tion performance.

Recently,  deep  learning-based  methods  (Zeng  et  al.,  2018;  Peng 
et al., 2020; Zhou and Zhou, 2020; Kim et al., 2018; Lyu et al., 2020; Wei 
et al., 2022; Falvo et al., 2019; Dhengre and Sinha, 2022; Feng et al., 
2024; Huang et al., 2022; Li et al., 2022; Li et al., 2022; Lyu et al., 2022; 
Korkmaz et al., 2022; Aghabiglou and Eksioglu, 2021; Liu et al., 2021; 
Feng et al., 2022; Wang et al., 2023; Dar et al., 2020) have been intro-
duced  to  accelerate  multi-contrast  MR  imaging.  These  methods  are 
broadly categorized into guided reconstruction and joint reconstruction. 
In guided reconstruction, auxiliary contrast MR images serve as prior 
information to guide the reconstruction of target contrast MR images. 

* Corresponding author at: No. 185 Yinjiang Road, Jimei Zone, Xiamen City, Fujian Province, 361021, China

E-mail address: zongyinglai@jmu.edu.cn (Z. Lai). 
1 These authors contributed equally to this work.

https://doi.org/10.1016/j.neuroimage.2024.120921
Received 4 August 2024; Received in revised form 4 November 2024; Accepted 6 November 2024  
Available online 7 November 2024 
1053-8119/© 2024 The Authors. Published by Elsevier Inc. This is an open access article under the CC BY-NC-ND license ( http://creativecommons.org/licenses/by- 
nc-nd/4.0/ ). 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

Joint  reconstruction,  on  the  other  hand,  simultaneously  reconstructs 
images  across  multiple  contrasts.  For  instance,  Li  et  al.  (2022) incor-
porated  a  cross-attention  transformer  (Wavtrans)  based  on  wavelet 
transform  to  enhance  the  clarity  and  structural  accuracy  of 
multi-contrast MR images. Similarly, SDAUT (Huang et al., 2022) im-
proves reconstruction performance by integrating a Swin Transformer 
with  a  deformable  attention  mechanism  to  better  capture  image  fea-
tures.  MD-GraphFormer  (Wang  et  al.,  2023)  combines  a  transformer 
architecture  based  on  graphs  to  capture  structural  correlations  and 
long-distance  dependencies  between 
thus  accelerating 
multi-contrast MR imaging and enhancing image quality.

images, 

Multi-contrast  image  feature  fusion  which  combines  images  from 
different  contrasts  into  one  input,  leverages  the  complementary  and 
shared structural features among contrasts, offering greater robustness 
than  relying  on  a  single  contrast  image.  For  example,  hybrid  fusion 
networks (Zhou et al., 2020) have been used to synthesize multi-contrast 
MR images. In attempts to accelerate multi-contrast MR imaging, some 
methods (Sun et al., 2019; Dar et al., 2020; Xiang et al., 2018) concat-
enate auxiliary contrast and target contrast MR images before feeding 
them into the network or use information extracted from the auxiliary 
contrast image to augment the target contrast image. However, current 
fusion methods (Sun et al., 2019; Dar et al., 2020; Xiang et al., 2018) 
primarily treat auxiliary contrast MR images as additional inputs, only 
modestly  improving  image  quality.  They  fail  to  fully  explore  the  po-
tential  complementarity  and  dynamic  interaction  between  different 
contrasts. Future work needs delve deeper into these potential comple-
mentary relationships to further accelerate multi-contrast MR imaging 
and enhance reconstruction quality.

In this study, we propose an adjacency complementary graph assis-
ted residual hybrid attention network (ACGRHA-Net) for accelerating 
multi-contrast MR imaging. As shown in Fig. 2, ACGRHA-Net consists of 
two  parallel  sub-networks:  adjacency  complementary  graph  network 
(ACG-Net) and residual hybrid attention network (RHA-Net). ACG-Net 
constructs adjacency matrices derived from auxiliary contrast images, 
mapping relationships between image patches and transforming target 
image  patches  into  graph-based  features.  Meanwhile,  the  residual 
hybrid  attention  module  (RHAM)  integrates multiple  block structures 
that combine channel attention and spatial attention, offering enhanced 
flexibility to process various types of information within a local residual 
learning structure. RHAM’s multi-block structure allows for the reten-
tion  and  transfer  of  shallow  feature  information  to  deeper  layers, 
boosting feature processing efficiency by fusing all features and adap-
tively assigning higher importance to crucial information. This results in 
more effective image reconstruction. The contributions of this study are 
as follows: 

• We introduce a novel method using graph-based modeling from fully 
sampled auxiliary contrast images to train graph filters, better cap-
ture inter-patch connections between multi-contrast MR images, and 
improve 
image 
reconstruction.

for  multi-contrast  MR 

integration 

feature 

• A  hybrid  attention  mechanism  combining  channel  and  spatial 
attention  within  a  residual  learning  framework  is  proposed,  using 
multiple block structures with residual hybrid attention in each block 
to enhance the ability to adaptively weight and focus on key features, 
thereby  improving  reconstruction  accuracy  and  overall  feature 
discrimination.

• Experimental results show that the proposed method, by leveraging 
the combined strategies of two parallel networks, outperforms the 
current  state-of-the-art  methods  in  target  contrast  MR  image 
reconstruction.

2. Related works

2.1. Accelerated single-contrast MR imaging

With  the  advancement  of  deep  learning  technology,  end-to-end 
methods  (Schlemper  et  al.,  2017;  Wang  et  al.,  2016;  Ronneberger 
et  al., 2015; Jin et  al., 2017)  have been  widely applied in  the recon-
struction of single-contrast MR images. The Convolutional neural net-
works  (CNN)  leverage  their  local  convolution  operations  to  deeply 
extract image features and learn complex patterns, effectively restoring 
high-quality images from those containing aliasing artifacts. Wang et al. 
(2016) were the first to apply CNN to accelerated MR imaging, while Jin 
et  al.  (2017) tackled  the  inverse  imaging  problem  using  U-Net  archi-
tecture.  To  enhance  the  interpretability  and  effectiveness  of  clinical 
applications,  model-based  deep  learning  methods  (Aggarwal  et  al., 
2018; Zeng et al., 2020; Yang et al., 2018; Hammernik et al., 2018) have 
also been introduced. Aggarwal et al. (Aggarwal et al., 2018) combined 
model-driven approaches with data-driven learning to improve image 
reconstruction quality by enhancing data consistency and reducing ar-
tifacts. ADMM-CSNet (Yang et al., 2018) proposed a deep learning-based 
compressed  sensing  approach,  achieving  strong  performance  by  inte-
grating the alternating direction multiplier method (ADMM) with CNN. 
Additionally,  generative  adversarial  networks  (GAN)  (Mardani  et  al., 
2018; Zhao et al., 2023), consisting of a generator and discriminator, 
have  been 
reconstruction. 
Transformer-based architectures (Zhao et al., 2023; Feng et al., 2021; 
Zhang et al., 2021; Luo et al., 2021) have been increasingly applied to 
medical  imaging,  as  they  excel  at  capturing  long-range  dependencies 
and  establishing  remote  contextual  connections.  By 
leveraging 
self-attention  mechanisms,  these  models  can  effectively  learn  global 
relationships within images. Zhao et al. (2023) introduced Swin-GAN, a 
dual-domain cascade generator that effectively utilizes MR image fre-
quency  domain  information,  reconstructing  the  entire  k-space  by 
leveraging zero-filled k-space data to capture key information. Spectral 
graph convolution (Osher et al., 2017; Ma et al., 2024) has also been 
used  to  enhance  the  structural  and  regional  connectivity  within  MR 
images. Ma et al. (2024) applied a graph convolutional network (GCN) 
to improve self-similarity in MR image reconstruction. Building on the 
acceleration  of  single-contrast  MR  images,  recent  studies  have  begun 
exploring feature sharing between different contrast MR images, using 

single  MR 

applied 

image 

to 

Fig. 1. Example of two different contrast MR images and their structural information. (a) and (c) are auxiliary and target MR images of the same subject. (b) and (d) 
are their corresponding structural information. Different contrasts from the same subject showed consistent structural features.

2 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

Fig. 2. The overall structure of ACGRHA-Net consists of two parallel learning architectures. The ACG-Net extracts the adjacency relationship between the image 
patches of the auxiliary contrast MR image and the node features in the target contrast MR image, thus building an adjacency complementary graph, and then 
facilitates the information exchange by using the similarity weights in the adjacency matrix through graph convolutional network. Meanwhile, RHA-Net utilizes 
cascaded residual hybrid attention modules to enhance deep feature extraction. The detailed structure of ACG-Net is delineated within the red dashed box. While the 
components of RHA-Net are highlighted in the blue dashed box.

auxiliary contrast images as prior information to guide target contrast 
image reconstruction.

2.2. Accelerated multi-contrast MR imaging

Multi-contrast MR images capture different physical and biochem-
ical properties of the same anatomical region, providing doctors with a 
more  accurate  basis  for  identifying  and  differentiating  pathological 
changes. By fusing these different contrast images, the complementary 
information  and  shared  features  between  them  can  significantly 
enhance the quality of image reconstruction (Lai et al., 2018; Zhou and 
Zhou, 2020; Li et al., 2022; Lyu et al., 2022; Liu et al., 2021; Feng et al., 
2022; Dalmaz et al., 2022; Li et al., 2024; Luo et al., 2023; Yang and Li`o, 
2023;  Güng¨or  et  al.,  2023).  Yang  and  Li`o,  2023)  introduced  a 
dual-domain multi-contrast MRI reconstruction method that utilizes a 
synthesis-based  fusion  network  to  process  and  integrate  information 
from  both  image  and  frequency  domains,  improving  reconstruction 
quality. Liu et al. (Liu et al., 2021) applied a channel attention mecha-
nism, assigning different weights to feature maps for multi-contrast MR 
image reconstruction. AdaDiff (Güng¨or et al., 2023) employs an adap-
tive  diffusion  prior  trained  via  adversarial  mapping  to  optimize  MR 
image reconstruction performance and enhance adaptation to domain 
variations. The cross-domain reconstruction is improved by fine-tuning 
the prior and minimizing data consistency loss. SSDiffRecon (Korkmaz 
et al., 2023) is an innovative self-supervised deep reconstruction model 
that overcomes  the limitations  of existing methods  in  terms of image 
fidelity,  contextual  sensitivity,  and  reliance  on  fully  sampled  acquisi-
tions. It achieves this by expressing the conditional diffusion process as 
an unfolded architecture, interleaving cross-attention transformers for 
reverse diffusion steps with data consistency blocks for physics-driven 
processing.  Xiang  et  al.  (2018) introduced  Dense-Unet,  which  uses 
fully sampled T1 and undersampled T2 images as inputs to recover the 
target  contrast  image.  The  Transformer  architecture  has  become  a 
popular  research  direction  due  to  its  exceptional  ability  to  establish 

3 

contextual connections. DuDoCAF (Lyu et al., 2022) utilizes a recursive 
Transformer structure to fuse features from different contrast images for 
reconstruction.  DS-TransUNet  (Lin  et  al.,  2022)  proposes  a  novel 
Transformer  interaction  fusion  module  to  enhance  global  contextual 
learning. DSFormer (Zhou et al., 2023) is a self-supervised Transformer 
model that effectively integrates multi-contrast information through a 
dual-domain  self-supervised  learning  strategy  and  a  cascaded  Swin 
Transformer  network,  achieving  multi-contrast  image  reconstruction 
with  performance  comparable  to  fully  supervised  methods,  even 
without fully sampled data. MD-GraphFormer (Wang et al., 2023) is a 
model-driven  graph  Transformer 
the  Graph 
Attention-Based Interaction Module (GAB-IM) with the Multi-Contrast 
Data  Consistency  Module  (MC-DCM),  deeply  mining  complementary 
information between different MRI contrasts. Additionally, by incorpo-
rating MRI’s physical constraints, it enables efficient multi-contrast MR 
image reconstruction.

integrates 

that 

2.3. Multi-contrast MR image features fusion

long-range  contextual 

Multi-contrast image feature fusion enhances robustness compared 
to using single-contrast images by leveraging the complementary and 
shared  structural  features  of  different  contrast  images,  merging  them 
into a single input image. For example, hybrid fusion networks (Zhou 
et al., 2020) have been utilized to synthesize multi-contrast MR images. 
I2I-Mamba (Atli et al., 2024) is a novel adversarial model that effectively 
captures 
through  selective 
state-space modeling while preserving local details via channel-mixed 
Mamba  modules, 
in 
multi-contrast MR imaging. MCCA (Li et al., 2024) employs a multi-scale 
feature  fusion  strategy  to  reconstruct  undersampled  modalities  by 
integrating the transferable complementary knowledge from auxiliary 
modalities into target modalities. MTrans (Feng et al., 2022) utilizes an 
improved  multi-attention  mechanism  to  efficiently  integrate  features 
between  auxiliary  and  target  modalities  to  capture  richer  structural 

synthesizing  missing 

relationships 

thereby 

images 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

information and details. DuDoRNet (Zhou and Zhou, 2020) improves the 
quality of MR imaging by simultaneously reconstructing both the image 
domain and  the k-space  domain, in particular using T1WI  as a  depth 
prior. MCMRSR (Li et al., 2022) proposes a novel multi-scale contextual 
matching  mechanism,  capturing  contextual  information  in  reference 
features at different scales. It utilizes complementary information from 
different contrast images to achieve the super-resolution reconstruction 
of multi-contrast MR images. However, leveraging the complementary 
information from different contrasts using GCN (Hammond et al., 2011; 
Kipf  and  Welling,  2016)  is  still  relatively  uncommon.  GCN  naturally 
processes images as graph-structured data, where nodes represent local 
regions or features of the image, and edges represent the connections 
between  these  regions.  By  utilizing  an  auxiliary  contrast  image  to 
enhance  these  connections,  GCNs  can  effectively  capture  the  global 
structure while establishing local associations between the target and 
auxiliary images, leading to more efficient integration of complemen-
tary information from multi-contrast images.

3. Problem definition

To simulate the k-space zero-filling process in real-world scenarios, 
the  fully  sampled  complex-valued  k-space  data  kf  is  element-wise 
multiplied by a zero-filled matrix M to produce the zero-filled k-space 
data kz  (as shown in Fig. 2). The zero-filled images xz  are then obtained 
by performing an inverse Fourier transform on kz. This process can be 
expressed as: 
xz = F (cid:0) 1
= F (cid:0) 1
M∘kf + ϕ
= F (cid:0) 1(kz + ϕ),

)
M∘F xf + ϕ
)

(1) 

(cid:0)

(cid:0)

where  xf ∈ CH × W  is  the  fully  sampled  MR  image,  H  and  W  are  the 
image dimensions, F  and F (cid:0) 1 represent the fast Fourier transform and 
its inverse, ϕ is noise, and ‘∘’ is element-wise multiplication. The goal of 
zero-filled  image  reconstruction  is  to  accurately  restore  the  original 
image xf  from limited, noise k-space data kzby leveraging image sparsity 
in a specific domain and other regularization strategies. Typically, the 
CS-MRI model can be represented by an optimization problem: 

xr = argmin

xf

‖ M∘F xf (cid:0) kz ‖2

2

+ γξ

(cid:0)

)
,

xf

multi-contrast  MR  images  as  input  and  processes  them  through  two 
parallel branches.  One branch  is the  adjacency complementary  graph 
network (ACG-Net), which is based on spectral graph convolution (Kipf 
and Welling, 2016), while the other branch is the attention-based re-
sidual  hybrid  attention  network  (RHA-Net).  ACG-Net  leverages  the 
structural  similarity  between  multi-contrast  MR  images  (as  shown  in 
Fig. 1) to learn and interact with complementary features. Meanwhile, 
RHA-Net  uses  a  hybrid  attention  mechanism  to  focus  on  important 
features in the target contrast MR images, reducing interference from 
irrelevant  information  to  improve  reconstruction  quality.  Next,  we 
describe our architecture in detail.

4.1. Two-branch learning network (ACGRHA-Net)

The  ACGRHA-Net  reconstructs  the  target  MR  image  end-to-end, 
using  zero-filled  target  contrast  MR  images  as  input.  Both  ACG-Net 
and  RHA-Net  operate  in  parallel.  First,  ACG-Net  converts  the  target 
and  auxiliary  contrast  MR  images  into  graph  structures  for  graph 
convolution. Specifically, the target MR image uses the adjacency matrix 
of  the  auxiliary  contrast  MR  images  as  prior  information  to  guide  its 
reconstruction, thereby improving contour processing. Simultaneously, 
RHA-Net  deeply  extracts  and  fuses  features  through  hybrid  attention 
and residual learning, preserving shallow features while allowing them 
to pass through deeper layers. Due to the weighting mechanism, RHA- 
Net  emphasizes  large  artifact  areas,  high-frequency  textures,  and 
important details in the image. Finally, the output features of the two 
sub-networks are fused, and the final reconstruction is obtained through 
a data consistency (DC) layer: 

(cid:0)

)

= fDC
{[

xtari
r
= F (cid:0) 1

αxtari
ACG
(1 (cid:0) M)∘F

+ βxtari
RHA
(cid:0)
αxtari
ACG

+ βxtari
RHA

)]

}

,

+ ktari
z

(4) 

r

∈ RC × H × W  represents  the  final  reconstruction  result, 
where  xtari
∈ RC × H × Wof ACG-Net and 
which fuses with the output feature xtari
ACG
∈ RC × H × W  of RHA-Net via the DC layer fDC. 
the output feature xtari
RHA
represents  undersampled  k-space,  while  α  and  β  are 
The  term  ktari
z 
trainable  weights  that  balance  the  contributions  of  the  two  network 
outputs, ensuring optimal reconstruction quality, where α + β = 1.

(2) 

4.2. Adjacency complementary graph

where ‖ ⋅ ‖2
2  is l2  norm measuring consistency between the reconstruc-
tion MR image and observed data, ξ(⋅) is a regularization term that in-
corporates  prior  knowledge,  γ  balances  reconstruction  quality  and 
regularization,  and  xr is  the  approximately  fully  sampled  images 
reconstructed from the zero-filled images. In the deep learning model, 
the reconstruction task becomes an end-to-end learning problem, where 
the mapping from zero-filled k-space data to the fully sampled image 
space is learned directly. This process can be described as: 

xr = argmin

ΘAR

‖ M∘F

(cid:0)

)
(xz|ΘAR)

N ΘAR

(cid:0) kz‖2

2

+ γ‖ xf (cid:0) N ΘAR

(xz|ΘAR) ‖2

2

,

(3) 

where N ΘAR  is the neural network ACGRHA-Net proposed in this paper 
driven by parameter ΘAR. Based on the above issues, the next section 
introduces  the  ACGRHA-Net  architecture,  focusing  on  its  two  sub- 
networks: ACG-Net and RHA-Net. The overall structure (illustrated in 
Fig.  2)  employs  multi-block  hybrid  attention  networks  to  recover 
essential  image  features,  while  the  adjacency  complementary  graph 
network  facilitates  multi-contrast  MR  image  reconstruction  by  fusing 
image features of different contrasts in parallel.

4. ACGRHA-Net architecture

As  shown  in  Fig.  2,  the  proposed  ACGRHA-Net  takes  zero-filled 

4 

i

Given the structural similarities between fully sampled auxiliary and 
target contrast MR images, we extract the adjacency relationships be-
tween image patches from the auxiliary image and node feature from the 
target  image  to  establish  the  adjacency  complementary  graph  (ACG). 
∈ RN × N  (i = 1, 2, ⋯, N represented as the 
Then adjacency matrix Aaux
i-th image) is constructed by calculating the similarity weights ε of each 
source  image  patch  np
i  in  the  auxiliary  contrast  image  and  its  most 
similar  image  patches  nq
i .  This  matrix  effectively  captures  structural 
similarities in auxiliary contrast images. For multi-contrast MR images, 
)
(cid:0)
, E aux
we  form  a  graph  G i =
,  where  V i  is  the  set  of  nodes 
(cid:0)
i
np
, nq
np
(p, q = 1, 2, ⋯, N).  To 
i
i
i
deepen the connection between nodes, the similarity between them is 
measured using a Gaussian-weighted Euclidean distance (Osher et al., 
2017): 

∈ V i and  E i  represents  edges 

V tar
i

∈ E i

)

(

Aaux
i

= exp

(cid:0)

)

,

‖2
(cid:0) nq
‖ np
i
i
2
)2
(cid:0)
V aux
σ
i

(5) 

(cid:0)

)

V aux
i

where σ
is the standard deviation of the nodes in the auxiliary 
contrast MR images. Gaussian weighting adjusts the connection strength 
based on node proximity, reducing the influence of distant nodes and 
emphasizing key relationships, thus improving the model’s sensitivity 
and stability in representing structural information. Initially, the node 
features in the graph are represented as vectorized image patches, while 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

i

∑
N
q Aaux
i 

represents  the  similarity  weight  between 
=

the  adjacency  matrix  Aaux
i 
these  patches.  The  diagonal  degree  matrix  Daux
represents 
the total influence of the p-th node on all other nodes in the graph. As 
shown  in  Fig.  3,  after  identifying  similar  positions  of  source  image 
patches  in  the  auxiliary  image,  we  map  these  locations  to  the  corre-
sponding patches in the target image, which serve as node features in the 
graph.  Once  the  adjacency  matrices  and  node  features  are  prepared, 
they are input into a graph convolutional network (GCN) (Osher et al., 
2017; Ma et al., 2024; Kipf and Welling, 2016): 

fθ ∗ Btar
i

= UfθUTBtar
i

,

(6) 

i

(cid:0) 1
2Aaux

∈ RN × M  is the matrix of node features of i-th target contrast 
where Btar
MR images stacked by rows and fθ  is the spectral kernel parameterized 
by θ ∈ RN, i.e. fθ = diag(θ). U is the eigenvector matrix of the normal-
(cid:0) 1
ized Laplacian operator, i.e. L = I (cid:0) Daux
2 = UΛUT, where I 
represents the identity matrix and Λ is the diagonal matrix of the Lap-
lacian eigenvalues. To reduce computational complexity, through Che-
byshev  polynomial  expansion  (Hammond  et  al.,  2011),  which  is  an 
,  where  ̂L  =
approximation  to  Eq.  (6),  fθ ∗ Btar
(2 /λmax)L (cid:0)
I, λmax  is the largest eigenvalues of L, and Tj(⋅) is the Che-
byshev polynomial. For J = 2, λmax ≈ 2, θ0 = θ1 = (cid:0) θ, Eq. (6) can be 
⎛
⎝Daux

further  rewritten  as  fθ ∗ Btar

j=0 θjTj(̂L)Btar

⎞
⎠Btar

.  We  further 

(cid:0) 1
2Aaux

i Daux
i

∑
J

= θ

(cid:0) 1
2

≈

i

i

i

i Daux
i

i

i

i

extend the graph filtering process to multiple input channels using the 
renormalization  technique  for  Kipf  and  Welling (2016),  which  means 
∈ RN × M  with 
that the filtering method is also applicable to signals Btar

N input channels. Let 

̂
A

aux
i

= I + Aaux

i

̂
D

aux
i

, 

=

Wtar
i

= ̂

Daux
i

(cid:0) 1
2 ̂
A

aux

i

̂
Daux
i

(cid:0) 1
2Btar

i Φ,

∑

i

̂
A

q

aux
i  we can get: 

(7) 

∈ RN × F  is the target 
where Φ ∈ RM × F  is the filter parameter and Wtar
and Btar
contrast MR image after graph convolution. 
represent the 
i 
adjacency matrices and node features of the auxiliary and target contrast 
MR images, respectively.

i
aux
i 

̂
A

In summary, the most similar image patches in the target contrast 
image are linked to their corresponding source image patch through the 
edges of the auxiliary contrast image, forming the ACG. Once the ACG is 
input, the GCN updates its training parameter Φ to adaptively merge the 
source image patches with their adjacent nodes leveraging the optimal 
structural similarity from the auxiliary construct image. In other words, 
similarity  image  patches  interact  through  the  GCN,  which  uses  the 
similar  weights  in  the  adjacency  matrix  to  facilitate  information  ex-
change, thereby achieving effective assisted reconstruction.

4.3. Residual hybrid attention

This section introduces the residual hybrid attention network (RHA- 

z

Net)  as  shown  in  Fig.  4.  The  input  to  RHA-Net  is  a  zero-filled  target 
∈ R2 × H × W. Initially, the input feature map 
contrast MR image, xtari
undergoes a convolutional layer to adjust the number of channels and 
∈ RC × H × W.  Then 
enhance  the  feature  extraction,  yielding  xtari
C
enhanced feature map xtari
is further processed through a residual hybrid 
C 
attention  module  (RHAM)  to  extract  and  fuse  critical  features,  i.e. 
xtari
RHAMl ,  where  l = 1, 2, ⋯, N  represents  the  l-th  RHAM.  Each  RHAM 
consists  of  N  blocks,  with  each  block  incorporating  both  a  channel 
attention  module  (CAM)  and  a  spatial  attention  module  (SAM)  com-
bined with residual learning.

Block Structure (BS) The block structure integrates local residual 
learning  with  CAM  and  SAM,  facilitating  direct  signal  transmission 
through  residual  connections.  This  design  effectively  addresses  the 
vanishing gradient issue in deep networks and enhances deep feature 
learning. By filtering out less significant information, the network fo-
cuses on crucial details, ultimately improving the reconstruction quality 
of the target contrast MR image. This process is expressed as: 
(

)))

))

(

(

(

(

xtari
BSk

= fSAM

fCAM

Conv

ReLU

Conv

xtari
BSk(cid:0) 1

+ xtari

BSk(cid:0) 1

+ xtari

BSk(cid:0) 1

,

(8) 

(k = 1, 2, ⋯, N) represents the output of the k-th block, xtari

where xtari
BSk
BSk(cid:0) 1 
is the input of k-th block and the input of the first block is xtari
C . Conv(⋅)
represent a convolution layer with a 3 × 3 kernel and ReLU(⋅) denotes 
the  ReLU  activation  function.  fCAM  and  fSAM  refer  to  the  channel  and 
spatial attention modules, respectively.

Residual  Hybrid  Attention  Module  (RHAM)  The  RHAM  is 
composed of N blocks and a final global residual learning component. In 
this  implementation,  20  blocks  are  used  to  gradually  deepen  feature 
learning through successive hybrid attention mechanisms and residual 
connections. This process is expressed as: 
(
f 1
BS

(
f k(cid:0) 1

+ xtari

= f k
BS

xtari
RHAMl(cid:0) 1

xtari
RHAMl

))))

RHAMl(cid:0) 1

(9) 

⋯

(

(

BS

,

where xtari
RHAMl  represents the output of the l-th RHAM which also serves as 
the input to the l + 1-th RHAM, and f k
BS  is the l-th block structure. Four 
RHAMs are used, with the output of each connected through skip con-
nections.  After  the  final  RHAM,  two  convolutional  layers,  a  CAM,  a 
PAM,  and  a  global  residual  learning  component  are  applied  to  effec-
tively  restore  the  texture  details  of  the  zero-filled  target  contrast  MR 
images. This design enhances feature extraction and information fusion, 
further improving the quality of reconstructed images.

4.4. Loss function

The  loss  function  for  ACGRHA-Net  measures  the  discrepancy  be-
tween the fully sampled and reconstructed target contrast MR images 
using the mean square error (MSE). This is mathematically expressed as: 

Fig. 3. In the target contrast MR image, a source image patch and seven other similar image patches are selected, and the most similar one is the source image patch 
itself. Auxiliary contrast MR images serve as edges to represent their weight of similarity.

5 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

Fig. 4. Detailed structure of RHA-Net and its key components are as follows: RHA-Net is comprised of multiple Residual Hybrid Attention Module (RHAM), with each 
RHAM being made up of several Blocks primarily composed of channel attention and spatial attention. The deep extraction of features with the network is achieved 
through the cascaded RHAMs. In the proposed method, a configuration of 4 RHAMs with 20 Blocks is chosen to optimize feature learning and representation.

Loss(ΘAR) = 1
N

∑N

i=1

‖ xtari
gt

(cid:0) xtari
r

,

‖2
2

(10) 

Table 1 
Training configurations and model parameters of ACGRHA-Net.

where N represents the batch size, xtari
and reconstructed target contrast MR images, ‖ ⋅ ‖2
represents the learnable parameters of ACGRHA-Net.

gt  and xtari
r 

represent ground truth 
2  is l2  norm, and ΘAR 

5. Experiments

5.1. Datasets

We  use  two  raw  MR  image  datasets  to  evaluate  our  method:  (1) 
fastMRI  (Zbontar  et  al.,  2018),  a  large  publicly  available  dataset 
accessible  at  https://fastmri.med.nyu.edu/.  We  selected  the  brain 
dataset, filtering out 768 and 96 pairs of T1WI and T2WI brain slices for 
training and validation. (2) IXI, which contains single-coil brain data, is 
available at https://brain-development.org/ixi-dataset. From this data-
set, we filter out 600 and 75 pairs of T1WI and T2WI brain slices for 
training and validation. In both datasets, each slice has a resolution of 
256 × 256 pixels, with all pixel values normalized to the range [0, 1]. 
T1WI serves as the auxiliary contrast image, while T2WI is the target 
contrast image.

5.2. Experiments details

As  shown  in  Table  1,  the  proposed  ACGRHA-Net  is  implemented 
using  PyTorch  (version  2.0.0),  running  on  an  Ubuntu  22.04  system 
environment. The hardware setup includes an NVIDIA 3090Ti GPU with 
24GB  of  VRAM  and  an  Intel  i9–12900KF  CPU.  The  training  process 
= 0.9 and 
utilizes the AdamW optimizer, where the hyperparameters β1 
(cid:0) 3 
= 0.999 are set for optimization. The initial learning rate is set to 1e
β2
and decays by a factor of 0.9 after a predefined number of steps using a 
step-learning policy. The model is trained for 100 epochs, with a batch 
size of 1, and random seed 42 is used to ensure reproducibility.

β1, β2  of AdamW
Initial learning rate

0.9, 0.999
1e

(cid:0) 3

Type

Setting

Type

Pytorch (2.0.0)

Optimizer

Compile 

environment

System environment
GPU

Epoch
Batch size
Random seed

Ubuntu (22.04)
NVIDIA3090Ti (24 
G)
100
1
42

The first layer of 

IF=36, OF=64

GCN

Similarity image 

8

patches

Learning policy
Learning decay
Graph convolution 
layer
The second layer of 
GCN
Activation function

RHAM
CK of CAM and SAM
Convolution weight

4
1
mean=0, std=0.01

Block
CK of Block
Pooling layer

Stride

1

Padding

IF= input feature, OF=output feature, CK= convolution kernel.

5.3. Evaluation metrics

Setting

AdamW

Step
0.9
2

IF=64, 
OF=36
Relu

20
3
Global 
average
0

To  evaluate  the  reconstruction  effect,  we  use  the  Peak  Signal-to- 
Noise  Ratio  (PSNR),  Relative  l2  Norm  Error  (RLNE),  and  Structural 
Similarity Index Measure (SSIM) as evaluation criteria. High PSNR and 
SSIM values indicate better  reconstruction quality, while lower RLNE 
values mean smaller errors, thus reflecting the accuracy of the recon-
struction results and the quality of the image. 

(1) The PSNR is an indicator used to evaluate the quality of image 
reconstruction  or  compression.  It  quantifies  the  level  of  image 
distortion or noise by calculating the maximum possible signal and 
noise  between the ground-truth  images xtari
gt  and the  reconstructed 
target MR images xtari
: 

r

6 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

(
xtari
gt

PSNR

)

, xtari
r

= 10log10

)2

(cid:0)
Nmax
∑
N
i=1

‖ xtari
gt

xtari
gt
, xtari
r

,

‖2
2

(11) 

)

(
xtari
gt

where max
batch size. 

refers to the max value of the image pixel, and N is the 

(2)  The  RLNE  quantifies  the  weight  of  distortion  in  the  image 
restoration process by calculating the relative norm error between 
the ground-truth images and the reconstructed images: 

(

)

RLNE

xtari
gt

, xtari
r

=

‖ xtari
gt
‖ xtari

(cid:0) xtari
r
r ‖2

‖2

.

(12) 

(3)  The  SSIM  evaluates  the  structural  similarity  between  the  fully 
sampled image and the reconstructed image, more accurately mea-
sures the visual image quality, and highlights the weight of preser-
vation of image structural information: 

(
xtari
gt

, xtari
r

)

SSIM

(

)(

)

2μ

μ

tari
x
r

tari
gt

x

+ C1

)(

2σ

tari
tari
gt x
r

x

+ C2

=

(

μ2
x

tari
gt

+ μ2
tari
x
r

+ C1

σ2
x

tari
gt

+ σ2
tari
x
r

+ C2

),

(13) 

and μ

where μ
reconstructed  target  contrast  MR  images,  respectively.  Likewise,  σ2
x

represent the mean values of the fully sampled and 

tari
x
r 

tari
gt 

x

tari
gt 

and  σ2
x
structed target contract MR images, while σ

tari
r 

represent  the  local  variances  of  fully-sampled  and  recon-

tari
gt x

tari
r 

x

is the local covariance 

between  these  two  images.  C1  and  C2  are  constant  relaxation  terms, 
where C1  is set to 0.03 and C2  is set to 0.07.

6. Results

6.1. Experiment on different reconstruction methods

To  verify  the  performance  of  ACGRHA-Net,  we  compared  it  with 
several reconstruction models, including the T2-Net (Feng et al., 2021), 
which  combines  convolutional  neural  networks  with  a  transformer 
module; Wavtrans (Li et al., 2022), which integrates wavelet and cross 
attention  transformer;  Swin-GAN  (Zhao  et  al.,  2023),  a  dual-domain 
U-shaped Swin-Transformer combined with generative adversarial net-
works; SDAUT (Huang et al., 2022), which incorporates a deformation 
attention  mechanism;  and  DuDoRNet  (Zhou  and  Zhou,  2020),  a 
dual-domain  reconstruction  model  based  recurrent  networks.  Fig.  5
shows the comparison of loss curves when different methods are trained 
on the fastMRI (Zbontar et al., 2018) dataset using a 4 × Cartesian mask. 
During  training,  the  losses  of  all  methods  decrease  as  the  number  of 
epochs increases. Initially, SDAUT (Huang et al., 2022) has the largest 
loss value, while our method becomes lower than other methods after 
the 20th epoch and maintains the lowest loss throughout the training 
process.

Table  2 presents  the  quantitative  results  of  various  reconstruction 
methods using three sampling modes (Cartesian, Gaussian, and Radial) 
and  two  acceleration  factors  (4  × and  8  × )  on  the  fastMRI  and  IXI 
datasets. It is evident that when using the fastMRI dataset, all methods 
perform poorly with Cartesian sampling but show improved results with 
Gaussian and Radial sampling. Additionally, performance improves as 
the sampling rate increases. DuDoRNet (Zhou and Zhou, 2020) achieves 
the  second-best  reconstruction  quality  with  a  4  × Radial  mask.  In 
comparison, our method improves PSNR by 4.13 dB, SSIM by 0.007, and 
reduces RLNE by 0.013. Similarly, with the IXI dataset, our proposed 

7 

Fig.  5. The  training 
fastMRI dataset.

loss  of  different  reconstruction  models  on  the 

method improves PSNR by 1.822, SSIM by 0.027, and reduces RLNE by 
0.026 under 4 × acceleration factor compared to Swin-GAN (Zhao et al., 
2023),  which  employs  dual-domain  reconstruction.  In  summary,  the 
proposed method shows better performance than the compared methods 
across various sampling patterns, accelerated factors, and datasets. The 
ACG-Net integrates features through graph convolution, enhancing the 
fusion  and  interaction  between  auxiliary  and  target  contrast  images. 
Additionally, the residual hybrid attention mechanism of RHA-Net ex-
pands  the  receptive  field,  improves  feature  extraction,  effectively 
transmits shallow image information to deep layers, and promotes detail 
recovery.

Figs. 6 and 7 show the qualitative reconstruction results from various 
methods across three different sampling patterns (Cartesian, Gaussian, 
and  Radial)  at  both  8  × and  4  × accelerated  factors.  These  figures 
display a progression from the ground true (GT) images, zero-filled (ZF) 
images, target contrast MR images (TC MR images) reconstructed with 
different methods, enlarged detail images, and error maps. The PSNR 
and SSIM values of single reconstructed images for different methods are 
provided at the bottom. The lighter colors in the error maps indicate that 
the method is more effective in suppressing the error. The value range of 
the  error  map  is  [(cid:0) 0.4,  0.4].  The  results  show  that  among  the  three 
different  sampling  patterns,  the  Cartesian  mask  performs  poorly  in 
recovering brain details, while the Gaussian and Radial masks perform 
better. As the sampling rate increases, the reconstruction quality of all 
methods gradually improves, and the artifacts in the error map decrease. 
In  particular,  our  method  shows  better  reconstruction  results  when 
compared with other methods at a fixed sampling pattern and acceler-
ated  factor,  the  restored  details  are  closer  to  the  real  image  and 
outperform other methods in preserving texture details. For experiments 
with 8 × or 4 × accelerated factors, the image outline can be effectively 
restored.  This  proves  that  our  method  can  effectively  improve  the 
reconstruction quality of MR images, especially in the recovery of details 
and  contours,  while  significantly  reducing  artifacts  during  the  image 
reconstruction process.

Fig.  8 presents  the  qualitative  reconstruction  results  of  various 
methods using a 4  × Cartesian sampling pattern in the IXI dataset. It 
can be observed that the proposed method improves the PSNR by 1.55 
dB,  increases  the  SSIM  by  0.022,  and  decreases  the  RLNE  by  0.021 
compared  to  the  suboptimal  DuDoRNet  (Zhou  and  Zhou,  2020). 
Experimental results on both the fastMRI and IXI datasets demonstrate 
that the proposed method delivers superior performance, further vali-
dating its robustness and stability.

Fig.  9 shows  the  calculated  p-values  for  PSNR,  SSIM,  and  RLNE, 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

Table 2 
Quantitative  comparison  of  different  reconstruction  methods  on  two  MRI 
datasets (fastMRI, IXI), with two acceleration factors (i.e., 4  × , 8  × ) and three 
sampling masks (i.e., 1D Cartesian, 2D Gaussian, and Radial).

Table 2 (continued )

Accelerated Factors

Methods 

8  ×

4  ×

Accelerated Factors

Methods

8  ×

4  ×

PSNR↑

RLNE↓

SSIM↑

PSNR↑

RLNE↓

SSIM↑

fastMRI 1D Cartesian (Mean (Standard))

20.438 
(0.951)
28.848 
(1.033)

0.360 
(0.033)
0.137 
(0.013)

0.594 
(0.038)
0.864 
(0.033)

22.357 
(1.052)
30.363 
(1.087)

0.289 
(0.031)
0.115 
(0.011)

0.669 
(0.038)
0.873 
(0.027)

33.358 
(1.008)

0.082 
(0.009)

0.930 
(0.029)

35.414 
(1.018)

0.064 
(0.007)

0.940 
(0.023)

30.969 
(1.269)

0.108 
(0.016)

0.899 
(0.039)

34.143 
(1.230)

0.075 
(0.011)

0.932 
(0.027)

33.165 
(1.055)

0.083 
(0.010)

0.925 
(0.031)

35.656 
(1.058)

0.063 
(0.007)

0.942 
(0.023)

33.106 
(1.108)

0.084 
(0.101)

0.930 
(0.029)

36.849 
(1.217)

0.055 
(0.008)

0.956 
(0.019)

37.908 
(1.092)

0.049 
(0.006)

0.963 
(0.017)

41.492 
(1.259)

0.032 
(0.005)

0.975 
(0.012)

fastMRI 2D Gaussian (Mean (Standard))

23.589 
(0.995)
30.041 
(1.181)

0.251 
(0.023)
0.120 
(0.013)

0.601 
(0.034)
0.834 
(0.030)

25.058 
(1.025)
31.440 
(1.218)

0.212 
(0.020)
0.102 
(0.012)

0.644 
(0.030)
0.851 
(0.027)

Swin-GAN (
Zhao et al., 
2023)
SDAUT (
Huang 
et al., 2022)
DuDoRNet (
Zhou and 
Zhou, 2020)
Ours

PSNR↑ 

RLNE↓ 

SSIM↑ 

PSNR↑ 

RLNE↓ 

SSIM↑

27.267 
(1.272)

0.217 
(0.028)

0.761 
(0.035)

30.905 
(1.082)

0.142 
(0.016)

0.861 
(0.019)

26.497 
(1.053)

0.236 
(0.025)

0.758 
(0.044)

29.911 
(1.047)

0.159 
(0.017)

0.822 
(0.027)

28.087 
(1.322)

0.197 
(0.028)

0.807 
(0.043)

31.647 
(1.265)

0.131 
(0.018)

0.861 
(0.027)

28.912 
(1.267)

0.175 
(0.023)

0.838 
(0.033)

32.727 
(1.295)

0.116 
(0.015)

0.888 
(0.021)

P-value<0.05 was considered as a statistically significant level. The best results 
are labeled in bold.

comparing  the  proposed  method  with  other  methods  across  various 
sampling rates, patterns, and datasets, based on the data in Table 2. As 
shown,  all  p-values  are  below  0.05,  indicating  statistical  significance 
and further validating the superiority of the proposed method.

Fig. 10 visually displays the PSNR and SSIM comparison of various 
methods with fastMRI dataset using a 4 × Radial mask in the form of box 
plots. The results show that the method proposed in this study surpasses 
other compared methods in both PSNR and SSIM indicators, reflecting 
its superior reconstruction performance.

34.296 
(1.036)

0.073 
(0.008)

0.929 
(0.028)

35.965 
(0.984)

0.060 
(0.007)

0.936 
(0.025)

6.2. Ablation experiment

34.303 
(1.220)

0.073 
(0.010)

0.926 
(0.029)

37.395 
(1.315)

0.051 
(0.008)

0.950 
(0.021)

34.905 
(1.097)

0.068 
(0.008)

0.935 
(0.027)

36.976 
(1.094)

0.054 
(0.007)

0.945 
(0.022)

36.328 
(1.265)

0.058 
(0.008)

0.952 
(0.020)

39.848 
(1.364)

0.039 
(0.006)

0.968 
(0.014)

39.781 
(1.281)

0.039 
(0.006)

0.967 
(0.015)

43.275 
(1.287)

0.026 
(0.004)

0.978 
(0.011)

fastMRI 2D Radial (Mean (Standard))

22.865 
(0.898)
30.000 
(1.167)

0.272 
(0.021)
0.120 
(0.013)

0.557 
(0.034)
0.830 
(0.031)

26.319 
(0.978)
32.347 
(1.325)

0.183 
(0.015)
0.092 
(0.116)

0.692 
(0.037)
0.867 
(0.029)

34.016 
(0.974)

0.076 
(0.008)

0.925 
(0.028)

36.582 
(1.031)

0.056 
(0.006)

0.944 
(0.021)

34.154 
(1.154)

0.075 
(0.009)

0.930 
(0.025)

38.659 
(1.393)

0.045 
(0.007)

0.965 
(0.016)

34.876 
(1.023)

0.069 
(0.008)

0.936 
(0.025)

38.384 
(1.121)

0.046 
(0.006)

0.958 
(0.017)

35.837 
(1.180)

0.061 
(0.008)

0.950 
(0.020)

40.323 
(1.436)

0.037 
(0.006)

0.973 
(0.013)

39.576 
(1.212)

0.040 
(0.006)

43.978 
(1.261)
IXI 1D Cartesian (Mean (Standard))

0.965 
(0.016)

0.024 
(0.004)

0.980 
(0.010)

21.240 
(0.664)
26.839 
(0.956)

0.430 
(0.018)
0.227 
(0.021)

0.456 
(0.036)
0.731 
(0.034)

23.051 
(0.699)
29.009 
(0.840)

0.350 
(0.020)
0.176 
(0.013)

0.540 
(0.031)
0.759 
(0.024)

28.141 
(1.250)

0.200 
(0.026)

0.812 
(0.040)

31.031 
(1.283)

0.141 
(0.019)

0.841 
(0.032)

To validate the effectiveness of each component of ACGRHA-Net (i.e. 
w/o Residual learning, ACG-Net, RHA-Net, RHAM, and AAM), a series of 
ablation experiments were conducted using a 10 × Cartesian mask on 
the fastMRI (Zbontar et al., 2018) dataset. The quantitative results are 
shown in Table 3. These experiments evaluate the individual contribu-
tion of RHA-Net and ACG-Net, where RHA-Net was replaced by a 6-layer 
CNN when ACG-Net was tested alone. The w/o AAM refers to obtaining 
the adjacency matrix by pre-reconstructing the target contrast MR image 
using the 6-layer CNN instead of deriving it from the auxiliary contrast 
MR image. While this alternative method helps restore image edges, it 
proves  less  effective  and  less  practical  compared  to  ACGRHA-Net’s 
approach.  Moreover,  the  pre-reconstruction process  adds  unnecessary 
complexity. Further experiments examined the role of residual learning 
and the residual hybrid attention modules (RHAM) within RHA-Net. The 
results showed that both components are essential for improving PSNR 
and SSIM indicators. Specifically, adding RHAM improves the PSNR by 
4.225  dB,  and  the  SSIM  by  0.03,  highlighting  its  critical  role  in 
enhancing  the  reconstruction  quality.  Furthermore,  the  experiments 
highlight the complementary synergy between ACG-Net and RHA-Net. 
ACG-Net  effectively  facilitates  feature  interaction  between  the  auxil-
iary and target contrast MR images through graph convolution, which 
enhances  the  fusion  of  similar  patches.  RHA-Net  then  utilizes  this 
enriched  feature  information  to  accurately  reconstruct  the  target 
contrast  MR  images.  This  process  ensures  that  shallow  features  are 
preserved and progressively transferred to deeper layers. By integrating 
multi-level features and adaptively learning the weights across different 
feature  layers,  RHA-Net  continually  achieves  superior  reconstruction 
outcomes for the target contrast MR images.

The  effect  of  the  number  of  residual  hybrid  attention  modules  on 
RHA-Net reconstruction performance was verified through experiments 
on  the  fastMRI  (Zbontar  et  al.,  2018)  dataset.  The  quantitative  and 
qualitative  results  are  shown  in  Table  4 and  Fig.  11.  Increasing  the 
number of RHAMs significantly improves the reconstruction quality of 
the target contrast image. Notably, when increasing from 1 to 2 RHAMs, 
the PSNR, RLNE, and SSIM indicators improved considerably. As shown 

8 

ZF

T2-Net (
Feng et al., 
2021)
Wavtrans (
Li et al., 
2024)
Swin-GAN (
Zhou et al., 
2023)
SDAUT (
Huang 
et al., 2022)
DuDoRNet (
Zhou and 
Zhou, 2020)
Ours

ZF

T2-Net (
Feng et al., 
2021)
Wavtrans (
Li et al., 
2024)
Swin-GAN (
Zhou et al., 
2023)
SDAUT (
Huang 
et al., 2022)
DuDoRNet (
Zhou and 
Zhou, 2020)
Ours

ZF

T2-Net (
Feng et al., 
2021)
Wavtrans (
Li et al., 
2024)
Swin-GAN (
Zhou et al., 
2023)
SDAUT (
Huang 
et al., 2022)
DuDoRNet (
Zhou and 
Zhou, 2020)
Ours

ZF

T2-Net (
Feng et al., 
2022)
Wavtrans (
Li et al., 
2024)

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

Fig. 6. Qualitative comparison with different reconstruction methods using three different 8 × masks (Cartesian, Gaussian, Radial) on the fastMRI dataset. Ground 
truth, zero-filled, reconstructed target contrast MR images, error maps, and zoomed-in details are provided with corresponding evaluation metrics in PSNR/SSIM 
× 100.

in the corresponding enlarged images and error maps in Fig. 11, details 
are  better  restored  with  a  larger  number  of  residual  hybrid  attention 
modules. Further increasing to 4 RHAMs continues to enhance perfor-
mance,  though  the  improvement  is  relatively  small  when  increasing 
from  4  to  5.  Fig.  12 demonstrates  that  as  the  number  of  RHAMs  in-
creases, the reconstruction quality significantly improves, thus verifying 
the  effectiveness  of  adding  these  components.  Based  on  the  above 
analysis, our experiments show that using 5 RHAMs outperforms using 4 
RHAMs, but the marginal gain in performance is not high. Additionally, 
increasing the number of RHAMs increases the parameters and depth of 
the network, which leads to increased complexity. To strike a balance 
between  performance  and  network  complexity,  the  proposed  method 
uses 4 RHAMs.

7. Discussions and limitations

In previous studies, most methods simply directly input MR images 
with different contrasts into the network or concatenate them, which 
limits  the  potential  for  improvement  in  the  reconstruction  quality  of 
multi-contrast  MR  images.  In  this  study,  we  propose  a  novel  multi- 
contrast MR  image  fusion  method. Given  the  structural similarity  be-
tween multi-contrast MR images, the adjacency matrix derived from the 
fully sampled auxiliary contrast MR image can be effectively utilized to 
assist  the  edge  reconstruction  for  the  zero-filled  target  contrast  MR 
image.  By  leveraging  GCN,  the  complementary  adjacency  between 
similar image patches in the auxiliary contrast MR image and the target 
contrast MR image can be effectively learned. This facilitates the fusion 
of multi-contrast image features and enhances the quality of the target 
image reconstruction.

Fig. 13(a) and (b) show the process of constructing the source image 

9 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

Fig. 7. Qualitative comparison with different reconstruction methods using three different 4 × masks (Cartesian, Gaussian, Radial) on the fastMRI dataset. Ground 
truth, zero-filled, reconstructed target contrast MR images, error maps, and zoomed-in details are provided with corresponding evaluation metrics in PSNR/SSIM 
× 100.

patch and other most similar image patches in the target contrast MR 
image  using the  adjacency relationship of  the fully sampled  auxiliary 
contrast  MR  image  and  the  zero-filled  target  contrast  MR  image, 
respectively.  By  comparing  the  similarity  between  the  similar  image 
patches and the source image patch in (a) and (b), it can be seen that the 
similar image patches in (a) are more similar to the source image patch. 
Therefore, compared with using the zero-filled target MR image, con-
structing ACG using the fully sampled auxiliary contrast MR image is 
more likely to identify image patches that are more similar to the source 
image patches. This method can not only more effectively restore the 
details  of  the  target  contrast  MR  image,  but  also  better  explore  the 

complementarity between MR images of different contrasts.

As shown in Fig. 14, we use a 10 × Cartesian mask on the fastMRI 
dataset  to  compare  the  effects  of  w/o  the  auxiliary  adjacency  matrix 
(AAM)  and  w/o  ACG-Net  learning  the  complementarity  between  MR 
images  of  different  contrasts  on  the  reconstruction  results.  From  the 
reconstructed details and error maps, it can be seen that using ACG-Net 
and  AAM  can  better  restore  details  and  contour  information,  which 
proves  the  effectiveness  of  our  proposed  method  in  fusing  different 
contrast MR images. To verify the effectiveness of using the adjacency 
matrix of the auxiliary contrast MR image to find similar image patches 
of the target contrast MR image to learn the complementary between 

10 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

Fig. 8. Qualitative comparison with different reconstruction methods using a 4 × Cartesian mask on the IXI dataset. Ground truth, zero-filled, reconstructed target 
contrast MR images, error maps, and zoomed-in details are provided with corresponding evaluation metrics in PSNR/SSIM  × 100/RLNE  × 100.

Fig. 9. Scatter plot showing the p-values comparison of the proposed method and other methods in terms of PSNR, SSIM, and RLNE. (p-value<0.05 was considered 
as a statistically significant level.)

Fig. 10. Boxplot of the distribution of PSNR and SSIM from different reconstruction methods using a 4 × Radial mask on the fastMRI dataset.

11 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

Table 3 
Ablation study on different variant models using a 10 × Cartesian sampling mask 
on the fastMRI dataset.

image quality, and make the network more adaptable to diverse clinical 
settings.

Methods

PSNR↑

RLNE↓

SSIM↑

8. Conclusion

fastMRI 1D Cartesian 10 × (Mean (Standard))
ZF
w/o Residual learning
w/o RHA-Net
w/o RHAM
w/o ACG-Net
w/o AAM
Ours

20.106(0.927)
20.443(0.951)
29.808(0.937)
33.570(0.899)
35.428(0.995)
36.515(1.084)
37.795(1.116)

0.374(0.034)
0.360(0.033)
0.122(0.012)
0.079(0.007)
0.064(0.007)
0.057(0.007)
0.049(0.006)

0.569(0.037)
0.593(0.038)
0.878(0.035)
0.930(0.025)
0.947(0.026)
0.953(0.020)
0.960(0.017)

The best results are labeled in bold.

Table 4 
Quantitative  comparison  of  the  number  of  RHAMs  in  RHA-Net  using  an  8  ×
Cartesian mask on the fastMRI dataset.

Methods

PSNR↑

RLNE↓

SSIM↑

fastMRI 1D Cartesian 8 × (Mean (Standard))
ZF
RHAM-1
RHAM-2
RHAM-3
Ours
RHAM-5

20.438(0.951)
34.145(0.919)
36.070(1.007)
37.105(1.057)
37.361(1.064)
37.581(1.100)

0.360(0.033)
0.074(0.007)
0.060(0.006)
0.053(0.006)
0.051(0.006)
0.050(0.006)

0.594(0.038)
0.938(0.023)
0.951(0.020)
0.959(0.018)
0.961(0.017)
0.962(0.017)

multi-contrast  MR  images,  we  also  compared  the  use  of  CNN  to  pre- 
reconstruct  the  target  contrast  MR 
images  and  use  the  pre- 
reconstructed adjacency  matrix of the  target contrast MR  images and 
its node images into the GCN. As shown in Table 3, compared with w/o 
AAM, the PSNR of the proposed method is improved by 1.435 dB, and 
the SSIM is improved by 0.007. This not only proves the effectiveness of 
the method but also shows that the structural similarity between multi- 
contrast MR images can be exploited to learn their adjacency comple-
mentary graph, thereby better integrating their structural features and 
producing better reconstruction results.

The current method employs a fixed approach for learning structural 
similarity  and  graph  filters,  which  cannot  be  dynamically  adjusted 
during network training. A potential direction of future work is to train 
the convolution kernel parameters in graph convolutional neural net-
works  with  a  dynamically  updated  graph  representation  of  optimal 
structural similarity during training, thereby enhancing feature repre-
sentation ability. Moreover, incorporating multi-coil data in the recon-
struction process could further enhance the model’s flexibility, improve 

This study proposes a new multi-contrast MR image reconstruction 
network called ACGRHA-Net which leverages the structural similarity of 
multi-contrast images through learned graph filtering to assist in multi- 
contrast MR image reconstruction using a deep-level hybrid attention 
reconstruction network. The framework not only promotes the fusion 
and  interaction  of  shared  feature  information  among  MR  images  of 
different contrasts but also effectively extracts key features and relocates 
image  features through a  residual hybrid attention mechanism.  Addi-
tionally, the network can skip information in regions with lighter arti-
facts and low frequencies via local residual connections, thus enabling 
the transfer and fusion of features across different levels. Experimental 
results  demonstrate the advantages  of ACGRHA-Net  in improving  the 
quality and robustness of multi-contrast MR image reconstruction even 
at relatively low sampling rates.

Data and code availability

• fastMRI dataset: This dataset is provided by New York University, 
includes brain MRI data, and is publicly available at https://fastmri. 
med.nyu.edu/. For this study, we selected 768 pairs of T1-weighted 
imaging  (T1WI)  and  T2-weighted  imaging  (T2WI)  brain  slices  for 
training, and 96 pairs for validation.

• IXI  dataset:  This  dataset  is  provided  by  the  Brain  Development 
Project, and consists of single-coil brain MRI data, publicly available 
at https://brain-development.org/ixi-dataset. We screened 600 pairs 
of  T1WI  and  T2WI  brain  slices  for  training,  and  75  pairs  for 
validation.

Ethics statement

This study was approved by the Ethics Committee of Jimei University 
(ethical approval number JMU202411086). All procedures in this study 
were  performed  in  compliance  with  relevant  laws  and  institutional 
guidelines.

CRediT authorship contribution statement

Haotian Zhang: Writing – review & editing, Writing – original draft, 
Methodology.  Qiaoyu  Ma:  Writing  –  review  &  editing.  Yiran  Qiu: 

Fig. 11. Qualitative comparison of the reconstruction results of target contrast MR images with different numbers of RHAMs using an 8 × Cartesian mask on the 
fastMRI dataset. Ground truth (GT), zero-filled (ZF), reconstructed target contrast MR images (TC MR image), error maps, and zoomed-in details are provided with 
corresponding evaluation metrics in PSNR/SSIM × 100.

12 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

Fig. 12. Boxplot of the distribution of PSNR and SSIM from different numbers of RHAMs using an 8 × Cartesian mask on the fastMRI dataset.

Fig. 13. An example of finding the eight most similar patches for a target patch (red box marked). Adjacency relations learned from fully sampled auxiliary contrast 
MR images are more consistent with the target MR image. (a) Patch adjacency relations built in the target contrast image using adjacency relations learned from the 
fully sampled auxiliary contrast MR image; (b) Patch adjacency relations built in the target contrast image using adjacency relations learned from zero-filled target 
contrast MR image; (c) Eight most similar patches are marked with different colors, with similarity decreasing from left to right.

Fig. 14. Qualitative comparison w/o AAM and ACG-Net using a 10 × Cartesian mask on the fastMRI dataset. Ground truth, zero-filled, reconstructed target MR 
images, error maps, and zoomed-in details are provided with corresponding evaluation metrics in PSNR/SSIM × 100.

13 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

Writing – review & editing. Zongying Lai: Writing – review & editing, 
Methodology, Funding acquisition.

Declaration of competing interest

The authors declare that they have no known competing financial 
interests or personal relationships that could have appeared to influence 
the work reported in this paper.

Acknowledgments

This  work  was  supported  in  part  by  the  National  Natural  Science 
Foundation  of  China  under  Grant  61901188,  the  Natural  Science 
Foundation of Fujian Province of China under Grant 2022J05163, and 
the Science and Technology Fund of Fujian Education Department under 
Grant JT180280.

References

Aggarwal, H.K., Mani, M.P., Jacob, M., 2018. MoDL: model-based deep learning 
architecture for inverse problems. IEEe Trans. Med. ImAging 38, 394–405.

Aghabiglou, A., Eksioglu, E.M., 2021. Projection-Based cascaded U-Net model for MR 

image reconstruction. Comput. Methods Programs Biomed. 207, 106151.

Atli, O.F., Kabas, B., Arslan, F., Yurt, M., Dalmaz, O., Çukur, T., 2024. I2I-Mamba: multi- 
modal medical image synthesis via selective state space modeling. arXiv preprint 
arXiv:2405.14022. 

Bilgic, B., Goyal, V.K., Adalsteinsson, E., 2011. Multi-contrast reconstruction with 

Bayesian compressed sensing. Magn. Reson. Med. 66, 1601–1615.

Bustin, A., Lima da Cruz, G., Jaubert, O., Lopez, K., Botnar, R.M., Prieto, C., 2019. High- 

dimensionality undersampled patch-based reconstruction (HD-PROST) for 
accelerated multi-contrast MRI. Magn. Reson. Med. 81, 3705–3719.
Bustin, A., Voilliot, D., Menini, A., Felblinger, J., de Chillou, C., Burschka, D., 

Bonnemains, L., Odille, F., 2018. Isotropic reconstruction of MR images using 3D 
patch-based self-similarity learning. IEEe Trans. Med. ImAging 37, 1932–1942.

Dalmaz, O., Yurt, M., Çukur, T., 2022. ResViT: residual vision transformers for 

multimodal medical image synthesis. IEEe Trans. Med. ImAging 41, 2598–2614.
Dar, S.U., Yurt, M., Shahdloo, M., Ildız, M.E., Tınaz, B., Çukur, T., 2020. Prior-guided 
image reconstruction for accelerated multi-contrast MRI via generative adversarial 
networks. IEEe J. Sel. Top. Signal. Process. 14, 1072–1087.

Dhengre, N., Sinha, S., 2022. Multiscale U-net-based accelerated magnetic resonance 

imaging reconstruction. Signal. Image Video Process. 16, 881–888.

Ehrhardt, M.J., Betcke, M.M., 2016. Multicontrast MRI reconstruction with structure- 

guided total variation. SIAM. J. ImAging Sci. 9, 1084–1106.

Esfahani, E.E., 2022. Isotropic multichannel total variation framework for joint 

reconstruction of multicontrast parallel MRI. J. Med. Imaging 9, 013502. -013502. 

Falvo, A., Comminiello, D., Scardapane, S., Scarpiniti, M., Uncini, A., 2019. 

A multimodal dense u-net for accelerating multiple sclerosis mri. In: 2019 IEEE 29th 
International Workshop on Machine Learning for Signal Processing (MLSP). IEEE, 
pp. 1–6.

Feng, C.-M., Yan, Y., Chen, G., Xu, Y., Hu, Y., Shao, L., Fu, H., 2022. Multimodal 

transformer for accelerated MR imaging. IEEe Trans. Med. ImAging 42, 2804–2816.
Feng, C.-M., Yan, Y., Fu, H., Chen, L., Xu, Y., 2021. Task transformer network for joint 

MRI reconstruction and super-resolution. In: Medical Image Computing and 
Computer Assisted Intervention–MICCAI 2021: 24th International Conference, 
Strasbourg, France, September 27–October 1, 2021, Proceedings, Part VI 24. 
Springer, pp. 307–317.

Feng, C.-M., Yan, Y., Yu, K., Xu, Y., Fu, H., Yang, J., Shao, L., 2024. Exploring separable 

attention for multi-contrast MR image super-resolution. IEEe Trans. Neural Netw. 
Learn. Syst.
Güng¨or, A., Dar, S.U., 

¨
Oztürk, S¸ ., Korkmaz, Y., Bedel, H.A., Elmas, G., Ozbey, M., 

Çukur, T., 2023. Adaptive diffusion priors for accelerated MRI reconstruction. Med. 
Image Anal. 88, 102872.

Gungor, A., Kopanoglu, E., Cukur, T., Guven, E., Yarman-Vural, F.T., 2017. Joint 

dictionary learning reconstruction of compressed multi-contrast magnetic resonance 
imaging. In: 2017 21st National Biomedical Engineering Meeting (BIYOMUT). IEEE, 
pp. i–iv.

Hammernik, K., Klatzer, T., Kobler, E., Recht, M.P., Sodickson, D.K., Pock, T., Knoll, F., 
2018. Learning a variational network for reconstruction of accelerated MRI data. 
Magn. Reson. Med. 79, 3055–3071.

Hammond, D.K., Vandergheynst, P., Gribonval, R., 2011. Wavelets on graphs via spectral 

graph theory. Appl. Comput. Harmon. Anal. 30, 129–150.

Huang, J., Xing, X., Gao, Z., Yang, G., 2022. Swin deformable attention u-net transformer 
(sdaut) for explainable fast mri. In: International Conference on Medical Image 
Computing and Computer-Assisted Intervention. Springer, pp. 538–548.

Jin, K.H., McCann, M.T., Froustey, E., Unser, M., 2017. Deep convolutional neural 

network for inverse problems in imaging. IEEE Transact. Image Process.. 26, 
4509–4522.

Kim, K.H., Do, W.J., Park, S.H., 2018. Improving resolution of MR images with an 

adversarial network incorporating images with different contrast. Med. Phys. 45, 
3120–3131.

Kipf, T.N., Welling, M., 2016. Semi-supervised classification with graph convolutional 

networks. arXiv preprint arXiv:1609.02907. 

Korkmaz, Y., Cukur, T., Patel, V.M., 2023. Self-supervised MRI reconstruction with 
unrolled diffusion models. In: International Conference on Medical Image 
Computing and Computer-Assisted Intervention. Springer, pp. 491–501.

Korkmaz, Y., Dar, S.U., Yurt, M., 

¨
Ozbey, M., Cukur, T., 2022. Unsupervised MRI 

reconstruction via zero-shot learned adversarial transformers. IEEe Trans. Med. 
ImAging 41, 1747–1763.

Lai, Z., Zhang, X., Guo, D., Du, X., Yang, Y., Guo, G., Chen, Z., Qu, X., 2018. Joint sparse 

reconstruction of multi-contrast MRI images with graph based redundant wavelet 
transform. BMC. Med. ImAging 18, 1–16.

Li, B., Hu, W., Feng, C.-M., Li, Y., Liu, Z., Xu, Y., 2024. Multi-contrast complementary 
learning for accelerated MR Imaging. IEEE J. Biomed. Health Inf. 28, 1436–1447.
Li, G., Lv, J., Tian, Y., Dou, Q., Wang, C., Xu, C., Qin, J., 2022a. Transformer-empowered 
multi-scale contextual matching and aggregation for multi-contrast MRI super- 
resolution. In: Proceedings of the IEEE/CVF conference on computer vision and 
pattern recognition, pp. 20636–20645.

Li, G., Lyu, J., Wang, C., Dou, Q., Qin, J., 2022b. Wavtrans: synergizing wavelet and 

cross-attention transformer for multi-contrast mri super-resolution. In: International 
Conference on Medical Image Computing and Computer-Assisted Intervention. 
Springer, pp. 463–473.

Lin, A., Chen, B., Xu, J., Zhang, Z., Lu, G., Zhang, D., 2022. Ds-transunet: dual swin 

transformer u-net for medical image segmentation. IEEE Transact. Instrument. 71, 
1–15.

Liu, X., Wang, J., Lin, S., Crozier, S., Liu, F., 2021. Optimizing multicontrast MRI 

reconstruction with shareable feature aggregation and selection. NMR Biomed. 34, 
e4540.

Luo, Y., Wang, Y., Zu, C., Zhan, B., Wu, X., Zhou, J., Shen, D., Zhou, L., 2021. 3D 

transformer-GAN for high-quality PET reconstruction. In: Medical Image Computing 
and Computer Assisted Intervention–MICCAI 2021: 24th International Conference, 
Strasbourg, France, September 27–October 1, 2021, Proceedings, Part VI 24. 
Springer, pp. 276–285.

Luo, Y., Wei, M., Li, S., Ling, J., Xie, G., Yao, S., 2023. An effective co-support guided 
analysis model for multi-contrast MRI reconstruction. IEEE J. Biomed. Health Inf. 27, 
2477–2488.

Lustig, M., Donoho, D., Pauly, J.M., Sparse, M.R.I., 2007. The application of compressed 

sensing for rapid MR imaging. Magnet. Resonance Med. 58, 1182–1195.

Lyu, J., Sui, B., Wang, C., Tian, Y., Dou, Q., Qin, J., 2022. Dudocaf: dual-domain cross- 

attention fusion with recurrent transformer for fast multi-contrast mr imaging. In: 
International Conference on Medical Image Computing and Computer-Assisted 
Intervention. Springer, pp. 474–484.

Lyu, Q., Shan, H., Steber, C., Helis, C., Whitlow, C., Chan, M., Wang, G., 2020. Multi- 
contrast super-resolution MRI through a progressive network. IEEe Trans. Med. 
ImAging 39, 2738–2749.

Ma, Q., Lai, Z., Wang, Z., Qiu, Y., Zhang, H., Qu, X., 2024. MRI reconstruction with 

enhanced self-similarity using graph convolutional network. BMC. Med. ImAging 24, 
113.

Mardani, M., Gong, E., Cheng, J.Y., Vasanawala, S.S., Zaharchuk, G., Xing, L., Pauly, J. 
M., 2018. Deep generative adversarial neural networks for compressive sensing MRI. 
IEEe Trans. Med. ImAging 38, 167–179.

Osher, S., Shi, Z., Zhu, W., 2017. Low dimensional manifold model for image processing. 

SIAM. J. ImAging Sci. 10, 1669–1690.

Peng, C., Lin, W.-A., Chellappa, R., Zhou, S.K., 2020. Towards multi-sequence MR image 
recovery from undersampled k-space data. Medical Imaging with Deep Learning. 
PMLR, pp. 614–623.

Pingfan, S., Weizman, L., MOTA, J., 2018. Coupled dictionary learning for multi-contrast 

MRI reconstruction. In: The 25th IEEE International Conference on Image 
Processing. Athens, Greece, pp. 2880–2884.

Ronneberger, O., Fischer, P., Brox, T., 2015. U-net: convolutional networks for 

biomedical image segmentation. In: Medical image computing and computer- 
assisted intervention–MICCAI 2015: 18th international conference, Munich, 
Germany, October 5-9, 2015, proceedings, part III 18. Springer, pp. 234–241.
Schlemper, J., Caballero, J., Hajnal, J.V., Price, A., Rueckert, D., 2017. A deep cascade of 

convolutional neural networks for MR image reconstruction. In: Information 
Processing in Medical Imaging: 25th International Conference, IPMI 2017, Boone, 
NC, USA, June 25-30, 2017, Proceedings 25. Springer, pp. 647–658.

Sun, L., Fan, Z., Fu, X., Huang, Y., Ding, X., Paisley, J., 2019. A deep information sharing 
network for multi-contrast compressed sensing MRI reconstruction. IEEE Transact. 
Image Process. 28, 6141–6153.

Wang, J., Yang, Y., Yang, H., Lian, C., Xu, Z., Sun, J., 2023. MD-GraphFormer: a model- 
driven graph transformer for fast multi-contrast MR imaging. IEEe Trans. Comput. 
Imag. 9, 1018–1030.

Wang, S., Su, Z., Ying, L., Peng, X., Zhu, S., Liang, F., Feng, D., Liang, D., 2016. 

Accelerating magnetic resonance imaging via deep learning. In: 2016 IEEE 13th 
international symposium on biomedical imaging (ISBI). IEEE, pp. 514–517.

Wei, H., Li, Z., Wang, S., Li, R., 2022. Undersampled multi-contrast MRI reconstruction 
based on double-domain generative adversarial network. IEEe J. Biomed. Health 
Inform. 26, 4371–4377.

Xiang, L., Chen, Y., Chang, W., Zhan, Y., Lin, W., Wang, Q., Shen, D., 2018. Deep- 

learning-based multi-modal fusion for fast MR reconstruction. IEEE Transact. 
Biomed. Eng. 66, 2105–2114.

Yaman, B., Weing¨artner, S., Kargas, N., Sidiropoulos, N.D., Akçakaya, M., 2019. Low- 
rank tensor models for improved multidimensional MRI: application to dynamic 
cardiac T1 mapping. IEEe Trans. Comput. Imaging 6, 194–207.

Yang, J., Li`o, P., 2023. Dual-Domain Multi-Contrast MRI Reconstruction with Synthesis- 

based Fusion Network. arXiv preprint arXiv:2312.00661. 

14 

H. Zhang et al.                                                                                                                                                                                                                                  

NeuroImage 303 (2024) 120921 

Yang, Y., Sun, J., Li, H., Xu, Z., 2018. ADMM-CSNet: a deep learning approach for image 

compressive sensing. IEEe Trans. Pattern. Anal. Mach. Intell. 42, 521–538.

Yi, Z., Liu, Y., Zhao, Y., Xiao, L., Leong, A.T., Feng, Y., Chen, F., Wu, E.X., 2021. Joint 
calibrationless reconstruction of highly undersampled multicontrast MR datasets 
using a low-rank Hankel tensor completion framework. Magn. Reson. Med. 85, 
3256–3271.

Zbontar, J., Knoll, F., Sriram, A., Murrell, T., Huang, Z., Muckley, M.J., Defazio, A., 

Stern, R., Johnson, P., Bruno, M., 2018. fastMRI: an open dataset and benchmarks for 
accelerated MRI. arXiv preprint arXiv:1811.08839. 

Zeng, K., Zheng, H., Cai, C., Yang, Y., Zhang, K., Chen, Z., 2018. Simultaneous single-and 
multi-contrast super-resolution for brain MRI images based on a convolutional 
neural network. Comput. Biol. Med. 99, 133–141.

Zeng, W., Peng, J., Wang, S., Liu, Q., 2020. A comparative study of CNN-based super- 

Zhang, X., He, X., Guo, J., Ettehadi, N., Aw, N., Semanek, D., Posner, J., Laine, A., 
Wang, Y., 2021. PTNet: a high-resolution infant MRI synthesizer based on 
transformer. arXiv preprint arXiv:2105.13993. 

Zhao, X., Yang, T., Li, B., Zhang, X., 2023. SwinGAN: a dual-domain Swin Transformer- 

based generative adversarial network for MRI reconstruction. Comput. Biol. Med. 
153, 106513.

Zhou, B., Dey, N., Schlemper, J., Salehi, S.S.M., Liu, C., Duncan, J.S., Sofka, M., 2023. 
DSFormer: a dual-domain self-supervised transformer for accelerated multi-contrast 
MRI reconstruction. In: Proceedings of the IEEE/CVF winter conference on 
applications of computer vision, pp. 4966–4975.

Zhou, B., Zhou, S.K., 2020. DuDoRNet: learning a dual-domain recurrent network for fast 
MRI reconstruction with deep T1 prior. In: Proceedings of the IEEE/CVF conference 
on computer vision and pattern recognition, pp. 4273–4282.

resolution methods in MRI reconstruction and its beyond. Signal Process. Image 
Commun. 81, 115701.

Zhou, T., Fu, H., Chen, G., Shen, J., Shao, L., 2020. Hi-net: hybrid-fusion network for 
multi-modal MR image synthesis. IEEe Trans. Med. ImAging 39, 2772–2781.

15 

