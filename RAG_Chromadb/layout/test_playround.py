import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import sqlite3
import os

from RAG_Chromadb.tiny_rag import TinyRAG


class DatabaseViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("知识库查询界面")
        self.root.geometry("800x600")

        # 创建数据库连接
        self.tiny_rag = TinyRAG(db_path="../chromadb_data", ebedding_model="BAAI/bge-m3")
        self.collections = self.tiny_rag.chromadbProcessor.get_cellection_names()

        # 创建界面
        self.create_widgets()

        # 加载数据库列表
        self.load_databases()


    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # 左侧数据库列表
        left_frame = ttk.LabelFrame(main_frame, text="数据库", padding="5")
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # 数据库列表
        self.db_listbox = tk.Listbox(left_frame, width=20)
        self.db_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.db_listbox.bind('<<ListboxSelect>>', self.on_database_select)

        # 数据库列表滚动条
        db_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.db_listbox.yview)
        db_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.db_listbox.configure(yscrollcommand=db_scrollbar.set)

        # 右侧框架
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        # 右上结果显示窗口
        result_frame = ttk.LabelFrame(right_frame, text="查询结果", padding="5")
        result_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

        self.result_text = scrolledtext.ScrolledText(result_frame, width=60, height=20, state=tk.DISABLED)
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 右下输入窗口
        input_frame = ttk.LabelFrame(right_frame, text="输入查询问题", padding="5")
        input_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(0, weight=1)

        self.input_text = scrolledtext.ScrolledText(input_frame, width=60, height=5)
        self.input_text.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 发送按钮
        send_button = ttk.Button(input_frame, text="执行查询", command=self.execute_query)
        send_button.grid(row=1, column=1, sticky=tk.E, pady=(5, 0))

        # 清除按钮
        clear_button = ttk.Button(input_frame, text="清除", command=self.clear_input)
        clear_button.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        # 配置权重
        left_frame.rowconfigure(0, weight=1)
        left_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=3)
        right_frame.rowconfigure(1, weight=1)

    def load_databases(self):
        """加载数据库列表"""
        # 这里我们只使用一个示例数据库
        for db in self.collections:
            index = self.db_listbox.size()
            self.db_listbox.insert(tk.END, db)
            if index == 0:  # 只选中第一个
                self.db_listbox.selection_set(index)


    def on_database_select(self, event):
        """当选择数据库时显示表信息"""
        selection = self.db_listbox.curselection()
        if selection:
            db_name = self.db_listbox.get(selection[0])
            self.tiny_rag.chromadbProcessor.change_name(db_name)
            self.tiny_rag.history = []

    def execute_query(self):
        """执行SQL查询"""
        query = self.input_text.get("1.0", tk.END).strip()
        if not query:
            #messagebox.showwarning("警告", "请输入查询内容")
            return
        self.input_text.delete("1.0", tk.END)
        self.display_result(query)

        def callback(text):
            self.tiny_rag.query2(text, self.result_text)

        thread = threading.Thread(target=callback, args=(query,))
        thread.daemon = True
        thread.start()


    def display_result(self, text):
        """在结果窗口中显示文本"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)
        self.result_text.config(state=tk.DISABLED)
        self.result_text.update_idletasks()

    def clear_input(self):
        """清除输入窗口"""
        self.input_text.delete("1.0", tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseViewer(root)
    root.mainloop()