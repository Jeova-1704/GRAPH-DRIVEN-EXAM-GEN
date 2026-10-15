"""Cypher statements for :Questao nodes (official ENEM items + LLM-generated corpus items).

alternativas is stored as a JSON string (questoes_json) because Neo4j node properties
must be primitives or homogeneous arrays — not nested maps.
"""

CONSTRAINTS = [
    "CREATE CONSTRAINT questao_id IF NOT EXISTS FOR (q:Questao) REQUIRE q.id IS UNIQUE",
]

MERGE_QUESTAO = """
MATCH (h:Habilidade {codigo: $habilidade_codigo})
MERGE (q:Questao {id: $id})
SET
    q.enunciado = $enunciado,
    q.alternativas_json = $alternativas_json,
    q.gabarito = $gabarito,
    q.justificativa = $justificativa,
    q.origem = $origem,
    q.ano_origem = $ano_origem,
    q.validacao_estrutural_ok = $validacao_estrutural_ok
MERGE (q)-[:AVALIA]->(h)
"""

SET_METRICAS = """
MATCH (q:Questao {id: $id})
SET
    q.cobertura_lexical = $cobertura_lexical,
    q.especificidade_curricular = $especificidade_curricular,
    q.similaridade_semantica = $similaridade_semantica,
    q.ttr = $ttr,
    q.fkgl = $fkgl
"""

SET_METRICAS_EXTRA = """
MATCH (q:Questao {id: $id})
SET
    q.especificidade_curricular = $especificidade_curricular,
    q.similaridade_semantica = $similaridade_semantica
"""

SET_JULGAMENTO = """
MATCH (q:Questao {id: $id})
SET
    q.judge_d1_alinhamento = $d1,
    q.judge_d2_objetos_conhecimento = $d2,
    q.judge_d3_distratores = $d3,
    q.judge_d4_escolaridade = $d4,
    q.judge_d5_formato_enem = $d5,
    q.judge_justificativa = $justificativa
"""

GET_FEWSHOTS_POR_HABILIDADE = """
MATCH (q:Questao {origem: "ENEM"})-[:AVALIA]->(:Habilidade {codigo: $habilidade_codigo})
RETURN q.enunciado AS enunciado, q.alternativas_json AS alternativas_json, q.gabarito AS gabarito
LIMIT $limite
"""

_CAMPOS_QUESTAO = """
    q.id AS id, h.codigo AS habilidade_codigo, q.enunciado AS enunciado,
    q.alternativas_json AS alternativas_json, q.gabarito AS gabarito, q.justificativa AS justificativa,
    q.origem AS origem, q.ano_origem AS ano_origem, q.validacao_estrutural_ok AS validacao_estrutural_ok,
    q.cobertura_lexical AS cobertura_lexical, q.especificidade_curricular AS especificidade_curricular,
    q.similaridade_semantica AS similaridade_semantica, q.ttr AS ttr, q.fkgl AS fkgl,
    q.judge_d1_alinhamento AS judge_d1_alinhamento, q.judge_d2_objetos_conhecimento AS judge_d2_objetos_conhecimento,
    q.judge_d3_distratores AS judge_d3_distratores, q.judge_d4_escolaridade AS judge_d4_escolaridade,
    q.judge_d5_formato_enem AS judge_d5_formato_enem, q.judge_justificativa AS judge_justificativa
"""

GET_QUESTAO = f"""
MATCH (q:Questao {{id: $id}})-[:AVALIA]->(h:Habilidade)
RETURN {_CAMPOS_QUESTAO}
"""

COUNT_QUESTOES_POR_ORIGEM = """
MATCH (q:Questao {origem: $origem})
RETURN count(q) AS total
"""

GET_QUESTOES_POR_ORIGEM = f"""
MATCH (q:Questao {{origem: $origem}})-[:AVALIA]->(h:Habilidade)
RETURN {_CAMPOS_QUESTAO}
"""
