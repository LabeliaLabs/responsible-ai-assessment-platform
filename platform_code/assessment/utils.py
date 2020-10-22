import re


def markdownify_bold(text):
    """
    This function markdownify bold in a text which is in html format.
    It replaces "**" by html tag
    :param text:
    :return: text
    """
    text_bis = re.sub(
        r"(?<!\_)\_\_(?!\_)(.*?)(?<!\_)\_\_(?!\_)",
        "<strong>\g<1></strong>",  # noqa
        text,
    )
    return re.sub(
        r"(?<!\*)\*\*(?!\*)(.*?)(?<!\*)\*\*(?!\*)",
        "<strong>\g<1></strong>",  # noqa
        text_bis,
    )


def markdownify_italic(text):
    """
    This function markdownify italic in a text which is in html format.
    It replaces "*" and "_" by html tag
    :param text:
    :return: text
    """
    text_bis = re.sub(
        r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)", "<i>\g<1></i>", text  # noqa
    )
    return re.sub(
        r"(?<!\_)\_(?!\_)(.*?)(?<!\_)\_(?!\_)", "<i>\g<1></i>", text_bis  # noqa
    )


def select_label_choice(text):
    """
    This function selects the string between /" after 'value' keyword and before "id"
    :param text:
    :return:
    """
    return re.findall(r"[0-9]\"\>\r?\n?(.*?)\<\/label", text)
