import os

from LLMGraphTransformer import LLMGraphTransformer
from LLMGraphTransformer.schema import NodeSchema
from LLMGraphTransformer.schema import RelationshipSchema
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_neo4j import Neo4jGraph
from langchain_openai import AzureChatOpenAI

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

SCHEMA_PROMPT = """
You extract a KNOWLEDGE GRAPH from CV / resume text.

Node types:
- Person {id, name, location, email, phone, headline, total_experience_years}
- Skill {id, category, subcategory}
- Company {id, name, industry, size, location}
- Project {id, title, description, start_date, end_date, budget}
- Certification {id, name, provider, date_earned, expiry_date}
- University {id, name, location, ranking}
- RFP {id, title, description, requirements, budget, deadline}

Relationships:
- (Person)-[HAS_SKILL {proficiency, years_experience}]->(Skill)
- (Person)-[WORKED_AT {role, start_date, end_date}]->(Company)
- (Person)-[WORKED_ON {role, contribution, start_date, end_date}]->(Project)
- (Person)-[EARNED {date, score}]->(Certification)
- (Person)-[STUDIED_AT {degree, graduation_year, gpa}]->(University)
- (Person)-[ASSIGNED_TO {allocation_percentage, start_date, end_date}]->(Project)
- (Project)-[REQUIRES {minimum_level, preferred_level}]->(Skill)
- (RFP)-[NEEDS {required_count, experience_level}]->(Skill)

Rules:
- There must be EXACTLY ONE Person node per CV. That Person is the CV owner.
- Do NOT create Person nodes for companies or organizations. Names like
  "Luna Web Design" or "Express Scripts" must be Company nodes, not Person nodes.
- Person.total_experience_years must be numeric (e.g. "6"). If not stated, omit it.
  Do NOT put job titles (e.g. "Senior Web Developer") into this field.
  Put that text into Person.headline instead, or omit it.
- Skills must be concrete abilities, technologies, tools, or soft skills
  (e.g., "Java", "HTML", "Project Management").
  Do NOT create Skill nodes from job titles (e.g., "Web Developer").
- If a property value is not explicitly present, omit that property.
  Never use empty strings ("") or placeholders like "N/A".
- Always connect the Person node to:
  - all Skills via HAS_SKILL
  - each Company via WORKED_AT
  - University via STUDIED_AT
  - each Certification via EARNED
  - each Project via WORKED_ON or ASSIGNED_TO when applicable.
- Use only the node types, relationship types, and property names listed above.
- Do NOT hallucinate data.
- Add property `source_id` to every node and relationship, from document metadata.
- Whenever you create a Certification node that belongs to the Person (e.g. degrees, professional certs),
  you MUST also create (Person)-[EARNED {date: date_earned}]->(Certification).
"""
SYSTEM_PROMPT = SCHEMA_PROMPT.replace("{", "{{").replace("}", "}}")


def ingest_cv_text_into_graph(text: str, source_id: str) -> None:
    llm = get_llm()

    allowed_nodes = [
        NodeSchema(type="Person"),
        NodeSchema(type="Skill"),
        NodeSchema(type="Company"),
        NodeSchema(type="Project"),
        NodeSchema(type="Certification"),
        NodeSchema(type="University"),
        NodeSchema(type="RFP"),
    ]

    allowed_rels = [
        RelationshipSchema(source="Person", type="HAS_SKILL", target="Skill"),
        RelationshipSchema(source="Person", type="WORKED_AT", target="Company"),
        RelationshipSchema(source="Person", type="WORKED_ON", target="Project"),
        RelationshipSchema(source="Person", type="EARNED", target="Certification"),
        RelationshipSchema(source="Person", type="STUDIED_AT", target="University"),
        RelationshipSchema(source="Person", type="ASSIGNED_TO", target="Project"),
        RelationshipSchema(source="Project", type="REQUIRES", target="Skill"),
        RelationshipSchema(source="RFP", type="NEEDS", target="Skill"),
    ]

    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=allowed_nodes,
        allowed_relationships=allowed_rels,
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
        include_source=False,
        baseEntityLabel=True,
    )
