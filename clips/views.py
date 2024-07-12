from django.views.generic import ListView
from .models import Clip
from django.conf import settings
import os
import vlc
from time import sleep

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
        }
        return render(self.request, self.template_name, context=ctx)

    # Process POST AJAX Request
    def post(self, request):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                # Parse the JSON payload
                data = json.loads(request.body)[0]
                # Loop over our list order. The id equals the question id. Update the order and save
                for idx, row in enumerate(data):
                    pq = Clip.objects.get(pk=row['id'])
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
                media_player.set_media(media)
                media_player.play()
                sleep(3)
                media_player.stop()

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


class ClipUpdateView(UpdateView):
    model = Clip
    form_class = ClipUploadForm
    template_name = 'clips/update.html'
    success_url = reverse_lazy('clip_list')


class ClipDeleteView(DeleteView):
    model = Clip
    template_name = 'clips/delete.html'
    success_url = reverse_lazy('clip_list')
