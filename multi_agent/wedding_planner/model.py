from langchain_ollama.chat_models import ChatOllama

ollama = ChatOllama(
    model="qwen3.5:4b",
    temperature=0.5
)