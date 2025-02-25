from blinker import signal

person_created = signal('person-created')
person_unchanged = signal('person-unchanged')
person_updated = signal('person-updated')
person_identifiers_updated = signal('person-identifiers-updated')
person_deleted = signal('person-deleted')

publications_to_be_updated = signal('publications-to-update')

structure_created = signal('structure-created')
structure_updated = signal('structure-updated')
structure_unchanged = signal('structure-unchanged')
structure_deleted = signal('structure-deleted')

source_record_created = signal('source-record-created')
source_record_updated = signal('source-record-updated')

document_sources_changed = signal('document-sources-changed')
document_updated = signal('document-updated')
document_created = signal('document-created')
document_deleted = signal('document-deleted')
document_unchanged = signal('document-unchanged')
