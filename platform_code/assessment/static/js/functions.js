// This file contains the javascript functions used in the project

// Functions to manage resources

function like(x, element_id, resource_id){
    console.log("id",element_id,resource_id);
    var form = document.getElementById("like_resources"+element_id);
    console.log("form", form);
    $.ajax({ data: $(form).serialize() + "&resource_id=" + resource_id,
             type: "POST",
             url: $(form).attr('action'),
             success: function(response) {
                console.log("response", response);
                 if(response['success']) {
                     if (response['like']){
                        var resources_list = document.getElementsByName("resource_not_liked"+resource_id);
                        console.log("list ressources", resources_list);

                        // remove the text when we like a resource
                        var text_no_resources = document.getElementById("no-resources-message");
                        if ($(text_no_resources).attr("style", "display: block;")){
                            $(text_no_resources).attr("style", "display: none;");
                            $("#no-resources-message-temp").addClass("display-none");
                        }

                        for ( var i = 0; i <= resources_list.length; i++){
                        console.log("Icon", resources_list[i]);
                            $(resources_list[0]).removeClass("fa-bookmark-o").addClass("fa-bookmark");
                            $(resources_list[0]).attr("name","resource_liked"+resource_id);
                            console.log("After like, check name = liked", resources_list[i]);
                        }
                     var resources_liked_array = document.getElementById("liked-resources-array");
                     console.log("ARRAY", resources_liked_array);
                     var resource_text = response["resource_text"];
                     $(resources_liked_array).append('<li id="resource'+resource_id+'" class="object-linked list-with-disc margin-10">'+resource_text+'</li>');
                     } else {
                        var resources_list = document.getElementsByName("resource_liked"+resource_id);

                        for ( var i = 0; i <= resources_list.length; i++){
                            $(resources_list[0]).removeClass("fa-bookmark").addClass("fa-bookmark-o");
                            $(resources_list[0]).attr("name","resource_not_liked"+resource_id);

                        }
                        var resource = document.getElementById("resource"+resource_id);
                        console.log("success", resource);
                        $("#resource"+resource_id).remove();

                        // Manage the fact there is no more resource liked and the text message is displayed
                        if (response["no_resource_liked"]){
                            $("#no-resources-message-temp").removeClass("display-none");
                        }
                     }

                 }
             }
    });
}

function remove(x, resource_id){
    console.log("LIKE", x);
    console.log("id",resource_id);
    var form = document.getElementById(resource_id);
    console.log("form", form);
    $.ajax({ data: $(form).serialize() + "&resource_id=" + resource_id,
             type: "POST",
             url: $(form).attr('action'),
             success: function(response) {
                console.log("response", response);
                 if(response['success']) {
                    var resource = document.getElementById("resource"+resource_id);
                    console.log("success", resource);
                    $("#resource"+resource_id).remove();
                    var resources_list = document.getElementsByName("resource_liked"+resource_id)
                    for ( var i = 0; i <= resources_list.length; i++){
                        $(resources_list[0]).removeClass("fa-bookmark").addClass("fa-bookmark-o");
                        $(resources_list[0]).attr("name","resource_not_liked"+resource_id);
                        $("#resource_list"+resource_id).addClass("hidden-div");

                    }
                    // Manage the fact there is no more resource liked and the text message is displayed
                    if (response["no_resource_liked"]){
                        $("#no-resources-message-temp").removeClass("display-none");
                    }
                 } else {
                    var messages = response["error_messages"];
                    $("#error_messages_resources").html("");
                    $("#error_messages_resources").show();
                    for (message of messages){
                        console.log("message", message);
                        $("#error_messages_resources").append("<li class='alert alert-danger'>"+message+"</li>");
                     }
                    $("#error_messages").delay(4000).slideUp(200, function() {
                    $(this).hide();
                    });

                 }
             }
    });
}

// Content of the evaluation part (submit send feedback, reset answer, submit answer)

function feedback(id, feedback_object){
    console.log("feedback function", "id "+id, typeof id, feedback_object);
    var form = document.getElementById("feedback_user_"+feedback_object+id);
    console.log("form feedback", form);
    var button = document.getElementsByName("button_feedback");
    $(button).attr("disabled","true");
    $.ajax({ data: $(form).serialize() + "&"+feedback_object+"_id=" + id,
             type: $(form).attr('method'),
             url: $(form).attr('action'),
             success: function(response) {
                 if(response['success']) {
                     console.log("response success", response);

                     $("#confirmation_feedback_"+feedback_object+id).html("<div class='alert alert-success'>"+response['message']+"</div>");
                     $(".alert-success").delay(4000).slideUp(200, function() {
                        $(this).remove();
                        $(form)[0].reset();
                        $(button).removeAttr("disabled");
                        $('#modal-feedback-'+feedback_object+id +" .close").click();
                      });
                 } else {
                 console.log("response fail", response);
//                 var button = document.getElementsByName("button_feedback");
//                 $(button).attr("disabled","true");
                 $("#confirmation_feedback_"+feedback_object+id).html("<div class='alert alert-danger'>"+response['message']+"</div>");
                 $(".alert-danger").delay(5000).slideUp(200, function() {
                        $(this).remove();
                        $(button).removeAttr("disabled");
                        $('#modal-feedback-'+feedback_object+id+" .close").click();
                      });
                 }
             }
    });
};

function resetChoice(id_form){
    var element_id = id_form;
    let i =0;
    do {
        var choice = document.getElementById("id_"+element_id+"_"+i);
        console.log(i);
        console.log("choice",choice);
        choice.checked = false;
        i += 1;
    } while (document.getElementById("id_"+element_id+"_"+i));

    console.log("reset the choices", "confirmation"+id_form);
    var form = document.getElementById("form"+element_id);
    var name = $(form).attr("element");
    console.log("form", form);
    $.ajax({ data: $(form).serialize() + "&element_id=" + element_id,
             type: $(form).attr('method'),
             url: $(form).attr('action'),
             success: function(response) {
                 if(response['success']) {
                     console.log("response", response);
                     console.log("message", document.getElementById("#confirmationform"+element_id));
                     setSectionProgressBar(response);
                     if (response["element_status_changed"]){
                        setElementEvaluationStatusNotDone(element_id);
                     }
                     if(response['conditional_elements_list'].length > 0) {
                        for (var i=0; i < response['conditional_elements_list'].length; i++) {
                            var id_evaluation_element = response['conditional_elements_list'][i];
                            location.reload();
//                            todo : change and update the elements
                        }
                    }
                    // If the evaluation is no more finished
                    if (!response["evaluation_finished"]){
                        console.log("unable the validation");
                        var temp_button = document.getElementById("temp-validation-button");
                        var permanent_button = document.getElementsByName("validation-button");
                        console.log("permanent button, check", permanent_button);
                        // If it is the permanent button displayed, we disable it
                        if($(temp_button).hasClass("display-none")){
                            $(permanent_button).attr("disabled", "true");
                        } else {
                            $(temp_button).addClass("display-none");
                            $(permanent_button).attr("disabled", "true");
                            $(permanent_button).removeClass("display-none");
                        }

                    }
                     $("#confirmationform"+element_id).html("<div class='alert alert-success'>"+response['message_reset']+"</div>");
                     $(".alert-success").delay(4000).slideUp(200, function() {
                        $(this).remove();
                        });
                 }
             }
     });
};

// Validation of an evaluation element

function submitForm(id_form){
    console.log("enter submit function", "confirmation"+id_form);
    var form = document.getElementById(id_form);
    var name = $(form).attr("element");
    var element_id = $(form).attr("name");
    console.log("form", form);
    $.ajax({ data: $(form).serialize() + "&element_id=" + element_id,
             type: $(form).attr('method'),
             url: $(form).attr('action'),
             success: function(response) {
                 if(response['success']) {
                     console.log("response", response);
                     setSectionProgressBar(response);
                     if (response["element_status_changed"]){
                        setElementEvaluationStatusDone(element_id);
                     }
                     if (response["no_more_condition_inter"]){
                        location.reload();
//                        todo : change and update the elements instead of reload the page !
                     }
                     $("#confirmation"+id_form).html("<div class='alert alert-success'>"+response['message']+"</div>");
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
                     $(".alert-success").delay(3000).slideUp(200, function() {
                        $(this).remove();
                        });


                 } else {
                   console.log("response", response);
                   if (response['conditions_respected']){
                       $("#confirmation"+id_form).html("<div class='alert alert-danger'>"+response['message']+"</div>");
                       $(".alert-danger").delay(3000).slideUp(200, function() {
                          $(this).remove();
                        });
                   } else {
                       $("#confirmation"+id_form).html("<div class='alert alert-warning'>"+response['message']+"</div>");
                       $(".alert-warning").delay(3000).slideUp(200, function() {
                          $(this).remove();
                        });
                    }
                 }

                 if(response['conditional_elements_list'].length > 0) {
                    for (var i=0; i < response['conditional_elements_list'].length; i++) {
                        var id_evaluation_element = response['conditional_elements_list'][i];
                        setElementEvaluationStatusDone(id_evaluation_element);
                        $("#temp_warning"+id_evaluation_element).attr("style", "display: block;");
                        $("#disable_element"+id_evaluation_element).attr("disabled","true");
                        $("#validate"+id_evaluation_element).attr("disabled", "true");
                        $("#reset"+id_evaluation_element).attr("onclick", "");
                    }
                 }

             }
    });

};

function submitUserSettingsDataForm(id_form){
    console.log("enter submit function", id_form);
    var form = document.getElementById(id_form);
    console.log("form", form);
    $.ajax({ data: $(form).serialize(),
             type: $(form).attr('method'),
             url: $(form).attr('action'),
             success: function(response) {
                 console.log("response", response);
                 if(response['success']) {
                 $("#confirmation").html("<div class='alert alert-success margin-50'>"+response['message_success']+"</div>");
                 $(".alert").delay(3000).slideUp(200, function() {
                    $(this).remove();
                    });
                 } else {
                    $(form)[0].reset();
                    $("#error_messages").html("");
                    $("#error_messages").show();
                    $("#error_messages").append("<div class='alert alert-danger margin-50'>"+response['message_fail']+"</div>");

                    $("#error_messages").delay(4000).slideUp(200, function() {
                    $(this).hide();
                    });


                 }


             }
    });

};

function submitUserSettingsPasswordForm(id_form){
    console.log("enter submit function", id_form);
    var form = document.getElementById(id_form);
    console.log("form", form);
    $.ajax({ data: $(form).serialize(),
             type: $(form).attr('method'),
             url: $(form).attr('action'),
             success: function(response) {
                 console.log("response", response);
                 if(response['success']) {
<!--                 $('#id_form').trigger("reset");-->
                 $('input[name="old_password"]').val("");
                 $('input[name="new_password1"]').val("");
                 $('input[name="new_password2"]').val("");
                 $("#confirmation"+id_form).html("<div class='alert alert-success margin-70'>"+response['message_success']+"</div>");
                 $(".alert").delay(5000).slideUp(200, function() {
                    $(this).remove();
                    });
                 } else {
                    var messages = response["error_messages"];
                    $("#error_messages_password").html("");
                    $("#error_messages_password").show();
                    for (message of messages){
                        console.log("message", message);
                        $("#error_messages_password").append("<li class='alert alert-danger margin-70'>"+message+"</li>");
                     }
                    $("#error_messages_password").delay(4000).slideUp(200, function() {
                    $(this).hide();
                    });


                 }


             }
    });

};


function setSectionProgressBar(response){
    console.log("set progress bar", response["section_progression"]);
    var progress_bar = document.getElementById("section-progress-bar");
    var progress_bar_content = document.getElementById("section-progress-bar-content");
    progress_bar.setAttribute("title", "Progression de "+response['section_progression']+"%");
    progress_bar_content.setAttribute("style", "width:"+response["section_progression"]+"%;");
    progress_bar_content.setAttribute("aria-valuenow", response['section_progression']);
    progress_bar_content.setAttribute("title", "Progression de "+response['section_progression']+"%");

}

function setElementEvaluationStatusDone(element_id){
    var element_status_to_disable = document.getElementsByName("element_status_not_done"+element_id);
    var new_element_status = document.getElementsByName("element_status_temporary"+element_id);
    console.log("elements older and then new", element_status_to_disable, new_element_status);
    if (document.getElementsByName("element_status_not_done"+element_id).length ===0){
        $(new_element_status).html('<i class="fa fa-circle fa-stack-2x"></i></span>');
    } else {
        element_status_to_disable[0].setAttribute("style", "display: none;");
        $(new_element_status).attr("style", "display: block;");
        $(new_element_status).html('<i class="fa fa-circle fa-stack-2x"></i></span>');
    }

}

function setElementEvaluationStatusNotDone(element_id){
    console.log("reset_element");
    var element_status_to_disable = document.getElementsByName("element_status_done"+element_id);
    var new_element_status = document.getElementsByName("element_status_temporary"+element_id);
//    case the element has been validated then reset without page refresh, so it is temporary div
    if (document.getElementsByName("element_status_done"+element_id).length ===0){
        $(new_element_status).html('<i class="fa fa-circle-o fa-stack-2x"></i></span>');
    } else {
        element_status_to_disable[0].setAttribute("style", "display: none;");
        console.log("elements older and then new", element_status_to_disable, new_element_status);
        $(new_element_status).attr("style", "display: block;");
        $(new_element_status).html('<i class="fa fa-circle-o fa-stack-2x"></i></span>');
    }
}
// not used
function setElementEvaluationStatusNotDoneAfterInvalid(element_id){
    console.log("reset_element after invalid");
    var element_status_to_disable = document.getElementsByName("element_status_invalid"+element_id);
    var new_element_status = document.getElementsByName("element_status_temporary"+element_id);
//    case the element has been validated then reset without page refresh, so it is temporary div
    if (document.getElementsByName("element_status_invalid"+element_id).length ===0){
        $(new_element_status).html('<i class="fa fa-circle-o fa-stack-2x"></i></span>');
    } else {
        element_status_to_disable[0].setAttribute("style", "display: none;");
        console.log("elements older and then new", element_status_to_disable, new_element_status);
        $(new_element_status).attr("style", "display: block;");
        $(new_element_status).html('<i class="fa fa-circle-o fa-stack-2x"></i></span>');
    }
}

// used in the profile view to adapt the breadcrumbs
function displayTextLink(text_to_display, link_id){
    console.log("select active breadcrumb",text_to_display, link_id);
    var link_object = document.getElementById(link_id);
    link_object.innerHTML=text_to_display;
}

function changeNameEvaluation(form_id, evaluation_id){
    var form = document.getElementById(form_id);
    console.log("form", form);
    $.ajax({ data: $(form).serialize()+ "&evaluation_id=" + evaluation_id,
             type: $(form).attr('method'),
             url: $(form).attr('action'),
             success: function(response) {
                 console.log("response", response);
                 if(response['success']) {
                     $("#confirmation"+form_id).html("<div class='alert alert-success margin-10'>"+response['message']+"</div>");
                     $(".alert").delay(3000).slideUp(200, function() {
                        $(this).remove();
                        });
                     location.reload();  // to update the array and the page
                 } else {
                    $("#confirmation"+form_id).html("<div class='alert alert-danger margin-10'>"+response['message']+"</div>");
                    $(".alert").delay(5000).slideUp(200, function() {
                        $(this).remove();
                        });
                 }
             }
    });

};

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
            console.log("response", response);
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
                console.log("test message rep", response["message"])
                text_message.textContent = response["message"];
                setTimeout(location.reload.bind(location), 3000);
             }
        }
    });
}
