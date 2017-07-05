from rest_framework import serializers

from dashboard.models import AudioFile, User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """Serialize the user model showing just some essential information."""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class AudioFileSerializer(serializers.HyperlinkedModelSerializer):
    """Serialize the AudioFile model showing its information and
    the ones regarding the uploader user.
    """
    uploader = UserSerializer(many=False)

    class Meta:
        model = AudioFile
        fields = (
            'id', 'uploader', 'upload_datetime',
            'name', 'description', 'language_spoken',
            'duration', 'transcription_coverage'
        )
