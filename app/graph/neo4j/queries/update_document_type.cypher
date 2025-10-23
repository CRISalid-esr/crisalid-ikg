MATCH (doc:Document {uid: $document_uid})
SET doc.document_type = $document_type

WITH doc, apoc.node.labels(doc) AS labels
WITH doc, [l IN labels WHERE l <> 'Document'] AS current, $document_labels AS target

CALL apoc.create.removeLabels(doc, [l IN current WHERE NOT l IN target]) YIELD node AS doc_tmp
CALL apoc.create.addLabels(doc_tmp, [l IN target WHERE NOT l IN current]) YIELD node AS updated_doc
RETURN updated_doc