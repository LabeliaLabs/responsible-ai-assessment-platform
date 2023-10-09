from django.db import models


class PlatformText(models.Model):
    homepage_text = models.TextField()

    @classmethod
    def get_or_create(cls):
        """ "
        Get the object if it exists or creates it and return it
        """
        if cls.objects.first():
            return cls.objects.first()
        else:
            created_obj = cls()
            created_obj.save()
            return created_obj
