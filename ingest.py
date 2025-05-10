import os
from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from embeddings import OllamaEmbeddings

DATA_DIR = "./data"
CHROMA_DIR = "./chroma_db"

def load_and_split(file_path):
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        loader = UnstructuredExcelLoader(file_path, mode="elements")
    else:
        raise ValueError(f"Unsupported file type: {file_path}")

    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
    return text_splitter.split_documents(documents)

def process_all_files():
    embeddings = OllamaEmbeddings()

    vectorstore = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings
    )

    for filename in os.listdir(DATA_DIR):
        file_path = os.path.join(DATA_DIR, filename)
        if not os.path.isfile(file_path):
            continue

        print(f"Processing file: {filename}")
        chunks = load_and_split(file_path)
        vectorstore.add_documents(chunks)
        vectorstore.persist()
        print(f"Finished processing: {filename}")

if __name__ == "__main__":
    process_all_files()