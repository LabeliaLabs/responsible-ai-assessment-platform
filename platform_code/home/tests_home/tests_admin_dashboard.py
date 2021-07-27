from django.test import TestCase, Client
from django.urls import reverse
from home.models import User, Organisation
from assessment.tests.object_creation import create_assessment_body, create_evaluation, create_scoring
from assessment.models import Assessment


class DashAccessTestCase(TestCase):
    """
    Test that only users with staff privileges and above can access the dashboard page
    """

    def setUp(self):
        self.email_admin = "admin@test.com"
        self.password_admin = "admin_password"

        self.email_staff = "staff@test.com"
        self.password_staff = "staff_password"

        self.email_user = "user@test.com"
        self.password_user = "user_password"

        # Users and Clients
        self.user_admin = User.object.create_superuser(self.email_admin, self.email_admin)
        self.user_staff = User.object.create_staffuser(self.email_staff, self.password_staff)
        self.user = User.object.create_user(self.email_user, self.password_user)

        self.client_1 = Client()
        self.client_1.login(email=self.email_admin, password=self.password_admin)
        self.client_2 = Client()
        self.client_2.login(email=self.email_staff, password=self.password_staff)
        self.client_3 = Client()
        self.client_3.login(email=self.email_user, password=self.password_user)

        # Assessment
        create_assessment_body(version="1.0")
        self.assessment = Assessment.objects.get(version="1.0")
        create_scoring(assessment=self.assessment)

        # Organisations
        self.organisation_2 = Organisation.create_organisation(name="orga_2",
                                                               size=Organisation.SIZE[0][0],
                                                               country="FR",
                                                               sector=Organisation.SECTOR[0][0],
                                                               created_by=self.user)

        self.organisation_1 = Organisation.create_organisation(name="orga_1",
                                                               size=Organisation.SIZE[0][0],
                                                               country="FR",
                                                               sector=Organisation.SECTOR[0][0],
                                                               created_by=self.user_admin)

        # Evaluations
        self.evaluation_1 = create_evaluation(
            assessment=self.assessment,
            name="evaluation",
            created_by=self.user_admin,
            organisation=self.organisation_1
        )
        self.evaluation_2 = create_evaluation(
            assessment=self.assessment,
            name="evaluation",
            created_by=self.user,
            organisation=self.organisation_2
        )

    # TODO
    # def test_dashboard_access(self):
    #     url = reverse("home:dashboard-view")
    #
    #     # test admin access
    #     print("URL ", url)
    #     response = self.client_1.get('/fr/dashboard/')
    #     print("type of response ", type(response), dir(response))
    #
    #     # self.assertTemplateUsed(response, "home/dashboard/dashboard-admin.html")
    #     print("STATUs code", response.status_code)
    #     self.assertEqual(response.status_code, 200)
    #
    #     # test staff access
    #     response2 = self.client_2.get('/fr/dashboard/')
    #     print("response.status_code", response2.status_code)
    #     # self.assertTemplateUsed(response, "home/dashboard/dashboard-admin.html")
    #     self.assertEqual(response2.status_code, 200)
    #
    #     # test user access
    #     response3 = self.client_3.get('/fr/dashboard')
    #     # self.assertTemplateNotUsed(response, "home/dashboard/dashboard-admin.html")
    #     self.assertEqual(response3.status_code, 302)

    def test_context_content(self):
        url = reverse('home:dashboard-view')
        response = self.client_1.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context), 11)
        self.assertEqual(response.context["nb_orgas"], 2)
        self.assertEqual(response.context["nb_evals"], 2)
        self.assertEqual(response.context["nb_in_progress_evals"], 2)
        self.assertEqual(response.context["nb_users"], 3)
