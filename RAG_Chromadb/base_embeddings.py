#####2.文本向量化

import numpy as np
from typing import List

from chromadb import EmbeddingFunction
from langchain_core.embeddings import Embeddings


class SiliconEmbedding(EmbeddingFunction):
    """使用硅基流动的免费嵌入模型"""

    def __init__(self, key: str = "sk-rueedcryxhkrvvvltnmnzhmrewqosxnkckipuboydiibptmw",
                 url: str = "https://api.siliconflow.cn/v1/embeddings",
                 embedding_model: str = "BAAI/bge-m3"):
        self.url = url
        self.key = key
        self.embedding_model = embedding_model

    def get_embedding(self, text: str) -> List[float]:
        """使用硅基流动的免费嵌入模型"""
        import requests
        import json
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.key
        }
        data = {
            "input": text,
            "model": self.embedding_model
        }
        response = requests.post(self.url, headers=headers, data=json.dumps(data))
        return response.json()["data"][0]["embedding"]

    def __call__(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        i = 0
        for text in texts:
            embeddings.append(self.get_embedding(text))
            print(f"向量化进度: {i + 1}/{len(texts)}")
            i += 1

        return embeddings


class SiliconEmbeddingLCH(Embeddings):
    """使用硅基流动的免费嵌入模型"""
    def __init__(self, key: str = "sk-rueedcryxhkrvvvltnmnzhmrewqosxnkckipuboydiibptmw",
                 url: str = "https://api.siliconflow.cn/v1/embeddings",
                 embedding_model: str = "Qwen/Qwen3-Embedding-0.6B"):
        self.url = url
        self.key = key
        self.embedding_model = embedding_model

    def embed_query(self, text: str) -> list[float]:
        import requests
        import json
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.key
        }
        data = {
            "input": text,
            "model": self.embedding_model
        }
        response = requests.post(self.url, headers=headers, data=json.dumps(data))
        return response.json()["data"][0]["embedding"]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        i = 0
        for text in texts:
            embeddings.append(self.embed_query(text))
            print(f"向量化进度: {i + 1}/{len(texts)}")
            i += 1

        return embeddings
