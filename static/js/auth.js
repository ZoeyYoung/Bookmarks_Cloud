(function($) {
    //  登录
    $(document).on('click', '#signInBtn', function() {
        var email = $('#email').val();
        var password = $('#password').val();
        $.ajax({
            url: '/auth/signin',
            data: {
                email: email,
                password: password
            },
            dataType: 'json',
            type: "POST"
        }).done(function(response) {
            if (response) {
                location.href = response.redirect;
                console.log("登录成功");
            }
        });
    });
    //  注册
    $(document).on('click', '#signUpBtn', function() {
        var email = $('#email').val();
        var username = $('#username').val();
        var password = $('#password').val();
        $.ajax({
            url: '/auth/signup',
            data: {
                email: email,
                username: username,
                password: password
            },
            dataType: 'json',
            type: "POST"
        }).done(function(response) {
            if (response) {
                location.href =　response.redirect;
                console.log("注册成功");
            }
        });
    });
})(jQuery);
