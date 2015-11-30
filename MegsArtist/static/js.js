jQuery(function ($) { // First argument is the jQuery object
    var substringMatcher = function (strs) {
        return function findMatches(q, cb) {
            var matches, substringRegex;

            // an array that will be populated with substring matches
            matches = [];

            // regex used to determine if a string contains the substring `q`
            substrRegex = new RegExp(q, 'i');

            // iterate through the pool of strings and for any string that
            // contains the substring `q`, add it to the `matches` array
            $.each(strs, function (i, str) {
                if (substrRegex.test(str)) {
                    matches.push(str);
                }
            });

            cb(matches);
        };
    };


    function getTags() {
        var tags = [];
        $.ajax({
            type: "GET",
            url: "/getTags/",
            dataType: "json",
            complete: function (xhr, textStatus) {
                var oldTags = xhr.responseJSON;
                for (var x = 0; x < oldTags.length; x++) {
                    tags.push(oldTags[x]);
                }
            }
        });
        return tags;
    };


    $("button#addTag").on("click", function () {
        var newTag = ($("#tagInput").val());
        var artistName = $("input#artistName").val();
        var data = {
            newTag: newTag,
            artistName: artistName
        };

        $.ajax({
            type: 'POST',
            url: window.location.href + 'tag/',
            data: JSON.stringify(data),
            dataType: 'json',
            contentType: 'application/json; charset=utf-8',
            success: function (msg) {
                //if duplicate tag
                if (msg.tag_id == -1) {
                    $("#tag_error").remove();
                    $('#tagInput').css({
                        'border': '2px solid red'
                    });
                    $("<div class='row text-center' id='tag_error'>Error:<b>'" + newTag + "'</b> Already exists</div>").insertBefore(".addTag .row .col-md-12 .row");
                }
                else {
                    $('#artistTags').append($('<option>', {
                        value: msg.tag_id,
                        text: data.newTag
                    }));//TODO: insert where it should be in abc order
                    $('#artistTags').val(msg.tag_id);
                    $('.addTag').modal('hide');
                }
            }

        })
    });

//will open addTag modal
    $('select').on('change', function () {
        if (this.value == -1) {
            $('.addTag').modal('show');
        }
    });


    $('#artistTags').tokenfield({
        typeahead: [null, {source: substringMatcher(getTags())}]
    });


    $('#artistTags').on('tokenfield:createtoken', function (event) {
        var existingTokens = $(this).tokenfield('getTokens');
        $.each(existingTokens, function (index, token) {

            /* if (token.value === event.attrs.value)
             event.preventDefault();*/
        });
    });
})
;
