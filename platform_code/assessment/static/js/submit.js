function submitField(field){
    console.log("entre submit function");
    $.ajax({ data: field.attr('data') ,
                type: field.attr('method'),
                url: field.attr('action'),
                success: function(response) {
                    if(response['success']) {
                    $("#confirmation").html("<div class='alert alert-success'>Succesfully sent feedback, thank you!</div>");
                     }
                }
    });

}
$(document).ready(function() {
    $("#form{{element.id}}").submit(function(event) {
       var name = $(this).attr("name");
       event.preventDefault();
       $.ajax({ data: $(this).serialize() +"&name=" + name,
                type: $(this).attr('method'),
                url: $(this).attr('action'),
                success: function(response) {
                    $("#confirmation").append('<p>' + response.data + '</p>');
                     }
                     if(response['error']) {
                         $("#message").html("<div class='alert alert-danger'>" +
                            response['error']['comment'] +"</div>");
                     }
                },
                error: function (request, status, error) {
                     console.log(request.responseText);
                }
       });
   });
})
