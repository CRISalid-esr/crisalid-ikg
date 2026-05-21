MATCH (n:Embeddable)
RETURN n.embedding_status AS status, count(n) AS count
