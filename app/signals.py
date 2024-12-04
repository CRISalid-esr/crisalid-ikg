from blinker import signal

person_created = signal('person-created')
person_unchanged = signal('person-unchanged')
person_identifiers_updated = signal('person-identifiers-updated')
person_deleted = signal('person-deleted')

source_record_created = signal('source-record-created')
source_record_updated = signal('source-record-updated')

textual_document_updated = signal('textual-document-updated')
