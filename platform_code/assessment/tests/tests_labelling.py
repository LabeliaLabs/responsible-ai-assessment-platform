from django.test import TestCase, Client, RequestFactory

from assessment.models import (
    Assessment,
    Evaluation,
    Labelling,
)
from home.models import User, Organisation, PlatformManagement
from home.views.profile import ProfileView


class TestLabellingProcess(TestCase):
    """
    Test the labelling model and the synergy with the evaluation model.
    """
    def setUp(self):
        # Configure an user and organisation
        self.email = "admin@hotmail.com"
        self.password = "admin_password"
        self.user = User.object.create_superuser(email=self.email, password=self.password)
        self.organisation = Organisation.create_organisation(
            "organisation",
            size=Organisation.SIZE[0][0],
            country="FR",
            sector=Organisation.SECTOR[0][0],
            created_by=self.user
        )
        self.client = Client()
        self.client.login(email=self.email, password=self.password)
        scoring_file = open('assessment/tests/import_test_files/scoring_test_v1.json')
        assessment_file = open('assessment/tests/import_test_files/assessment_test_v1_no_previous_version.json')
        post_data = {
            "assessment_json_file": assessment_file,  # just the field need to not be empty
            "scoring_json_file": scoring_file
        }
        # Create the assessment
        self.client.post('/fr/admin/assessment/assessment/upload-json/', post_data)
        self.assessment = Assessment.objects.first()
        # Create an evaluation
        self.evaluation = Evaluation.create_evaluation(
            "evaluation",
            self.assessment,
            self.user,
            self.organisation,
        )
        self.evaluation.create_evaluation_body()

    def test_labelling_creation_fail_evaluation_not_completed(self):
        """
        Test that labelling is only created with completed evaluations
        """
        labelling = Labelling.create_labelling(self.evaluation)
        self.assertIsNone(labelling)

    def test_labelling_creation(self):
        """
        Complete the evaluation to have a max score
        Then create a labelling object associated
        """
        self.evaluation.complete_evaluation(characteristic="max")
        labelling = Labelling.create_labelling(self.evaluation)
        self.assertEqual(labelling.status, "progress")
        self.assertEqual(labelling.counter, 1)

    def test_labelling_justification_required(self):
        """
        Test that the class method sets the status to "justification"
        """
        self.evaluation.complete_evaluation(characteristic="max")
        labelling = Labelling.create_labelling(self.evaluation)
        self.assertEqual(labelling.status, "progress")
        labelling.set_justification_required()
        self.assertEqual(labelling.status, "justification")
        self.assertTrue(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)

    def test_labelling_submit_again(self):
        """
        Test that the class method
        """
        self.evaluation.complete_evaluation(characteristic="max")
        labelling = Labelling.create_labelling(self.evaluation)
        labelling.submit_again()
        self.assertEqual(labelling.status, "progress")
        self.assertEqual(labelling.counter, 2)
        self.assertFalse(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)

    def test_labelling_set_final_status(self):
        """
        Test that the class method
        """
        self.evaluation.complete_evaluation(characteristic="max")
        labelling = Labelling.create_labelling(self.evaluation)
        labelling.set_final_status("rejection")
        self.assertEqual(labelling.status, "refused")
        self.assertFalse(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)
        labelling.set_final_status("validation")
        self.assertEqual(labelling.status, "labelled")
        self.assertFalse(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)

    def test_labelling_process(self):
        """
        Test the sequence of the methods to manipulate the labelling
        """
        self.evaluation.complete_evaluation(characteristic="max")
        self.assertTrue(self.evaluation.is_editable)
        self.assertTrue(self.evaluation.is_deleteable)
        labelling = Labelling.create_labelling(self.evaluation)
        self.assertFalse(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)
        labelling.set_justification_required()
        self.assertEqual(labelling.status, "justification")
        self.assertTrue(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)
        labelling.submit_again()
        self.assertEqual(labelling.status, "progress")
        self.assertFalse(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)
        labelling.set_justification_required()
        self.assertEqual(labelling.status, "justification")
        labelling.submit_again()
        self.assertEqual(labelling.counter, 3)
        labelling.set_final_status("validation")
        self.assertEqual(labelling.status, "labelled")
        self.assertFalse(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)

    def test_evaluation_duplication(self):
        """
        Test the method evaluation_duplication of the Evaluation class
        and that the new evaluation has the same progression (here finished)
        and the same score!
        """
        self.assertEqual(len(list(Evaluation.objects.all())), 1)
        self.evaluation.complete_evaluation(characteristic="normal")
        self.evaluation.duplicate_evaluation()
        self.evaluation_score = self.evaluation.evaluationscore_set.all().first()
        self.assertEqual(len(list(Evaluation.objects.all())), 2)
        self.duplicated_evaluation = Evaluation.objects.filter(name="evaluation-duplication").first()
        self.assertIsNotNone(self.duplicated_evaluation)
        self.duplicated_evaluation_score = self.duplicated_evaluation.evaluationscore_set.all().first()
        self.assertEqual(self.evaluation.is_finished, self.duplicated_evaluation.is_finished)
        self.assertEqual(self.evaluation_score.score, self.duplicated_evaluation_score.score)

    def test_labelling_view_creation(self):
        """
        Test the labelling views:
            - complete the evaluation with a score not high enough and test
        the labelling is not created (labellingView)
            - complete the evaluation with the max score and test that the labelling
        is created, the eval is not editable (labellingView)
        """
        evaluation_score = self.evaluation.evaluationscore_set.all().first()
        # case 1: fail
        self.evaluation.complete_evaluation(characteristic="min")
        self.evaluation.refresh_from_db()
        # The min for the test file is 60 so this should be set manually
        evaluation_score.score = 0
        evaluation_score.save()
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.evaluation.refresh_from_db()
        with self.assertRaises(Exception):
            self.evaluation.labelling
        self.assertTrue(self.evaluation.is_editable)
        self.assertTrue(self.evaluation.is_deleteable)
        # case 2: success
        self.evaluation.complete_evaluation(characteristic="max")
        self.assertTrue(self.evaluation.is_finished)
        self.evaluation.evaluationscore_set.all().first().refresh_from_db()
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.evaluation.refresh_from_db()
        self.assertIsNotNone(self.evaluation.labelling)
        self.assertFalse(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)

    def test_labelling_view_process(self):
        """
        Test the labelling views:
            - creation and then change the status (ask
        justification and submit again)
            - then validate the labellisation
        """
        self.evaluation.complete_evaluation(characteristic="max")
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.evaluation.refresh_from_db()
        self.assertFalse(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)
        self.assertTrue(self.evaluation.has_labelling())
        labelling = self.evaluation.labelling
        self.assertEqual(labelling.status, "progress")
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/justification')
        labelling.refresh_from_db()
        self.evaluation.refresh_from_db()
        self.assertEqual(labelling.status, "justification")
        self.assertTrue(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling-again/')
        labelling.refresh_from_db()
        self.evaluation.refresh_from_db()
        self.assertEqual(labelling.status, "progress")
        self.assertFalse(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)
        self.assertEqual(labelling.counter, 2)
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/validation')
        labelling.refresh_from_db()
        self.evaluation.refresh_from_db()
        self.assertEqual(labelling.status, "labelled")
        self.assertFalse(self.evaluation.is_editable)
        self.assertFalse(self.evaluation.is_deleteable)
        self.assertEqual(labelling.counter, 2)

    def test_labelling_threshold(self):
        """
        Test that a labelling cannot be initiated if the evaluation score is lower than
        the labelling threshold
        """
        platform_management = PlatformManagement.get_or_create()
        self.evaluation.complete_evaluation(characteristic="max")
        self.evaluation.evaluationscore_set.all().first().refresh_from_db()
        evaluation_score = self.evaluation.evaluationscore_set.all().first()
        self.assertTrue(evaluation_score.score > platform_management.labelling_threshold)
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.evaluation.refresh_from_db()
        self.assertTrue(self.evaluation.has_labelling())
        labelling = self.evaluation.labelling
        self.assertEqual(labelling.status, "progress")
        # Now test that if the score lower than labelling threshold, cannot create a labelling
        labelling.delete()
        self.evaluation.refresh_from_db()
        self.assertFalse(self.evaluation.has_labelling())
        evaluation_score.score = 88
        evaluation_score.save()
        self.evaluation.refresh_from_db()
        platform_management.set_labelling_threshold(99)
        platform_management.refresh_from_db()
        self.assertTrue(evaluation_score.score < platform_management.labelling_threshold)
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.assertFalse(self.evaluation.has_labelling())

    def test_user_editor_cannot_create_labelling(self):
        """
        Test that an user member as editor of the evaluation cannot initiate
        a labelling process
        """
        email = "admin@hotmail2.com"
        user2 = User.object.create_user(email=email, password=self.password)
        self.client.login(email=email, password=self.password)
        self.organisation.add_user_to_organisation(user2, "editor")
        self.assertTrue(self.organisation.check_user_is_member_and_can_edit_evaluations(user2))
        self.evaluation.complete_evaluation(characteristic="max")
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.assertFalse(self.evaluation.has_labelling())

    def test_labelling_justification_not_admin(self):
        """
        Test that a user not admin cannot ask for labelling justification
        """
        email = "admin@hotmail2.com"
        user2 = User.object.create_user(email=email, password=self.password)
        self.client.login(email=email, password=self.password)
        self.organisation.add_user_to_organisation(user2, "admin")
        self.assertTrue(self.organisation.check_user_is_member_and_can_edit_evaluations(user2))
        self.evaluation.complete_evaluation(characteristic="max")
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.evaluation.refresh_from_db()
        self.assertTrue(self.evaluation.has_labelling())
        labelling = self.evaluation.labelling
        self.assertEqual(labelling.status, "progress")
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/justification')
        # Previous line not taken into consideration as the user is not an admin of the plateform
        labelling.refresh_from_db()
        self.assertEqual(labelling.status, "progress")

    def test_labelling_validation_not_admin(self):
        """
        Test that a user not admin cannot validate the labelling
        """
        email = "admin@hotmail2.com"
        user2 = User.object.create_user(email=email, password=self.password)
        self.client.login(email=email, password=self.password)
        self.organisation.add_user_to_organisation(user2, "admin")
        self.assertTrue(self.organisation.check_user_is_member_and_can_edit_evaluations(user2))
        self.evaluation.complete_evaluation(characteristic="max")
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.evaluation.refresh_from_db()
        self.assertTrue(self.evaluation.has_labelling())
        labelling = self.evaluation.labelling
        self.assertEqual(labelling.status, "progress")
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/validation')
        # Previous line not taken into consideration as the user is not an admin of the plateform
        labelling.refresh_from_db()
        self.assertEqual(labelling.status, "progress")
        # Connect the admin user to validate the labelling
        self.client.login(email=self.email, password=self.password)
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/validation')
        labelling.refresh_from_db()
        self.assertEqual(labelling.status, "labelled")

    def test_labelling_submit_again_fail(self):
        """
        Test that an evaluation not finished (due to modifications during the justification)
        cannot be submit again
        """
        self.evaluation.complete_evaluation(characteristic="max")
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.evaluation.refresh_from_db()
        labelling = self.evaluation.labelling
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/justification')
        labelling.refresh_from_db()
        self.evaluation.refresh_from_db()
        self.assertEqual(labelling.status, "justification")
        # Reset one evaluation element answer to set the evaluation "not finished"
        evaluation_element = self.evaluation.section_set.first().evaluationelement_set.first()
        self.assertTrue(len(evaluation_element.get_list_choices_ticked()) >= 1)  # At least one choice ticked
        evaluation_element.reset_choices()
        evaluation_element.section.set_progression()
        self.evaluation.set_finished()
        self.assertFalse(self.evaluation.is_finished)
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling-again/')
        labelling.refresh_from_db()
        self.evaluation.refresh_from_db()
        self.assertNotEqual(labelling.status, "progress")
        self.assertEqual(labelling.status, "justification")

    def test_labelling_duplication_view(self):
        """
        Test that an evaluation with a labelling ongoing can be duplicated
        """
        # Test that when no labelling, no duplication of the evaluation
        self.assertEqual(len(list(Evaluation.objects.all())), 1)
        self.client.get(f'{self.evaluation.get_absolute_url()}duplicate/')
        self.assertEqual(len(list(Evaluation.objects.all())), 1)
        # Create the labelling
        self.evaluation.complete_evaluation(characteristic="max")
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.evaluation.refresh_from_db()
        self.assertTrue(self.evaluation.has_labelling())
        # Test that the duplication works when the labelling is created
        self.assertEqual(len(list(Evaluation.objects.all())), 1)
        self.client.get(f'{self.evaluation.get_absolute_url()}duplicate/')
        self.assertEqual(len(list(Evaluation.objects.all())), 2)

    def test_profile_view_add_labelable_evaluation(self):
        """
        Test that the list of the evaluation in the labelling tab in user dashboard page
        is correct (ie score > labelling_threshold or that the evaluation has already a labelling)
        No evaluation case
        """
        request = RequestFactory().get('accounts/profile/')
        request.user = self.user
        response = ProfileView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        context = response.context_data
        self.assertEqual(context["labelable_evaluations"], [])

    def test_profile_view_add_labelable_evaluation_bis(self):
        """
        Test that the list of the evaluation in the labelling tab in user dashboard page
        is correct (ie score > labelling_threshold or that the evaluation has already a labelling)
        One evaluation case
        """
        self.evaluation.complete_evaluation(characteristic="max")
        self.evaluation.refresh_from_db()
        request = RequestFactory().get('accounts/profile/')
        request.user = self.user
        response = ProfileView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        context = response.context_data
        self.assertEqual(context["labelable_evaluations"], [self.evaluation])

    def test_profile_view_add_labelable_evaluation_score_lower(self):
        """
        Test that the list of the evaluation in the labelling tab in user dashboard page
        is correct (ie score > labelling_threshold or that the evaluation has already a labelling)
        Case evaluation score lower than labelling threshold before labelling creation
        """
        self.evaluation.complete_evaluation(characteristic="max")
        self.evaluation.refresh_from_db()
        request = RequestFactory().get('accounts/profile/')
        request.user = self.user
        context = ProfileView.as_view()(request).context_data
        # Ok
        self.assertEqual(context["labelable_evaluations"], [self.evaluation])
        # Now, labelling threshold higher than eval score
        platform_management = PlatformManagement.get_or_create()
        platform_management.set_labelling_threshold(99)
        platform_management.refresh_from_db()
        evaluation_score = self.evaluation.evaluationscore_set.all().first()
        evaluation_score.score = 80
        evaluation_score.save()
        self.assertTrue(platform_management.get_labelling_threshold() > evaluation_score.score)
        request = RequestFactory().get('accounts/profile/')
        request.user = self.user
        context = ProfileView.as_view()(request).context_data
        self.assertEqual(context["labelable_evaluations"], [])

    def test_profile_view_add_labelable_evaluation_already_labelling(self):
        """
        Test that the list of the evaluation in the labelling tab in user dashboard page
        is correct (ie score > labelling_threshold or that the evaluation has already a labelling)
        Case has already a labelling
        """
        self.evaluation.complete_evaluation(characteristic="max")
        self.evaluation.refresh_from_db()
        request = RequestFactory().get('accounts/profile/')
        request.user = self.user
        response = ProfileView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        context = response.context_data
        self.assertEqual(context["labelable_evaluations"], [self.evaluation])
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling-again/')
        # Set not finished
        evaluation_element = self.evaluation.section_set.first().evaluationelement_set.first()
        self.assertTrue(len(evaluation_element.get_list_choices_ticked()) >= 1)  # At least one choice ticked
        evaluation_element.reset_choices()
        evaluation_element.section.set_progression()
        self.evaluation.set_finished()
        self.assertFalse(self.evaluation.is_finished)
        # Test that even if not finished the evaluation is still in the list as has_labelling()
        request = RequestFactory().get('accounts/profile/')
        request.user = self.user
        context = ProfileView.as_view()(request).context_data
        self.assertEqual(context["labelable_evaluations"], [self.evaluation])

    def test_profile_view_add_labelable_evaluation_complex_case(self):
        """
        Test that the list of the evaluation in the labelling tab in user dashboard page
        is correct (ie score > labelling_threshold or that the evaluation has already a labelling)
        Case labelling_threshold become higher than the score after labelling created
        """
        self.evaluation.complete_evaluation(characteristic="max")
        self.evaluation.refresh_from_db()
        evaluation_score = self.evaluation.evaluationscore_set.all().first()
        evaluation_score.score = 80
        evaluation_score.save()
        self.client.get(f'{self.evaluation.get_absolute_url()}labelling/')
        self.assertTrue(self.evaluation.has_labelling())
        platform_management = PlatformManagement.get_or_create()
        platform_management.set_labelling_threshold(99)
        platform_management.refresh_from_db()
        # Labelling threshold higher than the evaluation score
        self.assertTrue(platform_management.get_labelling_threshold() > evaluation_score.score)
        request = RequestFactory().get('accounts/profile/')
        request.user = self.user
        response = ProfileView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        context = response.context_data
        # Still the evaluation in the list as
        self.assertEqual(context["labelable_evaluations"], [self.evaluation])
