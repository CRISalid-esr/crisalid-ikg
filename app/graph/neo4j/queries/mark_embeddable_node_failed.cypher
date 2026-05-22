MATCH (n:Embeddable) WHERE elementId(n) = $element_id
SET n.embedding_status = 'failed',
    n.embedding_error  = $error
