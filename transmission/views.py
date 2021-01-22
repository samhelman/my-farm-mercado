from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .models import APIError

class APIErrorView(TemplateView):
    template_name = "transmission/api-error.html"

    def get(self, request):
        if request.user.is_superuser:
            context = {
                'api_errors': []
            }
            errors = APIError.objects.order_by('-log_time').all()
            for error in errors:
                error_object = {
                    'endpoint': error.endpoint,
                    'error': error.error,
                    'log_time': error.log_time
                }
                context['api_errors'].append(error_object)
            return render(request, self.template_name, context=context)
        return redirect('home-index')