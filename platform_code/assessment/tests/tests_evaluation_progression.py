from assessment.models import (
    Assessment,
    Choice,
    Evaluation,
    EvaluationElement,
    MasterSection,
    Section,
)
from django.test import TestCase

from .object_creation import create_assessment_body, create_evaluation, create_scoring

"""
In this file, we test the evaluation progression and the methods related to it in the different classes.
This starts from the choice ticked and goes to the evaluation. We only test the methods from models here, not the forms
nor the CBV.
"""


class EvaluationProgressionTestCase(TestCase):
    def setUp(self):
        create_assessment_body(version="1.0")
        self.assessment = Assessment.objects.get(version="1.0")
        create_scoring(assessment=self.assessment)
        # Create the evaluation object linked to the assessment but without body yet
        self.evaluation = create_evaluation(assessment=self.assessment, name="evaluation")
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

    def tearDown(self):
        self.assertTrue(Evaluation.objects.get(name="evaluation"))  # Test is exists before
        self.evaluation.delete()
        with self.assertRaises(Exception):
            Evaluation.objects.get(name="evaluation")  # Test it does not exist after deletion

    def test_choice_ticked(self):
        # Test tick for choice
        self.assertFalse(self.choice1.is_ticked)
        self.choice1.set_choice_ticked()
        self.assertTrue(self.choice1.is_ticked)
        self.choice1.set_choice_unticked()
        self.assertFalse(self.choice1.is_ticked)
        self.choice1.is_ticked = True
        self.assertTrue(self.choice1.is_ticked)

    def test_choice_is_applicable(self):
        # test choice is applicable: C3 is a switch choice, so C4 is not applicable when C3 is ticked
        self.assertTrue(self.choice3.is_applicable())
        self.assertTrue(self.choice4.is_applicable())
        self.choice3.set_choice_ticked()
        self.assertTrue(self.choice3.is_applicable())
        self.assertFalse(self.choice4.is_applicable())

    def test_evaluation_element_status(self):
        self.assertFalse(self.choice1.is_ticked)
        self.assertFalse(self.evaluation_element1.status)
        self.choice1.set_choice_ticked()
        self.evaluation_element1.set_status()
        self.assertTrue(
            self.evaluation_element1.status
        )  # EE1 has status to True when C1 is ticked
        self.choice1.delete()
        self.evaluation_element1.set_status()
        self.assertFalse(self.evaluation_element1.status)

    def test_evaluation_element_get_list_choices_ticked(self):
        # Test get list choices ticked, first 0 then C3 then C3 and C4 then only C3
        self.assertEqual([], self.evaluation_element2.get_list_choices_ticked())  # Empty list
        self.choice3.set_choice_ticked()
        self.assertEqual([self.choice3], self.evaluation_element2.get_list_choices_ticked())
        self.choice4.set_choice_ticked()
        self.assertEqual(
            [self.choice3, self.choice4], self.evaluation_element2.get_list_choices_ticked()
        )
        self.choice3.set_choice_unticked()
        self.assertEqual([self.choice4], self.evaluation_element2.get_list_choices_ticked())

    def test_evaluation_element_reset_choices(self):
        # Test reset choices: first no choice ticked then C1 then reset the choices
        self.assertFalse(self.evaluation_element1.status)
        self.choice1.set_choice_ticked()
        self.evaluation_element1.set_status()
        self.assertTrue(self.evaluation_element1.status)
        self.evaluation_element1.reset_choices()  # set the status of the evaluation element
        # Need to do a refresh from DB to load the state of self.choice1 because DB updated, not the object...
        self.choice1.refresh_from_db()
        self.assertFalse(self.choice1.is_ticked)
        self.assertFalse(self.evaluation_element1.status)

    def test_evaluation_element_reset_choices_bis(self):
        self.choice3.set_choice_ticked()
        self.assertEqual([self.choice3], self.evaluation_element2.get_list_choices_ticked())
        self.evaluation_element2.reset_choices()
        self.choice3.refresh_from_db()
        self.assertEqual([], self.evaluation_element2.get_list_choices_ticked())

    def test_evaluation_element_are_conditions_between_choices_satisfied(self):
        # C3 is_concerned_switch is True so C3 and C4 cannot be both ticked
        # The method only compare the choices in the list it takes in argument
        self.assertTrue(self.evaluation_element2.are_conditions_between_choices_satisfied([]))
        self.assertTrue(
            self.evaluation_element2.are_conditions_between_choices_satisfied(
                [str(self.choice3)]
            )
        )
        self.assertTrue(self.evaluation_element2.has_condition_between_choices())
        self.assertFalse(
            self.evaluation_element2.are_conditions_between_choices_satisfied(
                [str(self.choice3), str(self.choice4)]
            )
        )

    def test_evaluation_element_is_applicable(self):
        self.assertTrue(self.evaluation_element2.is_applicable())
        self.choice1.set_choice_ticked()
        self.assertFalse(self.evaluation_element2.is_applicable())

    def test_section_progression(self):
        self.assertEqual(self.section1.user_progression, 0)
        self.choice2.set_choice_ticked()  # Use C2 because C1 sets conditions on EE2
        self.evaluation_element1.set_status()
        self.section1.set_progression()
        self.assertEqual(self.section1.user_progression, 50)
        self.choice3.set_choice_ticked()
        self.evaluation_element2.set_status()
        self.section1.set_progression()
        self.assertEqual(self.section1.user_progression, 100)
        self.evaluation_element1.reset_choices()
        self.choice1.refresh_from_db()
        self.section1.set_progression()
        self.assertEqual(self.section1.user_progression, 50)

    def test_section_progression_not_applicable(self):
        # The EE2 depends on C1
        self.choice1.set_choice_ticked()
        self.evaluation_element1.set_status()
        self.section1.set_progression()
        self.assertEqual(self.section1.user_progression, 100)

    def test_evaluation_progression_and_finished(self):
        """
        Set the choices C2, C3 and C5 to ticked in order to finish the evaluation
        :return:
        """
        self.assertEqual(self.evaluation.calculate_progression(), 0)
        self.choice2.set_choice_ticked()
        self.evaluation_element1.set_status()
        self.choice3.set_choice_ticked()
        self.evaluation_element2.set_status()
        self.section1.set_progression()
        self.assertEqual(self.section1.user_progression, 100)
        # Test evaluation is finished - should not work
        self.assertEqual(self.evaluation.calculate_progression(), 50)
        self.evaluation.set_finished()
        self.assertFalse(self.evaluation.is_finished)
        self.assertIsNone(self.evaluation.finished_at)
        # Section 2
        self.choice5.set_choice_ticked()
        self.evaluation_element3.set_status()
        self.section2.set_progression()
        self.assertEqual(self.section2.user_progression, 100)
        self.assertEqual(self.evaluation.calculate_progression(), 100)
        # Test set_finished
        self.evaluation.set_finished()
        self.assertTrue(self.evaluation.is_finished)
        self.assertIsNotNone(self.evaluation.finished_at)
