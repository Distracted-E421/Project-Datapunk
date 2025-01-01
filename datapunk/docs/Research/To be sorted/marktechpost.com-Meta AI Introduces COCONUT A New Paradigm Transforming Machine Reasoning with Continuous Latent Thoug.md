Meta AI Introduces COCONUT: A New Paradigm
Transforming Machine Reasoning with Continuous Latent
Thoughts and Advanced Planning Capabilities

marktechpost.com/2024/12/12/meta-ai-introduces-coconut-a-new-paradigm-transforming-machine-reasoning-with-

continuous-latent-thoughts-and-advanced-planning-capabilities

December 12, 2024

Sana Hassan
December 12, 2024
Large language models (LLMs) trained on vast datasets of human language simulate logical
and problem-solving abilities by following structured approaches. However, existing methods
predominantly operate within a language space, where textual chains explicitly express
reasoning processes. While effective for clarity, this reliance on language introduces
inefficiencies, as natural language is inherently optimized for communication rather than
reasoning. Studies in neuroscience reinforce this notion, showing that reasoning often
bypasses language networks in the human brain. These findings highlight the potential to
develop alternative reasoning frameworks that free LLMs from language constraints.

A limitation of language-based reasoning methods is their computational inefficiency. When
LLMs process reasoning chains, most tokens contribute to fluency rather than actual
reasoning, leading to wasted computational resources. On the other side, critical reasoning
steps demand precise planning and decision-making, which current architectures struggle to
handle effectively. These inefficiencies become more highlighted as the reasoning tasks
grow complex or require exploring multiple solutions simultaneously. Also, language-based
models often prematurely commit to single deterministic paths, limiting their ability to
backtrack or consider alternative solutions. This inability restricts their effectiveness
in solving dynamic or exploratory problems.

The Chain-of-Thought (CoT) reasoning approach has gained prominence as a method to
address these inefficiencies. By guiding LLMs to generate step-by-step intermediate
solutions in language, CoT enhances problem-solving clarity and accuracy. However, it
remains bound by the constraints of natural language, as it is less effective for tasks
requiring intricate planning or exploration. Recent innovations have sought to incorporate
latent reasoning, a method that allows models to perform non-verbal computation.
Despite these advances, latent reasoning approaches often need more scalability and
robustness to outperform traditional language-based methods across diverse tasks.

Researchers from FAIR at Meta, UC San Diego, proposed COCONUT (Chain of Continuous
Thought) to tackle these challenges. COCONUT introduces a new paradigm that enables
LLMs to reason in an unrestricted latent space, bypassing the limitations of language. Unlike
traditional CoT, which encodes reasoning states as word tokens, COCONUT uses the last

1/4

hidden state of an LLM as a continuous representation of the reasoning state. This
representation, referred to as a “continuous thought,” is directly fed into the model for
further processing without decoding it into language. By doing so, COCONUT allows the
model to process reasoning steps computationally efficiently while retaining the ability to
explore multiple solution paths.

COCONUT employs a multi-stage training process to optimize its latent reasoning
capabilities. During training, the model alternates between language and latent modes,
progressively replacing language-based reasoning steps with latent representations.
For instance, in its final training stage, COCONUT replaces all reasoning chains with
continuous thoughts, enabling the model to solve problems entirely in latent space. This
method resembles a breadth-first search (BFS) approach, where the model evaluates
multiple reasoning paths simultaneously before narrowing down to the most promising
solution. This flexibility allows COCONUT to address complex tasks that require substantial
planning and decision-making.

The COCONUT was validated through experiments on three datasets: 

1. GSM8k for math reasoning
2. ProntoQA for logical reasoning
3. ProsQA is a newly introduced dataset requiring advanced planning over graph

structures.

Results showed that COCONUT performed better than traditional CoT methods in accuracy
and efficiency. For example, COCONUT achieved an accuracy of 99.9% on logical
reasoning tasks, surpassing CoT’s 98.8%, and generated fewer reasoning tokens
during inference. On the ProsQA dataset, COCONUT exhibited a clear advantage in tasks
requiring extensive planning, outperforming CoT and achieving higher accuracy with fewer
computational resources.

2/4

The major plus point with COCONUT is its ability to encode multiple reasoning paths
simultaneously. The model avoids premature commitments to specific solutions by
processing reasoning states as continuous thoughts. Instead, it maintains a distribution of
potential next steps, progressively eliminating incorrect paths. This approach proved
particularly effective in open-domain reasoning tasks like GSM8k, where COCONUT
achieved 42.9% accuracy compared to CoT’s 42.0%. The flexibility to explore and
backtrack within the latent space equips COCONUT with superior planning capabilities and
positions it well-suited for tasks involving uncertainty or multiple solution pathways.

The key takeaways from the research on COCONUT are as follows:

COCONUT outperformed traditional methods by achieving 99.9% accuracy on logical
reasoning tasks (ProntoQA) and 42.9% on math reasoning tasks (GSM8k).
The model reduced the number of reasoning tokens generated during inference,
demonstrating computational efficiency.
COCONUT’s latent space reasoning mimics a BFS, enabling the model to explore
multiple solutions and adapt to complex tasks.
The multi-stage training process allows COCONUT to scale to increasingly challenging
problems while maintaining high performance.
COCONUT excelled in diverse reasoning tasks, ranging from open-domain math
problems to logical reasoning with graph structures.

3/4

In conclusion, by introducing continuous latent thoughts, COCONUT overcomes the
inefficiencies of language-based approaches and enhances computational efficiency. Its
ability to encode and explore multiple reasoning paths positions it as a good solution for
complex problem-solving. Thus, COCONUT sets a new benchmark for machine reasoning
with good results in logical reasoning and efficient token utilization.

4/4

