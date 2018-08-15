
var system = require('system');
var webpage = require('webpage');
var args = system.args;

var page = webpage.create()
var url = "http://tuvi.cohoc.net/404.html?ref=cache-not-found&id=" + args[1]
page.open(url, function (status) {
    console.log("PhantomJS:", url)
    console.log("Status: " + status);
    // setTimeout(function () { }, 5000);
    window.setTimeout(function () {
        //page.render('page_screen_' + args[1] + '.png')
        phantom.exit();
    }, 2000);
});
