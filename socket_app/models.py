from django.db import models

# Create your models here.

class BaseModel(models.Model):
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    is_delete = models.BooleanField(default=False)

    class Meta:
        abstract = True  # This makes it a base model (not stored in DB)


class SocketSettings(BaseModel):
    frequency = models.IntegerField(help_text="Socket connection frequency in minutes")

    def __str__(self):
        return f"{self.frequency} min"

    def save(self, *args, **kwargs):
        self.pk = 1  # Always use the same primary key (singleton)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Prevent deletion of the settings

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1, defaults={'frequency': 5})  # Default to 5 minutes
        return obj

class LocationData(BaseModel):
    user_id = models.CharField(help_text="User ID from Frappe")
    socket_id = models.CharField(help_text="Socket ID from Socket.IO",blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField() # auto_now_add=True
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return f"User : {self.user_id} - {self.latitude}, {self.longitude} at {self.date} {self.time}"




