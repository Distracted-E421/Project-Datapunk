Cheat codes for faster LLMs • The Register

theregister.com/2024/12/15/speculative_decoding

Tobias Mann

Hands on When it comes to AI inferencing, the faster you can generate a response, the
better – and over the past few weeks, we've seen a number of announcements from chip
upstarts claiming mind-bogglingly high numbers.

Most recently, Cerebras claimed it had achieved an inference milestone, generating 969
tokens/sec in Meta's 405 billion parameter behemoth – 539 tokens/sec at the model's full
128K context window.

In the small Llama 3.1 70B model, Cerebras reported even higher performance, topping
2,100 tokens/sec. Not far behind at 1,665 tokens/sec is AI chip startup Groq.

These numbers far exceed anything that's possible with GPUs alone. Artificial Analysis's
Llama 3.1 70B API leaderboard shows even the fastest GPU-based offerings top out at
around 120 tokens/sec, with conventional IaaS providers closer to 30.

Some of this is down to the fact that neither Cerebras or Groq's chips are GPUs. They're
purpose-built AI accelerators that take advantage of large banks of SRAM to overcome the
bandwidth bottlenecks normally associated with inference.

However, that doesn't account for such a large jump. Cerebras and Groq have previously
shown Llama 3.1 70B performance of around 450 and 250 tokens/sec, respectively.

Instead, the leap in performance is possible thanks to a technique called speculative
decoding.

A cheat code for performance

If you're not familiar with the concept of speculative decoding, don't worry. The technique is
actually quite simple and involves using a smaller draft model – say Llama 3.1 8B – to
generate the initial output, while a larger model – like Llama 3.1 70B or 405B – acts as a fact
checker in order to preserve accuracy.

When successful, research suggests the technique can speed up token generation by
anywhere from 2x to 3x while real-world applications have shown upwards of a 6x
improvement. 

You can think of this draft model a bit like a personal assistant who's an expert typist. They
can respond to emails a lot faster, and so long as their prediction is accurate, all you – in this
analogy the big model – have to do is click send. If they don't get it right on the odd email,

1/6

you can step in and correct it.

The result of using speculative decoding is, at least on average, higher throughputs because
the draft model requires fewer resources – both in terms of TOPS or FLOPS and memory
bandwidth. What's more, because the big model is still checking the results, the
benchmarkers at Artificial Analysis claim there's effectively no loss in accuracy compared to
just running the full model.

Try it for yourself

With all of that out of the way, we can move on to testing speculative decoding for ourselves.
Speculative decoding is supported in a number of popular model runners, but for the
purposes of this hands on we'll be using Llama.cpp.

This is not intended to be a guide for installing and configuring Llama.cpp. The good news is
getting it running is relatively straightforward and there are even some prebuilt packages
available for macOS, Windows, and Linux – which you can find here.

That said, for best performance with your specific hardware, we always recommend
compiling the latest release manually. You can find more information on compiling Llama.cpp
here.

Once you've got Llama.cpp deployed, we can spin up a new server using speculative
decoding. Start by locating the llama-server executable in your preferred terminal emulator.

Next we'll pull down our models. We'll be using a pair of 8-bit quantized GGUF models from
Hugging Face to keep things simple. For our draft model, we'll use Llama 3.2 1B and for our
main model, we'll use Llama 3.1 8B – which will require a little under 12GB of vRAM or
system memory to run.

If you're on macOS or Linux you can use wget to pull down the models.

wget https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-
GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q8_0.gguf 

wget https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-
3.2-1B-Instruct-Q8_0.gguf 

Next, we can test out speculative decoding by running the following command. Don't worry,
we'll go over each parameter in detail in a minute.

./llama-speculative -m Meta-Llama-3.1-8B-Instruct-Q8_0.gguf -md Llama-3.2-1B-
Instruct-Q8_0.gguf -c 4096 -cd 4096 -ngl 99 -ngld 99 --draft-max 16 --draft-min 4 -n 
128 -p "Who was the first prime minister of Britain?" 

2/6

Note: Windows users will want to replace ./llama-speculative with llama-
speculative.exe. If you aren't using GPU acceleration, you'll also want to remove -ngl 99
and -ngld 99.

A few seconds after entering our prompt, our answer will appear, along with a readout
showing the generation rate and how many tokens were drafted by the small model versus
how many were accepted by the big one. 

encoded    9 tokens in    0.033 seconds, speed:  269.574 t/s 
decoded  139 tokens in    0.762 seconds, speed:  182.501 t/s 
... 
n_draft   = 16 
n_predict = 139 
n_drafted = 208 
n_accept  = 125 
accept    = 60.096% 

The higher the acceptance rate, the higher the generation rate will be. In this case, we're
using fairly low parameter count models – particularly for the draft model – which may
explain why the accept rate is so low.

However, even with an acceptance rate of 60 percent, we're still seeing a pretty sizable uplift
in performance at 182 tokens/sec. Using Llama 3.1 8B without speculative decoding
enabled, we saw performance closer to 90–100 tokens/sec.

So what's going on in this command?  

./llama-speculative specifies that we want to use speculative decoding.
-m and -md set the path to the main (big) and draft (small) models, respectively
-c and -cd set the context window for the main and draft models, respectively
-ngl 99 and -ngld 99 tell Llama.cpp to offload all the layers of our main and draft
models to the GPU.
--draft-max and --draft-min set the maximum and minimum number of tokens the draft
model should generate at a time.
--draft-p-min sets the minimum probability of speculative decoding taking place.
-n sets the maximum number of tokens to output.
-p  is where we enter our prompt in quotes.

You can find a full breakdown of available parameters by running:

./llama-speculative --help 

If you'd like to use speculative decoding in a project, you can also spin up an OpenAI-
compatible API server using the following:

3/6

./llama-server -m Meta-Llama-3.1-8B-Instruct-Q8_0.gguf -md Llama-3.2-1B-Instruct-
Q8_0.gguf -c 4096 -cd 4096 -ngl 99 -ngld 99 --draft-max 8 --draft-min 4 --draft-p-min 
0.9 --host 0.0.0.0 --port 8087 

This will expose your API server on port 8087 when you can interact with it just like any other
OpenAI-compatible API server. This example is provided as a proof of concept. In a
production setting you'll likely want to set an API key and limit access via your firewall.

As a side note here, we also saw a modest performance uplift when including --sampling-
seq k to prioritize Top-K sampling, but your mileage may vary.

A full list of llama-server parameters can be found by running:

./llama-server --help 

With the server up and running, you can now point your application or a front-end like Open
WebUI to interact with the server. For more information on setting up the latter, check out our
guide on retrieval augmented generation here.

Why speculate?

Speculative decoding is by no means new. The technique was discussed at least as far back
as November 2022 – not long after ChatGPT triggered the AI arms race.

However, with monolithic models growing ever larger, speculative decode offers a means to
run large monolithic models like Llama 3.1 405B more efficiently without compromising on
accuracy.

While Meta's 405B foundation model might be tiny compared to OpenAI's GPT4 – which is
said to be roughly 1.7 trillion parameters in size – it's still an incredibly difficult model to run at
high throughputs.

At full resolution, achieving a generation rate of 25 tokens a second would require in excess
of 810GB of vRAM and more than 20 TB/sec of memory bandwidth. Achieving higher
performance would require additional levels of parallelism, which means more GPUs or
accelerators.

Using speculative decoding with something like Llama 3.1 70B as the draft model, you'd
need another 140GB of memory on top of the 810, but, in theory could achieve generation
rates well over 100 tokens/sec – until a mispredict happens, at which point your throughput
will crater.

And this is one of the challenges associated with speculative decoding: It's tremendously
effective at bolstering throughput, but in our testing, latency can be sporadic and
inconsistent.

4/6

We can actually see this in Cerebra's previously published results for Llama 3.1 70B when
using speculative decode. We don't know what the draft model is, but we're fairly certain it's
the 8B variant based on previous benchmarks. As you can see, there's a huge spike in
performance when speculative decode is implemented, but the variation in latency is still
huge – jumping up and down by 400 or more tokens.

To be perfectly clear, at 1,665 to 2,100 tokens/sec for 70B and up to 969 tokens/sec for
405B, there's a good chance the output will finish generating before you ever notice the
hiccup.

As for why you'd need an inference engine capable of generating hundreds or thousands of
tokens in the blink of an eye, Cerebras actually does a nice job of illustrating the problem.

In this slide, Cerebras makes its case for why faster inference and lower latency are
important for supporting CoT and agentic AI applications going forward – Click to enlarge

If you've tried out OpenAI's o1, you may have noticed it's a lot slower than previous models.
This is because the model employs a chain of thought (CoT) tree to break down the task into
individual steps, evaluate the responses, identify mistakes or gaps in logic, and correct them
before presenting an answer to the user.

Using CoT as part of the generative AI process is thought to improve the accuracy and
reliability of answers and mitigate errant behavior or hallucinations. However, the
consequence of the approach is it's a lot slower.

The next evolution of this is to combine CoT methods with multiple domain-specific models in
agentic workflow. According to Cerebras, such approaches require on the order of 100x as
many steps and computational power. So, the faster you can churn out tokens, the better you
can hide the added latency – or that's the idea anyway. ®

5/6

Editor's Note: The Register was provided an RTX 6000 Ada Generation graphics card by Nvidia, an Arc
A770 GPU by Intel, and a Radeon Pro W7900 DS by AMD to support stories like this. None of these
vendors had any input as to the content of this or other articles.

6/6

