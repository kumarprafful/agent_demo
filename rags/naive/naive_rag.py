from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama.embeddings import OllamaEmbeddings

'''
    we are building a simple rag to question a book

    rags can be divided up in two parts
    1. Ingestion pipeline
        collect -> normalize -> divide into chunks -> embed -> upsert into index(vector state) -> reindex(if data changes)
    2. Querying pipeline
        parse/rewrite -> retrieve candidate -> rereank -> assemble context -> 
'''


class RAG:
    def load_pdf_data(self, path) -> list[Document]:
        loader = PyPDFLoader(path)
        documents = loader.load()
        return documents
    
    def encode_data(self, documents, chunk_size=1000, chunk_overlap=200) -> list[Document]:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        texts = text_splitter.split_documents(documents)
        return texts
    
    def get_embedding_model(self, model='bge-large'):
        embedding = OllamaEmbeddings(model=model)
        return embedding


    def encode_pdf(self, paths) -> FAISS:
        documents = []
        for path in paths:
            documents += self.load_pdf_data(path=path)

        encoded_data = self.encode_data(documents=documents)
        # print("encoded_data", encoded_data)
        embedding = self.get_embedding_model()

        vectorstore = FAISS.from_documents(documents=encoded_data, embedding=embedding)

        return vectorstore
    
    def retriever(self, question):
        paths = ["/Users/praffulkumar/projects/agents/rags/naive/storage/The Creative Act By Rick Rubin.pdf"]

        chunks_vector_store = self.encode_pdf(paths=paths)

        chunks_query_retriever = chunks_vector_store.as_retriever(search_kwargs={"k": 2})

        docs = chunks_query_retriever.invoke(question)
        context = [doc.page_content for doc in docs]
        print(context)
        return

    
rag = RAG()
rag.retriever("what is most truthful and irrational aspects of ourselves?")

        