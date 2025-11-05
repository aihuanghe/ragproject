import re
from typing import List, Dict


import numpy as np


from LLM_base_trunking import LLMBasedChunker
from recursive_chunking import CustomRecursiveChunker
from structural_chunker import StructuralChunker
from langchain_semantic_chunker import SemanticChunkerLCH


class HybridChunker:
    def __init__(self, model="deepseek-ai/DeepSeek-V3", enbedding_model="BAAI/bge-m3"):
        """混合分块策略"""
        self.structural_chunker = StructuralChunker()
        self.recursive_chunker = CustomRecursiveChunker()
        self.llm_chunker = LLMBasedChunker(model)
        self.semantic_chunker = SemanticChunkerLCH(enbedding_model=enbedding_model)
        self.enbedding_model = enbedding_model

    def adaptive_chunk(self, text: str, doc_type: str = "auto") -> List[str]:
        """
        自适应分块策略

        Args:
            text: 待分块的文本
            doc_type: 文档类型（"structured", "narrative", "mixed", "auto"）

        Returns:
            包含块信息的字典列表
        """
        # 自动检测文档类型
        if doc_type == "auto":
            doc_type = self.detect_document_type(text)

        chunks_info = []

        if doc_type == "structured":
            # 结构化文档：优先使用结构化分块
            try:
                chunks = self.structural_chunker.chunk_text(text, "markdown")
                strategy_used = "structural"
            except:
                chunks = self.recursive_chunker.chunk_text(text)
                strategy_used = "recursive_fallback"

        elif doc_type == "narrative":
            # 叙述性文档：使用语义分块
            chunks = self.semantic_chunker.chunk_text(text)
            strategy_used = "semantic"

        elif doc_type == "mixed":
            # 混合类型：使用递归分块
            chunks = self.recursive_chunker.chunk_text(text)
            strategy_used = "recursive"

        else:
            # 默认使用递归分块
            chunks = self.recursive_chunker.chunk_text(text)
            strategy_used = "recursive_default"

        print(f"Using strategy: {strategy_used}")
        return chunks

    @classmethod
    def chinese_sent_tokenize(cls, text):
        """中文句子分割"""
        # 使用中文标点符号进行分割
        sentences = re.split(r'[。！？；;.!?;]', text)
        # 清理空字符串和空白
        sentences = [sent.strip() for sent in sentences if sent.strip()]
        return sentences

    def detect_document_type(self, text: str) -> str:
        """自动检测文档类型"""
        # 检查是否有明显的结构化标记
        has_markdown_headers = bool(re.search(r'^#{1,6}\s', text, re.MULTILINE))
        has_html_headers = bool(re.search(r'<h[1-6]>', text, re.IGNORECASE))

        if has_markdown_headers or has_html_headers:
            return "structured"

        # 检查是否是叙述性文本
        sentences = self.chinese_sent_tokenize(text)

        avg_sentence_length = np.mean([len(sent) for sent in sentences])

        # 长句子通常表示叙述性文本
        if avg_sentence_length > 80:
            return "narrative"

        return "mixed"




# 性能优化的分块器
class OptimizedChunker:
    def __init__(self, model="deepseek-ai/DeepSeek-V3", enbedding_model="BAAI/bge-m3"):
        """性能优化的分块器"""
        self.cache = {}  # 分块结果缓存
        self.batch_size = 10  # 批处理大小
        self.model = model
        self.enbedding_model = enbedding_model

    def batch_chunk_documents(self, documents: List[str],
                              strategy: str = "adaptive") -> List[List[str]]:
        """
        批量处理多个文档的分块

        Args:
            documents: 文档列表
            strategy: 分块策略

        Returns:
            每个文档的分块结果列表
        """
        results = []
        hybrid_chunker = HybridChunker()

        # 批量处理以提高效率
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]

            batch_results = []
            for doc in batch:
                # 检查缓存
                doc_hash = hash(doc)
                if doc_hash in self.cache:
                    batch_results.append(self.cache[doc_hash])
                    continue

                # 执行分块
                if strategy == "adaptive":
                    chunks = hybrid_chunker.adaptive_chunk(doc)
                else:
                    # 其他策略的实现...
                    chunks = hybrid_chunker.adaptive_chunk(doc,doc_type="narrative")

                # 缓存结果
                self.cache[doc_hash] = chunks
                batch_results.append(chunks)

            results.extend(batch_results)

        return results

    def chunk_documents(self, document: str,
                              strategy: str = "adaptive") -> List[str]:
        """
        批量处理多个文档的分块

        Args:
            document: 文档列表
            strategy: 分块策略

        Returns:
            每个文档的分块结果列表
        """

        hybrid_chunker = HybridChunker(model=self.model, enbedding_model=self.enbedding_model)

        if strategy == "adaptive":
            chunks = hybrid_chunker.adaptive_chunk(document)
        else:
            # 其他策略的实现...
            chunks = hybrid_chunker.adaptive_chunk(document, doc_type="narrative")

        return chunks






# 实际应用示例
def practical_rag_chunking_pipeline():
    """实际RAG系统中的分块流水线"""

    # 模拟不同类型的文档
    documents = {
"技术文档": """
# Python深度学习框架对比

## PyTorch
PyTorch是Facebook开发的深度学习框架，以动态计算图著称。

### 主要特点
- 动态计算图，便于调试
- 强大的GPU加速支持
- 灵活的模型定义方式

## TensorFlow
TensorFlow是Google开发的深度学习框架。

### 主要特点
- 静态计算图，性能优化好
- 完整的生产部署生态
- 丰富的预训练模型
""",

"新闻文章": """
人工智能技术在医疗领域的应用正在快速发展。最新研究表明，
AI诊断系统在某些疾病的识别准确率已经超过了人类专家。

机器学习算法能够分析大量的医疗数据，包括影像、基因信息和病历记录。
这种能力使得AI系统能够发现人类医生可能忽略的细微模式。

然而，AI在医疗领域的应用也面临着挑战。数据隐私、算法透明度
和监管合规等问题需要得到妥善解决。医疗AI的未来发展需要
技术进步与伦理考量并重。
""",

"学术论文": """
本研究提出了一种新的注意力机制优化方法。传统的自注意力机制
在处理长序列时存在计算复杂度过高的问题。

我们的方法通过引入稀疏注意力模式，将时间复杂度从O(n²)降低到O(n log n)。
实验结果表明，在保持模型性能的同时，训练速度提升了40%。

相关工作主要集中在注意力机制的改进上。Sparse Transformer和Linformer
等方法都尝试解决注意力机制的效率问题，但在长序列处理上仍有局限性。
"""
    }

    hybrid_chunker = HybridChunker()

    # 处理每种类型的文档
    for doc_name, doc_content in documents.items():
        print(f"\n处理文档：{doc_name}")
        print("=" * 50)

        # 执行自适应分块
        chunks = hybrid_chunker.adaptive_chunk(doc_content, doc_type="narrative")

        for i, chunk in enumerate(chunks):
            print(f"块 {i + 1}: {chunk}\n{'=' * 50}\n")


# 执行实际应用示例
if __name__ == "__main__":
    practical_rag_chunking_pipeline()
