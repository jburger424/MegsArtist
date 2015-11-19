jQuery(function ($) { // First argument is the jQuery object
    $("button#addGenre").on("click", function () {
        var newGenre = ($("#genreInput").val());
        var artistName = $("input#artistName").val();
        var data = {
            newGenre: newGenre,
            artistName: artistName
        };

        $.ajax({
            type: 'POST',
            url: window.location.href + 'genre/',
            data: JSON.stringify(data),
            dataType: 'json',
            contentType: 'application/json; charset=utf-8',
            success: function (msg) {
                //if duplicate genre
                if (msg.genre_id == -1) {
                    $("#genre_error").remove();
                    $('#genreInput').css({
                        'border': '2px solid red'
                    });
                    $("<div class='row text-center' id='genre_error'>Error:<b>'" + newGenre + "'</b> Already exists</div>").insertBefore(".addGenre .row .col-md-12 .row");
                }
                else {
                    $('#artistGenre').append($('<option>', {
                        value: msg.genre_id,
                        text: data.newGenre
                    }));//TODO: insert where it should be in abc order
                    $('#artistGenre').val(msg.genre_id);
                    $('.addGenre').modal('hide');
                }
            }

        })
    });

    //will open addGenre modal
    $('select').on('change', function () {
        if (this.value == -1) {
            $('.addGenre').modal('show');
        }
    });
});