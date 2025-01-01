Meet Memoripy: A Python Library that Brings Real
Memory Capabilities to AI Applications

marktechpost.com/2024/11/17/meet-memoripy-a-python-library-that-brings-real-memory-capabilities-to-ai-applications

November 17, 2024

By

Asif Razzaq
-

November 17, 2024
Artificial intelligence systems often struggle with retaining meaningful context over extended
interactions. This limitation poses challenges for applications such as chatbots and virtual
assistants, where maintaining a coherent conversation thread is essential. Most traditional AI
models operate in a stateless manner, focusing solely on immediate inputs without
considering the continuity of prior exchanges. This lack of effective memory leads to
fragmented and inconsistent interactions, hampering the ability to build truly engaging,
context-sensitive AI systems.

Meet Memoripy: A Python library that brings real memory capabilities to AI applications.
Memoripy addresses the problem of maintaining conversational context by equipping AI
systems with structured memory, allowing them to effectively store, recall, and build upon
prior interactions. Memoripy provides both short-term and long-term memory storage,
enabling AI systems to retain context from recent interactions while preserving important
information over the long term. By structuring memory in a way that mimics human cognition
—prioritizing recent events and retaining key details—Memoripy ensures that interactions
remain relevant and coherent over time.

🔗🔗 [Just Released] Meet EXAONE 3.5: A Three Model Series of Open-Source LLMs with
Top-tier Performance in Instruction Following and Long Context Capabilities (Promoted)
Memoripy organizes memory into short-term and long-term clusters, enabling the
prioritization of recent interactions for immediate recall while retaining significant historical
interactions for future use. This prevents the AI from becoming overwhelmed with excessive
data while ensuring relevant information is accessible. Memoripy also implements semantic
clustering, grouping similar memories together to facilitate efficient context retrieval. This
capability allows AI systems to quickly identify and link related memories, thereby enhancing
response quality. Furthermore, Memoripy incorporates memory decay and reinforcement
mechanisms, whereby less useful memories gradually fade, and frequently accessed
memories are reinforced, reflecting principles of human memory. Memoripy’s design
emphasizes local storage, which allows developers to handle memory operations entirely on

1/4

local infrastructure. This approach mitigates privacy concerns and provides flexibility in
integrating with locally hosted language models, as well as with external services like
OpenAI and Ollama.

To illustrate how Memoripy can be integrated into an AI application, consider the
following example:

🧵🧵 [Download] Evaluation of Large Language Model Vulnerabilities Report (Promoted)

2/4

from memoripy import MemoryManager, JSONStorage 

def main(): 

   # Replace 'your-api-key' with your actual OpenAI API key 
   api_key = "your-key" 
   if not api_key: 
       raise ValueError("Please set your OpenAI API key.") 

   # Define chat and embedding models 
   chat_model = "openai"  # Choose 'openai' or 'ollama' for chat 
   chat_model_name = "gpt-4o-mini"  # Specific chat model name 
   embedding_model = "ollama"  # Choose 'openai' or 'ollama' for embeddings 
   embedding_model_name = "mxbai-embed-large"  # Specific embedding model name 

   # Choose your storage option 
   storage_option = JSONStorage("interaction_history.json") 

   # Initialize the MemoryManager with the selected models and storage 
   memory_manager = MemoryManager( 
       api_key=api_key, 
       chat_model=chat_model, 
       chat_model_name=chat_model_name, 
       embedding_model=embedding_model, 
       embedding_model_name=embedding_model_name, 
       storage=storage_option 
   ) 

   # New user prompt 
   new_prompt = "My name is Khazar" 

   # Load the last 5 interactions from history (for context) 
   short_term, _ = memory_manager.load_history() 
   last_interactions = short_term[-5:] if len(short_term) >= 5 else short_term 

   # Retrieve relevant past interactions, excluding the last 5 
   relevant_interactions = memory_manager.retrieve_relevant_interactions(new_prompt, 

exclude_last_n=5) 

   # Generate a response using the last interactions and retrieved interactions
   response = memory_manager.generate_response(new_prompt, last_interactions, 

relevant_interactions) 

   # Display the response 
   print(f"Generated response:\n{response}") 

   # Extract concepts for the new interaction 
   combined_text = f"{new_prompt} {response}" 
   concepts = memory_manager.extract_concepts(combined_text) 

   # Store this new interaction along with its embedding and concepts 
   new_embedding = memory_manager.get_embedding(combined_text) 
   memory_manager.add_interaction(new_prompt, response, new_embedding, concepts) 

3/4

if __name__ == "__main__": 

   main()

In this script, the MemoryManager Is initialized with specified chat and embedding models,
along with a storage option. A new user prompt is processed, and the system retrieves
relevant past interactions to generate a contextually appropriate response. The interaction is
then stored with its embedding and extracted concepts for future reference.

Memoripy provides an essential advancement in building AI systems that are more context-
aware. The ability to retain and recall relevant information enables the development of virtual
assistants, conversational agents, and customer service systems that offer more consistent
and personalized interactions. For instance, a virtual assistant using Memoripy could
remember user preferences or details of prior requests, thereby offering a more tailored
response. Preliminary evaluations indicate that AI systems incorporating Memoripy exhibit
enhanced user satisfaction, producing more coherent and contextually appropriate
responses. Moreover, Memoripy’s emphasis on local storage is crucial for privacy-conscious
applications, as it allows data to be handled securely without reliance on external servers.

In conclusion, Memoripy represents a significant step towards more sophisticated AI
interactions by providing real memory capabilities that enhance context retention and
coherence. By structuring memory in a way that closely mimics human cognitive processes,
Memoripy paves the way for AI systems that can adapt based on cumulative user
interactions and offer more personalized, contextually aware experiences. This library
provides developers with the tools needed to create AI that not only processes inputs but
also learns from interactions in a meaningful way.

4/4

