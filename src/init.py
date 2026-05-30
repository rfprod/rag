import os
from dotenv import load_dotenv

from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_qdrant import QdrantVectorStore
from langchain_ollama import OllamaEmbeddings

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

urls = ["https://github.com/rfprod/nx-ng-starter/blob/main/README.md"]
docs = [WebBaseLoader(url).load() for url in urls]
docs_list = [item for sublist in docs for item in sublist]
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=250, chunk_overlap=0
)

doc_splits = text_splitter.split_documents(docs_list)

embedding = OllamaEmbeddings(base_url="http://localhost:11434", model="llama3.2:latest")

vector_store = QdrantVectorStore.from_documents(
    documents=doc_splits,
    embedding=embedding,
    collection_name="documents",
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    api_key=os.getenv("QDRANT__SERVICE__API_KEY", None),
)
retriever = vector_store.as_retriever(k=4)

prompt = PromptTemplate(
    template="""You are an assistant for question-answering tasks.
  Use the following documents to answer the question.
  If you don't know the answer, just say that you don't know.
  Use three sentences maximum and keep the answer concise:
  Question: {question}
  Documents: {documents}
  Answer:
  """,
    input_variables=["question", "documents"],
)

llm = ChatOllama(
    base_url="http://localhost:11434", model="llama3.2:latest", temperature=0
)

rag_chain = prompt | llm | StrOutputParser()


class RAGApplication:
    def __init__(self, retriever, rag_chain):
        self.retriever = retriever
        self.rag_chain = rag_chain

    def run(self, question):
        documents = self.retriever.invoke(question)
        doc_texts = "\\n".join([doc.page_content for doc in documents])
        answer = self.rag_chain.invoke({"question": question, "documents": doc_texts})
        return answer


rag_application = RAGApplication(retriever, rag_chain)

question = "What operating systems does nx-ng-starter support?"
answer = rag_application.run(question)
print("Question:", question)
print("Answer:", answer)
