MATCH (n:Embeddable)
WHERE n.embedding_status IN $statuses
  AND ($types IS NULL OR n.type IN $types)
  AND ($model_exclude IS NULL OR n.embedding_model <> $model_exclude OR n.embedding_model IS NULL)
RETURN elementId(n) AS element_id, n.value AS value, n.type AS type
SKIP $skip LIMIT $batch_size
