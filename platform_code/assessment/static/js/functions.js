// This file contains the javascript functions used in the project

function manageAjaxRequest(ajax, form, ...args) {
// Open the ajax object (XMLHttpRequest type)
// Set headers to ajax object: crsf, action, method, etc
// Send the request with the form and the args data
// Args: string, with the format: "key=value"
    ajax.open("POST", form.getAttribute("action"), true);
    ajax.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    ajax.setRequestHeader('X-Requested-With', 'XMLHttpRequest');  // allow django to recognize it is ajax
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    ajax.setRequestHeader("X-CSRFToken", csrftoken);
    let arg = args;  // array
    var data = arg.map(i => "&" + i);  // add "&" before each pair of key=value
    var additionalData = data.join();
    ajax.send(convertFormToString(form) + additionalData);
}

function convertFormToString(form) {
// For a form, for all the fields, add them to a string which is returned
// Used to pass form data into ajax call
    var formData = new FormData(form);
    var data = "";
    for (var pair of formData.entries()) {
        data = data + "&" + pair[0].toString() + "=" + encodeURIComponent(pair[1].toString());
    }
    return data
}

function timerMessageSlow(parentMessage, classCSS, timer, slow) {
// parentMessage: element of the DOM
// classCSS: string ('display-none' or 'hidden-div')
// timer: number (thousands, ex 5000 for 5 seconds)
// slow: boolean
// This function sets a timer to display the div "parentMessage". First it removes the css class (either 'hidden-div'
// or 'display-none', depending on the fact the height of the div is used or not). So the div is displayed as well
// as the children containing the messages and after a timer (number, ex 5000), the css class is added again to mask the
// div and the content of the div is destroyed.
    parentMessage.classList.remove(classCSS);
    // First timeout to create a slow remove effect
    if (slow) {
        setTimeout(function() {
            parentMessage.classList.add("transition");
        }, timer);
    }
    // After the css effect (1s) or not (slow=false), we clean the div
    var delaySlow = slow ? 1000 : 0;
    setTimeout(function() {
        parentMessage.textContent = '';
        parentMessage.classList.add(classCSS);
        parentMessage.classList.remove("transition");
    }, timer + delaySlow);
}

// Functions to manage resources

function like(element_id, resource_id) {
    var form = document.getElementById("like_resources"+element_id);
    var ajax = new XMLHttpRequest();

    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            if(response['success']) {
                var textNoResource = document.getElementById("no-resources-message");
                var textNoResourceTemp = document.getElementById("no-resources-message-temp");
                // If the user liked a resource, so the icon is changed, the text "no resource liked" is removed,
                // and the resource is added to the "my favorite resources" tab
                if (response['like']) {
                    // We get by name so this is an array as the resource is not unique, it can exists for several
                    // elements
                    var resourceToLikeList = document.getElementsByName("resource_not_liked"+resource_id);

                    // remove the text when we like a resource
                    if ( textNoResource && !textNoResource.classList.contains("display-none") && resourceToLikeList.length >= 1) {
                        textNoResource.classList.add("display-none");
                    } else if (textNoResourceTemp && resourceToLikeList.length >= 1) {
                        textNoResourceTemp.classList.add("display-none");
                    }
                    // Change the icon of the resource, start from the end of the list as changing the name of the icon
                    // remove it from the list
                    for (var i = resourceToLikeList.length - 1; i >= 0; i--) {
                        resourceToLikeList[i].classList.replace("fa-bookmark-o", "fa-bookmark");
                        resourceToLikeList[i].setAttribute("name", "resource_liked"+resource_id);
                    }
                    //
                    var favoriteResourcesArray = document.getElementById("liked-resources-array");
                    if (favoriteResourcesArray) {
                        var resourceText = response["resource_text"];
                        // Create the resource in the favorite resources
                        var favResource = document.createElement("div");
                        favResource.innerHTML = '<div class="grid-container-2-cols" id="div_resource_fav'+resource_id+'"><div class="grid-item"><li id="resource_fav'+resource_id+'" class="object-linked list-with-disc margin-10">'+resourceText+'</li></div></div>';
                        favoriteResourcesArray.appendChild(favResource);
                    }

                } else {
                    // call the function unlikeResource
                    unlikeResource(textNoResource, textNoResourceTemp, resource_id, response);
                }
            }
        }
    }
    manageAjaxRequest(ajax, form, "resource_id=" + resource_id)
}

function unlikeResource(textNoResource, textNoResourceTemp, resource_id, response) {
    // The user unlike a resource, so the icon is changed, the resource is removed from the favorite
    // and if no resources are liked, the text is displayed
    var resourcesToUnlikeList = document.getElementsByName("resource_liked"+resource_id);

    // Change the icon
    for (var i = resourcesToUnlikeList.length - 1; i >= 0; i--){
        resourcesToUnlikeList[i].classList.replace("fa-bookmark", "fa-bookmark-o");
        resourcesToUnlikeList[i].setAttribute("name", "resource_not_liked"+resource_id);
    }
    // Remove the resource from the favorite resources array
    var favResource = document.getElementById("div_resource_fav"+resource_id);
    favResource.remove();

    // Manage the fact there is no more resource liked and the text message is displayed
    // Always act on the temp div
    if (response["no_resource_liked"] && textNoResourceTemp && textNoResourceTemp.classList.contains("display-none")) {
        textNoResourceTemp.classList.remove("display-none");
    }
}

function removeResource(resource_id){
    var form = document.getElementById(resource_id);
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200) {
            var response = JSON.parse(ajax.response);
            if (response['success']) {
                // The resource is unliked, so it is removed from the favorite
                var textNoResource = document.getElementById("no-resources-message");
                var textNoResourceTemp = document.getElementById("no-resources-message-temp");
                unlikeResource(textNoResource, textNoResourceTemp, resource_id, response);
            }
        }
    }
    manageAjaxRequest(ajax, form, "resource_id=" + resource_id);
}

// Content of the evaluation part (submit send feedback, reset answer, submit answer)

function feedback(button, id, feedbackObject) {
// this: the button to sent the feedback
// id: number (either the id of the evaluation element or the section)
// feedbackObject: string (either 'element' or 'section')
// Used to submit the feedback of a section or a element, through a modal
    var form = document.getElementById("feedback_user_"+feedbackObject+id);
    var ajax = new XMLHttpRequest();
    button.disabled = true;

    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            var feedbackMessage = document.getElementById("confirmation_feedback_"+feedbackObject+id);
            if (response['success']) {
                addMessage(feedbackMessage, response['message'], "alert-success");
            } else {
                addMessage(feedbackMessage, response['message'], "alert-danger");
            }
            timerMessageSlow(feedbackMessage, "display-none", 4000, true);
            setTimeout(function() {
                form.reset();
                button.disabled = false;
                var closeButton = document.getElementById("close-modal-"+feedbackObject+id);
                closeButton.click();
            }, 5000);
        }
    }
    manageAjaxRequest(ajax, form, feedbackObject + "_id=" + id);
}

function untickAllChoices(element_id) {
    var baseChoiceId = "id_"+element_id+"-"+element_id+"_";
    let i =0;
    do {
        var choice = document.getElementById(baseChoiceId+i);
        choice.checked = false;
        i += 1;
    } while (document.getElementById(baseChoiceId+i));
}


function resetChoice(id_form) {
    var element_id = id_form;
    untickAllChoices(element_id);
    var form = document.getElementById("form"+element_id);
    var ajax = new XMLHttpRequest();

    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
                // First thing we do is to inform the user whether the action succeeded or not
                var parentMessage = document.getElementById("confirmationform"+element_id);
                parentMessage.textContent = '';
                addMessage(parentMessage, response['message'], response["message_type"]);
                if (response['message_notes']) {
                    addMessage(parentMessage, response['message_notes'], response["message_notes_type"]);
                }
                timerMessageSlow(parentMessage, "hidden-div", 4000, true);

                if(response['success']) {
                    setSectionProgressBar(response);
                    setSectionProgressionSidebar(response);
                    // There is not necessarily a need to change the status if it was already not done!
                    if (response["element_status_changed"]) {
                       setElementEvaluationStatusNotDone(element_id);
                    }
                    if(response['no_more_condition_inter']) {
                        location.reload();
                    }
                    // If the evaluation is no more finished
                    manageEvaluationValidation(response);
                 }
             }
     }
     manageAjaxRequest(ajax, form, "reset_element_id=" + element_id);
}

function addMessage(parentElement, message, alertType) {
// This function add a div to a parentElement with a message and the class alert-type (alert-success, alert-warning or
// alert-danger)
    var messageCreated = document.createElement('div');
    messageCreated.textContent = message;
    messageCreated.classList.add("alert", alertType);
    parentElement.append(messageCreated);
}

function timerMessageSlow(parentMessage, classCSS, timer, slow) {
// parentMessage: element of the DOM
// classCSS: string ('display-none' or 'hidden-div')
// timer: number (thousands, ex 5000 for 5 seconds)
// slow: boolean
// This function sets a timer to display the div "parentMessage". First it removes the css class (either 'hidden-div'
// or 'display-none', depending on the fact the height of the div is used or not). So the div is displayed as well
// as the children containing the messages and after a timer (number, ex 5000), the css class is added again to mask the
// div and the content of the div is destroyed.
    parentMessage.classList.remove(classCSS);
    // First timeout to create a slow remove effect
    if (slow) {
        setTimeout(function() {
            parentMessage.classList.add("transition");
        }, timer);
    }
    // After the css effect (1s) or not (slow=false), we clean the div
    var delaySlow = slow ? 1000 : 0;
    setTimeout(function() {
        parentMessage.textContent = '';
        parentMessage.classList.add(classCSS);
        parentMessage.classList.remove("transition");
    }, timer + delaySlow);
}


// Validation of an evaluation element

function submitForm(id_form, element_id) {

    var form = document.getElementById(id_form);
    var ajax = new XMLHttpRequest();
    for (var instance in CKEDITOR.instances)
          CKEDITOR.instances[instance].updateElement();
    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            // First thing we do is to inform the user whether the action succeeded or not
            var parentMessage = document.getElementById("confirmation"+id_form);
            parentMessage.textContent = '';
            addMessage(parentMessage, response['message'], response["message_type"]);
            if (response['message_notes']) {
                addMessage(parentMessage, response['message_notes'], response["message_notes_type"]);
            }
            timerMessageSlow(parentMessage, "hidden-div", 4000, true);

            if (response['success']) {

                setSectionProgressBar(response);
                setSectionProgressionSidebar(response);
                if (response["element_status_changed"]) {
                    setElementEvaluationStatusDone(element_id);
                }
                if (response["no_more_condition_inter"]) {
                    location.reload();
                // todo do not reload and modify the elements
                }
                // Manage the validation button
                manageEvaluationValidation(response);
             }
            if (response['conditional_elements_list'] && response['conditional_elements_list'].length > 0) {
                for (var i=0; i < response['conditional_elements_list'].length; i++) {
                    var id_evaluation_element = response['conditional_elements_list'][i];
                    setElementEvaluationStatusDone(id_evaluation_element);
                    untickAllChoices(id_evaluation_element); // reset the choices
                    document.getElementById("temp_warning"+id_evaluation_element).style.display = "block";
                    document.getElementById("disable_element"+id_evaluation_element).disabled = true;
                    document.getElementById("validate"+id_evaluation_element).disabled = true;
                    document.getElementById("reset"+id_evaluation_element).onclick = "";
                }
            }
        }
    }
    manageAjaxRequest(ajax, form, "element_id=" + element_id);
}

function manageEvaluationValidation(response) {
// If this evaluation element is the last one of the evaluation, the permanent buttons are removed
// and the temp one is displayed, disbaled or not depending on the evaluation status
    var tempButton = document.getElementById("temp-validation-button");
    removePermanentObjectByName("validation-button");
    if (!response["evaluation_finished"]) {
        tempButton.children[0].disabled = true;
    }
    tempButton.style.display = "block";
}

function submitUserSettingsDataForm(id_form){
    var form = document.getElementById(id_form);
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            var divMessage = document.getElementById("message");
            if (response['success']) {
                addMessage(divMessage, response['message'], "alert-success");
            } else {
                addMessage(divMessage, response['message'], "alert-danger");
            }
            timerMessageSlow(divMessage, "display-none", 4000, true);
        }
    }
    manageAjaxRequest(ajax, form);
}

function submitUserSettingsPasswordForm(id_form){
    var form = document.getElementById(id_form);
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            var divMessage = document.getElementById("messagePassword");
            if (response['success']) {
                form.reset();
                addMessage(divMessage, response['message'], "alert-success");
            } else {
                var messages = response["error_messages"];
                for (message of messages){
                    addMessage(divMessage, message, "alert-danger");
                }
            }
            timerMessageSlow(divMessage, "display-none", 6000, true);
        }
    }
    manageAjaxRequest(ajax, form);
}


function setSectionProgressBar(response) {
    var progress_bar = document.getElementById("section-progress-bar");
    var progress_bar_content = document.getElementById("section-progress-bar-content");
    progress_bar.setAttribute("title", "Progression de "+response['section_progression']+"%");
    progress_bar_content.setAttribute("style", "width:"+response["section_progression"]+"%;");
    progress_bar_content.setAttribute("aria-valuenow", response['section_progression']);
    progress_bar_content.setAttribute("title", "Progression de "+response['section_progression']+"%");
}

function setSectionProgressionSidebar(response) {
// The progression is only displayed in the sidebar for screens larger than 1300px
// For these screens, the sidebar link is changed to display the new user progression
    if (screen.width > 1300) {
       var sidebarLink = document.getElementById("sidebar-section-" + response["section_order_id"]);
       var regProgression = new RegExp("[0-9]{1,3}%");
       sidebarLink.textContent = sidebarLink.textContent.replace(regProgression, response['section_progression']+"%");
    }
}

function removePermanentObjectByName(name) {
// For an evaluation element, remove all the permanent status icon
    var permanentObjectList = document.getElementsByName(name);
    for (element of permanentObjectList) {
        element.style.display = "none";
    }
}

function setElementEvaluationStatusDone(element_id) {
// This function removes the current element status to set the temporary one to done
    var newElementStatus = document.getElementById("element_status_temporary"+element_id);
    removePermanentObjectByName("permanent-status-element"+element_id);
    newElementStatus.setAttribute("style", "display: block;");
    newElementStatus.setAttribute("title", "You have answered this evaluation element");
    newElementStatus.innerHTML ='<i class="fa fa-circle fa-stack-2x"></i></span>';
}

function setElementEvaluationStatusNotDone(element_id) {
// This function the current status to set a temporary one to "not done"
    var newElementStatus = document.getElementById("element_status_temporary"+element_id);
    removePermanentObjectByName("permanent-status-element"+element_id);
    newElementStatus.setAttribute("style", "display: block;");
    newElementStatus.setAttribute("title", "You have not answered this evaluation element yet");
    newElementStatus.innerHTML ='<i class="fa fa-circle-o fa-stack-2x"></i></span>';
}

// used in the profile view to adapt the breadcrumbs
function displayTextLink(text_to_display, link_id) {
    var link_object = document.getElementById(link_id);
    link_object.innerHTML = text_to_display;
}

function changeNameEvaluation(form_id, evaluation_id) {
    var form = document.getElementById(form_id);
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            var parentMessage = document.getElementById("confirmation"+form_id);

            if (response['success']) {
                addMessage(parentMessage, response['message'], 'alert-success');
                timerMessageSlow(parentMessage, "display-none", 3000, true);
                var evalName = document.getElementById("evaluation-name");
                if (evalName) {
                    evalName.textContent = response["name"];
                } else {
                    location.reload();
                }

                setTimeout(function() {
                    var closeButton = document.getElementById("close-modal-edit-name"+evaluation_id);
                    closeButton.click();
                }, 4500);
            } else {
                addMessage(parentMessage, response['message'], 'alert-danger');
                timerMessageSlow(parentMessage, "display-none", 3000, true);
                setTimeout(function() {
                    var closeButton = document.getElementById("close-modal-edit-name"+evaluation_id);
                    closeButton.click();
                }, 4500);
            }
        }
    }
    manageAjaxRequest(ajax, form, "evaluation_id=" + evaluation_id);
}

// upgrade function used to upgrade an evaluation and block the popin from closing
function upgrade(modal_id, form_id, evaluation_id){
    var upgrade_modal = document.getElementById(modal_id);
    var form = document.getElementById(form_id);
    var textMessage = document.getElementById("upgrade_message_text"+evaluation_id);
    var upgradeMessage = document.getElementById("upgrade_message"+evaluation_id);
    upgradeMessage.classList.add("alert-warning");
    upgradeMessage.classList.remove("display-none");
    textMessage.textContent = gettext('The upgrade is in process, please wait.');
    var buttons = document.getElementsByTagName('button');
    for (var button of buttons) {
        button.disabled = true;
        button.classList.add("waiting-cursor");
    }
    document.body.style.cursor='wait'; // transform the cursor to a loading cursor
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            if (response['success']) {
                document.body.style.cursor='default';
                upgradeMessage.classList.remove("alert-warning");
                addMessage(upgradeMessage, response["message"], 'alert-success');
                timerMessageSlow(upgradeMessage, "display-none", 3000, true);
                document.location.href=response["redirection"];
            } else {
                document.body.style.cursor='default';
                for (var button of buttons) {
                    button.disabled = false;
                    button.classList.remove("waiting-cursor");
                }
                upgradeMessage.classList.remove("alert-warning");
                addMessage(upgradeMessage, response["message"], 'alert-danger');
                setTimeout(location.reload.bind(location), 3000);
            }
        }
    }
    manageAjaxRequest(ajax, form);
}

function duplicate(event, evaluationId, formId) {
    event.preventDefault();
    var form = document.getElementById(formId);
    document.body.style.cursor='wait';
    var message = document.getElementById("duplicate-message"+evaluationId);
    message.classList.remove("display-none");
    var buttons = document.getElementsByTagName('button');
    for (var button of buttons) {
        button.disabled = true;
        button.classList.add("waiting-cursor");
    }
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            document.body.style.cursor='default';
            if (response['success']) {
                // reload to user-profile/evaluation page
                document.location.href = "evaluations"
            } else {
                for (var button of buttons) {
                    button.disabled = false;
                    button.classList.remove("waiting-cursor");
                }
                message.classList.replace("alert-warning", "alter-danger");
                message.textContent = response["message"]
                setTimeout(location.reload.bind(location), 3000);
            }
        }
    }
    manageAjaxRequest(ajax, form);
}

function sendInvitation(form_id) {
// Function to add a member to the organisation, the action triggered either invites the user if it exists
// or sends an email to signup
    var sendInvitationButton = document.getElementById("sendInvitationButton");
    sendInvitationButton.disabled = true;
    var form = document.getElementById(form_id);
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            var messageInvitation = document.getElementById("confirmationInvitation");

            if (response['success']) {
                var tabMembers = document.getElementById("arrayMembers");
                var newRow = tabMembers.insertRow();
                for (var i = 0; i < tabMembers.rows[0].cells.length; i++) {
                    var newCell  = newRow.insertCell(i);
                    newCell.classList.add("case-array");
                    var newText  = document.createTextNode(response["data_user"][i]);
                    newCell.appendChild(newText);
                }
                messageInvitation.textContent = '';
                addMessage(messageInvitation, response['message'], 'alert-success');
                timerMessageSlow(messageInvitation, "hidden-div", 4500, true);
                setTimeout(function() {
                    sendInvitationButton.disabled = false;
                    form.reset();
                    document.getElementById('close-button-invitation').click();
                }, 6000);

            } else {
                addMessage(messageInvitation, response['message'], 'alert-danger');
                setTimeout(function() {
                    messageInvitation.textContent = '';
                    sendInvitationButton.disabled = false;
                    document.getElementById('close-button-invitation').click();
                }, 4000);

            }
        }
    }
    manageAjaxRequest(ajax, form);
}

function removeMember(form_id, object_id, is_pending){
// This function is used to remove a member or invitation from an organisation
// It is called in assessment/organisation/member in remove-member.html and remove-pending-member.html
// It creates an ajax request managed by SummaryView
    var form = document.getElementById(form_id);
    if (is_pending) {
        var object_removed = "delete_invitation_id";
    } else {
        var object_removed = "remove_member_id";
    }
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            var messageMember = document.getElementById("messagesMember");
            if (response['success']) {
                var tabMembers = document.getElementById("arrayMembers");
                if (is_pending) {
                    var row = document.getElementById("rowPendingMember"+ object_id);
                } else {
                    var row = document.getElementById("rowMember"+ object_id);
                }
                tabMembers.removeChild(row);
                // Fix a bug we cannot scroll the document
                document.getElementsByTagName("body")[0].style.overflow = "auto";
                addMessage(messageMember, response['message'], "alert-success");
                timerMessageSlow(messageMember, "hidden-div", 6000, true);

            } else {
                addMessage(messageMember, response['message'], 'alert-danger');
                timerMessageSlow(messageMember, "hidden-div", 6000, true);
                if (is_pending) {
                    document.getElementById("close-remove-invitation"+ object_id).click();
                } else {
                    document.getElementById("close-remove-member"+ object_id).click();
                }
            }
        }
    }
    manageAjaxRequest(ajax, form, object_removed+"=" + object_id);
}

function editRoleMember(form_id, object_id, is_pending){
// This function is used to edit the role of members or pending invitations to join the organisation
// It creates an ajax request managed by SummaryView
// It is called in assessment/organisation/member in edit-role-member.html and edit_role-pending-member.html
    var form = document.getElementById(form_id);
    if (is_pending) {
        var object_edited = "edit_invitation_id";
    } else {
        var object_edited = "edit_member_id";
    }
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            var messageMember = document.getElementById("messagesMember");
            messageMember.textContent = "";
            if (response['success']) {
                var tabMembers = document.getElementById("arrayMembers");
                if (is_pending) {
                    var row = document.getElementById("rowPendingMember"+ object_id);
                } else {
                    var row = document.getElementById("rowMember"+ object_id);
                }
                var cell = row.cells[2]
                cell.textContent = response["new_role"]
                addMessage(messageMember, response["message"], "alert-success");
            } else {
                addMessage(messageMember, response["message"], "alert-danger");
            }
            setTimeout(function() {
                if (is_pending) {
                    document.getElementById("close-edit-invitation"+ object_id).click();
                } else {
                    document.getElementById("close-edit-member"+ object_id).click();
                }
            }, 1000)
        }
    }
    manageAjaxRequest(ajax, form, object_edited + "=" + object_id);
}


function filterDashboardGraphs(formId){
    var form = document.getElementById(formId);
    var ajax = new XMLHttpRequest();

    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200) {
            var response = JSON.parse(ajax.response);
            if(response["success"]){
                    var tab_to_update = response["which_tab"];
                    switch (tab_to_update) {
                    // update users stats and graphs
                    case 0:

                        document.getElementById("nb-users-indicator").innerHTML = response["nb_users"];
                        document.getElementById("min-date-indicator").innerHTML = response["min_date"];
                        document.getElementById("min-date-indicator-2").innerHTML = response["min_date"];
                        var users_stats_table = document.getElementById("users-stats-table");
                        var months = response["months"];
                        var users_count = response["users_count"];

                        for (var i = 1, row; row = users_stats_table.rows[i]; i++) {
                               row.cells[0].innerText = months[i-1];
                               row.cells[1].innerText = users_count[i-1];
                          }
                        break;

                    // update organisations stats and graphs
                    case 1:
                        document.getElementById("nb-orgas-indicator").innerHTML = response["nb_orgas"];
                        document.getElementById("selected-orgas-filter-date").innerHTML = response["creation_date"];
                        document.getElementById("selected-orgas-filter-date-2").innerHTML = response["creation_date"];

                        // update number of organisations per sector table
                         var organisationSectorsTableStats = document.getElementById("orgas-sectors-stats-table");
                         for (var i = 1, row; row = organisationSectorsTableStats.rows[i]; i++) {
                               row.cells[0].innerText = response["sectors_list"][i-1];
                               row.cells[1].innerText = response["orgas_count_per_sector"][i-1];
                         }

                        // update number of organisations per size table
                        organisationSizesTableStats = document.getElementById("orgas-sizes-stats-table")
                         for (var i = 1, row; row = organisationSizesTableStats.rows[i]; i++) {
                               row.cells[0].innerText = response["sizes_list"][i-1];
                               row.cells[1].innerText = response["orgas_count_per_size"][i-1];
                          }
                          break;

                    // update evaluations stats and graphs
                    case 2:
                        document.getElementById("nb-total-evals").innerHTML = response["total_nb_evals"];
                        document.getElementById("nb-completed-evals").innerHTML = response["nb_completed_evals"];
                        document.getElementById("nb-in-progress-evals").innerHTML = response["nb_in_progress_evals"];
                        document.getElementById("eval-creation-date-indicator-2").innerHTML = response["eval_creation_date"];
                        document.getElementById("eval-creation-date-indicator-1").innerHTML = response["eval_creation_date"];
                        var versions = response["versions_list"];
                        var evalVersionsStatsTable = document.getElementById("evals-versions-stats-table")
                        for (var i = 1, row; row = evalVersionsStatsTable.rows[i]; i++) {
                           row.cells[0].innerHTML = "V"+versions[i-1];
                           row.cells[1].innerHTML = response["nb_evals_per_version"][i-1];
                        }
                        break;
                    }
            } else {
                var parentMessage = document.getElementById("admin-dashboard-error");
                parentMessage.textContent = '';
                addMessage(parentMessage, response["message"] ,"alert-warning");
                timerMessageSlow(parentMessage, "hidden-div", 5000, true);
            }




        }
    }
    manageAjaxRequest(ajax, form);
}


function filterLabellingStatus(formId) {
    var form = document.getElementById(formId);
    var statusValue = form.status.value;
    var labellings = Array.from(document.querySelectorAll("[name=labelling-status]"));
    labellings.forEach((item) => {
        var classList = item.closest("tr").classList;
        var status = item.textContent;
        statusValue == "All status" || statusValue == status ?
            classList.remove("display-none") : classList.add("display-none");
    })

}


function submitOrganisationForm(formId, organisation_id) {
    var form = document.getElementById(formId);
    var ajax = new XMLHttpRequest();

    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response);
            // First thing we do is to inform the user whether the action succeeded or not
            var parentMessage = document.getElementById("confirmation"+formId);
            parentMessage.textContent = '';
            addMessage(parentMessage, response['message'], response["message_type"]);
            timerMessageSlow(parentMessage, "hidden-div", 4000, true);
            if (response['success']) {
                document.getElementById("organisation-name").textContent = response["organisation_name"];
                document.getElementById("organisation-sector").textContent = response["organisation_sector"];
                document.getElementById("organisation-size").textContent = response["organisation_size"];
                document.getElementById("organisation-country").textContent = response["organisation_country"];
                // Modify the page title
                var regex = /(Organisation\s?\:\s)(.*)/gi;
                var title = document.getElementsByTagName("h1")[0];
                title.textContent = title.textContent.replace(regex, '$1' + response["organisation_name_only"])
                setTimeout(() => {
                    document.getElementById("organisation-settings-form").classList.add("transition");
                    }, 4500
                );
                setTimeout(() => {
                    document.getElementById("organisation-settings-form").classList.remove("transition");
                    document.getElementById("organisation-settings-form").classList.add("display-none");
                    }, 5500
                );
            } else {
                document.getElementById("editOrganisationSettings" + organisation_id).reset();
            }
        }
    }
    manageAjaxRequest(ajax, form);
}



function submitSectionNotes(form_id, section_id){
// this function is used to save the notes of the section
// the call is made in content-section.html
// the ajax request is managed in SectionView
   var form = document.getElementById(form_id);
   var ajax = new XMLHttpRequest();

    ajax.onreadystatechange = function() {
        if (ajax.readyState == 4 && ajax.status == 200 ) {
            var response = JSON.parse(ajax.response) ;
            var messageSectionNotes = document.getElementById("messageSectionNotes"+section_id);
            messageSectionNotes.textContent = "";
             if (response['success']) {
                addMessage(messageSectionNotes, response["message"], "alert-success");
                timerMessageSlow(messageSectionNotes, "display-none", 4000, true);
             } else {
                addMessage(messageSectionNotes, response["message"], "alert-danger");
                timerMessageSlow(messageSectionNotes, "display-none", 4000, true);
             }
        }
    }
    // Ajax post with headers, data of the form plus notes_section_id
    manageAjaxRequest(ajax, form, "notes_section_id=" + section_id);
}

function displayElementCard(cardHeaderButtonId, cardContentId) {
// Function which open the element card by simulating a click on the card headers
// when the user hover the pastille tooltip
    cardContent = document.getElementById(cardContentId);
    cardHeaderButton = document.getElementById(cardHeaderButtonId)

    if (!cardContent.classList.contains('show')) {
        cardHeaderButton.setAttribute("data-opened-with-pastille", "yes")
        cardHeaderButton.click();
    }
}

function hideElementCard(cardHeaderButtonId, cardContentId) {
// Function which closes the element card by simulating a click on the card headers
// when the user moves the cursor away from the pastille (onmouseleave)

  cardContent = document.getElementById(cardContentId);
  cardHeaderButton = document.getElementById(cardHeaderButtonId)
  opened_with_pastille = cardHeaderButton.getAttribute("data-opened-with-pastille")
  if (opened_with_pastille == "yes"){
      if (cardContent.classList.contains('show')) {
            cardHeaderButton.click();
            cardHeaderButton.setAttribute("data-opened-with-pastille", "no")

        }

  }

}

function changeIconResource(divHeader) {
    var children = divHeader.children;
    if (children) {
        var divIcon = children[0];
        if (divIcon.classList.contains("fa-plus")) {
            divIcon.classList.replace("fa-plus", "fa-minus");
        } else {
            divIcon.classList.replace("fa-minus", "fa-plus");
        }
    }
}

function topFunction() {
  document.body.scrollTop = 0; // For Safari
  document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
}

function goNextElement(counter) {
// This function is used to go to the next evaluation element in the sectionView
// When the user click on the arrow-down
// Argument 'counter' is the number of element iterations for the section
    var cardList = document.querySelectorAll(".card");
//    counter starts at 1, cardList starts at 0
    var nextCard = cardList[counter];
    var nextCardHeader = nextCard.children[0].children[0];
    var rect = nextCard.getBoundingClientRect();
    scrollSlowly(rect.top, 1);
    //Show the next card
    nextCard.children[1].classList.add("show");

}

function goPreviousElement(counter) {
// This function is used to go to the previous evaluation element in the sectionView
// When the user click on the arrow-up
// Argument 'counter' is the number of element iterations for the section
    var cardList = document.querySelectorAll(".card");
    if (counter > 1) {
        var previousCard = cardList[counter-2];
        //Show the previous card
        previousCard.children[1].classList.add("show");
        var previousCardHeader = previousCard.children[0].children[0];
        var rect = previousCard.getBoundingClientRect();
        scrollSlowly(rect.top, -1);
    }
}

function scrollSlowly(distanceScroll, direction) {
//Each 20 milliseconds, the screen is scrolled of a distanceEach (int which represents the px)
//direction is number, 1 to scroll down, -1 to scroll up
    var x = 0;
    var id = setInterval(scrollDist, 20);
    var distanceEach = 20;
    function scrollDist() {
        if (Math.abs(x) >= Math.abs(distanceScroll)) {
          clearInterval(id);
        } else {
          x = x + direction * distanceEach;
          //scrollBy a distance, which means the screen will go "dist"px below/up
          window.scrollBy(0, direction * distanceEach);
        }
    }
}

// script used to adapt the grid of the evaluations and the organisations when the small screen width (<1025)
// and when there is only one card -> display it next to the column pills
var grid = document.getElementsByTagName('tbody')[0];
var orgaCards = document.getElementsByClassName("cards-orga")[0];
// if the screen is smaller than 1025px ie the array is transformed into cards
//console.log("grid", grid, orgaCards);
if (window.screen.width < 1025) {
    if (grid && grid.childElementCount <=1) {
        grid.style.gridTemplateColumns = "auto";
        // only the case there is also only one evaluation to avoid to have the column pills moved between eval/orga
        if (orgaCards && orgaCards.childElementCount <= 1) {
            orgaCards.style.gridTemplateColumns = "auto";
        }
    }
}


//script used to archive and remove notes.
//it creates the ajax request with params, executes it, notify the result to the user and executes func()
//form name is
function ajaxRequestAndNotify(form_name, note_element_id, notification_div_name, req_arg_name, func) {
    var form = document.getElementById(form_name + note_element_id);
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function () {
        if (ajax.readyState === 4 && ajax.status === 200) {
            //notify the result to the user
            var response = JSON.parse(ajax.response);
            var parentMessage = document.getElementById(notification_div_name + note_element_id);
            addMessage(parentMessage, response['message'], response["message_type"]);
            parentMessage.classList.remove("hidden-div");
            //execute the param function
            func(response, note_element_id)
            //remove the notification after 4 secondes
            setTimeout(function () {
                parentMessage.classList.add("hidden-div");
                parentMessage.textContent = '';
            }, 4000);
        }
    }
    manageAjaxRequest(ajax, form, req_arg_name + note_element_id);
}

//function used in on profile and on evaluation to archive and unarchive notes
function archiveNote(note_element_id, notif_div) {
    ajaxRequestAndNotify("form-archive-note-", note_element_id, notif_div,
        "archive_note_id=",
        function (response, note_element_id) {
            //if request succeed tick the checkbox and modify ever
            // the textarea or the text depending on where it is used
            if (response['success']) {
                var notesArea = document.getElementById("id_" + note_element_id + "-notes");
                var icon = document.getElementById("icon-" + note_element_id);
                var note_wrapper = document.getElementById("note-" + note_element_id);
                if (response["is_archived"]) {
                    if (note_wrapper)
                        note_wrapper.classList.add("note-disabled");
                    if (notesArea) {
                        notesArea.classList.add("note-disabled");
                        notesArea.setAttribute("disabled", "disabled");
                    }
                    icon.classList.remove("fa-square-o");
                    icon.classList.add("fa-check-square-o");

                } else {
                    if (note_wrapper)
                        note_wrapper.classList.remove("note-disabled");
                    if (notesArea) {
                        notesArea.classList.remove("note-disabled");
                        notesArea.removeAttribute("disabled");
                    }

                    icon.classList.remove("fa-check-square-o");
                    icon.classList.add("fa-square-o");
                }
            }
        })
}


//this function is used in the evaluation to remove a note
function removeNoteEvaluation(note_element_id, notification_div_id) {
    ajaxRequestAndNotify("form-delete-element-", note_element_id, notification_div_id,
        "delete_note_id=",
        function (response, note_element_id) {
            if (response['success']) {
                var notesArea = document.getElementById("id_" + note_element_id + "-notes");
                var icon = document.getElementById("icon-" + note_element_id);
                notesArea.value = '';
                notesArea.classList.remove("note-disabled");
                notesArea.removeAttribute("disabled");
                icon.classList.remove("fa-check-square-o");
                icon.classList.add("fa-square-o");
            }
        });
}

//this function is used on profile to remove a note
function removeNoteProfile(note_element_id, notification_div_id) {
    ajaxRequestAndNotify("form-delete-element-", note_element_id, notification_div_id,
        "delete_note_id=",
        function (response, note_element_id) {
            if (response['success']) {
                //if the request succeed remove the element content
                var note_wrapper = document.getElementById("note-wrapper-" + note_element_id);
                note_wrapper.textContent = '';
                //after 4 seconds remove the element and if needed the section, and the evaluation
                setTimeout(function () {
                    var element_div = document.getElementById("note-element-" + note_element_id);
                    var section_div_body = element_div.parentElement
                    element_div.remove();
                    // if the section is empty, removes it
                    if (section_div_body.childElementCount === 0) {
                        var section_div = document.getElementById("note-section-" + response["section_id"]);
                        var evaluation_div_body = document.getElementById("collapse-evaluation-" + response["evaluation_id"]);
                        section_div.remove();
                        // if the evaluation is empty removes it
                        if (evaluation_div_body.childElementCount === 0) {
                            var evaluation_div = document.getElementById("accordion-evaluation-" + response["evaluation_id"]);
                            evaluation_div.remove();
                            var child_count = document.querySelectorAll("#content-user-notes > div").length;
                            // if the child count is equals to 1, there is no more notes to display so we display a place-holder text
                            if (child_count === 1) {
                                document.getElementById("empty-notes-text").removeAttribute("hidden");
                            }
                        }

                    }
                }, 4000);
            }
        });
}


function actionPlan(elementId, messageDiv) {
    var form = document.getElementById("form-action-plan-" + elementId);
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function () {
        if (ajax.readyState === 4 && ajax.status === 200) {
            var response = JSON.parse(ajax.response);
            var parentMessage = document.getElementById(messageDiv + elementId);
            addMessage(parentMessage, response['message'], response["message_type"]);
            parentMessage.classList.remove("hidden-div");
            var actionPlanButton = document.getElementById(`action_plan-btn${elementId}`);
            var icon = actionPlanButton.querySelector("i");
            if (response["added_action_plan"]) {
                icon.classList.remove("fa-square-o");
                icon.classList.add("fa-check-square-o");
            } else {
                icon.classList.remove("fa-check-square-o");
                icon.classList.add("fa-square-o");
            }
            //remove the notification after 4 secondes
            setTimeout(function () {
                parentMessage.classList.add("hidden-div");
                parentMessage.textContent = '';
            }, 4000);
        }
    }
    manageAjaxRequest(ajax, form, "action_plan_element_id=" + elementId);
}

function removeElementActionPlan(elementId, messageDiv) {
    var form = document.getElementById("remove-element-action-plan-form" + elementId);
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function () {
        if (ajax.readyState === 4 && ajax.status === 200) {
            var response = JSON.parse(ajax.response);
            var parentMessage = document.getElementById(messageDiv + elementId);
            addMessage(parentMessage, response['message'], response["message_type"]);
            parentMessage.classList.remove("hidden-div");
            setTimeout(function () {
                parentMessage.classList.add("hidden-div");
                parentMessage.textContent = '';
            }, 4000);

            if (response['success']) {
                document.getElementById("element-footer" + elementId).textContent = '';
                setTimeout(function () {
                    var elementCard = document.getElementById(`action-plan-element-${elementId}`);
                    var sectionDiv = elementCard.parentElement;
                    elementCard.remove();
                    if (sectionDiv.childElementCount === 0) {
                        var sectionCard = document.getElementById(`action-plan-section-${response["section_id"]}`);
                        var evaluationDiv = document.getElementById("evaluation-action-plan-" + response["evaluation_id"]);
                        sectionCard.remove();
                        if (evaluationDiv.childElementCount === 0) {
                            var evaluationCard = document.getElementById("accordion-evaluation-action-plan-" + response["evaluation_id"]);
                            evaluationCard.remove();
                            var childCount = document.querySelectorAll("#action-plans-wrapper > div").length;
                            if (childCount === 0) {
                                document.getElementById("no-action-plan").removeAttribute("hidden");
                            }
                        }

                    }
                }, 4000);
            }
        }
    }
    manageAjaxRequest(ajax, form, "action_plan_remove_element_id=" + elementId);
}

function changeIconRelease(divHeader) {
    var children = divHeader.children;
    if(children) {
        var divIcon = children[0];
        if(divIcon.classList.contains("fa-angle-down")){
            divIcon.classList.replace("fa-angle-down", "fa-angle-up");
        } else {
            divIcon.classList.replace("fa-angle-up", "fa-angle-down");
        }
    }
}
