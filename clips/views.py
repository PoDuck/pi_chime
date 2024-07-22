from .models import Clip
from django.conf import settings
import os
import vlc

import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from .forms import ClipUploadForm
from django.urls import reverse_lazy


class ClipsList(View):
    template_name = "clips/clip_list.html"

    # Ensure we have a CSRF cooke set
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        ctx = {
            'object_list': Clip.objects.all().order_by('order'),
            'page': 'home',
        }
        return render(self.request, self.template_name, context=ctx)

    # Process POST AJAX Request
    def post(self, request):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                # Parse the JSON payload
                data = json.loads(request.body)
                # Loop over our list order. The id equals the question id. Update the order and save
                for idx, row in enumerate(data):
                    pq = Clip.objects.get(pk=row)
                    pq.order = idx + 1
                    pq.save()

            except KeyError:
                HttpResponse(status="500", content="Malformed Data!")

            return JsonResponse({"success": True}, status=200)
        else:
            return JsonResponse({"success": False}, status=400)

    def put(self, request, pk):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                clip = Clip.objects.get(pk=pk)
                media_player = vlc.MediaPlayer()
                media = vlc.Media(os.path.join(settings.MEDIA_ROOT, str(clip.file)))
                media_player.audio_set_volume(clip.max_volume)
                if clip.end_time != clip.start_time:
                    if clip.end_time > clip.start_time:
                        media.add_option('start-time=' + str(clip.start_time))
                        media.add_option('run-time=' + str(clip.end_time - clip.start_time))
                media_player.set_media(media)
                media_player.play()
                # sleep(3)
                # media_player.stop()

            except KeyError:
                HttpResponse(status="500", content="Malformed Data!")
            return JsonResponse({"success": True}, status=200)
        else:
            return JsonResponse({"success": False}, status=400)


class ClipUploadView(CreateView):
    model = Clip
    form_class = ClipUploadForm
    template_name = 'clips/upload.html'
    success_url = reverse_lazy('index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page'] = 'create'
        return context


class ClipUpdateView(UpdateView):
    model = Clip
    form_class = ClipUploadForm
    template_name = 'clips/update.html'
    success_url = reverse_lazy('clip_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page'] = 'update'
        return context

class ClipDeleteView(DeleteView):
    model = Clip
    template_name = 'clips/delete.html'
    success_url = reverse_lazy('clip_list')


class TriggerChime(View):
    def get(self, request):
        play_next = False
        clips = Clip.objects.all().order_by('order')
        last_played = Clip.objects.filter(last_played=True)
        if list(clips)[-1].last_played or not last_played:
            play_next = True
            if list(clips)[-1].last_played:
                list(clips)[-1].last_played = False
        for clip in clips:
            if clip.last_played:
                play_next = True
                clip.last_played = False
                clip.save()
            elif play_next:
                media_player = vlc.MediaPlayer()
                media = vlc.Media(os.path.join(settings.MEDIA_ROOT, str(clip.file)))
                media_player.set_media(media)
                media_player.set_volume(clip.volume)
                if clip.end_time != clip.start_time:
                    if clip.end_time > clip.start_time:
                        media_player.add_option('start-time=' + str(clip.start_time))
                        media_player.add_option('run-time=' + str(clip.end_time - clip.start_time))
                media_player.play()
                # sleep(3)
                # media_player.stop()
                clip.last_played = True
                break
        for clip in clips:
            clip.save()
        return JsonResponse({"success": True}, status=200)
