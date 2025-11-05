######1.文档加载与智能切分
import hashlib

import tiktoken
from typing import List
import os

from HybridChunker import OptimizedChunker

enc = tiktoken.get_encoding("cl100k_base")


class DocumentProcessor:
    """文档处理类"""
    idx = 0

    @classmethod
    def read_file_content(cls, file_path: str) -> str:
        """根据文件类型读取内容"""
        if file_path.endswith('.pdf'):
            return cls.read_pdf(file_path)
        elif file_path.endswith('.md'):
            return cls.read_markdown(file_path)
        elif file_path.endswith('.txt'):
            return cls.read_text(file_path)
        elif file_path.endswith('.docx'):
            return cls.read_word(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_path}")

    @classmethod
    def read_text(cls, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @classmethod
    def read_pdf(cls, file_path: str) -> str:
        import PyPDF2
        reader = PyPDF2.PdfReader(file_path)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
            text += '\n\n'
        return text

    @classmethod
    def read_markdown(cls, file_path: str) -> str:
        import markdown
        with open(file_path, 'r', encoding='utf-8') as f:
            html = markdown.markdown(f.read())
        return html

    @classmethod
    def read_word(cls, path: str) -> str:
        import docx
        doc = docx.Document(path)
        return '\n\n'.join([paragraph.text for paragraph in doc.paragraphs])


    @classmethod
    def get_chunks(cls, text: str, max_token_len: int = 600,
                   cover_content: int = 150) -> List[str]:
        """智能文档切分"""
        chunk_text = []
        curr_len = 0
        curr_chunk = ''
        token_len = max_token_len - cover_content
        lines = text.splitlines()

        for line in lines:
            line = line.strip()
            line_len = len(enc.encode(line))

            if line_len > max_token_len:
                if curr_chunk:
                    chunk_text.append(curr_chunk)
                    curr_chunk = ''
                    curr_len = 0

                line_tokens = enc.encode(line)
                num_chunks = (len(line_tokens) + token_len - 1) // token_len

                for i in range(num_chunks):
                    start_token = i * token_len
                    end_token = min(start_token + token_len, len(line_tokens))
                    chunk_tokens = line_tokens[start_token:end_token]
                    chunk_part = enc.decode(chunk_tokens)

                    if i > 0 and chunk_text:
                        prev_chunk = chunk_text[-1]
                        cover_part = prev_chunk[-cover_content:]
                        chunk_part = cover_part + chunk_part

                    chunk_text.append(chunk_part)

                curr_chunk = ''
                curr_len = 0

            elif curr_len + line_len + 1 <= token_len:
                if curr_chunk:
                    curr_chunk += '\n'
                    curr_len += 1
                curr_chunk += line
                curr_len += line_len

            else:
                if curr_chunk:
                    chunk_text.append(curr_chunk)

                if chunk_text:
                    prev_chunk = chunk_text[-1]
                    cover_part = prev_chunk[-cover_content:]
                    curr_chunk = cover_part + '\n' + line
                    curr_len = len(enc.encode(cover_part)) + 1 + line_len
                else:
                    curr_chunk = line
                    curr_len = line_len

        if curr_chunk:
            chunk_text.append(curr_chunk)

        return chunk_text

    @classmethod
    def get_trunks_Optimized(cls, documents: List[str]) -> list[list[str]]:
        """优化分块"""
        chunker = OptimizedChunker()
        chunks = chunker.batch_chunk_documents(documents)
        return chunks

    @classmethod
    def get_trunks_Hybrid(cls, documents: str, strategy: str = "adaptive", enbedding_model="BAAI/bge-m3") -> list[str]:
        """混合分块"""
        chunker = OptimizedChunker(enbedding_model=enbedding_model)
        chunks = chunker.chunk_documents(documents,strategy)
        return chunks

    @classmethod
    def read_file_paths(cls, path: str):
        """读取文件路径"""
        file_paths = []
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                file_paths.append(file_path)

        return file_paths

    @classmethod
    def get_ids(cls, trunks: List[str], metadatas: List[dict]):
        """获取id"""
        ids = []
        for i in range(len(trunks)):
            text = f"{trunks[i]}_{metadatas[i].get('file_name')}_{metadatas[i].get('chunk_size')}"
            id = hashlib.md5(text.encode('utf-8')).hexdigest()
            if id not in ids:
                ids.append(id)
        return ids

    @classmethod
    def get_metadatas(cls, filename: str, trunks: List[str]):
        """获取元数据"""
        file = os.path.basename(filename)

        metadatas = []
        for trunk in trunks:
            metadata = {
                "file_name": file,
                "chunk_size": len(trunk)
            }
            metadatas.append(metadata)
        return metadatas


class DocumentAgent:
    """文档处理代理类"""
    def __init__(self, path: str = ""):
        self.path = path
        self.chunks = []
        self.ids = []
        self.metadatas = []

    def load_documents(self, path: str, strategy: str = "adaptive", enbedding_model="BAAI/bge-m3"):
        self.path = path or self.path
        content = DocumentProcessor.read_file_content(self.path)
        self.chunks = DocumentProcessor.get_trunks_Hybrid(content, strategy, enbedding_model)
        self.metadatas = DocumentProcessor.get_metadatas(self.path, self.chunks)
        self.ids = DocumentProcessor.get_ids(self.chunks, self.metadatas)

    def load_documents_path(self, path: str, strategy: str = "adaptive", enbedding_model="BAAI/bge-m3"):
        file_paths = DocumentProcessor.read_file_paths(path)
        for file_path in file_paths:
            content = DocumentProcessor.read_file_content(file_path)
            chipmunks = DocumentProcessor.get_trunks_Hybrid(content, strategy, enbedding_model)
            chipolatas = DocumentProcessor.get_metadatas(file_path, chipmunks)
            self.ids.append(DocumentProcessor.get_ids(chipmunks, chipolatas))
            self.metadatas.append(chipolatas)
            self.chunks.append(chipmunks)

    def print_documents(self):
        for i, chunk in enumerate(self.chunks):
            print(f"======================分块{i + 1}======================")
            print(chunk)
            print("-" * 50)

    def release(self):
        self.path = None
        self.chunks = None
        self.metadatas = None
        self.ids = None
