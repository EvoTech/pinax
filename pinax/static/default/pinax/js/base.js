jQuery.fn.autoscroll = function() {
    $('html,body').animate({scrollTop: this.offset().top}, 500);
}

$(function() {
    $("#messages li a").click(function() {
        $(this).parent().fadeOut();
        return false;
    });
});

function htmlEncode(value){
    if (value) {
        // return jQuery('<div />').text(value).html(); // Do not use it, not handle quotes
        return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    } else {
        return '';
    }
}
 
function htmlDecode(value) {
    if (value) {
        // return $('<div />').html(value).text();
        return value.replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"').replace(/&#039;/g, "'");
    } else {
        return '';
    }
}
