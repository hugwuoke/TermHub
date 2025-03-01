"""Queries"""
from functools import cache
from typing import List, Dict
from fastapi import Query
from backend.db.utils import sql_query, sql_query_single_col, get_db_connection, sql_in


def get_concepts(concept_ids: List[int], con=get_db_connection(), table:str='concepts_with_counts') -> List:
    """Get information about concept sets the user has selected"""
    q = f"""
          SELECT *
          FROM {table}
          WHERE concept_id {sql_in(concept_ids)};"""
    rows: List = sql_query(con, q)
    return rows


def get_vocab_of_concepts(id: List[int] = Query(...), con=get_db_connection(), table:str='concept') -> List:
    """Expecting only one vocab for the list of concepts"""
    q = f"""
          SELECT DISTINCT vocabulary_id
          FROM {table}
          WHERE concept_id {sql_in(id)};"""
    vocabs: List = sql_query_single_col(con, q)
    if len(vocabs) > 1:
        raise RuntimeError(f"can only handle concepts from a single vocabulary at a time (for now). Got {', '.join(vocabs)}")
    return vocabs[0]


def get_vocabs_of_concepts(id: List[int] = Query(...), con=get_db_connection(),
                           table:str='concept') -> Dict:
    """Return dict of {vocab: concept_id list}"""
    q = f"""
          SELECT vocabulary_id, array_agg(concept_id) AS concept_ids
          FROM {table}
          WHERE concept_id {sql_in(id)}
          GROUP BY 1 ORDER BY 1
          """
    vocabs: List = sql_query(con, q)
    return dict(vocabs)
