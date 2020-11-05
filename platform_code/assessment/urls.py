from django.urls import path, re_path, include

from . import views


app_name = "assessment"

urlpatterns = [
    re_path(
        r"^organisation/(?P<orga_id>[0-9]{1,})/",
        include(
            [
                path(
                    "creation-evaluation/",
                    views.EvaluationCreationView.as_view(),
                    name="creation-evaluation",
                ),
                path("", views.SummaryView.as_view(), name="orga-summary"),
                path("leave-organisation", views.leave_organisation, name="leave-organisation"),
                path(
                    "<slug:slug>/<int:pk>/",
                    include(
                        [
                            path("", views.EvaluationView.as_view(), name="evaluation"),
                            path(
                                "delete/",
                                views.DeleteEvaluation.as_view(),
                                name="delete-evaluation",
                            ),
                            path("upgrade/", views.upgradeView, name="upgrade"),
                            re_path(
                                r"^section/(?P<id>[0-9]{1,})/(?P<name>[-\w\W]+)/(?P<page>\d+)$",
                                views.SectionView.as_view(),
                                name="section",
                            ),
                            path(
                                "results/", views.ResultsView.as_view(), name="results"
                            ),
                        ]
                    ),
                ),
            ]
        ),
    )
]
