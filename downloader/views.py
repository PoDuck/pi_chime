import mimetypes
import os
import subprocess
import threading
from pathlib import Path

from django.conf import settings
from django.db import connection
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from .models import DownloadJob

RAW_DIR = os.path.join(settings.MEDIA_ROOT, 'downloads', 'raw')
DOWNLOADS_DIR = os.path.join(settings.MEDIA_ROOT, 'downloads')

AUDIO_CODEC_MAP = {
    'mp3':  ['-codec:a', 'libmp3lame', '-q:a', '2'],
    'm4a':  ['-codec:a', 'aac', '-b:a', '192k'],
    'aac':  ['-codec:a', 'aac', '-b:a', '192k'],
    'flac': ['-codec:a', 'flac'],
    'wav':  ['-codec:a', 'pcm_s16le'],
    'ogg':  ['-codec:a', 'libvorbis', '-q:a', '5'],
    'opus': ['-codec:a', 'libopus', '-b:a', '128k'],
}

VIDEO_CODEC_MAP = {
    'mp4':  ['-codec:v', 'libx264', '-preset', 'fast', '-crf', '23', '-codec:a', 'aac'],
    'webm': ['-codec:v', 'libvpx-vp9', '-crf', '33', '-b:v', '0', '-codec:a', 'libopus'],
    'mkv':  ['-codec:v', 'copy', '-codec:a', 'copy'],
    'avi':  ['-codec:v', 'libx264', '-preset', 'fast', '-crf', '23', '-codec:a', 'libmp3lame'],
    'mov':  ['-codec:v', 'libx264', '-preset', 'fast', '-crf', '23', '-codec:a', 'aac'],
}


def _safe_title(title):
    return ''.join(c for c in title if c.isalnum() or c in ' -_').strip()[:60]


def _fetch_job(job_id):
    """Phase 1: download raw file from YouTube for preview."""
    try:
        job = DownloadJob.objects.get(pk=job_id)
        job.status = DownloadJob.STATUS_FETCHING
        job.save()

        import yt_dlp

        os.makedirs(RAW_DIR, exist_ok=True)

        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            info = ydl.extract_info(job.url, download=False)
            title = info.get('title', 'download')
            duration = float(info.get('duration') or 0)

        job.title = title[:300]
        job.duration = duration
        job.save()

        ydl_opts = {
            # Prefer a pre-merged mp4 (no postprocessing needed).
            # Fall back to merging into mp4 (H.264+AAC is always valid in mp4).
            # Using only the job pk as filename avoids any special-char issues.
            'format': (
                'best[ext=mp4][height<=1080]'
                '/bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]'
                '/bestvideo[height<=1080]+bestaudio'
                '/best'
            ),
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(RAW_DIR, f'{job.pk}.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([job.url])

        raw_files = [f for f in Path(RAW_DIR).glob(f'{job.pk}.*') if not f.name.endswith('.part')]
        if not raw_files:
            raise RuntimeError('yt-dlp produced no output file')

        job.raw_file = os.path.join('downloads', 'raw', raw_files[0].name)
        job.status = DownloadJob.STATUS_FETCHED
        job.save()

    except Exception as exc:
        try:
            job = DownloadJob.objects.get(pk=job_id)
            job.status = DownloadJob.STATUS_ERROR
            job.error_message = str(exc)
            job.save()
        except Exception:
            pass
    finally:
        connection.close()


def _convert_job(job_id):
    """Phase 2: trim and re-encode to requested format."""
    try:
        job = DownloadJob.objects.get(pk=job_id)
        job.status = DownloadJob.STATUS_CONVERTING
        job.save()

        raw_path = os.path.join(settings.MEDIA_ROOT, job.raw_file)
        out_name = f'{job.pk}_{_safe_title(job.title)}.{job.output_format}'
        out_path = os.path.join(DOWNLOADS_DIR, out_name)

        cmd = ['ffmpeg', '-y']
        if job.start_time:
            cmd += ['-ss', str(job.start_time)]
        cmd += ['-i', raw_path]
        if job.end_time:
            # -t duration when -ss is before -i, so player end aligns correctly
            duration = (job.end_time - (job.start_time or 0))
            cmd += ['-t', str(duration)]

        if job.format_type == 'audio':
            cmd += AUDIO_CODEC_MAP.get(job.output_format, ['-codec:a', 'copy'])
            cmd += ['-vn']
        else:
            cmd += VIDEO_CODEC_MAP.get(job.output_format, ['-codec:v', 'copy', '-codec:a', 'copy'])

        cmd.append(out_path)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f'ffmpeg failed:\n{result.stderr[-800:]}')

        job.output_file = os.path.join('downloads', out_name)
        job.status = DownloadJob.STATUS_DONE
        job.save()

    except Exception as exc:
        try:
            job = DownloadJob.objects.get(pk=job_id)
            job.status = DownloadJob.STATUS_ERROR
            job.error_message = str(exc)
            job.save()
        except Exception:
            pass
    finally:
        connection.close()


class DownloaderView(View):
    template_name = 'downloader/index.html'

    def get(self, request):
        return render(request, self.template_name, {
            'jobs': DownloadJob.objects.all()[:20],
            'page': 'downloader',
        })

    def post(self, request):
        url = request.POST.get('url', '').strip()
        if not url:
            return render(request, self.template_name, {
                'error': 'Please enter a URL.',
                'jobs': DownloadJob.objects.all()[:20],
                'page': 'downloader',
            })
        job = DownloadJob.objects.create(url=url)
        threading.Thread(target=_fetch_job, args=(job.pk,), daemon=True).start()
        return redirect('downloader_job', pk=job.pk)


class JobView(View):
    template_name = 'downloader/job.html'

    def get(self, request, pk):
        job = get_object_or_404(DownloadJob, pk=pk)
        return render(request, self.template_name, {'job': job, 'page': 'downloader'})


class JobStatusView(View):
    def get(self, request, pk):
        job = get_object_or_404(DownloadJob, pk=pk)
        return JsonResponse({
            'status': job.status,
            'title': job.title,
            'duration': job.duration,
            'error': job.error_message,
        })


class ConvertView(View):
    def post(self, request, pk):
        job = get_object_or_404(DownloadJob, pk=pk)
        if not job.raw_file:
            return JsonResponse({'error': 'Raw file not available'}, status=400)

        try:
            start = float(request.POST.get('start_time') or 0) or None
            end = float(request.POST.get('end_time') or 0) or None
        except ValueError:
            start, end = None, None

        job.start_time = start
        job.end_time = end
        job.format_type = request.POST.get('format_type', 'audio')
        job.output_format = request.POST.get('output_format', 'mp3')
        job.output_file = ''
        job.error_message = ''
        job.save()

        threading.Thread(target=_convert_job, args=(job.pk,), daemon=True).start()
        return redirect('downloader_job', pk=job.pk)


class RawFileView(View):
    def get(self, request, pk):
        job = get_object_or_404(DownloadJob, pk=pk)
        if not job.raw_file:
            raise Http404
        file_path = os.path.join(settings.MEDIA_ROOT, job.raw_file)
        if not os.path.exists(file_path):
            raise Http404
        content_type, _ = mimetypes.guess_type(file_path)
        return FileResponse(open(file_path, 'rb'), content_type=content_type or 'application/octet-stream')


class DownloadFileView(View):
    def get(self, request, pk):
        job = get_object_or_404(DownloadJob, pk=pk)
        if job.status != DownloadJob.STATUS_DONE or not job.output_file:
            raise Http404
        file_path = os.path.join(settings.MEDIA_ROOT, job.output_file)
        if not os.path.exists(file_path):
            raise Http404
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(file_path),
        )
