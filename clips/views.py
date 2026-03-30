from .models import Clip
from django.conf import settings
import os
import subprocess
import threading

import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from .forms import ClipUploadForm
from django.urls import reverse_lazy


def play_clip(clip):
    """Play audio clip using mpg123 via sudo in background thread."""
    file_path = os.path.join(settings.MEDIA_ROOT, str(clip.file))

    def _play():
        try:
            subprocess.run(['sudo', 'killall', 'mpg123'], stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'killall', 'ffmpeg'], stderr=subprocess.DEVNULL)
            use_trim = clip.start_time > 0 or clip.end_time > 0
            if use_trim:
                ffmpeg_cmd = ['ffmpeg', '-ss', str(clip.start_time)]
                if clip.end_time > 0:
                    ffmpeg_cmd += ['-to', str(clip.end_time)]
                ffmpeg_cmd += ['-i', file_path, '-f', 'mp3', '-loglevel', 'quiet', '-']
                ffmpeg = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
                subprocess.run(['sudo', 'mpg123', '-q', '-a', 'hw:0,0', '-'], stdin=ffmpeg.stdout, timeout=60)
                ffmpeg.stdout.close()
            else:
                subprocess.run(['sudo', 'mpg123', '-q', '-a', 'hw:0,0', file_path], timeout=60)
        except Exception as e:
            print(f'Error playing clip: {e}')

    thread = threading.Thread(target=_play, daemon=True)
    thread.start()


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
                play_clip(clip)

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


class LastPlayedView(View):
    def get(self, request):
        clip = Clip.objects.filter(last_played=True).first()
        return JsonResponse({"last_played_id": clip.pk if clip else None})


class TriggerChime(View):
    def get(self, request):
        clips = list(Clip.objects.all().order_by('order'))
        
        # Handle empty clip list
        if not clips:
            return JsonResponse({"success": False, "error": "No clips available"}, status=200)
        
        # Find the next clip to play
        last_played_idx = -1
        for idx, clip in enumerate(clips):
            if clip.last_played:
                last_played_idx = idx
                break
        
        # Calculate next clip index (cycle back to 0 if at end)
        next_idx = (last_played_idx + 1) % len(clips)
        
        # Update last_played flags
        if last_played_idx >= 0:
            clips[last_played_idx].last_played = False
            clips[last_played_idx].save()
        
        clips[next_idx].last_played = True
        clips[next_idx].save()
        
        # Play the clip
        play_clip(clips[next_idx])
        
        return JsonResponse({"success": True}, status=200)
