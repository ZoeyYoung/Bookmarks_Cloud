(function($) {
    // var mstags = $('#tags').magicSuggest({
    //     selectionPosition: 'right',
    //     allowFreeEntries: true,
    //     width: 80,
    //     maxSelectioninteger: 30
    // });
    // $.getJSON('/tags', function(data) {
    //     mstags.setData(data.tags);
    // });
    $("img.lazy").lazy();
    $('.quickflip-wrapper').quickFlip({
        closeSpeed : 200,
        openSpeed : 150
    });
    $(".nano").nanoScroller();
    $(window).resize(function() {
        $("#bookmarks-panel, #article-panel").css('max-height', jQuery(window).height() - 50);
    });
    $(document).on('mouseenter mouseleave', '.bookmark-item', function() {
        $('.bookmark-note', this).stop(true, true).slideToggle();
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

    function resetAddBookmarkForm() {
        $('#url').prop('disabled', false);
        $('#url').val('');
        $('#title').val('');
        $('#description').val('');
        $('#tags').val('');
        $('#note').val('');
        //$('#isstar').prop('checked', false),
        //$('#isreaded').prop('checked', false),
        // $('#bookmarkForm').hide(),
        // $('#bookmarks-panel').show();
    }

    $(document).on('click', '.stag', function() {
        // console.log($(this).text());
        // mstags.setValue($(this).text());
        $('#tags').val($('#tags').val() + ',' + $(this).text());
    });

    function initAddBookmarkForm(url, response) {
        // $('#bookmarks-panel').hide();
        $('#url').prop('disabled', true);
        $('#url').val(url);
        $("#title").val(response.title);
        $('#description').val(response.description);
        var tags_t = $('#tags').val();
        var tags = (tags_t === '') ? response.tags : response.tags + ',' + tags_t;
        $('#tags').val(tags);
        // mstags.empty();
        // mstags.clear();
        // mstags.setValue(tags);
        var stagsarr = response.suggest_tags;
        var stagshtml = (stagsarr.length) ? '<li class="stag label label-info">' + stagsarr.join('</li><li class="stag label label-info">') + '</li>' : '';
        $('#suggestTags').html(stagshtml);
        note_t = $('#note').val();
        note = (note_t === '') ? response.note : response.note + '\n' + note_t;
        $('#note').val(note);
        showArticle(url, response.title, response.article);
        // $('#bookmarkForm').show();
    }
    $(document).on('click', '#showBookmarkFormBtn', function() {
        // $('#bookmarkForm').toggle();
        // $('#bookmarks-panel').toggle();
        $('.quickflip-wrapper').quickFlipper();
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
            tags: $('#tags').val(), // mstags.getValue().join(","),
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
        var url = bookmark_item.find('.bookmark-title').attr('href');
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
        $('.quickflip-wrapper').quickFlipper();
        last_editor = $(this).closest('.bookmark-item');
        var url = last_editor.find('.bookmark-title').attr('href');
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
        var url = bookmark_item.find('.bookmark-title').attr('href');
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
        tag = $('#pageBookmarkList').attr('title');
        page = $(this).attr('title');
        $('#pageBookmarkList').empty().load('/bookmark', {tag: tag, page: page}, function() {
            $("img.lazy").lazy({ bind: "event", delay: 0});
        });
    });

    $(document).on('click', '.bookmark-read-btn', function() {
        var bookmark_item = $(this).closest('.bookmark-item');
        var url = bookmark_item.find('.bookmark-title').attr('href');
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
        $('#article-title').html(title);
        $('#article-content').html('<p><a target="_blank" href="' + url + '">查看原网页</a> <a target="_blank" href="/segmentation/' + url + '">查看分词结果</a></p>' + article);
        // FIXME 应该跳到文章顶部才对...也许该考虑换个插件了...
        $('#article-panel').nanoScroller({ scroll: 'top' });
    }
})(jQuery);
