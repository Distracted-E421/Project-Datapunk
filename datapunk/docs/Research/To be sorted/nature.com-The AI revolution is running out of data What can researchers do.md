The AI revolution is running out of data. What can
researchers do?

nature.com/articles/d41586-024-03990-2

Illustration: Adrià Voltà

AI developers are rapidly picking the Internet clean to train large language models such as
those behind ChatGPT. Here’s how they are trying to get around the problem.

The Internet is a vast ocean of human knowledge, but it isn’t infinite. And artificial intelligence
(AI) researchers have nearly sucked it dry.

The past decade of explosive improvement in AI has been driven in large part by making
neural networks bigger and training them on ever-more data. This scaling has proved
surprisingly effective at making large language models (LLMs) — such as those that power
the chatbot ChatGPT — both more capable of replicating conversational language and of
developing emergent properties such as reasoning. But some specialists say that we are
now approaching the limits of scaling. That’s in part because of the ballooning energy
requirements for computing. But it’s also because LLM developers are running out of the
conventional data sets used to train their models.

1

A prominent study  made headlines this year by putting a number on this problem:
researchers at Epoch AI, a virtual research institute, projected that, by around 2028, the
typical size of data set used to train an AI model will reach the same size as the total
estimated stock of public online text. In other words, AI is likely to run out of training data in
about four years’ time (see ‘Running out of data’). At the same time, data owners — such as
newspaper publishers — are starting to crack down on how their content can be used,
tightening access even more. That’s causing a crisis in the size of the ‘data commons’, says
Shayne Longpre, an AI researcher at the Massachusetts Institute of Technology in
Cambridge who leads the Data Provenance Initiative, a grass-roots organization that
conducts audits of AI data sets.

The imminent bottleneck in training data could be starting to pinch. “I strongly suspect that’s
already happening,” says Longpre.

1/5

Although specialists say there’s a chance that these restrictions might slow down the rapid
improvement in AI systems, developers are finding workarounds. “I don’t think anyone is
panicking at the large AI companies,” says Pablo Villalobos, a Madrid-based researcher at
Epoch AI and lead author of the study forecasting a 2028 data crash. “Or at least they don’t
e-mail me if they are.”

For example, prominent AI companies such as OpenAI and Anthropic, both in San
Francisco, California, have publicly acknowledged the issue while suggesting that they have
plans to work around it, including generating new data and finding unconventional data
sources. A spokesperson for OpenAI, told Nature: “We use numerous sources, including
publicly available data and partnerships for non-public data, synthetic data generation and
data from AI trainers.”

2/5

Even so, the data crunch might force an upheaval in the types of generative AI model that
people build, possibly shifting the landscape away from big, all-purpose LLMs to smaller,
more specialized models.

Trillions of words

LLM development over the past decade has shown its voracious appetite for data. Although
some developers don’t publish the specifications of their latest models, Villalobos estimates
that the number of ‘tokens’, or parts of words, used to train LLMs has risen 100-fold since
2020, from hundreds of billions to tens of trillions.

In AI, is bigger always better?

That could be a good chunk of what’s on the Internet, although the grand total is so vast that
it’s hard to pin down — Villalobos estimates the total Internet stock of text data today at
3,100 trillion tokens. Various services use web crawlers to scrape this content, then eliminate
duplications and filter out undesirable content (such as pornography) to produce cleaner data
sets: a common one called RedPajama contains tens of trillions of words. Some companies
or academics do the crawling and cleaning themselves to make bespoke data sets to train
LLMs. A small proportion of the Internet is considered to be of high quality, such as human-
edited, socially acceptable text that might be found in books or journalism.

The rate at which usable Internet content is increasing is surprisingly slow: Villalobos’s paper
estimates that it is growing at less than 10% per year, while the size of AI training data sets is
more than doubling annually. Projecting these trends shows the lines converging around
2028.

At the same time, content providers are increasingly including software code or refining their
terms of use to block web crawlers or AI companies from scraping their data for training.
Longpre and his colleagues released a preprint this July showing a sharp increase in how
many data providers block specific crawlers from accessing their websites . In the highest-
quality, most-often-used web content across three main cleaned data sets, the number of
tokens restricted from crawlers rose from less than 3% in 2023 to 20–33% in 2024.

2

Several lawsuits are now under way attempting to win compensation for the providers of data
being used in AI training. In December 2023, The New York Times sued OpenAI and its
partner Microsoft for copyright infringement; in April this year, eight newspapers owned by
Alden Global Capital in New York City jointly filed a similar lawsuit. The counterargument is
that an AI should be allowed to read and learn from online content in the same way as a
person, and that this constitutes fair use of the material. OpenAI has said publicly that it
thinks The New York Times lawsuit is “without merit”.

3/5

If courts uphold the idea that content providers deserve financial compensation, it will make it
harder for both AI developers and researchers to get what they need — including academics,
who don’t have deep pockets. “Academics will be most hit by these deals,” says Longpre.
“There are many, very pro-social, pro-democratic benefits of having an open web,” he adds.

Finding data

The data crunch poses a potentially big problem for the conventional strategy of AI scaling.
Although it’s possible to scale up a model’s computing power or number of parameters
without scaling up the training data, that tends to make for slow and expensive AI, says
Longpre — something that isn’t usually preferred.

If the goal is to find more data, one option might be to harvest non-public data, such as
WhatsApp messages or transcripts of YouTube videos. Although the legality of scraping
third-party content in this manner is untested, companies do have access to their own data,
and several social-media firms say they use their own material to train their AI models. For
example, Meta in Menlo Park, California, says that audio and images collected by its virtual-
reality headset Meta Quest are used to train its AI. Yet policies vary. The terms of service for
the video-conferencing platform Zoom say the firm will not use customer content to train AI
systems, whereas OtterAI, a transcription service, says it does use de-identified and
encrypted audio and transcripts for training.

How cutting-edge computer chips are speeding up the AI
revolution

For now, however, such proprietary content probably holds
only another quadrillion text tokens in total, estimates
Villalobos. Considering that a lot of this is low-quality or
duplicated content, he says this is enough to delay the data
bottleneck by a year and a half, even assuming that a single
AI gets access to all of it without causing copyright
infringement or privacy concerns. “Even a ten times increase in the stock of data only buys
you around three years of scaling,” he says.

Another option might be to focus on specialized data sets such as astronomical or genomic
data, which are growing rapidly. Fei-Fei Li, a prominent AI researcher at Stanford University
in California, has publicly backed this strategy. She said at a Bloomberg technology summit
in May that worries about data running out take too narrow a view of what constitutes data,
given the untapped information available across fields such as health care, the environment
and education.

4/5

But it’s unclear, says Villalobos, how available or useful such data sets would be for training
LLMs. “There seems to be some degree of transfer learning between many types of data,”
says Villalobos. “That said, I’m not very hopeful about that approach.”

The possibilities are broader if generative AI is trained on other data types, not just text.
Some models are already capable of training to some extent on unlabelled videos or images.
Expanding and improving such capabilities could open a floodgate to richer data.

Yann LeCun, chief AI scientist at Meta and a computer scientist at New York University who
is considered one of the founders of modern AI, highlighted these possibilities in a
presentation this February at an AI meeting in Vancouver, Canada. The 10  tokens used to
train a modern LLM sounds like a lot: it would take a person 170,000 years to read that
much, LeCun calculates. But, he says, a 4-year-old child has absorbed a data volume 50
times greater than this just by looking at objects during his or her waking hours. LeCun
presented the data at the annual meeting of the Association for the Advancement of Artificial
Intelligence.

13

Nature 636, 290-292 (2024)

doi: https://doi.org/10.1038/d41586-024-03990-2

References

1. Villalobos, P. et al. Proc. Mach. Learn. Res. 235, 49523–49544 (2024).

Google Scholar 

2. Longpre, S. et al. Preprint at arXiv https://doi.org/10.48550/arXiv.2407.14933 (2024).

3. Trinh, T. H., Wu, Y., Le, Q. V., He, H. & Luong, T. Nature 625, 476–482 (2024).

Article  PubMed  Google Scholar 

4. Alemohammad, S. et al. Preprint at arXiv https://doi.org/10.48550/arXiv.2307.01850

(2023).

5. Ho, A. et al. Preprint at arXiv https://doi.org/10.48550/arXiv.2403.05812 (2024).

6. Muennighoff, N. et al. Preprint at arXiv https://doi.org/10.48550/arXiv.2305.16264

(2023).

5/5

