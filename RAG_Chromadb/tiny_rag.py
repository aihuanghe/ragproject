import json
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from RAG_Chromadb.chromadb_processor import ChromadbProcessor
from RAG_Chromadb.document_processor import DocumentAgent
from RAG_Chromadb.llm_chat import SiliconAI


class TinyRAG:
    """Tiny-RAG完整系统"""
    def __init__(self, name: str = "", model: str = "deepseek-ai/DeepSeek-V3", db_path: str ="./chromadb_data", ebedding_model: str = "BAAI/bge-m3"):
        self.chromadbProcessor = ChromadbProcessor(name=name, chromadb_path=db_path, embedding_model=ebedding_model)
        self.llmchat = SiliconAI(model=model)
        self.history = []
        self.conversation_history = []
        self.documentAgent = DocumentAgent()
        self.ebedding_model = ebedding_model

    def add_document(self, path: str, strategy: str = "adaptive") -> object:
        self.documentAgent.load_documents(path=path, strategy=strategy, enbedding_model=self.ebedding_model)
        self.chromadbProcessor.add_texts(self.documentAgent)
        self.documentAgent.release()

    def add_document_path(self, path: str,strategy="adaptive"):
        self.documentAgent.load_documents_path(path=path,  strategy=strategy)
        self.chromadbProcessor.add_texts(self.documentAgent)
        self.documentAgent.release()

    def query(self, query: str):
        queryresult = self.chromadbProcessor.query(query, n_results=5)
        contents = queryresult["documents"][0]
        context = "\n\n".join(contents)
        answer = self.llmchat.chat(query, self.history, context)

        metadatas = queryresult["metadatas"][0]
        file_names = list(set(metadata["file_name"] for metadata in metadatas))
        print(f"参考文件：{file_names}")
        return answer

    def query2(self, query: str, scrolledText: ScrolledText =  None):
        queryresult = self.chromadbProcessor.query(query, n_results=5)
        contents = queryresult["documents"][0]
        context = "\n\n".join(contents)
        response = self.llmchat.chat2(query, self.history, context)
        result = self.layout_response(response, scrolledText)
        self.history.append({'role': 'assistant', 'content': result})
        metadatas = queryresult["metadatas"][0]
        file_names = list(set(metadata["file_name"] for metadata in metadatas))
        print(f"参考文件：{file_names}\n-----------------------------------\n\n")
        if scrolledText:
            self.display_result(f"参考文件：{file_names}\n-----------------------------------\n\n", scrolledText)

    def query3(self, query: str):
        queryresult = self.chromadbProcessor.query(query, n_results=5)
        contents = queryresult["documents"][0]
        metadatas = queryresult["metadatas"][0]
        files = {}
        context = ""
        for i, content in enumerate(contents):
            file_name = metadatas[i]["file_name"]
            if file_name not in files:
                files[file_name] = []
            files[file_name].append(content)

        for file_name, contents in files.items():
            tmpcontext = "\n\n".join(contents)
            tmpcontext = f"\n\n 参考文件：{file_name}{tmpcontext}"
            context = context + tmpcontext

        response = self.llmchat.chat2(query, self.history, context)
        return response


    def display_result(self, text, scrolledText: ScrolledText):
         scrolledText.config(state=tk.NORMAL)
         scrolledText.insert(tk.END, text)
         scrolledText.see(tk.END)
         scrolledText.config(state=tk.DISABLED)
         scrolledText.update_idletasks()


    def layout_response(self, response, scrolledText: ScrolledText =  None):
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
                            #print(chunk_str)
                        if chunk_str == "[DONE]":  # 完成了
                            print("\n\n============[DONE]============\n")
                            if scrolledText:
                                self.display_result("\n\n============[DONE]============\n", scrolledText)
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
                            #if finish_reason is not None:
                                #print("\n\n\n==>查看结束原因，如果是stop，表示是正常结束的。finish_reason =",
                                #      finish_reason)

                            # 打印结果内容：content（如果有）
                            if content is not None:
                                if first_content_output:
                                    print("\n\n=============结果:=================\n")
                                    if scrolledText:
                                        self.display_result("\n\n=============结果:=================\n", scrolledText)
                                    first_content_output = False
                                print(content, end='', flush=True)
                                if scrolledText:
                                    self.display_result(content, scrolledText)
                                result += content

                            if reasoning_content is not None:
                                if first_reasoning_output:
                                    print("\n\n============推理:==================\n")
                                    if scrolledText:
                                        self.display_result("\n\n=============推理:=================\n", scrolledText)
                                    first_reasoning_output = False
                                print(reasoning_content, end='', flush=True)
                                if scrolledText:
                                    self.display_result(content, scrolledText)

                    except json.JSONDecodeError as e:
                        print(f"JSON解码错误: {e}", flush=True)
                        result = f"请求失败，JSON解码错误: {e}"
                        if scrolledText:
                            self.display_result(f"JSON解码错误: {e}", scrolledText)
        else:
            result = f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}"
            if scrolledText:
                self.display_result(result, scrolledText)
        return result

