import factory
from factory.django import DjangoModelFactory

from django.contrib.auth import get_user_model

from agenda.models import Agenda
from event.models import Event
from exercise.models import EnergySegment, EnergySystem, Exercise, Stroke
from member.models import Member
from round.models import Round
from team.models import Team


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"user_factory_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@local.test")
    is_active = True
    password = factory.PostGenerationMethodCall('set_password', 'pass1234')


class TeamFactory(DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Sequence(lambda n: f"Team {n}")
    owner = factory.SubFactory(UserFactory)
    is_active = True
    is_public = False


class StrokeFactory(DjangoModelFactory):
    class Meta:
        model = Stroke

    name = factory.Sequence(lambda n: f"Stroke {n}")


class EnergySystemFactory(DjangoModelFactory):
    class Meta:
        model = EnergySystem

    name = factory.Sequence(lambda n: f"ES {n}")


class EnergySegmentFactory(DjangoModelFactory):
    class Meta:
        model = EnergySegment

    abv = factory.Sequence(lambda n: f"abv{n}")
    description = "test segment"
    energysystem = factory.SubFactory(EnergySystemFactory)


class MemberFactory(DjangoModelFactory):
    class Meta:
        model = Member

    firstname = factory.Sequence(lambda n: f"First{n}")
    lastname = factory.Sequence(lambda n: f"Last{n}")
    email = factory.LazyAttribute(
        lambda o: f"{o.firstname}.{o.lastname}@local.test".lower()
    )
    phonenumber = "+32400000000"

    @factory.post_generation
    def teams(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for team in extracted:
            self.teams.add(team)


class AgendaFactory(DjangoModelFactory):
    class Meta:
        model = Agenda

    name = factory.Sequence(lambda n: f"Agenda {n}")
    team = factory.SubFactory(TeamFactory)


class EventFactory(DjangoModelFactory):
    class Meta:
        model = Event

    name = factory.Sequence(lambda n: f"Event {n}")
    refer_agenda = factory.SubFactory(AgendaFactory)


class RoundFactory(DjangoModelFactory):
    class Meta:
        model = Round

    order = 1
    count = 1
    refer_event = factory.SubFactory(EventFactory)


class ExerciseFactory(DjangoModelFactory):
    class Meta:
        model = Exercise

    order = 1
    repetition = 1
    distance = 100
    refer_round = factory.SubFactory(RoundFactory)
