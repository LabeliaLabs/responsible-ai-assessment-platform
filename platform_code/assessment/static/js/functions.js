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
        data = data + "&" + pair[0].toString() + "=" + pair[1].toString();
    }
    return data
}

// Functions to manage resources

function like(element_id, resource_id) {
    var form = document.getElementById("like_resources"+element_id);
    $.ajax({ data: $(form).serialize() + "&resource_id=" + resource_id,
        type: "POST",
        url: $(form).attr('action'),
        success: function(response) {
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
    });
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
    $.ajax({ data: $(form).serialize() + "&resource_id=" + resource_id,
             type: "POST",
             url: $(form).attr('action'),
             success: function(response) {
                 if(response['success']) {
                    // The resource is unliked, so it is removed from the favorite
                    var textNoResource = document.getElementById("no-resources-message");
                    var textNoResourceTemp = document.getElementById("no-resources-message-temp");
                    unlikeResource(textNoResource, textNoResourceTemp, resource_id, response);
                 }
             }
    });
}

// Content of the evaluation part (submit send feedback, reset answer, submit answer)

function feedback(id, feedback_object){
    var form = document.getElementById("feedback_user_"+feedback_object+id);
    var button = document.getElementsByName("button_feedback");
    $(button).attr("disabled","true");
    $.ajax({ data: $(form).serialize() + "&"+feedback_object+"_id=" + id,
             type: $(form).attr('method'),
             url: $(form).attr('action'),
             success: function(response) {
                 if(response['success']) {

                     $("#confirmation_feedback_"+feedback_object+id).html("<div class='alert alert-success'>"+response['message']+"</div>");
                     $(".alert-success").delay(4000).slideUp(200, function() {
                        $(this).remove();
                        $(form)[0].reset();
                        $(button).removeAttr("disabled");
                        $('#modal-feedback-'+feedback_object+id +" .close").click();
                      });
                 } else {
                 $("#confirmation_feedback_"+feedback_object+id).html("<div class='alert alert-danger'>"+response['message']+"</div>");
                 $(".alert-danger").delay(5000).slideUp(200, function() {
                        $(this).remove();
                        $(button).removeAttr("disabled");
                        $('#modal-feedback-'+feedback_object+id+" .close").click();
                      });
                 }
             }
    });
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


function resetChoice(id_form){
    var element_id = id_form;
    untickAllChoices(element_id);
    var form = document.getElementById("form"+element_id);
    var name = $(form).attr("element");
    $.ajax({ data: $(form).serialize() + "&reset_element_id=" + element_id,
             type: $(form).attr('method'),
             url: $(form).attr('action'),
             success: function(response) {
                 // First thing we do is to inform the user whether the action succeeded or not
                 var parentMessage = document.getElementById("confirmationform"+element_id);
                 parentMessage.textContent = '';
                 addMessage(parentMessage, response['message'], response["message_type"]);
                 if (response['message_notes']) {
                        addMessage(parentMessage, response['message_notes'], response["message_notes_type"]);
                    }
                 parentMessage.classList.remove("hidden-div");
                 setTimeout(function() {
                       parentMessage.classList.add("hidden-div");
                       parentMessage.textContent = '';
                     }, 4000);

                 if(response['success']) {
                     setSectionProgressBar(response);
                     setSectionProgressionSidebar(response);
                     // There is not necessarily a need to change the status if it was already not done!
                     if (response["element_status_changed"]){
                        setElementEvaluationStatusNotDone(element_id);
                     }
                     if(response['no_more_condition_inter']) {
                         location.reload();
                     }
                    // If the evaluation is no more finished
                    if (!response["evaluation_finished"]){
                        var temp_button = document.getElementById("temp-validation-button");
                        var permanent_button = document.getElementsByName("validation-button");
                        // If it is the permanent button displayed, we disable it
                        if($(temp_button).hasClass("display-none")){
                            $(permanent_button).attr("disabled", "true");
                        } else {
                            $(temp_button).addClass("display-none");
                            $(permanent_button).attr("disabled", "true");
                            $(permanent_button).removeClass("display-none");
                        }
                    }
                 }
             }
     });
}

function addMessage(parentElement, message, alertType) {
// This function add a div to a parentElement with a message and the class alert-type (alert-success, alert-warning or
// alert-danger)
    var messageCreated = document.createElement('div');
    messageCreated.textContent = message;
    messageCreated.classList.add("alert", alertType);
    parentElement.append(messageCreated);
}


// Validation of an evaluation element

function submitForm(id_form){

    var form = document.getElementById(id_form);
    var name = $(form).attr("element");
    var element_id = $(form).attr("name");
    $.ajax({ data: $(form).serialize() + "&element_id=" + element_id,
             type: $(form).attr('method'),
             url: $(form).attr('action'),
             success: function(response) {
                 // First thing we do is to inform the user whether the action succeeded or not
                 var parentMessage = document.getElementById("confirmation"+id_form);
                 parentMessage.textContent = '';
                 addMessage(parentMessage, response['message'], response["message_type"]);
                 if (response['message_notes']) {
                        addMessage(parentMessage, response['message_notes'], response["message_notes_type"]);
                    }
                 parentMessage.classList.remove("hidden-div");
                 setTimeout(function() {
                       parentMessage.classList.add("hidden-div");
                       parentMessage.textContent = '';
                     }, 4000);

                 if(response['success']) {
                     setSectionProgressBar(response);
                     setSectionProgressionSidebar(response);
                     if (response["element_status_changed"]){
                        setElementEvaluationStatusDone(element_id);
                     }
                     if (response["no_more_condition_inter"]){
                        location.reload();
                        // todo do not reload and modify the elements
                     }

                     // If this evaluation element is the last one of the evaluation, we enable the validation button
                     var temp_button = document.getElementById("temp-validation-button");
                     var permanent_button = document.getElementsByName("validation-button");
                     if (response["evaluation_finished"]){
                        $(permanent_button).addClass("display-none");
                        $(temp_button).removeClass("display-none");
                     } else {
                         if($(temp_button).hasClass("display-none")){
                            $(permanent_button).attr("disabled", "true");
                         } else {
                             $(temp_button).addClass("display-none");
                             $(permanent_button).attr("disabled", "true");
                             $(permanent_button).removeClass("display-none");
                         }
                     }
                 }
                 if(response['conditional_elements_list'].length > 0) {
                    for (var i=0; i < response['conditional_elements_list'].length; i++) {
                        var id_evaluation_element = response['conditional_elements_list'][i];
                        setElementEvaluationStatusDone(id_evaluation_element);
                        untickAllChoices(id_evaluation_element); // reset the choices
                        $("#temp_warning"+id_evaluation_element).attr("style", "display: block;");
                        $("#disable_element"+id_evaluation_element).attr("disabled","true");
                        $("#validate"+id_evaluation_element).attr("disabled", "true");
                        $("#reset"+id_evaluation_element).attr("onclick", "");
                    }
                 }
             }
    });
}

function submitUserSettingsDataForm(id_form){
    var form = document.getElementById(id_form);
    $.ajax({ data: $(form).serialize(),
        type: $(form).attr('method'),
        url: $(form).attr('action'),
        success: function(response) {
            var divMessage = document.getElementById("message");
            divMessage.classList.remove("display-none");
            divMessage.textContent = "";
            if (response['success']) {
                addMessage(divMessage, response['message'], "alert-success");
            } else {
                addMessage(divMessage, response['message'], "alert-danger");
            }
            setTimeout( function() {
                divMessage.classList.add("display-none")
                divMessage.textContent = "";
                }, 4000);
        }
    });
}

function submitUserSettingsPasswordForm(id_form){
    var form = document.getElementById(id_form);
    $.ajax({ data: $(form).serialize(),
        type: $(form).attr('method'),
        url: $(form).attr('action'),
        success: function(response) {
            var divMessage = document.getElementById("messagePassword");
            divMessage.classList.remove("display-none");
            divMessage.textContent = "";
            if (response['success']) {
                form.reset();
                addMessage(divMessage, response['message'], "alert-success");
            } else {
                var messages = response["error_messages"];
                for (message of messages){
                    addMessage(divMessage, message, "alert-danger");
                }
            }
            setTimeout( function() {
                divMessage.classList.add("display-none")
                divMessage.textContent = "";
                }, 6000);
        }
    });
}


function setSectionProgressBar(response){
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

function setElementEvaluationStatusDone(element_id){
    var element_status_to_disable = document.getElementsByName("element_status_not_done"+element_id);
    var new_element_status = document.getElementsByName("element_status_temporary"+element_id);
    if (document.getElementsByName("element_status_not_done"+element_id).length ===0){
        $(new_element_status).html('<i class="fa fa-circle fa-stack-2x"></i></span>');
        $(new_element_status).attr("title", "You have answered this evaluation element"); // todo translation
    } else {
        element_status_to_disable[0].setAttribute("style", "display: none;");
        $(new_element_status).attr("style", "display: block;");
        $(new_element_status).attr("title", "You have answered this evaluation element"); // todo translation
        $(new_element_status).html('<i class="fa fa-circle fa-stack-2x"></i></span>');
    }

}

function setElementEvaluationStatusNotDone(element_id){
    var element_status_to_disable = document.getElementsByName("element_status_done"+element_id);
    var new_element_status = document.getElementsByName("element_status_temporary"+element_id);
//    case the element has been validated then reset without page refresh, so it is temporary div
    if (document.getElementsByName("element_status_done"+element_id).length ===0){
        $(new_element_status).html('<i class="fa fa-circle-o fa-stack-2x"></i></span>');
        $(new_element_status).attr("title", "You have not answered this evaluation element yet"); // todo translation
    } else {
        element_status_to_disable[0].setAttribute("style", "display: none;");
        $(new_element_status).attr("style", "display: block;");
        $(new_element_status).html('<i class="fa fa-circle-o fa-stack-2x"></i></span>');
        $(new_element_status).attr("title", "You have not answered this evaluation element yet"); // todo translation
    }
}
// not used
function setElementEvaluationStatusNotDoneAfterInvalid(element_id){
    var element_status_to_disable = document.getElementsByName("element_status_invalid"+element_id);
    var new_element_status = document.getElementsByName("element_status_temporary"+element_id);
//    case the element has been validated then reset without page refresh, so it is temporary div
    if (document.getElementsByName("element_status_invalid"+element_id).length ===0){
        $(new_element_status).html('<i class="fa fa-circle-o fa-stack-2x"></i></span>');
    } else {
        element_status_to_disable[0].setAttribute("style", "display: none;");
        $(new_element_status).attr("style", "display: block;");
        $(new_element_status).html('<i class="fa fa-circle-o fa-stack-2x"></i></span>');
    }
}

// used in the profile view to adapt the breadcrumbs
function displayTextLink(text_to_display, link_id){
    var link_object = document.getElementById(link_id);
    link_object.innerHTML=text_to_display;
}

function changeNameEvaluation(form_id, evaluation_id){
    var form = document.getElementById(form_id);
    $.ajax({ data: $(form).serialize()+ "&evaluation_id=" + evaluation_id,
             type: $(form).attr('method'),
             url: $(form).attr('action'),
             success: function(response) {
                 if(response['success']) {
                     $("#confirmation"+form_id).html("<div class='alert alert-success margin-10'>"+response['message']+"</div>");
                     $(".alert").delay(3000).slideUp(200, function() {
                        $(this).remove();
                        location.reload();  // to update the array and the page
                        });
                 } else {
                    $("#confirmation"+form_id).html("<div class='alert alert-danger margin-10'>"+response['message']+"</div>");
                    $(".alert").delay(5000).slideUp(200, function() {
                        $(this).remove();
                        });
                 }
             }
    });
}

// upgrade function used to upgrade an evaluation and block the popin from closing
function upgrade(modal_id, form_id, evaluation_id){
    var upgrade_modal = document.getElementById(modal_id);
    var form = document.getElementById(form_id);
    var text_message = document.getElementById("upgrade_message_text"+evaluation_id);
    var upgrade_message = document.getElementById("upgrade_message"+evaluation_id);
    $(upgrade_message).addClass("alert-warning");
    $(upgrade_message).removeClass("display-none");
    text_message.textContent = 'The upgrade is in process, please wait.';
    var buttons = document.getElementsByTagName('button');
    for (var button of buttons) {
        $(button).attr("disabled", "true");
        $(button).addClass("waiting-cursor");
    }
    document.body.style.cursor='wait'; // transform the cursor to a loading cursor
    $.ajax({
        type: $(form).attr('method'),
        url: $(form).attr('action'),
        success: function(response) {
             if(response['success']) {
                document.body.style.cursor='default';
                $(upgrade_message).removeClass("alert-warning");
                $(upgrade_message).addClass("alert-success");
                text_message.textContent = response["message"];
                $(".alert").delay(5000).slideUp(200, function() {
                    $(this).remove();
                });
                document.location.href=response["redirection"];
             } else {
                document.body.style.cursor='default';
                for (var button of buttons) {
                    $(button).removeAttr("disabled");
                    $(button).removeClass("waiting-cursor");
                }
                $(upgrade_message).removeClass("alert-warning");
                $(upgrade_message).addClass("alert-danger");
                text_message.textContent = response["message"];
                setTimeout(location.reload.bind(location), 3000);
             }
        }
    });
}

function send_invitation(form_id){
    $("#sendInvitationButton").attr("disabled", "true");
    var form = document.getElementById(form_id);
    $.ajax({
        data: $(form).serialize(),
        type: $(form).attr('method'),
        url: $(form).attr('action'),
        success: function(response) {
             if(response['success']) {
                 var tabMembers = document.getElementById("arrayMembers");
                 var newRow = tabMembers.insertRow();
                 for (var i = 0; i < tabMembers.rows[0].cells.length; i++){
                    var newCell  = newRow.insertCell(i);
                    $(newCell).addClass("case-array");
                    var newText  = document.createTextNode(response["data_user"][i]);
                    newCell.appendChild(newText);
                 }
                 $("#confirmationInvitation").html("<div class='alert alert-success'>"+response['message']+"</div>");
                 $(".alert-success").delay(4000).slideUp(200, function() {
                    $(this).remove();
                    $(form)[0].reset();
                    $("#sendInvitationButton").removeAttr("disabled");
                    $("#modal-add-member .close").click();
                  });
             } else {
             $("#confirmationInvitation").html("<div class='alert alert-danger'>"+response['message']+"</div>");
             $(".alert-danger").delay(5000).slideUp(200, function() {
                    $(this).remove();
                    $("#sendInvitationButton").removeAttr("disabled");
                    $("#modal-add-member .close").click();
                  });
             }
        }
    });

}

function removeMember(form_id, object_id, is_pending){
// This function is used to remove a member or invitation from an organisation
// It is called in assessment/organisation/member in remove-member.html and remove-pending-member.html
// It creates an ajax request managed by SummaryView
    var form = document.getElementById(form_id);
    if(is_pending) {
        var object_removed = "delete_invitation_id";
    } else {
        var object_removed = "remove_member_id";
    }
    $.ajax({
        data: $(form).serialize() +"&"+object_removed+"=" + object_id,
        type: $(form).attr('method'),
        url: $(form).attr('action'),
        success: function(response) {
             if(response['success']) {
                 var tabMembers = document.getElementById("arrayMembers");
                 if(is_pending) {
                       var row = document.getElementById("rowPendingMember"+ object_id);
                 } else {
                        var row = document.getElementById("rowMember"+ object_id);
                 }
                 var indexRemoved = row.rowIndex;
                 indexRemoved = indexRemoved - 1;
                 $(tabMembers.deleteRow(indexRemoved));
                 $("#messagesMember").html("<div class='alert alert-success'>"+response['message']+"</div>");
                 $(".modal").delay(1000).slideUp(200, function() {
                     $("#modal-remove-member"+object_id+" .close").click();
                     $("#modal-remove-member-pending"+object_id+" .close").click();
                  });
             } else {
                 $("#messagesMember").html("<div class='alert alert-danger'>"+response['message']+"</div>");
                 $(".modal").delay(1000).slideUp(200, function() {
                    $("#modal-remove-member"+object_id+" .close").click();
                    $("#modal-remove-member-pending"+object_id+" .close").click();
             });
             }
        }
    });
}

function editRoleMember(form_id, object_id, is_pending){
// This function is used to edit the role of members or pending invitations to join the organisation
// It creates an ajax request managed by SummaryView
// It is called in assessment/organisation/member in edit-role-member.html and edit_role-pending-member.html
    var form = document.getElementById(form_id);
    if(is_pending) {
        var object_edited = "edit_invitation_id";
    } else {
        var object_edited = "edit_member_id";
    }
    $.ajax({
        data: $(form).serialize() +"&"+object_edited+"=" + object_id,
        type: $(form).attr('method'),
        url: $(form).attr('action'),
        success: function(response) {
             if(response['success']) {
                 var tabMembers = document.getElementById("arrayMembers");
                 if(is_pending) {
                       var row = document.getElementById("rowPendingMember"+ object_id);
                 } else {
                        var row = document.getElementById("rowMember"+ object_id);
                 }
                 var cell = row.cells[2]
                 cell.textContent = response["new_role"]
                 $("#messagesMember").html("<div class='alert alert-success'>"+response['message']+"</div>");
                 $(".modal").delay(1000).slideUp(200, function() {
                     $("#modal-edit-role"+object_id+" .close").click();
                     $("#modal-edit-role-pending"+object_id+" .close").click();
                  });
             } else {
                 $("#messagesMember").html("<div class='alert alert-danger'>"+response['message']+"</div>");
                 $(".modal").delay(1000).slideUp(200, function() {
                    $("#modal-edit-role"+object_id+" .close").click();
                    $("#modal-edit-role-pending"+object_id+" .close").click();
             });
             }
        }
    });
}

function submitSectionNotes(form_id, section_id){
// this function is used to save the notes of the section
// the call is made in content-section.html
// the ajax request is managed in SectionView
   var form = document.getElementById(form_id);
    $.ajax({ data: $(form).serialize()+ "&notes_section_id=" + section_id,  // the id is not used but "notes_section_id" to know the context of the ajax
             type: $(form).attr('method'),
             url: $(form).attr('action'),
             success: function(response) {
                 if(response['success']) {
                     $("#messageSectionNotes"+section_id).removeClass("display-none")
                     $("#messageSectionNotes"+section_id).html("<div class='alert alert-success margin-10'>"+response['message']+"</div>");
                     $(".alert").delay(3000).slideUp(200, function() {
                        $(this).addClass("display-none");
                        });
                 } else {
                    $("#messageSectionNotes"+section_id).removeClass("display-none")
                    $("#messageSectionNotes"+section_id).html("<div class='alert alert-danger margin-10'>"+response['message']+"</div>");
                    $(".alert").delay(3000).slideUp(200, function() {
                        $(this).addClass("display-none");
                        });
                 }
             }
    });
}

function changeIconResource(divHeader) {
    var children = divHeader.children;
    if(children) {
        var divIcon = children[0];
        if(divIcon.classList.contains("fa-plus")){
            divIcon.classList.replace("fa-plus", "fa-minus");
        } else {
            divIcon.classList.replace("fa-minus", "fa-plus");
        }
    }
}

$(function() {
  $(".progress").each(function() {
    var value = $(this).attr('data-value');
    if (typeof value === "string"){
        value = parseFloat(value);
    }
    var left = $(this).find('.progress-left .progress-bar');
    var right = $(this).find('.progress-right .progress-bar');

    if (value >= 0 && value < 50) {
        right.css('transform', 'rotate(' + percentageToDegrees(value) + 'deg)')
    }
    if ( value >= 50 && value <=100) {
        right.css('transform', 'rotate(180deg)')
        left.css('transform', 'rotate(' + percentageToDegrees(value - 50) + 'deg)')
      }

  })

  function percentageToDegrees(percentage) {
    return percentage / 100 * 360
  }
});

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

//script used to send newsletter subscription to MailChimp and display succes/error messages
function registerNewsletter(event) {
    //disable normal form submit behavior
    event.preventDefault();
    var $form = $('#mc-embedded-subscribe-form');
    //replace some url's parts to get a json response to our request
    //this is not done in the <form> to allow user without js to register
    var formatedUrl = $form.attr('action').replace('post', 'post-json') + "&c=?"
    $(function () {
        //hide errors messages if present
        $('#divErrorsNewsletter').children("p").each(function (child) {
            $(this).hide();
        });
        $.ajax({
            type: "GET",
            url: formatedUrl,
            data: $form.serialize(),
            cache: false,
            dataType: 'json',
            contentType: "application/json; charset=utf-8",
            error: function (err) {
                $('#errorServerUnavailable').show();
            },
            success: function (data) {
                //if mailChimp does not return "succes" -> display an error message
                //else: hide form and display a confirmation message
                let errorNum;
                if (data.result != "success") {
                    //regroup mailChimp errors into 4 differents errors

                    //if the '0' is not present it means that the mail adress is already subscribed
                    if (data.msg[0] != '0') {
                        errorNum = "alreadySub";
                    } else {
                        let errorsReceivedRedirect = {
                            "0 - Please enter a value": "empty",
                            "0 - An email address must contain a single @": "format",
                            "0 - The domain portion of the email address is invalid (the portion after the @: )": "format",
                            "0 - The username portion of the email address is empty": "format",
                            "0 - This email address looks fake or invalid. Please enter a real email address.": "invalid",
                        }
                        errorNum = errorsReceivedRedirect[data.msg];
                    }

                    let displayError = {
                        'empty': function () {
                            $('#errorMailEmpty').show();
                        },
                        'format': function () {
                            $('#errorMailFormat').show();
                        },
                        'invalid': function () {
                            $('#errorInvalidMail').show();
                        },
                        'alreadySub': function () {
                            $('#mc_embed_signup').children('form').remove();
                            $('#errorAlreadySubscribed').show();
                        }
                    }
                    displayError[errorNum]();
                } else {
                    $('#mc_embed_signup').children('form').remove();
                    $('#confirmSubscribe').show();
                }

            }
        })
    });
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
