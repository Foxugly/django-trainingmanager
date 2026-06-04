from django.test import TestCase

from agenda.models import Agenda
from event.models import Event
from round.models import Round


class RoundSaveTests(TestCase):
    def test_save_links_to_event_idempotently(self):
        # Round.save() adds itself to refer_event.rounds; saving twice must not
        # create a duplicate M2M link (add() is idempotent).
        agenda = Agenda.objects.create()
        event = Event.objects.create(name="E", refer_agenda=agenda)
        r = Round.objects.create(order=1, count=1, refer_event=event)
        r.save()
        self.assertEqual(event.rounds.count(), 1)
        self.assertEqual(event.rounds.filter(pk=r.pk).count(), 1)
