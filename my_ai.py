import ollama

# 1. 模拟你的“私人文档”内容
my_documents = [
    "国家电网计算机岗位的笔试重点是数据结构、操作系统、计算机网络和数据库。",
    "2026年国网招聘的第一批考试通常在11月到12月之间举行。",
    "应聘国网建议考取英语六级证书和软考中级证书。"
]

# 2. 你的问题
user_question = "我想考国家电网，笔试要考什么？有哪些证书建议考？"

# 3. 简单的检索逻辑：寻找包含关键词的文档（实际RAG用向量，我们先做逻辑演示）
context = ""
for doc in my_documents:
    if "电网" in user_question:
        context += doc + "\n"

# 4. 构建给 AI 的指令（Prompt）
prompt = f"请根据以下已知信息回答问题：\n{context}\n问题：{user_question}"

# 5. 调用你本地的 Llama3 模型
response = ollama.generate(model='llama3', prompt=prompt)

print("--- AI 的回答 ---")
print(response['response'])
