import calendar
import json
from datetime import datetime

from assessment.models import Assessment, Evaluation, Labelling
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from home.forms import (
    DashboardEvaluationsStatsTabFilterForm,
    DashboardOrganisationsStatsTabFilterForm,
    DashboardUsersStatsTabFilterForm,
    LabellingStatusForm,
)
from home.models import Organisation, PlatformManagement, User


class DashboardView(TemplateView):
    """
    This class defines the admin dashboard page which is composed of several subpages (stats, labelling).
    It is accessible only for admin users.
    """

    template_name = "home/dashboard/dashboard-admin.html"

    users_form = DashboardUsersStatsTabFilterForm
    organisations_form = DashboardOrganisationsStatsTabFilterForm
    evaluations_form = DashboardEvaluationsStatsTabFilterForm

    context = {}  # context holder for the GET method
    dashboard_update = {}  # context holder for the POST method

    users_filters = {}
    organisations_filters = {}
    evaluations_filters = {}

    def get(self, request, *args, **kwargs):
        """
        GET which manages Filters Form and graphs initialisation when the dashboard page loads
        for the first time
        """
        if not request.user.is_staff:
            return redirect("home:homepage")

        self.context["tab"] = kwargs.get("tab", "stats")

        # initialize the forms and pass them as context
        self.context["users_filters_form"] = self.users_form
        self.context["organisations_filters_form"] = self.organisations_form
        self.context["evaluations_filters_form"] = self.evaluations_form

        # clear filters dictionaries
        self.users_filters.clear()
        self.organisations_filters.clear()
        self.evaluations_filters.clear()

        # initialize the stats and graphs for each dashboard tab
        # users
        users_stats = self.get_users_stats()
        months_list = [month for month, _ in users_stats["one_year_users_count"].items()]
        users_count = [count for _, count in users_stats["one_year_users_count"].items()]

        # organisations
        orgas_stats = self.get_number_organisations()
        sectors_list = [sector for sector, _ in orgas_stats["nb_orgas_per_sector"].items()]
        sizes_list = [size for size, _ in orgas_stats["nb_orgas_per_size"].items()]
        orgas_count_per_sector = [
            orgas_count for _, orgas_count in orgas_stats["nb_orgas_per_sector"].items()
        ]
        orgas_count_per_size = [
            orgas_count for _, orgas_count in orgas_stats["nb_orgas_per_size"].items()
        ]

        # evaluations
        evals_stats = self.get_evaluations_stats()
        versions_list = [
            version_number for version_number, _ in evals_stats["versions_stats"].items()
        ]
        evals_count_per_version = [
            nb_evals for _, nb_evals in evals_stats["versions_stats"].items()
        ]

        # pass the stats as context
        # users
        self.context["nb_users"] = users_stats["nb_users"]
        self.context["users_count_per_month"] = zip(months_list, users_count)
        self.context["min_date"] = users_stats["min_date"]

        # organisations
        self.context["nb_orgas"] = orgas_stats["nb_orgas"]
        self.context["orgas_count_per_sector"] = zip(sectors_list, orgas_count_per_sector)
        self.context["orgas_count_per_size"] = zip(sizes_list, orgas_count_per_size)
        self.context["creation_date"] = "01-01-2020"

        # evaluations
        self.context["nb_evals"] = evals_stats["total_nb_evals"]
        self.context["nb_completed_evals"] = evals_stats["nb_evaluations_completed"]
        self.context["nb_in_progress_evals"] = evals_stats["nb_evaluations_in_progress"]
        self.context["evals_count_per_version"] = zip(versions_list, evals_count_per_version)
        self.context["eval_creation_date"] = evals_stats["eval_creation_date"]

        # Manage the labellings
        self.context["labellings"] = [labelling for labelling in Labelling.objects.all()]
        self.context["labelling_threshold"] = PlatformManagement.get_labelling_threshold()
        self.context["labelling_status_form"] = LabellingStatusForm()

        return self.render_to_response(self.context)

    def post(self, request, *args, **kwargs):
        """
        POST which manages filters requests
        """
        if not request.user.is_staff:
            return redirect("home:homepage")

        # clear previous dashboard updates
        self.dashboard_update.clear()

        if request.method == "POST" and request.is_ajax:
            if "Inscription_date" in request.POST:
                self.update_stats_and_graphs(request, which_form=0)

            elif "creation_date" in request.POST:
                self.update_stats_and_graphs(request, which_form=1)

            elif "date" in request.POST:
                self.update_stats_and_graphs(request, which_form=2)
            else:
                self.dashboard_update["success"] = False
                self.dashboard_update["message"] = _(
                    "An error has occurred, please check your input"
                )

            return HttpResponse(
                json.dumps(self.dashboard_update), content_type="application/json"
            )

        else:
            return self.render_to_response(self.context)

    def update_stats_and_graphs(self, request, which_form):
        """
        Receive the values submitted through the filters form from one of the
        the three tabs, then calls stats and graphs functions
        """
        # handle users filter form
        if which_form == 0:
            form = DashboardUsersStatsTabFilterForm(request.POST)
            self.dashboard_update["which_tab"] = which_form
            if form.is_valid():
                self.users_filters["Inscription_date"] = form.cleaned_data.get(
                    "Inscription_date"
                ).strftime("%Y-%m-%d " "%H:%M:%S")
                users_stats = self.get_users_stats()

                self.dashboard_update["nb_users"] = users_stats["nb_users"]
                self.dashboard_update["months"] = [
                    month for month, nb_users in users_stats["one_year_users_count"].items()
                ]
                self.dashboard_update["users_count"] = [
                    nb_users for month, nb_users in users_stats["one_year_users_count"].items()
                ]
                self.dashboard_update["min_date"] = users_stats["min_date"]
                self.dashboard_update["success"] = True

            else:
                self.dashboard_update["success"] = False
                self.dashboard_update["message"] = _(
                    "An error has occurred, please check your input"
                )

        # handle organisations filter form
        elif which_form == 1:
            form = DashboardOrganisationsStatsTabFilterForm(request.POST)
            self.dashboard_update["which_tab"] = which_form
            if form.is_valid():
                self.organisations_filters["creation_date"] = form.cleaned_data.get(
                    "creation_date"
                ).strftime("%Y-%m-%d " "%H:%M:%S")

                # get the stats and graphs updates
                orgas_stats = self.get_number_organisations()

                self.dashboard_update["nb_orgas"] = orgas_stats["nb_orgas"]
                self.dashboard_update["sectors_list"] = [
                    str(sector)
                    for sector, nb_orgas in orgas_stats["nb_orgas_per_sector"].items()
                ]
                self.dashboard_update["sizes_list"] = [
                    str(size) for size, nb_orgas in orgas_stats["nb_orgas_per_size"].items()
                ]
                self.dashboard_update["orgas_count_per_sector"] = [
                    nb_orgas for sector, nb_orgas in orgas_stats["nb_orgas_per_sector"].items()
                ]
                self.dashboard_update["orgas_count_per_size"] = [
                    nb_orgas for size, nb_orgas in orgas_stats["nb_orgas_per_size"].items()
                ]
                self.dashboard_update["creation_date"] = form.cleaned_data.get(
                    "creation_date"
                ).strftime("%d-%m-%Y")
                self.dashboard_update["success"] = True

            else:
                self.dashboard_update["success"] = False
                self.dashboard_update["message"] = _(
                    "An error has occurred, please check your input"
                )

        # handle evaluations filter form
        elif which_form == 2:
            form = DashboardEvaluationsStatsTabFilterForm(request.POST)
            self.dashboard_update["which_tab"] = which_form
            if form.is_valid():
                self.evaluations_filters["date"] = form.cleaned_data.get("date").strftime(
                    "%Y-%m-%d " "%H:%M:%S"
                )
                self.evaluations_filters["date_raw"] = form.cleaned_data.get("date")
                self.evaluations_filters["sectors"] = form.cleaned_data.get("sectors")
                self.evaluations_filters["sizes"] = form.cleaned_data.get("sizes")

                evals_stats = self.get_evaluations_stats()
                self.dashboard_update["total_nb_evals"] = evals_stats["total_nb_evals"]
                self.dashboard_update["versions_list"] = [
                    version_number
                    for version_number, nb_evals in evals_stats["versions_stats"].items()
                ]

                self.dashboard_update["nb_evals_per_version"] = [
                    nb_evals for version, nb_evals in evals_stats["versions_stats"].items()
                ]
                self.dashboard_update["nb_completed_evals"] = evals_stats[
                    "nb_evaluations_completed"
                ]
                self.dashboard_update["nb_in_progress_evals"] = evals_stats[
                    "nb_evaluations_in_progress"
                ]
                self.dashboard_update["eval_creation_date"] = evals_stats["eval_creation_date"]
                self.dashboard_update["success"] = True
            else:
                self.dashboard_update["success"] = False
                self.dashboard_update["message"] = _(
                    "An error has occurred, please check your input"
                )

        else:
            self.dashboard_update["success"] = False
            self.dashboard_update["message"] = _(
                "An error has occurred, no relevant tabs were selected"
            )

    def get_number_organisations(self):
        """
        - Return the number of organisations based on the filters
        """
        orgas_stats = {"nb_orgas_per_sector": {}, "nb_orgas_per_size": {}}

        if not self.organisations_filters:
            # no filters to apply, return the total number of organisations
            orgas_stats["nb_orgas"] = Organisation.objects.all().count()

            # number of organisations per sector
            for sector_tuple in Organisation.SECTOR:
                orgas_stats["nb_orgas_per_sector"][
                    sector_tuple[1]
                ] = Organisation.objects.filter(sector=sector_tuple[0]).count()

            # number of organisations per size
            for size_tuple in Organisation.SIZE:
                orgas_stats["nb_orgas_per_size"][size_tuple[1]] = Organisation.objects.filter(
                    size=size_tuple[1]
                ).count()

        else:
            # apply filters here
            # organisation creation date
            orgas_stats["nb_orgas"] = Organisation.objects.filter(
                created_at__gte=self.organisations_filters["creation_date"]
            ).count()

            # number of organisations per sector
            for sector_tuple in Organisation.SECTOR:
                orgas_stats["nb_orgas_per_sector"][
                    sector_tuple[1]
                ] = Organisation.objects.filter(
                    sector=sector_tuple[0],
                    created_at__gte=self.organisations_filters["creation_date"],
                ).count()

            # number of organisations per size
            for size_tuple in Organisation.SIZE:
                orgas_stats["nb_orgas_per_size"][size_tuple[1]] = Organisation.objects.filter(
                    size=size_tuple[1],
                    created_at__gte=self.organisations_filters["creation_date"],
                ).count()

        return orgas_stats

    def get_users_stats(self):
        """
        Return the number of users based on the filters and call corresponding graph functions
        """
        users_stats = {"one_year_users_count": {}}

        if not self.users_filters:
            # no filters to apply, return the total number of users
            users_stats["nb_users"] = User.object.all().count()

            min_date = datetime(2020, 1, 1)
            users_stats["min_date"] = min_date.strftime("%d-%b-%Y")
            for i in range(12):
                date_to_filter_by = take_n_month_steps(min_date, i)
                users_stats["one_year_users_count"][
                    date_to_filter_by.strftime("%B-%Y")
                ] = User.object.filter(created_at__lte=date_to_filter_by).count()

        else:
            # apply filter
            users_stats["nb_users"] = User.object.filter(
                created_at__gte=self.users_filters["Inscription_date"]
            ).count()

            submitted_date = datetime.strptime(
                self.users_filters["Inscription_date"], "%Y-%m-%d %H:%M:%S"
            )
            users_stats["min_date"] = submitted_date.strftime("%d-%b-%Y")
            submitted_date_end_month = datetime(
                int(submitted_date.year),
                int(submitted_date.month),
                int(calendar.monthrange(submitted_date.year, submitted_date.month)[1]),
                23,
                59,
                59,
            )

            for i in range(12):
                date_to_filter_by = take_n_month_steps(submitted_date_end_month, i)
                users_stats["one_year_users_count"][
                    date_to_filter_by.strftime("%B-%Y")
                ] = User.object.filter(created_at__lte=date_to_filter_by).count()

        return users_stats

    def get_evaluations_stats(self):
        """
        Return the number of evaluations based on the filters(date,sector,size)
        """
        evals_stats = {"versions_stats": {}}
        versions = Assessment.objects.values("version")

        if not self.evaluations_filters:
            # no filters to apply, return the total number of evaluations
            # number of evaluations per status
            evals_stats["nb_evaluations_completed"] = Evaluation.objects.filter(
                is_finished=True
            ).count()
            evals_stats["nb_evaluations_in_progress"] = Evaluation.objects.filter(
                is_finished=False
            ).count()

            # number of evaluations per version
            for version in versions:
                evals_stats["versions_stats"][version["version"]] = Evaluation.objects.filter(
                    assessment=Assessment.objects.get(version=version["version"])
                ).count()
            evals_stats["eval_creation_date"] = "01-01-2020"

        else:
            # apply the filters
            evals_stats["eval_creation_date"] = self.evaluations_filters["date_raw"].strftime(
                "%d-%m-%Y"
            )
            if self.evaluations_filters["sectors"] == _(
                "all sectors"
            ) and self.evaluations_filters["sizes"] == _("all sizes"):
                # number of evaluations per version for all sectors and all sizes
                for version in versions:
                    evals_stats["versions_stats"][
                        version["version"]
                    ] = Evaluation.objects.filter(
                        assessment__version=version["version"],
                        created_at__gte=self.evaluations_filters["date"],
                    ).count()
                # number of evaluations per status for all sectors and all sizes
                evals_stats["nb_evaluations_completed"] = Evaluation.objects.filter(
                    is_finished=True, created_at__gte=self.evaluations_filters["date"]
                ).count()
                evals_stats["nb_evaluations_in_progress"] = Evaluation.objects.filter(
                    is_finished=False, created_at__gte=self.evaluations_filters["date"]
                ).count()
            elif self.evaluations_filters["sectors"] == _(
                "all sectors"
            ) and self.evaluations_filters["sizes"] != _("all sizes"):
                # number of evaluations per versions for all sectors but for a specified size
                for version in versions:
                    evals_stats["versions_stats"][
                        version["version"]
                    ] = Evaluation.objects.filter(
                        assessment__version=version["version"],
                        organisation__size=self.evaluations_filters["sizes"],
                        created_at__gte=self.evaluations_filters["date"],
                    ).count()
                # number of evaluations per status for all sectors but for a specified size
                evals_stats["nb_evaluations_completed"] = Evaluation.objects.filter(
                    is_finished=True,
                    created_at__gte=self.evaluations_filters["date"],
                    organisation__size=self.evaluations_filters["sizes"],
                ).count()
                evals_stats["nb_evaluations_in_progress"] = Evaluation.objects.filter(
                    is_finished=False,
                    created_at__gte=self.evaluations_filters["date"],
                    organisation__size=self.evaluations_filters["sizes"],
                ).count()
            elif self.evaluations_filters["sectors"] != _(
                "all sectors"
            ) and self.evaluations_filters["sizes"] == _("all sizes"):
                # number of evaluations per versions for all sizes but for a specified sector
                for version in versions:
                    evals_stats["versions_stats"][
                        version["version"]
                    ] = Evaluation.objects.filter(
                        assessment__version=version["version"],
                        organisation__sector=self.evaluations_filters["sectors"],
                        created_at__gte=self.evaluations_filters["date"],
                    ).count()
                # number of evaluations per status for all sizes but for a specified sector
                evals_stats["nb_evaluations_completed"] = Evaluation.objects.filter(
                    is_finished=True,
                    created_at__gte=self.evaluations_filters["date"],
                    organisation__sector=self.evaluations_filters["sectors"],
                ).count()
                evals_stats["nb_evaluations_in_progress"] = Evaluation.objects.filter(
                    is_finished=False,
                    created_at__gte=self.evaluations_filters["date"],
                    organisation__sector=self.evaluations_filters["sectors"],
                ).count()
            else:
                # number of evaluations per version for a specified sector and a size
                for version in versions:
                    evals_stats["versions_stats"][
                        version["version"]
                    ] = Evaluation.objects.filter(
                        assessment__version=version["version"],
                        organisation__sector=self.evaluations_filters["sectors"],
                        organisation__size=self.evaluations_filters["sizes"],
                        created_at__gte=self.evaluations_filters["date"],
                    ).count()
                # number of evaluations per status for a specified sector and a size
                evals_stats["nb_evaluations_completed"] = Evaluation.objects.filter(
                    is_finished=True,
                    created_at__gte=self.evaluations_filters["date"],
                    organisation__sector=self.evaluations_filters["sectors"],
                    organisation__size=self.evaluations_filters["sizes"],
                ).count()
                evals_stats["nb_evaluations_in_progress"] = Evaluation.objects.filter(
                    is_finished=False,
                    created_at__gte=self.evaluations_filters["date"],
                    organisation__sector=self.evaluations_filters["sectors"],
                    organisation__size=self.evaluations_filters["sizes"],
                ).count()
        evals_stats["total_nb_evals"] = (
            evals_stats["nb_evaluations_completed"] + evals_stats["nb_evaluations_in_progress"]
        )
        return evals_stats


def take_n_month_steps(date, nb_steps):
    """
    This function takes a "date" as a parameter then adds or subtracts "nb_steps" months from it (depending
    on the sign of nb_steps), It returns the resulting date
    """
    m, y = (date.month + nb_steps) % 12, date.year + (date.month + nb_steps - 1) // 12
    if not m:
        m = 12
    d = min(
        date.day,
        [
            31,
            29 if y % 4 == 0 and (not y % 100 == 0 or y % 400 == 0) else 28,
            31,
            30,
            31,
            30,
            31,
            31,
            30,
            31,
            30,
            31,
        ][m - 1],
    )
    return date.replace(day=d, month=m, year=y)
