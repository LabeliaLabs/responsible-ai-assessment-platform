from django.urls import path, re_path, include

from .views import (
    EvaluationView,
    EvaluationCreationView,
    DeleteEvaluation,
    SummaryView,
    ResultsView,
    leave_organisation,
    upgradeView,
    SectionView,
    ResultsPDFView,
    labellingView,
    labellingAgainView,
    labellingJustification,
    labellingEnd,
    duplicateView
)


app_name = "assessment"

urlpatterns = [
    re_path(
        r"^organisation/(?P<orga_id>[0-9]{1,})/",
        include(
            [
                path(
                    "creation-evaluation/",
                    EvaluationCreationView.as_view(),
                    name="creation-evaluation",
                ),
                path("", SummaryView.as_view(), name="orga-summary"),
                path("leave-organisation", leave_organisation, name="leave-organisation"),
                path(
                    "<slug:slug>/<int:pk>/",
                    include(
                        [
                            path("", EvaluationView.as_view(), name="evaluation"),
                            path(
                                "delete/",
                                DeleteEvaluation.as_view(),
                                name="delete-evaluation",
                            ),
                            path("upgrade/", upgradeView, name="upgrade"),
                            path("duplicate/", duplicateView, name="duplicate"),
                            path("labelling/", labellingView, name="labelling"),
                            path("labelling-again/", labellingAgainView, name="submit-labelling-again"),
                            path("labelling/justification", labellingJustification, name="labelling-justification"),
                            re_path(r"labelling/(?P<status>[a-z]{1,15})", labellingEnd, name="end-labelling"),
                            re_path(
                                r"^section/(?P<id>[0-9]{1,})/(?P<name>[-\w\W]+)/(?P<page>\d+)$",
                                SectionView.as_view(),
                                name="section",
                            ),
                            path(
                                "results/", include([
                                    path("", ResultsView.as_view(), name="results"),
                                    path("pdf/", ResultsPDFView.as_view(), name="resultsPDF")
                                ])

                            ),
                        ]
                    ),
                ),
            ]
        ),
    )
]
