import tkinter as tk
from tkinter import filedialog

from RAG_Chromadb.chromadb_processor import ChromadbProcessor
from RAG_Chromadb.document_processor import DocumentAgent
from RAG_Chromadb.tiny_rag import TinyRAG


def test1():
    documentAgent = DocumentAgent('./docment1.txt')
    documentAgent.load_documents(strategy="LLM")
    documentAgent.print_documents()


    chromadbProcessor = ChromadbProcessor("test")
    chromadbProcessor.add_texts(documentAgent)


def test2():
    # 选取文件
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    root.update()
    file_path = filedialog.askopenfilename(title="选择文件", filetypes=[("*", "*.*")])
    tinyRAG = TinyRAG("bidding-law")
    tinyRAG.add_document(path=file_path, strategy="OTHER")


if __name__ == "__main__":
    test2()