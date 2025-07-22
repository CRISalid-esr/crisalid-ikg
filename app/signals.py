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

institution_created = signal('institution-created')
institution_updated = signal('institution-updated')
institution_unchanged = signal('institution-unchanged')
institution_deleted = signal('institution-deleted')

source_record_created = signal('source-record-created')
source_record_updated = signal('source-record-updated')

document_created_from_sources = signal('document-created-from-sources')
document_sources_changed = signal('document-sources-changed')
document_updated = signal('document-updated')
document_created = signal('document-created')
document_deleted = signal('document-deleted')
document_unchanged = signal('document-unchanged')

harvesting_state_event_received = signal('harvesting-event-received')
harvesting_result_event_received = signal('harvesting-result-event-received')

source_journal_created = signal('source-journal-created')
source_journal_updated = signal('source-journal-updated')
source_journal_unchanged = signal('source-journal-unchanged')
source_journal_deleted = signal('source-journal-deleted')
