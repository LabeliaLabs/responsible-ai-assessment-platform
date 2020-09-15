import re

from .models import Assessment, MasterChoice, MasterSection, MasterEvaluationElement,\
    ExternalLink, ScoringSystem, EvaluationElementWeight


def treat_and_save_dictionary_data(dic):
    """
    This function is used when we want to import a json (the assessment).
    The argument is a dictionary which comes from a json file and represents all the assessment
    dictionary
    :param dic:
    :return:
    """

    # First layer : Assessment data
    version = dic.get("version")
    # If there already is an assessment with the same version, raise error and ask for change
    if list(Assessment.objects.filter(version=version)):
        raise ValueError(
            "Un assessment existe déjà avec cette version. Veuillez la changer"
        )
    # Otherwise we can create the assessment
    assessment = Assessment(name=dic.get("name"), version=version)
    assessment.save()
    # In case we need to create the scoring system
    dic_choices = {}
    # In case, for the elements weight
    dic_elements = {}
    # Second layer : sections
    # Dic section keys as "section 1" and values are dictionaries with section data {"order_id":1, ...}
    dic_sections = dic.get("sections")

    for section in list(dic_sections.keys()):
        # print("SECTION INIT", dic_sections, section)
        section_data = dic_sections.get(section)  # dic of the section data

        if not test_order_id_number(section_data.get("order_id")):
            raise ValueError("L'id d'une section n'est pas un entier", section_data)

        master_section = MasterSection(
            assessment=assessment,
            name=section_data.get("name"),
            order_id=section_data.get("order_id"),
            description=section_data.get("description"),
        )
        master_section.save()

        # Third layer : evaluation elements

        # Dic_element has "element1" as key and the element data (dict) as value : {"order_id": "1", ..}
        dic_element = section_data.get("elements")

        for element in dic_element.keys():
            element_data = dic_element.get(element)  # dic of the element data

            # Case there is a condition inter evaluation elements
            # Condition : 1.5.a for example
            depends_on = None
            external_links_element = []
            if element_data.get("condition") != "n/a":
                condition = element_data.get("condition").split(".")
                depends_on = MasterChoice.objects.get(
                    order_id=condition[2],
                    master_evaluation_element__order_id=condition[1],
                    master_evaluation_element__master_section__order_id=condition[0],
                    master_evaluation_element__master_section__assessment=assessment,
                )

            # Case there are resources
            if element_data.get("resources"):
                external_link_dic = element_data.get("resources")
                # print("external_link_dic", external_link_dic)
                for i in range(len(external_link_dic.values())):
                    external_link_data = list(external_link_dic.values())[i]
                    resource_type = external_link_data.get("resource_type")
                    if not external_link_already_exist(external_link_data.get("resource_text"), resource_type):
                        external_link = ExternalLink(
                            text=external_link_data.get("resource_text"),
                            type=resource_type
                        )
                        external_link.save()
                    # Else, it already exists so we get it
                    else:
                        external_link = ExternalLink.objects.get(
                            text=external_link_data.get("resource_text"),
                            type=resource_type
                        )
                    external_links_element.append(
                        external_link
                    )  # Add to the list to add it later to the element

            if not test_order_id_number(element_data.get("order_id")):
                raise ValueError(
                    "L'id d'un élément d'évaluation n'est pas un entier", element_data
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

            dic_choice = element_data.get("answer_items")
            # print("dic choice", dic_choice)

            for choice in list(dic_choice.keys()):
                choice_data = dic_choice.get(choice)  # dic of the choice data
                # print("CHOICE DATA", choice_data)
                depends_on = None
                if choice_data.get("depends_on"):
                    depends_on = MasterChoice.objects.get(
                        master_evaluation_element=master_evaluation_element,
                        order_id=choice_data.get("depends_on"),
                        master_evaluation_element__master_section__assessment=assessment,
                    )
                if not test_order_id_letter(choice_data.get("order_id")):
                    raise ValueError(
                        "L'id d'un choix n'est pas une lettre", choice_data
                    )

                master_choice = MasterChoice(
                    master_evaluation_element=master_evaluation_element,
                    order_id=choice_data.get("order_id"),
                    answer_text=choice_data.get("answer_text"),
                    depends_on=depends_on,
                )
                master_choice.save()
                dic_choices[master_choice.get_numbering()] = "0"

    if not list(ScoringSystem.objects.filter(assessment=assessment)):
        scoring = ScoringSystem(
            assessment=assessment,
            name="scoring",
            master_choices_weight_json=dic_choices,
        )
        scoring.save()

    if not list(EvaluationElementWeight.objects.filter(assessment=assessment)):
        element_weight = EvaluationElementWeight(
            assessment=assessment,
            name="element weight",
            master_evaluation_element_weight_json=dic_elements,
        )
        element_weight.save()


def test_order_id_number(order_id):
    """Chek if the choice order_id is a letter"""
    reg = re.findall(r"[0-9]", order_id)
    return reg != []


def test_order_id_letter(order_id):
    """Chek if the choice order_id is a letter"""
    reg = re.findall(r"[a-z]", order_id)
    return reg != []


def external_link_already_exist(text, resource_type):
    """
    Check if there is already a resource in the table ExternalLinks. Return boolean (True if it exists).
    """
    return list(ExternalLink.objects.filter(text=text, type=resource_type)) != []
