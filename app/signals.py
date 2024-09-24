from blinker import signal

person_created = signal('person-created')
person_identifiers_updated = signal('person-identifiers-updated')
person_deleted = signal('person-deleted')

source_record_created = signal('source-record-created')
