from rest_framework.serializers import ModelSerializer, Serializer, IntegerField, CharField
from .models import CachedCommission, ProjectModel


class CachedCommissionSerializer(Serializer):
    id = IntegerField()
    title = CharField(max_length=32768)


class ProjectModelSerializer(ModelSerializer):
    class Meta:
        model = ProjectModel
        fields = "__all__"
