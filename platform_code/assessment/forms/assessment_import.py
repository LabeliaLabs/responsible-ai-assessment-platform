from django import forms


class JsonUploadForm(forms.Form):
    """
    This is the form used to import the assessment : json of the assessment, json of the choice scoring
    and if required, the upgrade json
    By default the upgrade json is not required and it will raise a message/error to the user if it is
    """
    assessment_json_file = forms.FileField()
    scoring_json_file = forms.FileField()
    upgrade_json_file = forms.FileField(required=False, help_text="Json file is the assessment (json) with the version "
                                                                  "convertible into a float (ex: '1.0') and upgrade "
                                                                  "file is the json where all the differences between "
                                                                  "this assessment and the assessments in the DB are "
                                                                  "registered. You don't need to provide and upgrade "
                                                                  "json when it's the first assessment in the database."
                                        )  # help text not displayed


class ImportAssessmentNewLanguageForm(forms.Form):
    """
    This form is used in admin/assessment to import the assessment selected in a new language
    """
    assessment_file = forms.FileField()
