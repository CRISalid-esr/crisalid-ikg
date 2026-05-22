MATCH (n:Embeddable)
SET n.embedding        = null,
    n.embedding_hash   = null,
    n.embedding_status = 'pending',
    n.embedding_error  = null
