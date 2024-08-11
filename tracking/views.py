from django.views import View
from django.views.generic.base import TemplateView
from django.http import JsonResponse
from django.conf import settings
from .models import Track
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from collections import Counter
import pytz


tz = pytz.timezone(settings.LOCAL_TIMEZONE)


class TrackingView(TemplateView):
    template_name = "tracking/tracking_view.html"


class TrackingDataView(View):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        data = Track.objects.all()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        days_of_week = []
        for track in data:
            created_at_tz = track.created.astimezone(tz)
            # Get the day of the week (0=Monday, 6=Sunday)
            day_of_week = created_at_tz.weekday()
            days_of_week.append(day_of_week)
        day_counts = Counter(days_of_week)
        percentages = [0 for _ in range(7)]
        for day_number, count in sorted(day_counts.items()):
            percentages[day_number] = round(count / len(days_of_week), 2) * 100

        ctx = {
            'labels': day_names,
            'data': percentages,
        }

        return JsonResponse(ctx)
