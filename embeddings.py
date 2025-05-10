from langchain_core.embeddings import Embeddings
import requests

class OllamaEmbeddings(Embeddings):
    def __init__(self, model_name="bge-m3:latest", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def embed_documents(self, texts):
        embeddings = []
        for text in texts:
            response = requests.post(f"{self.base_url}/api/embeddings", json={
                "model": self.model_name,
                "prompt": text
            })
            if response.status_code != 200:
                raise Exception(f"Error embedding text: {response.text}")
            embeddings.append(response.json()['embedding'])
        return embeddings

    def embed_query(self, text):
        return self.embed_documents([text])[0]