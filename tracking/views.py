from django.views import View
from django.views.generic.base import TemplateView
from django.http import JsonResponse
from django.conf import settings
from django.utils.dateparse import parse_datetime
from .models import Track
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from collections import Counter
import pytz
from datetime import datetime


tz = pytz.timezone(settings.LOCAL_TIMEZONE)


class DayTrackingView(TemplateView):
    template_name = "tracking/tracking_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dates = Track.objects.all().order_by('created')
        context['start_date'] = dates.first().created.date()
        context['end_date'] = dates.last().created.date()
        context['min_date'] = dates.first().created.date()
        context['max_date'] = dates.last().created.date()
        context['page'] = 'day-tracking'
        return context


class HourTrackingView(TemplateView):
    template_name = "tracking/hour_tracking_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dates = Track.objects.all().order_by('created')
        context['min_date'] = dates.first().created.date()
        context['max_date'] = dates.last().created.date()
        context['page'] = 'day-tracking'
        return context


class HourTrackingViewAllDays(HourTrackingView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_days'] = True
        return context


class HourTrackingDataView(View):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, pk, start_date, end_date, all_days):
        start = parse_datetime(start_date)
        tz_start = datetime(start.year, start.month, start.day, tzinfo=tz)
        end = parse_datetime(end_date)
        tz_end = datetime(end.year, end.month, end.day + 1, tzinfo=tz)
        data = Track.objects.all().filter(created__date__range=(tz_start, tz_end))
        hours_of_day = []
        for track in data:
            created_at_tz = track.created.astimezone(tz)
            if created_at_tz.weekday() == int(pk) or all_days == 'true':
                hour_of_day = created_at_tz.hour
                hours_of_day.append(hour_of_day)
        hour_counts = Counter(hours_of_day)
        percentages = [0 for _ in range(24)]
        for hour, count in sorted(hour_counts.items()):
            percentages[hour] = round(count / len(hours_of_day), 2) * 100
        hour_names = []
        for i in range(24):
            hour_names.append(f'{i}:00')
        ctx = {
            'labels': hour_names,
            'data': percentages,
        }

        return JsonResponse(ctx)


class DayTrackingDataView(View):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request, start_date, end_date):
        start = parse_datetime(start_date)
        tz_start = datetime(start.year, start.month, start.day, tzinfo=tz)
        end = parse_datetime(end_date)
        tz_end = datetime(end.year, end.month, end.day + 1, tzinfo=tz)
        data = Track.objects.all().filter(created__date__range=(tz_start, tz_end))
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
