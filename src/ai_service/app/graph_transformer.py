import os

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_neo4j import Neo4jGraph
from LLMGraphTransformer import LLMGraphTransformer
from langchain_core.documents import Document

load_dotenv('.env.dev')

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE')
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

LLM_PROVIDER = os.getenv("LLM_PROVIDER")


def get_llm():
    if LLM_PROVIDER == "azure":
        return AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0,
        )
    else:
        raise ValueError("LLM_PROVIDER must be 'azure' for now")


graph = Neo4jGraph(
    url=NEO4J_URI,
    database=NEO4J_DATABASE
)


def ingest_cv_text_into_graph(text: str, source_id: str) -> None:
    """
    Use LLMGraphTransformer to convert CV text into a graph
    and write it to Neo4j.
    """
    llm = get_llm()
    transformer = LLMGraphTransformer(llm=llm)

    # 1) Wrap text in a Document
    doc = Document(
        page_content=text,
        metadata={"source_id": source_id},
    )

    # 2) Convert Document -> GraphDocument(s)
    graph_documents = transformer.convert_to_graph_documents([doc])

    # 3) (Optional) ensure all nodes carry source_id
    for gd in graph_documents:
        for node in gd.nodes:
            node.properties.setdefault("source_id", source_id)

    # 4) Persist into Neo4j
    graph.add_graph_documents(
        graph_documents,
        include_source=True,
        baseEntityLabel=True,
    )
