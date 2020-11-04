from assessment.models import (
    Assessment,
    Evaluation,
    Section,
    MasterSection,
    MasterEvaluationElement,
    EvaluationElement,
    MasterChoice,
    Choice,
    ExternalLink,
)


RADIO = "radio"
CHECKBOX = "checkbox"

QUESTION_TYPES = (
    (RADIO, "radio"),
    (CHECKBOX, "checkbox"),
)

WEB_ARTICLE = "web article"
ACADEMIC_PAPER = "academic paper"
SOFTWARE = "software"
TECHNICAL_GUIDE = "technical guide"
TOOL = "tool"
CODE_REPOSITORY = "code repository"
PUBLIC_DECLARATION = "public declaration"
OFFICIAL_REPORT = "official report"

RESOURCE_TYPES = (
    (WEB_ARTICLE, "web article"),
    (ACADEMIC_PAPER, "academic paper"),
    (SOFTWARE, "software"),
    (TECHNICAL_GUIDE, "technical guide"),
    (TOOL, "tool"),
    (CODE_REPOSITORY, "code repository"),
    (PUBLIC_DECLARATION, "public declaration"),
    (OFFICIAL_REPORT, "official report"),
)


def create_assessment(name, version):
    """
    Create the assessment
    :param name:
    :param version:
    :return:
    """
    return Assessment.objects.create(name=name, version=version)


def create_evaluation(
    assessment,
    name,
    created_by=None,
    organisation=None,
    is_finished=False,
    score=None,
    finished_at=None,
):
    """
    Create the evaluation, by default all the fields not required are set to None
    :param assessment:
    :param name:
    :param created_by:
    :param organisation:
    :param is_finished:
    :param score:
    :param finished_at:
    :return:
    """
    return Evaluation.objects.create(
            assessment=assessment,
            name=name,
            created_by=created_by,
            organisation=organisation,
            is_finished=is_finished,
            score=score,
            finished_at=finished_at,
        )


def create_master_section(name, assessment, description, order_id):
    """
    Create the master section
    :param name:
    :param assessment:
    :param description:
    :param order_id:
    :return:
    """
    return MasterSection.objects.create(
        name=name, assessment=assessment, description=description, order_id=order_id
    )


def create_section(
    master_section,
    evaluation,
    user_progression=0,
    points=0,
    fetch=True,
    user_notes=None,
):
    """
    Create the section
    :param master_section:
    :param evaluation:
    :param user_progression:
    :param points:
    :param fetch:
    :param user_notes:
    :return:
    """
    return Section.object.create(
            master_section=master_section,
            evaluation=evaluation,
            user_progression=user_progression,
            points=points,
            fetch=fetch,
            user_notes=user_notes,
        )


def create_master_evaluation_element(
    name,
    master_section,
    order_id,
    question_type=RADIO,
    question_text="",
    explanation_text="",
    depends_on=None,
    *args,
    **kwargs,
):
    """
    Create the master evaluation element, some fields are initiated empty by default
    :param name:
    :param master_section:
    :param order_id:
    :param question_text:
    :param question_type:
    :param explanation_text:
    :param depends_on:
    :return:
    """
    master_evaluation_element = MasterEvaluationElement.objects.create(
        name=name,
        master_section=master_section,
        order_id=order_id,
        question_text=question_text,
        question_type=question_type,
        explanation_text=explanation_text,
        depends_on=depends_on,
    )
    if "external_links" in kwargs:
        external_links = kwargs.get("external_links")
        master_evaluation_element.external_links.add(external_links)
    return master_evaluation_element


def create_evaluation_element(
    master_evaluation_element,
    section,
    user_notes=None,
    points=0,
    status=False,
    fetch=True,
):
    """
    :param master_evaluation_element:
    :param section:
    :param user_notes:
    :param points:
    :param status:
    :param fetch:
    :return:
    """
    EvaluationElement.objects.create(
        master_evaluation_element=master_evaluation_element,
        section=section,
        user_notes=user_notes,
        points=points,
        status=status,
        fetch=fetch,
    )


def create_master_choice(
    master_evaluation_element, answer_text, order_id, is_concerned_switch=False
):
    """
    :param is_concerned_switch:
    :param master_evaluation_element:
    :param answer_text:
    :param order_id:
    :return:
    """
    return MasterChoice.objects.create(
        master_evaluation_element=master_evaluation_element,
        answer_text=answer_text,
        order_id=order_id,
        is_concerned_switch=is_concerned_switch,
    )


def create_choice(master_choice, evaluation_element, is_ticked=False, fetch=True):
    """
    :param master_choice:
    :param evaluation_element:
    :param is_ticked:
    :param fetch:
    :return:
    """
    Choice.objects.create(
        master_choice=master_choice,
        evaluation_element=evaluation_element,
        is_ticked=is_ticked,
        fetch=fetch,
    )


def create_external_link(text, type_link=WEB_ARTICLE):
    """
    Create an external link (resource)
    :param type_link:
    :param text:
    :return:
    """
    return ExternalLink.objects.create(text=text, type=type_link)


def create_assessment_body(
    version="1.0", resource_text="resource_text"
):
    """
    This function creates an assessment with 2 master sections (one with the possibility to set order_id to none or
    to a value), with 3 master evaluation elements (2 for master_section_1 and 1 for the other), and 2 master choices
    for the master element 1 and 2 and 1 for the master element 3
    :return:
    """
    assessment = create_assessment(name="assessment", version=version)
    master_section1 = create_master_section(
        name="master_section1", assessment=assessment, description="", order_id="1"
    )
    master_section2 = create_master_section(
        name="master_section2",
        assessment=assessment,
        description="",
        order_id="2",
    )
    # Create and get resources (External Link)
    resource = create_external_link(text=resource_text)
    # Create the master evaluation elements
    master_evaluation_element1 = create_master_evaluation_element(
        name="master_element1", master_section=master_section1, order_id="1"
    )

    master_choice_1 = create_master_choice(
        master_evaluation_element=master_evaluation_element1,
        answer_text="answer",
        order_id="a",
        is_concerned_switch=True,  # Todo change because it is a radio item so pointless
    )

    master_evaluation_element2 = create_master_evaluation_element(
        name="master_element2",
        master_section=master_section1,
        order_id="2",
        external_links=resource,
        depends_on=master_choice_1,
        question_type=CHECKBOX,
    )
    master_evaluation_element3 = create_master_evaluation_element(
        name="master_element3",
        master_section=master_section2,
        order_id="1",
        external_links=resource,
    )

    create_master_choice(
        master_evaluation_element=master_evaluation_element1,
        answer_text="answer",
        order_id="b",
    )
    create_master_choice(
        master_evaluation_element=master_evaluation_element2,
        answer_text="answer",
        order_id="a",
        is_concerned_switch=True,
    )
    create_master_choice(
        master_evaluation_element=master_evaluation_element2,
        answer_text="answer",
        order_id="b",
    )
    create_master_choice(
        master_evaluation_element=master_evaluation_element3,
        answer_text="answer",
        order_id="a",
    )
