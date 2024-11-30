# OmniParser

+-----------------------+-----------------------+-----------------------+
| > arXiv:2408.00203v1 | > **Yadong Lu**1**, | |
| > \[cs.CV\] 1 Aug | > Jianwei Yang**1**, | |
| > 2024 | > Yelong Shen**2**, | |
| | > Ahmed Awadallah**1 | |
| | > 1Microsoft Research | |
| | > 2 Microsoft Gen AI\ | |
| | > {yadonglu, | |
| | > jianwei.yang, | |
| | > yeshe, | |
| | > ahmed.awa | |
| | dallah}@microsoft.com | |
| | | |
| | **Abstract** | |
| | | |
| | > The recent success | |
| | > of large vision | |
| | > language models | |
| | > shows great | |
| | > potential in | |
| | > driv-ing the agent | |
| | > system operating on | |
| | > user interfaces. | |
| | > However, we argue | |
| | > that the power | |
| | > multimodal models | |
| | > like GPT-4V as a | |
| | > general agent on | |
| | > multiple operating | |
| | > systems across | |
| | > different | |
| | > applications is | |
| | > largely | |
| | > underestimated due | |
| | > to the lack of a | |
| | > robust screen | |
| | > parsing technique | |
| | > capable of: 1) | |
| | > reliably | |
| | > identifying | |
| | > interactable icons | |
| | > within the user | |
| | > interface, and 2) | |
| | > understanding the | |
| | > semantics of | |
| | > various elements in | |
| | > a screenshot and | |
| | > accurately | |
| | > associate the | |
| | > intended action | |
| | > with the | |
| | > corresponding | |
| | > region on the | |
| | > screen. To fill | |
| | > these gaps, we | |
| | > introduce | |
| | > OMNIPARSER, a | |
| | > comprehensive | |
| | > method for parsing | |
| | > user interface | |
| | > screenshots into | |
| | > structured | |
| | > elements, which | |
| | > significantly | |
| | > enhances the | |
| | > ability of GPT-4V | |
| | > to generate actions | |
| | > that can be | |
| | > accurately grounded | |
| | > in the | |
| | > corresponding | |
| | > regions of the | |
| | > interface. We first | |
| | > curated an | |
| | > interactable icon | |
| | > detection dataset | |
| | > using popular | |
| | > webpages and an | |
| | > icon description | |
| | > dataset. These | |
| | > datasets were | |
| | > utilized to | |
| | > fine-tune | |
| | > specialized models: | |
| | > a detection model | |
| | > to parse | |
| | > interactable | |
| | > regions on the | |
| | > screen and a | |
| | > caption model to | |
| | > extract the | |
| | > functional | |
| | > semantics of the | |
| | > detected elements. | |
| | > OMNIPARSER | |
| | > significantly | |
| | > improves GPT-4V's | |
| | > performance on | |
| | > ScreenSpot | |
| | > benchmark. And on | |
| | > Mind2Web and AITW | |
| | > benchmark, | |
| | > OMNIPARSER with | |
| | > screenshot only | |
| | > input outperforms | |
| | > the GPT-4V | |
| | > baselines requiring | |
| | > additional | |
| | > information outside | |
| | > of screenshot. | |
+-----------------------+-----------------------+-----------------------+
| | **1** | > **Introduction** |
+-----------------------+-----------------------+-----------------------+
| | > Large language | |
| | > models have shown | |
| | > great success in | |
| | > their understanding | |
| | > and reasoning | |
| | > capabilities. More | |
| | > recent works have | |
| | > explored the use of | |
| | > large | |
| | > vision-language | |
| | > models (VLMs) as | |
| | > agents to perform | |
| | > complex tasks on | |
| | > the user interface | |
| | > (UI) with the aim | |
| | > of completing | |
| | > tedious tasks to | |
| | > replace human | |
| | > efforts \[YZL+23, | |
| | > YYZ+23, DGZ+23, | |
| | > ZGK+24, HWL+23, | |
| | > YZS+24, WXJ+24, | |
| | > GFH+24, CSC+24\]. | |
| | > Despite the | |
| | > promising results, | |
| | > there remains a | |
| | > significant gap | |
| | > between current | |
| | > state-of-the-arts | |
| | > and creating widely | |
| | > usable agents that | |
| | > can work across | |
| | > multiple platforms, | |
| | > _e.g._ | |
| | > Windows/MacOS, | |
| | > IOS/Android and | |
| | > multiple | |
| | > applications (Web | |
| | > broswer Office365, | |
| | > PhotoShop, Adobe), | |
| | > with most previous | |
| | > work focusing on | |
| | > limiting | |
| | > applications or | |
| | > platforms. | |
+-----------------------+-----------------------+-----------------------+

> While large multimodal models like GPT-4V and other models trained on
> UI data \[HWL+23, YZS+24, CSC+24\] have demonstrated abilities to
> understand basic elements of the UI screenshot, action grounding
> remains one of the key challenges in converting the actions predicted
> by LLMs to the actual actions on screen in terms of keyboard/mouse
> movement or API call \[ZGK+24\]. It has been noted that GPT-4V is
> unable to produce the exact x-y coordinate of the button location,
> Set-of-Mark prompting \[YZL+23\] proposes to overlay a group of
> bounding boxes each with unique numeric IDs on to the original image,
> as a visual prompt sent to the GPT-4V model. By applying set-of-marks
> prompting, GPT-4V is able to ground the action into a specific
> bounding box which has ground truth location instead of a specific xy
> coordinate value, which greatly improves the robustness of the action
> grounding \[ZGK+24\]. However, the current solutions using SoM relies
> on parsed HTML information to extract bounding boxes for actionable
> elements such as buttons, which limits
>
> its usage to web browsing tasks. We aim to build a general approach
> that works on a variety of platforms and applications.
>
> In this work, we argue that previous pure vision-based screen parsing
> techniques are not satisfactory, which lead to significant
> underestimation of GPT-4V model's understanding capabilities. And a
> reliable vision-based screen parsing method that works well on general
> user interface is a key to improve the robustness of the agentic
> workflow on various operating systems and applications. We present
> OMNIPARSER, a general screen parsing tool to extract information from
> UI screenshot into structured bounding box and labels which enhances
> GPT-4V's performance in action prediction in a variety of user tasks.
>
> We list our contributions as follows:
>
> • We curate a interactable region detection dataset using bounding
> boxes extracted from DOM tree of popular webpages.
>
> • We propose OmniParser, a pure vision-based user interface screen
> parsing method that combines multiple finetuned models for better
> screen understanding and easier grounded action generation.
>
> • We evaluate our approach on ScreenSpot, Mind2Web and AITW benchmark,
> and demon-strated a significant improvement from the original GPT-4V
> baseline without requiring additional input other than screenshot.
>
> **2** **Related Works**
>
> **2.1** **UI Screen Understanding**
>
> There has been a line of modeling works focusing on detailed
> understanding of UI screens, such as Screen2Words \[WLZ+21\], UI-BERT
> \[BZX+21\], WidgetCaptioning \[LLH+20\], Action-BERT \[HSZ+21\]. These
> works demonstrated effective usage of multimodal models for extracting
> semantics of user screen. But these models rely on additional
> information such as view hierarchy, or are trained for visual question
> answering tasks or screen summary tasks.
>
> There are also a couple publicly available dataset that on UI screen
> understanding. Most notably the Rico dataset \[DHF+17\], which
> contains more than 66k unique UI screens and its view hierarchies.
> Later \[SWL+22\] auguments Rico by providing 500k human annotations on
> the original 66k RICO screens identifying various icons based on their
> shapes and semantics, and associations between selected general UI
> elements (like icons, form fields, radio buttons, text inputs) and
> their text labels. Same on mobile platform, PixelHelp \[LHZ+20\]
> provides a dataset that contains UI elements of screen spanning across
> 88 common tasks. In the same paper they also released RicoSCA which is
> a cleaned version of Rico. For the web and general OS domain, there
> are several works such Mind2Web \[DGZ+23\], MiniWob++\[LGP+18\],
> Visual-WebArena \[KLJ+24, ZXZ+24\], and OS-World \[XZC+24\] that
> provide simulated environment, but does not provide dataset explicitly
> for general screen understanding tasks such as interactable icon
> detection on real world websites.
>
> To address the absence of a large-scale, general web UI understanding
> dataset, and to keep pace with the rapid evolution of UI design, we
> curated an icon detection dataset using the DOM information from
> popular URLs avaialbe on the Web. This dataset features the up-to-date
> design of icons and buttons, with their bounding boxes retrieved from
> the DOM tree, providing ground truth locations.
>
> **2.2** **Autonomous GUI Agent**
>
> Recently there has been a lot of works on designing autonomous GUI
> agent to perform tasks in place of human users. One line of work is to
> train an end-to-end model to directly predict the next action,
> representative works include: Pixel2Act \[SJC+23\], WebGUM\[FLN+24\]
> in web domain, Ferret \[YZS+24\], CogAgent \[HWL+23\], and Fuyu
> \[BEH+23\] in Mobile domain. Another line of works involve leveraging
> existing multimodal models such as GPT-4V to perform user tasks.
> Representative works include MindAct agent \[DGZ+23\], SeeAct agent
> \[ZGK+24\] in web domain and agents in \[YYZ+23, WXY+24, RLR+23\] for
> mobile domain. These work often leverages the DOM information in web
> browser, or the view hierarchies in mobile apps to get the ground
> truth position of interactable elements of the screen, and use
> Set-Of-Marks\[YZL+23\] to overlay the

2

> bounding boxes on top of the screenshot then feed into the
> vision-language models. However, ground truth information of
> interactable elements may not always be available when the goal is to
> build a general agent for cross-platforms and cross-applications
> tasks. Therefore, we focus on providing a systematic approach for
> getting structured elements from general user screens.
>
> **3** **Methods**
>
> A complex task can usually be broken down into several steps of
> actions. Each step requires the model's (e.g. GPT-4V) ability to: 1)
> understand the UI screen in the current step, i.e. analyzing what is
> the screen content overall, what are the functions of detected icons
> that are labeled with numeric ID, and 2) predict what is the next
> action on the current screen that is likely to help complete the whole
> task. Instead of trying to accomplish the two goals in one call, we
> found it beneficial to extract some of the information such as
> semantics in the screen parsing stage, to alleviate the burden of
> GPT-4V so that it can leverages more information from the parsed
> screen and focus more on the action prediction.
>
> Hence we propose OMNIPARSER, which integrates the outputs from a
> finetuned interactable icon detection model, a finetuned icon
> description model, and an OCR module. This combination produces a
> structured, DOM-like representation of the UI and a screenshot
> overlaid with bounding boxes for potential interactable elements. We
> discuss each component of the OMNIPARSER in more details for the rest
> of the section.
>
> **3.1** **Interactable Region Detection**
>
> Identifying interactable regions from the UI screen is a crucial step
> to reason about what actions should be performed given a user tasks.
> Instead of directly prompting GPT-4V to predict the xy coordinate
> value of the screen that it should operate on, we follow previous
> works to use the Set-of-Marks approach \[YZL+23\] to overlay bounding
> boxes of interactable icons on top of UI screenshot, and ask GPT-4V to
> generate the bounding box ID to perform action on. However, different
> from \[ZGK+24, KLJ+24\] which uses the ground truth button location
> retrieved from DOM tree in web browswer, and \[YYZ+23\] which uses
> labeled bounding boxes in the AITW dataset \[RLR+23\], we finetune a
> detection model to extract interactable icons/buttons.
>
> Specifically, we curate a dataset of interactable icon detection
> dataset, containing 67k unique screen-shot images, each labeled with
> bounding boxes of interactable icons derived from DOM tree. We first
> took a 100k uniform sample of popular publicly availabe urls on the
> web \[OXL+22\], and collect bounding boxes of interactable regions of
> the webpage from the DOM tree of each urls. Some examples of the
> webpage and the interactable regions are shown in 2.
>
> Apart from interactable region detection, we also have a OCR module to
> extract bounding boxes of texts. Then we merge the bounding boxes from
> OCR detection module and icon detection module while removing the
> boxes that have high overlap (we use over 90% as a threshold). For
> every bounding box, we label it with a unique ID next to it using a
> simple algorithm to minimizing the overlap between numeric labels and
> other bounding boxes.
>
> **3.2** **Incorporating Local Semantics of Functionality**
>
> We found in a lot of cases where only inputting the UI screenshot
> overlayed with bounding boxes and associated IDs can be misleading to
> GPT-4V. We argue the limitation stems from GPT-4V's constrained
> ability to simultaneously perform the composite tasks of identifying
> each icon's semantic information and predicting the next action on a
> specific icon box. This has also been observed by several other works
> \[YYZ+23, ZGK+24\]. To address this issue, we incorporate the local
> semantics of functionality into the prompt, i.e. for each icons
> detected by the interactable region detection model, we use a
> finetuned model to generate description of functionality to the icons,
> and for each text boxes, we use the detected texts and its label.
>
> We perform more detailed analysis for this topic in section 4.1. To
> the best of our knowledge, there is no public model that is
> specifically trained for up-to-date UI icon description, and is
> suitable for our purpose to provide fast and accurate local semantics
> for the UI screenshot. Therefore we curate a dataset of 7k
> icon-description pairs using GPT-4o, and finetune a BLIP-v2 model
> \[LLSH23\] on this

3

![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image1.png){width="4.95in"
height="1.6444444444444444in"}

![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image2.png){width="4.95in"
height="1.9152777777777779in"}

![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image3.png){width="4.95in"
height="1.7277766841644795in"}

> Figure 1: Examples of parsed screenshot image and local semantics by
> OMNIPARSER. The inputs to OmniParse are user task and UI screenshot,
> from which it will produce: 1) parsed screenshot image with bounding
> boxes and numeric IDs overlayed, and 2) local semantics contains both
> text extracted and icon description.
>
> dataset. Details of dataset and training can be found in Appendix 7.1.
> After finetuning, we found the model is much more reliable in its
> description to common app icons. Examples can be seen in figure 4. And
> in figure 3, we show it is helpful to incorporate the semantics of
> local bounding boxes in the form of text prompt along with the UI
> screenshot visual prompt.
>
> **4** **Experiments and Results**
>
> We conduct experiments on several benchmarks to demonstrate the
> effectiveness of OMNIPARSER. We start by a motivating experiments
> showing that current GPT-4V model with set of mark prompting
> \[YZL+23\] is prone to incorrectly assigning label ID to the referred
> bounding boxes. Then we evaluate on Seeclick benchmark and Mind2Web to
> further showcase OMNIPARSER with local semantics can improve the
> GPT-4V's performance on real user tasks on different platforms and
> applications.
>
> **4.1** **Evaluation on SeeAssign Task**
>
> To test the ability of correctly predicting the label ID given the
> description of the bounding boxes for GPT-4v models, We handcrafted a
> dataset SeeAssign that contains 112 tasks consisting of samples

4

![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image4.png){width="5.5in"
height="1.6666666666666667in"}

> ![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image5.png){width="2.6944444444444446in"
> height="1.6333333333333333in"}
>
> ![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image6.png){width="2.6944444444444446in"
> height="1.6333333333333333in"}
>
> Figure 2: Examples from the Interactable Region Detection dataset. The
> bounding boxes are based on the interactable region extracted from the
> DOM tree of the webpage.
>
> from 3 different platforms: Mobile, Desktop and Web Browser. Each task
> includes a concise task description and a screenshot image. The task
> descriptions are manually created and we make sure each task refers to
> one of the detected bounding boxes, e.g. 'click on 'settings", 'click
> on the minimize button'. During evaluation, GPT-4V is prompted to
> predict the bounding box ID associated to it. Detailed prompt are
> specified in Appendix. The task screenshot images are sampled from the
> ScreenSpot \[CSC+24\] benchmark, where they are labeled with set of
> marks using OMNIPARSER. The tasks are further divided into 3
> sub-categories by difficulty: easy (less than 10 bounding boxes),
> medium (10-40 bounding boxes) and hard (more than 40 bounding boxes).
>
> From table 1, we see that GPT-4V often mistakenly assign the numeric
> ID to the table especially when there are a lot of bounding boxes over
> the screen. And by adding local semantics including texts within the
> boxes and short descriptions of the detected icons, GPT-4V's ability
> of correctly assigning the icon improves from 0.705 to 0.938.
>
> From figure 3, we see that without the description of the referred
> icon in the task, GPT-4V often fails to link the icon required in the
> task and the ground truth icon ID in the SoM labeled screenshot, which
> leads to hallucination in the response. With fine-grain local
> semantics added in the text prompt, it makes it much easier for GPT-4V
> to find the correct icon ID for the referred icon.

---

GPT-4V w.o. Easy Medium Hard Overall
local
semantics

---

                 0.913          0.692          0.620          0.705

GPT-4V w. 1.00 0.949 0.900 0.938
local
semantics

---

Table 1: Comparison of GPT-4V with and without local semantics

> **4.2** **Evaluation on ScreenSpot**
>
> ScreenSpot dataset \[CSC+24\] is a benchmark dataset that includes
> over 600 interface screenshots from mobile (iOS, Android), desktop
> (macOS, Windows), and web platforms. The task instructions are
> manually created so that each instruction corresponds to an actionable
> elements on the UI screen. We first evaluate the performance of
> OMNIPARSER using the this benchmark. In table 2, we can see across the
> 3 different platforms: Mobile, Desktop and Web, OMNIPARSER
> significantly improves the GPT-4V baseline. Noticeably, OMNIPARSER's
> performance even surpasses models

5

![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image7.png){width="5.444444444444445in"
height="2.5902777777777777in"}

> Figure 3: Examples from the SeeAssign evaluation. We can see that
> fine-grain local semantics improves the GPT-4V's ability to assign
> correct labels to the referred icon.
>
> that are specifically finetuned on GUI dataset including SeeClick,
> CogAgent and Fuyu by a large margin. We also note that incorporating
> the local semantics (OMNIPARSER w. LS in the table) further improves
> the overall performance. This corroborates with the finds in section
> 4.1 that incorporating local semantics of the UI screenshot in text
> format, i.e. adding OCR text and descriptions of the icon bounding
> boxes further helps GPT-4V to accurately identify the correct element
> to operate on. Furthermore, our findings indicate that the
> interactable region detection (ID) model we finetuned improves overall
> accuracy by an additional 4.3% compared to using the raw Grounding
> DINO model. This underscores the importance of accurately detecting
> interactable elements for the success of UI tasks. Overall, the
> results demonstrate that the UI screen understanding capability of
> GPT-4V is significantly underestimated and can be greatly enhanced
> with more accurate interactable elements detection and the
> incorporation of functional local semantics.

<table>
<colgroup>
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
<col style="width: 9%" />
</colgroup>
<thead>
<tr class="header">
<th colspan="2"><blockquote>
<p><strong>Methods</strong></p>
</blockquote></th>
<th><strong>Model Size</strong></th>
<th><strong>Text</strong></th>
<th rowspan="2"><blockquote>
<p><strong>Mobile</strong><br />
<strong>Icon/Widget</strong> 1.3%</p>
</blockquote></th>
<th><strong>Text</strong></th>
<th colspan="2" rowspan="2"><blockquote>
<p><strong>Desktop</strong><br />
<strong>Icon/Widget</strong> 3.6%</p>
</blockquote></th>
<th><strong>Text</strong></th>
<th rowspan="2"><blockquote>
<p><strong>Web</strong><br />
<strong>Icon/Widget</strong> 4.4%</p>
</blockquote></th>
<th><blockquote>
<p><strong>Average</strong></p>
</blockquote></th>
</tr>
<tr class="odd">
<th colspan="2"><blockquote>
<p>Fuyu</p>
</blockquote></th>
<th>8B</th>
<th><blockquote>
<p>41.0%</p>
</blockquote></th>
<th><blockquote>
<p>33.0%</p>
</blockquote></th>
<th><blockquote>
<p>33.9%</p>
</blockquote></th>
<th><blockquote>
<p>19.5%</p>
</blockquote></th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td colspan="2"><blockquote>
<p>CogAgent</p>
</blockquote></td>
<td>18B</td>
<td><blockquote>
<p>67.0%</p>
</blockquote></td>
<td>24.0%</td>
<td><blockquote>
<p>74.2%</p>
</blockquote></td>
<td colspan="2">20.0%</td>
<td><blockquote>
<p>70.4%</p>
</blockquote></td>
<td>28.6%</td>
<td><blockquote>
<p>47.4%</p>
</blockquote></td>
</tr>
<tr class="even">
<td colspan="2"><blockquote>
<p>SeeClick</p>
</blockquote></td>
<td>9.6B</td>
<td><blockquote>
<p>78.0%</p>
</blockquote></td>
<td>52.0%</td>
<td><blockquote>
<p>72.2%</p>
</blockquote></td>
<td colspan="2">30.0%</td>
<td><blockquote>
<p>55.7%</p>
</blockquote></td>
<td>32.5%</td>
<td><blockquote>
<p>53.4%</p>
</blockquote></td>
</tr>
<tr class="odd">
<td colspan="2"><blockquote>
<p>MiniGPT-v2</p>
</blockquote></td>
<td>7B</td>
<td>8.4%</td>
<td>6.6%</td>
<td>6.2%</td>
<td colspan="2">2.9%</td>
<td>6.5%</td>
<td>3.4%</td>
<td><blockquote>
<p>5.7%</p>
</blockquote></td>
</tr>
<tr class="even">
<td colspan="2"><blockquote>
<p>Qwen-VL</p>
</blockquote></td>
<td>9.6B</td>
<td>9.5%</td>
<td>4.8%</td>
<td>5.7%</td>
<td colspan="2">5.0%</td>
<td>3.5%</td>
<td>2.4%</td>
<td><blockquote>
<p>5.2%</p>
</blockquote></td>
</tr>
<tr class="odd">
<td colspan="2"><blockquote>
<p>GPT-4V</p>
</blockquote></td>
<td>-</td>
<td><blockquote>
<p>22.6%</p>
</blockquote></td>
<td>24.5%</td>
<td><blockquote>
<p>20.2%</p>
</blockquote></td>
<td colspan="2">11.8%</td>
<td>9.2%</td>
<td>8.8%</td>
<td><blockquote>
<p>16.2%</p>
</blockquote></td>
</tr>
<tr class="even">
<td colspan="2"><blockquote>
<p>OmniParser (w.o. LS, w. GD)</p>
</blockquote></td>
<td>-</td>
<td rowspan="3"><blockquote>
<p>92.7% <strong>94.8%</strong> 93.9%</p>
</blockquote></td>
<td>49.4%</td>
<td colspan="2">64.9%</td>
<td><blockquote>
<p>26.3%</p>
</blockquote></td>
<td rowspan="3">77.3% <strong>83.0%</strong> 81.3</td>
<td>39.7%</td>
<td><blockquote>
<p>58.38%</p>
</blockquote></td>
</tr>
<tr class="odd">
<td colspan="2"><blockquote>
<p>OmniParser (w. LS + GD)</p>
</blockquote></td>
<td>-</td>
<td rowspan="2"><blockquote>
<p>53.7%<br />
<strong>57.0%</strong></p>
</blockquote></td>
<td colspan="2" rowspan="2">89.3% <strong>91.3%</strong></td>
<td rowspan="2"><blockquote>
<p>44.9%<br />
<strong>63.6%</strong></p>
</blockquote></td>
<td rowspan="2"><blockquote>
<p>45.1%<br />
<strong>51.0%</strong></p>
</blockquote></td>
<td rowspan="2"><blockquote>
<p>68.7%<br />
<strong>73.0%</strong></p>
</blockquote></td>
</tr>
<tr class="even">
<td colspan="2"><blockquote>
<p>OmniParser (w. LS + ID)</p>
</blockquote></td>
<td>-</td>
</tr>
<tr class="odd">
<td colspan="11"><blockquote>
<p>Table 2: Comparison of different approaches on ScreenSpot Benchmark.
LS is short for local semantics of functionality, GD is short for
Grounding DINO, and ID is short for the interactable region detection
model we finetune.</p>
</blockquote></td>
</tr>
<tr class="even">
<td><strong>4.3</strong></td>
<td colspan="10"><blockquote>
<p><strong>Evaluation on Mind2Web</strong></p>
</blockquote></td>
</tr>
</tbody>
</table>

> In order to test how OMNIPARSER is helpful to the web navigation
> secnario, We evaluate on \[DGZ+23\] benchmark. There are 3 different
> categories of task in the test set: Cross-Domain, Cross-Website, and
> Cross-Tasks. We used a cleaned version of Mind2Web tests set processed
> from the raw HTML dump which eliminates a small number of samples that
> has incorrect bounding boxes. In total we have 867, 167, 242 tasks in
> the test set from Cross-Domain, Cross-Website, and Cross-Tasks
> category respectively. During evaluation, we feed both the parsed
> screen results and the action history as text prompt, and SOM labeled
> screenshot to GPT-4V similar to the prompting strategy in \[YYZ+23,
> ZGK+24\]. Following the original paper, we perform offline evaluation
> focusing on the element accuracy, Operation F1 and step success rate
> averaged across the task.

6

> In the first section of the table (row 1-3), We report numbers from a
> set of open source VL models as it appears in \[ZGK+24, CSC+24\]. Here
> CogAgent and Qwen-VL are not finetuned on the Mind2Web training set.
> More detailed information about model settings can be found in the
> Appendix7.4.
>
> In the second section of the table (row 4-9) we report numbers from
> Mind2web paper \[DGZ+23\] and SeeAct \[ZGK+24\] paper. In this
> section, all of the approaches use the HTML elements selected by a
> finetuned element proposal model on Mind2Web training set which
> produces top 50 relevant elements on the HTML page based on the user
> task. Additionally, GPT-4V+SOM and GPT-4V+textual choices corresponds
> to the SeeAct with image annotation, and textual choices grounding
> methods respectively. In GPT-4V+SOM, the set of mark (SOM) boxes are
> selected from the element proposal model, and are labeled with the
> ground truth location extracted from HTML. In contrast, GPT-4V+textual
> uses DOM information of the selected relevant elements directly in the
> text prompt, rather than overlaying bounding boxes on top of
> screenshot. The better performance of textual choice corroborates with
> the experiment results in 4.1.
>
> In the last section (row 10-11), we report numbers from OMNIPARSER. We
> observe GPT-4V augumented with local semantics of icon functionality
> and the finetuned interactable region detection model (w. LS + ID)
> performs better than the model with raw grounding DINO model (w. LS +
> GD) in all of the categories.
>
> Further, without using parsed HTML information, OMNIPARSER is able to
> outperform GPT-4's performance that uses HTML in every sub-category by
> a large margin, suggesting the substantial benefit of the screen
> parsing results provided by OMNIPARSER. Additionally, OMNIPARSER
> outper-forms the GPT-4V+SOM by a large margin. Compared to
> GPT-4V+textual choices, OMNIPARSER significantly outperforms in
> Cross-Website and Cross-Domain category (+4.1% and +5.2%), while
> underperforming (-0.8%) slightly in the Cross-Task category, which
> indicates that OMNIPARSER provides higher quality information compared
> ground truth element information from DOM and top-k relevant elemnt
> proposal used by the GPT-4V+textual choices set-up, and make the
> GPT-4V easier to make a accurate action prediction. Lastly, OMNIPARSER
> with GPT-4V significantly outperform all the other trained models
> using only UI screenshot such as SeeClick and Qwen-VL.

<table>
<colgroup>
<col style="width: 8%" />
<col style="width: 8%" />
<col style="width: 8%" />
<col style="width: 8%" />
<col style="width: 8%" />
<col style="width: 8%" />
<col style="width: 8%" />
<col style="width: 8%" />
<col style="width: 8%" />
<col style="width: 8%" />
<col style="width: 8%" />
<col style="width: 8%" />
</colgroup>
<thead>
<tr class="header">
<th><blockquote>
<p><strong>Methods</strong></p>
</blockquote></th>
<th colspan="2" rowspan="4"><p><strong>Input Types</strong></p>
<blockquote>
<p>HTML free image</p>
<p>✓✓</p>
<p>✓✓</p>
<p>✓✓</p>
<p>××</p>
</blockquote></th>
<th colspan="3" rowspan="2"><p><strong>Cross-Website</strong></p>
<blockquote>
<p><strong>Ele.Acc Op.F1</strong> <strong>Step SR</strong></p>
<p>18.4 42.2 13.4</p>
<p>13.2 83.5 9.2</p>
</blockquote></th>
<th colspan="3" rowspan="2"><p><strong>Cross-Domain</strong></p>
<blockquote>
<p><strong>Ele.Acc</strong> <strong>Op.F1</strong> <strong>Step
SR</strong></p>
<p>20.6 42.0 15.5</p>
<p>14.1 84.3 12.0</p>
</blockquote></th>
<th></th>
<th><strong>Cross-Task</strong></th>
<th></th>
</tr>
<tr class="odd">
<th><blockquote>
<p>CogAgent<br />
Qwen-VL</p>
</blockquote></th>
<th><strong>Ele.Acc</strong> 22.4<br />
14.1</th>
<th><blockquote>
<p><strong>Op.F1</strong> 53.0<br />
84.3</p>
</blockquote></th>
<th><strong>Step SR</strong> 17.6<br />
12.0</th>
</tr>
<tr class="header">
<th><blockquote>
<p>SeeClick</p>
</blockquote></th>
<th>21.4</th>
<th>80.6</th>
<th>16.4</th>
<th>23.2</th>
<th>84.8</th>
<th>20.8</th>
<th>28.3</th>
<th>87.0</th>
<th>25.5</th>
</tr>
<tr class="odd">
<th><blockquote>
<p>MindAct (gen)</p>
</blockquote></th>
<th rowspan="3"><blockquote>
<p>13.9<br />
<strong>42.0</strong><br />
19.3</p>
</blockquote></th>
<th>44.7</th>
<th rowspan="3"><blockquote>
<p>11.0<br />
<strong>38.9</strong><br />
16.2</p>
</blockquote></th>
<th>14.2</th>
<th>44.7</th>
<th>11.9</th>
<th>14.2</th>
<th>44.7</th>
<th rowspan="3"><blockquote>
<p>11.9<br />
<strong>39.6</strong><br />
18.6</p>
</blockquote></th>
</tr>
<tr class="header">
<th><blockquote>
<p>MindAct</p>
</blockquote></th>
<th>×</th>
<th>×</th>
<th>65.2</th>
<th>42.1</th>
<th>66.5</th>
<th>39.6</th>
<th>42.1</th>
<th>66.5</th>
</tr>
<tr class="odd">
<th><blockquote>
<p>GPT-3.5-Turbo</p>
</blockquote></th>
<th>×</th>
<th>×</th>
<th>48.8</th>
<th>21.6</th>
<th>52.8</th>
<th>18.6</th>
<th>21.6</th>
<th>52.8</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td><blockquote>
<p>GPT-4<br />
GPT-4V+som</p>
</blockquote></td>
<td rowspan="4"><blockquote>
<p>×<br />
×<br />
×<br />
✓<br />
✓</p>
</blockquote></td>
<td rowspan="2"><blockquote>
<p>×<br />
✓<br />
✓</p>
</blockquote></td>
<td><blockquote>
<p>35.8<br />
-</p>
</blockquote></td>
<td><blockquote>
<p>51.1<br />
-</p>
</blockquote></td>
<td><blockquote>
<p>30.1<br />
32.7</p>
</blockquote></td>
<td><blockquote>
<p>37.1<br />
-</p>
</blockquote></td>
<td><blockquote>
<p>46.5<br />
-</p>
</blockquote></td>
<td><blockquote>
<p>26.4<br />
23.7</p>
</blockquote></td>
<td rowspan="2"><blockquote>
<p>41.6<br />
-<br />
<strong>46.4</strong></p>
</blockquote></td>
<td><blockquote>
<p>60.6<br />
-</p>
</blockquote></td>
<td>36.2<br />
20.3</td>
</tr>
<tr class="even">
<td><blockquote>
<p>GPT-4V+textual choice</p>
</blockquote></td>
<td>38.0</td>
<td>67.8</td>
<td>32.4</td>
<td>42.4</td>
<td>69.3</td>
<td>36.8</td>
<td>73.4</td>
<td>40.2</td>
</tr>
<tr class="odd">
<td>OmniParser (w. LS + GD)</td>
<td>✓</td>
<td>41.5</td>
<td rowspan="2"><blockquote>
<p>83.2<br />
<strong>84.8</strong></p>
</blockquote></td>
<td>36.1</td>
<td rowspan="2"><blockquote>
<p>44.9<br />
<strong>45.5</strong></p>
</blockquote></td>
<td rowspan="2"><blockquote>
<p>80.6<br />
<strong>85.7</strong></p>
</blockquote></td>
<td>36.8</td>
<td>42.3</td>
<td>86.7</td>
<td>38.7</td>
</tr>
<tr class="even">
<td>OmniParser (w. LS + ID)</td>
<td>✓</td>
<td>41.0</td>
<td>36.5</td>
<td><strong>42.0</strong></td>
<td>42.4</td>
<td><strong>87.6</strong></td>
<td>39.4</td>
</tr>
</tbody>
</table>

Table 3: Comparison of different methods across various categories on
Mind2Web benchmark.

> **4.4** **Evaluation on AITW**
>
> In additional to evaluation on multi-step web browsing tasks, we
> assess OMNIPARSER on the mobile navigating benchmark AITW \[RLR+23\],
> which contains 30k instructions and 715k trajectories. We use the same
> train/test split as in \[CSC+24\] based on instructions, which retain
> only one trajectory for each instructions and no intersection between
> train and test. For a fair comparison, we only use their test split
> for evaluation and discard the train set as our method does not
> require finetuing.
>
> In table 4, we report the GPT-4V baseline in \[YYZ+23\] paper, which
> corresponds to the best performing set up (GPT-4V ZS+history) that
> uses UI elements detected by IconNet \[SWL+22\] through set-of-marks
> prompting \[YZL+23\] for each screenshot at every step of the
> evaluation. The detected UI elements consist of either OCR-detected
> text or an icon class label, which is one of the 96 possible icon
> types identified by IconNet. Additionally, action history is also
> incorporated at each step's prompt as well. We used the exact same
> prompt format in \[YYZ+23\] except the results from the IconNet model
> is replaced with the output of the finetuned interactable region
> detection (ID) model. Interestingly, we found that the ID model can
> generalize well to mobile screen. By replacing the IconNet with the
> interactable region detection (ID) model we finetuned on the collected
> webpages, and incorporating local semantics of icon functionality
> (LS), we find OMNIPARSER

7

> delivers significantly improved performance across most
> sub-categories, and a 4.7% increase in the overall score compared to
> the best performing GPT-4V + history baseline.

+-------+-------+-------+-------+-------+-------+-------+-------+-------+
| > **| |** | _|_ | **Go | **Sin | **Web | ** |
| Metho | | Modal | \_Gene | \_Inst | ogleA | gle\_\_ | Shopp | Overa |
| ds**\ | | ity** | ral** | all**| pps** | 9.4 | ing**| ll**\ |
| > C | | Text | 5.9 | 4.4 | 10.5 | | 8.4 | 7.7 |
| hatGP | | | | | | | | |
| T-CoT | | | | | | | | |
+=======+=======+=======+=======+=======+=======+=======+=======+=======+
| PaLM | | Text | \- | \- | \- | \- | \- | > |
| 2-CoT | | | | | | | | 39.6 |
+-------+-------+-------+-------+-------+-------+-------+-------+-------+
| G | | Image | 41.7 | 42.6 | 49.8 | > | 45.7 | > |
| PT-4V | | | | | | 72.8\ | | 50.5 |
| image | | | | | | > | | |
| -only | | | | | | **78 | | |
| | | | | | | .3**\ | | |
| | | | | | | > | | |
| | | | | | | 77.4 | | |
+-------+-------+-------+-------+-------+-------+-------+-------+-------+
| GPT | | Image | 43.0 | 46.1 | 49.2 | | 48.2 | > |
| -4V + | | | | | | | | 53.0 |
| hi | | | | | | | | |
| story | | | | | | | | |
+-------+-------+-------+-------+-------+-------+-------+-------+-------+
| OmniP | | Image | **4 | **5 | **5 | | **5 | > **5 |
| arser | | | 8.3** | 7.8** | 1.6** | | 2.9** | 7.7** |
| (w. | | | | | | | | |
| LS + | | | | | | | | |
| ID) | | | | | | | | |
+-------+-------+-------+-------+-------+-------+-------+-------+-------+
| > | | | | | | | | |
| Table | | | | | | | | |
| > 4: | | | | | | | | |
| > | | | | | | | | |
| Compa | | | | | | | | |
| rison | | | | | | | | |
| > of | | | | | | | | |
| > | | | | | | | | |
| diff | | | | | | | | |
| erent | | | | | | | | |
| > me | | | | | | | | |
| thods | | | | | | | | |
| > a | | | | | | | | |
| cross | | | | | | | | |
| > va | | | | | | | | |
| rious | | | | | | | | |
| > | | | | | | | | |
| tasks | | | | | | | | |
| > and | | | | | | | | |
| > ov | | | | | | | | |
| erall | | | | | | | | |
| > p | | | | | | | | |
| erfor | | | | | | | | |
| mance | | | | | | | | |
| > in | | | | | | | | |
| > | | | | | | | | |
| AITW | | | | | | | | |
| > | | | | | | | | |
| bench | | | | | | | | |
| mark. | | | | | | | | |
+-------+-------+-------+-------+-------+-------+-------+-------+-------+
| **5** | > | | | | | | | |
| | **Dis | | | | | | | |
| | cussi | | | | | | | |
| | ons\*\* | | | | | | | |
+-------+-------+-------+-------+-------+-------+-------+-------+-------+

> In this section, we discuss a couple of common failure cases of
> OMNIPARSER with examples and potential approach to improve.
>
> **Repeated Icons/Texts** From analysis of the the GPT-4V's response
> log, we found that GPT-4V often fails to make the correct prediction
> when the results of the OMNIPARSER contains multiple repeated
> icons/texts, which will lead to failure if the user task requires
> clicking on one of the buttons. This is illustrated by the figure 7
> (Left) in the Appendix. A potential solution to this is to add finer
> grain descriptions to the repeated elements in the UI screenshot, so
> that the GPT-4V is aware of the existence of repeated elements and
> take it into account when predicting next action.
>
> **Corase Prediction of Bounding Boxes** One common failure case of
> OMNIPARSER is that it fails to detect the bounding boxes with correct
> granularity. In figure 7 (Right), the task is to click on the text
> 'MORE'. The OCR module of OMNIPARSER detects text bounding box 8 which
> encompass the desired text. But since it uses center of the box as
> predicted click point, it falls outside of the ground truth bounding
> box. This is essentially due to the fact that the OCR module we use
> does not have a notion of which text region are hyperlink and
> clickable. Hence we plan to train a model that combines OCR and
> interactable region detection into one module so that it can better
> detect the clickable text/hyperlinks.
>
> **Icon Misinterpretation** We found that in some cases the icon with
> similar shape can have different meanings depending on the UI
> screenshot. For example, in figure 8, the task is to find button
> related to 'More information', where the ground truth is to click the
> three dots icon in the upper right part of the screenshot. OMNIPARSER
> successfully detects all the relevant bounding boxes, but the icon
> description model interpret it as: \"a loading or buffering
> indicator\". We think this is due to the fact that the icon
> description model is only able to see each icon cropped from image,
> while not able to see the whole picture during both training and
> inference. So without knowing the full context of the image, a symbol
> of three dots can indeed mean loading buffer in other scenarios. A
> potential fix to this is to train an icon description model that is
> aware of the full context of the image.
>
> **6** **Conclusion**
>
> In this report, We propose OMNIPARSER, a general vision only approach
> that parse UI screenshots into structured elements. OMNIPARSER
> encompasses two finetuned models: an icon detection model and a
> functional description models. To train them, we curated an
> interactable region detection dataset using popular webpages, and an
> icon functional description dataset. We demonstrate that with the
> parsed results, the performance of GPT-4V is greatly improved on
> ScreenSpot benchmarks. It achieves better performance compared to
> GPT-4V agent that uses HTML extracted information on Mind2Web, and
> outperforms GPT-4V augmented with specialized Android icon detection
> model on AITW benchmark. We hope OMNIPARSER can serve as a general and
> easy-to-use tool that has the capability to parse general user screen
> across both PC and mobile platforms without any dependency on extra
> information such as HTML and view hierarchy in Android.

8

> **Acknowledgement**
>
> We would like to thank Corby Rosset and authors of ClueWeb22 for
> providing the seed urls for which we use to collect data to finetune
> the interactable region detection model. The data collection pipeline
> adapted AutoGen's multimodal websurfer code for extracting interatable
> elements in DOM, for which we thank Adam Fourney. We also thank Dillon
> DuPont for providing the processed version of mind2web benchmark.
>
> **References**

+-----------------------------------+-----------------------------------+
| > \[BEH+23\] \[BZX+21\] | > Rohan Bavishi, Erich Elsen, |
| > | > Curtis Hawthorne, Maxwell Nye, |
| > \[CSC+24\] \[DGZ+23\] | > Augustus Odena, Arushi Somani, |
| > \[DHF+17\] | > and Sa˘gnak Ta¸sırlar. |
| | > Introducing our multimodal |
| \[FLN+24\] | > models, 2023. |
| | > |
| \[GFH+24\] | > Chongyang Bai, Xiaoxue Zang, |
| | > Ying Xu, Srinivas Sunkara, |
| \[HSZ+21\] | > Abhinav Rastogi, Jindong Chen, |
| | > and Blaise Aguera y Arcas. |
| | > Uibert: Learning generic |
| | > multimodal representations for |
| | > ui understanding, 2021. |
| | |
| | Kanzhi Cheng, Qiushi Sun, Yougang |
| | Chu, Fangzhi Xu, Yantao Li, |
| | Jianbing Zhang, and Zhiyong Wu. |
| | Seeclick: Harnessing gui |
| | grounding for advanced visual gui |
| | agents, 2024. |
| | |
| | > Xiang Deng, Yu Gu, Boyuan |
| | > Zheng, Shijie Chen, Samuel |
| | > Stevens, Boshi Wang, Huan Sun, |
| | > and Yu Su. Mind2web: Towards a |
| | > generalist agent for the web, |
| | > 2023. |
| | > |
| | > Biplab Deka, Zifeng Huang, Chad |
| | > Franzen, Joshua Hibschman, |
| | > Daniel Afergan, Yang Li, |
| | > Jeffrey Nichols, and Ranjitha |
| | > Kumar. Rico: A mobile app |
| | > dataset for building |
| | > data-driven design |
| | > applications. In _Proceedings |
| | > of the 30th Annual ACM |
| | > Symposium on User Interface |
| | > Software and Technology_, UIST |
| | > '17, page 845--854, New York, |
| | > NY, USA, 2017. Association for |
| | > Computing Machinery. |
| | > |
| | > Hiroki Furuta, Kuang-Huei Lee, |
| | > Ofir Nachum, Yutaka Matsuo, |
| | > Aleksandra Faust, Shixiang |
| | > Shane Gu, and Izzeddin Gur. |
| | > Multimodal web navigation with |
| | > instruction-finetuned |
| | > foundation models, 2024. |
| | > |
| | > Izzeddin Gur, Hiroki Furuta, |
| | > Austin Huang, Mustafa Safdari, |
| | > Yutaka Matsuo, Dou-glas Eck, |
| | > and Aleksandra Faust. A |
| | > real-world webagent with |
| | > planning, long context |
| | > understanding, and program |
| | > synthesis, 2024. |
| | > |
| | > Zecheng He, Srinivas Sunkara, |
| | > Xiaoxue Zang, Ying Xu, Lijuan |
| | > Liu, Nevan Wichers, Gabriel |
| | > Schubiner, Ruby Lee, Jindong |
| | > Chen, and Blaise Agüera y |
| | > Arcas. Actionbert: Leveraging |
| | > user actions for semantic |
| | > understanding of user |
| | > interfaces, 2021. |
+===================================+===================================+
+-----------------------------------+-----------------------------------+

> \[HWL+23\] Wenyi Hong, Weihan Wang, Qingsong Lv, Jiazheng Xu, Wenmeng
> Yu, Junhui Ji, Yan Wang, Zihan Wang, Yuxuan Zhang, Juanzi Li, Bin Xu,
> Yuxiao Dong, Ming Ding, and Jie Tang. Cogagent: A visual language
> model for gui agents, 2023.

+-----------------------------------+-----------------------------------+
| \[KLJ+24\] | > Jing Yu Koh, Robert Lo, |
| | > Lawrence Jang, Vikram Duvvur, |
| \[LGP+18\] | > Ming Chong Lim, Po-Yu Huang, |
| | > Graham Neubig, Shuyan Zhou, |
| \[LHZ+20\] | > Ruslan Salakhutdinov, and |
| | > Daniel Fried. Visualwebarena: |
| \[LLH+20\] | > Evaluating multimodal agents on |
| | > realistic visual web tasks. |
| \[LLSH23\] | > _arXiv preprint |
| | > arXiv:2401.13649_, 2024. |
| | > |
| | > Evan Zheran Liu, Kelvin Guu, |
| | > Panupong Pasupat, Tianlin Shi, |
| | > and Percy Liang. Rein-forcement |
| | > learning on web interfaces |
| | > using workflow-guided |
| | > exploration. In _Interna-tional |
| | > Conference on Learning |
| | > Representations (ICLR)_, 2018. |
| | > |
| | > Yang Li, Jiacong He, Xin Zhou, |
| | > Yuan Zhang, and Jason |
| | > Baldridge. Mapping natural |
| | > language instructions to mobile |
| | > UI action sequences. In Dan |
| | > Jurafsky, Joyce Chai, Natalie |
| | > Schluter, and Joel Tetreault, |
| | > editors, _Proceedings of the |
| | > 58th Annual Meeting of the |
| | > Association for Computational |
| | > Linguistics_, pages 8198--8210, |
| | > Online, July 2020. Association |
| | > for Computational Linguistics. |
| | > |
| | > Yang Li, Gang Li, Luheng He, |
| | > Jingjie Zheng, Hong Li, and |
| | > Zhiwei Guan. Widget captioning: |
| | > Generating natural language |
| | > description for mobile user |
| | > interface elements, 2020. |
| | > |
| | > Junnan Li, Dongxu Li, Silvio |
| | > Savarese, and Steven Hoi. |
| | > Blip-2: Bootstrapping |
| | > language-image pre-training |
| | > with frozen image encoders and |
| | > large language models, 2023. |
+===================================+===================================+
+-----------------------------------+-----------------------------------+

9

+-----------------------------------+-----------------------------------+
| > \[OXL+22\] \[RLR+23\] | > Arnold Overwijk, Chenyan Xiong, |
| > \[SJC+23\] | > Xiao Liu, Cameron VandenBerg, |
| | > and Jamie Callan. Clueweb22: 10 |
| | > billion web documents with |
| | > visual and semantic |
| | > information, 2022. |
| | > |
| | > Christopher Rawles, Alice Li, |
| | > Daniel Rodriguez, Oriana Riva, |
| | > and Timothy Lillicrap. Android |
| | > in the wild: A large-scale |
| | > dataset for android device |
| | > control, 2023. |
| | > |
| | > Peter Shaw, Mandar Joshi, James |
| | > Cohan, Jonathan Berant, |
| | > Panupong Pasupat, Hexiang Hu, |
| | > Urvashi Khandelwal, Kenton Lee, |
| | > and Kristina Toutanova. From |
| | > pixels to ui actions: Learning |
| | > to follow instructions via |
| | > graphical user interfaces, |
| | > 2023. |
+===================================+===================================+
+-----------------------------------+-----------------------------------+

> \[SWL+22\] Srinivas Sunkara, Maria Wang, Lijuan Liu, Gilles Baechler,
> Yu-Chung Hsiao, Jindong Chen, Abhanshu Sharma, and James Stout.
> Towards better semantic understanding of mobile interfaces. _CoRR_,
> abs/2210.02663, 2022.
>
> \[WLZ+21\] Bryan Wang, Gang Li, Xin Zhou, Zhourong Chen, Tovi
> Grossman, and Yang Li. Screen2words: Automatic mobile ui summarization
> with multimodal learning, 2021.

+-----------------------------------+-----------------------------------+
| \[WXJ+24\] | > Junyang Wang, Haiyang Xu, |
| | > Haitao Jia, Xi Zhang, Ming Yan, |
| | > Weizhou Shen, Ji Zhang, Fei |
| | > Huang, and Jitao Sang. |
| | > Mobile-agent-v2: Mobile device |
| | > operation assistant with |
| | > effective navigation via |
| | > multi-agent collaboration, |
| | > 2024. |
+===================================+===================================+
+-----------------------------------+-----------------------------------+

> \[WXY+24\] Junyang Wang, Haiyang Xu, Jiabo Ye, Ming Yan, Weizhou Shen,
> Ji Zhang, Fei Huang, and Jitao Sang. Mobile-agent: Autonomous
> multi-modal mobile device agent with visual perception, 2024.

+-----------------------------------+-----------------------------------+
| \[XZC+24\] | > Tianbao Xie, Danyang Zhang, |
| | > Jixuan Chen, Xiaochuan Li, |
| \[YYZ+23\] | > Siheng Zhao, Ruisheng Cao, Toh |
| | > Jing Hua, Zhoujun Cheng, |
| > \[YZL+23\] \[YZS+24\] | > Dongchan Shin, Fangyu Lei, |
| > | > Yitao Liu, Yiheng Xu, Shuyan |
| > \[ZGK+24\] \[ZXZ+24\] | > Zhou, Silvio Savarese, Caiming |
| | > Xiong, Victor Zhong, and Tao |
| | > Yu. Osworld: Benchmarking |
| | > multimodal agents for |
| | > open-ended tasks in real |
| | > computer environments, 2024. |
| | > |
| | > An Yan, Zhengyuan Yang, Wanrong |
| | > Zhu, Kevin Lin, Linjie Li, |
| | > Jianfeng Wang, Jianwei Yang, |
| | > Yiwu Zhong, Julian McAuley, |
| | > Jianfeng Gao, Zicheng Liu, and |
| | > Lijuan Wang. Gpt-4v in |
| | > wonderland: Large multimodal |
| | > models for zero-shot smartphone |
| | > gui navigation, 2023. |
| | > |
| | > Jianwei Yang, Hao Zhang, Feng |
| | > Li, Xueyan Zou, Chunyuan Li, |
| | > and Jianfeng Gao. Set-of-mark |
| | > prompting unleashes |
| | > extraordinary visual grounding |
| | > in gpt-4v, 2023. |
| | > |
| | > Keen You, Haotian Zhang, Eldon |
| | > Schoop, Floris Weers, Amanda |
| | > Swearngin, Jeffrey Nichols, |
| | > Yinfei Yang, and Zhe Gan. |
| | > Ferret-ui: Grounded mobile ui |
| | > understanding with multimodal |
| | > llms, 2024. |
| | > |
| | > Boyuan Zheng, Boyu Gou, Jihyung |
| | > Kil, Huan Sun, and Yu Su. |
| | > Gpt-4v(ision) is a generalist |
| | > web agent, if grounded, 2024. |
| | > |
| | > Shuyan Zhou, Frank F Xu, Hao |
| | > Zhu, Xuhui Zhou, Robert Lo, |
| | > Abishek Sridhar, Xi-anyi Cheng, |
| | > Yonatan Bisk, Daniel Fried, Uri |
| | > Alon, et al. Webarena: A |
| | > realistic web environment for |
| | > building autonomous agents. |
| | > _ICLR_, 2024. |
+===================================+===================================+
+-----------------------------------+-----------------------------------+

10

> **7** **Appendix**
>
> **7.1** **Details of Icon-Description Dataset**
>
> In figure 4, we see that the original BLIP-2 model tend to focus on
> describing shapes and colors of app icons, while struggling to
> recognize the semantics of the icon. This motivates us to finetune
> this model on an icon description dataset. For the dataset, we use the
> result of parsed icon bounding boxes inferenced by the interactable
> icon detection model on the ScreenSpot dataset since it contains
> screenshots on both mobile and PC. For the description, we ask GPT-4o
> whether the object presented in the parsed bounding box is an app
> icon. If GPT-4o decides the image is an icon, it outputs one-sentence
> description of the icon about the potential functionality. And if not,
> GPT-4o will output 'this is not an icon', while still including this
> in the dataset. In the end, we collected 7185 icon-description pairs
> for finetuning.
>
> We finetune BLIP-2 model for 1 epoch on the generated dataset with
> constant learning rate of 1*e−*5, no weight decay and Adam optimizer.
> We show a few of the qualitative examples of finetuned model vs the
> original model in figure 4.

![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image8.png){width="4.399998906386702in"
height="2.2777777777777777in"}

> Figure 4: Example comparisons of icon description model using BLIP-2
> (Left) and its finetuned version (Right). Original BLIP-2 model tend
> to focus on describing shapes and colors of app icons. After
> finetuning on the functionality semantics dataset, the model is able
> to show understanding of semantics of some common app icons.
>
> **7.2** **Training details of Interactable Icon Region Detection
> Model**
>
> As introduced in 3.1, we train a YOLOv8 model on the interactable icon
> region detection dataset. We collect in total of 66990 samples where
> we split 95% (63641) for training, and 5% (3349) for validation. We
> train for 20 epochs with batch size of 256, learning rate of 1*e−*3,
> and the Adam optimizer on 4 GPUs. We show the training curve in figure 5.
>
> **7.3** **Details of SeeAssign Evaluation**
>
> **7.3.1** **Prompt Used for GPT-4V**
>
> GPT-4V without local semantics:
>
> Here is a UI screenshot image with bounding boxes and corresponding
> labeled ID overlayed on top of it, your task is {task}. Which icon box
> label you should operate on? Give a brief analysis, then put your
> answer in the format of \\n'''Box with label ID: \[xx\]'''\\n
>
> GPT-4V with local semantics:
>
> Here is a UI screenshot image with bounding boxes and corresponding
> labeled ID overlayed on top of it, and here is a list of icon/text box
> description: {

11

![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image9.png){width="4.399998906386702in"
height="2.2in"}

Figure 5: Training curves of interactable icon region detection model.

> parsed_local_semantics}. Your task is {task}. Which bounding box label
> you should operate on? Give a brief analysis, then put your answer in
> the format of \\n'''Box with label ID: \[xx\]'''\\n
>
> **7.4** **Details of Mind2Web Evaluation**
>
> Here we list more details of each baseline in table 3.
>
> **SeeClick, QWen-VL** SeeClick is a finetuned version of Qwen-VL on
> the Mind2Web training set and we report both of their numbers in their
> paper.
>
> **CogAgent** CogAgent number is taken from the SEEAct paper
> \[ZGK+24\], where they report cogagent-chat-hf checkpoint that is not
> fine-tuned on Mind2Web for experiments.
>
> **MindAct(Gen), MindAct, GPT-3.5-Turbo, GPT-4** The numbers for these
> baseline are taken from the Mind2Web \[DGZ+23\] paper, where they use
> HTML information to augument the corresponding web agent.
>
> **GPT-4V+som** This model corresponds to the image annotation
> grounding method in SeeAct paper, where the som boxes extracted from
> the selelcted HTML elements are provided to GPT-4V to make action
> prediction.
>
> **GPT-4V+textual choice** This corresponds to the best performing
> scenario in SeeAct paper (except the Oracle), that uses the selected
> HTML elments information in a multi-choice question format as input to
> the GPT-4V agent.
>
> **7.4.1** **Qualitative Examples**
>
> We list a few more examples to demonstrate local semantics of icon
> function description helps GPT-4V make better action prediction in
> figure 6.

12

![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image10.png){width="5.444444444444445in"
height="4.254166666666666in"}

> Figure 6: More examples of local semantics of icon functionality help
> with GPT-4V in grounding actions
>
> ![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image11.png){width="2.6944444444444446in"
> height="2.672221128608924in"}
>
> ![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image12.png){width="2.6944444444444446in"
> height="2.4986100174978128in"}
>
> Figure 7: Analysis of failure cases. All the bounding boxes are
> labeled by which relies only on the screenshot. **Left**: There are in
> total 7 similar enable button for 7 different alarm times in the
> parsed screenshot. And the correct Icon ID corresponding to alarm 7:30
> is 27. GPT-4V fails to make the correct prediction. **Right:** The
> ground truth region to click is the text 'MORE' inside bounding box 8.
> We can see that the OCR fails to detect the text 'MORE' in bold, and
> only detects the bounding box 8, which encompasses 'MORE'. Since the
> predicts the click point as the center of the box, so it the predicted
> click point falls outside of the ground truth region, which leads to
> failure in this task.

13

![](vertopal_8b135079be2243fa973aa9776b3d0217/media/image13.png){width="4.95in"
height="2.325in"}

> Figure 8: Analysis of failure cases. The task is to find button
> related to 'More information', and the ground truth is to click the
> three dots icon in the upper right part of the screenshot. The the
> icon functional description model does not take into account the
> context of this page and interpret it as: \"a loading or buffering
> indicator\" which causes the failure.

14
