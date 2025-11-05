import json

from RAG_Chromadb.tiny_rag import TinyRAG


# 可选：其他 AI 服务支持
class CustomAIService:
    """自定义 AI 服务（示例）"""

    def __init__(self):
        client = TinyRAG(model="deepseek-ai/DeepSeek-V3", db_path="../chromadb_data")
        self.collections = client.chromadbProcessor.get_cellection_names()

    def get_collection(self):
        return self.collections

    @classmethod
    def chat_stream(cls, message, history, collection_name):
        # 实现自定义流式响应
        client = TinyRAG(name=collection_name, model="deepseek-ai/DeepSeek-V3", db_path="../chromadb_data",
                         ebedding_model="BAAI/bge-m3")
        client.history = history
        print(f"client message:{message}")
        print(f"client history:{history}")

        response = client.query3(message)
        result = ""
        if response.status_code == 200:
            first_content_output = True
            first_reasoning_output = True

            for chunk in response.iter_lines():
                if chunk:  # 过滤掉keep-alive新行
                    chunk_str = chunk.decode('utf-8').strip()

                    try:
                        if chunk_str.startswith('data:'):
                            chunk_str = chunk_str[6:].strip()  # 去除"data:"前缀和之后的首位空格
                            # print(chunk_str)
                        if chunk_str == "[DONE]":  # 完成了
                            continue

                        # 解析JSON
                        chunk_json = json.loads(chunk_str)
                        if 'choices' in chunk_json:
                            choice = chunk_json['choices'][0]
                            delta = choice.get('delta', {})
                            # 获取思考过程信息
                            reasoning_content = delta.get('reasoning_content')
                            # 获取结果信息
                            content = delta.get('content')
                            # 获取完成原因
                            finish_reason = choice.get('finish_reason', None)
                            # if finish_reason is not None:
                            # print("\n\n\n==>查看结束原因，如果是stop，表示是正常结束的。finish_reason =",
                            #      finish_reason)

                            # 打印结果内容：content（如果有）
                            if content is not None:
                                if first_content_output:
                                    #print("\n\n=============结果:=================\n")
                                    #yield "\n\n=============结果:=================\n"
                                    first_content_output = False
                                #print(content, end='', flush=True)
                                yield content
                                result += content

                            if reasoning_content is not None:
                                if first_reasoning_output:
                                    #print("\n\n============推理:==================\n")
                                    #yield "\n\n=============推理:=================\n"
                                    first_reasoning_output = False
                                #print(reasoning_content, end='', flush=True)
                                yield reasoning_content

                    except json.JSONDecodeError as e:
                        #print(f"JSON解码错误: {e}", flush=True)
                        result = f"请求失败，JSON解码错误: {e}"
        else:
            result = f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}"
        return result
