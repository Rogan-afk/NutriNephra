from langchain.retrievers.multi_vector import MultiVectorRetriever

def build_multivector_retriever(vectorstore, docstore, id_key: str):
    return MultiVectorRetriever(vectorstore=vectorstore, docstore=docstore, id_key=id_key)
