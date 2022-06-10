import json

from django.test import TestCase, RequestFactory

from assessment.models import (
    Assessment,
    Evaluation,
    Section,
    MasterSection,
    EvaluationElement,
)
from assessment.views.utils.utils import treat_delete_note, treat_archive_note
from home.models import User, Organisation
from .object_creation import (
    create_evaluation,
    create_assessment_body,
    create_scoring,
)


class NotesTestCases(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.object.create_user("test@test.com", "secret_pass")
        create_assessment_body(version="1.0")
        self.assessment = Assessment.objects.get(version="1.0")
        create_scoring(assessment=self.assessment)
        # Create the evaluation object linked to the assessment but without body yet
        self.organisation = Organisation.create_organisation(
            created_by=self.user,
            country="fr",
            name="orgTest",
            size="10-49",
            sector="Industriel - ETI",
        )
        self.evaluation = create_evaluation(
            assessment=self.assessment,
            name="evaluation",
            organisation=self.organisation,
        )
        self.evaluation.save()
        self.evaluation.create_evaluation_body()
        self.master_section1 = MasterSection.objects.get(name="master_section1")
        self.section1 = Section.objects.get(
            master_section=self.master_section1, evaluation=self.evaluation
        )
        self.master_section2 = MasterSection.objects.get(name="master_section2")
        self.section2 = Section.objects.get(
            master_section=self.master_section2, evaluation=self.evaluation
        )
        self.evaluation_element1 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="1",
            section__master_section__order_id="1",
        )
        self.evaluation_element2 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="2",
            section__master_section__order_id="1",
        )

    def tearDown(self):
        self.assertTrue(
            Evaluation.objects.get(name="evaluation")
        )  # Test is exists before
        self.evaluation.delete()
        self.organisation.delete()
        self.user.delete()
        with self.assertRaises(Exception):
            Evaluation.objects.get(
                name="evaluation"
            )  # Test it does not exist after deletion

    def test_treat_delete_note(self):
        self.evaluation_element1.user_notes = "notes"
        self.evaluation_element1.save()
        # creates a request to delete the note from the element 2 with the correct user,
        # this element does not have note
        # the response must be an error(code 500) and the note must be unchanged
        request = self.factory.post(
            "/fr/accounts/profile/", {"delete_note_id": self.evaluation_element2.id}
        )
        request.user = self.user
        response = treat_delete_note(request)
        response_dict = json.loads(response.content)
        self.evaluation_element1.refresh_from_db()
        self.assertFalse(response_dict["success"])
        self.assertIsNone(self.evaluation_element2.user_notes)

        # creates a request to delete the note from the element 1 with the correct user,
        # this element have a note
        # the response must be a success (code 200) and the note must be None
        request = self.factory.post(
            "/fr/accounts/profile/", {"delete_note_id": self.evaluation_element1.id}
        )
        request.user = self.user
        response = treat_delete_note(request)
        response_dict = json.loads(response.content)
        self.evaluation_element1.refresh_from_db()
        self.assertIsNone(self.evaluation_element1.user_notes)
        self.assertTrue(response_dict["success"])

    def test_treat_archive_note(self):
        # try to archive a none existing note, should return a success=False and keep note unarchived
        request = self.factory.post(
            "/fr/accounts/profile/", {"archive_note_id": self.evaluation_element1.id}
        )
        request.user = self.user
        response = treat_archive_note(request)
        response_dict = json.loads(response.content)
        self.assertFalse(self.evaluation_element1.user_notes_archived)
        self.assertFalse(response_dict["success"])

        # try to archive a note, should return a success=True and user_notes_archived should be True
        self.evaluation_element1.user_notes = "notes"
        self.evaluation_element1.save()
        request = self.factory.post(
            "/fr/accounts/profile/", {"archive_note_id": self.evaluation_element1.id}
        )
        request.user = self.user
        response = treat_archive_note(request)
        response_dict = json.loads(response.content)
        self.evaluation_element1.refresh_from_db()
        self.assertTrue(self.evaluation_element1.user_notes_archived)
        self.assertTrue(response_dict["success"])

        # try to unarchive a note, should return a success=True and user_notes_archived should be False
        request = self.factory.post(
            "/fr/accounts/profile/", {"archive_note_id": self.evaluation_element1.id}
        )
        request.user = self.user
        response = treat_archive_note(request)
        response_dict = json.loads(response.content)
        self.evaluation_element1.refresh_from_db()
        self.assertFalse(self.evaluation_element1.user_notes_archived)
        self.assertTrue(response_dict["success"])
