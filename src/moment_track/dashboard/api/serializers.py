from rest_framework import serializers

from dashboard.models import AudioFile, User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class AudioFileSerializer(serializers.HyperlinkedModelSerializer):
    uploader = UserSerializer(many=False)

    class Meta:
        model = AudioFile
        fields = (
            'id', 'uploader', 'upload_datetime',
            'name', 'description', 'language_spoken',
            'duration', 'transcription_coverage'
        )
