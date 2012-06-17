from wakawaka.models import Revision


for field in Revision._meta.fields[:]:
    if field.name in ('creator',):
        field.rel.related_name = 'waka_revisions'
        #Revision._meta.fields.remove(field)

Revision.creator.related_name = 'waka_revisions'
