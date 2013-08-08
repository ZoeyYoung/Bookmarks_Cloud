(function($) {
    $("img.lazy").lazy();
    $('div.quickflip-wrapper').quickFlip({
        closeSpeed : 200,
        openSpeed : 150
    });
    $("div.nano").nanoScroller();
    $(window).resize(function() {
        $("#bookmarks-panel, #article-panel").css('max-height', jQuery(window).height() - 50);
    });
    $(document).on('mouseenter mouseleave', 'div.bookmark-item', function() {
        $(this).find('.bookmark-note').stop(true, true).slideToggle();
    });
    function getRandomBookmark() {
        jQuery.getJSON('/randombookmark', function(response) {
            if (response.success === 'true') {
                $('#bookmarkList').prepend(response.bookmark_module);
                $("img.lazy").lazy();
                showArticle(response.url, response.title, response.article);
            } else {
                alert('数据库返回错误');
            }
        });
    }
    getRandomBookmark();

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

    function resetAddBookmarkForm() {
        $('#url').prop('disabled', false);
        $('#url').val('');
        $('#title').val('');
        $('#description').val('');
        $('#tags').val('');
        $('#note').val('');
    }

    $(document).on('click', '.stag', function() {
        $('#tags').val($('#tags').val() + ',' + $(this).text());
    });

    function initAddBookmarkForm(url, response) {
        $('#url').prop('disabled', true);
        $('#url').val(url);
        $("#title").val(response.title);
        $('#description').val(response.description);
        var tags_t = $('#tags').val();
        var tags = (tags_t === '') ? response.tags : response.tags + ',' + tags_t;
        $('#tags').val(tags);
        var stagsarr = response.suggest_tags;
        var stagshtml = (stagsarr.length) ? '<li class="stag label label-info">' + stagsarr.join('</li><li class="stag label label-info">') + '</li>' : '';
        $('#suggestTags')[0].innerHTML = stagshtml;
        var note_t = $('#note').val();
        var note = (note_t === '') ? response.note : response.note + '\n' + note_t;
        $('#note').val(note);
        showArticle(url, response.title, response.article);
    }
    $(document).on('click', '#showBookmarkFormBtn', function() {
        $('div.quickflip-wrapper').quickFlipper();
    });
    // do get bookmark infomation
    $(document).on('click', '#getBookmarkInfoBtn', function() {
        $('#getBookmarkInfoBtn').button('loading');
        jQuery.getJSON('/bookmark/get_info', {
            url: $("#url").val()
        }, function(response) {
            $('#getBookmarkInfoBtn').button('reset');
            if (response.success === 'true') {
                initAddBookmarkForm($("#url").val(), response);
            } else {
                alert('数据库返回错误');
            }
        });
    });
    $(document).on('click', '#addBookmarkBtn', function() {
        var url = $('#url').val();
        var title = $('#title').val();
        jQuery.postJSON('/bookmark/add', {
            url: url,
            favicon: '',
            title: title,
            description: $('#description').val(),
            tags: $('#tags').val(),
            note: $('#note').val(),
            html: ''
        }, function(response) {
            if (response.success === 'true') {
                last_editor.replaceWith(response.bookmark_module);
                showArticle(url, title, response.article);
                resetAddBookmarkForm();
            } else {
                alert('数据库返回错误');
            }
        });
    });
    var last_editor = null;
    $(document).on('click', '#cancelAddBookmarkBtn', function() {
        resetAddBookmarkForm();
    });
    // 刷新书签信息
    $(document).on('click', '.bookmark-refresh-btn', function() {
        var bookmark_item = $(this).closest('.bookmark-item');
        var url = bookmark_item.find('.bookmark-favicon').attr('href');
        var animateClass = "icon-spin";
        $(this).addClass(animateClass);
        that = $(this);
        jQuery.getJSON('/bookmark/refresh', {
            url: url
        }, function(response) {
            if (response.success === 'true') {
                bookmark_item.replaceWith(response.bookmark_module);
                showArticle(url, response.title, response.article);
            } else {
                that.removeClass(animateClass);
                alert('数据库返回错误');
            }
        });
    });
    // 编辑书签
    $(document).on('click', '.bookmark-edit-btn', function() {
        $('div.quickflip-wrapper').quickFlipper();
        last_editor = $(this).closest('.bookmark-item');
        var url = last_editor.find('.bookmark-favicon').attr('href');
        jQuery.getJSON('/bookmark/get_detail', {
            url: url
        }, function(response) {
            if (response.success === 'true') {
                initAddBookmarkForm(url, response);
            } else {
                alert('数据库返回错误');
            }
        });
    });
    $(document).on('click', '.bookmark-del-btn', function() {
        var bookmark_item = $(this).closest('.bookmark-item');
        var url = bookmark_item.find('.bookmark-favicon').attr('href');
        jQuery.postJSON('/bookmark/del', {
            url: url
        }, function(response) {
            if (response.success === 'true') {
                bookmark_item.remove();
            } else {
                alert('数据库返回错误');
            }
        });
    });

    $(document).on('click', '#randomBookmarksBtn', function() {
        $('#randomBookmarks').empty().load('/random');
    });

    $(document).on('click', '.pagination li a', function() {
        keywords = $('#pageBookmarkList').attr('keywords');
        tag = $('#pageBookmarkList').attr('tag');
        page = this.title;
        $('#pageBookmarkList').empty().load('/bookmark', {keywords: keywords, tag: tag, page: page}, function() {
            $("img.lazy").lazy({ bind: "event", delay: 0});
        });
    });

    $(document).on('click', '.bookmark-read-btn', function() {
        var bookmark_item = $(this).closest('.bookmark-item');
        var url = bookmark_item.find('.bookmark-favicon').attr('href');
        jQuery.getJSON('/bookmark/get_article', {
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
        $('#article-title')[0].innerHTML = title;
        $('#article-content')[0].innerHTML = '<p><a target="_blank" href="' + url + '">查看原网页</a> <a target="_blank" href="/segmentation/' + url + '">查看分词结果</a></p>' + article;
        // FIXME 应该跳到文章顶部才对...也许该考虑换个插件了...
        $('#article-panel').nanoScroller({ scroll: 'top' });
    }
})(jQuery);
