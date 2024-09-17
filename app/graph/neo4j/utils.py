import os


def load_query(query_name: str) -> str:
    """
    Load a cypher query from the queries directory
    :param query_name: The name of the query
    :return: The cypher query
    """
    queries_dir = os.path.join(os.path.dirname(__file__), 'queries')
    query_path = os.path.join(queries_dir, f'{query_name}.cypher')
    with open(query_path, 'r', encoding='utf8') as query_file:
        return query_file.read()
