from langchain_core.prompts import ChatPromptTemplate

rephrase_system_prompt = (
    "Given a chat history, the list of uploaded documents, and the latest user question "
    "which might reference context in the chat history or those documents, "
    "formulate a standalone question which can be understood without the chat history. "
    "The documents available in this session are: [{file_names}]. "
    "Use these filenames to make the reformulated question more specific and optimized for search. "
    "Do NOT answer the question, just reformulate it and otherwise return it as is.\n\n"
    "--- CHAT HISTORY ---\n"
    "{chat_history}"
)

rephrase_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", rephrase_system_prompt),
        ("human", "{question}"),
    ]
)






qa_system_prompt = (
    "You are an expert AI acting as a {persona}. "
    "You have access to the following uploaded documents: [{file_names}].\n\n"
    "INSTRUCTIONS:\n"
    "1. Use the 'RETRIEVED CONTEXT' and 'CHAT HISTORY' provided below to answer the user's question.\n"
    "2. Provide a DEEP and DETAILED analysis. Do not give short answers. Expand on technical points and explain the reasoning.\n"
    "3. Structure your response using markdown (headers, bullet points, or bold text) for better readability.\n"
    "4. If the context doesn't contain the answer, state that you can't find it in the provided documents but offer general insights if appropriate.\n\n"
    "CRITICAL CITATION RULE:\n"
    "You MUST cite your sources. After any sentence or paragraph that uses info from a file, "
    "add: (Source: [original_filename], Page: [page_number]).\n\n"
    "--- CHAT HISTORY ---\n"
    "{chat_history}\n\n"
    "--- RETRIEVED CONTEXT ---\n"
    "{context}"
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        ("human", "{question}"),
    ]
)