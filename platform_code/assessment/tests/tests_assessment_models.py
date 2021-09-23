import json

from django.test import TestCase
from django.template.defaultfilters import slugify
from django.utils.translation import activate

from assessment.models import (
    Assessment,
    Evaluation,
    EvaluationScore,
    Section,
    MasterSection,
    MasterEvaluationElement,
    EvaluationElement,
    MasterChoice,
    Choice,
    get_last_assessment_created,
    ElementChangeLog,
)

from home.models import (
    User,
    Organisation,
)

from home.views.utils import get_all_change_logs

from .object_creation import (
    create_evaluation,
    create_external_link,
    create_assessment,
    create_master_evaluation_element,
    create_master_section,
    create_assessment_body,
    create_scoring,
    create_element_change_log,
)

# Create your tests here.

# a master evaluation element can not depends on itself -> need to see for choice.depends_on in this case
from ..import_assessment import ImportAssessment

"""
In this file, we test the creation of the different objects (Assessment, MS, MEE, MC, Evaluation, Section, EE, Choice),
their properties (name, suppression, numbering, get_absolute_url).
For the EE (Evaluation Element) and the Choice classes, we test all the logic and interactions between the objects
(conditions intra, inter EE, conditions on choices, etc).
"""


class AssessmentTestCase(TestCase):
    """
    Test the object assessment
    """

    def setUp(self):
        create_assessment(name="assessment1", version="1.0")
        create_assessment(name="assessment2", version="2.0",
                          previous_assessment=Assessment.objects.get(name="assessment1"))

    def test_version_assessment(self):
        """
        Not really useful, the tests of the version would be implemented in the import process
        :return:
        """
        assessment1 = Assessment.objects.get(name="assessment1")
        assessment2 = Assessment.objects.get(name="assessment2")
        self.assertEqual(assessment1.version, "1.0")
        self.assertEqual(assessment2.version, "2.0")
        self.assertEqual(assessment1.previous_assessment, None)
        self.assertEqual(assessment2.previous_assessment.version, "1.0")
        self.assertTrue(type(assessment1.version) == str)
        self.assertEqual(assessment1.version, assessment2.previous_assessment.version)
        self.assertTrue(float(assessment1.version) < float(assessment2.version))
        self.assertTrue(float(assessment2.version) > float(assessment2.previous_assessment.version))

    def test_get_last_assessment_created(self):
        assessment2 = Assessment.objects.get(name="assessment2")
        self.assertEqual(get_last_assessment_created(), assessment2)

    """
    def test_previous_assessment_null_after_deletion(self):
        assessment1 = Assessment.objects.get(name="assessment1")
        assessment2 = Assessment.objects.get(name="assessment2")
        assessment1.delete()
        self.assertIsNone(assessment2.previous_assessment)
    """


class MasterSectionTestCase(TestCase):
    """
    Test the object master section: the name and the numbering
    """

    def setUp(self):
        assessment = create_assessment(name="assessment", version="1.0")
        self.master_section1 = create_master_section(
            name="master_section1",
            assessment=assessment,
            description="description",
            order_id="1",
            keyword="Protection des données"
        )
        self.master_section2 = create_master_section(
            name="master_section2",
            assessment=assessment,
            description="description",
            order_id="2",
            keyword="Documentation des modèles"
        )

    def test_master_section_name(self):
        self.assertEqual(str(self.master_section1), "Master section S1 master_section1")
        self.assertEqual(str(self.master_section2), "Master section S2 master_section2")

    def test_numbering(self):
        self.assertEqual(self.master_section1.get_numbering(), "1")
        self.assertEqual(self.master_section2.get_numbering(), "2")


class MasterEvaluationElementTestCase(TestCase):
    """
    Test the object master evaluation element: check the method has_resources, the name and the numbering
    """

    def setUp(self):
        assessment = create_assessment(name="assessment", version="1.0")
        master_section = create_master_section(
            name="master_section",
            assessment=assessment,
            description="description",
            order_id="1",
            keyword="Protection des données"
        )
        master_section2 = create_master_section(
            name="master_section2",
            assessment=assessment,
            description="description",
            order_id="2",
            keyword="Documentation des modèles"
        )
        resource = create_external_link(text="text_test")
        self.master_evaluation_element1 = create_master_evaluation_element(
            name="master_element1", master_section=master_section, order_id="1"
        )
        self.master_evaluation_element2 = create_master_evaluation_element(
            name="master_element2",
            master_section=master_section,
            order_id="2",
            external_links=resource,
        )
        self.master_evaluation_element3 = create_master_evaluation_element(
            name="master_element3",
            master_section=master_section2,
            order_id="1",
            external_links=resource,
        )

    def test_resources(self):
        self.assertFalse(self.master_evaluation_element1.has_resources())
        self.assertTrue(self.master_evaluation_element2.has_resources())

    def test_master_evaluation_element_numbering(self):
        self.assertEqual(self.master_evaluation_element1.get_numbering(), "1.1")
        self.assertEqual(self.master_evaluation_element2.get_numbering(), "1.2")
        self.assertEqual(self.master_evaluation_element3.get_numbering(), "2.1")

    def test_master_evaluation_element_name(self):
        self.assertEqual(str(self.master_evaluation_element1), "Master Q1.1 master_element1")
        self.assertEqual(str(self.master_evaluation_element3), "Master Q2.1 master_element3")


class MasterChoiceTestcase(TestCase):
    """
    Test the object master choice: the numbering, the name
    """

    def setUp(self):
        create_assessment_body()
        self.master_element1 = MasterEvaluationElement.objects.get(
            name="master_element1"
        )
        self.master_element2 = MasterEvaluationElement.objects.get(
            name="master_element2"
        )
        self.master_element3 = MasterEvaluationElement.objects.get(
            name="master_element3"
        )

    def test_master_choice_get_numbering(self):
        master_choice1 = MasterChoice.objects.get(
            master_evaluation_element=self.master_element1, order_id="a"
        )
        master_choice2 = MasterChoice.objects.get(
            master_evaluation_element=self.master_element1, order_id="b"
        )
        master_choice5 = MasterChoice.objects.get(
            master_evaluation_element=self.master_element3, order_id="a"
        )
        self.assertEqual(master_choice1.get_numbering(), "1.1.a")
        self.assertEqual(master_choice2.get_numbering(), "1.1.b")
        self.assertEqual(master_choice5.get_numbering(), "2.1.a")

    def test_master_choice_name(self):
        master_choice1 = MasterChoice.objects.get(
            master_evaluation_element=self.master_element1, order_id="a"
        )
        master_choice2 = MasterChoice.objects.get(
            master_evaluation_element=self.master_element1, order_id="b"
        )
        master_choice5 = MasterChoice.objects.get(
            master_evaluation_element=self.master_element3, order_id="a"
        )
        self.assertEqual(str(master_choice1), "Master choice 1.1.a answer")
        self.assertEqual(str(master_choice2), "Master choice 1.1.b answer")
        self.assertEqual(str(master_choice5), "Master choice 2.1.a answer")

    def test_master_choice_test_numbering(self):
        master_choice1 = MasterChoice.objects.get(
            master_evaluation_element=self.master_element1, order_id="a"
        )
        master_choice5 = MasterChoice.objects.get(
            master_evaluation_element=self.master_element3, order_id="a"
        )
        self.assertTrue(master_choice1.test_numbering())
        self.assertTrue(master_choice5.test_numbering())

    def test_master_choice_get_list_master_element_depending_on(self):
        master_choice1 = MasterChoice.objects.get(
            master_evaluation_element=self.master_element1, order_id="a"
        )
        master_choice5 = MasterChoice.objects.get(
            master_evaluation_element=self.master_element3, order_id="a"
        )
        self.assertEqual(master_choice1.get_list_master_element_depending_on(), [self.master_element2])
        self.assertEqual(master_choice5.get_list_master_element_depending_on(), [])

    def test_master_choice_has_master_element_conditioned_on(self):
        master_choice1 = MasterChoice.objects.get(master_evaluation_element=self.master_element1, order_id="a")
        master_choice5 = MasterChoice.objects.get(master_evaluation_element=self.master_element3, order_id="a")
        self.assertTrue(master_choice1.has_master_element_conditioned_on())
        self.assertFalse(master_choice5.has_master_element_conditioned_on())


class EvaluationTestCase(TestCase):
    """
    test the object evaluation: its creation, the creation of its body from an assessment, the method to get all
    the elements, the absolute url and the suppression
    """

    def setUp(self):
        create_assessment_body(version="1.0")
        self.assessment = Assessment.objects.get(version="1.0")
        create_scoring(assessment=self.assessment)
        # Create the evaluation object linked to the assessment but without body yet
        self.evaluation = create_evaluation(
            assessment=self.assessment, name="evaluation"
        )
        # Create the evaluation object with a previous assessment
        create_assessment_body(version="2.0", previous_assessment=self.assessment)
        self.assessment_2 = Assessment.objects.get(version="2.0")
        self.evaluation_2 = create_evaluation(
            assessment=self.assessment_2, name="evaluation_2"
        )

    def test_evaluation_creation(self):
        # Create an evaluation without body
        evaluation_model = Evaluation.create_evaluation(
            name="evaluation", assessment=self.assessment, user=None, organisation=None
        )
        self.assertEqual(self.evaluation.name, evaluation_model.name)
        self.assertEqual(
            self.evaluation.assessment.version, evaluation_model.assessment.version
        )
        evaluation_model_2 = Evaluation.create_evaluation(
            name="evaluation_2", assessment=self.assessment_2, user=None, organisation=None)
        self.assertEqual(self.evaluation_2.name, evaluation_model_2.name)
        self.assertEqual(
            self.evaluation_2.assessment.version, evaluation_model_2.assessment.version
        )

    def test_evaluation_create_body(self):
        # Compare the number of objects in the assessment and in the evaluation (sections, evaluation element, choice)
        self.evaluation.create_evaluation_body()
        query_sections = self.evaluation.section_set.all()
        query_evaluation_element = EvaluationElement.objects.all()
        query_choice = Choice.objects.all()
        self.assertEqual(len(query_sections), 2)
        self.assertEqual(len(query_evaluation_element), 3)
        self.assertEqual(len(query_choice), 5)

    def test_evaluation_create_body_score(self):
        """
        Test the Evaluation score creation
        The scoring is test in the file tests_scoring.py
        """
        with self.assertRaises(Exception):
            EvaluationScore.objects.get(evaluation=self.evaluation)
        self.evaluation.create_evaluation_body()
        self.assertTrue(EvaluationScore.objects.get(evaluation=self.evaluation))  # Get the object barely created

    def test_evaluation_slugify(self):
        self.evaluation.save()
        self.assertEqual(self.evaluation.slug, "evaluation")

    def test_list_all_elements(self):
        list_evaluation_elements = []
        for section in self.evaluation.section_set.all():
            for evaluation_element in section.evaluationelement_set.all():
                list_evaluation_elements.append(evaluation_element)
        self.assertEqual(
            list_evaluation_elements, self.evaluation.get_list_all_elements()
        )

    def test_evaluation_get_absolute_url(self):
        user = User.object.create(email="test@email.com", password="test123456")
        organisation = Organisation.objects.create(
            name="organisation",
            size=Organisation.SIZE[0][0],
            created_by=user,
            country="FR",
            sector=Organisation.SECTOR[0][0],
        )
        evaluation = Evaluation.create_evaluation(
            name="evaluation",
            assessment=self.assessment,
            user=user,
            organisation=organisation,
        )
        evaluation_id = evaluation.id
        self.assertEquals(
            evaluation.get_absolute_url(),
            f"/fr/assessment/organisation/{organisation.id}/{evaluation.slug}/{evaluation.id}/",
        )
        self.assertEquals(
            evaluation.get_absolute_url(),
            f"/fr/assessment/organisation/1/evaluation/{evaluation_id}/",
        )  # evaluation_id = 5

    def test_evaluation_suppression(self):
        self.evaluation.delete()
        self.assertEqual(len(list(Section.objects.all())), 0)
        self.assertEqual(len(list(EvaluationElement.objects.all())), 0)
        self.assertEqual(len(list(Choice.objects.all())), 0)


class SectionTestCase(TestCase):
    """
    Test the object section: the creation, the suppression and the absolute url
    """

    def setUp(self):
        create_assessment_body(version="1.0")
        self.assessment = Assessment.objects.get(version="1.0")
        create_scoring(assessment=self.assessment)
        # Create the evaluation object linked to the assessment but without body yet
        self.evaluation = create_evaluation(
            assessment=self.assessment, name="evaluation"
        )
        self.master_section1 = MasterSection.objects.get(name="master_section1")
        self.master_section2 = MasterSection.objects.get(name="master_section2")

    def test_create_section(self):
        section1 = Section.create_section(
            master_section=self.master_section1, evaluation=self.evaluation
        )
        self.assertEqual(section1.master_section.name, "master_section1")
        self.assertEqual(section1.evaluation.name, "evaluation")

    def test_section_get_absolute_url(self):
        user = User.object.create(email="test@email.com", password="test123456")
        organisation = Organisation.objects.create(
            name="organisation",
            size=Organisation.SIZE[0][0],
            created_by=user,
            country="FR",
            sector=Organisation.SECTOR[0][0],
        )
        evaluation = Evaluation.create_evaluation(
            name="evaluation",
            assessment=self.assessment,
            user=user,
            organisation=organisation,
        )
        section1 = Section.create_section(
            master_section=self.master_section1, evaluation=evaluation
        )
        self.assertEquals(
            section1.get_absolute_url(),
            f"/fr/assessment/organisation/{organisation.id}/{evaluation.slug}/{evaluation.id}/section/"
            f"{section1.id}/{slugify(section1.master_section.keyword)}/{section1.master_section.order_id}",
        )
        self.assertEquals(
            section1.get_absolute_url(),
            f"/fr/assessment/organisation/2/evaluation/{evaluation.id}/section/"  # evaluation_id = 10
            f"{section1.id}/protection-des-donnees/1",
        )  # section_id = 4

    def test_fill_notes(self):
        section1 = Section.create_section(
            master_section=self.master_section1, evaluation=self.evaluation
        )
        self.assertFalse(section1.user_notes)
        section1.fill_notes()
        self.assertTrue(section1.user_notes)

    def test_section_suppression(self):
        section1 = Section.create_section(
            master_section=self.master_section1, evaluation=self.evaluation
        )
        self.master_section1.delete()
        self.assertFalse(section1 in Section.objects.all())

    def test_section_suppression_bis(self):
        section2 = Section.create_section(
            master_section=self.master_section2, evaluation=self.evaluation
        )
        self.evaluation.delete()
        self.assertFalse(section2 in Section.objects.all())


class EvaluationElementTestCase(TestCase):
    """
    Test all the logic for EvaluationElement class: creation, suppression, conditions intra between choices and
    conditions inter elements, fetching the change log
    """

    def setUp(self):
        create_assessment_body(version="0.9")
        self.assessment_2 = Assessment.objects.get(version="0.9")

        create_assessment_body(version="1.0", previous_assessment=self.assessment_2)
        self.assessment = Assessment.objects.get(version="1.0")

        create_scoring(assessment=self.assessment)
        # Create the evaluation object linked to the assessment but without body yet
        self.evaluation = create_evaluation(
            assessment=self.assessment, name="evaluation"
        )

        self.evaluation.create_evaluation_body()
        self.evaluation_element1 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="1",
            section__master_section__order_id="1",
        )
        self.evaluation_element2 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="2",
            section__master_section__order_id="1",
        )
        self.evaluation_element3 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="1",
            section__master_section__order_id="2",
        )
        self.choice1 = Choice.objects.get(
            master_choice__order_id="a",
            evaluation_element__master_evaluation_element__name="master_element1",
        )
        self.choice2 = Choice.objects.get(
            master_choice__order_id="b",
            evaluation_element__master_evaluation_element__name="master_element1",
        )
        self.choice3 = Choice.objects.get(
            master_choice__order_id="a",
            evaluation_element__master_evaluation_element__name="master_element2",
        )
        self.choice4 = Choice.objects.get(
            master_choice__order_id="b",
            evaluation_element__master_evaluation_element__name="master_element2",
        )
        self.choice5 = Choice.objects.get(
            master_choice__order_id="a",
            evaluation_element__master_evaluation_element__name="master_element3",
        )

        self.change_log_1 = create_element_change_log(
            "new edito",
            "nouvel édito",
            "New",
            "Nouveau",
            self.evaluation_element1.master_evaluation_element.get_numbering(),
            self.assessment_2,
            self.assessment,
        )
        self.change_log_2 = create_element_change_log(
            "updated edito",
            "edito mis à jour",
            "Updated",
            "Mis à jour",
            self.evaluation_element2.master_evaluation_element.get_numbering(),
            self.assessment_2,
            self.assessment,
        )
        self.change_log_3 = create_element_change_log(
            "",
            "",
            "Unchanged",
            "Inchangé",
            self.evaluation_element3.master_evaluation_element.get_numbering(),
            self.assessment_2,
            self.assessment,
        )

    def create_element_change_logs(self):
        create_scoring(assessment=self.assessment)
        # Create the evaluation object linked to the assessment but without body yet
        self.evaluation = create_evaluation(
            assessment=self.assessment, name="evaluation"
        )

        self.evaluation.create_evaluation_body()
        self.evaluation_element1 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="1",
            section__master_section__order_id="1",
        )
        self.evaluation_element2 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="2",
            section__master_section__order_id="1",
        )
        self.evaluation_element3 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="1",
            section__master_section__order_id="2",
        )
        self.choice1 = Choice.objects.get(
            master_choice__order_id="a",
            evaluation_element__master_evaluation_element__name="master_element1",
        )
        self.choice2 = Choice.objects.get(
            master_choice__order_id="b",
            evaluation_element__master_evaluation_element__name="master_element1",
        )
        self.choice3 = Choice.objects.get(
            master_choice__order_id="a",
            evaluation_element__master_evaluation_element__name="master_element2",
        )
        self.choice4 = Choice.objects.get(
            master_choice__order_id="b",
            evaluation_element__master_evaluation_element__name="master_element2",
        )
        self.choice5 = Choice.objects.get(
            master_choice__order_id="a",
            evaluation_element__master_evaluation_element__name="master_element3",
        )

        self.change_log_1 = create_element_change_log(
            "new edito",
            "nouvel édito",
            "New",
            "Nouveau",
            self.evaluation_element1.master_evaluation_element.get_numbering(),
            self.assessment_2,
            self.assessment,
        )
        self.change_log_2 = create_element_change_log(
            "updated edito",
            "edito mis à jour",
            "Updated",
            "Mis à jour",
            self.evaluation_element2.master_evaluation_element.get_numbering(),
            self.assessment_2,
            self.assessment,
        )
        self.change_log_3 = create_element_change_log(
            "",
            "",
            "Unchanged",
            "Inchangé",
            self.evaluation_element3.master_evaluation_element.get_numbering(),
            self.assessment_2,
            self.assessment,
        )

    def test_evaluation_element_name(self):
        self.assertEqual(str(self.evaluation_element1), "Q1.1 master_element1")
        self.assertEqual(str(self.evaluation_element2), "Q1.2 master_element2")
        self.assertEqual(str(self.evaluation_element3), "Q2.1 master_element3")

    def test_get_choices_as_tuple(self):
        self.assertEqual(
            self.evaluation_element1.get_choices_as_tuple(),
            (
                (
                    self.choice1,
                    "answer | (Lorsque cette réponse est sélectionnée, les autres ne peuvent pas"
                    " l'être)",
                ),
                (self.choice2, "answer"),
            ),
        )
        self.assertEqual(
            self.evaluation_element3.get_choices_as_tuple(), ((self.choice5, "answer"),)
        )

    def test_evaluation_element_notes(self):
        self.assertFalse(self.evaluation_element1.are_notes_filled())
        self.evaluation_element1.user_notes = "Bonjour"
        self.evaluation_element1.save()
        self.assertTrue(self.evaluation_element1.are_notes_filled())

    def test_evaluation_element_possible_answers(self):
        self.assertEqual(self.evaluation_element1.get_number_possible_answers(), 2)
        self.assertEqual(self.evaluation_element2.get_number_possible_answers(), 2)
        self.evaluation_element1.master_evaluation_element.question_type = "radio"
        self.evaluation_element1.master_evaluation_element.save()
        self.assertEqual(self.evaluation_element1.get_number_possible_answers(), 1)

    def test_element_get_master_choice_depending_on(self):
        self.assertEqual(
            self.evaluation_element2.get_master_choice_depending_on(),
            self.choice1.master_choice,
        )
        self.assertEqual(
            self.evaluation_element1.get_master_choice_depending_on(), None
        )

    def test_element_has_condition_on(self):
        self.assertFalse(self.evaluation_element1.has_condition_on())
        self.assertTrue(self.evaluation_element2.has_condition_on())

    def test_element_get_choice_depending_on(self):
        self.assertEqual(
            self.evaluation_element2.get_choice_depending_on(), self.choice1
        )
        self.assertEqual(self.evaluation_element1.get_choice_depending_on(), None)

    def test_element_get_element_depending_on(self):
        self.assertEqual(
            self.evaluation_element2.get_element_depending_on(),
            self.evaluation_element1,
        )
        self.assertEqual(self.evaluation_element1.get_element_depending_on(), None)

    def test_element_has_condition_on_other_elements(self):
        self.assertTrue(self.evaluation_element1.has_condition_on_other_elements())
        self.assertFalse(self.evaluation_element2.has_condition_on_other_elements())

    def test_element_get_choice_setting_conditions_on_other_elements(self):
        self.assertEqual(
            self.evaluation_element1.get_choice_setting_conditions_on_other_elements(),
            self.choice1,
        )
        self.assertEqual(
            self.evaluation_element2.get_choice_setting_conditions_on_other_elements(),
            None,
        )

    def test_element_has_condition_between_choices(self):
        self.assertTrue(self.evaluation_element1.has_condition_between_choices())
        self.assertTrue(self.evaluation_element2.has_condition_between_choices())
        self.assertFalse(self.evaluation_element3.has_condition_between_choices())

    def test_element_get_choice_condition_intra(self):
        # Test the method get_choice_condition_intra from EvaluationElement class
        self.assertEqual(self.choice1, self.evaluation_element1.get_choice_condition_intra())
        self.assertNotEqual(self.choice2, self.evaluation_element1.get_choice_condition_intra())
        self.assertIsNone(self.evaluation_element3.get_choice_condition_intra())

    def test_element_get_list_choices_with_condition(self):
        self.assertEqual(
            self.evaluation_element1.get_list_choices_with_condition(), [self.choice2]
        )
        self.assertEqual(self.evaluation_element3.get_list_choices_with_condition(), [])

    def test_evaluation_element_suppression(self):
        master_element1 = MasterEvaluationElement.objects.filter(name="master_element1")
        master_element1.delete()
        with self.assertRaises(Exception):
            EvaluationElement.objects.get(
                master_evaluation_element__order_id="1",
                section__master_section__order_id="1",
            )
        self.assertEqual(len(list(EvaluationElement.objects.all())), 2)
        self.evaluation_element2.delete()
        with self.assertRaises(Exception):
            EvaluationElement.objects.get(
                master_evaluation_element__order_id="2",
                section__master_section__order_id="1",
            )
        self.assertEqual(len(list(EvaluationElement.objects.all())), 1)

    def test_get_list_of_choices(self):
        self.assertEqual(
            sorted(
                self.evaluation_element1.get_choices_list(),
                key=lambda choice: choice.master_choice.order_id
            ),
            [self.choice1, self.choice2]
        )
        self.assertEqual(
            sorted(
                self.evaluation_element2.get_choices_list(),
                key=lambda choice: choice.master_choice.order_id
            ),
            [self.choice3, self.choice4]
        )

    def test_get_list_of_choices_without_condition_inter(self):
        # Choice 1 has conditions inter
        self.assertEqual(
            self.evaluation_element1.get_list_of_choices_without_condition_inter(),
            [self.choice2]
        )
        # No conditions inter
        self.assertEqual(
            sorted(
                self.evaluation_element2.get_list_of_choices_without_condition_inter(),
                key=lambda choice: choice.master_choice.order_id
            ),
            [self.choice3, self.choice4]
        )

    def test_list_of_choices_without_conditions(self):
        # Choice 1 has conditions inter
        self.assertEqual(
            self.evaluation_element1.get_list_of_choices_without_conditions(),
            [self.choice2]
        )
        # Choice 3 has conditions intra
        self.assertEqual(
            self.evaluation_element2.get_list_of_choices_without_conditions(),
            [self.choice4]
        )

    def test_get_list_of_choices_with_conditions(self):
        self.assertEqual(
            self.evaluation_element1.get_list_of_choices_with_conditions(),
            [self.choice1]
        )
        self.assertEqual(
            self.evaluation_element2.get_list_of_choices_with_conditions(),
            [self.choice3]
        )
        self.assertEqual(
            self.evaluation_element3.get_list_of_choices_with_conditions(),
            []
        )

    def test_get_choice_min_points(self):
        """
        Get the choice without condition with the min points
        """
        self.assertEqual(
            self.evaluation_element1.get_choice_min_points(),
            self.choice2
        )
        self.assertEqual(
            self.evaluation_element2.get_choice_min_points(),
            self.choice4
        )
        self.assertEqual(
            self.evaluation_element3.get_choice_min_points(),
            self.choice5
        )

    def test_get_choices_list_max_points(self):
        self.assertEqual(
            self.evaluation_element1.get_choices_list_max_points(),
            [self.choice2]
        )
        self.assertEqual(
            self.evaluation_element2.get_choices_list_max_points(),
            [self.choice4]
        )

    def test_fill_notes(self):
        self.assertFalse(self.evaluation_element1.user_notes)
        self.evaluation_element1.fill_notes()
        self.assertTrue(self.evaluation_element1.user_notes)

    def test_tick_random_choices_no_condition(self):
        # Test for the first element which has condition inter (on choice1)
        self.assertEqual(self.evaluation_element1.get_list_choices_ticked(), [])
        self.evaluation_element1.tick_random_choices_no_condition()
        # As only one choice not setting condition for element 1, it must be ticked
        self.assertEqual(self.evaluation_element1.get_list_choices_ticked(), [self.choice2])

        # Same for the second element which has condition intra
        self.assertEqual(self.evaluation_element2.get_list_choices_ticked(), [])
        self.evaluation_element2.tick_random_choices_no_condition()
        # As only one choice not setting condition for element 2, it must be ticked
        self.assertEqual(self.evaluation_element2.get_list_choices_ticked(), [self.choice4])

        # Same for the third element which has only one choice and is a radio
        self.assertEqual(self.evaluation_element3.get_list_choices_ticked(), [])
        self.evaluation_element3.tick_random_choices_no_condition()
        # As only one choice not setting condition for element 2, it must be ticked
        self.assertEqual(self.evaluation_element3.get_list_choices_ticked(), [self.choice5])

    def test_element_change_log(self):
        """
        Test that the three change logs are in the DB, that we're able to retrieve each one
        with the correct translation, and that their visibility is set to True by default
        """

        self.assertEqual(len(ElementChangeLog.objects.all()), 3)
        self.assertTrue(self.evaluation_element1.is_change_log_visible())
        self.assertTrue(self.evaluation_element2.is_change_log_visible())
        self.assertTrue(self.evaluation_element3.is_change_log_visible())
        activate("en")
        self.assertEqual(self.evaluation_element1.get_change_log_pastille(), "New")
        self.assertEqual(self.evaluation_element1.get_change_log_pastille(),
                         self.evaluation_element1.get_element_change_log().pastille_en)
        self.assertEqual(self.evaluation_element2.get_change_log_pastille(), "Updated")
        self.assertEqual(self.evaluation_element2.get_change_log_pastille(),
                         self.evaluation_element2.get_element_change_log().pastille_en)
        self.assertEqual(self.evaluation_element3.get_change_log_pastille(), "Unchanged")
        self.assertEqual(self.evaluation_element3.get_change_log_pastille(),
                         self.evaluation_element3.get_element_change_log().pastille_en)

        self.assertEqual(self.evaluation_element1.get_change_log_edito(), "new edito")
        self.assertEqual(self.evaluation_element1.get_change_log_edito(),
                         self.evaluation_element1.get_element_change_log().edito_en)
        self.assertEqual(self.evaluation_element2.get_change_log_edito(), "updated edito")
        self.assertEqual(self.evaluation_element2.get_change_log_edito(),
                         self.evaluation_element2.get_element_change_log().edito_en)
        self.assertEqual(self.evaluation_element3.get_change_log_edito(), "")
        self.assertEqual(self.evaluation_element3.get_change_log_edito(),
                         self.evaluation_element3.get_element_change_log().edito_en)

        activate("fr")
        self.assertEqual(self.evaluation_element1.get_change_log_pastille(), "Nouveau")
        self.assertEqual(self.evaluation_element1.get_change_log_pastille(),
                         self.evaluation_element1.get_element_change_log().pastille_fr)
        self.assertEqual(self.evaluation_element2.get_change_log_pastille(), "Mis à jour")
        self.assertEqual(self.evaluation_element2.get_change_log_pastille(),
                         self.evaluation_element2.get_element_change_log().pastille_fr)
        self.assertEqual(self.evaluation_element3.get_change_log_pastille(), "Inchangé")
        self.assertEqual(self.evaluation_element3.get_change_log_pastille(),
                         self.evaluation_element3.get_element_change_log().pastille_fr)

        self.assertEqual(self.evaluation_element1.get_change_log_edito(), "nouvel édito")
        self.assertEqual(self.evaluation_element1.get_change_log_edito(),
                         self.evaluation_element1.get_element_change_log().edito_fr)
        self.assertEqual(self.evaluation_element2.get_change_log_edito(), "edito mis à jour")
        self.assertEqual(self.evaluation_element2.get_change_log_edito(),
                         self.evaluation_element2.get_element_change_log().edito_fr)
        self.assertEqual(self.evaluation_element3.get_change_log_edito(), "")
        self.assertEqual(self.evaluation_element3.get_change_log_edito(),
                         self.evaluation_element3.get_element_change_log().edito_fr)

    def test_element_change_logs_visibility(self):
        """
        Test that the hide and display methods works as intended for evaluation elements
        """
        self.evaluation_element2.hide_change_log()
        self.assertFalse(self.evaluation_element2.is_change_log_visible())
        self.evaluation_element2.display_change_log()
        self.assertTrue(self.evaluation_element2.is_change_log_visible())

    def test_get_all_change_logs_function(self):
        """
        Test the get_all_change_logs function which is used to retrieve all change logs stored in the DB to be displayed
        on the profile page
        """
        change_logs_dict = get_all_change_logs()

        self.assertEqual(len(list(change_logs_dict.keys())), 1)
        self.assertEqual(list(change_logs_dict.keys()), [self.assessment])

        # master_section2 shouldn't exist in the dictionary because it only contains pastilles of type "Unchanged"
        # so the number of keys in the assessment dictionary should be 1
        self.assertEqual(len(list(change_logs_dict[self.assessment].keys())), 1)

        # test that this is indeed the master_section1 that's inside
        self.assertEqual(list(change_logs_dict[self.assessment].keys())[0],
                         self.evaluation_element1.master_evaluation_element.master_section)

        # test that master_section1 dictionary contain the two master evaluation elements
        master_section1_dict = change_logs_dict[self.assessment][
            self.evaluation_element1.master_evaluation_element.master_section]

        self.assertEqual(len(list(master_section1_dict.keys())), 2)
        self.assertEqual(len(list(change_logs_dict[self.assessment][
                                      self.evaluation_element1.master_evaluation_element.master_section])), 2)

        master_evaluation_element1_change_log = master_section1_dict[
            self.evaluation_element1.master_evaluation_element]
        master_evaluation_element2_change_log = master_section1_dict[
            self.evaluation_element2.master_evaluation_element]

        # test that both master_evaluation_element1 and master_evaluation_element2 has one change log each
        self.assertEqual(master_evaluation_element1_change_log,
                         ElementChangeLog.objects.get(
                             eval_element_numbering=self.evaluation_element1.master_evaluation_element.get_numbering()))
        self.assertEqual(master_evaluation_element2_change_log,
                         ElementChangeLog.objects.get(
                             eval_element_numbering=self.evaluation_element2.master_evaluation_element.get_numbering()))

        # test the function after deleting one of the change logs
        ElementChangeLog.objects.get(
            eval_element_numbering=self.evaluation_element1.master_evaluation_element.get_numbering()).delete()
        change_logs_dict = get_all_change_logs()

        # test that master_section1 dictionary contain one master evaluation elements
        master_section1_dict = change_logs_dict[self.assessment][
            self.evaluation_element2.master_evaluation_element.master_section]

        self.assertEqual(len(list(master_section1_dict.keys())), 1)
        self.assertEqual(len(list(change_logs_dict[self.assessment][
                                      self.evaluation_element1.master_evaluation_element.master_section])), 1)

        # test that the evaluation element has its change log
        master_evaluation_element2_change_log = master_section1_dict[
            self.evaluation_element2.master_evaluation_element]

        self.assertEqual(master_evaluation_element2_change_log,
                         ElementChangeLog.objects.get(
                             eval_element_numbering=self.evaluation_element2.master_evaluation_element.get_numbering()))

        # test the function when there are no change logs, it should return an empty dictionary
        ElementChangeLog.objects.get(
            eval_element_numbering=self.evaluation_element2.master_evaluation_element.get_numbering()).delete()
        change_logs_dict = get_all_change_logs()
        self.assertFalse(any(change_logs_dict[self.assessment]))

    def test_element_change_logs_deletion(self):
        """
         We test that if we delete at least one of the two assessment related to change logs objects
         they also get deleted as a consequence
        """
        self.assessment.delete()
        self.assertEqual(len(ElementChangeLog.objects.all()), 0)

        create_assessment_body(version="1.0", previous_assessment=self.assessment_2)
        self.assessment = Assessment.objects.get(version="1.0")
        self.create_element_change_logs()
        self.assessment_2.delete()
        self.assertEqual(len(ElementChangeLog.objects.all()), 0)


class ChoiceTestCase(TestCase):
    """
    Test all the logic for choice class
    """

    def setUp(self):
        create_assessment_body(version="1.0")
        self.assessment = Assessment.objects.get(version="1.0")
        create_scoring(assessment=self.assessment)
        # Create the evaluation object linked to the assessment but without body yet
        self.evaluation = create_evaluation(
            assessment=self.assessment, name="evaluation"
        )
        self.evaluation.create_evaluation_body()
        self.choice1 = Choice.objects.get(
            master_choice__order_id="a",
            evaluation_element__master_evaluation_element__name="master_element1",
        )
        self.choice2 = Choice.objects.get(
            master_choice__order_id="b",
            evaluation_element__master_evaluation_element__name="master_element1",
        )
        self.choice3 = Choice.objects.get(
            master_choice__order_id="a",
            evaluation_element__master_evaluation_element__name="master_element2",
        )
        self.choice4 = Choice.objects.get(
            master_choice__order_id="b",
            evaluation_element__master_evaluation_element__name="master_element2",
        )
        self.choice5 = Choice.objects.get(
            master_choice__order_id="a",
            evaluation_element__master_evaluation_element__name="master_element3",
        )

    def test_choice_name(self):
        self.assertEqual(str(self.choice1), "1.1.a answer")
        self.assertEqual(str(self.choice2), "1.1.b answer")
        self.assertEqual(str(self.choice3), "1.2.a answer")
        self.assertEqual(str(self.choice4), "1.2.b answer")
        self.assertEqual(str(self.choice5), "2.1.a answer")

    def test_choice_convert_order_id_to_int(self):
        self.assertEqual(self.choice1.convert_order_id_to_int(), 0)
        self.assertEqual(self.choice2.convert_order_id_to_int(), 1)

    def test_choice_get_evaluation_id(self):
        self.assertEqual(self.choice1.get_evaluation_id(), self.evaluation.id)
        self.assertEqual(self.choice5.get_evaluation_id(), self.evaluation.id)

    def test_choice_get_list_element_depending_on(self):
        evaluation_element2 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="2",
            section__master_section__order_id="1",
        )
        self.assertEqual(
            self.choice1.get_list_element_depending_on(), [evaluation_element2]
        )
        self.assertEqual(self.choice2.get_list_element_depending_on(), [])

    def test_choice_has_element_conditioned_on(self):
        self.assertTrue(self.choice1.has_element_conditioned_on())
        self.assertFalse(self.choice2.has_element_conditioned_on())

    def test_choice_has_condition_on(self):
        self.assertFalse(self.choice3.has_condition_on())
        self.assertTrue(self.choice4.has_condition_on())

    def test_choice_get_choice_depending_on(self):
        self.assertEqual(self.choice2.get_choice_depending_on(), self.choice1)
        self.assertEqual(self.choice1.get_choice_depending_on(), None)

    def test_choice_set_conditions_on_other_choices(self):
        self.assertTrue(self.choice1.set_conditions_on_other_choices())
        self.assertFalse(self.choice2.set_conditions_on_other_choices())


# Test models after import

class ModelsAfterImportTestCase(TestCase):
    """
    Test some methods of the assessment models (Assessment, Master classes, Evaluation, etc)
    after the import process
    """

    def setUp(self):
        # Import the v2 file
        with open(
                "assessment/tests/import_test_files/assessment_test_first_version.json"
        ) as json_file:
            self.assessment_data = json.load(json_file)
        json_file.close()
        import_assessment = ImportAssessment(self.assessment_data)
        self.assessment = import_assessment.assessment

    def test_assessment_count_risk_elements(self):
        self.assertEqual(self.assessment.version, "0.9")
        self.assertEqual(self.assessment.count_master_elements_with_risks(), 2)
