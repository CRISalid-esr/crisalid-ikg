MATCH (document:Document)-[:RECORDED_BY]->(:SourceRecord {uid: $source_record_uid})
OPTIONAL MATCH (document)-[:HAS_TITLE]->(title:Literal {type: 'document_title'})
OPTIONAL MATCH (document)-[:HAS_ABSTRACT]->(abstract:TextLiteral {type: 'document_abstract'})
OPTIONAL MATCH (document)-[:HAS_CONTRIBUTION]->(contribution:Contribution)<-[:HAS_CONTRIBUTION]-(contributor:Person)
OPTIONAL MATCH (contributor:Person)-[:RECORDED_BY]->(sp:SourcePerson)
MATCH (document)-[:RECORDED_BY]->(sr:SourceRecord)
OPTIONAL MATCH (document)-[:HAS_SUBJECT]->(c:Concept)
OPTIONAL MATCH (document)-[pi:PUBLISHED_IN]->(journal:Journal)
WITH document, title, abstract, collect(DISTINCT contribution {. *, contributor:contributor}) AS contributions,
     sr, c, pi, journal
RETURN document,
       collect(DISTINCT sr) AS source_records,
       collect(DISTINCT title) AS titles,
       collect(DISTINCT abstract) AS abstracts,
       collect(DISTINCT c) AS subjects,
       contributions,
       collect(DISTINCT {volume: pi.volume, issue: pi.issue, pages: pi.pages, journal: journal }) AS publication_channels,
       labels(document) AS labels
