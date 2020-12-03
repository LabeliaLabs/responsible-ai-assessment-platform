import json

from django.test import TestCase

from assessment.models import (
    Assessment,
    MasterSection,
    MasterEvaluationElement,
    MasterChoice,
    ExternalLink,
)
from assessment.import_assessment import (
    treat_and_save_dictionary_data,
    external_link_already_exist,
    test_order_id_number,
    test_order_id_letter,
)
from assessment.scoring import check_and_valid_scoring_json


class ImportAssessmentTestCase(TestCase):
    """
    This class test the import of the assessment. It does not verify the conditions (json file, json format)
    but that the logic of the assessment is respected in the json
    """

    def setUp(self):
        with open(
            "assessment/tests/import_test_files/assessment_test_v1.json"
        ) as json_file:
            self.assessment_data = json.load(json_file)

    def tearDown(self):
        del self.assessment_data
        for assessment in Assessment.objects.all():
            assessment.delete()

    def test_import_assessment(self):
        self.assertTrue(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertEqual(len(list(Assessment.objects.all())), 1)
        self.assertEqual(len(list(MasterSection.objects.all())), 2)
        self.assertEqual(len(list(MasterEvaluationElement.objects.all())), 3)
        self.assertEqual(len(list(MasterChoice.objects.all())), 6)
        self.assertEqual(len(list(ExternalLink.objects.all())), 1)

    def test_import_assessment_conditions_elements(self):
        self.assertTrue(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertEqual(len(list(MasterEvaluationElement.objects.all())), 3)
        self.assertEqual(len(list(MasterChoice.objects.all())), 6)
        master_evaluation_element1 = MasterEvaluationElement.objects.get(
            name="Element 1", master_section__name="section 1"
        )
        master_choice1a = MasterChoice.objects.get(
            master_evaluation_element=master_evaluation_element1, answer_text="answer a"
        )
        master_evaluation_element2 = MasterEvaluationElement.objects.get(
            name="Element 2"
        )
        self.assertEqual(master_evaluation_element2.depends_on, master_choice1a)

    def test_import_assessment_conditions_choices(self):
        self.assertTrue(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertEqual(len(list(MasterEvaluationElement.objects.all())), 3)
        self.assertEqual(len(list(MasterChoice.objects.all())), 6)
        master_evaluation_element2 = MasterEvaluationElement.objects.get(
            name="Element 2", master_section__name="section 1"
        )
        master_choice2a = MasterChoice.objects.get(
            master_evaluation_element=master_evaluation_element2, answer_text="answer a"
        )
        master_choice2b = MasterChoice.objects.get(
            master_evaluation_element=master_evaluation_element2, answer_text="answer b"
        )
        self.assertTrue(master_choice2a.is_concerned_switch)
        self.assertFalse(master_choice2b.is_concerned_switch)

    def test_import_assessment_element_resources(self):
        self.assertTrue(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertEqual(len(list(MasterEvaluationElement.objects.all())), 3)
        self.assertEqual(len(list(ExternalLink.objects.all())), 1)
        master_evaluation_element1 = MasterEvaluationElement.objects.get(
            name="Element 1", master_section__name="section 1"
        )
        resource = ExternalLink.objects.all()[0]
        self.assertEqual(master_evaluation_element1.external_links.all()[0], resource)

    def test_import_assessment_negative_version(self):
        self.assessment_data["version"] = "-5"
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertEqual(
            treat_and_save_dictionary_data(self.assessment_data)[1],
            "The version must be convertible" " into a positive number",
        )

    def test_import_assessment_not_floatable_version(self):
        self.assessment_data["version"] = "1.0-alpha"
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "The version must not contain letters. It should be convertible into a float ('0.5', '1.0', etc)."
            " The version you provided was",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )

    def test_import_assessment_without_version(self):
        del self.assessment_data["version"]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You need to provide an assessment version which could be converted into a float",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )

    def test_import_assessment_without_name(self):
        del self.assessment_data["name"]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertEqual(
            "You need to provide a name for the assessment",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )

    def test_import_assessment_without_sections(self):
        del self.assessment_data["sections"]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertEqual(
            "You haven't sections in your assessment",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_without_section_name(self):
        del self.assessment_data["sections"]["section 1"]["name"]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have a section without name",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_letter_order_id_sections(self):
        self.assessment_data["sections"]["section 1"]["order_id"] = "a"
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "The section id is not an integer for this section",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_float_order_id_sections(self):
        self.assessment_data["sections"]["section 1"]["order_id"] = "0.25"
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "The section id is not an integer for this section",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_no_order_id_sections(self):
        del self.assessment_data["sections"]["section 1"]["order_id"]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have a section without order_id",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_section_without_elements(self):
        del self.assessment_data["sections"]["section 1"]["elements"]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have a section without elements",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_element_without_order_id(self):
        del self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "order_id"
        ]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have missing fields for the element",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_element_without_name(self):
        del self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "name"
        ]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have missing fields for the element",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_element_without_condition(self):
        del self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "condition"
        ]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have missing fields for the element",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_element_without_question_text(self):
        del self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "question_text"
        ]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have missing fields for the element",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_element_without_question_type(self):
        del self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "question_type"
        ]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have missing fields for the element",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_element_bad_condition_format(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "condition"
        ] = "55a"
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have a condition for a choice which the numbering is",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_element_condition_on_nonexistent_choice(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "condition"
        ] = "1.3.a"
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have set a condition on a choice which does not exist or which is",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_element_bad_order_id_format(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "order_id"
        ] = "A"
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "The order_id is not an convertible into an integer for this element",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_element_bad_order_id_format_bis(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "order_id"
        ] = "1,"
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "The order_id is not an convertible into an integer for this element",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_element_no_answer_items(self):
        del self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "answer_items"
        ]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "has no answer_items",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_bad_condition_intra_element(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 2"][
            "answer_items"
        ]["1.2.b"]["is_concerned_switch"] = "c"
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "The choice has not a boolean value for is_concerned_switch",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_choice_bad_order_id(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "answer_items"
        ]["1.1.b"]["order_id"] = "1"
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "The order_id is not a letter for this choice",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_choice_no_answer_text(self):
        del self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "answer_items"
        ]["1.1.b"]["answer_text"]
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have missing fields for the choice",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")

    def test_import_assessment_duplicate_choice_numbering(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 2"][
            "order_id"
        ] = "1"
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data)[0])
        self.assertIn(
            "You have duplicate choice numbering so please verify your",
            treat_and_save_dictionary_data(self.assessment_data)[1],
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(name="assessment", version="1.0")


class TestOrderIdTestCase(TestCase):
    def test_order_id_number(self):
        # It should be a string convertible into an integer
        self.assertTrue(test_order_id_number("1"))
        self.assertFalse(test_order_id_number("0.5"))
        self.assertFalse(test_order_id_number(1))
        self.assertFalse(test_order_id_number("a"))

    def test_order_id_letter(self):
        # It should be a lower case between "a" and "n"
        self.assertFalse(test_order_id_letter("1"))
        self.assertFalse(test_order_id_letter("0.5"))
        self.assertFalse(test_order_id_letter("A"))
        self.assertTrue(test_order_id_letter("a"))
        self.assertTrue(test_order_id_letter("h"))
        self.assertTrue(test_order_id_letter("i"))
        self.assertFalse(test_order_id_letter("a,"))


class ExternalLinkAlreadyExistsTestCase(TestCase):
    def setUp(self):
        self.resource1 = ExternalLink(text="test resource", type="Official report")
        self.resource1.save()

    def test_external_link_already_exists(self):
        self.assertEqual(len(list(ExternalLink.objects.all())), 1)
        same_resource1 = ExternalLink(text="test resource", type="Official report")
        self.assertTrue(
            external_link_already_exist(same_resource1.text, same_resource1.type)
        )
        self.assertTrue(
            ExternalLink.objects.get(text="test resource", type="Official report")
        )

    def test_external_resource_already_exists_fails(self):
        self.assertEqual(len(list(ExternalLink.objects.all())), 1)
        new_resource1 = ExternalLink(text="test resource", type="Academic paper")
        new_resource2 = ExternalLink(text="test_resource", type="Official report")
        self.assertFalse(
            external_link_already_exist(new_resource1.text, new_resource1.type)
        )
        self.assertFalse(
            external_link_already_exist(new_resource2.text, new_resource2.type)
        )


class ScoringImportTestCase(TestCase):
    """
    Test the logic of the scoring import (same number of choices than in the assessment, weights are convertible
    into floats, etc)
    """
    def setUp(self):
        with open(
            "assessment/tests/import_test_files/assessment_test_v1.json"
        ) as json_file:
            self.assessment_data = json.load(json_file)
        treat_and_save_dictionary_data(self.assessment_data)
        self.assessment = Assessment.objects.get(name="assessment")
        json_file.close()
        with open(
            "assessment/tests/import_test_files/scoring_test_v1.json"
        ) as scoring_json:
            self.decoded_file = scoring_json.read()

    def test_scoring_import(self):
        self.assertTrue(
            check_and_valid_scoring_json(
                decoded_file=self.decoded_file, assessment=self.assessment
            )[0]
        )

    def test_scoring_import_wrong_json_format(self):
        self.decoded_file = self.decoded_file + ","
        self.assertFalse(
            check_and_valid_scoring_json(
                decoded_file=self.decoded_file, assessment=self.assessment
            )[0]
        )
        self.assertIn(
            "There is an issue in your json architecture. Please verify you file",
            check_and_valid_scoring_json(
                decoded_file=self.decoded_file, assessment=self.assessment
            )[1],
        )

    def test_scoring_import_bad_weight_format(self):
        json_data = json.loads(self.decoded_file)
        json_data["1.1.a"] = "a"
        self.assertFalse(
            check_and_valid_scoring_json(
                decoded_file=json.dumps(json_data), assessment=self.assessment
            )[0]
        )
        self.assertIn(
            "must be convertible into a float like '0.5'",
            check_and_valid_scoring_json(
                decoded_file=json.dumps(json_data), assessment=self.assessment
            )[1],
        )

    def test_scoring_import_missing_choice(self):
        json_data = json.loads(self.decoded_file)
        del json_data["1.1.a"]
        self.assertFalse(
            check_and_valid_scoring_json(
                decoded_file=json.dumps(json_data), assessment=self.assessment
            )[0]
        )
        self.assertIn(
            "Missing choice in the json",
            check_and_valid_scoring_json(
                decoded_file=json.dumps(json_data), assessment=self.assessment
            )[1],
        )

    def test_scoring_import_too_much_choice(self):
        json_data = json.loads(self.decoded_file)
        json_data["1.1.c"] = "5"
        self.assertFalse(
            check_and_valid_scoring_json(
                decoded_file=json.dumps(json_data), assessment=self.assessment
            )[0]
        )
        self.assertIn(
            "is not in the assessment but in the json",
            check_and_valid_scoring_json(
                decoded_file=json.dumps(json_data), assessment=self.assessment
            )[1],
        )

    def test_scoring_import_bad_weight_conditions_inter(self):
        """
        Test the import scoring when a choice with conditions inter evaluation element has a weight not null
        """
        json_data = json.loads(self.decoded_file)
        json_data["1.1.a"] = "1"
        self.assertFalse(
            check_and_valid_scoring_json(
                decoded_file=json.dumps(json_data), assessment=self.assessment
            )[0]
        )
        self.assertIn(
            "has conditions intra/inter but has points associated",
            check_and_valid_scoring_json(
                decoded_file=json.dumps(json_data), assessment=self.assessment
            )[1],
        )

    def test_scoring_import_bad_weight_conditions_intra(self):
        """
        Test the import scoring when a choice with conditions intra evaluation element has a weight not null
        """
        json_data = json.loads(self.decoded_file)
        json_data["1.2.a"] = "1"
        self.assertFalse(
            check_and_valid_scoring_json(
                decoded_file=json.dumps(json_data), assessment=self.assessment
            )[0]
        )
        self.assertIn(
            "has conditions intra/inter but has points associated",
            check_and_valid_scoring_json(
                decoded_file=json.dumps(json_data), assessment=self.assessment
            )[1],
        )

# todo test the scoring and evaluation element weight creation while importing assessment

# todo test the upgrade table
