# todo rename file name "add_attr"
from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def get_key_by_position(dictionary, i):
    print("get key", dictionary, i)
    if type(dictionary) == dict and type(i) == int and i <= len(dictionary.keys()):
        list_keys = list(dictionary.keys())
        return list_keys[i]


@register.filter
def get_value_by_position(dictionary, i):
    if type(dictionary) == dict and type(int(i)) == int and i <= len(dictionary.keys()):
        list_values = list(dictionary.values())
        return list_values[i]


@register.filter
def get_item(dictionary, key):
    if type(dictionary) == dict and key in dictionary.keys():
        return dictionary.get(key)
    else:
        return None


@register.filter
def get_type_form(dictionary, key):
    """ For a dictionary with evaluation element as key and form as value (usually dic_form from SectionView)
    Will return the type of the field in the form which has the key as name"""
    form = dictionary.get(key)
    type_form = form.fields[str(key.id)].widget.input_type
    # print('GET TYPE FORM', form, type_form)
    return type_form


@register.filter
def get_element_list_by_id(list_, i):
    # todo comment, used for what ?
    print("LIST ID", i, type(i))
    if i > 1:
        return list_[i - 1]
    else:
        # todo logs
        return None


@register.filter
def is_not_applicable(self):
    """
    For an evaluation element, if a choice can disable it, we get this one with the function
    get_choice_depending_on. If it is ticked, so this evaluation element shouldn't be available.
    A warning message will appear in the evaluation element card

    :param self:
    :param evaluation: user evaluation
    :return: boolean, True if the choice is ticked and so the evaluation element is not applicable, else False
    """
    choice = self.get_choice_depending_on()
    if choice.is_ticked:
        return True
    else:
        return False


@register.filter
def turn_into_link(link, name):
    # print("TURN LINK", link, type(link), 'name', name, type(name))
    return format_html('<a target="_blank" href="{0}">{1}</a>', link, str(name),)


@register.filter
def order_elements_of_section(section):
    list_element = list(
        section.evaluationelement_set.all().order_by(
            "master_evaluation_element__order_id"
        )
    )
    print(list_element)
    return list_element


@register.filter
def format_date_calendar(string_date):
    return string_date.strftime("%d/%m/%Y")


@register.filter
def manage_external_links(self, element):
    """ Self is explanation text (string) and element is the evaluation element which belongs the explanation text"""
    # list of the explanation that should have their name in the explanation text of the master evalaution element
    list_explanation = list(element.master_evaluation_element.external_links.all())
    for explanation in list_explanation:
        if explanation.name in self and explanation.type == "explication":
            self = self.replace(explanation.name, explanation.turn_into_link())
        else:
            print()
    return format_html(self)


@register.filter
def evaluation_created_by(member, evaluation_list):
    user = member.user
    string_to_display = ""
    for eval in evaluation_list:
        if eval.created_by == user:
            string_to_display += eval.name + ", "
    if len(string_to_display) > 0:
        print(string_to_display[-5:])
        string_to_display = string_to_display[:-2]
    return string_to_display


@register.filter
def count_in_progress(list_evaluation):
    """
    Used in the organisation settings to count the number of evaluations in progress
    :param list_evaluation:
    :return:
    """
    count = 0
    for evaluation in list_evaluation:
        if not evaluation.is_finished:
            count += 1
    return count


@register.filter
def count_finished(list_evaluation):
    """
    Used in the organisation settings to count the number of evaluations finished
    :param list_evaluation:
    :return:
    """
    count = 0
    for evaluation in list_evaluation:
        if evaluation.is_finished:
            count += 1
    return count


@register.filter
def get_evaluation_form(dictionary, key):
    key = str(key)
    if type(dictionary) == dict and key in dictionary.keys():
        return dictionary.get(key)
    else:
        return None
