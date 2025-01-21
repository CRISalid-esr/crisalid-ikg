from blinker import signal

person_created = signal('person-created')
person_unchanged = signal('person-unchanged')
person_updated = signal('person-updated')
person_identifiers_updated = signal('person-identifiers-updated')
person_deleted = signal('person-deleted')

structure_created = signal('structure-created')
structure_updated = signal('structure-updated')
structure_unchanged = signal('structure-unchanged')
structure_deleted = signal('structure-deleted')

source_record_created = signal('source-record-created')
source_record_updated = signal('source-record-updated')

textual_document_sources_changed = signal('textual_document_sources_changed')
textual_document_updated = signal('textual-document-updated')
textual_document_created = signal('textual-document-created')
textual_document_deleted = signal('textual-document-deleted')
textual_document_unchanged = signal('textual-document-unchanged')
