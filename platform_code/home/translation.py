from home.models import PlatformText, ReleaseNote
from modeltranslation.translator import TranslationOptions, register


@register(ReleaseNote)
class ReleaseNoteTranslationOptions(TranslationOptions):
    fields = ("text",)
    required_languages = {"default": ("text",)}


@register(PlatformText)
class PlatformTextTranslationOptions(TranslationOptions):
    fields = ("homepage_text",)
    required_languages = {"default": ("homepage_text",)}
