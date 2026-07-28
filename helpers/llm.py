from langchain_ollama  import ChatOllama


def get_llm(**kwargs):
    llm = ChatOllama(
        **kwargs
    )
    return llm