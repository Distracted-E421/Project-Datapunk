Pinecone expands vector database with cascading
retrieval, boosting enterprise AI accuracy by up to 48%

venturebeat.com/data-infrastructure/pinecone-expands-vector-database-with-cascading-retrieval-boosting-enterprise-

ai-accuracy-by-up-to-48

Sean Michael Kerner

December 2, 2024

Pinecone has made a name for itself in recent years as being one of the leading native
vector database platforms. Pinecone is continuing to differentiate in an increasingly
competitive market with new capabilities to help solve enterprise AI challenges.

Today Pinecone announced a series of updates to its namesake vector database platform.
The updates include a new cascading retrieval approach that combines the benefits of dense
and sparse vector retrieval.

Pinecone is also deploying a new set of reranking technologies designed to help improve
accuracy and efficiency for vector embeddings.

The company claims the new innovations will help enterprises to build enterprise AI
applications that are up to 48% more accurate.

“We’re trying to expand beyond our core vector database to solve basically the broader
retrieval challenges,” Gareth Jones, staff product manager at Pinecone, told VentureBeat.

Understanding the difference between dense and sparse vectors

To date, Pinecone’s vector database technology, like many others, has relied on dense
vectors.

Jones explained that dense text embedding models produce fixed-length vectors that
capture semantic and contextual meaning. They are powerful for maintaining context, but not
as effective for keyword search or entity lookup. He noted that without significant fine-tuning,
dense models can sometimes struggle with concepts like phone numbers, part numbers and
other specific entities. 

In contrast, sparse indexes allow for more flexible keyword search and entity lookup.
Pinecone is adding sparse indexes to address the limitations of dense vector search alone.
The overall goal is to provide a more comprehensive retrieval solution.

The idea of combining keyword type searches with vectors is not new. It’s a concept that is
often lumped under the term “hybrid search.” Jones referred to the new Pinecone approach
as “cascading retrieval.” He argued that it is different from a generic hybrid search.

1/2

Jones said that cascading retrieval goes beyond a simple hybrid approach of running dense
and sparse indexes in parallel. The approach involves adding a cascading set of
improvements, such as reranking models, on top of the dense and sparse retrieval. The
cascading approach combines the strengths of different techniques, rather than just doing a
basic score-based fusion of the results.

How reranking further improves Pinecone’s vector database
accuracy

Pinecone is also improving the accuracy of results with the integration of a series of new
reranker technologies.

An AI reranker is a critical tool in the enterprise AI stack, optimizing the order or “rank” of
results from a query. Pinecone’s update includes multiple reranking options, including
Cohere’s new state-of-the-art Rerank 3.5 model and Pinecone’s own high-performance
rerankers. 

By building its own reranker technology, Pinecone is aiming to further differentiate itself in the
crowded vector database market. The new Pinecone rerankers are the first rerankers
developed by the company, and aim to deliver the best possible results, albeit with some
latency impact. According to Pinecone’s own analysis its new pinecone-rerank-v0 on its own
can improve search accuracy by up to 60%, in an evaluation with the Benchmarking-IR
(BEIR) benchmark. The new pinecone-sparse-english-v0 reranking model has the potential
to specifically boost performance for keyword-based queries by up to 44%.

The key benefit of these reranking components is that they allow Pinecone to deliver
optimized retrieval results by combining the outputs of the dense and sparse indexes. This
matters to enterprises because it allows them to consolidate their retrieval stack and get
better performance without having to manage multiple vendors or models. Pinecone is
aiming to provide a tightly integrated stack where users can simply send text and get back
reranked results, without the overhead of managing the underlying components.

On top of having more features inside the platform, Jones emphasized, the new offering is a
serverless one that helps enterprises optimize costs. The serverless architecture
automatically handles scaling based on actual usage patterns.

“We maintain a serverless pay-go model,” Jones states. “People’s traffic to their application
looks very different on a particular day, whether it be queries or writing documents to index…
we handle all of that, so they’re not over-provisioning at any given time.”

2/2

