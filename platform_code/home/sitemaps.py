from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewsSitemap(Sitemap):
    def items(self):
        return [
            "home:homepage",
        ]

    def location(self, item):
        return reverse(item)
