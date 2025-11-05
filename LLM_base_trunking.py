import json
import re
from typing import List, Dict

from recursive_chunking import CustomRecursiveChunker
from silicon_ai import SiliconAIProcessor


class LLMBasedChunker:
    def __init__(self, model_name: str = "deepseek-ai/DeepSeek-V3",
                 target_chunk_size: int = 800
                 ):
        """
        初始化基于LLM的分块器

        Args:
            model_name: 使用的LLM模型名称
            target_chunk_size: 目标块大小
            api_key: OpenAI API密钥
        """
        self.model_name = model_name
        self.target_chunk_size = target_chunk_size

    def create_chunking_prompt(self, text: str) -> str:
        """创建分块指令"""
        prompt = f"""
请将以下文本分割成语义完整的块。每个块应该：
1. 包含完整的语义单元（完整的思想或概念）
2. 长度控制在{self.target_chunk_size}字符左右
3. 保持上下文的连贯性
4. 在自然的语义边界处分割

请以JSON格式返回分块结果，格式如下：
{{
    "chunks": [
        {{"id": 1, "content": "第一个块的内容", "summary": "块的概要"}},
        {{"id": 2, "content": "第二个块的内容", "summary": "块的概要"}}
    ]
}}

待分块的文本：
{text}
"""
        return prompt

    def call_llm_for_chunking(self, text: str) -> List[Dict]:
        """调用LLM进行分块"""
        try:
            prompt = self.create_chunking_prompt(text)


            #processor = AIProcessor(self.model_name)
            #response = processor.send_request(prompt,"你是一个专业的文本分块专家，擅长识别文本的语义边界。只输出JSON格式文本，不要输出其他任何内容")

            processor = SiliconAIProcessor(model=self.model_name)
            history = [{'role': 'user', 'content': prompt}]
            response = processor.create(history)

            # 尝试解析JSON响应
            try:
                result = json.loads(response)
                return result.get("chunks", [])
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试提取文本块
                return self.fallback_parsing(response)

        except Exception as e:
            print(f"LLM调用失败: {e}")
            return self.fallback_to_recursive_chunking(text)

    def fallback_parsing(self, text: str) -> List[Dict]:
        """当JSON解析失败时的后备解析方法"""
        chunks = []
        # 尝试从文本中提取块内容
        chunk_pattern = re.compile(r'"content":\s*"([^"]*)"', re.DOTALL)
        matches = chunk_pattern.findall(text)

        for i, match in enumerate(matches):
            chunks.append({
                "id": i + 1,
                "content": match.strip(),
                "summary": f"块{i + 1}的内容"
            })

        return chunks

    def fallback_to_recursive_chunking(self, text: str) -> List[str]:
        """当LLM不可用时回退到递归分块"""
        recursive_chunker = CustomRecursiveChunker(
            chunk_size=self.target_chunk_size,
            chunk_overlap=100
        )

        chunks = recursive_chunker.chunk_text(text)
        return chunks

    def chunk_text(self, text: str) -> List[str]:
        """
        使用LLM进行文本分块

        Args:
            text: 待分块的文本

        Returns:
            分块后的文本列表
        """
        # 如果文本过长，先进行预分割
        if len(text) > 8000:  # LLM上下文限制
            pre_chunks = self.pre_split_large_text(text)
            all_chunks = []

            for pre_chunk in pre_chunks:
                chunk_results = self.call_llm_for_chunking(pre_chunk)
                all_chunks.extend([chunk["content"] for chunk in chunk_results])

            return all_chunks
        else:
            chunk_results = self.call_llm_for_chunking(text)
            return [chunk["content"] for chunk in chunk_results]

    def pre_split_large_text(self, text: str) -> List[str]:
        """预分割过大的文本"""
        # 使用段落分割作为预处理
        paragraphs = text.split('\n\n')
        pre_chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) < 7000:  # 保留一些余量
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    pre_chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            pre_chunks.append(current_chunk.strip())

        return pre_chunks


# 模拟LLM分块的简化版本（不需要实际API调用）
class MockLLMChunker:
    def __init__(self, target_chunk_size: int = 800):
        self.target_chunk_size = target_chunk_size

    def chunk_text(self, text: str) -> List[str]:
        """
        模拟LLM分块的逻辑：
        1. 按段落分割
        2. 分析每个段落的主题
        3. 将相关段落合并成语义完整的块
        """
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            # 简单的主题相关性判断（实际应用中这里会调用LLM）
            if len(current_chunk) + len(para) <= self.target_chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


if __name__ == '__main__':
    # 测试LLM分块
    sample_text = """
    人工智能的发展历程可以追溯到20世纪50年代。当时，计算机科学家们开始探索让机器模拟人类智能的可能性。
    
    图灵测试是人工智能领域的一个重要里程碑。阿兰·图灵提出了这个测试来评估机器是否具有类似人类的智能。
    
    机器学习作为人工智能的一个分支，在20世纪80年代开始兴起。它让计算机能够从数据中学习，而不需要明确的编程指令。
    
    深度学习在21世纪初期开始受到关注。它使用多层神经网络来模拟人脑的工作方式，在图像识别和语音识别等任务上取得了突破性进展。
    
    自然语言处理是人工智能的另一个重要领域。它专注于让计算机理解和生成人类语言，包括文本分析、机器翻译和对话系统等应用。
    
    大模型简介
    
    大模型（Large Model / Foundation Model） 是指参数规模达到数十亿甚至上万亿的人工智能模型。它们通常通过大规模数据和强大的计算资源进行训练，能够在自然语言处理、计算机视觉、多模态理解等多个领域展现出强大的泛化能力。
    
    1. 起源与发展
        •	早期阶段：传统机器学习依赖人工设计特征，模型规模较小。
        •	深度学习崛起：随着神经网络的发展，模型规模逐渐增大，如 ResNet、LSTM 等。
        •	大模型时代：从 OpenAI 的 GPT 系列、Google 的 BERT 到最近的 GPT-4、GPT-5、Claude、Gemini、Llama 等，参数量从亿级增长到万亿级。
    
    2. 核心特征
        •	超大规模参数：模型拥有数十亿 ~ 万亿参数。
        •	预训练 + 微调：先在大规模无标注数据上进行预训练，再通过微调适配下游任务。
        •	通用性与泛化能力：在翻译、写作、问答、代码生成等多任务上表现优异。
        •	少样本/零样本学习：可以在几乎没有样本的情况下完成任务。
    
    3. 技术关键
        •	Transformer 架构：注意力机制带来长距离依赖建模能力。
        •	大规模分布式训练：数据并行、模型并行、流水线并行等技术。
        •	高质量语料：互联网文本、代码、图像等多模态数据。
        •	推理优化：量化、蒸馏、LoRA 等方法降低使用成本。
    
    4. 应用场景
        •	自然语言处理：对话系统、机器翻译、信息检索。
        •	代码生成：辅助编程、自动调试。
        •	多模态应用：图文理解、视频生成。
        •	企业级应用：智能客服、知识管理、自动文档处理。
    
    5. 挑战与问题
        •	高昂的训练成本：算力与能耗需求极大。
        •	幻觉问题（Hallucination）：有时生成虚假内容。
        •	数据与隐私风险：训练数据可能存在偏见或隐私泄露。
        •	可解释性不足：模型的内部推理过程难以理解。
    """

    llm_chunker = LLMBasedChunker(target_chunk_size=400)
    llm_chunks = llm_chunker.chunk_text(sample_text)
    #llm_chunks = llm_chunker.fallback_to_recursive_chunking(sample_text)

    print("基于LLM的分块结果：")
    for i, chunk in enumerate(llm_chunks):
        print(f"块 {i + 1}: {chunk}\n")
