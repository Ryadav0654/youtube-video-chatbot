from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import (
    RunnableParallel,
    RunnablePassthrough,
    RunnableLambda,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI


def format_docs(retrieved_docs):
    context_text = "\n\n".join(doc.page_content for doc in retrieved_docs)
    return context_text


def split_transcript_and_store(transcript):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.create_documents([transcript])
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vector_store = FAISS.from_documents(chunks, embeddings)
    return vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})


def summarize_transcript(transcript: str) -> str:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = PromptTemplate(
        template="""
        You are a helpful assistant.
        Summarize the following YouTube video transcript clearly and concisely.
        Focus on the main ideas and key takeaways.

        Transcript:
        {transcript}
""".strip(),
        input_variables=["transcript"],
    )

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"transcript": transcript})


def ask_query(retriever, query: str) -> str:
    model = ChatOpenAI(model="gpt-5.2", temperature=0, max_tokens=2000)
    prompt = PromptTemplate(
        template="""
        You are a helpful assistant.
        Answer ONLY from the provided transcript context.
        If the context is insufficient, just say you don't know.

        {context}
        Question: {question}
        """.strip(),
        input_variables=["context", "question"],
    )
    parallel_chain = RunnableParallel(
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
    )

    chain = parallel_chain | prompt | model | StrOutputParser()
    return chain.invoke(query)
