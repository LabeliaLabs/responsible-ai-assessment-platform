"""dev_platform URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog
from home.admin import admin_dashboard
from home.sitemaps import StaticViewsSitemap

sitemaps = {"static": StaticViewsSitemap}

urlpatterns = (
    i18n_patterns(
        path(
            "sitemap.xml",
            sitemap,
            {"sitemaps": sitemaps},
            name="django.contrib.sitemaps.views.sitemap",
        ),
        path("", include("home.urls")),
        path("i18n/", include("django.conf.urls.i18n")),
        path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
        path("assessment/", include("assessment.urls")),
        path("admin/", admin.site.urls),
        path("admin-monitoring/", admin_dashboard.urls),
        prefix_default_language=True,
    )
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
)

handler404 = "assessment.views.utils.error_handler.error_404_view_handler"
handler500 = "assessment.views.utils.error_handler.error_500_view_handler"
handler403 = "assessment.views.utils.error_handler.error_403_view_handler"
handler400 = "assessment.views.utils.error_handler.error_400_view_handler"
