from modeltranslation.translator import register, TranslationOptions

from assessment.models import (
    Assessment,
    MasterSection,
    MasterEvaluationElement,
    MasterChoice,
    ExternalLink,
)
from home.models import ReleaseNote


@register(Assessment)
class AssessmentTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(MasterSection)
class MasterSectionTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'keyword',)


@register(MasterEvaluationElement)
class MasterEvaluationElementTranslationOptions(TranslationOptions):
    fields = ('name', 'question_text', 'explanation_text')


@register(MasterChoice)
class MasterChoiceTranslationOptions(TranslationOptions):
    fields = ('answer_text',)


@register(ExternalLink)
class ExternalLinkTranslationOptions(TranslationOptions):
    fields = ('text',)


@register(ReleaseNote)
class ReleaseNoteTranslationOptions(TranslationOptions):
    fields = ('text',)
    required_languages = {'default': ('text',)}
