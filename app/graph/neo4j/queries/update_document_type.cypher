MATCH (doc:Document {uid: $document_uid})
SET doc.document_type = $document_type

WITH doc, apoc.node.labels(doc) AS labels
WITH doc, [l IN labels WHERE l <> 'Document'] AS current, $document_labels AS target

CALL apoc.create.removeLabels(doc, [l IN current WHERE NOT l IN target]) YIELD node
CALL apoc.create.addLabels(node, [l IN target WHERE NOT l IN current]) YIELD node
RETURN node AS updated_doc