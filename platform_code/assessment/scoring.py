import json


def check_and_valid_scoring_json(*args, **kwargs):
    """
    This function is used when we import a json for the scoring, in ScoringSystemForm.
    We need to check that the choices are the same that in the assessment
    """

    # Case: we test the json
    json_data = kwargs.get("decoded_file")
    if json_data is not None:
        dict_data = json.loads(json_data)

    assessment = kwargs.get("assessment")

    list_number = []
    count_choice = 0
    for master_section in assessment.mastersection_set.all():
        for master_element in master_section.masterevaluationelement_set.all():
            for master_choice in master_element.masterchoice_set.all():
                numbering = master_choice.get_numbering()
                # Add the master_choice number (1.1.a) to the list
                list_number.append(numbering)
                count_choice += 1
                # If the master choice is present in the assessment but not in the imported scoring file
                if numbering not in dict_data.keys():
                    raise ValueError("Missing choice in the json", numbering)

                # Check the values are numbers
                try:
                    float(dict_data[numbering])
                except ValueError as e:
                    # TODO add logs
                    print(
                        f"The scoring choice value must be convertible into a float like '0.5', error {e}",
                        numbering,
                        dict_data[numbering],
                    )

    # Reverse test, check if all the json keys (items) are well in the assessment's choices database
    for key in dict_data.keys():
        if key not in list_number:
            raise ValueError(
                f"The choice {key} is not in the assessment but in the json"
            )
