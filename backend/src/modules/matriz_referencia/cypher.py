"""Cypher statements for the ENEM Reference Matrix graph.

Schema (matches Figure 1b of the approved paper): (:Area)-[:POSSUI]->(:Competencia)
-[:REQUER]->(:Habilidade)-[:ABRANGE]->(:ObjetoConhecimento). Generated items attach
via (:Questao)-[:AVALIA]->(:Habilidade) (see modules/questoes).

All statements are idempotent MERGEs (Secao 3.4.3 do TCC) — safe to re-run.
"""

CONSTRAINTS = [
    "CREATE CONSTRAINT area_codigo IF NOT EXISTS FOR (a:Area) REQUIRE a.codigo IS UNIQUE",
    "CREATE CONSTRAINT competencia_area_numero IF NOT EXISTS FOR (c:Competencia) REQUIRE (c.area_codigo, c.numero) IS UNIQUE",
    "CREATE CONSTRAINT habilidade_codigo IF NOT EXISTS FOR (h:Habilidade) REQUIRE h.codigo IS UNIQUE",
    "CREATE CONSTRAINT objeto_conhecimento_codigo IF NOT EXISTS FOR (o:ObjetoConhecimento) REQUIRE o.codigo IS UNIQUE",
]

MERGE_AREA = """
MERGE (a:Area {codigo: $codigo})
SET a.nome = $nome
"""

MERGE_OBJETO_CONHECIMENTO = """
MATCH (a:Area {codigo: $area_codigo})
MERGE (oc:ObjetoConhecimento {codigo: $codigo})
SET oc.titulo = $titulo, oc.descricao = $descricao, oc.area_codigo = $area_codigo
MERGE (a)-[:POSSUI_OC]->(oc)
"""

MERGE_COMPETENCIA = """
MATCH (a:Area {codigo: $area_codigo})
MERGE (c:Competencia {area_codigo: $area_codigo, numero: $numero})
SET c.descricao = $descricao
MERGE (a)-[:POSSUI]->(c)
"""

MERGE_HABILIDADE = """
MATCH (c:Competencia {area_codigo: $area_codigo, numero: $competencia_numero})
MERGE (h:Habilidade {codigo: $codigo})
SET h.descricao = $descricao, h.area_codigo = $area_codigo
MERGE (c)-[:REQUER]->(h)
"""

MERGE_HABILIDADE_ABRANGE_OC = """
MATCH (h:Habilidade {codigo: $habilidade_codigo})
MATCH (oc:ObjetoConhecimento {codigo: $oc_codigo})
MERGE (h)-[:ABRANGE]->(oc)
"""

COUNT_NODES_BY_LABEL = """
MATCH (n)
WHERE $label IN labels(n)
RETURN count(n) AS total
"""

COUNT_HABILIDADES_SEM_OC = """
MATCH (h:Habilidade)
WHERE NOT (h)-[:ABRANGE]->(:ObjetoConhecimento)
RETURN count(h) AS total
"""

COUNT_HABILIDADES_SEM_COMPETENCIA = """
MATCH (h:Habilidade)
WHERE NOT (:Competencia)-[:REQUER]->(h)
RETURN count(h) AS total
"""

COUNT_COMPETENCIAS_SEM_AREA = """
MATCH (c:Competencia)
WHERE NOT (:Area)-[:POSSUI]->(c)
RETURN count(c) AS total
"""

GET_AREAS = """
MATCH (a:Area)
RETURN a.codigo AS codigo, a.nome AS nome
ORDER BY a.codigo
"""

GET_HABILIDADE_COM_CONTEXTO = """
MATCH (h:Habilidade {codigo: $codigo})<-[:REQUER]-(c:Competencia)<-[:POSSUI]-(a:Area)
OPTIONAL MATCH (h)-[:ABRANGE]->(oc:ObjetoConhecimento)
RETURN
    h.codigo AS habilidade_codigo,
    h.descricao AS habilidade_descricao,
    c.numero AS competencia_numero,
    c.descricao AS competencia_descricao,
    a.codigo AS area_codigo,
    a.nome AS area_nome,
    collect({codigo: oc.codigo, titulo: oc.titulo, descricao: oc.descricao}) AS objetos_conhecimento
"""

GET_HABILIDADES_POR_AREA = """
MATCH (a:Area {codigo: $area_codigo})-[:POSSUI]->(:Competencia)-[:REQUER]->(h:Habilidade)
RETURN h.codigo AS codigo, h.descricao AS descricao
ORDER BY h.codigo
"""
