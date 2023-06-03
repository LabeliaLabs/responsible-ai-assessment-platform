import json

from assessment.forms import JsonUploadForm
from assessment.import_assessment import (
    ImportAssessment,
    add_resources,
    external_link_already_exist_lang,
    test_order_id_letter,
    test_order_id_number,
)
from assessment.models import (
    Assessment,
    ExternalLink,
    MasterChoice,
    MasterEvaluationElement,
    MasterSection,
)
from assessment.scoring import check_and_valid_scoring_json
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from home.models import User


class ImportAssessmentTestCase(TestCase):
    """
    This class test the import of the assessment. It does not verify the conditions (json file, json format)
    but that the logic of the assessment is respected in the json

    The fact that the objects match with the language is tested in tests_model_translation.
    """

    def setUp(self):
        with open("assessment/tests/import_test_files/assessment_test_v1.json") as json_file:
            self.assessment_data = json.load(json_file)
        json_file.close()

        # import and save a second assessment to test the previous version attribute
        with open(
            "assessment/tests/import_test_files/assessment_test_first_version.json"
        ) as json_file_2:
            self.assessment_data_2 = json.load(json_file_2)
        json_file_2.close()
        ImportAssessment(self.assessment_data_2)

    def tearDown(self):
        del self.assessment_data
        del self.assessment_data_2
        for assessment in Assessment.objects.all():
            assessment.delete()

    def test_check_assessment(self):
        self.assertTrue(ImportAssessment(self.assessment_data).success)

    def test_check_assessment_fail(self):
        del self.assessment_data["version"]
        self.assertFalse(ImportAssessment(self.assessment_data).success)

    def test_check_assessment_fail_bis(self):
        del self.assessment_data["sections"]["section 1"]["elements"]
        self.assertFalse(ImportAssessment(self.assessment_data).success)

    def test_import_assessment(self):
        self.assertTrue(ImportAssessment(self.assessment_data).success)
        self.assertEqual(len(list(Assessment.objects.all())), 2)
        self.assertEqual(len(list(MasterSection.objects.all())), 4)
        self.assertEqual(len(list(MasterEvaluationElement.objects.all())), 6)
        self.assertEqual(len(list(MasterChoice.objects.all())), 12)
        self.assertEqual(len(list(ExternalLink.objects.all())), 1)

    def test_import_assessment_conditions_elements(self):
        self.assertTrue(ImportAssessment(self.assessment_data).success)
        self.assertEqual(len(list(MasterEvaluationElement.objects.all())), 6)
        self.assertEqual(len(list(MasterChoice.objects.all())), 12)
        master_evaluation_element1 = MasterEvaluationElement.objects.get(
            name="Element 1 fr", master_section__name="section 1 fr"
        )
        master_choice1a = MasterChoice.objects.get(
            master_evaluation_element=master_evaluation_element1, answer_text="answer a fr"
        )
        master_evaluation_element2 = MasterEvaluationElement.objects.get(name="Element 2 fr")
        self.assertEqual(master_evaluation_element2.depends_on, master_choice1a)

    def test_import_assessment_conditions_choices(self):
        self.assertTrue(ImportAssessment(self.assessment_data).success)
        self.assertEqual(len(list(MasterEvaluationElement.objects.all())), 6)
        self.assertEqual(len(list(MasterChoice.objects.all())), 12)
        master_evaluation_element2 = MasterEvaluationElement.objects.get(
            name="Element 2 fr", master_section__name="section 1 fr"
        )
        master_choice2a = MasterChoice.objects.get(
            master_evaluation_element=master_evaluation_element2, answer_text="answer a fr"
        )
        master_choice2b = MasterChoice.objects.get(
            master_evaluation_element=master_evaluation_element2, answer_text="answer b fr"
        )
        self.assertTrue(master_choice2a.is_concerned_switch)
        self.assertFalse(master_choice2b.is_concerned_switch)

    def test_import_assessment_element_resources(self):
        self.assertTrue(ImportAssessment(self.assessment_data).success)
        self.assertEqual(len(list(MasterEvaluationElement.objects.all())), 6)
        self.assertEqual(len(list(ExternalLink.objects.all())), 1)
        master_evaluation_element1 = MasterEvaluationElement.objects.get(
            name="Element 1 fr", master_section__name="section 1 fr"
        )
        resource = ExternalLink.objects.all()[0]
        self.assertEqual(master_evaluation_element1.external_links.all()[0], resource)

    # Test the assessment keys
    def test_import_assessment_missing_assessment_key(self):
        keys_list = [
            "name_fr",
            "name_en",
            "sections",
            "version",
            "previous_assessment_version",
        ]
        for key in keys_list:
            del self.assessment_data[key]
            self.assertFalse(ImportAssessment(self.assessment_data).success)
            self.assertIn(
                "You have missing keys for the assessment data",
                ImportAssessment(self.assessment_data).message,
            )
            with self.assertRaises(Exception):
                Assessment.objects.get(version="1.0")

    def test_import_assessment_prod_version(self):
        self.assessment_data["version"] = "0.93"
        self.assertTrue(ImportAssessment(self.assessment_data).success)
        self.assertTrue(Assessment.objects.all())  # There is an assessment in the BD
        assessment_queryset = Assessment.objects.filter(version="0.93")
        self.assertIsNotNone(assessment_queryset)
        self.assertEqual(list(assessment_queryset)[0].version, "0.93")

    def test_import_assessment_negative_version(self):
        self.assessment_data["version"] = "-5"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "The version must be convertible into a positive number",
            ImportAssessment(self.assessment_data).message,
        )

    def test_import_assessment_not_floatable_version(self):
        self.assessment_data["version"] = "1.0-alpha"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "The version must not contain letters. It should be convertible into a float ('0.5', '1.0', etc).",
            ImportAssessment(self.assessment_data).message,
        )

    def test_import_assessment_not_floatable_previous_version(self):
        self.assessment_data["previous_assessment_version"] = "1.0-pre-alpha"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "The previous version must not contain letters. It should be convertible",
            ImportAssessment(self.assessment_data).message,
        )

    def test_import_assessment_negative_previous_version(self):
        self.assessment_data["previous_assessment_version"] = "-4"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "The previous version must be convertible into a positive number",
            ImportAssessment(self.assessment_data).message,
        )

    def test_import_assessment_refers_missing_previous_assessment(self):
        """
        Test that the previous version refers to an existing assessment
        """
        self.assessment_data["previous_assessment_version"] = "0.8"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "The previous version refers to a non-existing assessment.",
            ImportAssessment(self.assessment_data).message,
        )

    # Test the section keys
    def test_import_assessment_missing_section_key(self):
        section_keys = [
            "order_id",
            "name_fr",
            "name_en",
            "keyword_fr",
            "keyword_en",
            "description_fr",
            "description_en",
            "elements",
        ]
        for key in section_keys:
            del self.assessment_data["sections"]["section 1"][key]
            self.assertFalse(ImportAssessment(self.assessment_data).success)
            self.assertIn(
                "You have a section without the required keys",
                ImportAssessment(self.assessment_data).message,
            )
            with self.assertRaises(Exception):
                Assessment.objects.get(version="1.0")

    def test_import_assessment_letter_order_id_sections(self):
        self.assessment_data["sections"]["section 1"]["order_id"] = "a"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "The section id is not an integer for this section",
            ImportAssessment(self.assessment_data).message,
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(version="1.0")

    def test_import_assessment_float_order_id_sections(self):
        self.assessment_data["sections"]["section 1"]["order_id"] = "0.25"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "The section id is not an integer for this section",
            ImportAssessment(self.assessment_data).message,
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(version="1.0")

    # Test missing element keys
    def test_import_assessment_element_without_a_key(self):
        element_keys = [
            "order_id",
            "name_fr",
            "name_en",
            "condition",
            "question_text_fr",
            "question_text_en",
            "question_type",
            "answer_items",
            "explanation_text_fr",
            "explanation_text_en",
            "resources",
        ]
        for key in element_keys:
            del self.assessment_data["sections"]["section 1"]["elements"]["element 1"][key]
            self.assertFalse(ImportAssessment(self.assessment_data).success)
            self.assertIn(
                "without the required keys",
                ImportAssessment(self.assessment_data).message,
            )
            with self.assertRaises(Exception):
                Assessment.objects.get(version="1.0")

    # Test element keys with bad values
    def test_import_assessment_element_bad_condition_format(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "condition"
        ] = "55a"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "You have a condition for a choice which the numbering is",
            ImportAssessment(self.assessment_data).message,
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(version="1.0")

    def test_import_assessment_element_condition_on_nonexistent_choice(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "condition"
        ] = "1.3.a"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "You have set a condition on a choice which does not exist or which is",
            ImportAssessment(self.assessment_data).message,
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(version="1.0")

    def test_import_assessment_element_bad_order_id_format(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "order_id"
        ] = "A"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "The order_id is not an convertible into an integer for this element",
            ImportAssessment(self.assessment_data).message,
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(version="1.0")

    def test_import_assessment_element_bad_order_id_format_bis(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
            "order_id"
        ] = "1,"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "The order_id is not an convertible into an integer for this element",
            ImportAssessment(self.assessment_data).message,
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(version="1.0")

    # Test missing choice keys
    def test_import_assessment_choice_without_key(self):
        choice_keys = ["order_id", "answer_text_fr", "answer_text_en", "is_concerned_switch"]
        for key in choice_keys:
            del self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
                "answer_items"
            ]["1.1.b"][key]
            self.assertFalse(ImportAssessment(self.assessment_data).success)
            self.assertIn(
                "without the required keys",
                ImportAssessment(self.assessment_data).message,
            )
            with self.assertRaises(Exception):
                Assessment.objects.get(version="1.0")

    # Test bad choice key values
    def test_import_assessment_bad_condition_intra_element(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 2"]["answer_items"][
            "1.2.b"
        ]["is_concerned_switch"] = "c"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "The choice has not a boolean value for is_concerned_switch",
            ImportAssessment(self.assessment_data).message,
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(version="1.0")

    def test_import_assessment_choice_bad_order_id(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 1"]["answer_items"][
            "1.1.b"
        ]["order_id"] = "1"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "The order_id of the choice is not a letter",
            ImportAssessment(self.assessment_data).message,
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(version="1.0")

    def test_import_assessment_duplicate_choice_numbering(self):
        self.assessment_data["sections"]["section 1"]["elements"]["element 2"][
            "order_id"
        ] = "1"
        self.assertFalse(ImportAssessment(self.assessment_data).success)
        self.assertIn(
            "You have duplicate choice numbering so please verify your",
            ImportAssessment(self.assessment_data).message,
        )
        with self.assertRaises(Exception):
            Assessment.objects.get(version="1.0")

    # Test resource keys
    def test_import_assessment_resource_keys(self):
        resource_keys = ["resource_type", "resource_text_fr", "resource_text_en"]
        for key in resource_keys:
            del self.assessment_data["sections"]["section 1"]["elements"]["element 1"][
                "resources"
            ]["0"][key]
            self.assertFalse(ImportAssessment(self.assessment_data).success)
            self.assertIn(
                "without the required keys",
                ImportAssessment(self.assessment_data).message,
            )
            with self.assertRaises(Exception):
                Assessment.objects.get(version="1.0")


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


class ResourceTestCase(TestCase):
    def setUp(self):
        self.resource1 = ExternalLink(
            text_fr="test resource", text_en="test resource en", type="Official report"
        )
        self.resource1.save()

    def test_external_link_already_exists(self):
        self.assertEqual(len(list(ExternalLink.objects.all())), 1)
        same_resource1 = ExternalLink(text_fr="test resource", type="Official report")
        self.assertTrue(
            external_link_already_exist_lang(same_resource1.text_fr, same_resource1.type, "fr")
        )
        self.assertFalse(
            external_link_already_exist_lang(same_resource1.text_en, same_resource1.type, "en")
        )
        self.assertTrue(ExternalLink.objects.get(text="test resource", type="Official report"))

    def test_external_resource_already_exists_fails(self):
        self.assertEqual(len(list(ExternalLink.objects.all())), 1)
        new_resource1 = ExternalLink(text_fr="test resource", type="Academic paper")
        new_resource2 = ExternalLink(text_fr="test_resource", type="Official report")
        self.assertFalse(
            external_link_already_exist_lang(new_resource1.text_fr, new_resource1.type, "fr")
        )
        self.assertFalse(
            external_link_already_exist_lang(new_resource2.text_fr, new_resource2.type, "fr")
        )

    def test_add_resource(self):
        # first import the first version
        with open(
            "assessment/tests/import_test_files/assessment_test_first_version.json"
        ) as json_file_2:
            self.assessment_data_2 = json.load(json_file_2)
        json_file_2.close()
        ImportAssessment(self.assessment_data_2)

        with open("assessment/tests/import_test_files/assessment_test_v1.json") as json_file:
            assessment_data = json.load(json_file)
        ImportAssessment(assessment_data)

        master_element = MasterEvaluationElement.objects.first()
        master_element_data = {
            "resources": {
                "0": {
                    "resource_type": "Academic paper",
                    "resource_text_fr": "*[Counterfactual Explanations without Opening theBlack Box: Automated"
                    "Decisions and the GDPR]"
                    "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
                    "B.Mittelstadt, C.Russell, 2018",
                    "resource_text_en": "*[Counterfactual Explanations without Opening the Black Box: Automated"
                    "Decisions and the GDPR]"
                    "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
                    "B.Mittelstadt, C.Russell, 2018",
                }
            }
        }
        initial_resources = len(master_element.external_links.all())
        add_resources(master_element_data, master_element)
        self.assertEqual(len(master_element.external_links.all()), initial_resources + 1)

    def test_add_english_resource_text(self):
        """
        Test add resource empty English text, so first it is created, text_en=None.
        Then import again with text_en not empty so it should catch the existing resource and add English field
        instead of creating new one.
        """

        with open(
            "assessment/tests/import_test_files/assessment_test_first_version.json"
        ) as json_file_2:
            self.assessment_data_2 = json.load(json_file_2)
        json_file_2.close()
        ImportAssessment(self.assessment_data_2)

        with open("assessment/tests/import_test_files/assessment_test_v1.json") as json_file:
            assessment_data = json.load(json_file)
        ImportAssessment(assessment_data)
        master_element = MasterEvaluationElement.objects.filter(external_links=None)[0]
        master_element_data_initial = {
            "resources": {
                "0": {
                    "resource_type": "Academic paper",
                    "resource_text_fr": "*[Counterfactual Explanations without Opening theBlack Box: Automated"
                    "Decisions and the GDPR]"
                    "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
                    "B.Mittelstadt, C.Russell, 2018",
                    "resource_text_en": "",
                }
            }
        }
        master_element_data = {
            "resources": {
                "0": {
                    "resource_type": "Academic paper",
                    "resource_text_fr": "*[Counterfactual Explanations without Opening theBlack Box: Automated"
                    "Decisions and the GDPR]"
                    "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
                    "B.Mittelstadt, C.Russell, 2018",
                    "resource_text_en": "*[Counterfactual Explanations without Opening the Black Box: Automated"
                    "Decisions and the GDPR]"
                    "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
                    "B.Mittelstadt, C.Russell, 2018",
                }
            }
        }
        self.assertEqual(len(master_element.external_links.all()), 0)
        add_resources(master_element_data_initial, master_element)
        self.assertEqual(len(master_element.external_links.all()), 1)
        resource = master_element.external_links.all()[0]
        self.assertEqual(resource.text_en, "")
        add_resources(master_element_data, master_element)
        # No new resource created
        self.assertEqual(len(master_element.external_links.all()), 1)
        # English text set
        resource.refresh_from_db()
        self.assertEqual(
            resource.text_en,
            "*[Counterfactual Explanations without Opening the Black Box: Automated"
            "Decisions and the GDPR]"
            "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
            "B.Mittelstadt, C.Russell, 2018",
        )

    def test_add_french_resource_text(self):
        """
        Test add resource empty French text, so first it is created, text_fr=None.
        Then import again with text_fr not empty so it should catch the existing resource and add English field
        instead of creating new one.
        """
        with open(
            "assessment/tests/import_test_files/assessment_test_first_version.json"
        ) as json_file_2:
            self.assessment_data_2 = json.load(json_file_2)
        json_file_2.close()
        ImportAssessment(self.assessment_data_2)

        with open("assessment/tests/import_test_files/assessment_test_v1.json") as json_file:
            assessment_data = json.load(json_file)
        ImportAssessment(assessment_data)
        master_element = MasterEvaluationElement.objects.filter(external_links=None)[0]
        master_element_data_initial = {
            "resources": {
                "0": {
                    "resource_type": "Academic paper",
                    "resource_text_fr": "",
                    "resource_text_en": "*[Counterfactual Explanations without Opening the Black Box: Automated"
                    "Decisions and the GDPR]"
                    "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
                    "B.Mittelstadt, C.Russell, 2018",
                }
            }
        }
        master_element_data = {
            "resources": {
                "0": {
                    "resource_type": "Academic paper",
                    "resource_text_fr": "*[Counterfactual Explanations without Opening theBlack Box: Automated"
                    "Decisions and the GDPR]"
                    "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
                    "B.Mittelstadt, C.Russell, 2018",
                    "resource_text_en": "*[Counterfactual Explanations without Opening the Black Box: Automated"
                    "Decisions and the GDPR]"
                    "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
                    "B.Mittelstadt, C.Russell, 2018",
                }
            }
        }
        self.assertEqual(len(master_element.external_links.all()), 0)
        add_resources(master_element_data_initial, master_element)
        self.assertEqual(len(master_element.external_links.all()), 1)
        resource = master_element.external_links.all()[0]
        self.assertEqual(resource.text_fr, "")
        add_resources(master_element_data, master_element)
        # No new resource created
        self.assertEqual(len(master_element.external_links.all()), 1)
        # English text set
        resource.refresh_from_db()
        self.assertNotEqual(resource.text_fr, "")

    def test_add_new_resource_text(self):
        """
        Test add resource empty French text and then import new resource (french text modified)
        so new resource created
        """
        with open(
            "assessment/tests/import_test_files/assessment_test_first_version.json"
        ) as json_file_2:
            self.assessment_data_2 = json.load(json_file_2)
        json_file_2.close()
        ImportAssessment(self.assessment_data_2)

        with open("assessment/tests/import_test_files/assessment_test_v1.json") as json_file:
            assessment_data = json.load(json_file)
        ImportAssessment(assessment_data)
        master_element = MasterEvaluationElement.objects.filter(external_links=None)[0]
        master_element_data_initial = {
            "resources": {
                "0": {
                    "resource_type": "Academic paper",
                    "resource_text_fr": "",
                    "resource_text_en": "*[Counterfactual Explanations without Opening the Black Box: Automated"
                    "Decisions and the GDPR]"
                    "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
                    "B.Mittelstadt, C.Russell, 2018",
                }
            }
        }
        master_element_data_bis = {
            "resources": {
                "0": {
                    "resource_type": "Academic paper",
                    "resource_text_fr": "*[Counterfactual Explanations without Opening theBlack Box: Automated"
                    "Decisions and the GDPR]"
                    "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
                    "B.Mittelstadt, C.Russell, 2018",
                    "resource_text_en": "*[Counterfactual Explanations without Opening the Black Box: Automated"
                    "Decisions and the GDPR]"
                    "(https: // arxiv.org / abs / 1711.00399) *, S.Wachter, "
                    "B.Mittelstadt, C.Russell, "
                    "2018 BUT THE RESOURCE HAS CHANGED",
                }
            }
        }
        self.assertEqual(len(master_element.external_links.all()), 0)
        add_resources(master_element_data_initial, master_element)
        self.assertEqual(len(master_element.external_links.all()), 1)
        resource = master_element.external_links.all()[0]
        self.assertEqual(resource.text_fr, "")
        add_resources(master_element_data_bis, master_element)
        # New resource created as text_en has changed
        self.assertEqual(len(master_element.external_links.all()), 2)


class ScoringImportTestCase(TestCase):
    """
    Test the logic of the scoring import (same number of choices than in the assessment, weights are convertible
    into floats, etc)
    """

    def setUp(self):
        with open(
            "assessment/tests/import_test_files/assessment_test_first_version.json"
        ) as json_file_2:
            self.assessment_data_2 = json.load(json_file_2)
        json_file_2.close()
        ImportAssessment(self.assessment_data_2)

        with open("assessment/tests/import_test_files/assessment_test_v1.json") as json_file:
            self.assessment_data = json.load(json_file)
        json_file.close()
        import_assessment = ImportAssessment(self.assessment_data)
        self.assertTrue(import_assessment.success)
        self.assessment = Assessment.objects.get(name="assessment fr")
        with open("assessment/tests/import_test_files/scoring_test_v1.json") as scoring_json:
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


class TestJsonUpload(TestCase):
    """ "
    Test the import assessment & scoring json validation function
    """

    def setUp(self):
        self.email = "admin@hotmail.com"
        self.password = "admin_password"
        self.user = User.object.create_superuser(email=self.email, password=self.password)
        self.client = Client()
        self.client.login(email=self.email, password=self.password)

    def test_upload_json_form(self):
        scoring_file = open("assessment/tests/import_test_files/scoring_test_v1.json", "rb")
        assessment_file = open(
            "assessment/tests/import_test_files/assessment_test_v1.json", "rb"
        )
        post_data = {
            "assessment_json_file": "",  # just the field need to not be empty
            "scoring_json_file": "",
        }
        files = {
            "assessment_json_file": SimpleUploadedFile(
                "assessment_json_file", assessment_file.read()
            ),
            "scoring_json_file": SimpleUploadedFile("scoring_json_file", scoring_file.read()),
        }
        form = JsonUploadForm(post_data, files=files)
        self.assertTrue(form.is_valid())

    def test_upload_json_invalid_form(self):
        """
        Missing scoring, only assessment file
        """
        assessment_file = open("assessment/tests/import_test_files/assessment_test_v1.json")
        post_data = {
            "assessment_json_file": assessment_file,
        }
        form = JsonUploadForm(post_data)
        self.assertFalse(form.is_valid())
        response = self.client.post("/fr/admin/assessment/assessment/upload-json/", post_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("There was an error in the form", str(messages[0]))

    def test_upload_json_post(self):
        scoring_file = open("assessment/tests/import_test_files/scoring_test_v1.json")
        assessment_file = open(
            "assessment/tests/import_test_files/assessment_test_first_version.json"
        )
        post_data = {
            "assessment_json_file": assessment_file,  # just the field need to not be empty
            "scoring_json_file": scoring_file,
        }
        response = self.client.post("/fr/admin/assessment/assessment/upload-json/", post_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 2)
        self.assertEqual(str(messages[0]), "The scoring system has been imported!")
        self.assertEqual(str(messages[1]), "The assessment has been imported!")

    def test_upload_json_invalid_file_type(self):
        """
        Not a json file
        """
        assessment_file = open("assessment/tests/tests_assessment_models.py")
        scoring_file = open("assessment/tests/import_test_files/scoring_test_v1.json")
        post_data = {
            "assessment_json_file": assessment_file,
            "scoring_json_file": scoring_file,
        }
        response = self.client.post("/fr/admin/assessment/assessment/upload-json/", post_data)
        messages = list(get_messages(response.wsgi_request))
        self.assertIn("Incorrect file type, one is not a json:", str(messages[0]))
