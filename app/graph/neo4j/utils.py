import os
from typing import cast

from typing_extensions import LiteralString


def load_query(query_name: LiteralString) -> LiteralString:
    """
    Load a cypher query from the queries directory
    :param query_name: The name of the query
    :return: The cypher query
    """
    queries_dir = os.path.join(os.path.dirname(__file__), 'queries')
    query_path = os.path.join(queries_dir, f'{query_name}.cypher')
    with open(query_path, 'r', encoding='utf8') as query_file:
        file_content = query_file.read()
        return cast(LiteralString, file_content)
