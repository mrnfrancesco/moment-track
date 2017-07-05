from collections import OrderedDict
from datetime import timedelta

import math
from django.db.models import Sum, F
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response

from moment_track import settings

from dashboard.api.serializers import AudioFileSerializer
from dashboard.models import AudioFile, PrivateUser, Company, EmployeeUser, CreditsPacketPurchase


class AudioFileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to view and search audio files

    list:
    Return a list of all public files uploaded

    retrieve:
    Return the specified public files if it exists
    """
    queryset = AudioFile.objects.filter(is_public=True)
    serializer_class = AudioFileSerializer
    filter_fields = ('name', 'description', 'language_spoken', 'uploader__email')
    ordering_fields = ('name', 'upload_datetime', 'trancription_coverage')
    ordering = ('-upload_datetime', )


class SearchInFile(APIView):
    """
    Return the time interval(s) in which the specified query has been pronounced
    in the specified file.

    Results will follow this format:
    ```json
    {
        "precision": Float (precision in seconds for the results),
        "results": [
            {
                "offset": Float (seconds from the beginning of the file),
                "confidence": Float (confidence from 0 to 1 of the result)
            },
            ...
        ]
    }
    ```
    """
    def get(self, request, id, query):
        try:
            audio = AudioFile.objects.get(id=id, is_public=True)
        except AudioFile.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        query = query.strip()
        if not query:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        results = audio.transcriptions\
            .filter(text__icontains=query)\
            .order_by('offset', 'confidence')\
            .values_list('offset', 'confidence')

        results = [
            {'offset': offset, 'confidence': confidence}
            for offset, confidence in OrderedDict(results).items()
        ]

        return Response({
            'precision': settings.MOMENTTRACK_AUDIO_FRAGMENT_DURATION,
            'results': results,
        })


class Statistics(APIView):
    """
    Return some statistical information useful for marketing purpose

    Result will follow this format:

    ```json
    {
        "users": {
            "private": Integer (total number of private users),
            "company": Integer (total number of company users),
            "employee": Integer (total number of employee users)
        },
        "companies": Integer (total number of companies),
        "files": {
            "public": Integer (total number of public uploaded files),
            "private": Integer (total number of private uploaded files)
        },
        "processed_minutes": Integer (total number of processed time in minutes),
        "credits": Integer (total number of credits bought)
    }
    ```
    """
    def get(self, request):
        private_users = PrivateUser.objects.filter(user__is_active=True).count()
        companies = Company.objects.count()
        employees = EmployeeUser.objects.filter(user__is_active=True).count()

        public_audio_files = AudioFile.objects.filter(is_public=True)
        private_audio_files = AudioFile.objects.filter(is_public=False)

        processed_time = AudioFile.objects.aggregate(total=Sum('duration')).get('total', timedelta())
        processed_minutes = int(math.ceil(processed_time.total_seconds() / 60.0))

        credits = CreditsPacketPurchase.objects.aggregate(total=Sum('credits_purchased')).get('total', 0)

        return Response({
            'users': {
                'private': private_users,
                'company': companies,
                'employee': employees,
            },
            'companies': companies,
            'files': {
                'public': public_audio_files,
                'private': private_audio_files,
            },
            'processed_minutes': processed_minutes,
            'credits': credits,
        })
