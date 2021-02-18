from datetime import date, datetime
import io
import logging
import reportlab
import textwrap

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

from assessment.models import Evaluation
from assessment.models import Organisation
from assessment.utils import (
    get_client_ip,
    remove_markdown_bold,
    remove_markdownify_italic,
)
from assessment.views.utils.security_checks import membership_security_check
from assessment.views.utils.utils import (
    manage_evaluation_score,
    manage_evaluation_max_points,
)

logger = logging.getLogger("monitoring")


class ResultsPDFView(LoginRequiredMixin, DetailView):
    """
    This view defines the PDF page of the results of an evaluation,
    with the score and the overall evaluation and choices
    It is accessible only if the evaluation is finished.
    """

    model = Evaluation
    login_url = "home:login"
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
        self.pdf.setProducer("Substra Fondation")
        self.pdf.setCreator("Substra Fondation")
        self.pdf.setTitle("Substra Assessment " + date.today().strftime("%Y/%m/%d"))
        self.pdf.setSubject("Substra Assessment " + date.today().strftime("%Y/%m/%d"))

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
        self.pdf.setFont("UbuntuRegular", 25)
        self.pdf.drawCentredString(
            self.PAGE_WIDTH / 2, self.cursor, _("Synthetic evaluation score")
        )
        self.cursor -= self.LINE_JUMP * 2
        self.pdf.drawCentredString(
            self.PAGE_WIDTH / 2,
            self.cursor,
            str(context["evaluation_score"]) + " / 100",
        )
        self.cursor -= self.LINE_JUMP * 2

        # score per section
        self.pdf.setFont("UbuntuRegular", 25)
        self.pdf.drawCentredString(
            self.PAGE_WIDTH / 2, self.cursor, _("Score per section")
        )
        self.cursor -= self.LINE_JUMP * 2
        self.pdf.setFont("UbuntuRegular", 12)
        for section in context["dict_sections_elements"]:
            string = f"{_('Section')} {section.id}: {section.master_section.name}"
            self.draw_centered_string_on_pdf(string, 500)
            section_points = (section.calculate_score_per_section() / section.max_points) * 100
            self.draw_centered_string_on_pdf(
                f"{section_points:.1f} %",
                400,
            )
            self.cursor -= self.PARAGRAPH_SPACE
        self.cursor -= self.LINE_JUMP

        # explanations text
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
                "that you can consult on assessment.substra.ai"
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
            f"PDF generated on {today_date} at {current_time} UTC by the assessment.substra.ai platform. "
            f"This is a self-assessment realized by the organisation {organisation_name}. "
            "It has not been verified or audited by Substra Foundation."
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
        if element.user_notes:
            element_content["user_notes"] = element.user_notes

        elem_height = self.element_size(element_content)

        # if the element does not fit in the current page
        # => page break
        if self.cursor - elem_height < self.MARGIN_BOTTOM:
            self.page_break(
                evaluation_name=element.section.evaluation.name,
                section_order_id=element.section.master_section.order_id,
            )

        q_header_size = self.PARAGRAPH_SPACE + self.LINE_BREAK * self.get_line_count(
            str(element), "UbuntuRegular", 12, 480
        )
        self.draw_element_border(elem_height, q_header_size)

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

        # NOTES
        if element.user_notes:
            self.draw_string_on_pdf(_("My notes") + ":", self.MARGIN_NOTES)
            self.draw_string_on_pdf(element.user_notes, self.MARGIN_NOTES)
            self.cursor -= self.PARAGRAPH_SPACE
        self.cursor -= self.LINE_JUMP * 2

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

    def element_size(self, elem_content):
        """
        returns the pixel height of an element(question, answers and notes)
        """
        size = 0
        # each text line takes 15 pixels
        # we add 10 pixels for space between paragraphs
        size += self.PARAGRAPH_SPACE + self.LINE_BREAK * self.get_line_count(
            elem_content["elem_text"], "UbuntuRegular", 12, 480
        )
        size += self.LINE_BREAK
        size += self.PARAGRAPH_SPACE + self.LINE_BREAK * self.get_line_count(
            elem_content["element_text"], "UbuntuBold", 12, 480
        )
        size += self.PARAGRAPH_SPACE + self.LINE_BREAK * self.get_line_count(
            elem_content["question_type_note"], "UbuntuItalic", 12, 480
        )

        if elem_content["not_concerned"]:
            # this block takes 2 lines
            size += self.LINE_BREAK * 2 + self.PARAGRAPH_SPACE

        for choice in elem_content["choices"]:
            size += self.PARAGRAPH_SPACE + self.LINE_BREAK * self.get_line_count(
                choice.master_choice.answer_text, "UbuntuRegular", 12, 450
            )
        if "user_notes" in elem_content:
            # The "My notes: " text takes 1 line
            size += self.LINE_JUMP
            size += self.PARAGRAPH_SPACE + self.LINE_BREAK * self.get_line_count(
                elem_content["user_notes"], "UbuntuRegular", 12, 475
            )
        return size

    def draw_string_on_pdf(self, string, x):
        """
        This method draws the string on pdf at coordinates x in param and y = self.cursor
        it adds as line breaks as needed
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
            str(self.page_num), self.PAGE_WIDTH - self.MARGIN_QUESTION - 20
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
            today_date = date.today().strftime("%Y-%m-%d")
            evaluation_name = evaluation.name.replace(" ", "-")
            organisation_name = organisation.name.replace(" ", "-")
            filename = f"{today_date}-{evaluation_name}-{organisation_name}-Substra-Foundation.pdf"
            filename = filename.replace("_", "-")
            return FileResponse(
                self.print_pdf(context), as_attachment=True, filename=filename
            )
        else:
            logger.warning(
                f"[html_forced] The user {request.user.email}, "
                f"with IP address {get_client_ip(request)} "
                f"forced the button to valid the evaluation"
                f" (id {evaluation.id}) to access the results"
            )
            messages.warning(request, _("You cannot do this action!"))
            return redirect("home:user-profile")
