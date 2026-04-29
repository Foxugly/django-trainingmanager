from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Attendance, AttendanceStatus


class AttendanceStatusSerializer(serializers.ModelSerializer):
    """Public flavor: 'label' is auto-localized by modeltranslation."""

    class Meta:
        model = AttendanceStatus
        fields = [
            "id",
            "code",
            "label",
            "is_default",
            "order",
            "color",
            "is_active",
        ]
        read_only_fields = fields


class AttendanceStatusAdminSerializer(serializers.ModelSerializer):
    """Admin flavor: exposes per-language label variants."""

    class Meta:
        model = AttendanceStatus
        fields = [
            "id",
            "code",
            "label_fr",
            "label_nl",
            "label_en",
            "label_it",
            "label_es",
            "is_default",
            "order",
            "color",
            "is_active",
        ]
        read_only_fields = ["id"]


class AttendanceSerializer(serializers.ModelSerializer):
    member_fullname = serializers.SerializerMethodField()
    status_code = serializers.CharField(source="status.code", read_only=True)

    class Meta:
        model = Attendance
        fields = [
            "id",
            "event",
            "member",
            "member_fullname",
            "status",
            "status_code",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "event",
            "member_fullname",
            "status_code",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.CharField())
    def get_member_fullname(self, obj) -> str:
        m = obj.member
        parts = [p for p in [m.firstname, m.lastname] if p]
        return " ".join(parts) if parts else f"Member#{m.pk}"


class AttendanceBulkItemSerializer(serializers.Serializer):
    member_id = serializers.IntegerField()
    status_code = serializers.CharField(max_length=30)


class AttendanceBulkSerializer(serializers.Serializer):
    attendances = AttendanceBulkItemSerializer(many=True)

    def validate_attendances(self, value):
        if not value:
            raise serializers.ValidationError(
                "attendances list cannot be empty.",
                code="empty_attendances",
            )
        member_ids = [item["member_id"] for item in value]
        if len(member_ids) != len(set(member_ids)):
            raise serializers.ValidationError(
                "Duplicate member_id in attendances list.",
                code="duplicate_member",
            )
        return value
