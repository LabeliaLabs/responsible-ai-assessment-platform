import re
import plotly.offline as opy
import plotly.graph_objs as go
import datetime

from django.conf import settings
from django.contrib import admin
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path


class DashboardAdminSite(admin.AdminSite):
    site_header = "Admin monitoring"
    site_title = "Monitoring"
    index_title = "Welcome to the admin monitoring dashboard"
    context = {"graph_list": []}

    def get_urls(self):
        urls = super().get_urls()
        # Replace the admin-dashboard:index by admin:index in order to route well in the template
        urls[0] = admin.site.urls[0][0]
        urls += [
            path('monitoring/', self.admin_view(self.get_view), name="monitoring")
        ]
        return urls

    def get_view(self, request):
        """
        Generate the view of the dashboard, if the user is admin.
        Call the function set_context to add all the graphs registered in the context.
        """
        user = request.user
        if user.is_admin:
            self.set_context()
            return TemplateResponse(request, "admin/monitoring.html", self.context)
        else:
            return redirect("home:homepage")

    def set_context(self):
        """
        This method add the graphs to the context in a list "graph_list".
        You can add other objects to the context here as it will be called by the method "get_view"
        """
        self.account_creation_graph()
        self.organisation_creation_graph()
        self.evaluation_creation_graph()
        self.user_connection_graph()
        self.error_graph()

    def get_logs(self, *args, **kwargs):
        """
        Return the lines of the log files in platform_code/logs.
        You can pass in kwargs the name of the file : "file_name=<name>"
        :return:
        """
        if "file_name" in kwargs:
            file_name = kwargs.get("file_name")
            with open(file_name, "r") as file:
                file_data = file.read()
                file.close()
        else:
            if settings.DEBUG:
                with open("dev.log", "r") as file:
                    file_data = file.read()
                    file.close()
            # Prod configuration
            else:
                with open("prod.log", "r") as file:
                    file_data = file.read()
                    file.close()
        return file_data

    def add_graph_to_context(self, graph):
        """
        Add a graph (plotly)
        """
        self.context["graph_list"].append(graph)

    def make_time_graph(self, days, graph_type, log_tag, graph_title, y_axis_title, ):
        """
        This method creates a plotly graph with time in x axis and you chose the variable for y "log_tag"
        which will be search in the logs.

        :param days: int, the number of days in the x axis
        :param graph_type: string ("line" or "bar")
        :param log_tag: string, searched in the logs
        :param graph_title: string, title of the graph
        :param y_axis_title: string, title of y axis
        """
        logs_data = self.get_logs()
        # Number of days
        length = days
        today = datetime.datetime.now()
        x = [today]
        y = [0] * length
        for i in range(length):
            x = [today - datetime.timedelta(i)] + x
            date = today - datetime.timedelta(i)
            date_readable = datetime.datetime.strftime(date, "%Y-%m-%d")
            regex = re.findall(rf'({date_readable})(.*)\[({log_tag})\]', logs_data)
            y[-i - 1] = len(regex)
        if graph_type == "bar":
            data = go.Bar(x=x, y=y)
        elif graph_type == "line":
            data = go.Scatter(x=x, y=y,
                              marker={'color': 'red'},
                              mode="lines",
                              )

        layout = go.Layout(title=graph_title,
                           xaxis={'title': 'date',
                                  'type': 'date',
                                  'tick0': x[0],
                                  'tickmode': 'linear',
                                  'tickformat': '%d %b %Y',
                                  'dtick': 86400000.0 * 7  # every week a date
                                  },
                           yaxis={'title': y_axis_title,
                                  'dtick': '1',
                                  }
                           )
        figure = go.Figure(data=data, layout=layout)
        return opy.plot(figure, auto_open=False, output_type='div')

    def account_creation_graph(self):
        """
        Number of account creation ie account which has been activated
        """
        graph = self.make_time_graph(days=30,
                                     graph_type="bar",
                                     log_tag="account_activated",
                                     graph_title="Number of accounts created and activated per day",
                                     y_axis_title="Account activated")
        self.add_graph_to_context(graph=graph)

    def organisation_creation_graph(self):
        """
        Organisation creation
        """
        graph = self.make_time_graph(days=30,
                                     graph_type="bar",
                                     log_tag="organisation_creation",
                                     graph_title="Number of organisations created per day",
                                     y_axis_title="Organisations created")
        self.add_graph_to_context(graph=graph)

    def evaluation_creation_graph(self):
        """
        Evaluation creation
        """
        graph = self.make_time_graph(days=30,
                                     graph_type="bar",
                                     log_tag="evaluation_creation",
                                     graph_title="Number of evaluations created per day",
                                     y_axis_title="Evaluations created")
        self.add_graph_to_context(graph=graph)

    def error_graph(self):
        """
        Graph of all the error 404, 403, 500 and 400
        """
        graph = self.make_time_graph(days=30,
                                     graph_type="line",
                                     log_tag="(.*)error(.*)",
                                     graph_title="Number of errors - all",
                                     y_axis_title="error")
        self.add_graph_to_context(graph=graph)

    def user_connection_graph(self):
        """
        Create the plotly graph to count the user connections
        During a certain period of time until today, we search in the log file if there is a lof for an user connection
        to the corresponding date. We count them day by day (list y) using regex.
        :return:
        """
        graph = self.make_time_graph(days=30,
                                     graph_type="line",
                                     log_tag="user_connection",
                                     graph_title="Number of users connection per day",
                                     y_axis_title="connections")
        self.add_graph_to_context(graph=graph)
