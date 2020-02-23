from django.db import models
from django.core.management.utils import get_random_secret_key

class Secret(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    key = models.CharField(max_length=50, default=get_random_secret_key)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.key
