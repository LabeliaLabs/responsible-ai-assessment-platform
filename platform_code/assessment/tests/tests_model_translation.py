# TODO : refactor the test and use setattr!!! create class and inherit methods test_fr and test_en

import json

from django.test import TestCase

from assessment.models import (
    Assessment,
    MasterSection,
)
from assessment.import_assessment import (
    treat_and_save_dictionary_data,
    save_new_assessment_language,
    clean_failed_assessment_import,
)


class ImportAssessmentLanguageTestCase(TestCase):
    """
    Test that the assessment is well imported in one language and that the functions to add the new language work well
    """

    def setUp(self):
        with open(
                "assessment/tests/import_test_files/assessment_test_fr_v1.json"
        ) as json_file:
            self.assessment_data_fr = json.load(json_file)
        json_file.close()
        with open(
                "assessment/tests/import_test_files/assessment_test_en_v1.json"
        ) as json_file_en:
            self.assessment_data_en = json.load(json_file_en)
        json_file_en.close()

    def tearDown(self):
        del self.assessment_data_fr
        del self.assessment_data_en
        for assessment in Assessment.objects.all():
            assessment.delete()

    def test_import_fr(self):
        self.assertTrue(treat_and_save_dictionary_data(self.assessment_data_fr)[0])

    def test_import_en(self):
        self.assertTrue(treat_and_save_dictionary_data(self.assessment_data_en)[0])

    def test_import_both_languages_at_same_time(self):
        """
        Both assessment cannot be imported together as they have the same version
        """
        self.assertTrue(treat_and_save_dictionary_data(self.assessment_data_fr)[0])
        self.assertFalse(treat_and_save_dictionary_data(self.assessment_data_en)[0])
        self.assertIn(
            "There already is an assessment with this version for this language. Please change it.",
            treat_and_save_dictionary_data(self.assessment_data_en)[1]
        )

    def test_import_fr_assessment_and_check_language(self):
        """
        Test the assessment import depending on the language and that all the fields which need translation are
        well translated and that they do not exist in the other languages
        """
        # Todo : Is it possible to factorize this test with the next one ?
        treat_and_save_dictionary_data(self.assessment_data_fr)  # Save the French assessment
        assessment = Assessment.objects.get(version="1.0")
        # Check that the assessment name is the same value than the French one
        self.assertEqual(assessment.name, assessment.name_fr)
        # Check that the English field name is empty
        self.assertIsNone(assessment.name_en)
        # Check also on the master section
        for master_section in assessment.mastersection_set.all():
            # Check the description of the master section
            self.assertEqual(master_section.description, master_section.description_fr)
            self.assertIn("en français", master_section.description)
            # Check that the name responds well
            self.assertIsNotNone(master_section.name_fr)
            self.assertIsNone(master_section.name_en)
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                # Check the master evaluation element French fields
                self.assertIsNotNone(master_evaluation_element.name_fr)
                self.assertIsNotNone(master_evaluation_element.question_text_fr)
                self.assertIsNotNone(master_evaluation_element.explanation_text_fr)
                # Check the English fields
                self.assertIsNone(master_evaluation_element.name_en)
                self.assertIsNone(master_evaluation_element.question_text_en)
                self.assertIsNone(master_evaluation_element.explanation_text_en)
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    # Check the master choice French fields is not None
                    self.assertIsNotNone(master_choice.answer_text_fr)
                    # Check the master choice English field is None
                    self.assertIsNone(master_choice.answer_text_en)
                for resource in master_evaluation_element.external_links.all():
                    self.assertIsNotNone(resource.text_fr)
                    self.assertIsNone(resource.text_en)

    def test_import_en_assessment_and_check_language(self):
        """
        Same test that the previous one, but for the English assessment
        """
        treat_and_save_dictionary_data(self.assessment_data_en)
        assessment = Assessment.objects.get(version="1.0")
        self.assertEqual(assessment.name, assessment.name_en)
        self.assertIsNone(assessment.name_fr)
        for master_section in assessment.mastersection_set.all():
            # Check the description of the master section
            self.assertEqual(master_section.description, master_section.description_en)
            self.assertIn("in English", master_section.description)
            # Check that the name responds well
            self.assertIsNotNone(master_section.name_en)
            self.assertIsNone(master_section.name_fr)
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                # Check the master evaluation element English fields
                self.assertIsNotNone(master_evaluation_element.name_en)
                self.assertIsNotNone(master_evaluation_element.question_text_en)
                self.assertIsNotNone(master_evaluation_element.explanation_text_en)
                # Check the French fields
                self.assertIsNone(master_evaluation_element.name_fr)
                self.assertIsNone(master_evaluation_element.question_text_fr)
                self.assertIsNone(master_evaluation_element.explanation_text_fr)
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    # Check the master choice English fields is not None
                    self.assertIsNotNone(master_choice.answer_text_en)
                    # Check the master choice French field is None
                    self.assertIsNone(master_choice.answer_text_fr)
                for resource in master_evaluation_element.external_links.all():
                    self.assertIsNotNone(resource.text_en)
                    self.assertIsNone(resource.text_fr)

    def test_import_new_language_en(self):
        """
        Import the French assessment and then add the English version
        """
        treat_and_save_dictionary_data(self.assessment_data_fr)
        assessment = Assessment.objects.get(version="1.0")
        success, message = save_new_assessment_language(self.assessment_data_en, assessment)
        self.assertTrue(success)
        self.assertIsNotNone(assessment.name_fr)
        self.assertIsNotNone(assessment.name_en)
        for master_section in assessment.mastersection_set.all():
            # Check the description of the master section
            self.assertIsNotNone(master_section.name_en)
            self.assertIsNotNone(master_section.name_fr)
            self.assertIsNotNone(master_section.description_fr)
            self.assertIsNotNone(master_section.description_fr)
            self.assertIn("en français", master_section.description_fr)
            self.assertIn("in English", master_section.description_en)
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                # Check the master evaluation element English fields
                self.assertIsNotNone(master_evaluation_element.name_en)
                self.assertIsNotNone(master_evaluation_element.question_text_en)
                self.assertIsNotNone(master_evaluation_element.explanation_text_en)
                # Check the French fields
                self.assertIsNotNone(master_evaluation_element.name_fr)
                self.assertIsNotNone(master_evaluation_element.question_text_fr)
                self.assertIsNotNone(master_evaluation_element.explanation_text_fr)
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    # Check the master choice English fields is not None
                    self.assertIsNotNone(master_choice.answer_text_en)
                    # Check the master choice French field is None
                    self.assertIsNotNone(master_choice.answer_text_fr)
                for resource in master_evaluation_element.external_links.all():
                    self.assertIsNotNone(resource.text_en)
                    self.assertIsNotNone(resource.text_fr)

    def test_import_new_language_fr(self):
        """
        Import the English assessment and then add the French version - almost same test than the previous one
        """
        treat_and_save_dictionary_data(self.assessment_data_en)
        assessment = Assessment.objects.get(version="1.0")
        success, message = save_new_assessment_language(self.assessment_data_fr, assessment)
        self.assertTrue(success)
        self.assertIsNotNone(assessment.name_fr)
        self.assertIsNotNone(assessment.name_en)
        for master_section in assessment.mastersection_set.all():
            # Check the description of the master section
            self.assertIsNotNone(master_section.name_en)
            self.assertIsNotNone(master_section.name_fr)
            self.assertIsNotNone(master_section.description_fr)
            self.assertIsNotNone(master_section.description_fr)
            self.assertIn("en français", master_section.description_fr)
            self.assertIn("in English", master_section.description_en)
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                # Check the master evaluation element English fields
                self.assertIsNotNone(master_evaluation_element.name_en)
                self.assertIsNotNone(master_evaluation_element.question_text_en)
                self.assertIsNotNone(master_evaluation_element.explanation_text_en)
                # Check the French fields
                self.assertIsNotNone(master_evaluation_element.name_fr)
                self.assertIsNotNone(master_evaluation_element.question_text_fr)
                self.assertIsNotNone(master_evaluation_element.explanation_text_fr)
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    # Check the master choice English fields is not None
                    self.assertIsNotNone(master_choice.answer_text_en)
                    # Check the master choice French field is None
                    self.assertIsNotNone(master_choice.answer_text_fr)
                for resource in master_evaluation_element.external_links.all():
                    self.assertIsNotNone(resource.text_en)
                    self.assertIsNotNone(resource.text_fr)


class AssessmentLanguageTestCase(TestCase):
    """
    Test the Assessment methods linked to the language: available languages, delete a language
    """

    def setUp(self):
        with open(
                "assessment/tests/import_test_files/assessment_test_fr_v1.json"
        ) as json_file:
            self.assessment_data_fr = json.load(json_file)
        json_file.close()
        with open(
                "assessment/tests/import_test_files/assessment_test_en_v1.json"
        ) as json_file_en:
            self.assessment_data_en = json.load(json_file_en)
        json_file_en.close()

    def import_the_assessment_in_both_languages(self):
        treat_and_save_dictionary_data(self.assessment_data_fr)
        assessment = Assessment.objects.get(version="1.0")
        save_new_assessment_language(self.assessment_data_en, assessment)
        return assessment

    def test_assessment_get_available_languages(self):
        treat_and_save_dictionary_data(self.assessment_data_fr)
        assessment = Assessment.objects.get(version="1.0")
        self.assertEqual(assessment.get_the_available_languages(), ["fr"])
        save_new_assessment_language(self.assessment_data_en, assessment)
        self.assertIn("fr", assessment.get_the_available_languages())
        self.assertIn("en", assessment.get_the_available_languages())

    def test_assessment_get_available_languages_bis(self):
        """
        Same test than the previous one but with a different order, first import English assessment
        """
        treat_and_save_dictionary_data(self.assessment_data_en)
        assessment = Assessment.objects.get(version="1.0")
        self.assertEqual(assessment.get_the_available_languages(), ["en"])
        save_new_assessment_language(self.assessment_data_fr, assessment)
        self.assertIn("fr", assessment.get_the_available_languages())
        self.assertIn("en", assessment.get_the_available_languages())

    def test_assessment_delete_en(self):
        """
        Test the raw method delete_english_language
        """
        assessment = self.import_the_assessment_in_both_languages()
        self.assertIn("en", assessment.get_the_available_languages())
        assessment.delete_language("en")
        self.assertEqual(["fr"], assessment.get_the_available_languages())
        self.assertEqual(assessment.name, assessment.name_fr)
        # Check that the English field name is empty
        self.assertIsNone(assessment.name_en)
        # Check also on the master section
        for master_section in assessment.mastersection_set.all():
            self.assertIsNotNone(master_section.name_fr)
            self.assertIsNone(master_section.name_en)
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                # Check the master evaluation element French fields
                self.assertIsNotNone(master_evaluation_element.name_fr)
                self.assertIsNotNone(master_evaluation_element.question_text_fr)
                self.assertIsNotNone(master_evaluation_element.explanation_text_fr)
                # Check the English fields
                self.assertIsNone(master_evaluation_element.name_en)
                self.assertIsNone(master_evaluation_element.question_text_en)
                self.assertIsNone(master_evaluation_element.explanation_text_en)
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    # Check the master choice French fields is not None
                    self.assertIsNotNone(master_choice.answer_text_fr)
                    # Check the master choice English field is None
                    self.assertIsNone(master_choice.answer_text_en)
                for resource in master_evaluation_element.external_links.all():
                    self.assertIsNotNone(resource.text_fr)
                    self.assertIsNone(resource.text_en)

    def test_assessment_delete_fr(self):
        """
        Test the raw method delete_french_language
        """
        assessment = self.import_the_assessment_in_both_languages()
        self.assertIn("fr", assessment.get_the_available_languages())
        assessment.delete_language("fr")
        self.assertNotIn("fr", assessment.get_the_available_languages())
        self.assertEqual(assessment.name, assessment.name_en)
        self.assertIsNone(assessment.name_fr)
        for master_section in assessment.mastersection_set.all():
            # Check that the name responds well
            self.assertIsNotNone(master_section.name_en)
            self.assertIsNone(master_section.name_fr)
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                # Check the master evaluation element English fields
                self.assertIsNotNone(master_evaluation_element.name_en)
                self.assertIsNotNone(master_evaluation_element.question_text_en)
                self.assertIsNotNone(master_evaluation_element.explanation_text_en)
                # Check the French fields
                self.assertIsNone(master_evaluation_element.name_fr)
                self.assertIsNone(master_evaluation_element.question_text_fr)
                self.assertIsNone(master_evaluation_element.explanation_text_fr)
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    # Check the master choice English fields is not None
                    self.assertIsNotNone(master_choice.answer_text_en)
                    # Check the master choice French field is None
                    self.assertIsNone(master_choice.answer_text_fr)
                for resource in master_evaluation_element.external_links.all():
                    self.assertIsNotNone(resource.text_en)
                    self.assertIsNone(resource.text_fr)

    def test_delete_language(self):
        assessment = self.import_the_assessment_in_both_languages()
        self.assertIn("en", assessment.get_the_available_languages())
        assessment.delete_language("en")
        self.assertEqual(assessment.get_the_available_languages(), ["fr"])
        save_new_assessment_language(self.assessment_data_en, assessment)
        self.assertIn("en", assessment.get_the_available_languages())
        self.assertIn("fr", assessment.get_the_available_languages())
        assessment.delete_language("fr")
        self.assertEqual(assessment.get_the_available_languages(), ["en"])

    def test_delete_language_should_fail(self):
        assessment = self.import_the_assessment_in_both_languages()
        assessment.delete_language("en")
        self.assertEqual(assessment.get_the_available_languages(), ["fr"])
        # Cannot delete French as this is the only remaining language
        with self.assertRaises(Exception):
            assessment.delete_language("fr")

    def test_delete_language_unknown(self):
        assessment = self.import_the_assessment_in_both_languages()
        self.assertIn("en", assessment.get_the_available_languages())
        self.assertIn("fr", assessment.get_the_available_languages())
        assessment.delete_language("de")
        self.assertIn("en", assessment.get_the_available_languages())
        self.assertIn("fr", assessment.get_the_available_languages())


class FailsImportAssessmentLanguageTestCase(TestCase):
    """
    Test the cases where the import of the new language should fail.
    Note that the function create_assessment_body() has the same base for the first language or an addition so
    I will not test the structure of the json. For this, please refer to the test_import.py file.

    As shown above, this is equivalent to import first French assessment and add English language or the opposite.
    So I will do the tests only with French assessment import and then adding the English one.
    """

    def setUp(self):
        with open(
                "assessment/tests/import_test_files/assessment_test_fr_v1.json"
        ) as json_file:
            self.assessment_data_fr = json.load(json_file)
        json_file.close()
        treat_and_save_dictionary_data(self.assessment_data_fr)
        self.assessment = Assessment.objects.get(version="1.0")
        with open(
                "assessment/tests/import_test_files/assessment_test_en_v1.json"
        ) as json_file_en:
            self.assessment_data_en = json.load(json_file_en)
        json_file_en.close()

    def tearDown(self):
        del self.assessment_data_fr
        del self.assessment_data_en
        for assessment in Assessment.objects.all():
            assessment.delete()

    def test_clean_failed_assessment_import(self):
        """
        Test that when adding a language fails, there is no trace of that language in the DB
        """
        save_new_assessment_language(self.assessment_data_en, self.assessment)
        self.assertTrue(self.assessment.check_has_language("en"))
        clean_failed_assessment_import(self.assessment, "en", first_language=False)
        self.assertFalse(self.assessment.check_has_language("en"))
        # todo tests for all the fields + refactor with the tests before

    def test_no_language(self):
        del self.assessment_data_en["language"]
        self.assertFalse(save_new_assessment_language(self.assessment_data_en, self.assessment)[0])
        self.assertIn(
            "You need to provide the language of the assessment as key of the json",
            save_new_assessment_language(self.assessment_data_en, self.assessment)[1],
        )
        self.assertIsNone(self.assessment.name_en)
        self.assertIsNotNone(self.assessment.name_fr)

    def test_add_language_bad_language_key(self):
        """
        Bad key language (example "de")
        """
        self.assessment_data_en["language"] = "de"
        self.assertFalse(save_new_assessment_language(self.assessment_data_en, self.assessment)[0])
        self.assertIn(
            "There is an issue with the language, expected 'en'",
            save_new_assessment_language(self.assessment_data_en, self.assessment)[1],
        )
        self.assertIsNone(self.assessment.name_en)
        self.assertIsNotNone(self.assessment.name_fr)

    def test_add_language_already_existing(self):
        """
        Key language already in DB (fr)
        """
        self.assessment_data_en["language"] = "fr"
        self.assertFalse(save_new_assessment_language(self.assessment_data_en, self.assessment)[0])
        self.assertIn(
            "The language you want to import (fr) already exists for the assessment,",
            save_new_assessment_language(self.assessment_data_en, self.assessment)[1],
        )
        self.assertIsNone(self.assessment.name_en)
        self.assertIsNotNone(self.assessment.name_fr)

    def test_add_language_not_same_version(self):
        """
        Not the same version (regardless the version value)
        """
        self.assessment_data_en["version"] = "aaa"
        self.assertFalse(save_new_assessment_language(self.assessment_data_en, self.assessment)[0])
        self.assertIn(
            "You need to furnish an assessment with the same version than",
            save_new_assessment_language(self.assessment_data_en, self.assessment)[1],
        )
        self.assertIsNone(self.assessment.name_en)
        self.assertIsNotNone(self.assessment.name_fr)

    def test_add_language_no_version(self):
        """
        Not the same version (regardless the version value)
        """
        self.assessment_data_en["version"] = "aaa"
        self.assertFalse(save_new_assessment_language(self.assessment_data_en, self.assessment)[0])
        self.assertIn(
            "You need to furnish an assessment with the same version than",
            save_new_assessment_language(self.assessment_data_en, self.assessment)[1],
        )
        self.assertIsNone(self.assessment.name_en)
        self.assertIsNotNone(self.assessment.name_fr)

    def test_add_language_no_name(self):
        """
        Remove name from the data
        """
        del self.assessment_data_en["name"]
        self.assertFalse(save_new_assessment_language(self.assessment_data_en, self.assessment)[0])
        self.assertIn(
            "You need to provide a name for the assessment",
            save_new_assessment_language(self.assessment_data_en, self.assessment)[1],
        )
        self.assertIsNone(self.assessment.name_en)
        self.assertIsNotNone(self.assessment.name_fr)

    def test_adding_language_missing_object(self):
        del self.assessment_data_en["sections"]["section 2"]
        self.assertFalse(save_new_assessment_language(self.assessment_data_en, self.assessment)[0])
        self.assertIn(
            "There are missing objects in the json, all the objects have not the translation they should",
            save_new_assessment_language(self.assessment_data_en, self.assessment)[1],
        )
        self.assertIsNone(self.assessment.name_en)
        self.assertIsNotNone(self.assessment.name_fr)

    def test_adding_language_extra_object(self):
        """
        Delete the 2nd section of the assessment t have virtually one more section in the English json
        """
        master_section_2 = MasterSection.objects.get(assessment=self.assessment, order_id="2")
        master_section_2.delete()
        self.assertFalse(save_new_assessment_language(self.assessment_data_en, self.assessment)[0])
        self.assertIn(
            "There is an issue with the master section",
            save_new_assessment_language(self.assessment_data_en, self.assessment)[1],
        )
        self.assertIsNone(self.assessment.name_en)
        self.assertIsNotNone(self.assessment.name_fr)
