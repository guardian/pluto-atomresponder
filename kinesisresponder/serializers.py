from rest_framework.serializers import ModelSerializer
from .models import KinesisTracker


class KinesisTrackerSerializer(ModelSerializer):
    class Meta:
        model = KinesisTracker
        fields = '__all__'