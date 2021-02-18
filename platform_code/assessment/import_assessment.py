import re

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from .models import (
    Assessment,
    MasterChoice,
    MasterSection,
    MasterEvaluationElement,
    ExternalLink,
    ScoringSystem,
    EvaluationElementWeight,
    Upgrade,
    get_last_assessment_created,
)


class ImportAssessment:
    """
    Class which manages the import of the assessment data.

    First check the data with the method check_dic_data (approx 0.03 seconds on personal computer),
    so if there is an issue in the data structure it is fastly caught and we do not import the assessment objects.

    Then, if all the checks are ok, the assessment data are imported (approx 170 times longer).
    The data do not need to be checked as it has been done before, except for the condition inter elements
    and the uniqueness of the choices, which are the 2 cases the method process import can be interrupted and
    the assessment deleted.
    """

    def __init__(self, data_dic):
        self.data_dic = data_dic
        self.assessment = None
        self.success = True
        self.message = "The assessment has been imported!"
        self.check_dic_data()
        if self.success:
            self.process_import()

    def check_dic_data(self):
        try:
            self.check_assessment()
        except Exception as e:
            # Just to do not have a bare except
            self.message = f" Error: {e}."
            self.success = False

    def process_import(self):
        self.assessment = self.create_assessment()
        # In case we need to create the scoring system
        scoring_system_dic = {}
        # In case, for the elements weight
        dic_elements_weight = {}
        dic_sections = self.data_dic.get("sections")
        for section_data in list(dic_sections.values()):
            section = create_section(section_data, self.assessment)
            dic_elements = section_data.get("elements")
            for element_data in list(dic_elements.values()):
                depends_on = self.manage_conditions_inter_elements(element_data)
                # If the condition inter did not fail
                if not self.success:
                    return None
                element = create_element(element_data, section, depends_on)
                # Add the resources of the element
                add_resources(element_data, element)
                # Add the default element weight to the dictionary
                dic_elements_weight[element.get_numbering()] = "1"
                dic_choices = element_data.get("answer_items")
                for choice_data in list(dic_choices.values()):
                    choice = create_choice(choice_data, element)
                    self.verify_choice(choice, scoring_system_dic)
                    if not self.success:
                        return None
                    scoring_system_dic[choice.get_numbering()] = "0"
        self.manage_evaluation_elements_weight_creation(dic_elements_weight)
        self.manage_scoring_system(scoring_system_dic)

    def check_assessment(self):
        """
        This function is used when we want to import a json (the assessment).
        The argument is a dictionary which comes from a json file and represents all the assessment
        dictionary, with data for both the French and English languages
        A success (boolean) is returned, init to false, and a message
        :return: tuple (boolean and string)
        """
        keys_list = ["name_fr", "name_en", "sections", "version"]
        if not test_keys_in_dic(dic=self.data_dic, keys_list=keys_list):
            self.message = f"You have missing keys for the assessment data, please provide {keys_list}"
            raise Exception(self.message)

        version = self.data_dic["version"]

        # If there already is an assessment with the same version, raise error and ask for change if it is the same
        # language
        if list(Assessment.objects.filter(version=version)):
            self.message = "There already is an assessment with this version for this language. Please change it."
            raise Exception(self.message)
        # The version must be convertible into float value (example '0.5', '1.0', etc)
        try:
            float(version)
        except ValueError as e:
            self.message = f"Error {e}. The version must not contain letters. It should be convertible into a float " \
                           f"('0.5', '1.0', etc). The version you provided was '{version}'",
            raise Exception(self.message)

        if float(version) <= 0:
            self.message = "The version must be convertible into a positive number"
            raise Exception(self.message)
        if get_last_assessment_created():
            if float(version) < float(get_last_assessment_created().version):
                self.message = f"The assessment version must not be smaller than the" \
                               f" assessment versions already in the DB" \
                               f"The new assessment version is {version} and the latest in th DB" \
                               f" is {get_last_assessment_created().version}",
                raise Exception(self.message)

        for section in list(self.data_dic["sections"].keys()):
            self.check_section(self.data_dic["sections"].get(section))

    def check_section(self, section_data):
        """
        Do the checks for the choice data:
            - all the keys are present
            - order_id is a string convertible into a integer

        and then call the check of the elements
        """
        key_list = ["order_id", "name_fr", "name_en", "keyword_fr", "keyword_en",
                    "description_fr", "description_en", "elements"]
        if not test_keys_in_dic(section_data, keys_list=key_list):
            self.message = f"You have a section without the required keys {key_list}"
            raise Exception(self.message)

        if not test_order_id_number(section_data.get("order_id")):
            self.message = f"The section id is not an integer for this section {section_data}"
            raise Exception(self.message)

        for element in section_data.get("elements").keys():
            self.check_element(section_data.get("elements").get(element))

    def check_element(self, element_data):
        """
        Do the checks for the element data:
            - all the keys are present
            - order_id is the string of an integer
            - if there is a condition inter, that the value is a choice numbering like "1.1.a"

        and then call the tests for the choices and the resources
        """
        # Test that the keys are present in the dictionary
        key_list = ["order_id", "name_fr", "name_en", "condition", "question_text_fr", "question_text_en",
                    "question_type", "answer_items", "explanation_text_fr", "explanation_text_en", "resources"]
        if not test_keys_in_dic(element_data, keys_list=key_list):
            self.message = f"You have an element {element_data} without the required keys {key_list}"
            raise Exception(self.message)

        # Test that the order id is a string convertible into a number
        if not test_order_id_number(element_data.get("order_id")):
            self.message = f"The order_id is not an convertible into an integer for this element {element_data}"
            raise Exception(self.message)

        # Test if there is a condition inter, that it does respect the format (ex "1.5.a")
        if element_data.get("condition") != "n/a" and not test_choice_numbering(element_data.get("condition")):
            self.message = f"You have a condition for a choice which the numbering is" \
                           f" not respected {element_data.get('condition')}. Please follow th format '1.1.a'"
            raise Exception(self.message)

        for choice in list(element_data["answer_items"].keys()):
            self.check_choice(element_data.get("answer_items").get(choice))
        for resource_data in list(element_data["resources"].values()):
            self.check_resource(resource_data)

    def check_choice(self, choice_data):
        """
        DO the check for the choice data:
            - all the keys are present
            - the order id is a lowercase letter
        """
        key_list = ["order_id", "answer_text_fr", "answer_text_en", "is_concerned_switch"]

        if not test_keys_in_dic(choice_data, keys_list=key_list):
            self.message = f"You have a choice {choice_data} without the required keys {key_list}"
            raise Exception(self.message)

        if not test_order_id_letter(choice_data.get("order_id")):
            self.message = f"The order_id of the choice is not a letter {choice_data}"
            raise Exception(self.message)

        if not choice_data.get("is_concerned_switch") in [0, 1, "True", "False"]:
            self.message = f"The choice has not a boolean value for is_concerned_switch {choice_data}"
            raise Exception(self.message)

    def check_resource(self, resource_data):
        """
        Check that the resource fields are in the dictionary
        """
        key_list = ["resource_type", "resource_text_fr", "resource_text_en"]
        if not test_keys_in_dic(resource_data, keys_list=key_list):
            self.message = f"You have a resource {resource_data} without the required keys {key_list}"
            raise Exception(self.message)

    def manage_conditions_inter_elements(self, element_data):
        """
        Manage the case the element has condition inter.
        Try to get the Master Choice which sets the condition if it exists, if it fails, set self.success to False
        and delete the assessment. The import process is stopped.
        Return Master Choice or None
        """
        depends_on = None
        if element_data.get("condition") != "n/a":
            condition = element_data.get("condition").split(".")
            try:
                depends_on = MasterChoice.objects.get(
                    order_id=condition[2],
                    master_evaluation_element__order_id=condition[1],
                    master_evaluation_element__master_section__order_id=condition[0],
                    master_evaluation_element__master_section__assessment=self.assessment,
                )
            except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
                self.success = False
                self.message = f"You have set a condition on a choice which does not exist or which is not " \
                               f"before the evaluation element, error {e}. Choice {element_data.get('condition')}"
                self.assessment.delete()
                return depends_on
        return depends_on

    def verify_choice(self, choice, dic_choices):
        """
        Verify that the new choice has not already the same numbering in the dic_choices
        ie verify the order_id uniqueness
        """
        if choice.get_numbering() in dic_choices:
            self.success = False
            self.message = f"You have duplicate choice numbering so please verify your " \
                           f"order_id {choice.get_numbering()}"
            self.assessment.delete()

    def create_assessment(self):
        assessment = Assessment(
            version=self.data_dic['version'],
            name_fr=self.data_dic["name_fr"],
            name_en=self.data_dic["name_en"]
        )
        assessment.save()
        return assessment

    def manage_scoring_system(self, dic_choices):
        """
        If there is not a scoring system linked to the assessment, one is created
        """
        if not list(ScoringSystem.objects.filter(assessment=self.assessment)):
            scoring = ScoringSystem(
                assessment=self.assessment,
                name="choice_scoring_of_" + self.assessment.name_fr,
                master_choices_weight_json=dic_choices,
            )
            scoring.save()

    def manage_evaluation_elements_weight_creation(self, dic_elements):
        """
        If there is not already an evaluation element weight dic affected to the assessment, one is created,
        with only ones is
        """
        if not list(EvaluationElementWeight.objects.filter(assessment=self.assessment)):
            element_weight = EvaluationElementWeight(
                assessment=self.assessment,
                name="element_weight_of_" + self.assessment.name,
                master_evaluation_element_weight_json=dic_elements,
            )
            element_weight.save()


def create_section(section_data, assessment):
    section = MasterSection(
        assessment=assessment,
        name_fr=section_data.get("name_fr"),
        name_en=section_data.get("name_en"),
        keyword_fr=section_data.get("keyword_fr"),
        keyword_en=section_data.get("keyword_en"),
        order_id=section_data.get("order_id"),
        description_fr=section_data.get("description_fr"),
        description_en=section_data.get("description_en"),
    )
    section.save()
    return section


def create_element(element_data, section, depends_on):

    element = MasterEvaluationElement(
        master_section=section,
        name_fr=element_data.get("name_fr"),
        name_en=element_data.get("name_en"),
        order_id=element_data.get("order_id"),
        question_text_fr=element_data.get("question_text_fr"),
        question_text_en=element_data.get("question_text_en"),
        question_type=element_data.get("question_type"),
        explanation_text_fr=element_data.get("explanation_text_fr").replace("n/a", ""),
        explanation_text_en=element_data.get("explanation_text_fr").replace("n/a", ""),
        depends_on=depends_on,
    )
    element.save()
    return element


def create_choice(choice_data, element):
    choice = MasterChoice(
        master_evaluation_element=element,
        order_id=choice_data.get("order_id"),
        answer_text_fr=choice_data.get("answer_text_fr"),
        answer_text_en=choice_data.get("answer_text_en"),
        is_concerned_switch=choice_data.get("is_concerned_switch"),
    )
    choice.save()
    return choice


def create_resource(resource_data):
    """
    Create and save the external link (resource)
    """
    resource = ExternalLink(
        text_fr=resource_data.get("resource_text_fr"),
        text_en=resource_data.get("resource_text_en"),
        type=resource_data.get("resource_type"),
    )
    resource.save()
    return resource


def add_resources(element_data, element):
    """
    This method manages the resources of the evaluation element.
    It creates the resources which do not exist yet or it adds it to the evaluation element.
    """
    external_links_element = []
    resources_data_dic = element_data.get("resources")
    if resources_data_dic:
        for resource_data in list(resources_data_dic.values()):
            # If it is not an addition of another language, we check if we need to create the external links
            if not external_link_already_exist(
                    resource_data.get("resource_text_fr"),
                    resource_data.get("resource_type")
            ):
                # Note that there is no condition on the resource type or resource text as
                # it is only markdownify (no need to respect a format with a template tags)
                resource = create_resource(resource_data)

            # Else, it already exists so we get it
            else:
                resource = ExternalLink.objects.get(
                    text_fr=resource_data.get("resource_text_fr"),
                    type=resource_data.get("resource_type"),
                )
            # Add the resource to the list to add it later to the element
            external_links_element.append(resource)
        # After the loop, associate the resources to the master evaluation element (m2m field)
        element.external_links.add(*external_links_element)
        element.save()


def test_keys_in_dic(dic, keys_list):
    """
    Tests for each string in the keys_list (list) if it is a key of the dictionary dic
    Returns a boolean, True is all the objects of the list are keys of the dictionary
    """
    return all(x in dic.keys() for x in keys_list)


def test_order_id_number(order_id):
    """Check if the choice order_id is a string convertible into an integer"""
    if isinstance(order_id, str):
        try:
            int(order_id)
            return True
        except ValueError:
            return False
    else:
        return False


def test_order_id_letter(order_id):
    """Check if the choice order_id is a letter between a and n"""
    reg = re.findall(r"^[a-n]$", order_id)
    return reg != []


def test_choice_numbering(numbering):
    """Check the numbering for a string. It s almost the same principle of test_numbering in the MasterChoice class"""
    reg = re.findall(r"^[0-9]\.[0-9]\.[a-n]$", numbering)
    return reg != []


def external_link_already_exist(text_fr, resource_type):
    """
    Check if there is already a resource in the table ExternalLinks. Return boolean (True if it exists).
    """
    return list(ExternalLink.objects.filter(text_fr=text_fr, type=resource_type)) != []


def check_upgrade(dict_upgrade_data):
    """
    In this function, we gonna check that the upgrade_dic has all the objects of the brand new assessment
    This function returns a boolean, True if the checks are ok, and a message
    :param dict_upgrade_data:
    :return:
    """
    success = False
    message = ""
    # dic differences like {'1.0': {'sections': {'1': '1', '2': '1', '3': '1', '4': 'no_fetch', '5': 'no_fetch',
    # '6': '5', '7': '1'}, 'elements': {'1.1': '1'}, 'answer_items': {'1.1.a': '1', '1.1.b': 'no_fetch'}}}
    list_dic_differences = [
        {key: val} for key, val in dict_upgrade_data["diff_per_version"].items()
    ]
    assessment = get_last_assessment_created()  # check it is the same we just created
    for master_section in assessment.mastersection_set.all():
        for dic_diff in list_dic_differences:
            # We check for each dic version if the section is within. If not, it raises an error
            success, message = check_object_within(
                "sections", master_section, list(dic_diff.values())[0]
            )
            if not success:
                return success, message
        for master_element in master_section.masterevaluationelement_set.all():
            # We check for each dic version if the element is within. If not, it raises an error
            for dic_diff in list_dic_differences:
                success, message = check_object_within(
                    "elements", master_element, list(dic_diff.values())[0]
                )
                if not success:
                    return success, message
            for master_choice in master_element.masterchoice_set.all():
                # We check for each dic version if the choice is within. If not, it raises an error
                for dic_diff in list_dic_differences:
                    # Be careful, it is "answer_items" and not "choices" while it is the same concept
                    success, message = check_object_within(
                        "answer_items", master_choice, list(dic_diff.values())[0]
                    )
                    if not success:
                        return success, message
    return success, "The upgrade json check is ok"


def check_object_within(object_type, object_assessment, dic_diff):
    """
    We check that the object_assessment (section, element or choice) is within the dic_diff
    :param object_type: string, ("sections", "elements", 'choices")
    :param object_assessment: object of the assessment (section, element, choice)
    :param dic_diff: dictionary, like {'sections': {'1': '1', '2': '1', '3': '1', '4': 'no_fetch',
     '5': 'no_fetch', '6': '5', '7': '1'}, 'elements': {'1.1': '1'},
      'answer_items': {'1.1.a': '1.1.a', '1.1.b': 'no_fetch'}}
    :return:
    """
    success = True
    message = ""
    if object_assessment.get_numbering() not in dic_diff[object_type].keys():
        success = False
        message = (
            f"The {object_type} {object_assessment.get_numbering()} of"
            f" the assessment is not in the dictionary of differences for"
            f" the version {dic_diff.keys()}, the {object_type} present are : {dic_diff[object_type].keys()}"
        )
    return success, message


def save_upgrade(dict_upgrade_data):
    """
    This function is used to save the json file we receive in the Upgrade table
    Return the success (boolean) and a message
    :param dict_upgrade_data:
    :return:
    """
    success = True

    # Need to check it is the last created
    final_assessment = get_last_assessment_created()
    list_dic_differences = [
        {key: val} for key, val in dict_upgrade_data["diff_per_version"].items()
    ]
    message = f"{len(list_dic_differences)} upgrade item(s) has/have been created "  # todo use way to format plural
    # We cover all the dic of differences (for each different version) which are in the json
    # And for each, we save the upgrade
    for dic_differences in list_dic_differences:
        version = list(dic_differences.keys())[0]

        try:
            version = str(version)  # be sure it is a string !
            origin_assessment = Assessment.objects.get(version=version)
            upgrade = Upgrade(
                final_assessment=final_assessment,
                origin_assessment=origin_assessment,
                upgrade_json=list(dic_differences.values())[0],
            )
            upgrade.save()
        except ObjectDoesNotExist as e:
            success = False
            message = (
                f"The version {version} in the upgrade json is not an assessment version in the database. "
                f"Error {e}"
            )
    return success, message
