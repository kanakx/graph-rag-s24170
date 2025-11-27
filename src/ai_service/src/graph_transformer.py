import os

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_neo4j import Neo4jGraph
from LLMGraphTransformer import LLMGraphTransformer
from langchain_core.prompts import ChatPromptTemplate
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
            temperature=1,
        )
    else:
        raise ValueError("LLM_PROVIDER must be 'azure' for now")


graph = Neo4jGraph(
    url=NEO4J_URI,
    database=NEO4J_DATABASE
)

SCHEMA_PROMPT = """
You extract a KNOWLEDGE GRAPH from CV / resume text.

Use ONLY these node types and properties:

(Person {id, name, location, email, phone, years_experience})
(Skill {id, category, subcategory})
(Company {id, name, industry, size, location})
(Project {id, title, description, start_date, end_date, budget})
(Certification {id, name, provider, date_earned, expiry_date})
(University {id, name, location, ranking})
(RFP {id, title, description, requirements, budget, deadline})

Relationships:

(Person)-[HAS_SKILL {proficiency, years_experience}]->(Skill)
(Person)-[WORKED_AT {role, start_date, end_date}]->(Company)
(Person)-[WORKED_ON {role, contribution, start_date, end_date}]->(Project)
(Person)-[EARNED {date, score}]->(Certification)
(Person)-[STUDIED_AT {degree, graduation_year, gpa}]->(University)
(Person)-[ASSIGNED_TO {allocation_percentage, start_date, end_date}]->(Project)
(Project)-[REQUIRES {minimum_level, preferred_level}]->(Skill)
(RFP)-[NEEDS {required_count, experience_level}]->(Skill)

Rules:
- Use only these labels, relationships and properties.
- Do NOT hallucinate data. If you don't see a value, omit that property.
- Create a Person node for the CV owner and connect all extracted info to that Person.
- Add property `source_id` to every node and relationship, taken from the document metadata.
"""
SYSTEM_PROMPT = SCHEMA_PROMPT.replace("{", "{{").replace("}", "}}")


def ingest_cv_text_into_graph(text: str, source_id: str) -> None:
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),  # <- escaped version
            ("human", "{input_text}"),  # <- this stays single-braced, it's a real variable
        ]
    )

    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=[],
        allowed_relationships=[],
        additional_instructions=SCHEMA_PROMPT,
        strict_mode=True,
    )

    doc = Document(
        page_content=text,
        metadata={"source_id": source_id},
    )

    graph_documents = transformer.convert_to_graph_documents([doc])

    for gd in graph_documents:
        for node in gd.nodes:
            node.properties.setdefault("source_id", source_id)

    graph.add_graph_documents(
        graph_documents,
        include_source=True,
        baseEntityLabel=True,
    )
