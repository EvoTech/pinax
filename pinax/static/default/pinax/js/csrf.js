if (window.jQuery) {
  jQuery(document).ajaxSend(function(event, xhr, settings) {
    // from https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
  });
}


if (window.dojo) {
    require(["dojo", "dojo/cookie", "dojo/_base/lang"], function(dojo){
        dojo._xhr__origin = dojo.xhr;
        dojo.xhr = function(/*String*/ method, /*dojo.__XhrArgs*/ args, /*Boolean?*/ hasBody){
            var csrfHeader = {
                "X-CSRFToken": dojo.cookie('csrftoken')
            }
            if (args.headers) {
                dojo.mixin(args.headers, csrfHeader);
            } else {
                args.headers = csrfHeader; 
            }
            /* if ("POST|PUT".indexOf(method.toUpperCase()) != -1 && !args.form) {
                if (!args.content) {
                    args.content = {}
                }
                if (!args.content.csrfmiddlewaretoken) {
                    args.content.csrfmiddlewaretoken = dojo.cookie('csrftoken');
                }
            }
            if (method.toUpperCase() == 'DELETE' && args.url) {
                if (args.url.indexOf('csrfmiddlewaretoken') == -1) {
                    args.url += args.url.indexOf('?') == -1 ? '?' : '&';
                    args.url += 'csrfmiddlewaretoken=' + dojo.cookie('csrftoken');
                }
            } */
            return this._xhr__origin(method, args, hasBody);
        }
    });
}
