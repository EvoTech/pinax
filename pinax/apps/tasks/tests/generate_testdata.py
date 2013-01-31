from __future__ import absolute_import, unicode_literals
import random
import uuid

from django.contrib.auth.models import User

from pinax.apps.tasks.models import Task



def generate_data(tickets, max_tags):
    myuser = User.objects.all()[0]
    for i in range(0, tickets):
        t = Task.objects.create(summary=str(uuid.uuid4()), creator=myuser)
        t.tags = " ".join(["test{0}".format(random.randint(1, max_tags * 4)) for j in range(0, random.randint(round(max_tags / 2), max_tags))])
        t.save()
