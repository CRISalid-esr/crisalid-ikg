UNWIND $rows AS row
MATCH (n:Embeddable) WHERE elementId(n) = row.element_id
SET n.embedding            = row.embedding,
    n.embedding_hash       = row.embedding_hash,
    n.embedding_model      = row.embedding_model,
    n.embedding_status     = 'success',
    n.embedding_updated_at = datetime(),
    n.embedding_error      = null
