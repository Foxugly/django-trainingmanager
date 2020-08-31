from bootstrap_modal_forms.generic import BSModalCreateView, BSModalUpdateView, BSModalDeleteView

from exercise.models import Stroke, EnergySystem, EnergySegment, Exercise
from tools.generic_views import *


class StrokeCreateView(GenericCreateView):
    model = Stroke


class StrokeListView(GenericListView):
    model = Stroke


class StrokeUpdateView(GenericUpdateView):
    model = Stroke


class StrokeDetailView(GenericDetailView):
    model = Stroke


class StrokeDeleteView(GenericDeleteView):
    model = Stroke


class EnergySystemCreateView(GenericCreateView):
    model = EnergySystem


class EnergySystemListView(GenericListView):
    model = EnergySystem


class EnergySystemUpdateView(GenericUpdateView):
    model = EnergySystem


class EnergySystemDetailView(GenericDetailView):
    model = EnergySystem


class EnergySystemDeleteView(GenericDeleteView):
    model = EnergySystem


class EnergySegmentCreateView(GenericCreateView):
    model = EnergySegment


class EnergySegmentListView(GenericListView):
    model = EnergySegment


class EnergySegmentUpdateView(GenericUpdateView):
    model = EnergySegment


class EnergySegmentDetailView(GenericDetailView):
    model = EnergySegment


class EnergySegmentDeleteView(GenericDeleteView):
    model = EnergySegment


class ExerciseCreateView(BSModalCreateView):
    model = Exercise

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


class ExerciseListView(GenericListView):
    model = Exercise


class ExerciseUpdateView(BSModalUpdateView):
    model = Exercise

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


class ExerciseDetailView(GenericDetailView):
    model = Exercise


class ExerciseDeleteView(BSModalDeleteView):
    model = Exercise

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url
