import os

from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_neo4j import Neo4jGraph
from pydantic import BaseModel

from .graph_transformer import get_llm

router = APIRouter()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")

graph = Neo4jGraph(url=NEO4J_URI, database=NEO4J_DATABASE)


class ChatRequest(BaseModel):
    messages: list[dict]


class ChatResponse(BaseModel):
    response: str


def retrieve_graph_context(query: str) -> str:
    query = (query or "").strip()
    if not query:
        return "No query provided."

    # If the user asks a generic question, don't rely on fulltext.
    generic_triggers = {
        "do you know any people",
        "do you know people",
        "who do you know",
        "list people",
        "show people",
        "any candidates",
        "any persons",
    }
    is_generic = query.lower().strip(" ?!.") in generic_triggers

    if not is_generic:
        seed_people_cypher = """
        CALL db.index.fulltext.queryNodes('search_index', $query)
        YIELD node, score
        WITH node, score
        ORDER BY score DESC
        LIMIT 10
        WITH node,
             CASE WHEN node:Person THEN node ELSE NULL END AS p0
        OPTIONAL MATCH (node)--(p1:Person)
        WITH coalesce(p0, p1) AS p
        WHERE p IS NOT NULL
        RETURN elementId(p) AS pid
        LIMIT 5
        """
        try:
            seed = graph.query(seed_people_cypher, {"query": query})
        except Exception:
            seed = []
        person_ids = [r["pid"] for r in seed if r.get("pid")]
    else:
        person_ids = []

    if not person_ids:
        fallback_people_cypher = """
        MATCH (p:Person)
        WHERE coalesce(p.name,'') <> ''
        RETURN elementId(p) AS pid
        ORDER BY p.name
        LIMIT 5
        """
        try:
            seed = graph.query(fallback_people_cypher)
        except Exception:
            return "Graph search failed."
        person_ids = [r["pid"] for r in seed if r.get("pid")]

    if not person_ids:
        return "No people found in the knowledge graph."

    expand_cypher = """
    MATCH (p:Person)
    WHERE elementId(p) IN $pids
    OPTIONAL MATCH (p)-[hs:HAS_SKILL]->(s:Skill)
    OPTIONAL MATCH (p)-[wa:WORKED_AT]->(c:Company)
    OPTIONAL MATCH (p)-[sa:STUDIED_AT]->(u:University)
    OPTIONAL MATCH (p)-[:EARNED]->(cert:Certification)
    RETURN
        p.name AS person_name,
        p.headline AS headline,
        collect(DISTINCT s.id)[..10] AS skills,
        collect(DISTINCT {company: c.name, role: wa.role})[..5] AS experience,
        collect(DISTINCT {university: u.name, degree: sa.degree})[..3] AS education,
        collect(DISTINCT cert.name)[..5] AS certifications
    ORDER BY person_name
    """

    records = graph.query(expand_cypher, {"pids": person_ids})

    context_parts = []
    for r in records:
        lines = [f"Person: {r.get('person_name', 'Unknown')}"]
        if r.get("headline"):
            lines.append(f"Headline: {r['headline']}")
        if r.get("skills"):
            skills = [x for x in r["skills"] if x]
            if skills:
                lines.append(f"Skills: {', '.join(skills)}")
        if r.get("experience"):
            exp = [f"{e.get('company')} ({e.get('role')})" for e in r["experience"] if e.get("company")]
            if exp:
                lines.append(f"Experience: {', '.join(exp)}")
        if r.get("education"):
            edu = [f"{e.get('university')} ({e.get('degree')})" for e in r["education"] if e.get("university")]
            if edu:
                lines.append(f"Education: {', '.join(edu)}")
        if r.get("certifications"):
            certs = [c for c in r["certifications"] if c]
            if certs:
                lines.append(f"Certifications: {', '.join(certs)}")

        context_parts.append("\n".join(lines))

    return "\n\n---\n\n".join(context_parts)[:8000]


CHAT_SYSTEM_PROMPT = """You are a chatbot connected to a Neo4j knowledge graph of CV/resume data.

You will receive "Knowledge Graph Context" which is the ONLY source of truth.
- Answer the user's question using that context.
- If the answer isn't in the context, say "I don't see that in the graph yet."
- Do NOT ask the user to upload a CV unless the context explicitly says the graph is empty.
- If asked "do you know any people?", list up to 10 people from the context.
- Do not reveal that you are using graph under the hood. Say that you know what you know based on the files provided by the user. 

Knowledge Graph Context:
<context>
{context}
</context>
"""


@router.post("/chat")
def chat(request: ChatRequest) -> ChatResponse:
    llm = get_llm()

    user_query = next(
        (m["content"] for m in reversed(request.messages) if m["role"] == "user"),
        ""
    )

    graph_context = retrieve_graph_context(user_query)

    system_prompt = CHAT_SYSTEM_PROMPT.format(context=graph_context)

    langchain_messages = [SystemMessage(content=system_prompt)]

    for msg in request.messages:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            langchain_messages.append(AIMessage(content=msg["content"]))

    response = llm.invoke(langchain_messages)

    return ChatResponse(response=response.content)
