from django.db import models


class PlatformManagement(models.Model):
    """
    This class aims to furnish the possibility to admin users to realize actions on the platform globally.
    The platform_update fields manage the fact that during the release on production, the users may lose the unsaved
    content so a banner is displayed.
    The activate_multi_languages field manages the fact that we may want to do not activate the English version of the
    platform (because English assessment is not imported).
    """

    # Manage delivery and add a banner on the site
    platform_update = models.BooleanField(default=False)
    delivery_text_en = models.TextField(max_length=1000, default="Platform update ongoing")
    delivery_text_fr = models.TextField(
        max_length=1000, default="Mise à jour de la plateforme en cours"
    )
    # Manage the language
    activate_multi_languages = models.BooleanField(
        default=False,
        help_text="This should not be activated if an "
        "assessment does not exist both in French "
        "and English",
    )
    labelling_threshold = models.FloatField(default=45)

    primary_color = models.CharField(
        max_length=7, default="5550FF"
    )  # Store background color in hexadecimal format (e.g., #RRGGBB)
    primary_color_light = models.CharField(max_length=7, default="726EF5")
    secondary_color = models.CharField(max_length=7, default="FCE180")
    secondary_color_light = models.CharField(max_length=7, default="FAE8A7")
    tertiary_color = models.CharField(max_length=7, default="91D3FF")
    tertiary_color_light = models.CharField(max_length=7, default="B8DFFA")
    text_color = models.CharField(max_length=7, default="4D566B")
    text_color_light = models.CharField(max_length=7, default="70788B")
    app_logo = models.ImageField(upload_to="app_logo", null=True, blank=True)
    font_family = models.CharField(max_length=100, default="Ubuntu")

    def __str__(self):
        return "Platform management"

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

    @classmethod
    def get_labelling_threshold(cls):
        """
        Get the labelling threshold of the platform management object
        """
        return cls.get_or_create().labelling_threshold

    def set_labelling_threshold(self, value):
        """
        Set the labelling_threshold field if value is a float
        """
        if value and (isinstance(value, float) or isinstance(value, int)):
            self.labelling_threshold = value
            self.save()
