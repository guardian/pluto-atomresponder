from rest_framework.serializers import ModelSerializer
from .models import CachedCommission, ProjectModel


class CachedCommissionSerializer(ModelSerializer):
    class Meta:
        model = CachedCommission
        fields = "__all__"


class ProjectModelSerializer(ModelSerializer):
    class Meta:
        model = ProjectModel
        fields = "__all__"
