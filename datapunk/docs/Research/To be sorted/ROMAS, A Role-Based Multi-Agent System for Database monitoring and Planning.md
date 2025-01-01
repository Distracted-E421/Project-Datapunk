4
2
0
2
c
e
D
8
1

]
I

A
.
s
c
[

1
v
0
2
5
3
1
.
2
1
4
2
:
v
i
X
r
a

ROMAS: A Role-Based Multi-Agent System for
Database monitoring and Planning

Yi Huang1∗, Fangyin Cheng2∗, Fan Zhou1, Jiahui Li1,
Jian Gong1, Hongjun Yang1, Zhidong Fan1, Caigao Jiang1,
Siqiao Xue1†, Faqiang Chen1†
1Ant Group, 2JD Group
{yaqing.hy, faqiang.cfq}@antgroup.com, siqiao.xsq@gmail.com

Abstract

In recent years, Large Language Models (LLMs) have demonstrated remarkable
capabilities in data analytics when integrated with Multi-Agent Systems (MAS).
However, these systems often struggle with complex tasks that involve diverse
functional requirements and intricate data processing challenges, necessitating
customized solutions that lack broad applicability. Furthermore, current MAS
fail to emulate essential human-like traits such as self-planning, self-monitoring,
and collaborative work in dynamic environments, leading to inefficiencies and
resource wastage. To address these limitations, we propose ROMAS, a novel Role-
Based Multi-Agent System designed to adapt to various scenarios while enabling
low code development and one-click deployment. ROMAS has been effectively
deployed in DB-GPT [Xue et al., 2023a, 2024b], a well-known project utilizing
LLM-powered database analytics, showcasing its practical utility in real-world
scenarios. By integrating role-based collaborative mechanisms for self-monitoring
and self-planning, and leveraging existing MAS capabilities to enhance database
interactions, ROMAS offers a more effective and versatile solution. Experimen-
tal evaluations of ROMAS demonstrate its superiority across multiple scenarios,
highlighting its potential to advance the field of multi-agent data analytics.

1

Introduction

Multi-agent systems (MAS) have garnered significant attention for their potential to tackle complex
tasks in dynamic environments through the coordinated collaboration of multiple agents. As task
complexity and environmental dynamics increase, researchers have been working to enhance the
capabilities of MAS by decomposing intricate tasks into simpler subtasks and improving agents’
adaptive, reflective, and self-correcting abilities [Anderson et al., 2018, Wang et al., 2023a, Xue
et al., 2023a, Trivedi et al., 2024]. However, despite these efforts, current MAS approaches still face
several critical limitations.

In terms of structural design, traditional MAS often rely on static task allocation and predefined
processes, such as Chain of Thought (CoT) [Wei et al., 2022], Self-consistent CoT (CoT-SC) [Wang
et al., 2023c] and Tree of Thought (ToT) [Yao et al., 2023a]. These procedural methods suffer
from low fault tolerance and lack the capability for autonomous reflection and interaction, leading
to failures when deviations occur from the predetermined plan. Furthermore, task-oriented MAS,
exemplified by frameworks such as MetaGPT [Hong et al., 2024] and TaskWeaver [Qiao et al., 2024],
are domain-specific and fail to generalize well beyond their predefined scopes, thus limiting their

∗Equal contribution
†Corresponding Author

Preprint. Under review.

 
 
 
 
 
 
Perspective

Module

Profile

Structure design

Task planning

Function

Role-based cooperation
Scenario versatility

Global monitor
Dynamic agent generation
Plan corrected

Memory

Action

Scenario adaptation

-

Message queue
Hybrid memory

Guardrails
Self-reflection

Versatility
Flexibility
Robustness

ROMAS GA AA MG
✓ ✓ ✓
✓ ✓ ✓

✓
✓

✓
✓
✓

✓
✓

✓
✓

✓
✓
✓

✗ ✓ ✗
✓ ✓ ✗
✗
✗
✗

✓ ✗
✗
✓ ✓ ✓

✓ ✓ ✓
✓ ✓ ✓

✓ ✓ ✗
✓ ✓ ✓
✗
✗
✗

Table 1: Comparison of ROMAS and traditional Autonomous MAS (GA = Generative Agent, AA =
AutoAgents, MG = MetaGPT).

applicability. Interactive MAS, such as ReAct [Yao et al., 2023b] , ChatCoT [Chen et al., 2023] and
Voyager [Wang et al., 2023a], facilitate dynamic feedback and self-correction but struggle with high
correction costs and the inability to rectify previously executed subtasks.

In terms of implementation, traditional MAS application development often relies on open-source
frameworks, such as LangChain [Chase, 2022], RasaRasaHQ [2023], ChatDev [Qian et al., 2024],
and AgentScope [Gao et al., 2024], which offer a range of development tools, simulated environments,
and fundamental agent capabilities. Although these frameworks allow for the quick development
of customized MAS systems, they are limited by their inability to handle diverse data management,
provide robust built-in development components, and offer comprehensive complex problem solving
toolkits, which hinders the full development potential of MAS applications.

To address the aforementioned limitations, we introduce ROMAS, a novel role-based multi-agent
system deployed in DB-GPT3, featuring several key innovations.

• Role-based collaboration. ROMAS organizes agents into specific roles—planner, monitor, and
worker. The planner creates global task lists and allocates subtasks to workers (§3.1). The monitor
oversees workers, ensuring correctness and re-planning when needed (§3.2). This structure enables
real-time self-supervision, enhancing flexibility and robustness.

• Self-monitoring and self-planning. ROMAS allows agents to evaluate their performance and
adjust actions dynamically through self-monitoring and self-planning mechanisms, ensuring high
adaptability to changing conditions and complex tasks.

• Low-code development and one-click deployment. We developed ROMAS on the DB-GPT, a
multi-agent application framework that integrates efficient computing operators, rich database man-
agement components, user-friendly data analysis visualization, flexible multi-domain deployment,
and the Agentic Workflow Expression Language (AWEL) for low-code streamlined development.
DB-GPT provides users with an efficient, intuitive, and secure data interaction solution, facilitating
development and simplifying deployment.

• Enhanced database interactions. ROMAS optimizes data retrieval, processing, and storage,
with the help of DB-GPT’s advanced data handling capabilities. This makes ROMAS ideal for
applications involving large datasets and complex analytics, ensuring efficient and effective data
management.

2 Related Work

Recent research in MAS has focused on three key areas: structure design, application development
frameworks, and scenario adaptation [Wang et al., 2024a, Jiang et al., 2023, 2024]. Structure design

3https://github.com/eosphoros-ai/DB-GPT

2

Module

Component

DB-GPT AgentScope AutoGen LangChain

Rich component

Fine-tuning

Coding

Multiple databases
Data analysis
LLM proxy
GraphRAG

Text2SQL
NLU
Prompt

Workflow language
Operator
Private deployment
Distribution

User interaction

Drag-and-drop workshop
Visualization page

✓
✓
✓
✓

✓
✓
✓

✓
✓
✓
✓

✓
✓

✓
✓
✓
✓

✗
✗
✓

✓
✗
✗
✓

✓
✓

✗
✓
✓
✗

✗
✗
✓

✓
✓
✓
✓

✗
✓

✗
✓
✓
✗

✗
✗
✓

✓
✓
✗
✗

✗
✗

Table 2: Comparison of DB-GPT and traditional agent application framework.

emphasizes enhancing agent performance through modules such as profile, memory, planning, and
action [Masterman et al., 2024]. Application development framework emphasis on achieving low-code
development, convenient deployment, and user interaction experience. Scenario adaptability emphasis
on the ability to be effectively applied across various domains. A highly adaptable framework should
be able to easily accommodate different task requirements without requiring extensive adjustments.

Autonomous MAS. We compare ROMAS with traditional MAS in terms of structural design and
scenario adaptation as shown in table 1, Generative Agents [Park et al., 2023] simulates social
role definitions, determining each agent’s behavior, tasks, and interaction modes. The memory
module records all experiences through a memory stream and retrieves the highest-priority memories
based on recency, importance, and relevance. However, in task planning, Generative Agents lack a
global monitor mechanism, limiting ability to engage in global reflection and dynamic correction.
AutoAgents [Chen et al., 2024] adaptively generate specialized agents to build an AI team, which
consists of two critical stages: drafting stage and execution stage. During the drafting stage, the
planner determines the plan list and the generation of agents through discussions with the agent
observer and the plan observer. In the execution stage, the action observer corrects the behavior of
individual agents. Although multiple global supervisory roles are set, there is no correction of the
plan list during the execution stage. Therefore, if there is an error in the plan list during the drafting
stage, it cannot be corrected in the execution stage. MetaGPT [Hong et al., 2024] assigns multiple
engineer agent roles to collaboratively complete the software development coding and Standard
Operating Procedure (SOP) writing. However, MetaGPT lacks a global monitor and can’t adaptively
generate specialized agents. This means that once the plan is set, MetaGPT has limited flexibility for
adjustments or corrections during execution.

Application framework. We compare DB-GPT with traditional agent application framework as
shown in table 2, AgentScope [Gao et al., 2024] is a developer-centric multi-agent platform that offers
user-friendly interfaces for application demonstration and monitoring, a zero-code programming
workstation, and an automatic prompt tuning mechanism. In terms of coding, it provides rich syntactic
tools, built-in and customizable fault tolerance mechanisms, and an actor-based distributed framework.
However, AgentScope lacks components such as Text2SQL fine-tuning [Zhou et al., 2024b] for small
models and ready-made operators, making it less suitable for data analysis compared to DB-GPT.
LangChain [Chase, 2022] offers a rich set of components, such as LLMs, memory, and agents, as well
as structured component collections like chains to accomplish specific tasks. However, LangChain
lacks a user-friendly interface and does not support private deployment. AutoGen [Wu et al., 2023a]
main tasks include: (1) defining conversational agents with specific capabilities and roles; and (2)
programming the interaction behaviors between agents through computation and control within a
dialogue center. However, programming based on a QA scenario has limitations when it comes to
handling complex tasks.

3

Figure 1: ROMAS framework. The blue lines represent key message exchanged between agents and
DB-GPT, the orange lines signify the three distinct phases of ROMAS, and the green lines denote
each agent’s internal planning and reflection processes.

3 Methodology

ROMAS is a versatil data analysis framework based on the DB-GPT. Its principles prioritize high
flexibility and comprehensive functionality, without being constrained by specific scenarios, data
formats, or development complexity. the agent roles in ROMAS are divided into a planner, a monitor,
and multiple workers [Yong and Miikkulainen, 2009] shown in figure1, a detailed description of the
role definition is provided in the appendixA.

The ROMAS comprises three critical phases: initialization, execution, and re-planning, each
benefiting from the powerful database capabilities of DB-GPT. During the initialization phase,
the planner decomposes the requirements based on the scenario description and known database
information, forming an specailized agent team and designing specific task lists for each agent [Li
et al., 2024a]. The execution phase relies on multi-agent cooperation [Du et al., 2023], with workers
collaborating to complete tasks according to the planner’s plan. If errors occur, the system reports
key global information to the monitor, awaiting further instructions. In the re-planning phase, the
monitor and planner interact closely. If the monitor’s attempts to correct the errors fail, it triggers the
planner to re-plan, integrating key information to assist in the planner’s decision-making.

3.1

Initialization Phase

In this phase as illustrated in figure 2, firstly the planner automatically generate the profile prompt
based on templates and user input. Next, the planner will execute the self-planning process according
to the profile. During this process, it will sequentially generate two key strategies: the cooperation
workflow of the agent team and the task list for each agent. Once the strategies are generated, the
planner will perform self-reflection process to check the effectiveness of these strategies. Finally, an
action is executed to save the initial strategies and trigger the execution phase.

Self-planning process [Huang et al., 2024]. The input set <G, D, C, A, T> is defined in the profile. and
the output set is <AL, TL> which is the input of self-reflection process. Goal G specifies the planner’s
task goal in detail, which involve creating the entire cooperative agent team and assigning refined
task lists for each worker. Description D describes the provided scenario information, including
descriptions from user and a brief table with raw database index information for task assigning.
Constraint C represents the constraints that the planner must adhere to when generating the agent
team and task lists. Toolkit T is a set of pre-defined toolkits provided by DB-GPT like web search
tool [Microsoft, 2023]. Multiple tools can be combined to complete specific tasks in the agent’s task
list. Agentset A defines the range of agent roles available for generating the agent team. worker roles
are limited to tasker, retriever, extractor, and painter. Each role has a pre-defined parent class template

4

Figure 2: Initialization phase of ROMAS, the planner is primarily responsible for two steps: self-
planning and self-reflection. In self-planning, the planner generates the agent team and arranges
subtask list. In self-reflection, these strategies are validated for logical consistency.

that includes many general capabilities, which can be directly inherited and further refined based on
the specific scenario.

Agent list AL is a list of agents with a predefined call order, structured like a tree [Yao et al., 2023a].
tasker serves as the control center for each entire process including main process, planning and
managing the workflow of each agent. Following steps are executed in sequence in the tasker: 1. call
extractor: the extractor is responsible for extracting the required data from the raw data and storing it
categorically for future needs. This step enhances efficiency and reduces redundant work. 2. call
retriever: the retriever is responsible for recalling and assembling the metadata needed to complete
the task from the stored data. This ensures that all necessary information is prepared and ready.
3. call painter (not necessary): the painter is responsible for handling complex data analysis and
chart generation. It uses the data extracted and assembled in the previous steps to produce detailed
analytical reports and intuitive charts, helping users better understand and interpret the data. Task
list TL is a comprehensive series of tasks for each agent need to complete, with each task being
derived from the robust DB-GPT resource library which encompasses a wide array of tools, including
data extraction, data analysis, and more, designed to support a variety of complex operations and
workflows.

Self-reflection process [Li et al., 2024c]. The planner primarily addresses two main aspects [Chen
et al., 2024]: A. verifying the rationality of the agent team workflow. The following aspects are
primarily checked: 1. compliance, ensuring that the agent team adheres to the specifications defined
in the constraints. 2. scenario compatibility, verifying that the agent team is compatible with the
scenario information defined in the description. 3. system-individual coupling, assessing whether

5

each agent can adapt to the entire team and determining if there is a need to add or remove any agents.
B. verifying the rationality of each agent’s task list. The following aspects are primarily checked: 1.
task interdependency: ensuring that tasks are combined in a logical manner to accomplish specific
tasks. 2. input and output parameter logic: verifying that the input and output parameters of each
task are logically consistent and that the task can be executed successfully to complete its assigned
responsibilities.

Memory mechanism [Zhang et al., 2024]. ROMAS leverages a memory mechanism based on DB-
GPT to facilitate communication and feedback between agents. However, due to the varying recency,
importance, and relevance of different messages, as well as the limited prompt length processing
capability of LLM, it is impractical to cover all messages in a single pass. To address this, ROMAS
employs an effective memory categorization strategy, including sensory memory, short-term memory,
long-term memory, and hybrid memory, ensuring efficient management and utilization of diverse
types of information. Details of the memory mechanism implementation are in the appendixB.

3.2 Execution Phase

Figure 3: Execution phase of ROMAS, workers execute tasks based on the strategies formulated by
the planner, monitor classifies errors and decides to either fix them directly or report to the planner
for re-planning.

In this phase as illustrated in figure 3, When encountering errors, workers firstly attempt to self-correct
using the self-reflection mechanism. If the error persists after retries, workers must report the global
state to the monitor and await corrective instructions. Upon receiving the urgent information from
workers, the monitor firstly classifies the errors. Errors can be classified into two types depending on
nature: task list pipeline errors or agent team generation errors. For task list pipeline errors, which
typically indicate a problem at a specific process node and regarded as relatively simple orchestration
issues, the monitor can directly identify the fault and propose appropriate corrective instructions to
the workers. For agent team generation errors, which typically indicates that there exists fundamental
system issues in the planning process conducted by the planner. In this case, the monitor needs
to conduct a comprehensive analysis of the overall information, formulate a set of improvement
recommendations, and trigger the planner to restart the planning process in hopes of finding a better
solution.

Error alert. When workers encounter a problem, they report the global state to the monitor. Due to the
prompt length window limitation [Vaswani et al., 2023], the monitor only processes key information.
Therefore, we require that workers encountering errors report detailed information related to both

6

the individual and the system, including logs, error messages, history records, and the self-reflection
process. In contrast, workers that are operating normally only need to report their individual result
data and system-related context information, such as operation results, history records, and logs.
When a worker fails, it will broadcast an error message to all workers, all workers will then pause
their tasks and report their current status to the monitor.

Error tree search strategy [Browne et al., 2012]. Based on empirical data, we have hierarchically
organized the potential errors in the MAS into a tree structure, as shown in the appendixD. We classify
errors into two major categories: pipeline errors and logical errors. Pipeline errors typically involve
anomalies in the processing flow, while logical errors are related to defects in algorithm design. When
the monitor collects error information, it organizes key information and performs similarity searches
using this predefined error tree to pinpoint specific issues, starting from the root node and proceeding
layer by layer until it identifies the specific leaf node.

Instruction and recommendation generation. After identifying the error type, the monitor plans the
next steps based on the collected information from both the planner and the workers. (1). Agent team
generation errors: The monitor retrieves the planner’s planning and reflection record from short-term
memory in this current round. It also consolidates alert information provided by the workers, with
a particular focus on error-related data. Based on this information, the monitor extracts key global
insights and formulates recommendations, which are then transferred to the planner for replanning.
(2). Task pipeline error, the monitor will assess whether the input and output results of each task and
their upstream and downstream relationships meet the objectives according to the current strategy of
the planner. It will then issue adjustment instructions to correct any discrepancies without triggering
the planner to perform re-planning.

3.3 Re-planning Phase

Figure 4: Re-plannig phase of ROMAS, planner receives global critical information and modification
recommendation from the monitor to generate a new strategy for the current round.

In this phase as illustrated in figure4, the main responsibility is on the planner. The planner receives
global critical information and modification recommendation from the monitor, and combines them
with its own historical strategies and experience information from the previous round to generate
a new strategy for the current round. To ensure the effectiveness of the new strategy and avoid
resource wastage during the execution stage when validating its effectiveness, we introduce a strategy
called gap narrow. The gap narrow strategy aims to correct the errors from the previous round at the
minimum cost and align the inconsistencies between the current round’s strategy and the previous
round’s strategy through minimal modifications. This strategy not only enhances the system’s
efficiency but also ensures the consistency and continuity of the strategies, thereby optimizing the
overall performance. The algorithm at this stage is shown in the algorithm1.

7

Gap narrow rule [Li et al., 2024b]. After generating the new strategy, we first use LLM to conduct
a detailed comparison between the new and old strategies, analyzing and identifying their specific
differences. Next, we establish a set of prior rules aimed at minimizing modifications to the old
strategy. Then, we integrate comprehensive data from the monitor to perform a thorough reflection
and correction on each difference point. This process not only ensures that each difference point
effectively corrects the errors from the old strategy’s execution but also aims to achieve the best
possible solution with the minimum modification cost [Zhang et al., 2020].

4 Experiments

Datasets. We conducted our experience based on following 2 dataset, empirical evidence has
consistently demonstrated that ROMAS exhibits excellent performance in both general-knowledge
and domain-specific scenarios.

• FAMMA [Xue et al., 2024a]. We focus on the financial data analysis scenario, a critical
application area for generative language models [Xue et al., 2023c, Wu et al., 2023b], to
evaluate the capabilities of ROMAS. FAMMA is an open-source benchmark for financial
multilingual multimodal [Yin et al., 2024] question answering (QA) [Kapoor et al., 2024].
To adapt to the task requirements, we processed the original dataset by selecting 100 cases
that include both text and table images in the input and have standard options in the output,
and converted these table images into tabular format.

• HotpotQA [Yang et al., 2018]. To demonstrate reasoning capabilities in general scenarios, we
selected 100 samples from HotpotQA. This dataset is renowned for its multi-hop reasoning
questions and diverse question types, which encourage models to perform cross-document
information integration and complex reasoning, thereby comprehensively evaluating and
enhancing system performance in complex reasoning tasks.

Evaluation metrics. We select success rate, LLM evaluation [Wang et al., 2023b], and Human
evaluation as metrics. Besides using success rate to evaluate whether the system outputs standard
answers, we also adopt CoT to guide the agent in outputting its reasoning process along with
standard options. LLM evaluation and Human evaluation are used to assess the accuracy, coherence,
completeness, and logic of the descriptions [Wang et al., 2023b]. As shown in the appendixC, both
LLM and human evaluation are scored based on a standard scale of 10 points per dimension, with a
total of 100 points. The human score is independently evaluated by multiple financial analysis experts
according to a unified standard, with reasons for the scores recorded and the final score averaged.
By combining these three metrics, we can comprehensively assess the performance of ROMAS and
validate its effectiveness.

Setup. We developed ROMAS based on GPT-4 [OpenAI et al., 2024], configuring the temperature
to 0 to ensure the consistency of the model’s outputs. For each agent, the maximum retry count for
self-reflection and self-planning was set to 2, mitigating the risk of failure in a single invocation of
the LLM. The maximum retry count for the re-planning process was set to 3 to prevent exceeding
context threshold.

Analysis I: Comparison with other LLM and MAS. As shown in table 3, we categorize the
comparative objects into three groups: LLMs, single-agent with task planning capabilities, and the
current advanced MAS. In the LLMs group, we selected Qwen2-72B [Yang et al., 2024], Llama2-
70B [Touvron et al., 2023], and GPT-4, combining with single prompt technique as the baselines for
experiments. The result indicates that GPT-4 performs the best, likely due to its extensive training
with large-scale data and network parameters. In the single-agent group, we selected traditional
decision-making models with task planning capabilities, including CoT, ToT, and ReAct. The result
shows that ReAct significantly improves the baseline accuracy of LLMs. This improvement is likely
because the thought-act-observation [Yao et al., 2023b] process in ReAct enables a more reflective
and reasonable task planning process. In the MAS group, we compare the pioneering generative agent,
which introduces reflective thinking mechanisms in the MAS domain, and AutoAgent, which also
features role-based supervision. The result demonstrates that ROMAS outperforms the others. The
advantage over the generative agent could be attributed to the introduction of the monitor mechanism,
which offers error correction opportunities. ROMAS surpasses AutoAgent possibly because its
task planning error correction occurs during the execution phase when real problems arise, rather
than during the drafting phase as a prediction. Furthermore, ROMAS’s on-the-spot error correction

8

mechanism for pipeline errors significantly enhanced the efficiency of error correction in the MAS.
Simultaneously, experimental results show that performance on the HotpotQA dataset surpasses
that on FAMMA, particularly within the MAS grouping. This could be attributed to the LLM’s
proficiency in handling general knowledge, as well as ROMAS can flexibly adjust strategies in the
dynamical situation based on self-monitoring and self-planning process, which helps in handling the
uncertainties and changes that may arise during multi-hop reasoning.

Grouping

Model

SR
F / H(%)

LLM Eval HumanEval
F / H(0-100)
F / H(0-100)

LLM baseline

LLM w/ task planning

State-of-art MAS

LLAMA2-70B
QWEN2-72B
GPT-4

CoT (GPT-4)
ToT (GPT-4)
ReAct (GPT-4)

Generative Agent
AutoAgents
ROMAS

29.13 / 31.53
35.65 / 37.83
42.85 / 45.36

46.44 / 51.27
51.61 / 56.18
56.80 / 61.44

61.20 / 67.08
73.45 / 78.99
81.68 / 85.24

42.14 / 44.12
46.97 / 45.02
48.72 / 47.20

51.36 / 54.77
56.98 / 61.04
57.82 / 63.29

64.31 / 69.37
70.55 / 73.08
78.30 / 83.64

33.12 / 35.97
41.51 / 42.56
47.19 / 48.85

50.24 / 49.05
54.79 / 52.61
60.26 / 62.07

62.03 / 66.07
68.07 / 71.11
75.08 / 77.98

Table 3: Performance of ROMAS on FAMMA benchmark comparing with other LLM and MAS (F
= FAMMA, H = HotpotQA).

Analysis II: Ablation study. As shown in table 4, a comparison of ROMAS performance with and
without the corresponding components validates the effectiveness of each component.

On FAMMA. The result indicates that the absence of the monitor mechanism leads to the most
significant decline in ROMAS success rate, underscoring its critical role. Secondly, the self-reflection
module also has a considerable impact on the system, although its influence is less than that of the
monitor mechanism. The reason for this may be that the self-reflection process can only accomplish
independent reflection by the agent itself, based solely on predefined conditions and its own data. In
contrast, the information from the monitor mechanism is derived from a global perspective, enabling
it to improve the performance of individual agents by considering the overall system state, making the
correction process more reliable. The memory mechanism also has a substantial impact on the overall
performance of ROMAS, as memory serves as a crucial basis for agents to process information in
each round. Without classified storage and prioritization of memory, the task planning capability of
agents would significantly decrease. The gap narrow rule has the least impact on ROMAS, indicating
that the success rate in the re-planning process after an initial correction is high, thus requiring
minimal alignment operations.

Notably, on the HotpotQA, the self-reflection and memory mechanisms have the most significant
impact. This disparity may be attributed to the differing inferential demands of the two datasets. The
complex questions in FAMMA require precise monitoring mechanisms and self-reflection to avoid
errors, whereas HotpotQA’s multi-hop reasoning characteristic necessitates a system with stronger
memory capacity to maintain consistency and integrity across multiple steps, as well as self-reflection
to correct biases in the reasoning process.

Model

SR
F / H (%∆vs.romas)

LLM Eval HumanEval
F / H (0-100)
F / H (0-100)

76.69 (↓ 4.99) / 79.17 (↓ 6.07)
ROMAS w/o gap narrow rule
ROMAS w/o memory mechanism 68.63 (↓ 13.05) / 64.83 (↓ 20.41)
62.37 (↓ 19.31) / 59.92 (↓25.32)
ROMAS w/o self-reflection
ROMAS w/o monitor mechanism 59.02 (↓22.66) / 71.79 (↓ 13.45)
ROMAS

81.68 / 85.24

72.76 / 70.61
65.63 / 68.37
54.73 / 45.18
42.31 / 53.20
78.30 / 83.64

70.85 / 69.29
62.50 / 68.45
52.13 / 41.20
40.02 / 50.18
75.08 / 77.98

Table 4: The ablation study of ROMAS (F = FAMMA, H = HotpotQA).

Analysis III: DB-GPT effectiveness demonstration. As shown in table 4, we validate the effec-
tiveness of developing the ROMAS system using the DB-GPT framework through comparative

9

experiments. We also implemente the ROMAS system using two leading application frameworks,
LangChain and AgentScope, and select code volume, average QA time, and task success rate as the
evaluation metrics [Feng et al., 2020]. The result indicates that the DB-GPT framework significantly
reduces the amount of code required for development. This is primarily due to the robust open-
source community of DB-GPT, which has contributed numerous functions and operators that support
one-click invocation, greatly simplifying the development process of agent applications. Moreover,
DB-GPT’s extensive set of database operation tools and components further enhances the success
rate of task execution and execution efficiency.

Application framework SR CodeV olume AverageQAT ime

(%)

(number of rows)

(second)

LangChain
AgentScope
ROMAS

68.59
74.1
81.68

2500
1800
1500

22.08
19.97
12.23

Table 5: Comparison of ROMAS implementation using DB-GPT, LangChain, and AgentScope.

Analysis IV: Argument on diversity and functionality. As shown in figure5, the six subtask
categories predominantly center on DocumentQA [documentqa, 2023] and IndicatorQA, underscoring
their importance in building a qa system and substantial influence on overall system performance.
Additionally, for domain-specific dataset FAMMA, the higher task complexity, various data, and
complex reasoning necessitate more specialized subtasks, frequent self-reflection and replanning.
Consequently, the average frequency of self-reflection and replanning is higher, and the number of
generated workers is also greater.

Figure 5: Figure 1 shows the average proportions of different subtask types in the FAMMA and
HotpotQA. Figure 2 presents the average number of workers generated, the average self-reflection
frequency per agent, and the average replanning frequency of the planner. Figure 3 displays the
average proportions of instructions and recommendations given by the monitor.

5 Conclusion

In this paper, we presented ROMAS, a role-based multi-agent system designed for database monitor-
ing and planning, leveraging DB-GPT for enhanced self-monitoring, self-planning, and collaborative
interaction. By addressing the limitations of current multi-agent systems, ROMAS enables efficient
and versatile deployment in complex scenarios. Through evaluations on the FAMMA dataset, we
demonstrated the system’s effectiveness, highlighting its potential to streamline analytical tasks and
support future advancements in intelligent multi-agent systems.

10

Appendices

A Role Introduction

The planner aims to decompose user requests and scenario information into clear, well-defined
subtasks, generates the entire specialized agent team [Chen et al., 2024], and assigns a task list for
each agent.

The monitor is responsible for overseeing the entire system, ensuring global smooth operation through
continuous interaction with workers and the planner. If an error occurs during execution, the monitor
analyzes global information to categorize this error as either task list pipeline error or agent team
generation error. Depending on the type of error, monitor decides whether to correct the error itself
or to report it to the planner for replanning.

To align with the typical processes of data acquiring, data cleanning, data processing, and data
analysing [Maharana et al., 2022] in a data analysis scenario, we have categorized workers into the
following roles:

Tasker, as the primary manager for subtasks, aims to complete subtasks by flexibly planning the
collaboration between extractors, retrievers, and painters. One system can abstract different types
of taskers based on various subtasks, such as indicator tasker, document QA tasker, GraphRAG
tasker [Peng et al., 2024], and summary tasker.

Extractor, as a data processing assistant, aims to achieve information extraction and index storage from
structured and unstructured raw data. Its functions include PDF document loading, data preprocessing,
document block segmentation, document tree construction, table extraction and merging, and the
storage of text and table data.

Retriever, as a data acquiring helper, aims to retrieve the necessary data from the most suitable
database to support taskers. Its functions include sql generation, sql execution, python execution,
composite index calculation.

Painter, as a data analysing helper, aims to draw relevant charts based on the provided data, making it
easier for users to intuitively understand the analysis results.

B Memory Mechanism of ROMAS

Sensory memory [Wang et al., 2024a] is similar to human transient memory and primarily used for
recording and capturing real-time sensory information interacted with environment such as one-time
and repetitive actions of agents. Some important parts in Sensory memory is transferred to Short-term
memory over time.

Short-term memory [Wang et al., 2024a] stores recent important information with limited capacity
and duration. This type of memory temporarily holds information that requires quick access and
processing, such as the agent’s current self-planning and self-reflection results, agent current situations,
context information, temporary strategy. Some important parts in short-term memory is transferred to
long-term memory over time.

Long-term memory [Wang et al., 2024a] stores the knowledge and patterns learned by the agent
from past experiences, which are used to guide future decisions and actions. In ROMAS, long-term
memory commonly stores agent’s vital erroneous information and summaries of historical decisions.

Hybrid memory [Wang et al., 2024a] explicitly combines the advantage of short-term and long-term
memories, leveraging immediate data for short-term tasks while utilizing accumulated knowledge
for long-term strategy and learning. In ROMAS, hybrid memory is commonly used to generate the
current round strategy based on the previous round’s strategy and the current round’s state, such as
in the replanning phase, the planner combines its historical strategy in long-term memory with the
global state in monitor’s short-term memory to generate this round’s new strategy.

11

Figure 6: We divided the evaluation criteria into 10 dimensions based on common standards for large
models.

C Dimension of LLM and Human Evaluation

D Error tree search

Figure 7: Error tree search, we classified common errors in MAS into two categories based on
empirical data: pipeline and logic and constructed an error tree as reference for monitor’s error
classification, enabling precise error cause identification by DFS [Tarjan, 1972].

E Re-planning phase algorithm

F Ongoing and Future Works

We are actively exploring several extensions to enhance the capability and versatility of our system,
particularly in addressing more complex dialogue and analytical tasks. Our key areas of focus include:

• Empowering computational agents. Users increasingly expect systems not only to perform analyses
but also to deliver advanced computational capabilities, such as generating predictive insights [Jin
et al., 2023, Xue et al., 2024c] and facilitating decision-making based on historical data [Xue et al.,
2022a, Pan et al., 2023, Zhou et al., 2024a]. Developing these functionalities will significantly
enhance the system’s utility in real-world applications, such as recommendation systems [Chu
et al., 2023, Wang et al., 2024b] and traffic control [Xue et al., 2022b].

12

Algorithm 1 Re-planning phase
Require: global state from monitor G, recommendation from monitor R, user query Q, old strategy

Sold, scenario prompt P

else

for each rule rj ∈ R do

if di does not follow rj then

regenerate di based on {G, R, Q, Sold, P }
break

1: generate a new strategy, Snew ← LLM(G, R, Q, Sold, P ).
2: compute differences D between Snew and Sold, D = {d1, d2, . . . , dn} ← LLM(Snew, Sold).
3: establish prerequisites R = {r1, r2, . . . , rn} aimed at minimizing modifications.
4: for each difference di ∈ D do
5:
6:
7:
8:
9:
10:
11:
12:
13:
14:
15:
16:
17: end for
18: ensure each corrected difference integrates properly to form the optimized strategy Sopt
19: return optimized strategy Sopt

reflect on whether di has improved Sold based on G and R
if not improved then

regenerate differences D based on {G, R, Q, Sold, P }
break

end for

end if

end if

• Adopting advanced model training methodologies. Beyond pre-training, the integration of advanced
techniques such as continual learning, including continual pre-training [Jiang et al., 2023, 2024],
and prompt learning [Wang et al., 2022, Xue et al., 2023b], offers opportunities to improve the
system’s adaptability and performance. Leveraging these methods will drive advancements in
the development of systems for computational use and foster further innovation in the research
community.

References

Peter Anderson, Angel Chang, Devendra Singh Chaplot, Alexey Dosovitskiy, Saurabh Gupta, Vladlen
Koltun, Jana Kosecka, Jitendra Malik, Roozbeh Mottaghi, Manolis Savva, et al. On evaluation
of embodied navigation agents. arXiv preprint arXiv:1807.06757, 2018. URL https://arxiv.
org/abs/1807.06757.

Cameron B. Browne, Edward Powley, Daniel Whitehouse, Simon M. Lucas, Peter I. Cowling, Philipp
Rohlfshagen, Stephen Tavener, Diego Perez, Spyridon Samothrakis, and Simon Colton. A survey
of monte carlo tree search methods. IEEE Transactions on Computational Intelligence and AI in
Games, 4(1):1–43, 2012. doi: 10.1109/TCIAIG.2012.2186810.

Harrison Chase. LangChain, 2022. URL https://github.com/hwchase17/langchain.

Guangyao Chen, Siwei Dong, Yu Shu, Ge Zhang, Jaward Sesay, Börje F. Karlsson, Jie Fu, and
Yemin Shi. Autoagents: A framework for automatic agent generation, 2024. URL https:
//arxiv.org/abs/2309.17288.

Zhipeng Chen, Kun Zhou, Beichen Zhang, Zheng Gong, Wayne Xin Zhao, and Ji-Rong Wen. Chatcot:
Tool-augmented chain-of-thought reasoning on chat-based large language models, 2023. URL
https://arxiv.org/abs/2305.14323.

Zhixuan Chu, Hongyan Hao, Xin Ouyang, Simeng Wang, Yan Wang, Yue Shen, Jinjie Gu, Qing Cui,
Longfei Li, Siqiao Xue, et al. Leveraging large language models for pre-trained recommender
systems. arXiv preprint arXiv:2308.10837, 2023.

documentqa.

documentqa.

document-question-answering, 2023.

see

https://huggingface.co/tasks/

13

Yali Du, Joel Z. Leibo, Usman Islam, Richard Willis, and Peter Sunehag. A review of cooperation in

multi-agent learning, 2023. URL https://arxiv.org/abs/2312.05162.

Zhangyin Feng, Daya Guo, Duyu Tang, Nan Duan, Xiaocheng Feng, Ming Gong, Linjun Shou, Bing
Qin, Ting Liu, Daxin Jiang, and Ming Zhou. Codebert: A pre-trained model for programming and
natural languages, 2020. URL https://arxiv.org/abs/2002.08155.

Dawei Gao, Zitao Li, Xuchen Pan, Weirui Kuang, Zhijian Ma, Bingchen Qian, Fei Wei, Wenhao
Zhang, Yuexiang Xie, Daoyuan Chen, Liuyi Yao, Hongyi Peng, Zeyu Zhang, Lin Zhu, Chen
Cheng, Hongzhu Shi, Yaliang Li, Bolin Ding, and Jingren Zhou. Agentscope: A flexible yet robust
multi-agent platform, 2024. URL https://arxiv.org/abs/2402.14034.

Sirui Hong, Mingchen Zhuge, Jonathan Chen, Xiawu Zheng, Yuheng Cheng, Jinlin Wang, Ceyao
Zhang, Zili Wang, Steven Ka Shing Yau, Zijuan Lin, Liyang Zhou, Chenyu Ran, Lingfeng
Xiao, Chenglin Wu, and Jürgen Schmidhuber. MetaGPT: Meta programming for a multi-agent
collaborative framework. In The Twelfth International Conference on Learning Representations,
2024. URL https://openreview.net/forum?id=VtmBAGCN7o.

Xu Huang, Weiwen Liu, Xiaolong Chen, Xingmei Wang, Hao Wang, Defu Lian, Yasheng Wang,
Ruiming Tang, and Enhong Chen. Understanding the planning of llm agents: A survey, 2024.
URL https://arxiv.org/abs/2402.02716.

Gangwei Jiang, Caigao Jiang, Siqiao Xue, James Y. Zhang, Jun Zhou, Defu Lian, and Ying Wei.
Towards anytime fine-tuning: Continually pre-trained language models with hypernetwork prompt.
In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing
(EMNLP), 2023. URL https://arxiv.org/abs/2310.13024.

Gangwei Jiang, Caigao Jiang, Zhaoyi Li, Siqiao Xue, Jun Zhou, Linqi Song, Defu Lian, and Ying
Wei. Interpretable catastrophic forgetting of large language model fine-tuning via instruction vector.
https://arxiv.org/abs/2406.12227, 2024. URL https://arxiv.org/abs/2406.12227.

Ming Jin, Qingsong Wen, Yuxuan Liang, Chaoli Zhang, Siqiao Xue, Xue Wang, James Zhang,
Yi Wang, Haifeng Chen, Xiaoli Li, Shirui Pan, Vincent S. Tseng, Yu Zheng, Lei Chen, and Hui
Xiong. Large models for time series and spatio-temporal data: A survey and outlook, 2023.

Sayash Kapoor, Benedikt Stroebl, Zachary S. Siegel, Nitya Nadgir, and Arvind Narayanan. Ai agents

that matter, 2024. URL https://arxiv.org/abs/2407.01502.

Ao Li, Yuexiang Xie, Songze Li, Fugee Tsung, Bolin Ding, and Yaliang Li. Agent-oriented planning

in multi-agent systems, 2024a. URL https://arxiv.org/abs/2410.02189.

Jiahui Li, Hanlin Zhang, Fengda Zhang, Tai-Wei Chang, Kun Kuang, Long Chen, and Jun Zhou.
Optimizing language models with fair and stable reward composition in reinforcement learning. In
Yaser Al-Onaizan, Mohit Bansal, and Yun-Nung Chen, editors, Proceedings of the 2024 Conference
on Empirical Methods in Natural Language Processing, pages 10122–10140, Miami, Florida, USA,
November 2024b. Association for Computational Linguistics. doi: 10.18653/v1/2024.emnlp-main.
565. URL https://aclanthology.org/2024.emnlp-main.565.

Yuanchun Li, Hao Wen, Weijun Wang, Xiangyu Li, Yizhen Yuan, Guohong Liu, Jiacheng Liu,
Wenxing Xu, Xiang Wang, Yi Sun, Rui Kong, Yile Wang, Hanfei Geng, Jian Luan, Xuefeng Jin,
Zilong Ye, Guanjing Xiong, Fan Zhang, Xiang Li, Mengwei Xu, Zhijun Li, Peng Li, Yang Liu,
Ya-Qin Zhang, and Yunxin Liu. Personal llm agents: Insights and survey about the capability,
efficiency and security, 2024c. URL https://arxiv.org/abs/2401.05459.

Kiran Maharana, Surajit Mondal, and Bhushankumar Nemade. A review: Data pre-processing and
data augmentation techniques. Global Transitions Proceedings, 3(1):91–99, 2022. ISSN 2666-
285X. doi: https://doi.org/10.1016/j.gltp.2022.04.020. URL https://www.sciencedirect.
com/science/article/pii/S2666285X22000565.
International Conference on Intelligent
Engineering Approach(ICIEA-2022).

Tula Masterman, Sandi Besen, Mason Sawtell, and Alex Chao. The landscape of emerging ai
agent architectures for reasoning, planning, and tool calling: A survey, 2024. URL https:
//arxiv.org/abs/2404.11584.

14

Microsoft. bing. see https://www.microsoft.com/zh-cn/bing/search-app-desktop?rtc=

1, 2023.

OpenAI, Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad, Ilge Akkaya, Florencia Leoni
Aleman, Diogo Almeida, Janko Altenschmidt, Sam Altman, Shyamal Anadkat, Red Avila, Igor
Babuschkin, Suchir Balaji, Valerie Balcom, Paul Baltescu, Haiming Bao, Mohammad Bavarian,
Jeff Belgum, Irwan Bello, Jake Berdine, Gabriel Bernadett-Shapiro, Christopher Berner, Lenny
Bogdonoff, Oleg Boiko, Madelaine Boyd, Anna-Luisa Brakman, Greg Brockman, Tim Brooks,
Miles Brundage, Kevin Button, Trevor Cai, Rosie Campbell, Andrew Cann, Brittany Carey, Chelsea
Carlson, Rory Carmichael, Brooke Chan, Che Chang, Fotis Chantzis, Derek Chen, Sully Chen,
Ruby Chen, Jason Chen, Mark Chen, Ben Chess, Chester Cho, Casey Chu, Hyung Won Chung,
Dave Cummings, Jeremiah Currier, Yunxing Dai, Cory Decareaux, Thomas Degry, Noah Deutsch,
Damien Deville, Arka Dhar, David Dohan, Steve Dowling, Sheila Dunning, Adrien Ecoffet, Atty
Eleti, Tyna Eloundou, David Farhi, Liam Fedus, Niko Felix, Simón Posada Fishman, Juston Forte,
Isabella Fulford, Leo Gao, Elie Georges, Christian Gibson, Vik Goel, Tarun Gogineni, Gabriel
Goh, Rapha Gontijo-Lopes, Jonathan Gordon, Morgan Grafstein, Scott Gray, Ryan Greene, Joshua
Gross, Shixiang Shane Gu, Yufei Guo, Chris Hallacy, Jesse Han, Jeff Harris, Yuchen He, Mike
Heaton, Johannes Heidecke, Chris Hesse, Alan Hickey, Wade Hickey, Peter Hoeschele, Brandon
Houghton, Kenny Hsu, Shengli Hu, Xin Hu, Joost Huizinga, Shantanu Jain, Shawn Jain, Joanne
Jang, Angela Jiang, Roger Jiang, Haozhun Jin, Denny Jin, Shino Jomoto, Billie Jonn, Heewoo
Jun, Tomer Kaftan, Łukasz Kaiser, Ali Kamali, Ingmar Kanitscheider, Nitish Shirish Keskar,
Tabarak Khan, Logan Kilpatrick, Jong Wook Kim, Christina Kim, Yongjik Kim, Jan Hendrik
Kirchner, Jamie Kiros, Matt Knight, Daniel Kokotajlo, Łukasz Kondraciuk, Andrew Kondrich,
Aris Konstantinidis, Kyle Kosic, Gretchen Krueger, Vishal Kuo, Michael Lampe, Ikai Lan, Teddy
Lee, Jan Leike, Jade Leung, Daniel Levy, Chak Ming Li, Rachel Lim, Molly Lin, Stephanie
Lin, Mateusz Litwin, Theresa Lopez, Ryan Lowe, Patricia Lue, Anna Makanju, Kim Malfacini,
Sam Manning, Todor Markov, Yaniv Markovski, Bianca Martin, Katie Mayer, Andrew Mayne,
Bob McGrew, Scott Mayer McKinney, Christine McLeavey, Paul McMillan, Jake McNeil, David
Medina, Aalok Mehta, Jacob Menick, Luke Metz, Andrey Mishchenko, Pamela Mishkin, Vinnie
Monaco, Evan Morikawa, Daniel Mossing, Tong Mu, Mira Murati, Oleg Murk, David Mély,
Ashvin Nair, Reiichiro Nakano, Rajeev Nayak, Arvind Neelakantan, Richard Ngo, Hyeonwoo
Noh, Long Ouyang, Cullen O’Keefe, Jakub Pachocki, Alex Paino, Joe Palermo, Ashley Pantuliano,
Giambattista Parascandolo, Joel Parish, Emy Parparita, Alex Passos, Mikhail Pavlov, Andrew Peng,
Adam Perelman, Filipe de Avila Belbute Peres, Michael Petrov, Henrique Ponde de Oliveira Pinto,
Michael, Pokorny, Michelle Pokrass, Vitchyr H. Pong, Tolly Powell, Alethea Power, Boris Power,
Elizabeth Proehl, Raul Puri, Alec Radford, Jack Rae, Aditya Ramesh, Cameron Raymond, Francis
Real, Kendra Rimbach, Carl Ross, Bob Rotsted, Henri Roussez, Nick Ryder, Mario Saltarelli, Ted
Sanders, Shibani Santurkar, Girish Sastry, Heather Schmidt, David Schnurr, John Schulman, Daniel
Selsam, Kyla Sheppard, Toki Sherbakov, Jessica Shieh, Sarah Shoker, Pranav Shyam, Szymon
Sidor, Eric Sigler, Maddie Simens, Jordan Sitkin, Katarina Slama, Ian Sohl, Benjamin Sokolowsky,
Yang Song, Natalie Staudacher, Felipe Petroski Such, Natalie Summers, Ilya Sutskever, Jie
Tang, Nikolas Tezak, Madeleine B. Thompson, Phil Tillet, Amin Tootoonchian, Elizabeth Tseng,
Preston Tuggle, Nick Turley, Jerry Tworek, Juan Felipe Cerón Uribe, Andrea Vallone, Arun
Vijayvergiya, Chelsea Voss, Carroll Wainwright, Justin Jay Wang, Alvin Wang, Ben Wang,
Jonathan Ward, Jason Wei, CJ Weinmann, Akila Welihinda, Peter Welinder, Jiayi Weng, Lilian
Weng, Matt Wiethoff, Dave Willner, Clemens Winter, Samuel Wolrich, Hannah Wong, Lauren
Workman, Sherwin Wu, Jeff Wu, Michael Wu, Kai Xiao, Tao Xu, Sarah Yoo, Kevin Yu, Qiming
Yuan, Wojciech Zaremba, Rowan Zellers, Chong Zhang, Marvin Zhang, Shengjia Zhao, Tianhao
Zheng, Juntang Zhuang, William Zhuk, and Barret Zoph. Gpt-4 technical report, 2024. URL
https://arxiv.org/abs/2303.08774.

Chen Pan, Fan Zhou, Xuanwei Hu, Xinxin Zhu, Wenxin Ning, Zi Zhuang, Siqiao Xue, James Zhang,

and Yunhua Hu. Deep optimal timing strategies for time series. In ICDM, 2023.

Joon Sung Park, Joseph C. O’Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, and
Michael S. Bernstein. Generative agents: Interactive simulacra of human behavior, 2023. URL
https://arxiv.org/abs/2304.03442.

Boci Peng, Yun Zhu, Yongchao Liu, Xiaohe Bo, Haizhou Shi, Chuntao Hong, Yan Zhang, and Siliang
Tang. Graph retrieval-augmented generation: A survey, 2024. URL https://arxiv.org/abs/
2408.08921.

15

Chen Qian, Wei Liu, Hongzhang Liu, Nuo Chen, Yufan Dang, Jiahao Li, Cheng Yang, Weize
Chen, Yusheng Su, Xin Cong, Juyuan Xu, Dahai Li, Zhiyuan Liu, and Maosong Sun. Chatdev:
Communicative agents for software development, 2024. URL https://arxiv.org/abs/2307.
07924.

Bo Qiao, Liqun Li, Xu Zhang, Shilin He, Yu Kang, Chaoyun Zhang, Fangkai Yang, Hang Dong, Jue
Zhang, Lu Wang, Minghua Ma, Pu Zhao, Si Qin, Xiaoting Qin, Chao Du, Yong Xu, Qingwei Lin,
Saravan Rajmohan, and Dongmei Zhang. Taskweaver: A code-first agent framework, 2024. URL
https://arxiv.org/abs/2311.17541.

RasaHQ. Rasa. https://github.com/RasaHQ/rasa, 2023.

Robert Tarjan. Depth-first search and linear graph algorithms. SIAM Journal on Computing, 1(2):

146–160, 1972. doi: 10.1137/0201010. URL https://doi.org/10.1137/0201010.

Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Amjad Almahairi, Yasmine Babaei, Nikolay
Bashlykov, Soumya Batra, Prajjwal Bhargava, Shruti Bhosale, Dan Bikel, Lukas Blecher, Cris-
tian Canton Ferrer, Moya Chen, Guillem Cucurull, David Esiobu, Jude Fernandes, Jeremy Fu,
Wenyin Fu, Brian Fuller, Cynthia Gao, Vedanuj Goswami, Naman Goyal, Anthony Hartshorn,
Saghar Hosseini, Rui Hou, Hakan Inan, Marcin Kardas, Viktor Kerkez, Madian Khabsa, Isabel
Kloumann, Artem Korenev, Punit Singh Koura, Marie-Anne Lachaux, Thibaut Lavril, Jenya Lee,
Diana Liskovich, Yinghai Lu, Yuning Mao, Xavier Martinet, Todor Mihaylov, Pushkar Mishra,
Igor Molybog, Yixin Nie, Andrew Poulton, Jeremy Reizenstein, Rashi Rungta, Kalyan Saladi,
Alan Schelten, Ruan Silva, Eric Michael Smith, Ranjan Subramanian, Xiaoqing Ellen Tan, Binh
Tang, Ross Taylor, Adina Williams, Jian Xiang Kuan, Puxin Xu, Zheng Yan, Iliyan Zarov, Yuchen
Zhang, Angela Fan, Melanie Kambadur, Sharan Narang, Aurelien Rodriguez, Robert Stojnic,
Sergey Edunov, and Thomas Scialom. Llama 2: Open foundation and fine-tuned chat models,
2023. URL https://arxiv.org/abs/2307.09288.

Harsh Trivedi, Tushar Khot, Mareike Hartmann, Ruskin Manku, Vinty Dong, Edward Li, Shashank
Gupta, Ashish Sabharwal, and Niranjan Balasubramanian. Appworld: A controllable world of
apps and people for benchmarking interactive coding agents. In Proceedings of the Annual Meeting
of the Association for Computational Linguistics (ACL), 2024. URL https://arxiv.org/abs/
2407.18901.

Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz
Kaiser, and Illia Polosukhin. Attention is all you need, 2023. URL https://arxiv.org/abs/
1706.03762.

Guanzhi Wang, Yuqi Xie, Yunfan Jiang, Ajay Mandlekar, Chaowei Xiao, Yuke Zhu, Linxi Fan, and
Anima Anandkumar. Voyager: An open-ended embodied agent with large language models. arXiv
preprint arXiv:2305.16291, 2023a. URL https://arxiv.org/abs/2305.16291.

Lei Wang, Chen Ma, Xueyang Feng, Zeyu Zhang, Hao Yang, Jingsen Zhang, Zhiyuan Chen, Jiakai
Tang, Xu Chen, Yankai Lin, Wayne Xin Zhao, Zhewei Wei, and Jirong Wen. A survey on large
language model based autonomous agents. Frontiers of Computer Science, 18(6), March 2024a.
ISSN 2095-2236. doi: 10.1007/s11704-024-40231-1. URL http://dx.doi.org/10.1007/
s11704-024-40231-1.

Peiyi Wang, Lei Li, Liang Chen, Zefan Cai, Dawei Zhu, Binghuai Lin, Yunbo Cao, Qi Liu, Tianyu
Liu, and Zhifang Sui. Large language models are not fair evaluators, 2023b. URL https:
//arxiv.org/abs/2305.17926.

Xuezhi Wang, Jason Wei, Dale Schuurmans, Quoc Le, Ed Chi, Sharan Narang, Aakanksha Chowdh-
ery, and Denny Zhou. Self-consistency improves chain of thought reasoning in language models,
2023c. URL https://arxiv.org/abs/2203.11171.

Yan Wang, Zhixuan Chu, Xin Ouyang, Simeng Wang, Hongyan Hao, Yue Shen, Jinjie Gu, Siqiao
Xue, James Y Zhang, Qing Cui, Longfei Li, Jun Zhou, and Sheng Li. Llmrg: Improving recommen-
dations through large language model reasoning graphs. In Proceedings of the AAAI Conference
on Artificial Intelligence (AAAI), 2024b. URL https://ojs.aaai.org/index.php/AAAI/
article/view/29887.

16

Zifeng Wang, Zizhao Zhang, Chen-Yu Lee, Han Zhang, Ruoxi Sun, Xiaoqi Ren, Guolong Su, Vincent
Perot, Jennifer Dy, and Tomas Pfister. Learning to prompt for continual learning. In Proceedings
of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 139–149, 2022.

Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Ed Chi, Quoc Le, and Denny Zhou.
Chain of thought prompting elicits reasoning in large language models. In Advances in Neural
Information Processing Systems (NeurIPS), 2022. URL https://arxiv.org/abs/2201.11903.
pdf.

Qingyun Wu, Gagan Bansal, Jieyu Zhang, Yiran Wu, Beibin Li, Erkang Zhu, Li Jiang, Xiaoyun
Zhang, Shaokun Zhang, Jiale Liu, Ahmed Hassan Awadallah, Ryen W White, Doug Burger, and
Chi Wang. Autogen: Enabling next-gen llm applications via multi-agent conversation, 2023a.
URL https://arxiv.org/abs/2308.08155.

Shijie Wu, Ozan Irsoy, Steven Lu, Vadim Dabravolski, Mark Dredze, Sebastian Gehrmann, Prabhan-
jan Kambadur, David Rosenberg, and Gideon Mann. Bloomberggpt: A large language model for fi-
nance. arXiv preprint arXiv:2303.17564, 2023b. URL https://arxiv.org/abs/2303.17564.

Siqiao Xue, Chao Qu, Xiaoming Shi, Cong Liao, Shiyi Zhu, Xiaoyu Tan, Lintao Ma, Shiyu Wang,
Shijun Wang, Yun Hu, Lei Lei, Yangfei Zheng, Jianguo Li, and James Zhang. A meta reinforcement
learning approach for predictive autoscaling in the cloud. In KDD ’22: The 28th ACM SIGKDD
Conference on Knowledge Discovery and Data Mining, Washington, DC, USA, August 14 - 18,
2022, pages 4290–4299. ACM, 2022a. URL https://doi.org/10.1145/3534678.3539063.

Siqiao Xue, Xiaoming Shi, Y James Zhang, and Hongyuan Mei. Hypro: A hybridly normalized prob-
abilistic model for long-horizon prediction of event sequences. In Advances in Neural Information
Processing Systems (NeurIPS), 2022b. URL https://arxiv.org/abs/2210.01753.

Siqiao Xue, Caigao Jiang, Wenhui Shi, Fangyin Cheng, Keting Chen, Hongjun Yang, Zhiping
Zhang, Jianshan He, Hongyang Zhang, Ganglin Wei, Wang Zhao, Fan Zhou, Danrui Qi, Hong Yi,
Shaodong Liu, and Faqiang Chen. Db-gpt: Empowering database interactions with private large
language models. arXiv preprint arXiv:2312.17449, 2023a. URL https://arxiv.org/abs/
2312.17449.

Siqiao Xue, Yan Wang, Zhixuan Chu, Xiaoming Shi, Caigao Jiang, Hongyan Hao, Gangwei Jiang,
Xiaoyun Feng, James Zhang, and Jun Zhou. Prompt-augmented temporal point process for
streaming event sequence. In Advances in Neural Information Processing Systems (NeurIPS),
2023b. URL https://arxiv.org/abs/2310.04993.

Siqiao Xue, Fan Zhou, Yi Xu, Ming Jin, Qingsong Wen, Hongyan Hao, Qingyang Dai, Caigao
Jiang, Hongyu Zhao, Shuo Xie, Jianshan He, James Zhang, and Hongyuan Mei. Weaverbird:
Empowering financial decision-making with large language model, knowledge base, and search
engine. arXiv preprint arXiv:2308.05361, 2023c. URL https://arxiv.org/abs/2308.05361.

Siqiao Xue, Tingting Chen, Fan Zhou, Qingyang Dai, Zhixuan Chu, and Hongyuan Mei. Famma:
A benchmark for financial domain multilingual multimodal question answering. arXiv preprint
arXiv:2410.04526, 2024a. URL https://arxiv.org/abs/2410.04526.

Siqiao Xue, Danrui Qi, Caigao Jiang, Wenhui Shi, Fangyin Cheng, Keting Chen, Hongjun Yang,
Zhiping Zhang, Jianshan He, Hongyang Zhang, Ganglin Wei, Wang Zhao, Fan Zhou, Hong Yi,
Shaodong Liu, Hongjun Yang, and Faqiang Chen. Demonstration of db-gpt: Next generation data
interaction system empowered by large language models. In Proceedings of the VLDB Endowment,
2024b. URL https://arxiv.org/abs/2404.10209.

Siqiao Xue, Xiaoming Shi, Zhixuan Chu, Yan Wang, Hongyan Hao, Fan Zhou, Caigao Jiang, Chen
Pan, James Y. Zhang, Qingsong Wen, Jun Zhou, and Hongyuan Mei. Easytpp: Towards open
benchmarking temporal point processes. In International Conference on Learning Representations
(ICLR), 2024c. URL https://arxiv.org/abs/2307.08097.

An Yang, Baosong Yang, Binyuan Hui, Bo Zheng, Bowen Yu, Chang Zhou, Chengpeng Li,
Chengyuan Li, Dayiheng Liu, Fei Huang, Guanting Dong, Haoran Wei, Huan Lin, Jialong Tang,
Jialin Wang, Jian Yang, Jianhong Tu, Jianwei Zhang, Jianxin Ma, Jianxin Yang, Jin Xu, Jingren
Zhou, Jinze Bai, Jinzheng He, Junyang Lin, Kai Dang, Keming Lu, Keqin Chen, Kexin Yang,

17

Mei Li, Mingfeng Xue, Na Ni, Pei Zhang, Peng Wang, Ru Peng, Rui Men, Ruize Gao, Runji Lin,
Shijie Wang, Shuai Bai, Sinan Tan, Tianhang Zhu, Tianhao Li, Tianyu Liu, Wenbin Ge, Xiaodong
Deng, Xiaohuan Zhou, Xingzhang Ren, Xinyu Zhang, Xipin Wei, Xuancheng Ren, Xuejing Liu,
Yang Fan, Yang Yao, Yichang Zhang, Yu Wan, Yunfei Chu, Yuqiong Liu, Zeyu Cui, Zhenru Zhang,
Zhifang Guo, and Zhihao Fan. Qwen2 technical report. arXiv preprint arXiv:2407.10671, 2024.
URL https://arxiv.org/abs/2407.10671.

Zhilin Yang, Peng Qi, Saizheng Zhang, Yoshua Bengio, William Cohen, Ruslan Salakhutdinov, and
Christopher D. Manning. HotpotQA: A dataset for diverse, explainable multi-hop question answer-
ing. In Proceedings of the Conference on Empirical Methods in Natural Language Processing
(EMNLP), 2018. URL https://aclanthology.org/D18-1259.pdf.

Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L. Griffiths, Yuan Cao, and Karthik
Narasimhan. Tree of Thoughts: Deliberate problem solving with large language models. In
Advances in Neural Information Processing Systems (NeurIPS), 2023a. URL https://arxiv.
org/abs/2305.10601.

Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, and Yuan Cao.
React: Synergizing reasoning and acting in language models. In Proceedings of the International
Conference on Learning Representations (ICLR), 2023b. URL https://arxiv.org/abs/2210.
03629.

Shukang Yin, Chaoyou Fu, Sirui Zhao, Ke Li, Xing Sun, Tong Xu, and Enhong Chen. A survey
on multimodal large language models. National Science Review, page nwae403, 11 2024. ISSN
2095-5138. doi: 10.1093/nsr/nwae403. URL https://doi.org/10.1093/nsr/nwae403.

Chern Han Yong and Risto Miikkulainen. Coevolution of role-based cooperation in multiagent
systems. IEEE Transactions on Autonomous Mental Development, 1(3):170–186, 2009. doi:
10.1109/TAMD.2009.2037732.

Hengjie Zhang, Sihai Zhao, Gang Kou, Cong-Cong Li, Yucheng Dong, and Francisco Herrera.
An overview on feedback mechanisms with minimum adjustment or cost in consensus reaching
Information Fusion, 60:65–
in group decision making: Research paradigms and challenges.
79, 2020.
ISSN 1566-2535. doi: https://doi.org/10.1016/j.inffus.2020.03.001. URL https:
//www.sciencedirect.com/science/article/pii/S156625351930781X.

Zeyu Zhang, Xiaohe Bo, Chen Ma, Rui Li, Xu Chen, Quanyu Dai, Jieming Zhu, Zhenhua Dong, and
Ji-Rong Wen. A survey on the memory mechanism of large language model based agents, 2024.
URL https://arxiv.org/abs/2404.13501.

Fan Zhou, Chen Pan, Lintao Ma, Yu Liu, Siqiao Xue, James Zhang, Jun Zhou, Hongyuan Mei,
Weitao Lin, Zi Zhuang, Wenxin Ning, and Yunhua Hu. Gmp-ar: Granularity message passing and
adaptive reconciliation for temporal hierarchy forecasting. In Proceedings of the AAAI Conference
on Artificial Intelligence (AAAI), 2024a. URL https://ojs.aaai.org/index.php/AAAI/
article/view/28795.

Fan Zhou, Siqiao Xue, Danrui Qi, Wenhui Shi, Wang Zhao, Ganglin Wei, Hongyang Zhang, Caigai
Jiang, Gangwei Jiang, Zhixuan Chu, and Faqiang Chen. Db-gpt-hub: Towards open benchmarking
text-to-sql empowered by large language models. arXiv preprint arXiv:2406.11434, 2024b. URL
https://arxiv.org/abs/2406.11434.

18

