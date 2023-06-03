import json


def check_and_valid_scoring_json(*args, **kwargs):
    """
    This function is used when we import a json for the scoring, in ScoringSystemForm.
    We need to check that the choices are the same that in the assessment
    """

    # Case: we test the json
    success = False
    if "json" in kwargs:
        dict_data = kwargs.get("json")
    else:
        json_data = kwargs.get("decoded_file")
        if json_data is not None:
            try:
                dict_data = json.loads(json_data)
            except json.JSONDecodeError as e:
                return (
                    success,
                    f"There is an issue in your json architecture. Please verify you file. Error {e}",
                )

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
                    return success, f"Missing choice in the json {numbering}"

                # Check the values are numbers
                try:
                    float(dict_data[numbering])
                except ValueError as e:
                    # TODO add logs
                    return (
                        success,
                        f"The value {dict_data[numbering]} must be convertible into a float like '0.5', error {e}",
                    )
                # If the master_choice sets conditions intra or inter, it must has not points associated
                if (
                    master_choice.is_concerned_switch
                    or master_choice.has_master_element_conditioned_on()
                ):
                    # TODO tests
                    # numbering should exist in dict_data
                    if float(dict_data[numbering]) != 0.0:
                        return (
                            success,
                            f"The master_choice {numbering} has conditions intra/inter but has points associated "
                            f"({dict_data[numbering]}), should be 0.",
                        )

    # Reverse test, check if all the json keys (items) are well in the assessment's choices database
    for key in dict_data.keys():
        if key not in list_number:
            return success, f"The choice {key} is not in the assessment but in the json"

    return True, "The scoring is ok to be imported"
