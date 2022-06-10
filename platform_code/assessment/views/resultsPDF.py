from datetime import date, datetime
import io
import logging
from html import unescape
import reportlab
import textwrap
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views.generic import DetailView
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from sentry_sdk import capture_message

from assessment.models import Evaluation
from home.models import Organisation
from assessment.utils import (
    get_client_ip,
    remove_markdown_bold,
    remove_markdownify_italic,
)
from assessment.views.utils.security_checks import membership_security_check
from assessment.views.utils.utils import (
    manage_evaluation_score,
    manage_evaluation_max_points,
    manage_evaluation_exposition_score,
)

logger = logging.getLogger("monitoring")


class ResultsPDFView(LoginRequiredMixin, DetailView):
    """
    This view defines the PDF page of the results of an evaluation,
    with the score and the overall evaluation and choices
    It is accessible only if the evaluation is finished.
    """

    model = Evaluation
    login_url = "home:homepage"
    redirect_field_name = "home:homepage"

    STAMP_WIDTH = 300
    PAGE_WIDTH = 595
    PAGE_HEIGHT = 800
    MARGIN_BASE = 40
    MARGIN_QUESTION = MARGIN_BASE + 10
    MARGIN_ANSWER_CIRCLE = MARGIN_QUESTION + 15
    MARGIN_ANSWER = MARGIN_QUESTION + 30
    MARGIN_NOTES = MARGIN_BASE + 5
    MARGIN_BOTTOM = 50
    LINE_BREAK = 15
    PARAGRAPH_SPACE = 10
    LINE_JUMP = 25

    COLOR_TEXT = 0.3, 0.34, 0.42
    COLOR_TITLE = 0.33, 0.31, 1
    COLOR_FILL_CONCERN_NOTE = 1, 0.95, 0.8
    COLOR_TEXT_CONCERN_NOTE = 0.52, 0.39, 0
    COLOR_ELEMENT_RECTANGLE_FILL = 0.94, 0.94, 0.94
    COLOR_ELEMENT_RECTANGLE_STROKE = 0.88, 0.88, 0.88

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # creates a buffer that will be used by the pdf Canvas
        self.buffer = io.BytesIO()
        reportlab.rl_config.TTFSearchPath.append(
            str(settings.BASE_DIR) + "/assessment/static/fonts/Ubuntu"
        )
        pdfmetrics.registerFont(TTFont("UbuntuRegular", "Ubuntu-Regular.ttf"))
        pdfmetrics.registerFont(TTFont("UbuntuItalic", "Ubuntu-Italic.ttf"))
        pdfmetrics.registerFont(TTFont("UbuntuBold", "Ubuntu-Bold.ttf"))
        self.pdf = canvas.Canvas(self.buffer)
        self.cursor = self.PAGE_HEIGHT
        self.page_num = 1

    def print_pdf(self, context):
        """
        This method sets the metadata for the pdf and prints the header and sections on the buffer.
        After printing the buffer is closed and is returned
        """
        # METADATA
        self.pdf.setAuthor(context["organisation"].name)
        self.pdf.setTitle(context["evaluation"].name)
        self.pdf.setProducer("Labelia Labs")
        self.pdf.setCreator("Labelia Labs")
        self.pdf.setTitle("Labelia Assessment " + date.today().strftime("%Y/%m/%d"))
        self.pdf.setSubject("Labelia Assessment " + date.today().strftime("%Y/%m/%d"))

        # HEADER
        self.print_header(context)
        self.page_break(evaluation_name=context["evaluation"].name)

        # SECTION
        self.print_sections(context["dict_sections_elements"])

        # return
        self.pdf.save()
        self.buffer.seek(0)
        return self.buffer

    def print_header(self, context):
        """
        This method prints the pdf header, the print is sequential,
        the font is modified between prints
        """
        # evaluation name
        self.pdf.setFont("UbuntuRegular", 25)
        self.pdf.setFillColorRGB(*self.COLOR_TITLE)
        self.pdf.drawCentredString(
            self.PAGE_WIDTH / 2, self.cursor, context["evaluation"].name
        )
        self.cursor -= self.LINE_JUMP * 2
        self.pdf.setFillColorRGB(*self.COLOR_TEXT)
        self.pdf.setFont("UbuntuRegular", 18)
        self.pdf.drawCentredString(
            self.PAGE_WIDTH / 2,
            self.cursor,
            context["organisation"].name
            + " | "
            + context["evaluation"].finished_at.strftime("%d/%m/%Y"),
        )
        self.cursor -= self.LINE_JUMP

        # stamp
        self.print_stamp(context)

        # score
        self.pdf.setFont("UbuntuRegular", 18)
        self.pdf.drawCentredString(
            self.PAGE_WIDTH / 2,
            self.cursor,
            _("Synthetic evaluation score"),
        )
        self.cursor -= self.LINE_JUMP * 2
        self.pdf.drawCentredString(
            self.PAGE_WIDTH / 2,
            self.cursor,
            str(context["evaluation_score"]) + " / 100",
        )
        self.cursor -= self.LINE_JUMP * 2

        # Score per section
        self.pdf.setFont("UbuntuRegular", 18)
        self.pdf.drawCentredString(
            self.PAGE_WIDTH / 2, self.cursor, _("Score per section")
        )
        self.cursor -= self.LINE_JUMP * 2
        self.pdf.setFont("UbuntuRegular", 12)
        for section in context["dict_sections_elements"]:
            string = f"{_('Section')} {section.master_section.order_id}: {section.master_section.name}"
            self.draw_centered_string_on_pdf(string, 500)
            section_points = (section.calculate_score_per_section() / section.max_points) * 100
            self.draw_centered_string_on_pdf(
                f"{section_points:.1f} %",
                400,
            )
            self.cursor -= self.PARAGRAPH_SPACE
        self.cursor -= self.LINE_JUMP

        # Risk exposition
        # self.cursor -= self.LINE_JUMP * 2
        self.page_break(evaluation_name=context["evaluation"].name)
        self.pdf.setFillColorRGB(*self.COLOR_TEXT)
        self.pdf.setFont("UbuntuRegular", 18)
        self.pdf.drawCentredString(
            self.PAGE_WIDTH / 2,
            self.cursor,
            _("Exposition score")
        )
        self.pdf.setFont("UbuntuRegular", 12)

        self.cursor -= self.LINE_JUMP * 2
        self.pdf.drawCentredString(
            self.PAGE_WIDTH / 2,
            self.cursor,
            _("You are exposed to ") + str(context["nb_risks_exposed"]) + '/' + str(context["len_exposition_dic"]) +
            ' ' + _("of the risks identified in the assessment.")
        )
        self.cursor -= self.LINE_JUMP * 2
        data = convert_exposition_dic_to_data(context["exposition_dic"], 70)
        table = Table(data, colWidths=[self.PAGE_WIDTH / 3, 150], rowHeights=None)
        table.setStyle(TableStyle([
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ]))
        table_width, table_height = table.wrap(0, 0)
        table.wrapOn(self.pdf, 0, 0)
        table.drawOn(self.pdf, self.PAGE_WIDTH / 2 - table_width / 2, self.PAGE_HEIGHT - 80 - table_height)

        self.cursor -= table_height + self.LINE_JUMP * 2

        # Explanations text
        self.pdf.setFont("UbuntuRegular", 18)
        self.pdf.drawCentredString(
            self.PAGE_WIDTH / 2,
            self.cursor,
            _("Explanation")
        )
        self.cursor -= self.LINE_JUMP * 2
        self.pdf.setFont("UbuntuRegular", 12)
        self.draw_string_on_pdf(
            _(
                "The synthetic score is on a total of 100 theoretical maximum points for your "
                "full assessment. It provides an indication of the organization maturity "
                "level concerning a responsible and trustworthy data science. At the end of "
                "2020, the 50/100 threshold can be considered a very advanced maturity level."
            ),
            self.MARGIN_BASE,
        )
        self.cursor -= self.PARAGRAPH_SPACE
        self.draw_string_on_pdf(
            _(
                "The mechanism for calculating the score is described in the FAQ "
                "that you can consult on assessment.labelia.org"
            ),
            self.MARGIN_BASE,
        )
        self.cursor -= self.PARAGRAPH_SPACE
        self.draw_string_on_pdf(
            _(
                "Note: the score is a synthetic indication, "
                "not an end in itself. In particular, we invite "
                "you to consult the resources associated with "
                "each assessment element, which are excellent entry points for "
                "building skills on your topics of interest."
            ),
            self.MARGIN_BASE,
        )
        self.cursor -= self.LINE_JUMP * 2

    def print_stamp(self, context):
        """
        This method prints the stamp with the current date and the organisation name.
        """
        today_date = date.today().strftime("%d/%m/%Y")
        current_time = datetime.now().strftime("%H:%M")
        organisation_name = context["organisation"].name
        stamp = _(
            f"PDF generated on {today_date} at {current_time} UTC by the assessment.labelia.org platform. "
            f"This is a self-assessment realized by the organisation {organisation_name}. "
            "It has not been verified or audited by Labelia Labs."
        )
        self.pdf.setFont("UbuntuBold", 9)
        self.draw_centered_string_on_pdf(stamp, self.STAMP_WIDTH)
        self.cursor -= self.LINE_JUMP * 2

    def print_sections(self, dict_sections_elements):
        """
        This method prints the header for each section
        before calling print_element for each question
        After each section a page break is added
        """
        # 'Your answers' text
        self.pdf.setFont("UbuntuRegular", 25)
        self.draw_string_on_pdf(
            _("Evaluation details"), self.MARGIN_QUESTION
        )
        self.cursor -= self.PARAGRAPH_SPACE

        for section, elements in dict_sections_elements.items():
            self.pdf.setFont("UbuntuRegular", 16)
            self.pdf.setStrokeColorRGB(*self.COLOR_TEXT)
            self.pdf.setFillColorRGB(*self.COLOR_TEXT)
            self.draw_string_on_pdf(str(section), self.MARGIN_QUESTION)

            self.cursor -= 10
            for element, choices in elements.items():
                self.print_element(element, choices)
            self.page_break(
                evaluation_name=section.evaluation.name,
                section_order_id=section.master_section.order_id,
            )

    def print_element(self, element, choices):
        """
        This method prints a question and call print_answer for each answer related to it
        if the question size (with answers) is bigger than the size left on current pdf page
        it adds a page break before printing the question
        it finally prints the user notes for this question
        """
        # get text to write
        section_order_id = element.section.master_section.order_id
        element_order_id = element.master_evaluation_element.order_id
        question_text = element.master_evaluation_element.question_text
        element_text = f"Q{section_order_id}.{element_order_id} : {question_text}"
        question_type_note = ""

        if element.master_evaluation_element.question_type == "radio":
            question_type_note = (
                f"R{section_order_id}.{element_order_id}: "
                f"{_('Please select one answer which best matches to your organisation situation.')}"
            )
        elif element.master_evaluation_element.question_type == "checkbox":
            explanation_text = _(
                "Please select all the answers which best match to your organisation situation. "
                "Be careful, some combinations are not coherent."
            )
            question_type_note = (
                f"R{section_order_id}.{element_order_id}: " f"{explanation_text}"
            )

        not_concerned = (
                element.has_condition_on() and element.get_choice_depending_on().is_ticked
        )
        element_content = {
            "elem_text": str(element),
            "element_text": element_text,
            "question_type_note": question_type_note,
            "not_concerned": not_concerned,
            "choices": choices,
        }
        if element.user_justification:
            element_content["user_justification"] = element.user_justification
            element_content["formatted_justification"] = self.split_complex_string(
                element.user_justification, self.MARGIN_NOTES
            )
        else:
            element_content["formatted_justification"] = []

        if element.user_notes:
            element_content["user_notes"] = element.user_notes
            element_content["formatted_notes"] = self.split_complex_string(element.user_notes, self.MARGIN_NOTES)
        else:
            element_content["formatted_notes"] = []

        core_elem_height, full_elem_height = self.element_size(element_content)
        # if the core_element does not fit in the current page
        # => page break
        # if the core_element fits the current page height but not the full element (+ notes & justification)
        # => draw it and cut the text & border to go on the next page too
        if self.cursor - core_elem_height < self.MARGIN_BOTTOM:
            self.page_break(
                evaluation_name=element.section.evaluation.name,
                section_order_id=element.section.master_section.order_id,
            )

        q_header_size = self.PARAGRAPH_SPACE + self.LINE_BREAK * self.get_line_count(
            str(element), "UbuntuRegular", 12, 480
        )

        if self.cursor - full_elem_height >= self.MARGIN_BOTTOM:
            # Space to draw the full element so classic border
            self.draw_element_border(full_elem_height, q_header_size)
            self.draw_core_element(element, not_concerned, element_text, question_type_note, choices)
            self.draw_justification_and_notes(
                element_content["formatted_justification"],
                element_content["formatted_notes"]
            )

        else:
            # Not the space on the current page so need to cut it into 2 pages - or more
            remaining_height = self.draw_element_cut_border_first_page(full_elem_height, q_header_size)
            # Draw element title, questions - always on the 1st page of the element box
            self.draw_core_element(element, not_concerned, element_text, question_type_note, choices)
            remaining_formatted_justification, remaining_formatted_notes = \
                self.draw_justification_and_notes(
                    element_content["formatted_justification"],
                    element_content["formatted_notes"]
                )
            while remaining_height > 0:
                self.page_break(
                    evaluation_name=element.section.evaluation.name,
                    section_order_id=element.section.master_section.order_id,
                )
                if remaining_height > self.PAGE_HEIGHT - self.MARGIN_BOTTOM - self.MARGIN_BASE - self.LINE_JUMP * 2:
                    # Not enough space for the remaining text (justification & notes) in a full page
                    remaining_height = self.draw_element_cut_border_full_page(remaining_height)
                    remaining_formatted_justification, remaining_formatted_notes = \
                        self.draw_justification_and_notes(
                            remaining_formatted_justification,
                            remaining_formatted_notes
                        )
                else:
                    self.draw_element_cut_border_top(remaining_height + self.LINE_JUMP)
                    remaining_height = 0
                    remaining_formatted_justification, remaining_formatted_notes = \
                        self.draw_justification_and_notes(
                            remaining_formatted_justification,
                            remaining_formatted_notes
                        )

    def draw_element_border(self, elem_height, q_header_size):
        """
        This function draws a rectangle around the element and fill the header with a color
        """
        self.pdf.setFillColorRGB(*self.COLOR_ELEMENT_RECTANGLE_FILL)
        self.pdf.setStrokeColorRGB(*self.COLOR_ELEMENT_RECTANGLE_STROKE)
        self.pdf.roundRect(
            self.MARGIN_BASE,
            self.cursor - elem_height,
            self.PAGE_WIDTH - self.MARGIN_BASE * 2,
            elem_height + 15,
            8,
            fill=0,
        )
        self.pdf.roundRect(
            self.MARGIN_BASE,
            self.cursor - q_header_size + 15,
            self.PAGE_WIDTH - self.MARGIN_BASE * 2,
            q_header_size,
            8,
            fill=1,
            stroke=0,
        )
        self.pdf.rect(
            41,
            self.cursor - q_header_size + 10,
            self.PAGE_WIDTH - self.MARGIN_BASE * 2 - 1,
            12,
            fill=1,
            stroke=0,
        )
        self.pdf.line(
            self.MARGIN_BASE,
            self.cursor - q_header_size + 10,
            self.PAGE_WIDTH - self.MARGIN_BASE,
            self.cursor - q_header_size + 10,
        )

    def draw_element_cut_border_first_page(self, full_elem_height, q_header_size):
        """
        Draw the rectangle for the element when its height is longer than the current page.
        First, draw the rectangle on the current page and add a white rectangle to cover the bottom of the page
        to render as 'cut page'.
        """
        self.draw_element_border(self.cursor, q_header_size)
        self.hide_bottom_page_border()
        remaining_height = full_elem_height - self.cursor + self.MARGIN_BOTTOM + self.LINE_JUMP * 2
        return remaining_height

    def draw_element_cut_border_full_page(self, remaining_height):
        """
        Draw two lines on the page (left and right) for the element's borders
        """
        self.pdf.setStrokeColorRGB(*self.COLOR_ELEMENT_RECTANGLE_STROKE)
        self.pdf.line(
            self.MARGIN_BASE,
            self.MARGIN_BOTTOM,
            self.MARGIN_BASE,
            self.PAGE_HEIGHT - self.MARGIN_BASE
        )
        self.pdf.line(
            self.PAGE_WIDTH - self.MARGIN_BASE * 2,
            self.MARGIN_BOTTOM,
            self.PAGE_WIDTH - self.MARGIN_BASE * 2,
            self.PAGE_HEIGHT - self.MARGIN_BASE
        )
        return remaining_height - self.PAGE_HEIGHT + self.MARGIN_BOTTOM + self.MARGIN_BASE + 50

    def draw_element_cut_border_top(self, remaining_height):
        """
        Draw a rectangle at the top of the page and then hide the top part with white rectangle
        to make a 'cut aspect'.
        """
        self.pdf.setFillColorRGB(*self.COLOR_ELEMENT_RECTANGLE_FILL)
        self.pdf.setStrokeColorRGB(*self.COLOR_ELEMENT_RECTANGLE_STROKE)
        self.pdf.roundRect(
            self.MARGIN_BASE,  # x
            self.PAGE_HEIGHT - (remaining_height + self.MARGIN_BASE) + self.LINE_JUMP * 2,  # y
            self.PAGE_WIDTH - self.MARGIN_BASE * 2,  # Width
            self.PAGE_HEIGHT + 50,  # Height, out of the page
            8,
            fill=0,
        )
        self.hide_top_page_border()

    def hide_bottom_page_border(self):
        self.pdf.setFillColorRGB(1, 1, 1)
        self.pdf.setStrokeColorRGB(1, 1, 1)
        self.pdf.rect(0, 0, self.PAGE_WIDTH, self.MARGIN_BOTTOM + 10, fill=1, stroke=0)

    def hide_top_page_border(self):
        self.pdf.setFillColorRGB(1, 1, 1)
        self.pdf.setStrokeColorRGB(1, 1, 1)
        self.pdf.rect(0, self.PAGE_HEIGHT + 20, self.PAGE_WIDTH, self.MARGIN_BASE - 10, fill=1, stroke=0)

    def draw_core_element(self, element, not_concerned, element_text, question_type_note, choices):
        self.pdf.setFillColorRGB(*self.COLOR_TEXT)
        self.pdf.setFont("UbuntuRegular", 12)

        self.draw_string_on_pdf(str(element), self.MARGIN_QUESTION)
        self.cursor -= self.LINE_JUMP
        if not_concerned:
            self.pdf.setFillColorRGB(*self.COLOR_FILL_CONCERN_NOTE)
            self.pdf.rect(
                40,
                self.cursor - 15,
                self.PAGE_WIDTH - self.MARGIN_BASE * 2,
                40,
                fill=1,
                stroke=0,
            )
            self.pdf.setFillColorRGB(*self.COLOR_TEXT_CONCERN_NOTE)
            self.draw_string_on_pdf(
                _("You are not concerned by this evaluation element"),
                self.MARGIN_QUESTION,
            )
            self.pdf.setFillColorRGB(*self.COLOR_TEXT)
            self.cursor -= self.LINE_JUMP

        self.pdf.setFont("UbuntuBold", 12)
        self.draw_string_on_pdf(element_text, self.MARGIN_QUESTION)
        self.cursor -= self.PARAGRAPH_SPACE

        self.pdf.setFont("UbuntuItalic", 12)
        self.draw_string_on_pdf(question_type_note, self.MARGIN_QUESTION)
        self.cursor -= self.PARAGRAPH_SPACE

        # CHOICES
        for choice in choices:
            self.print_choice(choice)

    def print_choice(self, choice):
        """
        This method prints an answer and a radio button or checkbox on the same line
        """
        # circle
        self.pdf.setStrokeColorRGB(*self.COLOR_TITLE)
        self.pdf.setFillColorRGB(*self.COLOR_TITLE)
        self.pdf.setLineWidth(2)
        self.pdf.circle(
            self.MARGIN_ANSWER_CIRCLE,
            self.cursor + 4,
            7,
            fill=choice.is_ticked,
            stroke=1,
        )
        self.pdf.setLineWidth(1)

        # choice text
        self.pdf.setFillColorRGB(*self.COLOR_TEXT)
        self.pdf.setFont("UbuntuRegular", 12)
        self.draw_string_on_pdf(choice.master_choice.answer_text, self.MARGIN_ANSWER)
        self.cursor -= self.PARAGRAPH_SPACE

    def draw_justification_and_notes(self, formatted_justification, formatted_notes):
        """
        Draw the justification and the notes depending on the available height on the current page.
        If there is not enough height, return the remaining list of texts to write.
        :param formatted_justification: list of dictionaries which contains key 'text' which has
         the text split in a list of string as value, and there are also keys/values for the html format
        :param formatted_notes: same as formatted_justification but for the notes
        """
        remaining_justification = []
        remaining_notes = []
        self.pdf.setFillColorRGB(*self.COLOR_TEXT)
        self.pdf.setFont("UbuntuRegular", 12)
        if formatted_justification and len(formatted_justification) > 0:
            if self.cursor - self.LINE_BREAK * 4 < self.MARGIN_BOTTOM:
                # If not the space to write the block "Answer justification" plus 3 lines
                remaining_justification = formatted_justification
            else:
                self.pdf.setFont("UbuntuBold", 12)
                self.draw_string_on_pdf(_("Your answer justification:"), self.MARGIN_NOTES)
                self.pdf.setFont("UbuntuRegular", 12)
                remaining_justification = self.draw_html_on_pdf(formatted_justification)
                if not remaining_justification or len(remaining_justification) == 0:
                    # Means there was enough height for the justification on this page
                    self.cursor -= self.PARAGRAPH_SPACE
                    self.cursor -= self.LINE_JUMP
        if formatted_notes and len(formatted_notes) > 0 and len(remaining_justification) == 0:
            # User notes to write and also no remaining justification, other way it means no more space on the page
            if self.cursor - self.LINE_BREAK * 4 < self.MARGIN_BOTTOM:
                # If not the space to write the block "Answer justification" plus 3 lines
                remaining_notes = formatted_notes
            else:
                self.pdf.setFont("UbuntuBold", 12)
                self.draw_string_on_pdf(_("My notes:"), self.MARGIN_NOTES)
                self.pdf.setFont("UbuntuRegular", 12)
                remaining_notes = self.draw_html_on_pdf(formatted_notes)
        if len(remaining_notes) == 0 and len(remaining_justification) == 0:
            # If no remaining text to write, do a line jump to separate with next element
            self.cursor -= self.PARAGRAPH_SPACE
            self.cursor -= self.LINE_JUMP * 2
        elif len(remaining_justification) > 0:
            # Remain justification to write so the notes haven't been written
            remaining_notes = formatted_notes
        return remaining_justification, remaining_notes

    def element_size(self, elem_content):
        """
        returns the pixel height of an element(question, answers and notes)
        """
        core_size = 0
        extra_size = 0
        # each text line takes 15 pixels
        # we add 10 pixels for space between paragraphs
        core_size += self.PARAGRAPH_SPACE + self.LINE_BREAK * self.get_line_count(
            elem_content["elem_text"], "UbuntuRegular", 12, 480
        )
        core_size += self.LINE_BREAK
        core_size += self.PARAGRAPH_SPACE + self.LINE_BREAK * self.get_line_count(
            elem_content["element_text"], "UbuntuBold", 12, 480
        )
        core_size += self.PARAGRAPH_SPACE + self.LINE_BREAK * self.get_line_count(
            elem_content["question_type_note"], "UbuntuItalic", 12, 480
        )

        if elem_content["not_concerned"]:
            # this block takes 2 lines
            core_size += self.LINE_BREAK * 2 + self.PARAGRAPH_SPACE

        for choice in elem_content["choices"]:
            core_size += self.PARAGRAPH_SPACE + self.LINE_BREAK * self.get_line_count(
                choice.master_choice.answer_text, "UbuntuRegular", 12, 450
            )
        if "user_notes" in elem_content:
            # The "My notes: " text takes 1 line
            extra_size += self.LINE_JUMP
            extra_size += self.PARAGRAPH_SPACE + count_total_height(elem_content["formatted_notes"])
        if "user_justification" in elem_content:
            extra_size += self.LINE_JUMP
            extra_size += self.PARAGRAPH_SPACE + count_total_height(elem_content["formatted_justification"])

        return core_size, extra_size + core_size

    def draw_string_on_pdf(self, string, x):
        """
        This method draws the string on pdf at coordinates x in param and y = self.cursor
        This is used for classic text (text of the assessment).
        """
        string = remove_markdownify_italic(remove_markdown_bold(string))
        size = self.pdf.stringWidth(string) / (
                self.PAGE_WIDTH - self.MARGIN_BASE - x - 25
        )
        if int(len(string) / size) < 1:
            list_string = [string]
        else:
            list_string = textwrap.wrap(string, int(len(string) / size))
        for s in list_string:
            self.pdf.drawString(x, self.cursor, s)
            self.cursor -= self.LINE_BREAK

    def split_complex_string(self, string, x):
        """
        Splits a string with its linebreak and to fit the page width.
        Returns the list of the strings by line.
        """
        split_list = string.split('\r\n')
        split_list = manage_html_list(split_list)
        formatted_list = []
        for row in split_list:
            row_margin = self.manage_margin_left(x, row)
            font_size = set_font_size(row)
            row_text = re.sub(r'<(.|\n)*?>', '', row)
            row_text = manage_special_characters(row_text)
            row_size = self.pdf.stringWidth(row_text, 'UbuntuRegular', font_size) / \
                (self.PAGE_WIDTH - self.MARGIN_BASE - row_margin - 25)
            row_format_dic = self.format_html_text(row)
            row_format_dic["margin_left"] = row_margin
            row_format_dic["font_size"] = font_size
            row_format_dic["text_with_tags"] = \
                re.sub(
                    r'</?(h[1-6]|pre|p( style="margin-left:[0-9]+px")?|div|address|([uo])l|ol n=[0-9]+|li|\n)*?>',
                    '',
                    row
                )
            if row_size > 1:
                row_split = textwrap.wrap(row_text, int(len(row_text) / row_size))
                [row_format_dic['text'].append(val) for val in row_split]
                row_format_dic = self.calculate_height(row_format_dic)
                formatted_list.append(row_format_dic)
            else:
                row_format_dic['text'] = [row_text]
                formatted_list.append(row_format_dic)

        return formatted_list

    def format_html_text(self, text):
        """
        Initiates a dictionary with some of the specific properties of the text, used later to draw the text.
        """
        decomposition_dic = {
            "text": [],
            "text_with_tags": '',
            "margin_left": self.manage_margin_left(0, text),
            "height": self.LINE_BREAK,
            "font_size": 12,
            "bullet": text.count('<ul>') == 1,
            "numbering": manage_numbering_list(text),
        }

        return decomposition_dic

    def manage_margin_left(self, x, row):
        """
        This function increase the x-axis if there is a margin-left (indent) and if it is a list
        """
        additional_margin_left = x
        margin_left_list = re.findall(r'"margin-left:([0-9]*)px"', row)
        if len(margin_left_list) == 1:
            additional_margin_left += int(margin_left_list[0])
        tabulations = re.findall('\t', row)
        additional_margin_left += len(tabulations) * self.MARGIN_BASE
        return additional_margin_left

    def calculate_height(self, format_dic):
        """
        Calculate the height that the text of the dic will take in the page,
        depending of the styles, font size, etc.
        """
        height = len(format_dic['text']) * self.LINE_BREAK
        height = height * format_dic['font_size'] / 12
        format_dic['height'] = height
        return format_dic

    def draw_html_on_pdf(self, formatted_list):
        """
        Draw a text on the pdf which may require a special format (bold, italic, indent, etc).
        This is used to draw the user justifciations and the user notes.
        """
        i = 0
        while i < len(formatted_list) and self.cursor - formatted_list[i]['height'] > self.MARGIN_BOTTOM:
            # OK, space to write the text block
            format_dic = formatted_list[i]
            text_list = format_dic['text']
            self.pdf.setFont("UbuntuRegular", format_dic["font_size"])
            if format_dic["bullet"]:
                self.pdf.setFillColorRGB(*self.COLOR_TEXT)
                self.pdf.circle(format_dic['margin_left'] - 5, self.cursor + 5, 3.5, stroke=1, fill=1)
            if format_dic["numbering"]:
                self.pdf.drawString(format_dic['margin_left'] - 10, self.cursor, f'{format_dic["numbering"]}. ')
            if len(re.findall(r'<(.|\n)*?>', format_dic["text_with_tags"])) > 0:
                # If html, draw as paragraph
                self.draw_paragraph(format_dic)
                self.cursor -= int(format_dic['height'])
            else:
                # Text with html special format so draw it
                for text in text_list:
                    self.pdf.drawString(format_dic['margin_left'], self.cursor, text)
                    self.cursor -= self.LINE_BREAK
            i += 1
        if i < len(formatted_list):
            # Means lack of space
            return formatted_list[i:]
        else:
            return []

    def draw_centered_string_on_pdf(self, string, width):
        """
        This method draws the string centered on pdf, y = self.cursor
        """
        string = remove_markdownify_italic(remove_markdown_bold(string))
        text_size = self.pdf.stringWidth(string) / width
        list_string = textwrap.wrap(string, int(len(string) / text_size))
        for s in list_string:
            self.pdf.drawCentredString(self.PAGE_WIDTH / 2, self.cursor, s)
            self.cursor -= self.LINE_BREAK

    def draw_paragraph(self, format_dic):
        """
        Method to draw a paragraph on the pdf which can contains inline html tags (bold, italic, color, etc)
        """
        message_style = ParagraphStyle('Normal')
        message_style.linkUnderline = 1
        message = self.manage_html_tags(format_dic['text_with_tags'])
        message = Paragraph(message, style=message_style)
        message.wrap(
            self.PAGE_WIDTH - self.MARGIN_NOTES - self.MARGIN_BASE,  # Available width
            format_dic["height"]  # Available height
        )
        message.drawOn(self.pdf, format_dic['margin_left'], self.cursor)

    def manage_html_tags(self, text):
        """
        Last formatting before drawing the paragraph
        Replace some tags with reportlab required tags.
        Manage the color of the text and for the background
        """
        text = text.replace('<span', '<p').replace('</span', '</p')
        text = re.sub(r'<p style="color:(#[0-9a-z]+)">(.*)(<\/p>)', r'<font color="\1">\2</font>', text)
        text = re.sub(r'<p style="background-color:(#[0-9a-z]+)">(.*)(<\/p>)', r'<font  backcolor="\1">\2</font>', text)
        text = text.replace('<a', '<a color="#5550ff"')
        text = text.replace('<em', '<font name="UbuntuItalic"').replace('</em', '</font')
        text = text.replace('<strong', '<font name="UbuntuBold"').replace('</strong', '</font')
        text = text.replace('<s>', '<strike>').replace('</s>', '</strike>')
        text = f'<font size="12" name="UbuntuRegular" color="{self.COLOR_TEXT}">' + text + '</font>'
        return text

    def get_line_count(self, string, font_name, font_size, line_width):
        """
        This function returns the number of line used by the string
        """
        line_count = stringWidth(string, font_name, font_size) / line_width
        symbols_per_line = int(len(string) / line_count)
        # textwrap.wrap is used because it does not line break mid-word
        return len(textwrap.wrap(string, symbols_per_line))

    def page_break(self, evaluation_name, section_order_id=None):
        """
        This method jumps to the next pdf page and initialize it
        """
        self.draw_footer(evaluation_name, section_order_id)
        self.pdf.showPage()
        self.cursor = self.PAGE_HEIGHT

    def draw_footer(self, evaluation_name, section_order_id=None):
        self.cursor = 40
        self.draw_string_on_pdf(
            str(self.page_num), self.PAGE_WIDTH - self.MARGIN_QUESTION - 60
        )
        self.cursor = 40
        self.page_num += 1
        self.draw_centered_string_on_pdf(evaluation_name, 300)
        self.cursor = 40
        if section_order_id is not None:
            self.draw_string_on_pdf(
                f"{_('Section')} {section_order_id}", self.MARGIN_QUESTION
            )

    def get(self, request, *args, **kwargs):
        context = {}
        organisation_id = kwargs.get("orga_id")
        organisation = get_object_or_404(Organisation, id=organisation_id)

        # Check if the user is member of the org, if not, return HttpResponseForbidden
        if not membership_security_check(request, organisation=organisation):
            return redirect("home:homepage")

        evaluation = get_object_or_404(
            Evaluation, id=kwargs.get("pk"), organisation=organisation
        )

        # If the evaluation is finished, which should always be the case here,
        # set the score of the evaluation
        if evaluation.is_finished:

            # If the scoring system has changed,
            # it set the max points again for the evaluation, sections, EE
            success_max_points = manage_evaluation_max_points(
                request=request, evaluation_list=[evaluation]
            )
            if not success_max_points:
                return redirect("home:user-profile")

            # Get the score and calculate it if needed
            evaluation_score_dic = manage_evaluation_score(
                request=request, evaluation_list=[evaluation]
            )
            if evaluation_score_dic[evaluation.id]:
                context["evaluation_score"] = evaluation_score_dic[evaluation.id]
            # Error to get the score, the score is None so redirection
            else:
                return redirect("home:user-profile")

            context[
                "dict_sections_elements"
            ] = evaluation.get_dict_sections_elements_choices()
            context["evaluation"] = evaluation
            context["organisation"] = organisation
            context['nb_risks_exposed'], context['len_exposition_dic'], context['exposition_dic'] = \
                manage_evaluation_exposition_score(request, evaluation)
            today_date = date.today().strftime("%Y-%m-%d")
            evaluation_name = evaluation.name.replace(" ", "-")
            organisation_name = organisation.name.replace(" ", "-")
            filename = f"{today_date}-{evaluation_name}-{organisation_name}-Labelia-Labs.pdf"
            filename = filename.replace("_", "-")
            return FileResponse(
                self.print_pdf(context), as_attachment=True, filename=filename
            )
        else:
            capture_message(
                f"[html_forced] The user {request.user.email}, "
                f"with IP address {get_client_ip(request)} "
                f"forced the button to valid the evaluation"
                f" (id {evaluation.id}) to access the results"
            )
            messages.warning(request, _("You cannot do this action!"))
            return redirect("home:user-profile")


def convert_exposition_dic_to_data(exposition_dic, size):
    data = [[_("Risk domain"), _("Exposition to the risk")]]
    for key, value in exposition_dic.items():
        risk = key.risk_domain
        if value:
            text = format_string_to_paragraph(risk, size)
            data.append([Paragraph(f'''<b>{text}</b>'''), _("Exposed")])
        else:
            text = format_string_to_paragraph(risk, size)
            data.append([Paragraph(f'''<b>{text}</b>'''), _("Not exposed")])
    return data


def set_font_size(text):
    """
    Set the font size of the text, depending of the html tag (h1, h2, ...)
    If not a title tag, return 12, the default font_size
    """
    matching_font = {
        '1': 26,
        '2': 21,
        '3': 18,
        '4': 16,
        '5': 14,
        '6': 12,
    }
    html_tag = re.findall(r'<h([1-6])>', text)
    if len(html_tag) == 1:
        return matching_font.get(html_tag[0], 12)
    else:
        return 12


def count_total_height(formatted_list):
    """
    Returns the total height
    """
    count = 0
    for dic in formatted_list:
        count += dic["height"]
    return count


def manage_html_list(split_text):
    """
    Function used to remove the lines with the <ol> <ul> html tags and format the
    lines with <li> tags to keep the information.
    """
    val_to_add = ''
    new_data = []
    numbering = []
    bullet_depth = 0
    skip_value = False
    for i, val in enumerate(split_text):
        if len(numbering) > 0 and val.count('<li>') >= 1:
            val_to_add = f'<ol n={numbering[-1]}>'
            numbering[-1] += 1
        if val.count('<ol>') >= 1:
            numbering.append(1)
            continue
        elif val.count('<ul>') >= 1:
            val_to_add = '<ul>'
            bullet_depth += 1
            continue
        elif val.count('</ul>') >= 1:
            bullet_depth -= 1
            skip_value = True
            if not bullet_depth:
                val_to_add = ''
        elif val.count('</li>') >= 1 and val.count('<li>') == 0:
            continue
        elif val.count('</ol>') >= 1 and len(numbering) > 0:
            numbering = numbering[:-1]
            val_to_add = ''
            continue
        elif val.count('<pre>') >= 1:
            val_to_add = '<pre>'
            continue
        elif val.count('</pre>') >= 1:
            new_data.append(val_to_add + val)
            val_to_add = ''
            continue
        if not skip_value:
            new_data.append(val_to_add + val)
        skip_value = False
    return new_data


def manage_numbering_list(text):
    """
    Return the numbering value if there is one, else 0
    """
    numbering_list = re.findall(r'<ol n=([0-9]+)>', text)
    if len(numbering_list) == 1:
        val = int(numbering_list[0])
    else:
        val = 0
    return val


def manage_special_characters(text):
    """
    Unescape the special characters
    """
    return unescape(text)


def format_string_to_paragraph(text, size):
    split = [text[i:i + size] for i in range(0, len(text), size)]
    return split[0] + ''.join(t.replace(' ', '<br/>', 1) for t in split[1:])
