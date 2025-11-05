####4.大模型集成
from typing import List, Dict

from silicon_ai import SiliconAIProcessor

RAG_PROMPT_TEMPLATE = """
使用以下上下文来回答用户的问题。如果你不知道答案，就说你不知道。总是使用中文回答。

问题: {question}

可参考的上下文：
======================================================================
{context}
======================================================================

如果给定的上下文无法让你做出回答，请回答数据库中没有这个内容，你不知道。

有用的回答:
"""
RAG_PROMPT_TEMPLATE2 = """
使用以下上下文来回答用户的问题,答案中每个条目标明参考出处及所有参考的文件名。如果你不知道答案，就说你不知道。总是使用中文回答。

问题: {question}

可参考的上下文：
======================================================================
{context}
======================================================================

如果给定的上下文无法让你做出回答，请回答数据库中没有这个内容，你不知道。

有用的回答:
"""


class BaseModel:
    """大模型基类"""

    def __init__(self, path: str = ''):
        self.path = path

    def chat(self, prompt: str, history: List[Dict], content: str) -> str:
        raise NotImplementedError


class SiliconAI(BaseModel):
    """Silicon AI模型"""

    def __init__(self, api_key: str = "", model: str = "deepseek-ai/DeepSeek-V3"):
        super().__init__()
        self.api_key = api_key
        if self.api_key == "":
            self.processor = SiliconAIProcessor(model=model)
        else:
            self.processor = SiliconAIProcessor(api_key=self.api_key,model=model)

    def chat(self, prompt: str, history: List[Dict], content: str) -> str:

        rag_prompt = RAG_PROMPT_TEMPLATE.format(question=prompt, context=content)
        history.append({'role': 'user', 'content': rag_prompt})
        result = self.processor.create(history)
        history.append({'role': 'assistant', 'content': result})
        return result

    def chat2(self, prompt: str, history: List[Dict], content: str):
        rag_prompt = RAG_PROMPT_TEMPLATE2.format(question=prompt, context=content)
        print(rag_prompt)
        tmp_history = history.copy()
        history.append({'role': 'user', 'content': prompt})
        tmp_history.append({'role': 'user', 'content': rag_prompt})
        response = self.processor.create2(tmp_history)
        return response

if __name__ == "__main__":
    siliconAI = SiliconAI()
    history = []
    content = "模拟人脑的工作方式，在图像识别和语音识别等任务上取得了突破性进展。\n\n自然语言处理是人工智能的另一个重要领域。它专注于让计算机理解和生成人类语言，包括文本分析、机器翻译和对话系统等应用。\n\n大模型简介大模型（Large Model / Foundation Model） 是指参数规模达到数十亿甚至上万亿的人工智能模型。它们通常通过大规模数据和强大的计算资源进行训练，能够在自然语言处理、计算机视觉、多模态理解等多个领域展现出强大的泛化能力。\n\n1. 起源与发展\n\t•\t早期阶段：传统机器学习依赖人工设计特征，模型规模较小。\n\t•\t深度学习崛起：随着神经网络的发展，模型规模逐渐增大，如 ResNet、LSTM 等。\n\t•\t大模型时代：从 OpenAI 的 GPT 系列、Google 的 BERT 到最近的 GPT-4、GPT-5、Claude、Gemini、Llama 等，参数量从亿级增长到万亿级。"
    while True:
        prompt = input("请输入问题：")
        result = siliconAI.chat(prompt, history, content)
        print(result)
