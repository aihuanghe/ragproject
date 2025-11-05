from RAG_Chromadb.tiny_rag import TinyRAG

if __name__ == "__main__":
    rag = TinyRAG("test")

    while True:
        query = input("请输入查询内容：")
        if query == "exit":
            break
        answer = rag.query2(query)
        #print(answer)