Teaching LLMs how to know when to ask for help to
provide more accurate answers

techxplore.com/news/2024-11-llms-accurate.html

Bob Yirka

NOVEMBER 5, 2024

by Bob Yirka , Tech Xplore

Pipeline of the method. Credit: arXiv (2024). DOI: 10.48550/arxiv.2411.00412

A team of computer scientists and AI researchers at the University of California, San Diego,
working with a colleague from Tsinghua University, has developed a tactic that helps LLM
models more easily determine when they need help from an external source to provide an
accurate answer.

The group has written a paper describing their approach, called "Adapting While Learning:
Grounding LLMs for Scientific Problems with Intelligent Tool Usage," and have posted it on
the arXiv preprint server.

In the early days of LLM building, development teams assumed that bigger was always
better. The more parameters used, it was assumed, the more accurate the answers
produced would be. More recently, developers have been finding that bigger is not always
better—sometimes LLMs can be made smarter, and thus more accurate, by adding other
features or by changing some of their basic attributes.

1/2

In this new study, the research team added a feature that allows a given LLM to assess its
own confidence in an answer by using a built-in safety check. Such a safety check, the
researchers found, could be something as simple as adding categorization before tackling a
problem, such as whether a given task is easy or difficult to carry out. They found this could
allow a much smaller LLM to be as smart, or smarter, than one that was much larger.

To use the new approach, the team developed two learning phases. The first is called "World
Knowledge Distillation," and its job is to learn about solutions using external tools. Doing so
helps the LLM build up expertise on a given topic. The second phase, called "Tool Usage
Adaptation," classifies problems by giving them confidence levels when solving a solution
without help.

The system allows for solving simpler (but high confidence) problems without even checking
to see if external help might be needed, which reduces overall resource needs. If more
difficult problems require external help, it can be done more swiftly because of the lower
overhead demands.

Testing of the system on a model with just 8 billion parameters, showed it to have a 28.18%
improvement in answer accuracy over the same type of model without the changes. It also
led to a 13.89% increase in tool usage precision, which is why, the team notes, the system
was so much more accurate.

The researchers suggest their new approach shows that bigger is not always better and that
extremely powerful LLMs can be created without resorting to massive size increases.

More information: Bohan Lyu et al, Adapting While Learning: Grounding LLMs for
Scientific Problems with Intelligent Tool Usage Adaptation, arXiv (2024). DOI:
10.48550/arxiv.2411.00412

Journal information: arXiv 

2/2

