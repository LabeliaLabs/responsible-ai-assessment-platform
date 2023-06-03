import itertools

from django.conf import settings
from django.db import models

# Define as a constant as issue ith circular imports
# Do not register 'risk_domain' field of MasterEvaluationElement
TRANSLATED_FIELDS = {
    "assessment": ["name"],
    "master_section": ["name", "description", "keyword"],
    "master_evaluation_element": ["name", "question_text", "explanation_text"],
    "master_choice": ["answer_text"],
    "external_link": ["text"],
}


def get_last_assessment_created():
    """Get the last assessment created - If no assessment in DB, returns None"""

    if len(list(Assessment.objects.all().order_by("-created_at"))) > 0:
        return list(Assessment.objects.all().order_by("-created_at"))[0]
    else:
        return None


class Assessment(models.Model):
    """The class Assessment represents the object assessment with
    an ID, a name, a version and a date of creation and a date of last update
    This class stores the static information concerning the assessment (version)
    """

    name = models.CharField(max_length=100)
    version = models.CharField(max_length=200, default="mvp", unique=True)
    previous_assessment = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, default=None
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.name and self.version:
            return f"{self.name} - V{str(self.version)}"
        else:
            return f"Assessment {str(self.pk)}"

    def get_list_all_choices(self):
        """
        Returns a list of all the choices of the assessment (used to create upgrade json for example)
        :return:
        """
        list_all_choices = []
        for master_section in self.mastersection_set.all().order_by("order_id"):
            for master_element in master_section.masterevaluationelement_set.all().order_by(
                "order_id"
            ):
                for master_choice in master_element.masterchoice_set.all().order_by(
                    "order_id"
                ):
                    list_all_choices.append(master_choice.get_numbering())
        return list_all_choices

    def get_master_sections_list(self):
        return list(self.mastersection_set.all())

    def count_master_elements_with_risks(self):
        """
        Count all the risk domains defined in the assessment
        """
        list_risks = [
            [
                master_element.risk_domain_fr
                for master_element in master_section.masterevaluationelement_set.all()
                if master_element.risk_domain
            ]
            for master_section in self.mastersection_set.all()
        ]
        flatten_list = list(itertools.chain.from_iterable(list_risks))
        # Set remove the duplicates
        return len(set(flatten_list))

    def get_the_available_languages(self):
        """
        This method returns the list of the languages for the assessment, based on those
        which are registered in the settings
        """
        language_list = []
        for language in get_available_languages():
            if self.check_has_language(language):
                language_list.append(language)
        return language_list

    def check_has_language(self, language):
        """
        Check for each layer of the assessment (Assessment, MasterSection, MasterEvaluationElement, MasterChoice) and
        for the External Link that the fields which are registered to have a translation, are not None
        for the language.
        Returns True if all the fields are not None, else False
        """
        dic = TRANSLATED_FIELDS
        # For all the fields which have a translation in the Assessment class, check if they are not None
        for field in dic["assessment"]:
            if not getattr(self, field + "_" + language):
                return False
        # Check that all the fields of MasterSection which are registered to have a translation,
        # are not None for the language
        for master_section in self.mastersection_set.all():
            for field in dic["master_section"]:
                if not getattr(master_section, field + "_" + language):
                    return False
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                for field in dic["master_evaluation_element"]:
                    if (
                        not getattr(master_evaluation_element, field + "_" + language)
                        and master_evaluation_element.get_numbering() != "2.2"
                    ):
                        return False
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    for field in dic["master_choice"]:
                        if not getattr(master_choice, field + "_" + language):
                            return False
                for external_link in master_evaluation_element.external_links.all():
                    for field in dic["external_link"]:
                        if not getattr(external_link, field + "_" + language):
                            return False
        return True

    def get_fields_not_translated(self, language):
        """
        Check for each layer of the assessment (Assessment, MasterSection, MasterEvaluationElement, MasterChoice) and
        for the External Link that the fields which are registered to have a translation, are not None
        for the language. If they are, it is added to the dic_fields, with the obj as key and the field as value.
        The dic is then returned.
        """
        dic_fields = {}
        dic = TRANSLATED_FIELDS
        # For all the fields which have a translation in the Assessment class, check if they are not None
        for field in dic["assessment"]:
            if not getattr(self, field + "_" + language):
                dic_fields[self] = field + "_" + language
        # Check that all the fields of MasterSection which are registered to have a translation,
        # are not None for the language
        for master_section in self.mastersection_set.all():
            for field in dic["master_section"]:
                if not getattr(master_section, field + "_" + language):
                    dic_fields[master_section] = field + "_" + language
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                for field in dic["master_evaluation_element"]:
                    if (
                        not getattr(master_evaluation_element, field + "_" + language)
                        and master_evaluation_element.get_numbering() != "2.2"
                    ):
                        dic_fields[master_evaluation_element] = field + "_" + language
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    for field in dic["master_choice"]:
                        if not getattr(master_choice, field + "_" + language):
                            dic_fields[master_choice] = field + "_" + language
                for external_link in master_evaluation_element.external_links.all():
                    for field in dic["external_link"]:
                        if not getattr(external_link, field + "_" + language):
                            dic_fields[external_link] = field + "_" + language
        return dic_fields

    def delete_language(self, language):
        """
        This method sets all the fields of the assessment and its body which are in the language to None, the default
        value when the language is not registered.
        Requires that there are at least 2 languages for the assessment.
        """
        # The assessment needs at least to contain the field "name" in the language
        if language in self.get_the_available_languages():
            if len(self.get_the_available_languages()) > 1:
                self.clean_assessment_language(language)
            else:
                raise ValueError(
                    f"You cannot delete the language {language} as the assessment must have at least one language."
                )

    def clean_assessment_language(self, language):
        """
        This method sets all the fields of the assessment and its body which are in the language to None.
        Not that no check is done.
        """
        delete_language_translation_field(self, "assessment", language)
        for master_section in self.mastersection_set.all():
            delete_language_translation_field(master_section, "master_section", language)
            for master_evaluation_element in master_section.masterevaluationelement_set.all():
                delete_language_translation_field(
                    master_evaluation_element, "master_evaluation_element", language
                )
                for master_choice in master_evaluation_element.masterchoice_set.all():
                    delete_language_translation_field(master_choice, "master_choice", language)
                for resource in master_evaluation_element.external_links.all():
                    delete_language_translation_field(resource, "external_link", language)


def delete_language_translation_field(obj, obj_name, lang):
    """
    Set the translation to None for all the fields of the object obj.
    The fields are registered in the dic_translation_fields, obj_name mus be a key of this dictionary

    :param obj: object from a class model (Assessment, MasterSection, etc)
    :param obj_name: string, name of the object type ("assessment", "master_section"), must be a key of the dictionary
    :param lang: string, key of the language, either "fr" or "en"
    """
    dic_translated_fields = TRANSLATED_FIELDS
    if lang in get_available_languages():
        if obj_name in dic_translated_fields.keys():
            for fields in dic_translated_fields[obj_name]:
                setattr(obj, fields + "_" + lang, None)
            obj.save()
        else:
            raise KeyError(
                f"The obj_name {obj_name} is not a key of the dictionary of translated fields,"
                f"available keys: {dic_translated_fields.keys()}"
            )


def get_available_languages():
    """
    This function returns the available languages according to the settings, ex ["fr", "en"]
    """
    return [lang[0] for lang in settings.LANGUAGES]


def is_language_activation_allowed():
    """
    This function covers the assessments of the database and check if they are present in the available languages.
    If they are, return 1, else, return 0 - number instead booleans because it is used in js.
    This is used to display or not a warning in the admin interface when the user activate languages.
    """
    assessment_query = Assessment.objects.all()
    available_languages = get_available_languages()
    for assessment in assessment_query:
        if available_languages != assessment.get_the_available_languages():
            return 0
    return 1
