from wakawaka.models import Revision
#import rpdb2; rpdb2.start_embedded_debugger('111')
for field in Revision._meta.fields[:]:
    if field.name in ('creator',):
        field.rel.related_name = 'waka_revisions'
        #Revision._meta.fields.remove(field)

Revision.creator.related_name = 'waka_revisions'
