"""Save read-only Neo4j evidence for the lab report. Run after bench_kg.py --judge."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.graph import Neo4jGraph  # noqa: E402

QUERIES = {
    "labels": "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC",
    "relationships": "MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS n ORDER BY n DESC",
    "doc_coverage": "MATCH (n) WHERE n.doc_id IS NOT NULL RETURN n.doc_id AS doc_id, count(*) AS n ORDER BY doc_id",
    "no_bridge": "MATCH (k:Case) WHERE NOT (k)-[:CHARGED_WITH]->() RETURN k.name AS name, k.doc_id AS doc_id ORDER BY name",
    "substances": "MATCH (s:Substance) RETURN s.name AS name ORDER BY toLower(s.name)",
    "cases": "MATCH (k:Case) RETURN k.name AS name, k.doc_id AS doc_id, k.summary AS summary ORDER BY name",
    "empty_person_charge": "MATCH (p:Person)-[r:INVOLVED_IN]->(k:Case) WHERE coalesce(r.charge, '') = '' RETURN p.name AS person, r.role AS role, r.sentence AS sentence, k.name AS case_name, k.doc_id AS doc_id ORDER BY person",
    "mdma_cases": "MATCH (k:Case)-[r:INVOLVES]->(s:Substance) WHERE toLower(s.name) = 'mdma' OPTIONAL MATCH (p:Person)-[:INVOLVED_IN]->(k) RETURN k.name AS case_name, k.doc_id AS doc_id, r.amount AS amount, collect(DISTINCT p.name) AS people ORDER BY case_name",
    "repeated_person_cases": "MATCH (p:Person)-[:INVOLVED_IN]->(k:Case) WITH p, collect(DISTINCT {name:k.name, doc_id:k.doc_id}) AS cases WHERE size(cases) > 1 RETURN p.name AS person, p.aliases AS aliases, cases ORDER BY person",
    "article_255": "MATCH (a:Article {id:'Điều 255 BLHS'})-[:HAS_CLAUSE]->(cl:Clause) RETURN cl.number AS number, cl.penalty AS penalty ORDER BY number",
    "missing_doc_id": "MATCH (n) WHERE n.doc_id IS NULL RETURN labels(n)[0] AS label, count(*) AS n ORDER BY label",
}


def main() -> None:
    load_dotenv(ROOT / ".env", override=False)
    graph = Neo4jGraph(os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                       os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password123"))
    try:
        evidence = {name: {"cypher": query, "rows": graph.run(query)} for name, query in QUERIES.items()}
        evidence["stats"] = graph.stats()
        evidence["nodes"] = graph.run("MATCH (n) RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS properties ORDER BY id")
        evidence["edges"] = graph.run("MATCH (a)-[r]->(b) RETURN elementId(a) AS source, type(r) AS type, properties(r) AS properties, elementId(b) AS target")
        target = ROOT / "report/validation/graph_audit.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Saved {target.relative_to(ROOT)}; {evidence['stats']}")
        for name in ("labels", "no_bridge", "substances", "empty_person_charge", "mdma_cases", "repeated_person_cases"):
            print(name, json.dumps(evidence[name]["rows"], ensure_ascii=False))
    finally:
        graph.close()


if __name__ == "__main__":
    main()
