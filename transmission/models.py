from django.db import models

class APIError(models.Model):
    error = models.TextField()
    endpoint = models.CharField(max_length=150)
    log_time = models.DateTimeField()

    def __str__(self):
        return f"{self.id} - {self.error}"