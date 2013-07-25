(function($) {
    $(document).ready(function(){
        $(".article-edit-panel").mCustomScrollbar({
            scrollButtons:{
                enable:true
            },
            advanced:{
                updateOnBrowserResize: true,
                updateOnContentResize: true
            }
        });
        $(".bookmarks-panel").mCustomScrollbar({
            scrollButtons:{
                enable:true
            },
            advanced:{
                updateOnBrowserResize: true,
                updateOnContentResize: true
            }
        });
        jQuery.getJSON('/randomlink', function(response) {
            if (response.success === 'true') {
                showArticle(response.url, response.title, response.article, false);
            } else {
                alert('数据库返回错误');
            }
        });
    });
    // Placeholders for input/textarea
    $("input, textarea").placeholder();

    // 瀑布流 http://wlog.cn/waterfall/index-zh.html
    $(document).on('click', '#waterfallTab', function() {
        $('#waterflowContainer').waterfall({
            itemCls: 'link-item',
            prefix: 'link',
            fitWidth: true,
            gutterWidth: 0,
            gutterHeight: 15,
            bufferPixel: -50,
            align: 'center',
            colWidth: 300,
            minCol: 1,
            isAnimated: true,
            resizable: true,
            isFadeIn: true,
            checkImagesLoaded: false,
            path: function(page) {
                return '/link?page=' + page;
            },
            dataType: 'html'
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
        $('#article').show();
    }

    function initAddLinkForm(url, response) {
        $('#article').hide();
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
        $('#article').toggle();
    });
    $(document).on('click', '#searchBtn', function() {
        $('#searchForm').toggle();
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
                showArticle(url, title, response.article, false);
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
                showArticle(url, response.title, response.article, false);
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
                showArticle(url, response.title, response.article, false);
            } else {
                alert('数据库返回错误');
            }
        });
    });

    function showArticle(url, title, article, show_last_editor) {
        $('#article-title').html(title);
        $('#article-content').html('<p><a target="_blank" href="' + url + '">查看原网页</a></p>' + article);
        if (show_last_editor && last_editor !== null) {
            last_editor.show();
            last_editor = null;
        }
        $('#article').show();
        $(".article-edit-panel").mCustomScrollbar("update");
        $(".article-edit-panel").mCustomScrollbar("scrollTo","top",{scrollInertia:200
        }); //scroll to top
        $('#linkForm').hide();
    }
})(jQuery);
