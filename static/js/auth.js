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
                console.log("登录成功");
            }
        });
    });
    //  注册
    $(document).on('click', '#signUpBtn', function() {
        var email = $('#email').val();
        var password = $('#password').val();
        $.ajax({
            url: '/auth/signup',
            data: {
                email: email,
                password: password
            },
            dataType: 'json',
            type: "POST"
        }).done(function(response) {
            if (response) {
                console.log("注册成功");
            }
        });
    });
})(jQuery);
