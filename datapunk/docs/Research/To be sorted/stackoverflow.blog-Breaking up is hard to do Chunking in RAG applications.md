Breaking up is hard to do: Chunking in RAG applications

stackoverflow.blog/2024/12/27/breaking-up-is-hard-to-do-chunking-in-rag-applications

Ryan Donovan

[Ed. note: While we take some time to rest up over the holidays and prepare for next year,
we are re-publishing our top ten posts for the year. Please enjoy our favorite work this year
and we’ll see you in 2025.]

As you go deeper down the rabbit hole building LLM-based applications, you may find that
you need to root your LLM responses in your source data. Fine-tuning an LLM with your
custom data may get you a generative AI model that understands your particular domain, but
it may still be subject to inaccuracies and hallucinations. This has led a lot of organizations to
look into retrieval-augmented generation (RAG) to ground LLM responses in specific data
and back them up with sources.

With RAG, you create text embeddings of the pieces of data that you want to draw from and
retrieve. That allows you to place a piece of the source text within the semantic space that
LLMs use to create responses. At the same time, the RAG system can return the source text
as well, so that the LLM response is backed by human-created text with a citation.

When it comes to RAG systems, you’ll need to pay special attention to how big the individual
pieces of data are. How you divide your data up is called chunking, and it’s more complex
than embedding whole documents. This article will take a look at some of the current thinking
around chunking data for RAG systems.

1/4

Why is chunking important?

The size of the chunked data is going to make a huge difference in what information comes
up in a search. When you embed a piece of data, the whole thing is converted into a vector.
Include too much in a chunk and the vector loses the ability to be specific to anything it
discusses. Include too little and you lose the context of the data.

Don’t just take our word for it; we spoke to Roie Schwaber-Cohen, Staff Developer Advocate
at Pinecone, for the podcast, and discussed all things RAG and chunking. Pinecone is one of
the leading companies producing vector databases.

“The reason to start thinking about how to break my content into smaller chunks is so that
when I retrieve it, it actually hits the correct thing. You're taking a user's query and you're
embedding it,” says Schwaber-Cohen. “You are going to compare that with an embedding of
your content. If the size of the content that you're embedding is wildly different from the size
of the user's query, you're going to have a higher chance of getting a lower similarity score.”

In short, size matters.

But you have to consider both the size of the query and response. As Schwaber-Cohen said,
you’ll be matching text chunk vectors with query vectors. But you also need to consider the
size of the chunks used as responses. “If I embedded, let's say, a full chapter of content
instead of just a page or a paragraph, the vector database is going to find some semantic
similarity between the query and that chapter. Now, is all that chapter relevant? Probably not.
More importantly, is the LLM going to be able to take the content that you retrieved and the
query that the user had and then produce a relevant response out of that? Maybe, maybe
not. Maybe there's confounding elements within that content, maybe there aren't
confounding elements between that content. It's going to be dependent on the use case.”

If chunking were cut and dried, the industry would have settled on a standard pretty quickly,
but the best chunking strategy is dependent on the use case. Fortunately, you’re not just
chunking data, vectorizing it, and crossing your fingers. You’ve also got metadata. This can
be a link to the original chunk or larger portions of the document, categories and tags, text, or
really anything at all. “It's kind of like a JSON blob that you can use to filter out things,” said
Schwaber-Cohen. “You can reduce the search space significantly if you're just looking for a
particular subset of the data, and you could use that metadata to then link the content that
you're using in your response back to the original content.”

Chunking strategies

With these concerns in mind, several common chunking strategies have emerged. The most
basic is to chunk text into fixed sizes. This works for fairly homogenous datasets that use
content of similar formats and sizes, like news articles or blog posts. It’s the cheapest

2/4

method in terms of the amount of compute you’ll need, but it doesn’t take into account the
context of the content that you’re chunking. That might not matter for your use case, but it
might end up mattering a lot.

You could also use random chunk sizes if your dataset is a non-homogenous collection of
multiple document types. This approach can potentially capture a wider variety of semantic
contexts and topics without relying on the conventions of any given document type. Random
chunks are a gamble, though, as you might end up breaking content across sentences and
paragraphs, leading to meaningless chunks of text.

For both of these types, you can apply the chunking method over sliding windows; that is,
instead of starting new chunks at the end of the previous chunk, new chunks overlap the
content of the previous one and contain part of it. This can better capture the context around
the edges of each chunk and increase the semantic relevance of your overall system. The
tradeoff is that it requires greater storage requirements and can store redundant information,
which can require extra processing in searches and make it harder for your RAG system to
efficiently pull the right source.

This method won’t work for some content. “I'm not going to have to combine chunks together
to make something make sense, and those pieces that actually need to stay together,” said
Schwaber-Cohen. “For example, code examples. If you just took a piece of code Markdown
and gave it to their recursive text chunker, you would get back broken code. “

A slightly more complicated method pays attention to the content itself, albeit in a naive way.
Context-aware chunking splits documents based on punctuation like periods, commas, or
paragraph breaks or use markdown or HTML tags if your content contains them. Most text
contains these sort of semantic markers that indicate what characters make up a meaningful
chunk, so using them makes a lot of sense. You can recursively chunk documents into
smaller, overlapping pieces, so that a chapter gets vectorized and linked, but so does each
page, paragraph, and sentence it contains.

For example, when we were implementing semantic search on Stack Overflow, we
configured our embedding pipeline to consider questions, answers, and comments as
discrete semantic chunks. Our Q&A pages are highly structured and have a lot of information
built into the structure of the page. Anyone who uses Stack Overflow for Teams can organize
their data using that same semantically rich structure.

While context-aware chunking can provide good results, it does require additional pre-
processing to segment the text. This can add additional computing requirements that slow
down the chunking process. If you’re processing a batch of documents once and then
drawing from them forever, that’s no problem. But if your dataset includes documents that
may change over time, then this resource requirement can add up.

3/4

Then there’s adaptive chunking, which takes the context-aware method to a new level. It
chunks based on the content of each document. Many adaptive chunking techniques use
machine learning themselves to determine the best size for any given chunk and where they
overlap. Obviously, an additional layer of ML here makes this a compute-intensive method,
but it can produce highly-tailored and context-aware semantic units.

In general, though, Schwaber-Cohen recommends smaller chunks: "What we found for the
most part is that you would have better luck if you're able to create smaller semantically
coherent units that correspond to potential user queries."

Figuring out what works best

There are a lot of possible chunking strategies, so figuring out the optimal one for your use
case takes a little work. Some say that chunking strategies need to be custom for every
document that you process. You can use multiple strategies at the same time. You can apply
them recursively over a document. But ultimately, the goal is to store the semantic meaning
of a document and its constituent parts in a way that an LLM can retrieve based on query
strings.

When you’re testing chunking methods, test the results of your RAG system against sample
queries. Rate them with human reviews and with LLM evaluators. When you’ve determined
which method consistently performs better, you can further enhance results by filtering
results based on the cosine similarity scores.

Whatever method you end up using, chunking is just one part of the generative AI tech
puzzle. You’ll need LLMs, vector databases, and storage to make your AI project a success.
Most importantly, you’ll need a goal, or your GenAI feature won’t make it past the
experimentation phase.

4/4

