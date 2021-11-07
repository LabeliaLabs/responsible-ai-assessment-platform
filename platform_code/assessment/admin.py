from django.contrib import admin

from assessment.admin_utils.assessment_import import JsonUploadAssessmentAdmin
from assessment.admin_utils.evaluation_admin import EvaluationElementWeightAdmin, EvaluationAdmin
from assessment.admin_utils.master_choice_admin import MasterChoiceAdmin
from assessment.admin_utils.master_element_admin import MasterEvaluationElementAdmin
from assessment.admin_utils.element_change_log_admin import ElementChangeLogAdmin
from assessment.admin_utils.master_section_admin import MasterSectionAdmin
from assessment.admin_utils.scoring_import import ScoringAdmin
from assessment.admin_utils.labelling_admin import LabellingAdmin

from assessment.models import (
    Evaluation,
    Assessment,
    Choice,
    EvaluationElement,
    Section,
    ScoringSystem,
    MasterChoice,
    MasterSection,
    MasterEvaluationElement,
    ExternalLink,
    EvaluationElementWeight,
    Upgrade,
    EvaluationScore,
    Labelling,
    ElementChangeLog,
)

admin.site.register(MasterSection, MasterSectionAdmin)
admin.site.register(MasterEvaluationElement, MasterEvaluationElementAdmin)
admin.site.register(MasterChoice, MasterChoiceAdmin)
admin.site.register(ExternalLink)
admin.site.register(EvaluationElementWeight, EvaluationElementWeightAdmin)
admin.site.register(Evaluation, EvaluationAdmin)
admin.site.register(Section)
admin.site.register(EvaluationElement)
admin.site.register(Choice)
admin.site.register(Upgrade)
admin.site.register(ElementChangeLog, ElementChangeLogAdmin)
admin.site.register(EvaluationScore)
admin.site.register(Labelling, LabellingAdmin)
admin.site.register(Assessment, JsonUploadAssessmentAdmin)
admin.site.register(ScoringSystem, ScoringAdmin)
