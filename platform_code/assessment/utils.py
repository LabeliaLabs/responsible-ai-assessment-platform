import re

from django.db.models import JSONField


class RawJSONField(JSONField):
    """
    NOT USED
    Used for the exposition score, to keep the order of the json
    """

    def db_type(self, connection):
        return "json"


def markdownify_bold(text):
    """
    This function markdownify bold in a text which is in html format.
    It replaces "**" by html tag
    :param text:
    :return: text
    """
    text_bis = re.sub(
        r"(?<!\_)\_\_(?!\_)(.*?)(?<!\_)\_\_(?!\_)",
        r"<strong>\g<1></strong>",  # noqa
        text,
    )
    return re.sub(
        r"(?<!\*)\*\*(?!\*)(.*?)(?<!\*)\*\*(?!\*)",
        r"<strong>\g<1></strong>",  # noqa
        text_bis,
    )


def remove_markdown_bold(text):
    """
    This function is used to replace the markdown tags in master_choices in the results as it is not
    necessary
    :param text:
    :return: text
    """
    # todo tests
    text_bis = re.sub(
        r"(?<!\_)\_\_(?!\_)(.*?)(?<!\_)\_\_(?!\_)",
        r"\g<1>",  # noqa
        text,
    )
    return re.sub(
        r"(?<!\*)\*\*(?!\*)(.*?)(?<!\*)\*\*(?!\*)",
        r"\g<1>",  # noqa
        text_bis,
    )


def markdownify_italic(text):
    """
    This function markdownify italic in a text which is in html format.
    It replaces "*" and "_" by html tag
    :param text:
    :return: text
    """
    text_bis = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"<i>\g<1></i>", text)  # noqa
    return re.sub(r"(?<!\_)\_(?!\_)(.*?)(?<!\_)\_(?!\_)", r"<i>\g<1></i>", text_bis)  # noqa


def remove_markdownify_italic(text):
    """
    This function is used to remove italic markdown tags in the master_choice text in the results page
    :param text:
    :return: text
    """
    # Todo tests
    text_bis = re.sub(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", r"\g<1>", text)  # noqa
    return re.sub(r"(?<!\_)\_(?!\_)(.*?)(?<!\_)\_(?!\_)", r"\g<1>", text_bis)  # noqa


def select_label_choice(text):
    """
    This function selects the string between /" after 'value' keyword and before "id"
    :param text:
    :return:
    """
    return re.findall(r"\>\r?\n?(.*?\<\/label)", text)


def get_client_ip(request):
    """
    This function is used to get the IP address of the user from a request
    :param request:
    :return: string
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
