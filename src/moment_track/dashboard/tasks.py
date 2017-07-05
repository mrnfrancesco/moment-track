from __future__ import absolute_import, unicode_literals

import speech_recognition as sr

from celery import shared_task, group
from datetime import timedelta

from celery.exceptions import MaxRetriesExceededError
from django.db import transaction

from dashboard.models import AudioFile, Transcription
from dashboard.shortcuts import calculate_credits_usage
from moment_track import settings


@shared_task(bind=True, ignore_result=True)
def transcript_audio_fragment(self, audio_id, duration, offset):
    """Celery task to transcript the specified file fragment and
    save the results to the database as Transcription model instances.
    """
    try:
        audio_model = AudioFile.objects.get(id=audio_id)
        language = str(audio_model.language_spoken)

        recognizer = sr.Recognizer()
        recognizer.operation_timeout = 60

        # extract "duration" seconds of audio fragment from "offset"
        with sr.AudioFile(str(audio_model.file.path)) as source:
            audio_data = recognizer.record(source, duration, offset)

        transcriptions = []
        try:
            # try to transcript audio fragment using Google Speech Recognition API
            transcriptions = recognizer.recognize_google(
                key=settings.GOOGLE_SPEECH_RECOGNITION_API_KEY,
                audio_data=audio_data,
                language=language,
                show_all=True  # get all the transcriptions alternatives, not just the more confident
            )
            if isinstance(transcriptions, dict):
                transcriptions = transcriptions.get('alternative', [])
            else:
                transcriptions = []

        except sr.UnknownValueError:
            if settings.GOOGLE_CLOUD_SPEECH_CREDENTIALS is not None:
                try:
                    transcriptions = recognizer.recognize_google_cloud(
                        credentials_json=settings.GOOGLE_CLOUD_SPEECH_CREDENTIALS,
                        audio_data=audio_data,
                        language=language,
                        show_all=True  # get all the transcriptions alternatives, not just the best confident
                    ).get('results', [])
                except sr.UnknownValueError:
                    pass

        time_start = timedelta(seconds=offset)

        # Remove low confidence level transcriptions
        transcriptions = [
            transcription
            for transcription in transcriptions
            if transcription.get('confidence', .0) > settings.MOMENTTRACK_MIN_TRANSCRIPTION_CONFIDENCE
        ]

        if len(transcriptions) > 0:
            # create list of transcriptions model to avoid lots of single insert instead of a single bulk insert
            # (used for performance improvements)
            Transcription.objects.bulk_create([
                Transcription(
                    file=audio_model,
                    offset=time_start,
                    confidence=transcription.get('confidence'),
                    text=transcription.get('transcript')
                )
                for transcription in transcriptions
            ])
        else:
            # Save blank transcription to calculate properly transcription coverage for audio file
            Transcription(file=audio_model, offset=time_start, confidence=.5, text='').save()
    except Exception as exc:
        if type(exc) != MaxRetriesExceededError:
            # in case of any error retry after 180 sec (max 3 times)
            self.retry(exc=exc)


@shared_task(bind=True)
def process_audio_file(self, audio_id):
    """Celery task to parallelize the processing of the
    entire audio file fragment by fragment.
    """
    try:
        audio = AudioFile.objects.get(id=audio_id)

        with transaction.atomic():
            # remove credits needed for audio processing
            calculate_credits_usage(audio)

            # start from 00:00:00.00 to process audio
            start_time = timedelta()

            # prepare parallel tasks to process audio fragments
            tasks = []
            for i in range(0, audio.total_fragments):
                tasks.append(
                    transcript_audio_fragment.s(
                        audio_id=audio_id,
                        duration=settings.MOMENTTRACK_AUDIO_FRAGMENT_DURATION.total_seconds(),
                        offset=start_time.total_seconds()
                    )
                )

                # Update start time to fetch next fragment
                start_time += settings.MOMENTTRACK_AUDIO_FRAGMENT_DURATION

            # run processing tasks in parallel
            group(*tasks)()
    except (ValueError, AudioFile.DoesNotExist) as exc:
        self.retry(exc=exc)
