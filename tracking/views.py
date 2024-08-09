from django.shortcuts import render
from django.views import View
from .models import Track
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator


class TrackingView(View):
    template_name = "tracking/tracking_view.html"

    # Ensure we have a CSRF cooke set
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        ctx = {
            'object_list': Track.objects.all(),
            'page': 'home',
        }
        return render(self.request, self.template_name, context=ctx)
