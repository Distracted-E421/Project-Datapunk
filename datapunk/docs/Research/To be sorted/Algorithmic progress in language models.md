ALGORITHMIC PROGRESS IN LANGUAGE MODELS

Anson Ho1†

Tamay Besiroglu1,2†

Ege Erdil1

David Owen1

Robi Rahman1

Zifan Carl Guo2

David Atkinson1,3

Neil Thompson2

Jaime Sevilla1

ABSTRACT

We investigate the rate at which algorithms for pre-training language models have improved since the
advent of deep learning. Using a dataset of over 200 language model evaluations on Wikitext and
Penn Treebank spanning 2012-2023, we find that the compute required to reach a set performance
threshold has halved approximately every 8 months, with a 95% confidence interval of around 5 to 14
months, substantially faster than hardware gains per Moore’s Law. We estimate augmented scaling
laws, which enable us to quantify algorithmic progress and determine the relative contributions of
scaling models versus innovations in training algorithms. Despite the rapid pace of algorithmic
progress and the development of new architectures such as the transformer, our analysis reveals that
the increase in compute made an even larger contribution to overall performance improvements over
this time period. Though limited by noisy benchmark data, our analysis quantifies the rapid progress
in language modeling, shedding light on the relative contributions from compute and algorithms.

1 Introduction

The field of language modeling has seen rapid advances, with recent large language models (LLMs) demonstrating
strong performance in domains such as programming (Y. Li et al. 2022; Leblond et al. 2023), mathematics (Cobbe et al.
2021; Trinh et al. 2024), and a wide range of standardized tests (OpenAI 2023). These capabilities have enabled LLMs
to support a range of commercial and scientific applications (Kaddour et al. 2023).

A key driver of this progress has been algorithmic improvements, which result in more efficient use of resources such
as compute and training data. These include changes in model architectures, optimization algorithms, and software
frameworks. Many surveys of progress in language modeling describe specific innovations in detail, such as the
transformer architecture, layer normalization, IO-aware exact attention algorithms such as FlashAttention, positional
embeddings such as RoPE, and innovations in the attention mechanism such as multi-query attention (Zhao et al. 2023;
Jing and Xu 2019; Sun, X. Luo, and M. Y. Luo 2022; Huang and Chang 2022; Mialon et al. 2023; Shazeer 2019). In
addition, data quality improvements, such as training on high-quality textbook examples (Gunasekar et al. 2023) and
data pruning (Sorscher et al. 2022; Marion et al. 2023), can enable LLMs to be trained on substantially smaller datasets.

The rapid scaling of compute for training language models (Sevilla et al. 2022), coupled with insights from scaling laws
(Hoffmann et al. 2022; Kaplan et al. 2020), suggests that a substantial portion of the improvement in language model
capabilities can be attributed to the increased use of computational resources. The key question we wish to answer is
thus: How much of recent progress in language models has come from algorithmic improvements during pre-training,
and how much has been from scaling up models and datasets?

Related questions have been investigated in other domains of scientific computing, such as linear programming, SAT
solvers, and computer chess, among others (see Figure 1). While machine learning resists traditional computational
complexity analyses, it is possible to quantify algorithmic progress in terms of compute savings: How much less

†Joint first authors. 1Epoch. 2MIT FutureTech, CSAIL, 3Northeastern University. Email correspondence to tamay@epochai.

org. You can find our code and data here: https://github.com/epoch-research/lm-algorithmic-progress.

We thank Tom Davidson, Pablo Villalobos, Josh You, Lukas Finnveden, Eli Lifland, David Schneider-Joseph, Danny Hernandez,
Alyssa Vance, Yafah Edelman, Matthew Barnett, Ben Cottier, Keith Wynroe, Markus Anderljung, Carl Shulman, Marius Hobbhahn
and Nikola Jurkovi´c for their feedback. We thank Eduardo Roldán and Robert Sandler for helping design and implement graphs.

4
2
0
2

r
a

M
9

]
L
C
.
s
c
[

1
v
2
1
8
5
0
.
3
0
4
2
:
v
i
X
r
a

 
 
 
 
 
 
compute is required to attain some fixed level of performance over time? That is, we might say that an algorithm or
architecture is two times better than another one if it achieves the same result on a benchmark with half the compute.

In this paper, we quantify pre-training algorithmic improvements by following the approach first presented by Erdil and
Besiroglu (2022) in computer vision. Note that this is distinct from algorithmic progress in general, since we are not
considering “post-training enhancements", such as chain-of-thought prompting, improvements to fine-tuning techniques,
or the integration of search-based methods, which can significantly improve the performance of already-trained models
on downstream tasks (e.g. programming or solving mathematics problems) (Davidson et al. 2023).

To this end, we produce a dataset of over 200 language models that have been evaluated, by others and by ourselves,
on a range of popular language modeling datasets. We then use this data to estimate the rate of algorithmic progress.
The language modeling datasets we focus on are Wikipedia (WikiText-103 and WikiText-2 (Merity et al. 2016)) as
well as Penn Treebank (Taylor, Marcus, and Santorini 2003). We focus on evaluations on these datasets because
these represent high-quality text data that have been used for many years to evaluate language models. Focusing on
established benchmarks used throughout the development of neural language models provides continuity to compare
models old and new.

1.1 Previous work
Studies across computer science, including linear programming, SAT solving, game playing, and deep learning, reveal
algorithmic advances to be a vital driver of improved performance over time, on par with hardware improvements
following Moore’s law. Algorithmic innovations enable solutions of larger problem instances, expand the scope
of tractable problem classes, and reduce data and/or computation required to achieve fixed performance thresholds.
Estimated rates of algorithmic progress vary substantially across domains and problem sizes, but often correspond
to effectively doubling available compute resources for a task every 1-2 years (see Figure 1). However, progress is
heterogeneous, with some domains stagnating while others improve rapidly.

1.1.1 Algorithmic progress in computer science
There is a small but growing literature on progress in software and algorithms for common computer science problems.
Bixby 2012 reviews linear programming (LP) algorithm developments from 1985-1995 focusing on techniques to
efficiently solve large problems. Increased computing power enabled the implementation of more advanced algorithms
and the solution of larger models. They compare solution times using different versions of the CPLEX solver, indicating
speedups of over 1000× were achieved between 1988 and 1995. The paper concludes that advances in algorithms have
been as important as hardware improvements in enabling solutions of much larger linear programs, opening up new
domains of application.

Figure 1: Estimates of effective compute doubling from algorithmic improvements across different domains. Blue dots represent
central estimates or ranges; blue triangles correspond to doubling times for problems at different sizes (ranging from 1K to 1B);
purple dashed line corresponds to the 2-year doubling time associated with Moore’s law. Koch et al. 2022 estimate range spans
estimates for integer and mixed-integer linear programming.

2

Similarly, Koch et al. 2022 assess the progress in linear programming (LP) and mixed-integer linear programming
(MILP) solver performance by comparing modern solvers from 2020 against older solvers from around 2001. They find
algorithmic improvements have yielded 9× and 50× speedups for LPs and MILPs respectively, equating to 180× and
1000× total speedups when 20× hardware improvements are accounted for. However, the most significant advancement
has been in solving many more previously intractable problem instances and classes. While hardware gains have stalled
recently, algorithms continue rapidly advancing, expanding the frontier of tractable cases. In just the last 20 years, 62%
of problem instances from a recent benchmark went from requiring over 24 hours to solve to taking 104 seconds on
average.

Fichte, Hecher, and Szeider 2020 design a novel “time leap challenge" to evaluate the relative contributions of hardware
advances vs. algorithmic advances to progress in SAT solving over the past 20 years. By resurrecting decades-old
hardware and software, they compare modern SAT solvers from 2019 running on 1999-era hardware to early 2000s
solvers running on modern 2019 hardware. The modern solvers on old hardware solved a similar number of problem
instances as old solvers on modern hardware, suggesting that algorithmic improvements have been just as impactful as
hardware advances.

Finally, Sherry and Thompson 2021 provide a comprehensive analysis of over 100 important algorithm families and
provide evidence that algorithms have been a crucial driver of improved computing performance, and increasingly
so for larger problem sizes. Their work reveals extreme heterogeneity, with many algorithms stagnating while others
improve massively. Overall, 30-43% of algorithms outpaced hardware advances like Moore’s Law for algorithms when
the size of the work or inputs are of a moderate size (when the problem is of size n = 1 million).

1.1.2 Algorithmic progress in machine learning
Thus far, there have been few works investigating algorithmic progress in machine learning specifically. Notably,
Hernandez and T. Brown (2020) investigate the rate of algorithmic progress in computer vision; specifically, image
classification on the well-known ImageNet dataset. By re-implementing popular open-source models, they find a 44×
decrease in the compute required to train image classifiers to the same performance as AlexNet, the state-of-the-art model
in 2012. In related work, Karpathy (2022) reproduced the seminal work of LeCun et al. (1989), which demonstrated
early success in applying convolutional neural networks to handwritten digit recognition. By modernizing the model’s
loss function, optimizer, and regularization techniques while maintaining the original model size, Karpathy achieved a
60% reduction in error rate. This result highlights the significant role that advancements in training techniques have
played in the progress of computer vision over the past three decades.

Dorner (2021) measures progress in the sample efficiency of deep reinforcement learning algorithms over time
through historical training curves on Atari games, MuJoCo physics tasks, and DeepMind Control Suite environments.
Across these benchmarks, state-of-the-art sample efficiency is found to improve at exponential rates, with doubling
times ranging from 5 to 18 months depending on the domain and performance threshold. These rapid algorithmic
improvements enable reaching a fixed level of performance with orders of magnitude fewer environment samples over
time. Dorner finds that this progress is driven by factors such as better off-policy learning, model-based methods,
auxiliary objectives, and explicit tuning for efficiency.

More recently, Erdil and Besiroglu (2022) propose an alternative approach to estimating algorithmic progress based
on fitting a statistical model inspired by neural scaling laws, and use Shapley values—a technique from cooperative
game theory—to determine the relative contributions of training compute and data to performance. They find that
algorithmic improvements explain 25-70% of gains, with physical compute scaling accounting for 30-55% and data
scaling contributing 10-30%, indicating algorithms and hardware contribute roughly equally. The majority of this
algorithmic progress is “compute-augmenting", i.e. it enables the more efficient use of compute rather than data.
According to their estimates, compute-augmenting algorithmic advances halve physical compute requirements for a
certain performance level every 9 months, faster than hardware gains per Moore’s law.

Estimating the benefits of innovations in machine learning can be challenging, but in some cases the analysis is more
straightforward. For example, consider recent work by Hoffmann et al. 2022 proposing an improved scaling law for
training language models compared to the dominant understanding prescribed by Kaplan et al. 2020. By directly
applying the new scaling law, we calculate it provides a 2× to 4× reduction in compute needed to reach a given loss
target at the scale of current frontier LLMs, depending on the scale of the model (see Appendix B).

2 Methodology

2.1 Model definitions
We want to estimate the rate at which newer language models are able to achieve a certain level of performance more
efficiently than older models. We do this by fitting a model that meets two key desiderata: (1) the model must be broadly
consistent with previous work on neural scaling laws (e.g. Hoffmann et al. 2022), and (2) the model should allow for a

3

decomposition of the main contributors to increased performance, such as improvements in how efficiently data or free
parameters in the model are used. In this sense, our core approach is similar to that in Erdil and Besiroglu 2022.

The starting point is the scaling law from Hoffmann et al. 2022, which relates the training loss L of a dense transformer
to its number of parameters N and the training dataset size D:

L = E +

A
N α +

B
Dβ ,

(1)

where L is per-token cross entropy loss on the dataset, and E, A, B, α and β are constants. E represents the ‘irreducible
loss’ of the dataset, while the second and third terms, A
N α and B
Dβ , capture the errors that are due to the finiteness of the
model or dataset, respectively.

Following Erdil and Besiroglu 2022 and Hernandez and T. Brown 2020, we quantify algorithmic progress in terms of
reductions of the resources (N and D) required to achieve the same level of performance over time. To measure this,
we introduce the concepts of “effective data" Deff and “effective model size" Neff into the model:1

Neff ≡ N exp(α′(Y − Y0)), and Deff ≡ D exp(β′(Y − Y0)),
where Y is the current year, Y0 is some reference year2, and α′ and β′ characterize the rate of algorithmic progress for
model size and dataset size, respectively. In other words, we assume that continued algorithmic progress results in an
exponential increase in Deff and Neff over some time interval Y − Y0, even with fixed D and N . Plugging these into
the original scaling law gives:

(2)

L = E +

A
N αparam
eff

+

B
Dβdata
eff

= E +

A
N αparam

e−αyear(Y −Y0) +

B
Dβdata

e−βyear(Y −Y0),

(3)

where A, B, αparam, αyear, βdata and βyear are constants. In relation to equation 2, we have that α′ = αyear/αparam and
β′ = βyear/βdata. Algorithmic progress is thus captured as a constant exponential trend that multiplies with each of
the two terms in the scaling law. In doing so, we are able to estimate the rate at which fewer ‘resources’ (N and D)
are required to achieve the same level of performance over time. Furthermore, given that that the physical compute is
approximately given by C ≈ 6N D (Hoffmann et al. 2022; Kaplan et al. 2020), we can similarly define an “effective
compute" which is determined from the effective parameters and effective data.

2.2 Estimation approach
2.2.1 Model selection
We estimate variants of the augmented scaling law presented in equation (3) on our dataset of language model evaluations.
We perform extensive cross-validation exercises to identify the variant of the model that fits the data best. The goal of
this exercise is to consider different models that capture different effects (e.g. different scaling behavior across different
model architectures, different forms of algorithmic progress, etc.).

Concretely, we consider dataset-specific coefficients (A, B), rates of algorithmic progress (e.g. αyear, βyear), different
scaling coefficients for different architectures, regularization (αparam, βdata), and more. The model variants we consider
generally do not contain an irreducible loss term (i.e. E = 0) since this is poorly estimated on our data, and because it
does not change our estimated doubling times in practice—we check the robustness of this change in appendix H. In
total, we evaluate around 90 different model specifications through leave-one-out-cross validation and pick the models
that perform best on relevant out-of-sample metrics, see Appendix J for more details. In the end, the model we select is
model 7, where the coefficients A and B are benchmark specific, but estimates of algorithmic progress and scaling
exponents (e.g. α and β) are not. This model achieves an R2 of around 0.91 between predictions and held-out test data.

A further important consideration is the possibility of alternative forms of algorithmic progress. In particular, in section
2.1 we model algorithmic progress as causing exponential increases in an “effective" budget, e.g. of parameters. But
one could also observe progress through changes in scaling exponents (i.e. αparam and βdata). There are a priori reasons
to suspect that this might be the case—for instance, one notable innovation is due to a change in scaling laws such as
those introduced in Kaplan et al. 2020 and Hoffmann et al. 2022. Different model architectures, such as recurrent neural
networks and transformers, are also known to have different scaling behaviours (see for instance Tay et al. 2022 and
Droppo and Elibol 2021).

1This is not an original idea—for example, Hernandez and T. Brown 2020 and Erdil and Besiroglu 2022 use the concept of
“effective compute" to calculate doubling times for compute efficiency in computer vision, and Davidson 2023 incorporates a similar
idea into an integrated economic model.

2Note that the “years" in our model do not need to be integers, i.e. “fractions of a year" are allowed and are determined based on

the specific publication date of a model.

4

We attempt to account for this possibility in the cross validation analysis. In particular, we introduce three models
(models 13 to 15) which account for different kinds of scaling exponents, including the possibility of changing exponents
over time. Our chosen main model (model 7) outperforms these models in cross validation, but these alternatives also
perform similarly well, typically with an R2 of between 0.88 and 0.91. This analysis is described in more detail in
appendix J.

We also consider other factors that could potentially impact measured perplexity, and thereby measured rates of
algorithmic progress. For example, different tokenization schemes during preprocessing have been found to improve
WT103 perplexity in some instances (Radford et al. 2019), and training models for multiple epochs has been a common
way of improving performance (Muennighoff et al. 2023). We find that our core results are broadly the same while
varying these degrees of freedom—we provide more details on these experiments in the appendices.3

Finally, in order to account for uncertainty in our model specification in doubling times, we compare model predictions
across the different models that we consider in our cross validation analysis.

2.2.2 Data
Our dataset contains over 400 language models evaluated on WikiText-103 (WT103), WikiText-2 (WT2), and Penn
Treebank (PTB), about 60% of which we are able to use in our analysis. In particular, relevant information was retrieved
from around 200 different papers, as well as evaluations of 25 models that we performed ourselves using the framework
from Gao, Tow, et al. 2021. We then consider the subset of the data that contains the information necessary to fit
our proposed model structure in equation 3: token-level test perplexity (which determines the cross-entropy loss),
publication date, number of model parameters, and training dataset size. This leaves us with around 231 models for
analysis.

Figure 2: Log of perplexity of models used in our work, of over 231 language models analyzed in our work spanning over 8 orders
of magnitude of compute, with each shape representing a model. The size of the shape is proportional to the compute used during
training. Comparable perplexity evaluations are curated from the existing literature and from our own evaluations.

In some instances, multiple models are retrieved from the same paper, even if they constitute similar algorithmic
innovations. This could pose problems around autocorrelation, which could result in underestimating the uncertainty in
our individual parameter estimates. In the following main analysis, we therefore only include up to three models per
paper, which results in approximately 50 more models being excluded. To verify the robustness of this approach, we
also consider an alternative technique that directly accounts for autocorrelation in the analysis, which yields doubling
time and confidence interval estimates that are consistent with our main results (see Appendix I).

3 Empirical results

3.1 Models require 2× less compute roughly every eight months

How quickly are the algorithms underpinning language models improving? Our core approach is to back out doubling
times based on fitting the augmented scaling law introduced in equation (8), and using the definitions of effective
data, effective parameters, and effective compute we introduced in section 2.1. Here the effective data is given by

3In particular, we consider tokenization in appendix E.2.2, epochs in appendix F, and context length in E.2.1.

5

Deff = D exp
we have:

(cid:104) βyear
βdata

(Y − Y0)

(cid:105)
, so the doubling time for Deff is determined by the time Y − Y0 where Deff = 2D. Thus

TD = Y − Y0 =

βdata
βyear

ln 2.

(4)

The doubling times for parameter efficiency can be determined similarly, giving

αparam
αyear
which we can use to work out the doubling times for effective compute. In particular, since the total compute in FLOP,
C, required during training is approximately 6N D, the growth rates are related via gC = gN + gD. Here gC is the
growth rate in effective compute, gN is the growth rate in effective parameters, and gD is the growth rate in effective
data. Since doubling times are inversely related to growth rates, we therefore have that

TN =

ln 2,

(5)

TC =

(cid:18) 1
TN

+

1
TD

(cid:19)−1

,

(6)

where TC, TN , and TD are the doubling times (due only to algorithmic progress in pre-training) for effective compute,
effective parameters, and effective data respectively. Based on this approach, using our preferred model, we find that
the median doubling time for effective compute is 8.4 months, with a 95% confidence interval of 4.5 to 14.3 months.

(a) Core estimates. Doubling times
from our preferred model, and
aggregate of top ten models.

(b) Robustness across model specification. Swarm plots showing model estimates of
the rate of algorithmic progress across distinct model structures. For each model, we
choose the regularization strength δ that performs best in leave-one-out cross validation.

1

Degree of Freedom

2
10
Progress in Efficiency Along N ✓ ✗ ✓ ✓ ✓ ✓ ✓ ✗ ✓ ✓
✓
Progress in Efficiency Along D ✓ ✓ ✗ ✓ ✓ ✓ ✓ ✓ ✗
✗
✓
✗
✗ ✓ ✓ ✓ ✓

✗ ✓ ✓ ✓ ✗
✗
✗

Dataset Specific Exponents
Dataset Specific Constants

✗
✗

✗
✗

✗

4

5

6

7

8

9

3

11

12

13

14

15

✓
✓
✓
✓

✓
✓
✗
✗

✓ ✓T ✓T
✓ ✓T ✓T
✗
✗
✗
✗
✗
✗

(c) Summary of all model structures and the degrees of freedom included. Efficiency gains are captured by exponential decrease in
the relevant error terms, except models indicated by T , which have time-varying exponents. For a full specification, see Table 10.

Figure 3: Estimates of algorithmic progress of models selected by cross validation. Figure 3a shows aggregated estimates over
doubling times, and Figure 3b illustrates via swarm plots sorted from left to right in order of decreasing cross validation performance
(increasing MSE test loss). Note that model 14 is omitted from Figure 3b —we elaborate on our reasoning in appendix J.2.

We further check the robustness of this result by looking at the predictions from different models. In particular, because
we perform model selection using leave-one-out cross-validation, we can compare the predictions of our preferred
model with the predictions from other models we considered.4 Concatenating the doubling time estimates from the top
ten models according to our cross-validation exercise, we find a median doubling time of 7.8 months [95% CI: 1.5 to
17.6 months], which is similar to our preferred model.

4Note that our preferred model is model 7, whereas the model that performs best in cross validation is model 10. We opt for
model 7 given that it performs essentially as well in cross validation (MSE test loss of 0.0486 for model 7 compared to 0.0485 for
model 10) but uses two fewer parameters. In addition, model 7 can be used to back out a single rate of algorithmic progress, rather
than dataset-specific rates, which makes the results easier to interpret. More details about the models and their performance can be
found in appendix J.

6

Density

0.20

0.15

0.10

0.05

0.00

0

Model 7
Median: 8.4
Aggregated
Median: 7.9

5

10

15

20

Doubling time (months)

Doubling time (years)

3.5

3.0

2.5

2.0

1.5

1.0

0.5

0.0

10

7

15

8

12

5

9
6
Statistical model structure

13

11

4

3

1

2

Better cross-validation performance

Worse cross-validation performance

An alternative approach relies on a numerical procedure rather than a closed-form solution for doubling times. We first
calculate the reduction in loss ∆L that is achieved by doubling the compute budget, assuming that N and D are scaled
optimally under the estimated model. We then determine the time needed for algorithmic improvements to yield the
equivalent reduction in loss, ∆L. It turns out that these methods yield nearly identical results, with a median doubling
time of 8.6 months, and a 95% confidence interval of 4.5 to 14.5 months. This procedure is spelled out in more detail in
Appendix G.

This estimate falls within the range of confidence intervals of the estimated rates of algorithmic progress in computer
vision (Erdil and Besiroglu 2022), sample efficiency improvements in reinforcement learning (Dorner 2021), and the
rates observed for common algorithm families (Sherry and Thompson 2021) for certain input sizes. Overall, our results
suggest that algorithmic progress for language models is comparable to, and perhaps on the faster end of estimates of
rates of progress in algorithms and software in domains studied previously (see Figure 1).

While the structure of our model is not amenable to analyzing fine-grained speedups or slowdowns in the rate of
algorithmic improvements, we can nevertheless test the possibility of a one-time increase or decrease in growth rates
over the full time period. To this end, we consider a variant of our preferred model (model 7) where a dummy variable
is introduced—this is equal to 0 for any model that is published before the start of a certain year, and 1 otherwise. This
allows us to consider doubling times before and after a certain year cutoff (e.g. 2017), and we perform this analysis for
several such cutoffs.

The result is shown in Figure 4. Here we see that the difference in estimated doubling time before and after the start
of 2017 is very pronounced, however this is not the case for other choices of the cutoff year. In each year the median
doubling time is faster after the start of the cutoff year, but usually only marginally so. Overall, this does not provide
strong evidence of a drastic speedup in algorithmic progress. This does not rule out the possibility of weaker effect
sizes, since our approach is statistically under-powered.

Figure 4: Comparison of estimated doubling times for effective compute from algorithmic progress, before and after set cutoff years
from 2016-2020. Shorter doubling times in the "post" period relative to "pre" indicate an acceleration in the rate of algorithmic
progress after that cutoff year. Longer doubling times indicate a deceleration.

3.2 Most recent performance gains in next-token prediction have been from compute-scaling
Naively extrapolating our estimated doubling times suggests that, between 2014 and 2023, pre-training algorithmic
progress has enabled performance to improve as much as it would have with around 22,000× more compute.5 At the
same time, Sevilla et al. 2022 find that physical compute budgets have doubled roughly every 6 months since the start
of deep learning, including in language models. This suggests that physical compute has instead grown by a factor of
around one-million-fold. This paints a stylized picture where “effective compute" expanded by about 22-billion-fold
since 2014, with slightly under two-thirds of the scaling being due to increased use of actual, physical computing
resources.

5We consider 2014 since this is publication year of the earliest model in our dataset for which the training compute is known.

7

Doubling Time

Pre

Post

3.0

2.5

2.0

1.5

1.0

0.5

0.0

2016

2017

2018

Year

2019

2020

Figure 5: A stylized illustration of the relative contribution of compute scaling and algorithmic progress to effective compute. The
physical compute contribution is estimated from the doubling times in Sevilla et al. 2022, and the algorithmic progress contribution
is based on the aggregated doubling time estimate from the top 10 models in cross validation (see section 3.1). We further plot the
physical training compute values for several notable models (e.g. GPT-2) in their publication years.

There are reasons to be cautious about this naive extrapolation. For one, we do not directly observe gains of 22, 000×
(or even 10, 000×) anywhere in our dataset. However, given that it is unlikely that early researchers trained language
models on very large quantities of compute, it is therefore improbable that we observe such large declines over
the analyzed time period. Nevertheless, the lack of such observations still raises questions about the reliability of
extrapolating these trends between long multi-year periods.

One specific reason for caution is that the extrapolation neglects the scale-dependence of algorithmic innovations. It
is likely that some algorithmic innovations will become obsolete over time as models are trained at larger scales of
compute—e.g. the effectiveness of specific tokenizers or hyperparameter settings may diminish, making them less
useful for future, larger models. Conversely, recent innovations might fail to produce large or any benefits when
implemented at much smaller scales than models today. For example, the gains from scaling laws are related to the
scale of compute used (see Appendix B), and older architectures, such as the LSTM and convolutional network, can
exhibit higher efficiency at small scales relative to the transformer (Droppo and Elibol 2021; Karpathy 2022).

While a naive extrapolation of doubling times predicts substantial reductions in compute requirements, our work does
not provide compelling evidence that we can currently or in the future train extremely small models to achieve the
performance of much larger ones by applying the full suite of modern innovations. The scale-dependence of algorithmic
improvements and the lack of direct observations of such large efficiency gains in our dataset suggest that further
research and more comprehensive data are needed to validate these extrapolations.

Besides doubling times, we can also decompose the relative contributions from algorithms and compute scaling by
evaluating our estimated models directly. Given that our model is nonlinear, it is not possible to simply attribute
performance improvements to the scaling of compute, data, and improvements in algorithms based on coefficient
ratios. Hence, we follow Erdil and Besiroglu 2022 in using a Shapley values analysis, where we estimate the average
expected marginal contribution of each factor in reducing predicted perplexity. This analysis weakly supports the
stylized picture above that compute scaling has been more important for explaining performance improvements than
algorithmic progress since 2014.

The findings indicate that the relative contribution of algorithmic progress to performance improvements has diminished
over time, at least within the dataset of models that have historically been close to the state-of-the-art. This observation
aligns with the stylized representation in Figure 5 and the findings of Erdil and Besiroglu 2022 for computer vision,
where compute scaling has shown increasing importance over time.

One explanation for the diminishing relative contribution of algorithmic progress is that investments in expanding
physical compute have increased substantially, outpacing the rate of algorithmic improvements. This framing aligns

8

Effective compute (Relative to 2014)

1012

1010

108

106

104

102

100

Algorithmic 
progress

Chinchilla

OPT-175B

2.2 × 104

1.7 × 107

Turing-NLG

GPT-2

Physical  
compute scaling

LSTM

2014

2016

2018

Year

2020

2022

Parameter
scaling

Data
scaling

Parameter
efficiency

Data
efficiency

RNN (2012) → LSTM (2016)
RNN (2012) → Transformer (2018)
RNN (2012) → GPT-2 (2019)
RNN (2012) → GPT-3 (2021)
RNN (2012) → Gopher (2021)
LSTM (2016) → Transformer (2018)
LSTM (2016) → GPT-2 (2019)
LSTM (2016) → GPT-3 (2021)
LSTM (2016) → Gopher (2021)
Transformer (2018) → GPT-2 (2019)
Transformer (2018) → GPT-3 (2021)
Transformer (2018) → Gopher (2021)

12.7%
40.8%
42.9%
48.6%
48.4%
79.3%
65.8%
64.1%
63.2%
48.7%
56.8%
56.1%

46.5%
26.3%
32.5%
32.4%
29.8%
0.0%
21.2%
25.2%
22.3%
46.3%
35.9%
31.1%

4.9%
3.7%
2.8%
2.1%
2.5%
2.7%
1.7%
1.4%
1.9%
0.6%
0.8%
1.5%

35.9%
29.2%
21.8%
16.8%
19.3%
18.1%
11.3%
9.3%
12.6%
4.3%
6.4%
11.3%

Table 1: Attribution of progress to pre-training algorithmic progress and compute scaling between model pairs based on Shapley
decomposition in linear space. Numbers may not all add up to 100% due to rounding. The Transformer here is by Baevski and Auli
2018 (the earliest decoder-only transformer we have in our dataset), who modify the original transformer architecture by Vaswani
et al. 2017 to be decoder-only.

with the increased emphasis on scaling large language models over the last few years, particularly since the introduction
of GPT-2 in 2019 (Radford et al. 2019), relative to fundamental algorithmic or architectural changes.6Figure 5 illustrates
a stylized version of this perspective, depicting a sharp increase in physical compute scaling around 2018-2019, followed
by a return to previous compute scaling growth rates.

There are other potential explanations – for example, it is possible that the transformer architecture was a pivotal
innovation (see section 3.3), and subsequent algorithmic advances have been less significant in comparison. Alternatively,
this observation could also be explained by a secular decline in the rate of algorithmic innovation. However, we find
these two explanations less compelling than the results of Figure 4, where the rate of algorithmic progress does not
clearly decrease after the release of the transformer (e.g. with a 2018 cutoff). If anything, the rate increases slightly,
contrary to what both of these explanations predict.

3.3 The significance of the transformer architecture

Since its introduction in 2017 (Vaswani et al. 2017), the transformer architecture has become the dominant algorithmic
architecture in language modeling, forming the base of multiple notable systems. The transformer has also been
widely adopted in vision models, and there is a rich existing literature that has evaluated the merits of the transformer
architecture against other architectures in vision.

We attempt to quantify the contribution of the transformer architecture in terms of the “compute-equivalent gain" over
other architectures in our dataset (LSTMs, RNNs, state space models, among others). This is akin to the approach
outlined in Davidson et al. 2023—in this context, the compute-equivalent gain is the amount by which training compute
must be scaled to improve benchmark performance as the same amount as the introduction of the transformer. For
example, Hernandez and T. Brown 2020 find that a transformer (2017) achieves the same performance as a Seq2Seq
(2014) model on the WMT-14-EN-FR benchmark, with 61× less compute.

To capture the improvement represented by the transformer, we modify our core model as follows:

L =




σ(γT )



A
αyear
eff

N

(cid:18)

A
αyear
eff

N
+ B
D

βdata
eff

(cid:19)

+ B
D

βdata
eff

,

,

if transformer,

otherwise.

(7)

where σ : R → (0, 1) is the sigmoid function, given by σ(x) = 1/(1 + e−x). γT is a constant and all other terms have
the same meaning as in the original model.7 The key intuition is that the transformer could enable us to use compute (or
perhaps data) more efficiently than the architectures that precede it.

6We can provide further support for this interpretation by considering the average growth in compute between pairs of systems in
Table 1. This turns out to be higher for later pairs of systems that we consider: e.g. between the Transformer and GPT-3 there was an
average annual growth rate of 9%, compared to an average growth rate of 2% between the 2012 RNN and GPT-2.

7The sigmoid is introduced to make it easier to fit the model by improving optimizer stability.

9

After preprocessing, our dataset contains 103 transformer models, and 127 non-transformer models, largely consisting
of recurrent networks such as the LSTM. Fitting the model on this data reveals that the transformer architecture typically
lowers reducible loss proportionally by 4.6% [95% CI: 3.0%, 7.0%].

We can calculate its contribution in terms of “compute-equivalent gains" numerically: we first calculate the predicted
loss for a transformer with some N and D, and the predicted loss for a non-transformer with the same inputs. We
then determine reduction in N and D to match this difference in loss. Compute is then approximated as usual, as
C ≈ 6N D. In short, if an innovation halves the compute needed to achieve a specific loss, then that innovation has a
compute-equivalent gain of 2.

Based on 100 bootstraps, we obtain a median estimate of 7.2× [95% CI: 3.3×, 45.7×] for the transformer’s compute-
equivalent gain.8 This substantial gain indicates that the efficiency offered by the transformer architecture is equivalent
to around log(7)/ log(2e4) ≈ 20% of the total gains from algorithms in the past nine years, or nearly two years of
algorithmic progress in the field.9 Moreover, this could understate the gains if the transformer architecture also provides
a convenient vehicle through which to productively channel compute, thereby facilitating some of the gains through the
scaling of compute that have likely dominated the overall gains we have seen recently.

One caveat here is that the measured significance of the transformer may depend on how it is evaluated. For example,
transformers may be better adapted to long contexts than recurrent networks, and evaluations using longer contexts (e.g.
>1000 tokens) may suggest a larger improvement from transformers than evaluations using shorter contexts (Kaplan
et al. 2020). We have not explicitly controlled for context length here, and we discuss the potential impact of this
assumption in more detail in appendix E.2.1.

4 Discussion and conclusion

4.1 Summary of our findings
This paper presents a comprehensive empirical analysis of algorithmic progress in language model pre-training
from 2012 to 2023. By curating a dataset of over 200 language model evaluations on WikiText and Penn Treebank
benchmarks, we quantify the relative contributions of compute scaling and algorithmic efficiency improvements to the
overall performance gains. Our key findings are as follows:

First, we estimate that the compute required to reach a set language modeling performance level has halved every 8-9
months on average since 2012. This rate significantly exceeds hardware gains per Moore’s law and places language
modeling among the fastest advancing domains in algorithmic progress, alongside computer vision and reinforcement
learning. This supports the common intuition that language modeling is an unusually rapidly-advancing field of
computer science.

Second, our work reveals that the majority of recent advancements in language modeling stem more from scaling
models and datasets than from pre-training algorithmic innovations. A Shapley value-based analysis suggests that
60-95% of the performance gains stem from compute scaling, while algorithms contribute only 5-40%.

Third, the introduction of the transformer architecture in 2017 was a major algorithmic advance, representing between
3x and 46x in compute-equivalent gain, which accounts for more than 10% of the algorithmic innovation in pre-
trained language models in the past decade. This highlights the significance of the transformer as a key architectural
breakthrough in the field.

4.2 Limitations
While our analysis is an advance in quantifying algorithmic progress, several limitations reduce the precision of and
temper our confidence in our estimates:

• Lack of estimates of gains from specific innovations. Our model is specified to quantify algorithmic progress
over relatively large time periods (e.g. over several years). However, it is unable to give reliable fine-grained
information, such as progress over shorter time scales, or the significance of specific innovations. Experimental
work is better suited to estimating efficiency gains for specific algorithmic innovations.

• Limited availability of quality data. The approach we use in our analysis relies heavily on having many data
samples across many years. This proved to be very challenging for a number of reasons—e.g. models are not

8This assumes compute budgets of frontier models today, at 1025 FLOP. At lower compute budgets, such as 1022 FLOP, the gain

is still substantial at 6.6× [95% CI: 3.2×, 28.2×].

9Given the magnitude of this contribution, we also attempted to check the rate of algorithmic progress while subsetting our data
to non-transformers only. However, this roughly halves the data available for fitting, and our resulting estimates are unfortunately
extremely noisy. While our central doubling time estimate is 8.8 months, this result is no longer statistically significant, with a 95%
confidence interval of -30.6 to 34.8 months.

10

Predicted requirements for GPT-2 performance

Predicted requirements for Chinchilla performance

Figure 6: Pareto frontiers for GPT-2 (Radford et al. 2019) and Chinchilla (Hoffmann et al. 2022) level performance on WT103. We
truncate the frontiers to a factor of 1e3 greater or smaller than the existing training dataset size and parameter size of the actual
model since extrapolating further out would not be reliable.

always evaluated on the same benchmark, data is relatively sparse prior to 2017, and papers may not report
relevant information such as parameter counts. Among other reasons this can result in our estimates being
very noisy, yielding wide confidence intervals over doubling times. In addition, algorithmic improvements and
scaling have historically been introduced concurrently, and this correlation between the two in our dataset can
make it hard to disentangle their relative contributions to overall effective compute growth.

• Inconsistencies in model training and evaluations. Inconsistencies in evaluations are well-known. While we
have excluded non-standard evaluations from our dataset, our dataset spans models with different tokenization
schemes, text preprocessing, stride lengths, and other details. This introduces noise and potential bias in our
estimates of algorithmic progress, as researchers might have adopted more favorable evaluation schemes over
time. However, our estimated reductions in perplexity from algorithmic improvements are large; likely larger
than can be accounted for by changes in evaluation procedures. We expand on these points in Appendix E.2.3.

• Inability to distinguish between data quality and efficiency in data use. The way that we define efficiency
improvements in this paper is in terms of reductions in the amount of resources required to achieve a certain
level of performance over time. However, in the case of data efficiency, this runs into a problem—are our
measured reductions in data requirements due to improved data quality, or due to improvements in how
well algorithms are able to use data? This is not a question that our model equips us to answer.
It is
therefore important to note that our measured reductions in compute requirements pertain to both algorithmic
improvements and data quality improvements, the relative contributions of which could be a subject of future
research.

• Reliance on the Chinchilla scaling law. The scaling law from which our model is derived applies to dense
transformers following a GPT-3 architecture (Hoffmann et al. 2022; Rae et al. 2021). However, we use
this scaling law to model algorithmic improvements in different transformer architectures, recurrent neural
networks, etc. Future algorithms might also follow different scaling laws (e.g. GPT-4 is rumored to be a
mixture of experts). However, we believe it is likely that our core results should still hold: for one, neural
scaling is not a phenomenon restricted to transformers (e.g. it is known to happen in RNNs as well, see Kaplan
et al. 2020). We find that a wide range of statistical model structures provide consistent estimates, and that
alternative methods of estimating pre-training algorithmic progress also give similar results (see e.g. appendix
A), so it is probable that our core results are robust to the use of the scaling law from Hoffmann et al. 2022.

• Limited insight about future progress. While the results from this paper could be used to inform one about
future progress in language modeling, our paper focuses on historical improvements. Future rates of progress
could be slower (e.g. if one thinks that historical progress consisted of picking “low hanging-fruit"), but they
could potentially also be faster (e.g. due to increased research interest and investment). Expectations about
future progress need to account for factors such as these, which we do not discuss in depth for the most part.

11

Parameters

1012

1011

1010

109

108

107

107

108

109

1011
Training Dataset Size (Tokens)

1010

1012

Parameters

1017

1016

1015

1014

1013

1012

1011

1010

109

1010

1011

1012

1013

1014

1015

Training Dataset Size (Tokens)

4.3 Conclusion
Using a dataset of over 200 language model evaluations spanning 2012-2023 evaluated on Wikitext and Penn Treebank,
we find that the compute required to reach a fixed performance threshold has halved approximately every 8 months.
This is much faster than the rate associated with Moore’s law and many other domains of computing. While algorithmic
innovations have occurred rapidly, compute scaling has expanded by over a million-fold in this same period, exceeding
the gains from algorithms and constituting the predominant source of performance improvements in recent years.

Overall, our work provides a quantitative estimate of the rapid pace of progress in language modeling. It also reveals the
dominant role of scale rather than algorithms for recent gains. Future work could benefit from extending this analysis to
additional, specific benchmarks and more closely examining the impact of data quality improvements and the gains
from additional specific innovations. Despite its limitations, this research demonstrates the valuable insights that can be
gained from a detailed statistical analysis of extensive datasets of machine learning results. By identifying the main
drivers of performance improvements, this work lays the groundwork for further exploration and understanding of these
trends in the field.

Appendices

A Observing improvements in the data

Besides the statistical model that we presented in section 2.1, we can also attempt to obtain doubling time estimates
more directly. For example, we can look at LLMs that achieve close to Megatron-LM’s or GPT-2’s level of performance
over time, and see how much less compute is used. Doing so reveals that we need between 5-fold and 100-fold less
compute per year in 2023 to achieve the same performance achieved is between 2019 and 2023, amounting to a halving
time of between 6 and 15 months.

(a) Relative training compute needed for
Megatron-LM level performance

(b) Relative training compute needed for
GPT-2 level performance

(c) Relative training compute needed for
Gopher level performance

Figure 7: Relative compute (relative to baseline model) used to train models that achieve the same evaluated perplexity as
Megatron-LM, GPT-2, and Gopher respectively. Doubling times of effective compute are 14.9, 5.9, and 6.9 months using least
squares regression for Megatron-LM (cross-entropy range 2.87-3.06), GPT-2 (cross-entropy range 2.79-2.93), and Gopher
(cross-entropy range 1.87-2.32), respectively. Circles are proportional to the compute used during training.

This approach provides some insight but it has its issues, which is why we do not rely on it. For instance, it depends
on the particular choice of reference performance. As can be seen from the above figure, depending on the choice,
the exact rate can differ by a factor of 2.5. Moreover, this approach requires identifying models with similar or better
performance at later dates, where the training compute is known. However, the data for the latter is relatively limited.
We thus opt for using an arguably more principled approach with our core model presented in section 2.1 for our main
results.

B The gains from better scaling laws

We estimated the compute savings afforded by the Chinchilla scaling law, as proposed by Hoffmann et al. 2022, in
contrast to the previously dominant understanding based on the work of Kaplan et al. 2020. First, we defined loss
functions L(N, D) for both the Kaplan and Chinchilla scaling laws. Following this, we minimized these loss functions
across variables D and N , considering different levels of compute budget. For each specified budget, we then calculated
the amount of compute required under the Chinchilla scaling law to achieve a loss equivalent to the minimum loss

12

Relative training compute

300%

100%

30%

10%

3%

1%

Megatron-LM

HSO

ALiBi

NMST 
+GPT-2

Transformer + RD

DFWT

Transformer
 + GFM

B2T connection

Doubling Time:
14.9 months

2019

2020

2021

2022
Publication Date

2023

Relative training compute

300%

100%

30%

10%

3%

1%

GPT-2 (1542M)

Compressive 
Transformer

ALiBi

Doubling Time:
5.9 months

-former

Transformer
+ RD

2018

2019

2020

2021

2022

Publication Date

Relative training compute

300%

100%

30%

10%

3%

1%

Chinchilla

OPT-175B

Gopher

BLOOM-176B

LLaMA-33B

OPT-66B 
+ RE-PLUG

Doubling Time:
6.9 months

2021

2022

2023

2024

2025

Publication Date

obtained under the Kaplan scaling law. The Compute-Equivalent Gain (CEG) was subsequently determined as the ratio
of the original compute budget to the compute required by the Chinchilla scaling to match the Kaplan loss.

Figure 8: Compute equivalent multiplier from optimal scaling from switching from Kaplan et al. 2020 to Chinchilla (Hoffmann
et al. 2022) scaling laws as a function of training compute for dense autoregressive transformer models. Note that GPT-3 and PaLM
(540B) use around 1.7 and 1.44 tokens/parameter respectively, close to what the Kaplan scaling laws recommend, suggesting that
Kaplan-scaling was close to what was practiced at the time.

We find that the compute equivalent multiplier from the Chinchilla scaling laws for dense autoregressive transformer
models is between 1.75-fold (for GPT-2 scale models) and 4-fold (for PaLM-scale models Chowdhery et al. 2023).10

C Core model parameter estimates

The core model that we use was chosen based on leave-one-out cross validation, and is defined similarly to equation 3
but with a few modifications. The most important change is that A and B are estimated separately for each benchmark,
whereas all other parameters are benchmark-agnostic. In order to help with model fitting, we normalize N and D to
some minimum N0 and D0 values in our dataset, and reparameterize A and B as exponentials. In full, our model is

L = exp[α′

const − αyear(Y − Y0) − αparam log(N/N0)] + exp[β′

const − βyear(Y − Y0) − βdata log(D/D0)],

(8)

To estimate these in benchmark-specific fashion, we introduce dummy variables xWT2 and xPTB for WT2 and PTB
respectively. We then complete the model definition as follows:

α′

const = αconst + αconst,PTBxPTB + αconst,WT2xWT2,
β′
const = βconst + βconst,PTBxPTB + βconst,WT2xWT2.

Our parameter estimates are summarized in Table 2.

One observation about the parameter estimates in Table 2 is that the confidence intervals for αyear and βyear are not
statistically significant at the 5% significance level, while αparam and βdata are. As mentioned in section 3.2, the result is
that the model fails to obtain statistically significant estimates of effective parameter and effective data doubling times.
However, when we use these estimates to determine effective compute doubling times, we obtain statistically significant
estimates. The reason for this is illustrated in Figure 9—the estimates for αyear and βyear are clearly negatively correlated.
In particular, when αyear is positive, βyear is negative and vice versa, such that the overall estimated effective compute
doubling time is always positive.

10We use PaLM as a reference rather than larger more recent models such as GPT-4 because it was unlikely that GPT-4 would
have been trained without an improvement in our understanding of scaling laws, whereas PaLM was likely trained prior to the
development of updated scaling laws.

13

Compute multiple equivalent

5x

4x

3x

2x

1x

PaLM 
(540B) 
scale

GPT-3 
scale

GPT-2 
scale

1019

1020

1021

1022

Compute

1023

1024

1025

Estimate

95% CI

αconst

αconst,PTB

αconst,WT2

αyear

αparam

βconst

βconst,PTB

βconst,WT2

βyear

βdata

∗
0.913
(0.235)
0.000
(0.076)
0.055
(0.118)
0.004
(0.021)
∗
0.068
(0.022)
∗
0.771
(0.225)
0.176
(0.108)
0.095
(0.120)
0.036
(0.023)
∗
0.040
(0.011)

0.000, 1.208

−0.008, 0.185

−0.119, 0.176

−0.058, 0.032

0.045, 0.127

0.233, 1.293

−0.006, 0.285

−0.081, 0.317

−0.002, 0.080

0.023, 0.062

Table 2: Parameter estimates from the model described in equation 8, rounded to 3 decimal places. We report 95% confidence
intervals for all of the parameter estimates by bootstrapping 100 iterations. * corresponds to a p value below 5%.

C.1 Comparing our estimates to earlier work

Given that our core model is similar to previously proposed language model scaling laws, we can compare our estimates
to see how well they correspond to prior work. In particular, the estimates for αparam and βdata in Table 2 suggest that
cross entropy loss scales roughly as C −1/20, where C is training compute. In comparison, Kaplan et al. 2020 find a
scaling exponent of around -0.048, and Hoffmann et al. 2022 estimate values of around -0.3. Given that our model is
constructed based on the scaling law in Hoffmann et al. 2022, we might a priori have expected our estimated to match
those more closely—so what explains the difference?

Figure 9: (a) (Left) Comparison of scaling law predictions from our preferred model and previous work, specifically Kaplan et al.
2020 and Hoffmann et al. 2022. The grey lines represent scaling laws based on bootstraps of our proposed model. The two vertical
dotted lines indicated the 10th to 90th percentile range of training compute values in our dataset. (b) (Right) Estimated values of
αyear and βyear from 1000 bootstraps. 95.2% of the bootstrapped estimates lie to the right of the line αyear + βyear = 0.

One way to understand this discrepancy is to consider the scaling laws on the same plot, shown in Figure 9. Here we
observe that the scaling laws strongly diverge for compute values below around 1018 to 1019 FLOP (and the same is
true for values greater than 1022 FLOP). However, between these two regimes the scaling laws appear much more
similar in slope.

14

Cross entropy loss

Chinchilla

Kaplan

Ours

3.6 × 1017 
FLOP

1.2 × 1022 
FLOP

6

5

4

3

2

1014

1016

1018

1020

1022

FLOP

95.2%

4.8%

year

0.125

0.100

0.075

0.050

0.025

0.000

0.025

0.050

0.10

0.08

0.06

0.04

0.02 0.00

0.02

0.04

0.06

year

This observation suggests the possibility that the discrepancy in estimated scaling exponents is due to the range of
fitted data. Indeed, around 80% of our models with known training compute estimates lie between ∼ 4 × 1017 FLOP
and 1022 FLOP. This suggests that a large fraction of our data lies within the regime where it is hard for our model to
distinguish between the exponents from Hoffmann et al. 2022 and Kaplan et al. 2020.

Another possible explanation for this discrepancy that we considered is that it is due to the omission of an irreducible
loss term in our core model, resulting in an omitted variable bias. However we do not put much weight on this
explanation for our fits—in our robustness check using models with an irreducible loss term (see section H), we obtain
very similar scaling exponents to those obtained in our core model.

D Significance of the transformer architecture

Similarly to the doubling times for effective compute, we consider the predicted Compute-Equivalent Gains by applying
the same modification in Equation 7 to the top 10 models from our cross validation exercises. Most models yield
estimates within a similar ballpark as our core model, with some models yielding relatively noisy estimates. That said,
one model (model 12 with δ = 0.02) predicts a notably larger efficiency contribution from the transformer, and this
suggests that there is plausibly a fairly large degree of cross-model uncertainty present. These results are shown in
Figure 10.

Estimate

95% CI

αconst

αconst,PTB

αconst,WT2

αyear

αparam

βconst

βconst,PTB

βconst,WT2

βyear

βdata

γ

0.506
(0.496)
0.030
(0.165)
0.000
(0.123)
−0.035
(0.037)
∗
0.079
(0.054)
∗
1.103
(0.421)
0.107
(0.084)
0.112
(0.112)
0.055
(0.027)
∗
0.029
(0.018)
∗
2.972
(0.251)

−0.027, 1.314

−0.176, 0.180

−0.097, 0.399

−0.076, 0.049

0.040, 0.226

0.000, 1.376

−0.003, 0.259

−0.079, 0.306

−0.024, 0.076

0.018, 0.076

2.580, 3.492

Table 3: Parameter estimates from the model described in equation 7, reported to 3 decimal places. We report 95% confidence
intervals for all of the parameter estimates by bootstrapping 100 iterations. * corresponds to a p value below 5%.

E Dataset

E.1 Performance measure and dataset

A key component of measuring progress in machine learning algorithms is the presence of a performance metric
or benchmark. Since our focus is language modeling, token-level perplexity is a natural choice for this metric, for
which we choose three benchmarks: WikiText-103, WikiText-2, and Penn Treebank. Note that WT2 and WT103 are
both constructed from articles on Wikipedia. The two benchmarks share the same validation and testing set, while
WikiText-103 has a much larger vocabulary and training set. In total, our dataset is constructed from 226 papers, from
which we collect around 410 models that have reported token-level perplexity. Of these models, 370 contain sufficient
information to be considered for analysis (perplexity, parameter size, publication date, and size of dataset).

E.2 Perplexity

A standard metric for LLM performance is the measured test perplexity on standard datasets. For a language model,
this is defined in as the exponential of the cross-entropy L between the model predictions and the test set, i.e.
Perplexity = eL.

15

Figure 10: Contribution of the transformer in terms of Compute Equivalent Gain, as by introducing the structure in equation 7 to
the top 10 models in leave-one-out cross validation.

We choose this metric for two primary reasons. First, this is a commonly reported measure of performance, which
allows us to gather a large dataset for our analysis. Second, the simple relation between perplexity and cross entropy L
allows us to easily relate our model to neural scaling laws.

If a paper reports the perplexity of just one model, we collect that singular data point. However, when a paper presents
multiple models, only those meeting any of the following criteria are included in our dataset:

1. The model is trained or evaluated on a different benchmark dataset. A model trained on two different datasets
can be used as a reference to understand how perplexity metrics reported on different benchmarks relate to one
another. This can be helpful e.g. for data imputation

2. The model is constructed with a drastically different parameter size, as such data inform the impact of scaling

3. The model has a significant difference in the algorithms used than other models in the paper

For papers presenting many (10 or more) models, we exclude some from our dataset to prevent possible bias from
over-representing results from a few studies. We prioritize models with the lowest perplexity in their category, often
highlighted in bold within tables. We also exclude minor algorithm alterations and ablations that do not impact the
parameter count. In Appendix I, we take an alternative approach by including all models from each paper and explicitly
modelling the autocorrelation structure from results from the same paper. In doing so, we find results highly similar to
those we present in the paper.

E.2.1 Context length
Another consideration when analyzing algorithmic innovation in language models pertains to the context length. For
one, measured perplexity on benchmarks can depend on the context length (Kaplan et al. 2020; Xiong et al. 2023).
Different systems may have been trained or evaluated using different context lengths, and this might make model
perplexity scores less directly comparable.

One way to try and quantify the magnitude of this effect is to look at studies that compare the change in perplexity
given a change in context length. For example, based on the scaling relations relating loss and context length from
Xiong et al. 2023 and Kaplan et al. 2020, back-of-the-envelope calculations suggest that loss reductions each year due
to increasing context length could be 10-60% as large as the loss reductions from algorithmic progress.

In particular, Xiong et al. 2023 finds a relation between context length c and validation loss for different versions of
the LLaMa 2 language model. We can estimate ballpark values for context length over time based on data from Vries
2023, and use this to roughly estimate how expanding context lengths has decreased loss over time (e.g. a decrease of a
few percent per year). We can then compare the magnitude of this effect to the contribution of algorithmic progress to

16

Compute Equivalent Gain (CEG)

104

103

102

101

100

10 (0.001)

7 (0.0025)

15 (0.01)

8 (0.005)

15 (0.005)

7 (0.01)

12 (0.02)

10 (0.0025)

10 (0.005)

12 (0.005)

Better cross-validation performance

Worse cross-validation performance

Model (delta)

decreases in loss, and we typically arrive at values between 10-60% of the overall algorithmic progress contribution.11
We perform a similar analysis with the scaling relation described in Kaplan et al. 2020, with similar results. If this
rough calculation is correct, it suggests that increasing context length may have been a fairly important dimension along
which algorithms have been improving.

On top of measured reductions to averaged perplexity per token, one might also consider the increasing ability of
language models to perform long-context tasks to be largely downstream of algorithmic progress in itself. Being able to
handle long contexts is a key motivator for several recent algorithmic innovations (Liu et al. 2024; Gu and Dao 2023;
Gemini Team 2024), and this has likely grown very substantially since the introduction of FlashAttention (Dao et al.
2022; Vries 2023). We consider this to be an important avenue for further investigation.

E.2.2 Tokenization
One way to get a sense of the impact of tokenization on measured doubling times is to introduce a fixed effect that
depends on the benchmark vocabulary size into our preferred model. In particular, we introduce an irreducible loss term
to Equation 8, of the form γ log(vocabulary size).

As with the rest of our analysis, we perform bootstraps to obtain a distribution over estimated doubling times, and
further fold this model into our cross validation analysis. In particular, this model predicts a median effective compute
doubling time of 8.0 months, with a 95% confidence interval of 4.0 to 17.1 months. In cross validation, this model
performs essentially as well as our preferred model, with a MSE loss of 0.0486 in both cases. Both of these results are
very much in line with the results from our main model, lending some weight to the view that differences in tokenization
schemes used in practice do not substantially change our core results.

Figure 11: Histogram showing the most common vocabulary sizes for models in our dataset, separated by benchmark.

One possible reason for this is that in practice, the tokenization schemes used for evaluating language models on the
considered benchmarks (i.e. WT103, WT2 and PTB) are typically highly similar, and so including a contribution from
vocabulary size has only a limited effect within each dataset. For example, typical tokenizers for PTB, WT2 and WT103
have vocabularies of roughly 10k, 22k, and 268k tokens respectively. We illustrate this in Figure 11, where for each
benchmark, the majority of vocabularies fall into the same histogram bin.

Inconsistencies in perplexity evaluations

E.2.3
Inconsistencies in benchmark evaluations is a well-known issue in the machine learning community. These issues can
introduce noise (if inconsistencies are ‘random’), or bias if they systematically change over time. We curated data so
that models were evaluated in roughly comparable ways, but often the precise details of evaluations were lacking, so
that we could not verify the precise evaluation procedure. However, there are many other subtleties with evaluation
setups that may also cause perplexity results to differ, such as pretraining data, test-time adaptation (Takase, Suzuki,
and Nagata 2018), tokenization schemes, strides, and text preprocessing.

Overall, we do not see these issues substantially undermining our results. Our mainline estimates imply that 1 year of
pre-training algorithmic progress amounts to a reduction of perplexity of around 10%, which is a much larger reduction
than seems plausible to explain by changes in the average year-to-year evaluation procedures.

11This of course depends on variables like how quickly context lengths have expanded over time—details of this calculation can

be found in this spreadsheet.

17

PTB

WT2

WT103

Number of models

60

50

40

30

20

10

0

1e4

3e4

1e5

3e5

1e6

1e4

3e4

1e5

3e5

1e6

1e4

3e4

1e5

3e5

1e6

Vocabulary

Variation source

Significance

Training set

Word vs sub-word tok-
enization

Preprocessing and run-
time adaptation

Stride length

Early models in our dataset are often exclusively trained on the benchmark training set before evaluation,
whereas later models are generally pretrained on a larger pretraining dataset. Since the majority of our
dataset involves the latter type of model, we expect this effect to be minor. The direction of this effect
is somewhat ambiguous: the training set data is likely ‘closer’ to the test distribution relative to other
internet text-corpuses, so not training on the relevant training distribution could yield lower performance
at fixed budgets.
A further subtlety is that large text corpuses often, but not always, contain Wikipedia data. Pretraining
on such distributions could yield larger gains than otherwise, which could be attributed to algorithmic
progress. A small number of existing results illustrate this effect. For example, in a 1.3B GPT-3
reimplementation, including Wikipedia and other high-quality data in fixed-size pretraining reduced
WikiText perplexity from 8.27 to 5.59 (Gao, Biderman, et al. 2020, Table 3). In our dataset, this effect is
likely to show up as a small number of models receiving worse-than-otherwise perplexities in WikiText,
around the time of the transition to large-scale pretraining but before inclusion of Wikipedia data became
common. This is true of GPT-2, for example.
Changing to a sub-word vocabulary can reduce perplexity substantially in an otherwise unchanged
architecture, for example by ∼30% in a pre-GPT-2 LSTM (C. Wang, M. Li, and Smola 2019). In
our dataset this is likely to show up as a one-time change, potentially exaggerating the algorithmic
improvement in language models around GPT onwards.
Different preprocessing of data can affect results significantly. For example, inverting word-level
tokenization artifacts in WikiText-103 improved perplexity by ∼10% (Radford et al. 2019). Runtime
adaptation sometimes has similarly large effects (Alon et al. 2022). We expect that these sources of
variation mostly act as noise in our dataset, although if these improved over time, they might inflate
estimates of algorithmic efficiency.
The move to larger models led to evaluations using larger stride for lower computational cost. This can
increase perplexity, but only on the order of ∼10% at realistic settings (Hugging Face 2023). We believe
this should act as another source of variation, but without a strong influence on our overall findings.

Table 4: Sources of variation and their significance in language modelling evaluations.

Given that test perplexity on these datasets has persisted as a standard measure of language modeling performance in
the literature, we expect that differences in perplexity will broadly reflect genuine underlying differences in model
capabilities.

E.3 Dataset Size & Epochs

In reporting training dataset size, we generally record the size of pre-training datasets as well fine-tuning datasets if the
model in question has been fine-tuned. The number of epochs is usually sourced from the papers which describe the
language model in question, but if not provided, we estimate it via

num_epochs =

context_length_tokens · batch_size · training_steps
pretrain_tokens

.

We adjust our epoch and dataset size calculations accordingly for models like GPT-Neo and Pythia, which report the
effective number of tokens seen in training.

E.4 Parameter Size

We use the reported parameter size value if it is stated in the paper. We impute the parameter size from the previous
models for papers that do not specify parameter size but follow known, state-of-the-art models. Otherwise, we rely
on other papers referring to the model’s parameter size or manually compute parameters for certain RNN and LSTM
models based on provided details about the model architecture (e.g. the number and size of hidden layers).

E.5 Inclusion and exclusion criteria

We exclude several models in the dataset from the analysis based on whether they meet any of the following primary
criteria: (1) use of a retrieval mechanism, (2) use of model compression or pruning, (3) use of neural architecture search,
(4) use of teacher-learner or knowledge distillation mechanisms, (5) use of cache models. These models are excluded
because we expect these models to exhibit significantly different scaling behaviors from other models we analyze. In
particular, they can substantially change the ratio of parameters and data that would “optimally" minimize loss given
some compute budget.

18

F Quantifying training data D

One important degree of freedom in the modeling process is how to define the “training data". In particular, there we
consider three possible definitions:

1. Training dataset size: The number of tokens in the dataset on which the language model was trained. This
definition ignores the possibility of improvements in performance from training for multiple epochs, and is the
approach taken in Erdil and Besiroglu 2022.

2. Tokens seen: The total number of tokens seen during the course of training a language model—this is
the definition adopted in Hoffmann et al. 2022. This is equivalent to the training dataset size if the model
is trained for one epoch on the training set, which is fairly common practice but not totally ubiquitous.
In fact, it is possible that more recent models are being pushed towards training with multiple epochs
on the same data—e.g. GPT-4 was reportedly trained for 2 epochs on text and 4 epochs on code (Patel
and Wong 2023).
In cases where the tokens seen is not directly reported in paper, we estimate it via
tokens seen ≈ num. epochs × training dataset size.

3. Tokens seen with diminishing returns: One problem with the previous approach is that seeing data repeatedly
may yield diminishing returns. Muennighoff et al. 2023 find that the benefits in loss reduction drop significantly
when training on more than 4 epochs.

In order to test the robustness of our most important result (compute doubling times) to this degree of freedom, we
repeat our doubling times analysis as in section 3.1 but account for the number of training epochs. We then replace D
either with tokens seen (epochs times training dataset size) or tokens seen with diminishing returns. For each case we
consider two possibilities—either we drop datapoints for which the epoch number is unknown (this drops around 90
datapoints), or we impute the epoch number as 1. We report our core parameter estimates in Tables 6 and 7, and our
doubling time estimates in Table 5.

Definition
Dataset size (section 3.1)
Tokens seen
Tokens seen + impute
Tokens seen w. dim. returns
Tokens seen w. dim. returns + impute

Ceff doubling times (months)
[4.5, 8.4, 14.3]
[1.4, 3.5, 20.9]
[4.8, 9.1, 16.9]
[1.7, 5.7, 28.0]
[4.8, 9.2, 18.1]

Table 5: Estimated effective compute doubling times using the core model (equation 8), using three different definitions of “training
data". Numbers in the square brackets correspond to the [2.5th, 50th, and 97.5th percentile] after bootstrapping 100 times.

From the results in Table 5, we see that the model estimates are broadly consistent with each other. When dropping
datapoints with unknown epochs, the median estimates do appear to become slightly shorter, but importantly the overall
95% confidence interval spans a slightly larger range compared to the default model using dataset size. Our overall
uncertainty is therefore fairly similar under this degree of freedom. If we instead impute epoch values when they are
unknown, we obtain results that appear significantly more similar to our core results (e.g. in terms of the median
estimate), but with more probability mass on long doubling times.

We ultimately opt to quantify training data in terms of dataset size for simplicity, and this analysis suggests that our
results are robust to this change.

G Doubling times via optimal scaling

In the main paper we calculated doubling times for effective compute based on a closed form solution for the doubling
times, given by Equation 6. However, this equation was derived simply by considering changes in Deff, and it is not
clear a priori whether or not the effective compute is optimally allocated between Neff and Deff to minimize the cross
entropy loss. In addition, calculating compute efficiency doubling times is less straightforward for models which
also include changing scale exponents αparam and βdata (i.e. models 14 and 15 in our cross validation analysis, see J).
We thus supplement our previous calculation with an alternative approach, which instead enforces the condition of
compute-optimal scaling.

We approach this in two stages:

1. First, we calculate the reduction in cross entropy loss ∆L given a doubling in compute budgets and under

compute-optimality. Let the initial compute budget be C. We solve an optimization problem

L1 = min
(N,D)

L(N, D),

19

(9)

Estimate

95% CI

Estimate

95% CI

αconst

αconst,PTB

αconst,WT2

αyear

αparam

βconst

βconst,PTB

βconst,WT2

βyear

βdata

0.317
(0.336)
0.098
(0.079)
0.077
(0.158)
−0.069
(0.033)
∗
0.135
(0.026)
∗
1.373
(0.319)
0.049
(0.105)
0.100
(0.185)
0.075
(0.026)
∗
0.024
(0.010)

−0.000, 1.395

−0.033, 0.220

−0.071, 0.569

−0.107, 0.022

0.073, 0.186

0.000, 1.542

−0.034, 0.339

−0.649, 0.190

−0.003, 0.103

0.015, 0.063

αconst

αconst,PTB

αconst,WT2

αyear

αparam

βconst

βconst,PTB

βconst,WT2

βyear

βdata

0.930
(0.340)
0.000
(0.074)
0.143
(0.130)
−0.012
(0.031)
∗
0.081
(0.027)
∗
0.826
(0.331)
0.176
(0.129)
−0.001
(0.211)
∗
0.062
(0.028)
0.036
(0.013)

−0.000, 1.357

−0.088, 0.137

−0.001, 0.589

−0.097, 0.027

0.060, 0.165

0.000, 1.432

−0.003, 0.401

−0.756, 0.281

−0.006, 0.111

0.016, 0.060

Table 6: D = tokens seen.

Table 7: D = tokens seen with diminishing returns.

Parameter estimates from the model described in equation 8, to 3 decimal places. We report 95% confidence intervals for all of the
parameter estimates by bootstrapping 100 iterations. * corresponds to a p value below 5%.

subject to the constraint C = 6N D described in Hoffmann et al. 2022, which is solved with values N ∗
1 and
D∗
1. We then perform the same optimization problem but with a budget constraint of 2C = 6N D, yielding a
corresponding cross entropy loss of L2. The reduction in cross entropy loss is given by ∆L = L2 − L1 ≤ 0.

2. We then estimate the years of algorithmic progress that would be needed to achieve this same reduction ∆L.

In particular, the optimization problem is

min
δ∈R+

f (δ),

(10)

where we have
(cid:12) exp[α′

f = (cid:12)

const − αyear(Y + δ − Y0) − αparam log(N/N0)]

(11)
. Here δ can be interpreted as a doubling time for effective compute due to algorithmic progress in pre-training.
α′
const = αconst + αconst,PTBxPTB + αconst,WT2xWT2 and β′
const = βconst + βconst,PTBxPTB + βconst,WT2xWT2, where
xPTB and xWT2 are dummy variables for PTB and WT2 respectively.

const − βyear(Y + δ − Y0) − βdata log(D/D0)] − L2

+ exp[β′

(cid:12)
(cid:12)

We apply this approach over 100 bootstraps of our dataset, yielding a median doubling time of 8.6 months, and a 95%
confidence interval of 4.5 to 14.5 months. This is very similar to the doubling times estimated using the closed-form
approach discussed in section 3.1.

H Irreducible loss

Our main model for estimating doubling times does not estimate the irreducible loss. This is in part due to empirical
difficulties encountered in estimating plausible values for this term, and in part because the inclusion of this term does
not have a bearing on our estimates of the rate of algorithmic improvements. Since the latter is the focus of our paper,
we decided to move forward with the outlined model without irreducible loss estimates. However, we caution against
overinterpretation of these results—for instance, our parameter estimates are not reliable enough to strongly inform how
to scale models compute-optimally (although they can be somewhat illustrative).

The focus of this section is to justify the robustness of our core doubling time results to this omitted variable in our
model. In particular, we fit a model which incorporates estimates of the irreducible loss and show that the doubling
times remain in line with our previous findings. The model we consider is

ˆL = γ′ + exp(α′

const − αyear(Y − Y0) − αparam log N/N0) + exp(β′

(12)
where γ′ = γ + γP T BxP T B + γW T 2xW T 2, and the rest of the model is defined in the same way as in Section 3.1.
When we fit this model, we obtain a compute efficiency doubling time of 8.8 months, with a 95% confidence interval of
4.2 to 18.7 months, consistent with the estimates from our primary model. Our core parameter estimates are shown in
Table 8.

const − βyear(Y − Y0) − βdata log D/D0),

20

Estimate

95% CI

γ

γPTB

γWT2

αconst

αconst,PTB

αconst,WT2

αyear

αparam

βconst

βconst,PTB

βconst,WT2

βyear

βdata

−0.000
(0.072)
0.105
(0.100)
−0.044
(0.154)
∗
0.934
(0.250)
0.001
(0.056)
0.147
(0.128)
0.008
(0.022)
∗
0.068
(0.020)
∗
0.763
(0.253)
0.118
(0.100)
0.001
(0.135)
0.032
(0.024)
∗
0.040
(0.014)

−0.006, 0.250

−0.002, 0.356

−0.520, 0.004

0.000, 1.318

−0.041, 0.146

−0.066, 0.392

−0.062, 0.038

0.043, 0.132

0.001, 1.278

−0.003, 0.324

−0.173, 0.346

−0.010, 0.075

0.021, 0.075

Table 8: Parameter estimates from the model described in equation 12, reported to 3 decimal places. We report 95% confidence
intervals for all of the parameter estimates by bootstrapping 100 iterations. * corresponds to a p value below 5%.

I Autocorrelation

Our dataset was constructed by searching for papers with models that reported perplexity data on WT103, PTB, or
WT2. In our initial data collection, we sometimes also included multiple models originating from the same paper. In
some extreme instances, more than ten models from a single paper were included; for example, we incorporated 14
models from the paper "OPT: Open Pre-trained Transformer Language Models." This poses concerns of autocorrelation,
which might for instance result in us underestimating the uncertainty in our individual parameter estimates.

In the main body of the paper we approached this issue by retaining only three models per paper in our analysis,
which resulted in the exclusion of approximately 35 models. Here we consider an alternative approach for addressing
autocorrelation, where we explicitly quantify the correlations between models from the same paper. We then use this
information to establish a multivariate normal likelihood function, which we maximize to obtain parameter estimates.

First, let us define the residuals as ϵ = x − ˆx. The original loss function that we are using is the mean squared error,
i.e. where the loss is given by E[ϵT ϵ]. We want to modify our approach so that we take into account the correlations
between different datapoints. The approach we take is to take an approach similar to generalized least squares and
multiplicative attention—rather than consider just ϵT ϵ, we consider ϵT P ϵ, where P is a correlation matrix.
We do this using a maximum-likelihood approach, where ϵT Σϵ placed in a multivariate normal distribution, given by

f (ϵ; θ) =

1
(cid:112)(2π)k det(Σ)

(cid:18)

exp

−

1
2

ϵT Σ−1ϵ

(cid:19)

,

(13)

where Σ is a covariance matrix for the data. Our goal is to choose the appropriate parameters θ such that the resulting
ϵ = x − ¯x maximizes this distribution. This includes the original parameters in the model from equation 3 as well as
the correlation ρ between models from the same paper. We define the loss function as the negative of the logarithm of
this distribution (dropping constants which do not matter for the resulting minimization problem):

l(θ) =

1
2

log det Σ +

1
2

ϵT Σ−1ϵ.

(14)

In order to apply this to our data we need to specify the structure of the covariance matrix Σ = σ2nP (and thus
Σ−1 = σ−2nP −1. We can accordingly write the loss function as

l(θ) =

1
2

log det P +

n
2

log σ2 +

1
2σ2n ϵT P −1ϵ.

(15)

21

We are assuming that the models from different papers are uncorrelated, and that different models from the same
paper have a correlation coefficient of ρ. If we order the models such that all the models from the same paper form a
contiguous range of indices, then the correlation matrix looks block diagonal, where each block has 1s on the diagonal
and ρ for the off-diagonal terms. The matrix elements that are not in blocks are all zero. For example, one example
correlation matrix is:












0
0

0
0

0
1 ρ 0
0
ρ 1
0
0
0
1 ρ ρ ρ
0 ρ 1 ρ ρ
0
0 ρ ρ 1 ρ
0
0 ρ ρ ρ 1
0








(16)

As we can see, we need to determine both the inverse and the determinant of the correlation matrix P in order to calculate
the negative log-likelihood. While this can be done using standard libraries, the matrices that we are considering here
are quite sparse, and thus it is more efficient to simplify our calculations here. We detail the calculations in sections I.2
and I.3.

I.1 Results

To determine confidence intervals, we bootstrap this model based on clustering over 100 iterations, in similar fashion
to the main results. This yields a median doubling time of 8.1 months, with a 95% confidence interval of 2.9 to 13.8
months, which is consistent with our core estimates. In practice ρ is typically on the order of 0.45, which suggests that
the degree of autocorrelation is not very strong. We report our parameter estimates in Table 9.

Estimate

95% CI

αconst

αconst,PTB

αconst,WT2

αyear

αparam

βconst

βconst,PTB

βconst,WT2

βyear

βdata

0.839
(0.691)
−0.069
(0.378)
0.742
(0.390)
0.026
(0.065)
∗
0.076
(0.040)
∗
0.861
(0.429)
0.191
(0.304)
−1.081
(0.881)
0.016
(0.027)
∗
0.031
(0.009)

−1.181, 1.307

−0.684, 0.801

0.049, 1.553

−0.160, 0.034

0.064, 0.203

0.117, 1.559

−0.232, 0.873

−3.092, 0.168

0.005, 0.095

0.018, 0.043

Table 9: Parameter estimates from the model described in equation 8, but estimated using the clustering approach described in
equation 15. Estimates are rounded to 3 decimal places. We report 95% confidence intervals for all of the parameter estimates by
bootstrapping 100 iterations. * corresponds to a p value below 5%.

I.2 Determinant
In order to obtain the overall determinant for P we first work this out for a single block. In particular, the determinant
of each (n + 1) × (n + 1) block Bn is given by

We prove this by considering the associated matrix directly:

det Bn+1 = (1 − ρ)n(1 + nρ).

Bn+1 =









1 ρ . . . ρ ρ
. . . ρ ρ
ρ 1
...
...
. . .
ρ ρ . . .
1 ρ
ρ ρ . . . ρ 1









22

(17)

(18)

Since det Bn+1 is unchanged under the elementary row operation of adding a multiple of one row to another, we write

det Bn+1 =

det
(n+1)×(n+1)

ρ
1 − ρ2


1
0

...



0 ρ − ρ2

0 ρ − ρ2

ρ

. . .
. . . ρ − ρ2
. . .
1 − ρ2
. . .
. . . ρ − ρ2









ρ
ρ − ρ2
...
ρ − ρ2
1 − ρ2

.

We can thus simplify the determinant as

det Bn+1 = (1 − p)n det
n×n









1 + ρ
ρ
...
ρ
ρ

ρ

ρ
ρ

. . .
1 + ρ . . .
. . .
. . . 1 + ρ
. . .

ρ
ρ

ρ









ρ
ρ
...
ρ
1 + ρ

.

(19)

(20)

To evaluate the determinant of this matrix we follow a similar procedure, where we eliminate most of the elements
in the first column. We then repeat this process as the resulting matrix becomes smaller and smaller, until we reach a
trivial case. The kth step in this iterative procedure has the following structure (where k = 0, 1, . . . , n − 1, n):




det Bn+1 = (1 − p)n(1 + kρ)

det
(n−k)×(n−k)










...

1+(k+1)ρ
1+kρ
ρ
1+kρ

ρ
1+kρ
1+(k+1)ρ
1+kρ

ρ
1+kρ
ρ
1+kρ

ρ
1+kρ
ρ
1+kρ

ρ
1+kρ
ρ
1+kρ

1+(k+1)ρ
1+kρ
ρ
1+kρ

ρ
1+kρ
1+(k+1)ρ
1+kρ

ρ
1+kρ
ρ
1+kρ

...










(21)

. . .
. . .
. . .
. . .
. . .

ρ

1+(k+1)ρ times the first row from all other rows. In the first column, all except the first row thus
We now substract
becomes zeros, and there are two main cases we need to consider for the other elements. In the first case, for diagonal
elements, we have we have

1 + (k + 1)ρ
1 + kρ

−

ρ
1 + kρ

ρ
1 + (k + 1)ρ

=

=

[1 + (k + 1)ρ]2 − ρ2
[1 + kρ][1 + (k + 1)ρ]
1 + (k + 2)ρ
1 + (k + 1)ρ

.

In the second case, for off-diagonal elements, we instead have

ρ
1 + kρ

−

ρ
1 + kρ

ρ
1 + (k + 1)ρ

=

=

Thus we have that

det Bn+1 = (1 − p)n(1 + kρ)

det
(n−k)×(n−k)












1+(k+1)ρ
1+kρ
0
...
0

0

(cid:20) 1 + (k + 1)ρ − ρ
1 + (k + 1)ρ

(cid:21)

ρ
1 + kρ
ρ
1 + (k + 1)ρ

.

. . .
. . .
. . .

ρ
1+kρ
ρ
1+(k+1)ρ

ρ
1+kρ
1+(k+2)ρ
1+(k+1)ρ

ρ
1+(k+1)ρ
ρ
1+(k+1)ρ

1+(k+2)ρ
1+(k+1)ρ
. . .

ρ
1+(k+1)ρ
ρ
1+(k+1)ρ

(22)

(23)

(24)

(25)

(26)












ρ
1+kρ
ρ
1+(k+1)ρ

...

1+(k+2)ρ
1+(k+1)ρ

= (1 − p)n(1 + (k + 1)ρ)

det
(n−(k+1))×(n−(k+1)












ρ
1+(k+1)ρ
1+(k+2)ρ
1+(k+1)ρ

1+(k+2)ρ
1+(k+1)ρ
ρ
1+(k+1)ρ

...

ρ
1+(k+1)ρ
ρ
1+(k+1)ρ

ρ
1+(k+1)ρ
ρ
1+(k+1)ρ

. . .

. . .
. . .
. . .

. . .

ρ
1+(k+1)ρ
ρ
1+(k+1)ρ

ρ
1+(k+1)ρ
ρ
1+(k+1)ρ

...

1+(k+2)ρ
1+(k+1)ρ
ρ
1+(k+1)ρ

ρ
1+(k+1)ρ
1+(k+2)ρ
1+(k+1)ρ












.

(27)

23

If we repeat this argument n times (going from an (n + 1) × (n + 1) matrix to the trivial case of a n × n matrix, then
we conclude that

det Bn+1 = (1 − ρ)n(1 + nρ),
(28)
as desired. Now to work out the overall determinant of P , we simply have to multiply the determinants of the individual
blocks, and we are done.

I.3 Inverse
2σ2n ϵT P −1ϵ. One way to reduce the computational cost of this
We now want to determine the third term in l(θ), i.e.
calculation is to take advantage of P being block diagonal, where the inverse P −1 can be determined by inverting the
individual blocks. That is, for blocks Bi the inverse of the correlation matrix is

1

P −1 =










B−1
1
0
...
0
0

0
B−1
2

0
0

0
0

. . .
. . .
. . .
. . . B−1
n−1
0
. . .










0
0
...
0
B−1
n

.

To invert a single block B, first observe that each block B is such that the elements are

Bij =

(cid:26)1

if i = j,
ρ otherwise.

(29)

(30)

Now let D be the diagonal matrix with diagonal entries Dii = 1 − ρ. Then we have that B = D + ρvvT , where v is a
vector of ones. We can now calculate the inverse B−1 by application of the Sherman-Morrison formula. In particular
we have

B−1 = (D + ρvvT )−1 = D−1 −

.

(31)

ρD−1vvT D−1
1 + ρvT D−1v

Since the inverse of D is just D−1
c = 1
1−ρ . We then have

ρ + n

ii = 1

1−ρ , assuming that the correlation ρ ̸= 1. To simplify notation, we define

B−1

ij =

(cid:40) 1

1−ρ − 1
− 1
c(1−ρ)2

c(1−ρ)2

i = j
i ̸= j

,

(32)

and calculating the associated quadratic form 1

2σ2n ϵT P −1ϵ follows trivially.

J Cross validation for model choice

We determined our primary model for estimating doubling times using formal model selection procedures. In par-
ticular, we considered a range of 15 candidate model numbers and a range of possible regularization strengths
δ ∈ {0, 0.001, 0.0025, 0.005, 0.01, 0.02}. We consider each “model" as a pair, consisting of a particular model number
and a regularization strength δ. We then perform leave-one-out cross validation on all of these models. Here we show
the results of this analysis.

Our candidate models are defined by varying three degrees of freedom:

1. Which parameters to make benchmark-specific (e.g. having three separate parameters for the exponent on

training dataset size, one for each of WT103, PTB and WT2).

2. Whether to explicitly model algorithmic progress in parameters N , data D, or both.

In general we do not include the irreducible loss in the model (i.e. we usually set E = 0, in the equation 3)—this
is described in more detail in section H. In Table 10 we list the definitions of all models that we looped through in
leave-one-out cross validation. For this, we first define some common terms for simplication:

24

α′

const = αconst + αconst,PTBxPTB + αconst,WT2xWT2

α′

year = αyear + αyear,PTBxPTB + αyear,WT2xWT2

α′

param = αparam + αparam,PTBxPTB + αparam,WT2xWT2

β′
const = βconst + βconst,PTBxPTB + βconst,WT2xWT2

β′
year = βyear + βyear,PTBxPTB + βyear,WT2xWT2

β′
data = βdata + βdata,PTBxPTB + βdata,WT2xWT2

α∗

param = αparam,NT(1 − xT ) + αparam,TxT

β∗
data = βdata,NT(1 − xT ) + βdata,TxT

α†

param = αparam + αrate log Y

β†
data = βdata + βrate log Y

Here xPTB, xWT2, and xT are dummy variables for PTB, WT2, and the transformer respectively. Y is the year, and αrate
and βrate are constants that determine how quickly scaling exponents (αparam and βdata) change over time.

Models 1 to 11 are all constructed using a similar set of rules:

• αconst and βconst determine the coefficients of the parameter and data reducible loss terms respectively

• αyear and βyear capture algorithmic progress in parameters and data

• αparam and βdata determine the scaling behavior with respect to N and D respectively

All of these parameters may be set as benchmark-specific (e.g. by writing α′

const in lieu of αconst).

The remaining models are defined using a different set of rules:

• Model 12 is defined in similar fashion but in ‘Hicks-neutral’ fashion, such that the same degree of efficiency

gain is seen across both parameters and data.

• Model 13 models different scaling exponents αparam and βdata for transformer vs non-transformer models

• Model 14 captures only algorithmic progress via changes in the scaling exponents α†

param and β†

data

• Model 15 captures algorithmic progress via αyear and βyear, as well as changes in the scaling exponents

• Models 16 and 17 do not capture algorithmic progress, and are used as a baseline for goodness-of-fit com-
parisons. Model 16 is modeled off equation 34, and model 17 modifies this to include transformer-specific
scaling exponents. This is described in more detail in Appendix J.2

• Model 18 is a model that only considers the total compute, via the approximation C = 6N D. This is discussed

in more detail in Appendix J.1.

• Model 19 includes a term that accounts for different vocabulary sizes. We discuss this in Appendix E.2.2.

• Model 20 is the same as model 7, but rather than using purely the training dataset size, it defines “training
data" in a way that accounts for the number of epochs of training. Where the number of training epochs is
unknown, we impute an epoch count of 1. This model is presented in more detail in Appendix F.

We chose to include models 16 to 20 in the cross validation analysis to help the robustness checks performed in different
appendices.

25

No.

Model specification

Table 10: Model specifications for leave-one-out cross validation.

1

2

3

4

5

6

7

8

9

10

11

12

13

14

15

16

17

18

19

20

Algorithmic progress in both N and D
L = exp[αconst − αyear(Y − Y0) − αparam(log N − log N0)] + exp[βconst − βyear(Y − Y0) − βdata(log D − log D0)]
No algorithmic progress in parameters N
L = exp[αconst − αparam(log N − log N0)] + exp[βconst − βyear(Y − Y0) − βdata(log D − log D0)]
No algorithmic progress in data D
L = exp[αconst − αyear(Y − Y0) − αparam(log N − log N0)] + exp[βconst − βdata(log D − log D0)]
Benchmark-specific in αyear
L = exp[αconst − α′
Benchmark-specific in βyear
L = exp[αconst − αyear(Y − Y0) − αparam(log N − log N0)] + exp[βconst − β′
Benchmark-specific in αyear and βyear
L = exp[αconst − α′
Benchmark-specific in αconst and βconst
L = exp[α′

year(Y − Y0) − αparam(log N − log N0)] + exp[βconst − βyear(Y − Y0) − βdata(log D − log D0)]

year(Y − Y0) − αparam(log N − log N0)] + exp[βconst − β′

const − αyear(Y − Y0) − αparam(log N − log N0)] + exp[β′

const − βyear(Y − Y0) − βdata(log D − log D0)]

year(Y − Y0) − βdata(log D − log D0)]

year(Y − Y0) − βdata(log D − log D0)]

Benchmark-specific in αconst and βconst, with no algorithmic progress in N
L = exp[α′

const − αparam(log N − log N0)] + exp[β′

const − βyear(Y − Y0) − βdata(log D − log D0)]

Benchmark-specific in αconst and βconst, with no algorithmic progress in D
L = exp[α′

const − αyear(Y − Y0) − αparam(log N − log N0)] + exp[β′

const − βdata(log D − log D0)]

Benchmark-specific in αconst, αyear, βconst, βyear
L = exp[α′

year(Y − Y0) − αparam(log N − log N0)] + exp[β′

const − α′

const − β′

year(Y − Y0) − βdata(log D − log D0)]

Benchmark-specific in αconst, αyear, αparam, βconst, βyear and βdata
L = exp[α′

param(log N − log N0)] + exp[β′

year(Y − Y0) − α′

const − α′

const − β′

year(Y − Y0) − β′

data(log D − log D0)]

‘Hicks-neutral’ model
L = (exp[α′

const + αparam(log N − log N0)] + exp[β′

const + βdata(log D − log D0)]) exp[−αyear(Y − Y0)]

Transformer vs non-transformer scaling
L = exp[α′

const − αyear(Y − Y0) − α∗
Progress only via changing scaling exponents
L = exp[α′

const − α†

param(log N − log N0)] + exp[β′

const − β†

data(log D − log D0)]

param(log N − log N0)] + exp[β′

const − βyear(Y − Y0) − β∗

data(log D − log D0)]

Changing αyear, βyear, αparam, and βdata
const − αyear(Y − Y0) − α†
L = exp[α′

param(log N − log N0)] + exp[β′

const − βyear(Y − Y0) − β†

data(log D − log D0)]

Benchmark-specific Hoffmann et al. 2022 scaling law (for comparison only)
L = exp[α′

const − αparam(log N − log N0)] + exp[β′

const − βdata(log D − log D0)]

Transformer-specific scaling law (for comparison only)
L = exp[α′

param(log N − log N0)] + exp[β′

const − α∗

const − β∗

data(log D − log D0)]

Compute-only model (for comparison only)
L = exp[α′

const − αyear(Y − Y0) − αcompute(log(6N D) − log(6N0D0)]

Vocabulary fixed-effects (for comparison only)
L = γ log(vocab) + exp[α′
βdata(log D − log D0)]
Same as model 7 but with imputed epochs (for comparison only)
L = exp[α′

const − αyear(Y − Y0) − αparam(log N − log N0)] + exp[β′

const − αyear(Y − Y0) − αparam(log N − log N0)] + exp[β′

const − βyear(Y − Y0) −

const − βyear(Y − Y0) − βdata(log D − log D0)]

26

J.1 Compute-only model
Given that our core focus is on estimating doubling times in effective compute, one natural parameterization is to
directly consider total training compute C, in particular,

L = γ′ + exp[α′

(33)
Here γ′ is defined similarly to the “primed" constants above, i.e. γ′ = γ + γPTBxPTB + γWT2xWT2, and we have the
approximate relation that C ≈ 6N D (Hoffmann et al. 2022). However, this model has a tendency to yield implausible
results, in particular with a very small scale exponent αcompute and a very short effective compute doubling time (on the
order of 1-5 months).

const − αyear(Y − Y0) − αcompute(log C − log C0)].

We omit this model because we believe there are two reasons to expect this model to be strongly misspecified. The first
reason is that the model scaling does not accurately reflect complementarities between scaling parameter and data. For
illustration, compare the following two equations:

L = E +

A
N α +

B
Dβ

(34)

L = E +

A
(6N D)α

A
C α = E +
where E is the irreducible loss, and A, B, α, β are constants. In equation 34, reductions to the loss are bottlenecked by
a lack of sufficient data D. This bottleneck does not exist in the case of 35, where scaling N arbitrarily would bring
you to the irreducible loss E. This model thus unrealistically suggests equivalent performance between a 1-parameter
model trained on 1024 tokens, and a 1012 parameter model trained on 1012 tokens. Of course, such extreme choices of
parameters N and dataset size D are implausible in practice, but nevertheless we do see clear variation in how these
values are chosen in practice. For instance, Figure 12 shows a plot log10(N/D) for models across different years,
spanning over five orders of magnitude over this time period. This is in spite of the estimate by Hoffmann et al. 2022
that N/D should be O(1) for compute-optimal training.

(35)

Figure 12: Ratio of parameters N to dataset size D for models in our dataset. We emphasize the ratios corresponding to GPT-3
(T. B. Brown et al. 2020) and Chinchilla models (Hoffmann et al. 2022), which are of historical importance in determining how to
choose this ratio when scaling language models.

A second way in which equation 33 is misspecified is due to its unrealistic scaling behavior. To see why this is the case,
we compare the difference between the reducible loss terms in equations 34 and 35, by writing them as a single fraction
with the same denominator (N D)α. For illustration purposes, we also assume that α = β and A = B, which simplify
our argument without changing the core conclusion. If we then factor out the coefficient A, we then have that

1
N α +
1
(6N D)α =
where LH is the loss predicted from the scaling law in Hoffmann et al. 2022, and LC is the loss from only considering
compute. Here we observe that in the case of Chinchilla-scaling (equation 36), as N or D is increased the value of

6−α
(N D)α ,

1
Dα =

N α + Dα
(N D)α

LH ∝

LC ∝

(37)

(36)

27

Tokens per parameter D/N

Chinchilla

GPT-3

102

101

100

10 1

10 2

10 3

2012

2014

2016

2018

2020

2022

2024

Publication date

the numerator increases, whereas the opposite is true in the compute-only case (equation 37). As a result, fits of the
compute-only model tend to have very small values of α, since the difference in scaling behaviour between the two
expressions tends to be more pronounced for larger values of α. Indeed, estimates using the compute-only model yield
very small values of α, at 0.004 with a 95% CI of [0.002, 0.012]. We illustrate the difference between the scaling
behavior of equations 36 and 37 in Figure 13.

Figure 13: Comparing the scaling behavior of equations 36 and 37, for α = 0.01, 0.05 and 0.3. For illustration, we choose N = D,
and normalize both expressions to equal 1 when the number of parameters N = 106. The difference between the scaling laws
is smallest when α is set to a smaller value—this is illustrated by the double-headed arrow in each plot, showing the largest gap
between the two curves.

We nevertheless test the compute-only model in cross validation and find that it performs very poorly on out-of-sample
prediction, far worse than any of the other models that we consider. The results of this exercise are elaborated upon in
section J.3.

J.2 Algorithmic progress through changes in the scale exponents αparam and βdata

As mentioned in Section 2.1, the final model that we use for our core results does not explicitly account for efficiency
improvements through changes in scaling exponents (i.e. αparam and βdata). The primary reason for our decision is that
while this form of algorithmic progress is theoretically plausible, our model fits to the available data suggest that this
effect has not been very large. For example, if we consider the estimates from model 15, which includes both the form
of algorithmic progress described in Section 2.1 and improvements through changes in scaling exponents, we find that
the overall contribution to algorithmic progress is dominated by the former.

Another piece of supporting evidence is that in cross validation, model 14 appears to perform roughly as well as models
without any algorithmic progress at all (models 16 and 17). Furthermore, the parameters which determine the rate
of changing scale exponents (αrate and βrate) are generally very small (around 0.001 to 0.01). As such, the model
appears to simply be approximating the equivalent models without algorithmic progress. This suggests that this form of
algorithmic progress is negligible, and is also why we have excluded model 14 from Figure 3.

J.3 Performance metrics

In this section we list the resulting goodness-of-fit metrics from our cross validation analysis. In this case we report the
average out-of-sample MSE loss.

28

Normalized value

Chinchilla

Compute-only

1.0

0.8

0.6

0.4

0.2

0.0

 =0.01

 =0.05

 =0.3

106

107

108

109

1010

1011

1012

106

107

108

109

1010

1011

1012

106

107

108

109

1010

1011

1012

Parameters

Model/δ-value

0

0.001

0.0025

0.005

0.01

0.02

1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20

0.05304
0.05371
0.05294
0.05118
0.05011
0.05034
0.05049
0.05006
0.0505
0.04964
0.05281
0.04946
0.05227
0.06314
0.05068
0.06599
0.06427
0.72048
0.05117
0.05095

0.05309
0.0537
0.0529
0.0512
0.0501
0.05021
0.05028
0.04953
0.04996
0.04848
0.05186
0.04997
0.05267
0.06377
0.04975
0.06663
0.06472
0.72084
0.05009
0.05045

0.05308
0.05393
0.05262
0.05114
0.05004
0.05018
0.04856
0.04975
0.05097
0.049
0.05196
0.04939
0.0507
0.0652
0.04937
0.06701
0.06537
0.72198
0.05019
0.05018

0.05295
0.05852
0.05249
0.05134
0.05015
0.0503
0.04952
0.0487
0.05042
0.04913
0.0523
0.0492
0.05028
0.06359
0.04884
0.06486
0.06475
0.72421
0.04969
0.05009

0.05281
0.0586
0.05235
0.05227
0.05007
0.05049
0.04892
0.05208
0.04963
0.05009
0.05101
0.05012
0.05005
0.06302
0.04862
0.06431
0.06421
0.72828
0.04902
0.04939

0.05231
0.05921
0.05222
0.05199
0.05113
0.05162
0.0492
0.0525
0.04925
0.05105
0.05127
0.04897
0.05018
0.06336
0.04921
0.0631
0.06411
0.73591
0.04859
0.0498

Table 11: Average mean squared error test loss of all model-δ combinations from cross validation. δ-values here are the
regularization term in the L1 regularization set-up.

References

Alon, Uri et al. (2022). “Neuro-symbolic language modeling with automaton-augmented retrieval”. In: International

Conference on Machine Learning. PMLR, pp. 468–485.

Baevski, Alexei and Michael Auli (2018). “Adaptive Input Representations for Neural Language Modeling”. In: DOI:

10.48550/ARXIV.1809.10853. URL: https://arxiv.org/abs/1809.10853.

Bixby, Robert E (2012). “A brief history of linear and mixed-integer programming computation”. In: Documenta

Mathematica 2012, pp. 107–121.

Brown, Tom B. et al. (2020). “Language Models are Few-Shot Learners”. In: DOI: 10.48550/ARXIV.2005.14165.

URL: https://arxiv.org/abs/2005.14165.

Chowdhery, Aakanksha et al. (2023). “Palm: Scaling language modeling with pathways”. In: Journal of Machine

Learning Research 24.240, pp. 1–113.

Cobbe, Karl et al. (2021). “Training Verifiers to Solve Math Word Problems”. In: DOI: 10.48550/ARXIV.2110.14168.

URL: https://arxiv.org/abs/2110.14168.

Dao, Tri et al. (2022). “FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness”. In: ArXiv

abs/2205.14135. URL: https://api.semanticscholar.org/CorpusID:249151871.

Davidson, Tom (2023). What a compute-centric framework says about AI takeoff speeds. https : / / www .
alignmentforum.org/posts/Gc9FGtdXhK9sCSEYu/what-a-compute-centric-framework-says-about-
ai-takeoff.

Davidson, Tom et al. (2023). “AI capabilities can be significantly improved without expensive retraining”. In: arXiv

preprint arXiv:2312.07413.

Dorner, Florian E (2021). “Measuring progress in deep reinforcement learning sample efficiency”. In: arXiv preprint

arXiv:2102.04881.

Droppo, Jasha and Oguz H. Elibol (2021). “Scaling Laws for Acoustic Models”. In: Interspeech. URL: https :

//api.semanticscholar.org/CorpusID:235458551.

Erdil, Ege and Tamay Besiroglu (2022). “Algorithmic progress in computer vision”. In: DOI: 10.48550/ARXIV.2212.

05153. URL: https://arxiv.org/abs/2212.05153.

Fichte, Johannes K, Markus Hecher, and Stefan Szeider (2020). “A time leap challenge for SAT-solving”. In: Interna-

tional Conference on Principles and Practice of Constraint Programming. Springer, pp. 267–285.

Gao, Leo, Stella Biderman, et al. (2020). “The Pile: An 800GB dataset of diverse text for language modeling”. In: arXiv

preprint arXiv:2101.00027.

29

Gao, Leo, Jonathan Tow, et al. (2021). “A framework for few-shot language model evaluation”. In: Version v0. 0.1. Sept.
Gemini Team, Google (2024). “Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context”.

In: URL: https://storage.googleapis.com/deepmind-media/gemini/gemini_v1_5_report.pdf.

Gu, Albert and Tri Dao (2023). “Mamba: Linear-Time Sequence Modeling with Selective State Spaces”. In: ArXiv

abs/2312.00752. URL: https://api.semanticscholar.org/CorpusID:265551773.

Gunasekar, Suriya et al. (2023). “Textbooks Are All You Need”. In: arXiv preprint arXiv:2306.11644.
Hernandez, Danny and Tom Brown (2020). “Measuring the algorithmic efficiency of neural networks”. In: arXiv

preprint arXiv:2005.04305.

Hoffmann, Jordan et al. (2022). “Training Compute-Optimal Large Language Models”. In: arXiv preprint

arXiv:2203.15556.

Huang, Jie and Kevin Chen-Chuan Chang (2022). “Towards Reasoning in Large Language Models: A Survey”. In:

arXiv preprint arXiv:2212.10403.

Hugging Face (2023). Perplexity of fixed-length models. https : / / huggingface . co / docs / transformers /

perplexity. [Online; accessed 14-Nov-2023].

Jing, Kun and Jungang Xu (2019). “A survey on neural network language models”. In: arXiv preprint arXiv:1906.03591.
Kaddour, Jean et al. (2023). “Challenges and applications of large language models”. In: arXiv preprint

arXiv:2307.10169.

Kaplan, Jared et al. (2020). “Scaling laws for neural language models”. In: arXiv preprint arXiv:2001.08361.
Karpathy, Andrej (2022). Deep Neural Nets: 33 years ago and 33 years from now. http://karpathy.github.io/

2022/03/14/lecun1989/. [Online; accessed 21-July-2022].

Koch, Thorsten et al. (2022). “Progress in mathematical programming solvers from 2001 to 2020”. In: EURO Journal

on Computational Optimization 10, p. 100031.

Leblond, Rémi et al. (2023). AlphaCode 2 Technical Report. Tech. rep. Google DeepMind. URL: https://storage.

googleapis.com/deepmind-media/AlphaCode2/AlphaCode2_Tech_Report.pdf.

LeCun, Yann et al. (1989). “Backpropagation applied to handwritten zip code recognition”. In: Neural computation 1.4,

pp. 541–551.

Li, Yujia et al. (2022). “Competition-level code generation with alphacode”. In: arXiv preprint arXiv:2203.07814.
Liu, Hao et al. (2024). “World Model on Million-Length Video And Language With RingAttention”. In: ArXiv

abs/2402.08268. URL: https://api.semanticscholar.org/CorpusID:267637090.

Marion, Max et al. (2023). “When less is more: Investigating data pruning for pretraining llms at scale”. In: arXiv

preprint arXiv:2309.04564.

Merity, Stephen et al. (2016). “Pointer sentinel mixture models”. In: arXiv preprint arXiv:1609.07843.
Mialon, Grégoire et al. (2023). “Augmented language models: a survey”. In: arXiv preprint arXiv:2302.07842.
Muennighoff, Niklas et al. (2023). “Scaling Data-Constrained Language Models”. In: ArXiv abs/2305.16264. URL:

https://api.semanticscholar.org/CorpusID:258888192.

OpenAI (2023). “GPT-4 Technical Report”. In: URL: https://cdn.openai.com/papers/gpt-4.pdf.
Patel, Dylan and Gerald Wong (2023). GPT-4 Architecture, Infrastructure, Training Dataset, Costs, Vision, MoE. URL:

https://www.semianalysis.com/p/gpt-4-architecture-infrastructure.
Radford, Alec et al. (2019). “Language Models are Unsupervised Multitask Learners”. In.
Rae, Jack W. et al. (2021). “Scaling Language Models: Methods, Analysis & Insights from Training Gopher”. In: DOI:

10.48550/ARXIV.2112.11446. URL: https://arxiv.org/abs/2112.11446.

Sevilla, Jaime et al. (2022). Estimating training compute of Deep Learning models. Tech. rep.
Shazeer, Noam (2019). “Fast

transformer decoding: One write-head is all you need”. In: arXiv preprint

arXiv:1911.02150.

Sherry, Yash and Neil C Thompson (2021). “How fast do algorithms improve?[point of view]”. In: Proceedings of the

IEEE 109.11, pp. 1768–1777.

Sorscher, Ben et al. (2022). “Beyond neural scaling laws: beating power law scaling via data pruning”. In: Advances in

Neural Information Processing Systems 35, pp. 19523–19536.

Sun, Kaili, Xudong Luo, and Michael Y Luo (2022). “A survey of pretrained language models”. In: Knowledge
Science, Engineering and Management: 15th International Conference, KSEM 2022, Singapore, August 6–8, 2022,
Proceedings, Part II. Springer, pp. 442–456.

Takase, Sho, Jun Suzuki, and Masaaki Nagata (2018). “Direct Output Connection for a High-Rank Language Model”.

In: ArXiv abs/1808.10143. URL: https://api.semanticscholar.org/CorpusID:52138320.

Tay, Yi et al. (2022). “Scaling Laws vs Model Architectures: How does Inductive Bias Influence Scaling?” In: ArXiv

abs/2207.10551. URL: https://api.semanticscholar.org/CorpusID:250920512.

30

Taylor, Ann, Mitchell Marcus, and Beatrice Santorini (2003). “The Penn treebank: an overview”. In: Treebanks: Building

and using parsed corpora, pp. 5–22.

Trinh, Trieu H et al. (2024). “Solving olympiad geometry without human demonstrations”. In: Nature 625.7995,

pp. 476–482.

Vaswani, Ashish et al. (2017). “Attention is All you Need”. In: ArXiv abs/1706.03762.
Vries, Harm de (2023). In the long (context) run. URL: https://www.harmdevries.com/post/context-length/.
Wang, Chenguang, Mu Li, and Alexander J Smola (2019). “Language models with transformers”. In: arXiv preprint

arXiv:1904.09408.

Xiong, Wenhan et al. (2023). “Effective Long-Context Scaling of Foundation Models”. In: ArXiv abs/2309.16039. URL:

https://api.semanticscholar.org/CorpusID:263134982.

Zhao, Wayne Xin et al. (2023). “A survey of large language models”. In: arXiv preprint arXiv:2303.18223.

31

