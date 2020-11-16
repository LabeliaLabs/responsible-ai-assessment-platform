import json
from ast import literal_eval

from django.test import TestCase

from assessment.models import (
    Assessment,
    Evaluation,
    EvaluationScore,
    Section,
    EvaluationElement,
    MasterChoice,
    Choice, ScoringSystem,
)

from .object_creation import (
    create_evaluation,
)
from ..import_assessment import treat_and_save_dictionary_data

"""
In this file, the scoring is tested: the class EvaluationScore, the calculation of the max score

Be careful, the assessment is created based on the import file and not the assessment creation method !
"""


class TestEvaluationScoreStatic(TestCase):
    """
    Test the creation of evaluation score and the static fields (max_points, coefficient) which do not depend
    on the evaluation progression
    """

    def setUp(self):
        with open("assessment/tests/import_test_files/assessment_test_v1.json") as json_file:
            self.assessment_data = json.load(json_file)
        treat_and_save_dictionary_data(self.assessment_data)
        self.assessment = Assessment.objects.get(name="assessment")
        json_file.close()
        # Create the evaluation object linked to the assessment but without body yet
        self.evaluation = create_evaluation(assessment=self.assessment, name="evaluation")
        with open("assessment/tests/import_test_files/scoring_test_v1.json") as scoring_json:
            self.dic_choices = literal_eval(scoring_json.read())
        self.scoring_system = ScoringSystem.objects.get(assessment=self.assessment)
        self.scoring_system.master_choices_weight_json = self.dic_choices
        self.scoring_system.save()
        self.evaluation.create_evaluation_body()
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
        self.evaluation_element3 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="1",
            section=self.section2,
        )

    def test_evaluation_score_creation_no_body(self):
        """
        Create an evaluation without body and evaluation score associated
        """
        evaluation_test = create_evaluation(assessment=self.assessment, name="test")
        EvaluationScore.create_evaluation_score(evaluation=evaluation_test)
        self.assertTrue(EvaluationScore.objects.get(evaluation=evaluation_test))  # Test object created
        evaluation_score = EvaluationScore.objects.get(evaluation=evaluation_test)
        self.assertEqual(0, evaluation_score.max_points)  # No body so no points
        self.assertEqual(evaluation_score.coefficient_scoring_system, self.scoring_system.attributed_points_coefficient)

    def test_evaluation_score_creation(self):
        """
        Test real evaluation score creation
        """
        self.assertTrue(EvaluationScore.objects.get(evaluation=self.evaluation))
        evaluation_score = EvaluationScore.objects.get(evaluation=self.evaluation)
        self.assertEqual(evaluation_score.max_points, 2.5)  # Max points possible with the scoring import file

    def test_evaluation_score_set_coefficient_scoring_system(self):
        """
        Test this method, normal case, then change scoring system coefficient and then case no scoring
        """
        evaluation_score = EvaluationScore.objects.get(evaluation=self.evaluation)
        self.assertEqual(evaluation_score.coefficient_scoring_system, 0.5)
        self.scoring_system.attributed_points_coefficient = 0.8
        self.scoring_system.save()
        evaluation_score.set_coefficient_scoring_system()
        self.assertEqual(evaluation_score.coefficient_scoring_system, 0.8)
        self.scoring_system.delete()
        self.assertFalse(ScoringSystem.objects.all())  # Check there is no scoring system
        evaluation_score.set_coefficient_scoring_system()  # case by default, it should set 0.5
        self.assertEqual(evaluation_score.coefficient_scoring_system, 0.5)

    def test_evaluation_element_get_scoring(self):
        self.assertEqual(self.evaluation_element1.get_scoring_system(), self.scoring_system)
        self.assertEqual(self.evaluation_element1.get_dic_weight_scoring_system(),
                         self.scoring_system.master_choices_weight_json)
        self.assertEqual(self.evaluation_element1.get_coeff_scoring(),
                         self.scoring_system.attributed_points_coefficient)

    def test_evaluation_element_set_max_points(self):
        self.assertEqual(self.evaluation_element1.max_points, 1)
        self.assertEqual(self.evaluation_element2.max_points, 0.5)
        self.assertEqual(self.evaluation_element3.max_points, 1)

    def test_evaluation_element_set_max_points_with_changes(self):
        """
        Change the weight of choices for the scoring
        Note that element 3 is a radio while the 1 and 2 are checkboxes
        """
        self.assertEqual(self.evaluation_element1.max_points, 1)  # Before setting the max points
        self.assertEqual(self.evaluation_element3.max_points, 1)  # Before setting the max points
        kwargs = {"1.1.a": "3", "2.1.a": "1.5"}
        self.change_weight_choices(**kwargs)
        self.assertEqual(self.evaluation_element1.max_points, 4)  # Sum of the choices (3+1)
        self.assertEqual(self.evaluation_element3.max_points, 1.5)  # Not the sum of the choices (2.5) but the max (1.5)

    def test_section_max_points(self):
        self.assertEqual(self.section1.max_points, 1.5)
        self.assertEqual(self.section2.max_points, 1)

    def test_section_max_points_with_changes(self):
        kwargs = {"1.1.a": "3", "2.1.a": "1.5"}
        self.change_weight_choices(**kwargs)
        self.assertEqual(self.section1.max_points, 4.5)
        self.assertEqual(self.section2.max_points, 1.5)

    def test_evaluation_score_max_points(self):
        evaluation_score = EvaluationScore.objects.get(evaluation=self.evaluation)
        self.assertEqual(evaluation_score.max_points, 2.5)
        kwargs = {"1.1.a": "3", "2.1.a": "1.5"}
        self.change_weight_choices(**kwargs)
        evaluation_score.set_max_points()
        self.assertEqual(evaluation_score.max_points, 6)

    def change_weight_choices(self, **kwargs):
        """
        Intermediate function to change the weight of choices 1 and 5
        kwargs with choice numbering as key and string of float as value
        :return:
        """
        for key, value in kwargs.items():
            if key in self.dic_choices.keys():
                self.dic_choices[key] = value
        self.scoring_system.master_choices_weight_json = self.dic_choices
        self.scoring_system.save()
        self.evaluation_element1.set_max_points()
        self.evaluation_element2.set_max_points()
        self.evaluation_element3.set_max_points()
        self.section1.set_max_points()
        self.section2.set_max_points()


class TestScoreValues(TestCase):
    def setUp(self):
        with open("assessment/tests/import_test_files/assessment_test_v1.json") as json_file:
            self.assessment_data = json.load(json_file)
        treat_and_save_dictionary_data(self.assessment_data)
        self.assessment = Assessment.objects.get(name="assessment")
        json_file.close()
        # Create the evaluation object linked to the assessment but without body yet
        self.evaluation = create_evaluation(assessment=self.assessment, name="evaluation")
        with open("assessment/tests/import_test_files/scoring_test_v1.json") as scoring_json:
            self.dic_choices = literal_eval(scoring_json.read())
        self.scoring_system = ScoringSystem.objects.get(assessment=self.assessment)
        self.scoring_system.master_choices_weight_json = self.dic_choices
        self.scoring_system.save()
        self.evaluation.create_evaluation_body()
        self.evaluation_score = EvaluationScore.objects.get(evaluation=self.evaluation)
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
        self.evaluation_element1.reset_choices()
        self.evaluation_element2.reset_choices()
        self.evaluation_element3.reset_choices()
        for numbering in args:
            order_id_list = numbering.split(".")
            choice = Choice.objects.get(master_choice__order_id=order_id_list[2],
                                        evaluation_element__master_evaluation_element__order_id=order_id_list[1],
                                        evaluation_element__section__master_section__order_id=order_id_list[0])
            if isinstance(choice, Choice):
                choice.set_choice_ticked()
        self.evaluation_element1.set_status()
        self.evaluation_element2.set_status()
        self.evaluation_element3.set_status()
        self.section1.set_progression()
        self.section2.set_progression()
        if "no_change_max_points" not in kwargs:
            self.evaluation_element1.set_points()
            self.evaluation_element2.set_points()
            self.evaluation_element3.set_points()
            self.section1.set_points()
            self.section2.set_points()
        self.evaluation.set_finished()
        self.evaluation_score.need_to_calculate = True

    def change_weight_choices(self, **kwargs):
        """
        Intermediate function to change the weight of choices 1 and 5
        kwargs with choice numbering as key and string of float as value
        :return:
        """
        # Todo refactor DRY as this is the same method than in the previous class (?)
        for key, value in kwargs.items():
            if key in self.dic_choices.keys():
                self.dic_choices[key] = value
        self.scoring_system.master_choices_weight_json = self.dic_choices
        self.scoring_system.save()
        if "no_change_max_points" not in kwargs:
            self.evaluation_element1.set_max_points()
            self.evaluation_element2.set_max_points()
            self.evaluation_element3.set_max_points()
            self.section1.set_max_points()
            self.section2.set_max_points()

    def test_evaluation_element_set_points(self):
        """
        This method set the points of an element is it is applicable
        This method does not check the conditions to ticked the choices which are supposed to be correct!
        :return:
        """
        self.set_progression_evaluation("1.1.a")
        self.assertEqual(self.evaluation_element1.points, 0)
        self.set_progression_evaluation("1.1.b", "1.2.b")
        self.assertEqual(self.evaluation_element1.points, 1)
        self.assertEqual(self.evaluation_element2.points, 0.5)

    def test_evaluation_element_set_points_not_applicable(self):
        """
        EE2 depends on C1 (1.1.a)
        """
        self.set_progression_evaluation("1.1.a", "1.2.b")  # Normally this is not possible
        self.assertEqual(self.evaluation_element1.points, 0)
        self.assertFalse(self.evaluation_element2.is_applicable())
        self.assertEqual(self.evaluation_element2.points, 0)  # As EE2 is not applicable

    def test_evaluation_element_set_points_with_weight_changes(self):
        kwargs = {"1.1.a": "5", "1.1.b": "2", "2.1.a": "0.2545"}
        self.change_weight_choices(**kwargs)
        self.set_progression_evaluation("1.1.a", "1.1.b", "2.1.a")
        self.assertEqual(self.evaluation_element1.points, 7)
        self.assertEqual(self.evaluation_element2.points, 0)
        self.assertEqual(self.evaluation_element3.points, 0.2545)

    def test_section_set_points(self):
        self.set_progression_evaluation("1.1.a")
        self.assertEqual(self.section1.points, 0)
        self.set_progression_evaluation("1.1.b", "1.2.b", "2.1.a")
        self.assertEqual(self.section1.points, 1.5)
        self.assertEqual(self.section2.points, 0)

    def test_section_set_points_with_weight_changes(self):
        kwargs = {"1.1.b": "5", "1.2.a": "2", "2.1.a": "0.2545"}
        self.change_weight_choices(**kwargs)
        self.set_progression_evaluation("1.1.b", "1.2.a", "2.1.a")
        self.assertEqual(self.section1.points, 7)
        self.assertEqual(self.section2.points, 0.2545)

    def test_section_set_points_with_condition_inter(self):
        kwargs = {"1.1.a": "5"}
        self.change_weight_choices(**kwargs)
        self.set_progression_evaluation("1.1.a", "1.2.b")
        self.assertEqual(self.section1.points, 5)  # Points of 1.2.b are not counted

    def test_evaluation_element_calculate_points_not_concerned_no_conditions(self):
        self.assertEqual(self.evaluation_element1.calculate_points_not_concerned(), 0)  # No choice ticked
        self.set_progression_evaluation("1.1.b")
        self.assertEqual(self.evaluation_element1.calculate_points_not_concerned(), 0)  # 1.1.b has no conditions
        self.set_progression_evaluation("1.2.b")
        self.assertEqual(self.evaluation_element2.calculate_points_not_concerned(), 0)  # 1.2.b has no conditions

    def test_evaluation_element_calculate_points_not_concerned_conditions_intra(self):
        self.set_progression_evaluation("1.2.a")
        self.assertEqual(self.evaluation_element2.calculate_points_not_concerned(), 0.5)
        kwargs = {"1.2.b": "5.58"}
        self.change_weight_choices(**kwargs)
        self.set_progression_evaluation("1.2.a")
        self.assertEqual(self.evaluation_element2.calculate_points_not_concerned(), 5.58)
        self.assertEqual(self.evaluation_element2.calculate_points_not_concerned(), self.evaluation_element2.max_points)

    def test_evaluation_element_calculate_points_not_concerned_conditions_inter(self):
        self.set_progression_evaluation("1.1.a")
        self.assertEqual(self.evaluation_element2.calculate_points_not_concerned(), 0.5)
        kwargs = {"1.2.b": "5.58"}
        self.change_weight_choices(**kwargs)
        self.set_progression_evaluation("1.1.a")
        self.assertEqual(self.evaluation_element2.calculate_points_not_concerned(), 5.58)
        self.assertEqual(self.evaluation_element2.calculate_points_not_concerned(), self.evaluation_element2.max_points)

    def test_evaluation_score_set_points_not_concerned_no_condition(self):
        self.evaluation_score.set_points_not_concerned()
        self.assertEqual(self.evaluation_score.points_not_concerned, 0)

    def test_evaluation_score_set_points_not_concerned_condition_intra(self):
        self.set_progression_evaluation("1.1.b", "1.2.a")  # Condition intra on 1.2.a
        self.evaluation_score.set_points_not_concerned()
        self.assertEqual(self.evaluation_score.points_not_concerned, 0.5)
        kwargs = {"1.2.b": "5.58"}
        self.change_weight_choices(**kwargs)
        self.set_progression_evaluation("1.1.b", "1.2.a")  # Condition intra on 1.2.a
        self.evaluation_score.set_points_not_concerned()
        self.assertEqual(self.evaluation_score.points_not_concerned, 5.58)

    def test_evaluation_score_set_points_not_concerned_condition_inter(self):
        self.set_progression_evaluation("1.1.a", "1.1.b")  # Condition inter on 1.1.a
        self.evaluation_score.set_points_not_concerned()
        self.assertEqual(self.evaluation_score.points_not_concerned, 0.5)
        kwargs = {"1.2.b": "5.58"}
        self.change_weight_choices(**kwargs)
        self.set_progression_evaluation("1.1.a", "1.1.b")
        self.evaluation_score.set_points_not_concerned()
        self.assertEqual(self.evaluation_score.points_not_concerned, 5.58)

    def test_evaluation_score_set_points_not_concerned_multiple_conditions(self):
        master_choice_1 = MasterChoice.objects.get(order_id="a",
                                                   master_evaluation_element__order_id="1",
                                                   master_evaluation_element__master_section__order_id="1")
        master_choice_1.is_concerned_switch = 1
        master_choice_1.save()
        choice1 = Choice.objects.get(
            master_choice__order_id="a",
            evaluation_element=self.evaluation_element1,
        )
        choice1.save()
        self.set_progression_evaluation("1.1.a")  # Condition inter on 1.1.a and condition intra on 1.1.a
        self.assertEqual(self.evaluation_element1.calculate_points_not_concerned(), 1)
        self.assertEqual(self.evaluation_element2.calculate_points_not_concerned(), 0.5)
        self.evaluation_score.set_points_not_concerned()
        self.assertEqual(self.evaluation_score.points_not_concerned, 1.5)
        # No conditions in this case, so it should be 0
        self.set_progression_evaluation("1.1.b")
        self.evaluation_score.set_points_not_concerned()
        self.assertEqual(self.evaluation_score.points_not_concerned, 0)

    def test_evaluation_score_set_points_obtained_no_conditions(self):
        self.evaluation_score.set_points_obtained()
        self.assertEqual(self.evaluation_score.points_obtained, 0)
        self.set_progression_evaluation("1.1.b", "1.2.b")
        self.evaluation_score.set_points_not_concerned()
        self.evaluation_score.set_points_obtained()
        self.assertEqual(self.evaluation_score.points_not_concerned, 0)
        self.assertEqual(self.evaluation_score.points_obtained, 1.5)

    def test_evaluation_score_set_points_obtained_conditions_intra(self):
        self.set_progression_evaluation("1.1.b", "1.2.a")
        self.evaluation_score.set_points_not_concerned()
        self.evaluation_score.set_points_obtained()
        self.assertEqual(self.evaluation_score.points_not_concerned, 0.5)
        self.assertEqual(self.evaluation_score.coefficient_scoring_system, 0.5)  # To explain the result, 1+0.5*0.5
        self.assertEqual(self.evaluation_score.points_obtained, 1.25)

    def test_evaluation_score_set_points_obtained_conditions_inter(self):
        kwargs = {"1.2.b": "5"}
        self.change_weight_choices(**kwargs)
        self.set_progression_evaluation("1.1.a", "1.1.b")
        self.evaluation_score.set_points_not_concerned()
        self.evaluation_score.set_points_obtained()
        self.assertEqual(self.evaluation_score.points_not_concerned, 5)
        self.assertEqual(self.evaluation_score.points_obtained, 3.5)

    def test_evaluation_score_set_points_obtained_multiple_conditions(self):
        master_choice_1 = MasterChoice.objects.get(order_id="a",
                                                   master_evaluation_element__order_id="1",
                                                   master_evaluation_element__master_section__order_id="1")
        master_choice_1.is_concerned_switch = 1
        master_choice_1.save()
        choice1 = Choice.objects.get(
            master_choice__order_id="a",
            evaluation_element=self.evaluation_element1,
        )
        choice1.save()
        self.set_progression_evaluation("1.1.a", "2.1.b")  # Condition inter on 1.1.a and condition intra on 1.1.a
        self.evaluation_score.set_points_not_concerned()
        self.evaluation_score.set_points_obtained()
        self.assertEqual(self.evaluation_score.points_not_concerned, 1.5)
        self.assertEqual(self.evaluation_score.points_obtained, 1.75)

    def test_evaluation_score_dilatation(self):
        """
        It is just operations with values points_obtained and points_not_concerned so less test cases
        """
        self.set_progression_evaluation("1.1.b", "1.2.b")
        self.evaluation_score.set_points_not_concerned()
        self.evaluation_score.set_points_obtained()
        self.evaluation_score.set_points_to_dilate()
        self.evaluation_score.set_dilatation_factor()
        self.assertEqual(self.evaluation_score.points_to_dilate, 1.5)
        self.assertEqual(self.evaluation_score.dilatation_factor, 1)
        self.set_progression_evaluation("1.1.b", "1.2.a")
        self.evaluation_score.set_points_not_concerned()
        self.evaluation_score.set_points_obtained()
        self.evaluation_score.set_points_to_dilate()
        self.evaluation_score.set_dilatation_factor()
        self.assertEqual(self.evaluation_score.points_to_dilate, 1)
        self.assertEqual(self.evaluation_score.dilatation_factor, 1.125)

    def test_evaluation_score_set_score(self):
        self.set_progression_evaluation("1.1.b", "1.2.b", "2.1.a")
        self.evaluation_score.process_score_calculation()
        self.assertEqual(self.evaluation_score.score, 60)
        self.set_progression_evaluation("1.1.b", "1.2.a", "2.1.a")
        self.evaluation_score.process_score_calculation()
        self.assertEqual(self.evaluation_score.score, 55)

    def test_evaluation_scores_set_score_bis(self):
        kwargs = {"1.2.b": "5"}
        self.change_weight_choices(**kwargs)
        self.evaluation_score.set_max_points()
        self.set_progression_evaluation("1.1.a", "1.1.b", "2.1.a")
        self.evaluation_score.evaluation = Evaluation.objects.get(name="evaluation")  # Need to reload the evaluation
        self.evaluation_score.process_score_calculation()
        self.assertEqual(self.evaluation_score.score, 67.9)

    def test_evaluation_scores_set_score_max(self):
        self.set_progression_evaluation("1.1.b", "1.2.b", "2.1.b")
        self.evaluation_score.process_score_calculation()
        self.assertEqual(self.evaluation_score.score, 100)
        self.set_progression_evaluation("1.1.a", "1.1.b", "2.1.b")  # Condition inter
        self.evaluation_score.process_score_calculation()
        self.assertEqual(self.evaluation_score.score, 100)
        self.set_progression_evaluation("1.1.b", "1.2.a", "2.1.b")  # Condition inter
        self.evaluation_score.process_score_calculation()
        self.assertEqual(self.evaluation_score.score, 100)

    def test_evaluation_score_calculate_max_points_no_changes(self):
        self.assertFalse(self.evaluation_score.need_to_set_max_points)
        max_points_before = self.evaluation_score.max_points
        self.evaluation_score.need_to_set_max_points = True
        self.evaluation_score.save()
        self.assertTrue(self.evaluation_score.need_to_set_max_points)
        self.evaluation_score.calculate_max_points()
        self.assertEqual(self.evaluation_score.max_points, max_points_before)  # Nothing has changed so the same
        self.assertFalse(self.evaluation_score.need_to_set_max_points)  # Test the method changes the field

    def test_evaluation_score_calculate_max_points_blank_evaluation(self):
        kwargs = {"1.2.b": "5", "no_change_max_points": True}  # To do not set the max points in change_weight_choices()
        self.change_weight_choices(**kwargs)
        self.assertEqual(self.evaluation_score.max_points, 2.5)  # To test it has not been changed
        self.evaluation_score.need_to_set_max_points = True
        self.evaluation_score.save()
        self.evaluation_score.calculate_max_points()
        self.section1 = Section.objects.get(master_section__order_id="1", evaluation=self.evaluation)

        self.evaluation_element2 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="2",
            section=self.section1,
        )
        self.assertEqual(self.evaluation_element2.max_points, 5)
        self.assertEqual(self.section1.max_points, 6)
        self.assertEqual(self.evaluation_score.max_points, 7)

    def test_evaluation_score_calculate_max_points_evaluation_finished(self):
        self.set_progression_evaluation("1.1.b", "1.2.b", "2.1.b")
        self.evaluation_score.process_score_calculation()
        self.assertEqual(self.evaluation_score.points_obtained, 2.5)  # Before changing the scoring
        kwargs = {"1.2.b": "5", "2.1.b": "3", "no_change_max_points": True}
        self.change_weight_choices(**kwargs)
        self.assertEqual(self.evaluation_score.max_points, 2.5)  # To test it has not been changed
        # Just need "no_change_max_points" in kwargs
        self.set_progression_evaluation("1.1.b", "1.2.b", "2.1.b", **kwargs)
        self.assertEqual(self.evaluation_element2.points, 0.5)  # To test it has not changed
        self.evaluation_score.need_to_set_max_points = True
        self.evaluation_score.save()
        self.evaluation_score.calculate_max_points()
        # Need to get the objects again as they have been modified and not saved in this method
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
        self.evaluation_element3 = EvaluationElement.objects.get(
            master_evaluation_element__order_id="1",
            section=self.section2,
        )

        self.assertEqual(self.evaluation_element2.max_points, 5)
        self.assertEqual(self.section1.max_points, 6)
        self.assertEqual(self.section2.max_points, 3)  # As 2.1 is a radio
        self.assertEqual(self.evaluation_score.max_points, 9)
        # Test the points have changed
        self.assertEqual(self.evaluation_element2.points, 5)
        self.assertEqual(self.evaluation_element3.points, 3)
        self.assertEqual(self.section1.points, 6)
        self.assertEqual(self.section2.points, 3)
        # Not changed in the method calculate_max_points
        self.evaluation_score.process_score_calculation()
        self.assertEqual(self.evaluation_score.points_obtained, 9)
        self.assertEqual(self.evaluation_score.score, 100)
