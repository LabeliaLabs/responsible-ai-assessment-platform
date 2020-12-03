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


def treat_and_save_dictionary_data(dic):
    """
    This function is used when we want to import a json (the assessment).
    The argument is a dictionary which comes from a json file and represents all the assessment
    dictionary
    A succes (boolean) is returned, init to false, and a message
    :param dic:
    :return:
    """
    #
    success = False
    message = ""
    # First layer : Assessment data
    try:
        version = dic["version"]
    except KeyError as e:
        return success, f"You need to provide an assessment version which could be converted into a float, error {e}"
    # If there already is an assessment with the same version, raise error and ask for change
    if list(Assessment.objects.filter(version=version)):
        message = "There already is an assessment with this version. Please change it."
        return success, message
    # The version must be convertible into float value (example '0.5', '1.0', etc)
    try:
        float(version)
    except ValueError as e:
        return (success, f"Error {e}. The version must not contain letters. It should be convertible into a float "
                         f"('0.5', '1.0', etc). The version you provided was '{version}'")

    if float(version) <= 0:
        return success, "The version must be convertible into a positive number"
    if get_last_assessment_created():
        if float(version) < float(get_last_assessment_created().version):
            return success, f"The assessment version must not be smaller than the" \
                            f" assessment versions already in the DB" \
                            f"The new assessment version is {version} and the latest in th DB" \
                            f" is {get_last_assessment_created().version}"

    if "name" not in dic.keys():
        return success, "You need to provide a name for the assessment"

    name = dic["name"]
    # Otherwise we can create the assessment
    # If the import fails later, we need to delete the assessment
    assessment = Assessment(name=name, version=version)
    assessment.save()
    # In case we need to create the scoring system
    dic_choices = {}
    # In case, for the elements weight
    dic_elements = {}
    # Second layer : sections
    # Dic section keys as "section 1" and values are dictionaries with section data {"order_id":1, ...}

    try:
        dic_sections = dic["sections"]
    except KeyError:
        clean_failed_assessment_import(name, version)
        return success, "You haven't sections in your assessment"

    for section in list(dic_sections.keys()):
        # print("SECTION INIT", dic_sections, section)
        section_data = dic_sections.get(section)  # dic of the section data
        # Name cannot be null for a master section
        if "name" not in section_data.keys():
            clean_failed_assessment_import(name, version)
            return success, f"You have a section without name {section_data}"
        if "order_id" not in section_data.keys():
            clean_failed_assessment_import(name, version)
            return success, f"You have a section without order_id {section_data}"
        if not test_order_id_number(section_data.get("order_id")):
            clean_failed_assessment_import(name, version)
            return (
                success,
                f"The section id is not an integer for this section {section_data}",
            )

        master_section = MasterSection(
            assessment=assessment,
            name=section_data.get("name"),
            order_id=section_data.get("order_id"),
            description=section_data.get("description"),
        )
        master_section.save()

        # Third layer : evaluation elements

        # Dic_element has "element1" as key and the element data (dict) as value : {"order_id": "1", ..}
        if "elements" in section_data.keys():
            dic_element = section_data.get("elements")
        else:
            clean_failed_assessment_import(name, version)
            return success, "You have a section without elements"

        for element in dic_element.keys():
            element_data = dic_element.get(element)  # dic of the element data

            # If there are missing keys in the element_data dic
            if not all(x in element_data.keys() for x in ["order_id",
                                                          "name",
                                                          "condition",
                                                          "question_text",
                                                          "question_type",
                                                          ]):
                clean_failed_assessment_import(name, version)
                return success, f"You have missing fields for the element {element_data}"

            # Case there is a condition inter evaluation elements
            # Condition : 1.5.a for example
            depends_on = None
            external_links_element = []
            if element_data.get("condition") != "n/a":
                if not test_choice_numbering(element_data.get("condition")):
                    clean_failed_assessment_import(name, version)
                    return success, f"You have a condition for a choice which the numbering is" \
                                    f" not respected {element_data.get('condition')}. Please follow th format '1.1.a'"
                condition = element_data.get("condition").split(".")
                try:
                    depends_on = MasterChoice.objects.get(
                        order_id=condition[2],
                        master_evaluation_element__order_id=condition[1],
                        master_evaluation_element__master_section__order_id=condition[0],
                        master_evaluation_element__master_section__assessment=assessment,
                    )
                except (ObjectDoesNotExist, MultipleObjectsReturned):
                    clean_failed_assessment_import(name, version)
                    return success, f"You have set a condition on a choice which does not exist or which is not " \
                                    f"before the evaluation element. Choice {element_data.get('condition')}"

            # Case there are resources
            if element_data.get("resources"):
                external_link_dic = element_data.get("resources")
                # print("external_link_dic", external_link_dic)
                for i in range(len(external_link_dic.values())):
                    external_link_data = list(external_link_dic.values())[i]
                    resource_type = external_link_data.get("resource_type")
                    if not external_link_already_exist(
                        external_link_data.get("resource_text"), resource_type
                    ):
                        # Note that there is no condition on the resource type or resource text as
                        # it is only markdownify (no need to respect a format with a template tags)
                        external_link = ExternalLink(
                            text=external_link_data.get("resource_text"),
                            type=resource_type,
                        )
                        external_link.save()
                    # Else, it already exists so we get it
                    else:
                        external_link = ExternalLink.objects.get(
                            text=external_link_data.get("resource_text"),
                            type=resource_type,
                        )
                    external_links_element.append(
                        external_link
                    )  # Add to the list to add it later to the element

            if "order_id" not in element_data.keys():
                clean_failed_assessment_import(name, version)
                return success, f"The element {element_data} has no order_id"
            if not test_order_id_number(element_data.get("order_id")):
                clean_failed_assessment_import(name, version)
                return (
                    success,
                    f"The order_id is not an convertible into an integer for this element {element_data}",
                )

            master_evaluation_element = MasterEvaluationElement(
                master_section=master_section,
                name=element_data.get("name"),
                order_id=element_data.get("order_id"),
                question_text=element_data.get("question_text"),
                question_type=element_data.get("question_type"),
                explanation_text=element_data.get("explanation_text").replace(
                    "n/a", ""
                ),
                depends_on=depends_on,
            )

            master_evaluation_element.save()
            master_evaluation_element.external_links.add(*external_links_element)
            dic_elements[str(master_evaluation_element)] = "1"

            # Fourth layer : choices
            if "answer_items" in element_data:
                dic_choice = element_data.get("answer_items")
            else:
                clean_failed_assessment_import(name, version)
                return success, f"The element {element_data} has no answer_items"

            for choice in list(dic_choice.keys()):
                choice_data = dic_choice.get(choice)  # dic of the choice data
                # Test if all the fields are present for a master choice
                if not all(x in choice_data.keys() for x in ["order_id",
                                                             "answer_text",
                                                             "is_concerned_switch",
                                                             ]):
                    clean_failed_assessment_import(name, version)
                    return success, f"You have missing fields for the choice {element_data}"

                if not test_order_id_letter(choice_data.get("order_id")):
                    clean_failed_assessment_import(name, version)
                    return (
                        success,
                        f"The order_id is not a letter for this choice {choice_data}",
                    )

                if not choice_data.get("is_concerned_switch") in [0, 1, "True", "False"]:
                    clean_failed_assessment_import(name, version)
                    return (
                        success,
                        f"The choice has not a boolean value for is_concerned_switch {choice_data}",
                    )

                master_choice = MasterChoice(
                    master_evaluation_element=master_evaluation_element,
                    order_id=choice_data.get("order_id"),
                    answer_text=choice_data.get("answer_text"),
                    is_concerned_switch=choice_data.get("is_concerned_switch"),
                )
                master_choice.save()
                # The choice should be unique, so it shouldn't exist yet
                if master_choice.get_numbering() in dic_choices:
                    clean_failed_assessment_import(name, version)
                    return success, f"You have duplicate choice numbering so please verify your " \
                                    f"order_id {master_choice.get_numbering()}"
                else:
                    dic_choices[master_choice.get_numbering()] = "0"

    if not list(ScoringSystem.objects.filter(assessment=assessment)):
        scoring = ScoringSystem(
            assessment=assessment,
            name="choice_scoring_of_"+assessment.name,
            master_choices_weight_json=dic_choices,
        )
        scoring.save()

    if not list(EvaluationElementWeight.objects.filter(assessment=assessment)):
        element_weight = EvaluationElementWeight(
            assessment=assessment,
            name="element_weight_of_"+assessment.name,
            master_evaluation_element_weight_json=dic_elements,
        )
        element_weight.save()

    return True, "The assessment has been created"


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
        message = f"The {object_type} {object_assessment.get_numbering()} of" \
                  f" the assessment is not in the dictionary of differences for" \
                  f" the version {dic_diff.keys()}, the {object_type} present are : {dic_diff[object_type].keys()}"

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
            message = f"The version {version} in the upgrade json is not an assessment version in the database. " \
                      f"Error {e}"

    return success, message


def clean_failed_assessment_import(name, version):
    """
    Delete the assessment if the import fails because it can be created during the process but the latter
    failed after
    :param name: string
    :param version: string
    :return:
    """
    if len(list(Assessment.objects.filter(name=name, version=version))) == 1:
        Assessment.objects.get(name=name, version=version).delete()
    else:
        raise ValueError
