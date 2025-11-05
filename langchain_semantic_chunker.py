from typing import List

from langchain_experimental.text_splitter import SemanticChunker

from RAG_Chromadb.base_embeddings import SiliconEmbeddingLCH


class SemanticChunkerLCH:
    """基于语义的文本分块"""
    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 800, enbedding_model: str = "BAAI/bge-m3"):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.embedding_model = enbedding_model

    def chunk_text(self, text: str) -> List[str]:
        """基于语义进行文本分块"""
        text_splitter = SemanticChunker(
            embeddings=SiliconEmbeddingLCH(embedding_model=self.embedding_model),  # 嵌入模型
            breakpoint_threshold_type="percentile",  # 拆分阈值策略
            breakpoint_threshold_amount=95.0,  # 阈值具体数值
            min_chunk_size=50,  # 最小块大小
            sentence_split_regex=r"[。！？.!?]+"  # 句子分隔符（支持多语言）
        )

        rt = text_splitter.split_text(text)
        return rt


if __name__ == '__main__':
    text = """
        机器学习是人工智能的核心技术之一。它通过算法让计算机从数据中学习模式。
        监督学习需要标注数据来训练模型。无监督学习则从未标注的数据中发现隐藏模式。
        深度学习使用多层神经网络来处理复杂数据。卷积神经网络特别适合图像处理任务。
        自然语言处理专注于让计算机理解人类语言。这包括文本分类、情感分析等任务。
        推荐系统利用用户行为数据来预测用户偏好。协同过滤是常用的推荐算法之一。
        """
    sc = SemanticChunkerLCH()
    rt = sc.chunk_text(text)
    print(rt)