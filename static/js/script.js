(function($) {
    $("#bookmarks-panel, #article-panel").css('max-height', jQuery(window).height()-50).customScrollbar({hScroll: false, updateOnWindowResize: true});
    $(window).resize(function() {
        $("#bookmarks-panel, #article-panel").css('max-height', jQuery(window).height()-50);
    });
    $('.link-item').hover(
        function(){ $('.link-note', this).stop(true, true).slideToggle(); }
    );
    jQuery.getJSON('/randomlink', function(response) {
        if (response.success === 'true') {
            showArticle(response.url, response.title, response.article);
        } else {
            alert('数据库返回错误');
        }
    });
    // Placeholders for input/textarea
    $("input, textarea").placeholder();

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
        $('#bookmarks-panel').show();
    }

    function initAddLinkForm(url, response) {
        $('#bookmarks-panel').hide();
        $('#url').prop('disabled', true);
        $('#url').val(url);
        $("#title").val(response.title);
        $('#description').val(response.description);
        tags_t = $('#tags').val();
        tags = (tags_t === '') ? response.tags : response.tags + ','+ tags_t;
        $('#tags').val(tags);
        note_t = $('#note').val();
        note = (note_t === '') ? response.note : response.note + '\n' + note_t;
        $('#note').val(note);
        showArticle(url, response.title, response.article);
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
        $('#bookmarks-panel').toggle();
    });
    $(document).on('click', '#searchBtn', function() {
        $('#searchForm').toggle();
        $('#keywords').focus();
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
        var url = $('#url').val();
        var title = $('#title').val();
        jQuery.postJSON('/link/add', {
            url: url,
            favicon: '',
            title: title,
            description: $('#description').val(),
            tags: $('#tags').val(),
            note: $('#note').val(),
            html: ''
        }, function(response) {
            if(response.success === 'true') {
            // count = parseInt($('#linksCount').text()) + 1;
            // $('#linksCount').text(count);
            // $('#linkList').prepend(generateLinkHtml(response));
                $('#linkList').prepend(response.link_module);
                showArticle(url, title, response.article);
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
            last_editor = null;
        }
    });
    // 刷新书签信息
    $(document).on('click', '.link-refresh-btn', function() {
        var link_item = $(this).closest('.link-item');
        var url = link_item.find('.link-title').attr('href');
        var animateClass = "icon-spin";
        $(this).addClass(animateClass);
        jQuery.getJSON('/link/refresh', {
            url: url
        }, function(response) {
            if (response.success === 'true') {
                that.replaceWith(response.link_module);
                showArticle(url, response.title, response.article);
            } else {
                $(this).removeClass(animateClass);
                alert('数据库返回错误');
            }
        });
    });
    // 编辑书签
    $(document).on('click', '.link-edit-btn', function() {
        last_editor = $(this).closest('.link-item');
        var url = last_editor.find('.link-title').attr('href');
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
        var link_item = $(this).closest('.link-item');
        var url = link_item.find('.link-title').attr('href');
        jQuery.postJSON('/link/del', {
            url: url
        }, function(response) {
            if (response.success === 'true') {
                link_item.remove();
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
                showArticle(url, response.title, response.article);
            } else {
                alert('数据库返回错误');
            }
        });
    });

    function showArticle(url, title, article) {
        $('#article-title').html(title);
        $('#article-content').html('<p><a target="_blank" href="' + url + '">查看原网页</a></p>' + article);
        // FIXME 应该跳到文章顶部才对...也许该考虑换个插件了...
        $("#article-panel").customScrollbar("resize");
    }
})(jQuery);
