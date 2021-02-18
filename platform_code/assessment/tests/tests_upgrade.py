from django.contrib.messages import get_messages
from django.test import TestCase, Client

from assessment.models import (
    Assessment,
    Evaluation,
    EvaluationScore,
    Upgrade,
    Section,
    Choice,
    ScoringSystem,
    get_last_assessment_created, EvaluationElement,
)
from home.models import User


class TestJsonUploadUpgradeCase(TestCase):
    """
    Test the function to upload new assessment in the admin when one already in the DB.
    Init by uploading a first assessment.
    """
    def setUp(self):
        self.email = "admin@hotmail.com"
        self.password = "admin_password"
        self.user = User.object.create_superuser(email=self.email, password=self.password)
        self.client = Client()
        self.client.login(email=self.email, password=self.password)
        scoring_file = open('assessment/tests/import_test_files/scoring_test_v1.json')
        assessment_file = open('assessment/tests/import_test_files/assessment_test_v1.json')
        post_data = {
            "assessment_json_file": assessment_file,  # just the field need to not be empty
            "scoring_json_file": scoring_file
        }
        # Create the assessment
        self.client.post('/fr/admin/assessment/assessment/upload-json/', post_data)
        self.client.get('/fr/admin/')  # To pop the messages of the first import

    def test_import_new_assessment(self):
        scoring_v2_file = open('assessment/tests/import_test_files/scoring_test_v2.json')
        assessment_v2_file = open('assessment/tests/import_test_files/assessment_test_v2.json')
        upgrade_table = open('assessment/tests/import_test_files/upgrade_table.json')
        post_data = {
            "assessment_json_file": assessment_v2_file,  # just the field need to not be empty
            "scoring_json_file": scoring_v2_file,
            "upgrade_json_file": upgrade_table
        }
        # Create the assessment
        response = self.client.post('/fr/admin/assessment/assessment/upload-json/', post_data)
        messages = list(get_messages(response.wsgi_request))
        # list of the messages after the 1st import
        self.assertEqual(str(messages[0]), "The scoring system has been imported!")
        self.assertIn("The assessment has been imported! and 1 upgrade item(s) has/have been created",
                      str(messages[1])
                      )

    def test_import_new_assessment_without_upgrade_table(self):
        scoring_v2_file = open('assessment/tests/import_test_files/scoring_test_v2.json')
        assessment_v2_file = open('assessment/tests/import_test_files/assessment_test_v2.json')
        post_data = {
            "assessment_json_file": assessment_v2_file,  # just the field need to not be empty
            "scoring_json_file": scoring_v2_file,
        }
        response = self.client.post('/fr/admin/assessment/assessment/upload-json/', post_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "You need to provide a json file (end with '.json') for the upgrade")


class TestEvaluationFetch(TestCase):
    """
    Test the model methods linked with the upgrade process
    """
    def setUp(self):
        self.email = "admin@hotmail.com"
        self.password = "admin_password"
        self.user = User.object.create_superuser(email=self.email, password=self.password)
        self.client = Client()
        self.client.login(email=self.email, password=self.password)
        scoring_file = open('assessment/tests/import_test_files/scoring_test_v1.json')
        assessment_file = open('assessment/tests/import_test_files/assessment_test_v1.json')
        post_data = {
            "assessment_json_file": assessment_file,  # just the field need to not be empty
            "scoring_json_file": scoring_file
        }
        # Create the assessment
        self.client.post('/fr/admin/assessment/assessment/upload-json/', post_data)
        self.client.get('/fr/admin/')  # To pop the messages of the first import
        self.assessment_v1 = get_last_assessment_created()

    def import_new_assessment(self):
        scoring_v2_file = open('assessment/tests/import_test_files/scoring_test_v2.json')
        assessment_v2_file = open('assessment/tests/import_test_files/assessment_test_v2.json')
        upgrade_table = open('assessment/tests/import_test_files/upgrade_table.json')
        post_data = {
            "assessment_json_file": assessment_v2_file,  # just the field need to not be empty
            "scoring_json_file": scoring_v2_file,
            "upgrade_json_file": upgrade_table
        }
        self.client.post('/fr/admin/assessment/assessment/upload-json/', post_data)
        self.assessment_v2 = Assessment.objects.get(version="1.3")

    def test_is_upgradable(self):
        evaluation = Evaluation(name="Evaluation", assessment=self.assessment_v1)
        evaluation.save()
        evaluation.create_evaluation_body()
        self.import_new_assessment()
        self.assertTrue(evaluation.is_upgradable())

    def test_upgrade_model(self):
        self.import_new_assessment()
        self.assertIsNotNone(Upgrade.objects.first())
        upgrade_table = Upgrade.objects.first()
        self.assertEqual("Upgrade from V1.0 to V1.3", str(upgrade_table))

    def test_fetch_evaluation(self):
        """
        Test that when we create a new evaluation in an organisation which has multiple assessment versions,
        the new evaluation has the new objects of the version marked as "fetch=False" which display
        a text "New" in the front
        """
        self.import_new_assessment()
        # Create a new evaluation with the last assessment
        evaluation = Evaluation(name="Evaluation", assessment=self.assessment_v2)
        evaluation.save()
        evaluation.create_evaluation_body()
        section2 = Section.objects.get(master_section__order_id="2", evaluation=evaluation)
        new_element = EvaluationElement.objects.get(
            master_evaluation_element__order_id="1",
            section=section2,
        )
        element_2 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="2",
            section=section2,
        )
        choice_2_1_a = Choice.objects.get(
            evaluation_element=new_element,
            master_choice__order_id="a"
        )
        # Before setting fetch values, by default fetch is true
        self.assertTrue(element_2.fetch)
        self.assertTrue(new_element.fetch)
        self.assertTrue(choice_2_1_a.fetch)
        # Set the fetch values
        evaluation.fetch_the_evaluation(origin_assessment=self.assessment_v1)
        element_2.refresh_from_db()
        new_element.refresh_from_db()
        choice_2_1_a.refresh_from_db()
        self.assertTrue(element_2.fetch)
        self.assertFalse(new_element.fetch)
        self.assertFalse(choice_2_1_a.fetch)

    def test_upgrade_method(self):
        evaluation = Evaluation(name="Evaluation", assessment=self.assessment_v1)
        evaluation.save()
        evaluation.create_evaluation_body()
        self.import_new_assessment()


class TestEvaluationUpgrade(TestEvaluationFetch):
    """
    Test the evaluation upgrade method and the scoring resulting the upgrade
    Mix of the tests TestJsonUploadUpgradeCase and TestScoreValues

    Note: I tried to use inheritance from TestEvaluationFetch to call super().setUp and import_new_assessment()
    but the inheritance also seems to call all the tests .. which generate issues
    """
    def setUp(self):
        # Import the assessment v1
        self.email = "admin@hotmail.com"
        self.password = "admin_password"
        self.user = User.object.create_superuser(email=self.email, password=self.password)
        self.client = Client()
        self.client.login(email=self.email, password=self.password)
        scoring_file = open('assessment/tests/import_test_files/scoring_test_v1.json')
        assessment_file = open('assessment/tests/import_test_files/assessment_test_v1.json')
        post_data = {
            "assessment_json_file": assessment_file,  # just the field need to not be empty
            "scoring_json_file": scoring_file
        }
        # Create the assessment
        self.client.post('/fr/admin/assessment/assessment/upload-json/', post_data)
        self.client.get('/fr/admin/')  # To pop the messages of the first import
        self.assessment_v1 = get_last_assessment_created()
        self.evaluation = Evaluation(name="Evaluation", assessment=self.assessment_v1)
        self.evaluation.save()
        self.evaluation.create_evaluation_body()
        scoring_v2_file = open('assessment/tests/import_test_files/scoring_test_v2.json')
        assessment_v2_file = open('assessment/tests/import_test_files/assessment_test_v2.json')
        upgrade_table = open('assessment/tests/import_test_files/upgrade_table.json')
        post_data = {
            "assessment_json_file": assessment_v2_file,  # just the field need to not be empty
            "scoring_json_file": scoring_v2_file,
            "upgrade_json_file": upgrade_table
        }
        self.client.post('/fr/admin/assessment/assessment/upload-json/', post_data)
        self.assessment_v2 = Assessment.objects.get(version="1.3")
        self.set_objects()

    def set_objects(self):
        self.evaluation_score = EvaluationScore.objects.get(evaluation=self.evaluation)
        self.scoring_system = ScoringSystem.objects.get(assessment=self.assessment_v1)
        self.section1 = Section.objects.get(master_section__order_id="1",
                                            evaluation=self.evaluation)
        self.section2 = Section.objects.get(master_section__order_id="2",
                                            evaluation=self.evaluation)
        self.evaluation_element1 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="1",
            section=self.section1,
        )
        self.evaluation_element2 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="2",
            section=self.section1,
        )
        # New evaluation element
        self.evaluation_element3 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="1",
            section=self.section2,
        )

    def set_progression_evaluation(self, *args, **kwargs):
        """
        Set the progression of the evaluation by ticking the choices in the args and set the points for EE and sections
        :param args:
        :return:
        """
        element_list = [element for element in EvaluationElement.objects.all()]
        for element in element_list:
            element.reset_choices()
        for numbering in args:
            order_id_list = numbering.split(".")
            choice = Choice.objects.get(master_choice__order_id=order_id_list[2],
                                        evaluation_element__master_evaluation_element__order_id=order_id_list[1],
                                        evaluation_element__section__master_section__order_id=order_id_list[0])
            if isinstance(choice, Choice):
                choice.set_choice_ticked()
        for element in element_list:
            element.set_status()

        self.section1.set_progression()
        self.section2.set_progression()
        for element in element_list:
            element.set_points()
        self.section1.set_points()
        self.section2.set_points()
        self.evaluation.set_finished()
        self.evaluation_score.need_to_calculate = True

    def test_upgrade_evaluation_new_evaluation_created(self):
        self.assertTrue(self.evaluation.is_upgradable())
        self.evaluation.upgrade()
        # Assert a new evaluation has been created
        self.assertEqual(len(Evaluation.objects.all()), 2)
        self.assertEqual(len(Evaluation.objects.filter(assessment=self.assessment_v2)), 1)  # one object

    def test_upgrade_evaluation_objects(self):
        self.assertTrue(self.evaluation.is_upgradable())
        self.evaluation.upgrade()
        new_evaluation = Evaluation.objects.get(assessment=self.assessment_v2)
        section2 = Section.objects.get(master_section__order_id="2", evaluation=new_evaluation)
        self.assertEqual(len(EvaluationElement.objects.filter(section=section2)), 2)  # Two elements so new created
        section1 = Section.objects.get(master_section__order_id="1", evaluation=new_evaluation)
        evaluation_element1 = EvaluationElement.objects.get(master_evaluation_element__order_id="1", section=section1)
        self.assertEqual(len(Choice.objects.filter(evaluation_element=evaluation_element1)), 3)

    def test_upgrade_evaluation_objects_fetched(self):
        self.evaluation.upgrade()
        new_evaluation = Evaluation.objects.get(assessment=self.assessment_v2)
        section2 = Section.objects.get(master_section__order_id="2", evaluation=new_evaluation)
        element3 = EvaluationElement.objects.get(section=section2, master_evaluation_element__order_id="1")
        self.assertFalse(element3.fetch)
        section1 = Section.objects.get(master_section__order_id="1", evaluation=new_evaluation)
        evaluation_element1 = EvaluationElement.objects.get(master_evaluation_element__order_id="1", section=section1)
        new_choice = Choice.objects.get(evaluation_element=evaluation_element1, master_choice__order_id="c")
        self.assertFalse(new_choice.fetch)

    def test_upgrade_evaluation_progression_0(self):
        self.evaluation.upgrade()
        new_evaluation = Evaluation.objects.get(assessment=self.assessment_v2)
        self.assertEqual(new_evaluation.calculate_progression(), 0)

    def test_upgrade_evaluation_progression_partially(self):
        self.set_progression_evaluation("1.1.b", "1.2.b")
        # self.evaluation.refresh_from_db()
        self.assertEqual(self.evaluation.calculate_progression(), 50)
        self.evaluation.upgrade()
        new_evaluation = Evaluation.objects.get(assessment=self.assessment_v2)
        self.assertEqual(new_evaluation.calculate_progression(), 50)

    def test_upgrade_evaluation_progression_partially_bis(self):
        self.set_progression_evaluation("1.1.b", "2.1.b")
        self.assertEqual(self.evaluation.calculate_progression(), 75)
        self.assertEqual(self.section1.user_progression, 50)
        self.assertEqual(self.section2.user_progression, 100)
        self.evaluation.upgrade()
        new_evaluation = Evaluation.objects.get(assessment=self.assessment_v2)
        section1 = Section.objects.get(master_section__order_id="1", evaluation=new_evaluation)
        section2 = Section.objects.get(master_section__order_id="2", evaluation=new_evaluation)
        self.assertEqual(section1.user_progression, 50)
        self.assertEqual(section2.user_progression, 50)
        self.assertEqual(new_evaluation.calculate_progression(), 50)

    def test_upgrade_evaluation_progression_finished(self):
        self.set_progression_evaluation("1.1.b", "1.2.b", "2.1.b")
        self.assertEqual(self.evaluation.calculate_progression(), 100)
        self.assertEqual(self.section1.user_progression, 100)
        self.assertEqual(self.section2.user_progression, 100)
        self.evaluation.upgrade()
        new_evaluation = Evaluation.objects.get(assessment=self.assessment_v2)
        section1 = Section.objects.get(master_section__order_id="1", evaluation=new_evaluation)
        section2 = Section.objects.get(master_section__order_id="2", evaluation=new_evaluation)
        self.assertEqual(section1.user_progression, 100)
        self.assertEqual(section2.user_progression, 50)
        self.assertEqual(new_evaluation.calculate_progression(), 75)
        self.assertFalse(new_evaluation.is_finished)

    def test_upgrade_evaluation_points(self):
        self.set_progression_evaluation("1.1.b", "1.2.b", "2.1.a")
        self.assertEqual(self.section1.max_points, 1.5)
        self.assertEqual(self.section1.points, 1.5)
        self.assertEqual(self.section2.max_points, 1)
        self.assertEqual(self.section2.points, 0)
        self.evaluation.upgrade()
        new_evaluation = Evaluation.objects.get(assessment=self.assessment_v2)
        section1 = Section.objects.get(master_section__order_id="1", evaluation=new_evaluation)
        section2 = Section.objects.get(master_section__order_id="2", evaluation=new_evaluation)
        self.assertEqual(section1.max_points, 3)
        self.assertEqual(section1.points, 1.5)
        self.assertEqual(section2.max_points, 2)
        self.assertEqual(section2.points, 0)
