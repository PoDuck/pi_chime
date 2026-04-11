from .models import Clip, Playlist, PlaylistClip
from django.conf import settings
import os
import subprocess
import threading

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from .forms import ClipUploadForm
from django.urls import reverse_lazy


def get_clips_for_trigger():
    """Return ordered clip list for the next trigger: active playlist clips, or all clips."""
    active_playlist = Playlist.objects.filter(is_active=True).first()
    if active_playlist:
        playlist_clips = active_playlist.playlist_clips.select_related('clip').order_by('order')
        return [pc.clip for pc in playlist_clips]
    return list(Clip.objects.all().order_by('order'))


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
            'active_playlist': Playlist.objects.filter(is_active=True).first(),
            'page': 'clips',
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
    _last_trigger_time = 0
    COOLDOWN_SECONDS = 3

    def get(self, request):
        import time
        now = time.time()
        if now - TriggerChime._last_trigger_time < TriggerChime.COOLDOWN_SECONDS:
            return JsonResponse({"success": False, "error": "Cooldown active"}, status=200)
        TriggerChime._last_trigger_time = now

        clips = get_clips_for_trigger()

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


class PlaylistListView(View):
    template_name = 'clips/playlist_list.html'

    def get(self, request):
        return render(request, self.template_name, {
            'playlists': Playlist.objects.all(),
            'page': 'playlists',
        })

    def post(self, request):
        name = request.POST.get('name', '').strip()
        if name:
            Playlist.objects.create(name=name)
        return redirect('playlist_list')


class PlaylistDetailView(View):
    template_name = 'clips/playlist_detail.html'

    def get(self, request, pk):
        playlist = get_object_or_404(Playlist, pk=pk)
        playlist_clips = playlist.playlist_clips.select_related('clip').order_by('order')
        clip_ids = {pc.clip_id for pc in playlist_clips}
        available_clips = Clip.objects.exclude(pk__in=clip_ids).order_by('order')
        return render(request, self.template_name, {
            'playlist': playlist,
            'playlist_clips': playlist_clips,
            'available_clips': available_clips,
            'page': 'playlists',
        })

    def post(self, request, pk):
        # AJAX reorder
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            playlist = get_object_or_404(Playlist, pk=pk)
            data = json.loads(request.body)
            for idx, clip_id in enumerate(data):
                PlaylistClip.objects.filter(playlist=playlist, clip_id=clip_id).update(order=idx + 1)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False}, status=400)


class PlaylistRenameView(View):
    def post(self, request, pk):
        playlist = get_object_or_404(Playlist, pk=pk)
        name = request.POST.get('name', '').strip()
        if name:
            playlist.name = name
            playlist.save()
        return redirect('playlist_detail', pk=pk)


class PlaylistActivateView(View):
    def post(self, request, pk):
        playlist = get_object_or_404(Playlist, pk=pk)
        if playlist.is_active:
            playlist.is_active = False
            playlist.save()
        else:
            Playlist.objects.all().update(is_active=False)
            playlist.is_active = True
            playlist.save()
        return redirect('playlist_list')


class PlaylistDeleteView(DeleteView):
    model = Playlist
    template_name = 'clips/playlist_confirm_delete.html'
    success_url = reverse_lazy('playlist_list')


class PlaylistClipAddView(View):
    def post(self, request, pk):
        playlist = get_object_or_404(Playlist, pk=pk)
        clip_id = request.POST.get('clip_id')
        if clip_id:
            clip = get_object_or_404(Clip, pk=clip_id)
            max_order = playlist.playlist_clips.order_by('-order').values_list('order', flat=True).first() or 0
            PlaylistClip.objects.get_or_create(
                playlist=playlist,
                clip=clip,
                defaults={'order': max_order + 1},
            )
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('playlist_detail', pk=pk)


class PlaylistClipRemoveView(View):
    def post(self, request, pk, clip_pk):
        playlist = get_object_or_404(Playlist, pk=pk)
        PlaylistClip.objects.filter(playlist=playlist, clip_id=clip_pk).delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('playlist_detail', pk=pk)
