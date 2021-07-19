from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewsSitemap(Sitemap):

    def items(self):
        return [
            'home:homepage',
            'home:signup',
            'home:login',
            'home:legal-notices',
            'home:release-notes',
            'home:faq',
        ]

    def location(self, item):
        return reverse(item)
