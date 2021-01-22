from django.contrib import admin
from .models import APIError

@admin.register(APIError)
class AdminAPIError(admin.ModelAdmin):
    pass