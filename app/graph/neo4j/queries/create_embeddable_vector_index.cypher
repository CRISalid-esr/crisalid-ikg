CREATE VECTOR INDEX embeddable_embedding IF NOT EXISTS
FOR (n:Embeddable) ON n.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: $dims,
  `vector.similarity_function`: 'cosine'
}}
