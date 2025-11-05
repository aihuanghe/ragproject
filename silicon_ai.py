import json
import requests


class SiliconAIProcessor:
    """使用硅基流动的大语言模型"""

    def __init__(self, model="deepseek-ai/deepseek-vl2",
                 api_key="sk-rueedcryxhkrvvvltnmnzhmrewqosxnkckipuboydiibptmw"):  # 移除content和image_path参数
        self.url = "https://api.siliconflow.cn/v1/chat/completions"
        self.model = model
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def create(self,  messages):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "max_tokens": 2048,
            "stop": ["null"],
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.0,
            "n": 1,
            "response_format": {"type": "text"},
        }
        response = requests.post(self.url, json=payload, headers=self.headers, stream=True)
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
                                    first_content_output = False
                                print(content, end='', flush=True)
                                result += content

                            if reasoning_content is not None:
                                if first_reasoning_output:
                                    print("\n\n============推理:==================\n")
                                    first_reasoning_output = False
                                print(reasoning_content, end='', flush=True)

                    except json.JSONDecodeError as e:
                        print(f"JSON解码错误: {e}", flush=True)
                        result = f"请求失败，JSON解码错误: {e}"
        else:
            result = f"请求失败，状态码: {response.status_code}, 错误信息: {response.text}"

        return result

    def create2(self, messages):
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "max_tokens": 2048,
            "stop": ["null"],
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.0,
            "n": 1,
            "response_format": {"type": "text"},
        }
        response = requests.post(self.url, json=payload, headers=self.headers, stream=True)
        return response
