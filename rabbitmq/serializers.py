from rest_framework.serializers import ModelSerializer
from .models import CachedCommission


class CachedCommissionSerializer(ModelSerializer):
    class Meta:
        model = CachedCommission
        fields = "__all__"
