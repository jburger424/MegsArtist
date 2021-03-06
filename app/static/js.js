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

        function getArtists() {
        var artists = [];
        $.ajax({
            type: "GET",
            url: "/getArtists/",
            dataType: "json",
            complete: function (xhr, textStatus) {
                var oldArtists = xhr.responseJSON;
                for (var x = 0; x < oldArtists.length; x++) {
                    artists.push(oldArtists[x]);
                }
            }
        });
        return artists;
    };

//will open addTag modal
    $('select').on('change', function () {
        if (this.value == -1) {
            $('.addTag').modal('show');
        }
    });
    $('#artistSearch').typeahead(null, {
        source:substringMatcher(getArtists())
    });


    $('#artistTags,#trackTags').tokenfield({
        typeahead: [null,
            {
                source: substringMatcher(getTags())
        }]
    });


    $('#artistTags').on('tokenfield:createtoken', function (event) {
        var existingTokens = $(this).tokenfield('getTokens');
        $.each(existingTokens, function (index, token) {

        });
    });


//on-load


})
/*if ( $( "ul#tracks" ).length ) {*/
$('.modal').on('shown.bs.modal', function() {
  $(this).find('[autofocus]').focus();
});
$("input#artistSearch").keypress(function(event) {
    if (event.which == 13) {
        event.preventDefault();
        window.location.href = "/artists/"+$("input#artistSearch").val();
    }
});
function change(URL) {
    console.log("changing to " + URL);
    $("ul li.active").toggleClass("active", false);
    $('li[data-track-url="' + URL + '"]').toggleClass("active", true);
    //$("ul li.active").attr("class", "inactive");
    //$('li[data-track-url="' + URL + '"]').attr("class", "active");
    $("#player-source").attr("src", URL);
    audio[0].pause();
    audio[0].load(); //suspends and restores all audio element
    audio[0].oncanplaythrough = audio[0].play();
};
function prevSong() {
    var prev;
    if ($('li.active').prev('li')[0]) {
        prev = $('li.active').prev('li');
    } else {
        prev = $('li:last-child', $("li.active").parents('ul'));
    }
    change(prev.attr("data-track-url"));
}

function nextSong() {
    var next;
    if ($('li.active').next('li')[0]) {
        next = $('li.active').next('li');
    } else {
        next = $('li:first-child', $("li.active").parents('ul'));
    }
    change(next.attr("data-track-url"));
}
var audio;
$(window).load(function () {
    if ($("ul#tracks").length > 0) {
        console.log("before init audio");
        audio = $("#player");
        console.log("after init audio");
        $("a").click(function(){
            change("#");
        });
        $('ul#tracks li.list-group-item').click(function () {
            change($(this).attr("data-track-url"));
        });


        audio[0].addEventListener('ended', function (e) {
            nextSong();
        });
        $("#prev").click(function () {
            prevSong();
        });
        $("#next").click(function () {
            nextSong();
        });
        console.log("length: " + $('ul#tracks li').length);
        var randomTrack = Math.floor((Math.random() * $('ul#tracks li').length) + 1);
        change($("ul li.list-group-item:nth-child(" + randomTrack + ")").attr("data-track-url"));
    }

});

