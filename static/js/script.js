(function($) {
    // Placeholders for input/textarea
    $("input, textarea").placeholder();

    $(document).on('click', '#waterfallTab', function() {
        $('#waterflowContainer').waterfall({
            itemCls: 'link-item',
            prefix: 'link',
            dataType: 'html',
            colWidth: 330,
            gutterWidth: 5,
            gutterHeight: 15,
            isAnimated: true,
            checkImagesLoaded: false,
            fitWidth: true,
            maxCol: 3,
            path: function(page) {
                return '/link?page=' + page;
            }
        });
    });

    function getCookie(name) {
        var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
        return r ? r[1] : undefined;
    }

    jQuery.postJSON = function(url, args, callback) {
        // args._xsrf = getCookie("_xsrf");
        $.ajax({
            url: url,
            data: $.param(args),
            dataType: "text",
            type: "POST",
            success: function(response) {
                callback(eval("(" + response + ")"));
            }
        });
    };

    function resetAddLinkForm() {
        $('#url').prop('disabled', false),
        $('#url').val(''),
        $('#title').val(''),
        $('#description').val(''),
        $('#tags').val(''),
        $('#note').val(''),
        //$('#isstar').prop('checked', false),
        //$('#isreaded').prop('checked', false),
        $('#linkForm').hide(),
        $('#linkInfoInputs').hide();
    }

    function initAddLinkForm(url, response) {
        $('#url').prop('disabled', true);
        $('#url').val(url);
        $("#title").val(response.title);
        $('#description').val(response.description);
        $('#tags').val(response.tags);
        $('#note').val(response.note);
        // if (response.is_star == 1) {
        //     $('#isstar').prop('checked', true);
        // }
        // if (response.is_readed == 1) {
        //     $('#isreaded').prop('checked', true);
        // }
        $('#linkForm').show();
        $('#linkInfoInputs').show();
    }
    $(document).on('click', '#showLinkFormBtn', function() {
        $('#linkForm').toggle();
    });
    // do get link infomation
    $(document).on('click', '#getLinkInfoBtn', function() {
        $('#getLinkInfoBtn').button('loading');
        jQuery.getJSON('/link/get_info', {
            url: $("#url").val()
        }, function(response) {
            $('#getLinkInfoBtn').button('reset');
            if (response.success === 'true') {
                initAddLinkForm($("#url").val(), response);
            } else {
                alert('数据库返回错误');
            }
        });
    });
    $(document).on('click', '#addLinkBtn', function() {
        jQuery.postJSON('/link/add', {
            url: $('#url').val(),
            favicon: '',
            title: $('#title').val(),
            description: $('#description').val(),
            tags: $('#tags').val(),
            note: $('#note').val()
        }, function(response) {
            if(response.success === 'true') {
            // count = parseInt($('#linksCount').text()) + 1;
            // $('#linksCount').text(count);
            // $('#linkList').prepend(generateLinkHtml(response));
                $('#linkList').prepend(response.link_module);
                resetAddLinkForm();
            } else {
              alert('数据库返回错误');
            }
        });
    });
    var last_editor = null;
    $(document).on('click', '#cancelAddLinkBtn', function() {
        resetAddLinkForm();
        if (last_editor !== null) {
            last_editor.show();
        }
    });
    // 刷新书签信息
    $(document).on('click', '.link-refresh-btn', function() {
        var url = $(this).attr('title');
        var that = $(this).parent().parent().parent();
        var $icon = $(this).find(".icon-refresh" ),
            animateClass = "icon-spin";
        $icon.addClass(animateClass);
        jQuery.getJSON('/link/refresh', {
            url: url
        }, function(response) {
            if (response.success === 'true') {
                that.replaceWith(response.link_module);
                // $icon.removeClass(animateClass);
            } else {
                $icon.removeClass(animateClass);
                alert('数据库返回错误');
            }
        });
    });
    // 编辑书签
    $(document).on('click', '.link-edit-btn', function() {
        var url = $(this).attr('title');
        last_editor = $(this).parent().parent().parent();
        last_editor.hide();
        jQuery.getJSON('/link/get_detail', {
            url: url
        }, function(response) {
            if (response.success === 'true') {
                initAddLinkForm(url, response);
            } else {
                alert('数据库返回错误');
            }
        });
    });
    $(document).on('click', '.link-del-btn', function() {
        var url = $(this).attr('title');
        var that = $(this);
        jQuery.postJSON('/link/del', {
            url: url
        }, function(response) {
            if (response.success === 'true') {
                that.parent().parent().parent().remove();
                $('#waterflowContainer').waterfall('reLayout', $('#waterflowContainer'), null);
            } else {
                alert('数据库返回错误');
            }
        });
    });

    $(document).on('click', '#randomBookmarksBtn', function() {
        $('#randomBookmarks').empty();
        $('#randomBookmarks').load('/random');
    });

    $(document).on('click', '.link-read-btn', function() {
        var url = $(this).attr('title');
        jQuery.getJSON('/link/get_article', {
            url: url
        }, function(response) {
            if (response.success === 'true') {
                $('#article-title').html(response.title + ' <a target="_blank" href="' + url + '">查看原网页</a>');
                $('#article-content').html(response.article);
                $('#article').modal();
            } else {
                alert('数据库返回错误');
            }
        });
    });
})(jQuery);
