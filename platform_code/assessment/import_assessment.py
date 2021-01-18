import re

from django.utils.translation import activate
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


def treat_and_save_dictionary_data(dic, return_assessment=False):
    """
    This function is used when we want to import a json (the assessment).
    The argument is a dictionary which comes from a json file and represents all the assessment
    dictionary
    A success (boolean) is returned, init to false, and a message
    :param dic:
    :param return_assessment: boolean, if False, return the success (boolean) and the message (string)
    :return: tuple (boolean and string)
    """
    #
    success = False
    # First layer : Assessment data
    try:
        version = dic["version"]
    except KeyError as e:
        return (
            success,
            f"You need to provide an assessment version which could be converted into a float, error {e}",
        )

    # Check if there is the language provided and then if the language is valid
    try:
        language = dic["language"]
    except KeyError as e:
        return (
            success,
            f"You need to provide the language of the assessment as key of the json, error {e}",
        )
    if language not in ["en", "fr"]:
        return (
            success,
            f"The language is not a valid one, it must be 'en' for English or 'fr' for French, "
            f"currently {language}",
        )

    # If there already is an assessment with the same version, raise error and ask for change if it is the same language
    if list(Assessment.objects.filter(version=version)):
        message = "There already is an assessment with this version for this language. Please change it."
        return success, message
    # The version must be convertible into float value (example '0.5', '1.0', etc)
    try:
        float(version)
    except ValueError as e:
        return (
            success,
            f"Error {e}. The version must not contain letters. It should be convertible into a float "
            f"('0.5', '1.0', etc). The version you provided was '{version}'",
        )

    if float(version) <= 0:
        return success, "The version must be convertible into a positive number"
    if get_last_assessment_created():
        if float(version) < float(get_last_assessment_created().version):
            return (
                success,
                f"The assessment version must not be smaller than the"
                f" assessment versions already in the DB"
                f"The new assessment version is {version} and the latest in th DB"
                f" is {get_last_assessment_created().version}",
            )

    if "name" not in dic.keys():
        return success, "You need to provide a name for the assessment"
    name = dic["name"]
    # Otherwise we can create the assessment
    # If the import fails later, we need to delete the assessment
    # We activate the language in which we want to import the assessment (important!!!) otherwise, if the user language
    # is different from the language of the assessment, the main fields ("name") won't be saved, only the fields in the
    # assessment language ("name_fr")
    activate(language)
    assessment = create_assessment(name, version, language)
    success, message = create_assessment_body(
        dic, assessment, language, first_language=True
    )

    # activate(initial_language)  # set the initial language
    if not return_assessment:
        return success, message
    else:
        return assessment


def create_assessment(name, version, language):
    """
    Create the assessment in function of the language
    """
    if language == "fr":
        assessment = Assessment(name_fr=name, version=version)

    else:
        assessment = Assessment(name_en=name, version=version)
    assessment.save()
    return assessment


def add_language_assessment(assessment, name, language):
    """
    Add the name of the assessment in the language (fr or en) and save
    """
    if language == "fr":
        assessment.name_fr = name
    else:
        assessment.name_en = name
    assessment.save()


def create_master_section(assessment, section_data, language):
    """
    Create and save the master_section
    """
    if language == "fr":
        master_section = MasterSection(
            assessment=assessment,
            name_fr=section_data.get("name"),
            order_id=section_data.get("order_id"),
            description_fr=section_data.get("description"),
        )
    else:
        master_section = MasterSection(
            assessment=assessment,
            name_en=section_data.get("name"),
            order_id=section_data.get("order_id"),
            description_en=section_data.get("description"),
        )
    master_section.save()
    return master_section


def add_language_master_section(assessment, section_data, language):
    """
    Add the fields in the language for the master section, with order_id in section_data (tested it exists before)
    """
    master_section = MasterSection.objects.get(
        order_id=section_data.get("order_id"), assessment=assessment
    )
    if language == "fr":
        master_section.name_fr = section_data.get("name")
        master_section.description_fr = section_data.get("description")
    else:
        master_section.name_en = section_data.get("name")
        master_section.description_en = section_data.get("description")
    master_section.save()
    return master_section


def create_master_evaluation_element(
    master_section, element_data, depends_on, language
):
    """
    Create and save the master_evaluation_element
    """
    if language == "fr":
        master_evaluation_element = MasterEvaluationElement(
            master_section=master_section,
            name_fr=element_data.get("name"),
            order_id=element_data.get("order_id"),
            question_text_fr=element_data.get("question_text"),
            question_type=element_data.get("question_type"),
            explanation_text_fr=element_data.get("explanation_text").replace("n/a", ""),
            depends_on=depends_on,
        )
    else:
        master_evaluation_element = MasterEvaluationElement(
            master_section=master_section,
            name_en=element_data.get("name"),
            order_id=element_data.get("order_id"),
            question_text_en=element_data.get("question_text"),
            question_type=element_data.get("question_type"),
            explanation_text_en=element_data.get("explanation_text").replace("n/a", ""),
            depends_on=depends_on,
        )
    master_evaluation_element.save()
    return master_evaluation_element


def add_language_master_evaluation_element(master_section, element_data, language):
    """
    Get the master evaluation element, add the fields in the ne language save it and return it
    """
    master_evaluation_element = MasterEvaluationElement.objects.get(
        order_id=element_data.get("order_id"), master_section=master_section
    )
    if language == "fr":
        master_evaluation_element.name_fr = element_data.get("name")
        master_evaluation_element.question_text_fr = element_data.get("question_text")
        master_evaluation_element.explanation_text_fr = element_data.get(
            "explanation_text"
        )
    else:
        master_evaluation_element.name_en = element_data.get("name")
        master_evaluation_element.question_text_en = element_data.get("question_text")
        master_evaluation_element.explanation_text_en = element_data.get(
            "explanation_text"
        )
    master_evaluation_element.save()
    return master_evaluation_element


def create_master_choice(master_evaluation_element, choice_data, language):
    """
    Create and save the master choice
    """
    if language == "fr":
        master_choice = MasterChoice(
            master_evaluation_element=master_evaluation_element,
            order_id=choice_data.get("order_id"),
            answer_text_fr=choice_data.get("answer_text"),
            is_concerned_switch=choice_data.get("is_concerned_switch"),
        )
    else:
        master_choice = MasterChoice(
            master_evaluation_element=master_evaluation_element,
            order_id=choice_data.get("order_id"),
            answer_text_en=choice_data.get("answer_text"),
            is_concerned_switch=choice_data.get("is_concerned_switch"),
        )
    master_choice.save()
    return master_choice


def add_language_master_choice(master_evaluation_element, choice_data, language):
    """
    Get the master choice, add the fields in the new language and save it.
    It does not return the master choice
    """
    master_choice = MasterChoice.objects.get(
        order_id=choice_data.get("order_id"),
        master_evaluation_element=master_evaluation_element,
    )
    if language == "fr":
        master_choice.answer_text_fr = choice_data.get("answer_text")
    else:
        master_choice.answer_text_en = choice_data.get("answer_text")
    master_choice.save()


def create_external_link(external_link_data, resource_type, language):
    """
    Create and save the external link (resource)
    """
    if language == "fr":
        external_link = ExternalLink(
            text_fr=external_link_data.get("resource_text"),
            type=resource_type,
        )
    else:
        external_link = ExternalLink(
            text_en=external_link_data.get("resource_text"),
            type=resource_type,
        )
    external_link.save()
    return external_link


def add_language_external_link(master_evaluation_element, external_link_data, language):
    """
    We need to find the resource (external link) in the other language, based on the data we have on the new language.
    We suppose that the url is the same in both languages.
    So we get the url by regex, we do a query set on the resources of the evaluation element to get the resource.
    """
    text = external_link_data.get("resource_text")

    # Get the resource url, one among the several a resource text may contain
    # A resource has necessarily an url in the text
    regex_url = re.search(r"\((?P<url>https?.*?)\)", text)
    if regex_url:
        resource_url = regex_url.group("url")
    else:
        raise ValueError(f"The resource {external_link_data} has no link")

    # I do not know why, may be m2m field restriction, but I cannot just do the query on "text__icontains", it fails
    if language == "fr":
        query_resource = master_evaluation_element.external_links.filter(
            text_en__icontains=resource_url
        )
        # It should always get the resource which is unique (the probability of having 2 resources containing
        # the same url for the same master evaluation element is None (or should not exist!)
        resource = query_resource[0]
        resource.text_fr = external_link_data.get("resource_text")
    else:
        query_resource = master_evaluation_element.external_links.filter(
            text_fr__icontains=resource_url
        )
        resource = query_resource[0]
        resource.text_en = external_link_data.get("resource_text")
    resource.save()


def test_order_id_number(order_id):
    """Check if the choice order_id is a string convertible into an integer"""
    if type(order_id) == str:
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


def external_link_already_exist(text, resource_type):
    """
    Check if there is already a resource in the table ExternalLinks. Return boolean (True if it exists).
    """
    return list(ExternalLink.objects.filter(text=text, type=resource_type)) != []


# Import upgrade json part


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


def clean_failed_assessment_import(assessment, language, first_language):
    """
    Delete the assessment if the import fails because it can be created during the process but the latter
    failed after
    :param assessment: assessment
    :param first_language: boolean, True if first language imported and we need to delete the assessment, False if
    it is a new language added
    :param language: string, key of the language ("fr" or "en")
    :return:
    """
    if first_language:
        assessment.delete()
    else:
        assessment.clean_assessment_language(language)


def save_new_assessment_language(dic, assessment):
    """
    This function is used when the user wants to add the assessment in a new language during admin action.
    It checks that the assessment in the file (dict_data) has the save structure than the assessment in the DB.
    If it s ok and the assessment respect the conditions, the assessment objects are updated to have the texts, names,
    descriptions in the new language.
    """
    success = False

    # Study assessment version
    try:
        version = dic["version"]
    except KeyError as e:
        return (
            success,
            f"You need to provide an assessment version which could be converted into a float, error {e}",
        )
    if version != assessment.version:
        return (
            success,
            f"You need to furnish an assessment with the same version than {assessment.version}, "
            f"currently {version}",
        )

    # Check if there is the language provided and then if the language is valid ie the 2nd one available
    try:
        language = dic["language"]
    except KeyError as e:
        return (
            success,
            f"You need to provide the language of the assessment as key of the json, error {e}",
        )
    # Check that the language is not already present
    if language in assessment.get_the_available_languages():
        message = (
            f"The language you want to import ({language}) already exists for the assessment, "
            f"existing languages: {assessment.get_the_available_languages()}"
        )
        return success, message
    # Check that the language imported is not the one already in the DB
    if (
        len(assessment.get_the_available_languages()) == 1
    ):  # should always be the case as it already tested in admin
        if assessment.get_the_available_languages()[0] == "en":
            if language != "fr":
                return (
                    success,
                    f"There is an issue with the language, expected 'fr', get {language}",
                )
        elif assessment.get_the_available_languages()[0] == "fr":
            if language != "en":
                return (
                    success,
                    f"There is an issue with the language, expected 'en', get {language}",
                )

    # If there already is more than one assessment for this version, raise error
    if len(list(Assessment.objects.filter(version=version))) != 1:
        message = (
            f"There is an issue with the assessment and the version, expected one assessment "
            f"with version {version}, get {len(list(Assessment.objects.filter(version=version)))}"
        )
        return success, message

    if "name" not in dic.keys():
        return success, "You need to provide a name for the assessment"

    name = dic["name"]

    add_language_assessment(assessment, name, language)

    # Add the fields of the assessment in the new language
    success, message = create_assessment_body(
        dic, assessment, language, first_language=False
    )

    # In case of success, check that all the objects of the assessment have a translation, if not, there are missing
    if success and not assessment.check_has_language(language):
        dic_missing = assessment.get_fields_not_translated(language)
        assessment.clean_assessment_language(language)
        return (
            False,
            f"There are missing objects in the json, all the objects have not the translation they should "
            f"have. Missing for {dic_missing}",
        )
    return success, message


def test_keys_in_dic(dic, keys_list):
    """
    Tests for each string in the keys_list (list) if it is a key of the dictionary dic
    Returns a boolean, True is all the objects of the list are keys of the dictionary
    """
    return all(x in dic.keys() for x in keys_list)


def manage_keys_in_dic(dic, keys_list, assessment, language, first_language):
    """
    This function manages the error message when a key is not in the dictionary
    """
    clean_failed_assessment_import(assessment, language, first_language)
    return False, f"You have a dictionary {dic} without the required keys {keys_list}"


def create_assessment_body(dic, assessment, language, first_language=True):
    """"""
    success = False

    # In case we need to create the scoring system
    dic_choices = {}
    # In case, for the elements weight
    dic_elements = {}
    # Second layer : sections
    # Dic section keys as "section 1" and values are dictionaries with section data {"order_id":1, ...}

    try:
        dic_sections = dic["sections"]
    except KeyError:
        clean_failed_assessment_import(assessment, language, first_language)
        return success, "You haven't sections in your assessment"

    for section in list(dic_sections.keys()):
        section_data = dic_sections.get(section)  # dic of the section data

        # Test the master section and if all tests are ok, returns the master_section, else master_section=None
        test_section, message, master_section = manage_master_section(
            section_data, assessment, language, first_language
        )
        if not test_section:
            return test_section, message

        # Third layer : evaluation elements

        # Dic_element has "element1" as key and the element data (dict) as value : {"order_id": "1", ..}
        dic_element = section_data.get("elements")

        for element in dic_element.keys():
            element_data = dic_element.get(element)  # dic of the element data

            # Test the element dic (keys, order_id) and create the master_evaluation_element/add new language
            (
                element_test,
                message,
                master_evaluation_element,
                dic_elements,
            ) = manage_master_element(
                master_section,
                element_data,
                dic_elements,
                assessment,
                language,
                first_language,
            )
            if not element_test:
                return element_test, message

            # Case there are resources
            test_resource, message = manage_resources(
                master_evaluation_element,
                element_data,
                assessment,
                language,
                first_language,
            )
            if not test_resource:
                return test_resource, message

            # Fourth layer : choices
            dic_choice = element_data.get("answer_items")

            for choice in list(dic_choice.keys()):
                choice_data = dic_choice.get(choice)  # dic of the choice data
                test_choice, message, dic_choices = manage_choice(
                    choice_data,
                    master_evaluation_element,
                    dic_choices,
                    element_data,
                    assessment,
                    language,
                    first_language,
                )
                if not test_choice:
                    return test_choice, message
    # For first language assessment, we create a scoringSystem and ElementWeight and we return success and message
    if first_language:
        if not list(ScoringSystem.objects.filter(assessment=assessment)):
            scoring = ScoringSystem(
                assessment=assessment,
                name="choice_scoring_of_" + assessment.name,
                master_choices_weight_json=dic_choices,
            )
            scoring.save()

        if not list(EvaluationElementWeight.objects.filter(assessment=assessment)):
            element_weight = EvaluationElementWeight(
                assessment=assessment,
                name="element_weight_of_" + assessment.name,
                master_evaluation_element_weight_json=dic_elements,
            )
            element_weight.save()
        return True, "The assessment body has been created"
    # If we just add a language, return success and message
    else:
        return (
            True,
            f"The assessment {assessment.name} has the new language '{language}'",
        )


def manage_master_section(section_data, assessment, language, first_language):
    """
    If the tests are ok, creates the master_section or add the fields in the new language
    """
    if not test_keys_in_dic(section_data, ["name", "order_id", "elements"]):
        clean_failed_assessment_import(assessment, language, first_language)
        return (
            False,
            f"You have a section without the required keys {['name', 'order_id', 'elements']}",
            None,
        )

    if not test_order_id_number(section_data.get("order_id")):
        clean_failed_assessment_import(assessment, language, first_language)
        return (
            False,
            f"The section id is not an integer for this section {section_data}",
            None,
        )
        # Section creation or new language added to the section
    if first_language:
        master_section = create_master_section(assessment, section_data, language)
    else:
        try:
            master_section = add_language_master_section(
                assessment, section_data, language
            )
        except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
            clean_failed_assessment_import(assessment, language, first_language)
            return (
                False,
                f"There is an issue with the master section {section_data['name']},"
                f" it probably does not exist, error {e}",
                None,
            )
    return True, "This section is ok", master_section


def manage_master_element(
    master_section, element_data, dic_elements, assessment, language, first_language
):
    """
    This function manages the import of the master evaluation element, first testing the keys of the element_data dic,
    then managing the conditions inter, and if it's ok, create the master_evaluation_element or add new language

    :returns: boolean (True if all ok, else false)
    :returns: string (error message)
    :returns: master_evaluation_element (if boolean==False, it is None)
    :returns: dictionary (dic_elements)

    """
    test_element, message = test_the_element(
        element_data, assessment, language, first_language
    )
    if not test_element:
        return test_element, message, None, dic_elements

    # Manage to get the MasterChoice which sets condition inter if there is one, else None
    success_condition_inter, message, depends_on = manage_condition_inter_element(
        element_data, assessment, language, first_language
    )
    if not success_condition_inter:
        return success_condition_inter, message, None, dic_elements

    # Save the master evaluation element
    if first_language:
        master_evaluation_element = create_master_evaluation_element(
            master_section, element_data, depends_on, language
        )

        # Initiate a dictionary of the element weights, all set to 1 by default
        dic_elements[str(master_evaluation_element)] = "1"

    else:
        try:
            master_evaluation_element = add_language_master_evaluation_element(
                master_section, element_data, language
            )
        except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
            clean_failed_assessment_import(assessment, language, first_language)
            return (
                False,
                f"There is an issue with the master evaluation element {element_data['name']},"
                f"it probably does not exist, error {e}",
                None,
                dic_elements,
            )

    return True, "", master_evaluation_element, dic_elements


def test_the_element(element_data, assessment, language, first_language):
    """
    Test the dictionary of the element (keys, order_id, etc)
    """
    # If there are missing keys in the element_data dic
    if not all(
        x in element_data.keys()
        for x in [
            "order_id",
            "name",
            "condition",
            "question_text",
            "question_type",
            "answer_items",
        ]
    ):
        clean_failed_assessment_import(assessment, language, first_language)
        return False, f"You have missing fields for the element {element_data}"

    if not test_order_id_number(element_data.get("order_id")):
        clean_failed_assessment_import(assessment, language, first_language)
        return (
            False,
            f"The order_id is not an convertible into an integer for this element {element_data}",
        )
    return True, "This element is ok"


def manage_condition_inter_element(element_data, assessment, language, first_language):
    """
    This function manages the elements which depend on other evaluation element.
    It returns the status (boolean), the message (empty if success), and depends_on (None or MasterChoice)
    """
    depends_on = None
    if element_data.get("condition") != "n/a":
        if not test_choice_numbering(element_data.get("condition")):
            clean_failed_assessment_import(assessment, language, first_language)
            return (
                False,
                f"You have a condition for a choice which the numbering is"
                f" not respected {element_data.get('condition')}. Please follow th format '1.1.a'",
                depends_on,
            )

        condition = element_data.get("condition").split(".")
        try:
            depends_on = MasterChoice.objects.get(
                order_id=condition[2],
                master_evaluation_element__order_id=condition[1],
                master_evaluation_element__master_section__order_id=condition[0],
                master_evaluation_element__master_section__assessment=assessment,
            )
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            clean_failed_assessment_import(assessment, language, first_language)
            return (
                False,
                f"You have set a condition on a choice which does not exist or which is not "
                f"before the evaluation element. Choice {element_data.get('condition')}",
                depends_on,
            )
    return True, "", depends_on


def manage_resources(
    master_evaluation_element, element_data, assessment, language, first_language
):
    """
    This function manages the resources of the evaluation element.
    If it's an assessment import, create the resources which do not exist yet or add it to the evaluation element.
    If it is a new language import, add the field (text) in the new language
    """
    external_links_element = []
    if element_data.get("resources"):
        external_link_dic = element_data.get("resources")

        if first_language:
            for i in range(len(external_link_dic.values())):
                external_link_data = list(external_link_dic.values())[i]
                # Note that their is no constraint on the resource_type (just text)
                resource_type = external_link_data.get("resource_type")
                # If it is not an addition of another language, we check if we need to create the external links
                if not external_link_already_exist(
                    external_link_data.get("resource_text"), resource_type
                ):
                    # Note that there is no condition on the resource type or resource text as
                    # it is only markdownify (no need to respect a format with a template tags)
                    external_link = create_external_link(
                        external_link_data, resource_type, language
                    )

                # Else, it already exists so we get it
                else:
                    external_link = ExternalLink.objects.get(
                        text=external_link_data.get("resource_text"),
                        type=resource_type,
                    )
                external_links_element.append(
                    external_link
                )  # Add to the list to add it later to the element
            # After the loop, associate the resources to the master evaluation element (m2m field)
            master_evaluation_element.external_links.add(*external_links_element)
            # Else we add the the text in the new language
        else:
            for i in range(len(external_link_dic.values())):
                external_link_data = list(external_link_dic.values())[i]
                try:
                    add_language_external_link(
                        master_evaluation_element, external_link_data, language
                    )
                except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
                    clean_failed_assessment_import(assessment, language, first_language)
                    return (
                        False,
                        f"There is an issue with the resource {external_link_data}, error {e}",
                    )
    return True, ""


def test_the_choice(choice_data, element_data, assessment, language, first_language):
    """
    Realize the tests for the choice data (keys, order_id, etc)
    """
    # Test if all the fields are present for a master choice
    if not all(
        x in choice_data.keys()
        for x in [
            "order_id",
            "answer_text",
            "is_concerned_switch",
        ]
    ):
        clean_failed_assessment_import(assessment, language, first_language)
        return False, f"You have missing fields for the choice {element_data}"

    if not test_order_id_letter(choice_data.get("order_id")):
        clean_failed_assessment_import(assessment, language, first_language)
        return (
            False,
            f"The order_id is not a letter for this choice {choice_data}",
        )

    if not choice_data.get("is_concerned_switch") in [0, 1, "True", "False"]:
        clean_failed_assessment_import(assessment, language, first_language)
        return (
            False,
            f"The choice has not a boolean value for is_concerned_switch {choice_data}",
        )
    return True, ""


def manage_choice(
    choice_data,
    master_evaluation_element,
    dic_choices,
    element_data,
    assessment,
    language,
    first_language,
):
    """
    If the tests are ok, create the master choice or add the new language fields
    """
    test_choice, message = test_the_choice(
        choice_data, element_data, assessment, language, first_language
    )
    if not test_choice:
        return test_choice, message, dic_choices

    if first_language:
        master_choice = create_master_choice(
            master_evaluation_element, choice_data, language
        )
        # The choice should be unique, so it shouldn't exist yet
        if master_choice.get_numbering() in dic_choices:
            clean_failed_assessment_import(assessment, language, first_language)
            return (
                False,
                f"You have duplicate choice numbering so please verify your "
                f"order_id {master_choice.get_numbering()}",
                dic_choices,
            )
        else:
            # Initiate a dictionary of the choice weight, all set to 0 by default (used for Scoring system)
            dic_choices[master_choice.get_numbering()] = "0"

    else:
        try:
            add_language_master_choice(master_evaluation_element, choice_data, language)
        except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
            clean_failed_assessment_import(assessment, language, first_language)
            return (
                False,
                f"There is an issue with the resource {choice_data},"
                f"it probably does not exist for the assessment, error {e}",
                dic_choices,
            )
    return True, "", dic_choices
