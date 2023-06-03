from assessment.models import (
    Assessment,
    ElementChangeLog,
    ExternalLink,
    MasterChoice,
    MasterEvaluationElement,
    MasterSection,
)
from home.models import ReleaseNote
from modeltranslation.translator import TranslationOptions, register


@register(Assessment)
class AssessmentTranslationOptions(TranslationOptions):
    # Add new fields to TRANSLATED_FIELDS in models/assessment
    fields = ("name",)


@register(MasterSection)
class MasterSectionTranslationOptions(TranslationOptions):
    # Add new fields to TRANSLATED_FIELDS in models/assessment
    fields = (
        "name",
        "description",
        "keyword",
    )


@register(MasterEvaluationElement)
class MasterEvaluationElementTranslationOptions(TranslationOptions):
    # Add new fields to TRANSLATED_FIELDS in models/assessment
    fields = ("name", "question_text", "explanation_text", "risk_domain")


@register(MasterChoice)
class MasterChoiceTranslationOptions(TranslationOptions):
    # Add new fields to TRANSLATED_FIELDS in models/assessment
    fields = ("answer_text",)


@register(ExternalLink)
class ExternalLinkTranslationOptions(TranslationOptions):
    # Add new fields to TRANSLATED_FIELDS in models/assessment
    fields = ("text",)


@register(ReleaseNote)
class ReleaseNoteTranslationOptions(TranslationOptions):
    fields = ("text",)
    required_languages = {"default": ("text",)}


@register(ElementChangeLog)
class ElementChangeLogTranslationOptions(TranslationOptions):
    fields = (
        "edito",
        "pastille",
    )
