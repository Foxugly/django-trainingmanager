import factory
from factory.django import DjangoModelFactory

from django.contrib.auth import get_user_model

from event.models import Event
from exercise.models import EnergySegment, EnergySystem, Exercise, Modality
from member.models import Member
from program.models import Program
from round.models import Round
from sport.models import Sport
from team.models import Team


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda n: f"user_factory_{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@local.test")
    is_active = True
    password = factory.PostGenerationMethodCall("set_password", "pass1234")


class SportFactory(DjangoModelFactory):
    class Meta:
        model = Sport
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Sport {n}")
    slug = factory.Sequence(lambda n: f"sport-{n}")
    is_active = True


class TeamFactory(DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Sequence(lambda n: f"Team {n}")
    owner = factory.SubFactory(UserFactory)
    sport = factory.SubFactory(SportFactory)
    is_active = True
    is_public = False


class ModalityFactory(DjangoModelFactory):
    class Meta:
        model = Modality

    name = factory.Sequence(lambda n: f"Modality {n}")
    sport = factory.SubFactory(SportFactory)


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
    email = factory.LazyAttribute(lambda o: f"{o.firstname}.{o.lastname}@local.test".lower())
    phonenumber = "+32400000000"

    @factory.post_generation
    def teams(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for team in extracted:
            self.teams.add(team)


class ProgramFactory(DjangoModelFactory):
    class Meta:
        model = Program

    name = factory.Sequence(lambda n: f"Program {n}")
    team = factory.SubFactory(TeamFactory)


class EventFactory(DjangoModelFactory):
    class Meta:
        model = Event

    name = factory.Sequence(lambda n: f"Event {n}")
    refer_program = factory.SubFactory(ProgramFactory)

    @factory.post_generation
    def rounds(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for r in extracted:
            obj.rounds.add(r)


class RoundFactory(DjangoModelFactory):
    class Meta:
        model = Round

    order = 1
    count = 1
    sport = factory.SubFactory(SportFactory)

    @factory.post_generation
    def event(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted is not None:
            extracted.rounds.add(obj)

    @factory.post_generation
    def exercises(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for ex in extracted:
            obj.exercises.add(ex)


class ExerciseFactory(DjangoModelFactory):
    class Meta:
        model = Exercise

    order = 1
    repetition = 1
    distance = 100

    @factory.post_generation
    def round(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted is not None:
            extracted.exercises.add(obj)
