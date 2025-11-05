import os
import sqlite3
from typing import List, Dict, Tuple, Any, Sequence, Mapping

import chromadb
from chromadb import QueryResult
from numpy import ndarray, dtype, signedinteger, floating, unsignedinteger, float64

from RAG_Chromadb.base_embeddings import SiliconEmbedding
from RAG_Chromadb.document_processor import DocumentAgent


class ChromadbProcessor:
    """Chromadb处理器"""
    def __init__(self, name: str = "", chromadb_path: str = "./chromadb_data", embedding_model: str = "BAAI/bge-m3"):
        self.name = name
        self.chromadb_path = chromadb_path
        self.client = chromadb.PersistentClient(path=self.chromadb_path)
        self.embedding_model = SiliconEmbedding(key="sk-rueedcryxhkrvvvltnmnzhmrewqosxnkckipuboydiibptmw", embedding_model=embedding_model)
        if self.name == "":
            collections = self.get_cellection_names()
            self.name = collections[0] if collections else None
        self.collection = self.client.get_or_create_collection(name=self.name, embedding_function=self.embedding_model)

    def change_name(self, name: str):
        """修改名称"""
        self.name = name
        self.collection = self.client.get_or_create_collection(name=self.name, embedding_function=self.embedding_model)

    def get_cellection_names(self) -> List[str]:
        """获取集合名称"""
        collections = self.client.list_collections()
        if not collections:
            return self.get_collections_from_sqlite()
        return [collection.name for collection in collections]

    def get_collections_from_sqlite(self) -> List[str]:
        """
        直接从 ChromaDB 的 SQLite 数据库读取所有 collections
        """
        # ChromaDB 的 SQLite 数据库通常在这个路径
        collection_names = []
        db_path = os.path.join(self.chromadb_path, "chroma.sqlite3")

        if not os.path.exists(db_path):
            raise FileNotFoundError(f"ChromaDB 数据库文件不存在: {db_path}")

        collections = []

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 查询 collections 表
            cursor.execute("SELECT * FROM collections")
            rows = cursor.fetchall()

            # 获取列名
            column_names = [description[0] for description in cursor.description]

            print(f"找到 {len(rows)} 个 collections 在数据库中")
            for row in rows:
                collection_data = dict(zip(column_names, row))
                collection_names.append(collection_data['name'])
                print(f"Collection: {collection_data}")

            conn.close()

        except sqlite3.Error as e:
            print(f"SQLite 错误: {e}")
        except Exception as e:
            print(f"读取数据库时出错: {e}")

        return collection_names

    def add_texts(self, documentation: DocumentAgent):
        """添加文本"""
        # 插入数据之前需要剔除重复数据
        self.collection.upsert(documents=documentation.chunks, metadatas=documentation.metadatas, ids=documentation.ids)

    def query(self, query_text: str, n_results: int = 5, where: dict = None) -> QueryResult:
        """查询"""
        results = self.collection.query(query_texts=[query_text], n_results=n_results, where=where)
        return results

