from django.test import TestCase
from django.template.defaultfilters import slugify

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
)

from home.models import (
    User,
    Organisation,
)

from .object_creation import (
    create_evaluation,
    create_external_link,
    create_assessment,
    create_master_evaluation_element,
    create_master_section,
    create_assessment_body,
    create_scoring,
)

# Create your tests here.

# a master evaluation element can not depends on itself -> need to see for choice.depends_on in this case

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
        create_assessment(name="assessment2", version="2.0")

    def test_version_assessment(self):
        """
        Not really useful, the tests of the version would be implemented in the import process
        :return:
        """
        assessment1 = Assessment.objects.get(name="assessment1")
        assessment2 = Assessment.objects.get(name="assessment2")
        self.assertEqual(assessment1.version, "1.0")
        self.assertEqual(assessment2.version, "2.0")
        self.assertTrue(type(assessment1.version) == str)
        self.assertTrue(float(assessment1.version) < float(assessment2.version))

    def test_get_last_assessment_created(self):
        assessment2 = Assessment.objects.get(name="assessment2")
        self.assertEqual(get_last_assessment_created(), assessment2)


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
        self.assertEqual(str(self.master_section1), "S1 master_section1")
        self.assertEqual(str(self.master_section2), "S2 master_section2")

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
        self.assertEqual(str(self.master_evaluation_element1), "Q1.1 master_element1")
        self.assertEqual(str(self.master_evaluation_element3), "Q2.1 master_element3")


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
        self.assertEqual(str(master_choice1), "1.1.a answer")
        self.assertEqual(str(master_choice2), "1.1.b answer")
        self.assertEqual(str(master_choice5), "2.1.a answer")

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

    def test_evaluation_creation(self):
        # Create an evaluation without body
        evaluation_model = Evaluation.create_evaluation(
            name="evaluation", assessment=self.assessment, user=None, organisation=None
        )
        self.assertEqual(self.evaluation.name, evaluation_model.name)
        self.assertEqual(
            self.evaluation.assessment.version, evaluation_model.assessment.version
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
    conditions inter elements
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
        master_element1 = MasterEvaluationElement.objects.get(name="master_element1")
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


# todo test the scoring evolution

# class ScoringTest(TestCase):
#     def setUp(self):

# todo test the upgrade of the evaluation

# class UpgradeTest(TestCase):
#     def setUp(self):
#
# todo test that we cannot check multiple choices for radio items (modifying html)
