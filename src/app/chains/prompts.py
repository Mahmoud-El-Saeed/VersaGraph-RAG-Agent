from langchain_core.prompts import ChatPromptTemplate

# We injected {persona} and strict citation instructions
qa_system_prompt = (
    "You are a specialized AI acting as a {persona}. "
    "Use the following pieces of retrieved context AND the chat history to answer "
    "the question. If you don't know the answer, say that you don't know. "
    "Keep your answer professional, concise, and within three sentences if possible.\n\n"
    "CRITICAL INSTRUCTION FOR CITATIONS:\n"
    "You MUST cite your sources whenever you use information from the retrieved context. "
    "Add the citation at the end of the relevant sentence in this exact format: "
    "(Source: [original_filename], Page: [page_number]).\n"
    "Do not cite the chat history, only the retrieved context files.\n\n"
    "--- CHAT HISTORY ---\n"
    "{chat_history}\n"
    "--------------------\n"
    "--- RETRIEVED CONTEXT ---\n"
    "{context}"
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        ("human", "{question}"),
    ]
)