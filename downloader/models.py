from django.db import models


class DownloadJob(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_FETCHING = 'fetching'
    STATUS_FETCHED = 'fetched'
    STATUS_CONVERTING = 'converting'
    STATUS_DONE = 'done'
    STATUS_ERROR = 'error'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_FETCHING, 'Fetching'),
        (STATUS_FETCHED, 'Fetched'),
        (STATUS_CONVERTING, 'Converting'),
        (STATUS_DONE, 'Done'),
        (STATUS_ERROR, 'Error'),
    ]

    url = models.URLField(max_length=500)
    title = models.CharField(max_length=300, blank=True)
    raw_file = models.CharField(max_length=500, blank=True)
    duration = models.FloatField(default=0.0)
    start_time = models.FloatField(null=True, blank=True)
    end_time = models.FloatField(null=True, blank=True)
    format_type = models.CharField(max_length=10, blank=True)
    output_format = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    output_file = models.CharField(max_length=500, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.url
