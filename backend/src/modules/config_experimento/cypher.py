GET_CONFIG = """
MATCH (c:Config {id: "default"})
RETURN c
"""

MERGE_CONFIG = """
MERGE (c:Config {id: "default"})
SET c += $campos
RETURN c
"""
