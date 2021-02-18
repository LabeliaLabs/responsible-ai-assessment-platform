import json

from django.test import TestCase
from django.utils.translation import activate

from assessment.models import (
    Assessment,
    MasterSection,
    is_language_activation_allowed, ManageAssessmentTranslation,
)
from assessment.import_assessment import ImportAssessment


class ImportAssessmentLanguageTestCase(TestCase):
    """
    Test that the assessment is well imported in one language and that the functions to add the new language work well
    """

    def setUp(self):
        with open(
                "assessment/tests/import_test_files/assessment_test_v1.json"
        ) as json_file:
            self.assessment_data = json.load(json_file)
        json_file.close()

    def tearDown(self):
        del self.assessment_data
        for assessment in Assessment.objects.all():
            assessment.delete()

    def test_import_fr(self):
        self.assertTrue(ImportAssessment(self.assessment_data).success)

    def test_import_assessment_and_check_some_field_values(self):
        """
        Test the assessment import depending on the language and that all the fields which need translation are
        well translated and that they do not exist in the other languages
        """
        import_assessment = ImportAssessment(self.assessment_data)
        self.assertTrue(import_assessment.success)
        assessment = import_assessment.assessment
        # Activate French language
        activate("fr")
        # Check that the assessment name is the same value than the French one
        self.assertEqual(assessment.name, assessment.name_fr)
        self.assertEqual("assessment fr", assessment.name)
        # Check also on the master section
        master_section1 = MasterSection.objects.first()
        self.assertEqual(master_section1.name, "section 1 fr")
        self.assertEqual(master_section1.keyword, "Protection des données")
        activate('en')
        self.assertEqual("assessment en", assessment.name)
        self.assertEqual(master_section1.name, "section 1 en")
        self.assertEqual(master_section1.keyword, "Data protection")

    def test_import_assessment_translated_fields(self):
        """
        For each field registered in translation.py and for each object of the assessment,
        we check that the values are not None in the different languages (fr and en)
        """
        import_assessment = ImportAssessment(self.assessment_data)
        self.assertTrue(import_assessment.success)
        assessment = import_assessment.assessment
        dic_translated_fields = ManageAssessmentTranslation().dic_translated_fields
        # For all the fields which have a translation in the Assessment class, check if they are not None
        for fields in dic_translated_fields["assessment"]:
            self.assertTrue(getattr(assessment, fields + "_fr"))
            self.assertTrue(getattr(assessment, fields + "_en"))
        # Check that all the fields of MasterSection which are registered to have a translation,
        # are not None for the language
        for master_section in assessment.mastersection_set.all():
            for fields in dic_translated_fields["master_section"]:
                self.assertTrue(getattr(master_section, fields + "_fr"))
                self.assertTrue(getattr(master_section, fields + "_en"))
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                for fields in dic_translated_fields["master_evaluation_element"]:
                    self.assertTrue(getattr(master_evaluation_element, fields + "_fr"))
                    self.assertTrue(getattr(master_evaluation_element, fields + "_en"))
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    for fields in dic_translated_fields["master_choice"]:
                        self.assertTrue(getattr(master_choice, fields + "_fr"))
                        self.assertTrue(getattr(master_choice, fields + "_en"))
                for external_link in master_evaluation_element.external_links.all():
                    for fields in dic_translated_fields["external_link"]:
                        self.assertTrue(getattr(external_link, fields + "_fr"))
                        self.assertTrue(getattr(external_link, fields + "_en"))


class AssessmentLanguageTestCase(TestCase):
    """
    Test the Assessment methods linked to the language: available languages, delete a language
    """

    def setUp(self):
        with open(
                "assessment/tests/import_test_files/assessment_test_v1.json"
        ) as json_file:
            self.assessment_data = json.load(json_file)
        json_file.close()
        import_assessment = ImportAssessment(self.assessment_data)
        self.assessment = import_assessment.assessment

    def test_assessment_get_available_languages(self):
        self.assertIn("fr", self.assessment.get_the_available_languages())
        self.assertIn("en", self.assessment.get_the_available_languages())

    def test_is_language_activation_allowed(self):
        self.assertTrue(is_language_activation_allowed())

    def test_assessment_delete_en(self):
        """
        Test the raw method delete_english_language
        """
        self.assertIn("en", self.assessment.get_the_available_languages())
        self.assessment.delete_language("en")
        self.assertEqual(["fr"], self.assessment.get_the_available_languages())
        self.assertEqual(self.assessment.name, self.assessment.name_fr)
        # Check that the English field name is empty
        self.assertIsNone(self.assessment.name_en)

        dic_translated_fields = ManageAssessmentTranslation().dic_translated_fields
        # Check also on the master section
        for master_section in self.assessment.mastersection_set.all():
            for fields in dic_translated_fields["master_section"]:
                self.assertTrue(getattr(master_section, fields + "_fr"))
                self.assertFalse(getattr(master_section, fields + "_en"))
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                for fields in dic_translated_fields["master_evaluation_element"]:
                    self.assertTrue(getattr(master_evaluation_element, fields + "_fr"))
                    self.assertFalse(getattr(master_evaluation_element, fields + "_en"))
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    for fields in dic_translated_fields["master_choice"]:
                        self.assertTrue(getattr(master_choice, fields + "_fr"))
                        self.assertFalse(getattr(master_choice, fields + "_en"))
                for external_link in master_evaluation_element.external_links.all():
                    for fields in dic_translated_fields["external_link"]:
                        self.assertTrue(getattr(external_link, fields + "_fr"))
                        self.assertFalse(getattr(external_link, fields + "_en"))

    def test_assessment_delete_fr(self):
        """
        Test the raw method delete_english_language
        """
        self.assertIn("fr", self.assessment.get_the_available_languages())
        self.assessment.delete_language("fr")
        self.assertEqual(["en"], self.assessment.get_the_available_languages())
        self.assertEqual(self.assessment.name, self.assessment.name_en)
        # Check that the English field name is empty
        self.assertIsNone(self.assessment.name_fr)

        dic_translated_fields = ManageAssessmentTranslation().dic_translated_fields
        # Check also on the master section
        for master_section in self.assessment.mastersection_set.all():
            for fields in dic_translated_fields["master_section"]:
                self.assertTrue(getattr(master_section, fields + "_en"))
                self.assertFalse(getattr(master_section, fields + "_fr"))
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                for fields in dic_translated_fields["master_evaluation_element"]:
                    self.assertTrue(getattr(master_evaluation_element, fields + "_en"))
                    self.assertFalse(getattr(master_evaluation_element, fields + "_fr"))
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    for fields in dic_translated_fields["master_choice"]:
                        self.assertTrue(getattr(master_choice, fields + "_en"))
                        self.assertFalse(getattr(master_choice, fields + "_fr"))
                for external_link in master_evaluation_element.external_links.all():
                    for fields in dic_translated_fields["external_link"]:
                        self.assertTrue(getattr(external_link, fields + "_en"))
                        self.assertFalse(getattr(external_link, fields + "_fr"))

    def test_delete_language_should_fail(self):
        self.assessment.delete_language("en")
        self.assertEqual(self.assessment.get_the_available_languages(), ["fr"])
        # Cannot delete French as this is the only remaining language
        with self.assertRaises(Exception):
            self.assessment.delete_language("fr")

    def test_delete_language_unknown(self):
        self.assertIn("en", self.assessment.get_the_available_languages())
        self.assertIn("fr", self.assessment.get_the_available_languages())
        self.assessment.delete_language("de")
        self.assertIn("en", self.assessment.get_the_available_languages())
        self.assertIn("fr", self.assessment.get_the_available_languages())
