(function($) {
    var App = (function() {
        var lastEditor = null,
            $getBookmarkInfoBtn = $('#getBookmarkInfoBtn'),
            showArticle = function(url, title, article) {
                $('#article-title')[0].innerHTML = title;
                $('#article-content')[0].innerHTML = '<p><a target="_blank" href="' + url + '">查看原网页</a> <a target="_blank" href="/segmentation/' + url + '">查看分词结果</a></p>' + article;
            },
            // 初始化添加书签表单
            initBookmarkForm = function(url, response) {
                $('#url').val(url).prop('disabled', true);
                $("#title").val(response.title);
                $('#description').val(response.description);
                // 防止用户已输入标签被清除
                var tags_t = $('#tags').val();
                var tags = (tags_t === '') ? response.tags : response.tags + ',' + tags_t;
                $('#tags').val(tags);
                // 推荐标签
                var s_tags_arr = response.suggest_tags.split(',');
                var s_tags_html = (s_tags_arr && s_tags_arr.length) ? '<li class="stag">' + s_tags_arr.join('</li><li class="stag">') + '</li>' : '';
                $('#suggestTags')[0].innerHTML = s_tags_html;
                // 防止用户已输入笔记被清除
                var note_t = $('#note').val();
                var note = (note_t === '') ? response.note : response.note + '\n' + note_t;
                $('#note').val(note);
                // 显示正文
                showArticle(url, response.title, response.article);
            },
            resetBookmarkForm = function() {
                $('#url').val('').prop('disabled', false);
                $('#title').val('');
                $('#description').val('');
                $('#tags').val('');
                $('#suggestTags').empty();
                $('#note').val('');
                $('#article-title')[0].innerHTML = '';
                $('#article-content')[0].innerHTML = '';
                $('#getBookmarkInfoBtn').button('reset');
            },
            empty_article_btn_html = '<button type="button" class="bookmark-article-empty-btn btn btn-default btn-lg btn-block" data-toggle="button"><i class="fa fa-arrow-up" data-toggle="tooltip" title="收起正文"></i>收起正文</button>';
            // getRandomBookmark = function() {
            //     jQuery.getJSON('/randombookmark', function(response) {
            //         if (response.success === 'true') {
            //             $('#bookmarkList').prepend(response.bookmark_module);
            //             $("img.lazy").lazy();
            //             showArticle(response.url, response.title, response.article);
            //         } else {
            //             alert('数据库返回错误');
            //         }
            //     });
            // },
            init = function() {
                $("#vcard").popover({
                    trigger: "hover",
                    placement: "bottom"
                });
                $("img.lazy").lazy();
                $('div.quickflip-wrapper').quickFlip({
                    closeSpeed: 200,
                    openSpeed: 150
                });
                $(document).on('mouseenter mouseleave', 'div.bookmark-item', function() {
                    $(this).find('.bookmark-note').stop(true, true).slideToggle();
                });
                // 点击"添加"，显示添加书签表单
                $(document).on('click', '#showBookmarkFormBtn', function() {
                    $('div.quickflip-wrapper').quickFlipper();
                });
                // 取消添加书签
                $(document).on('click', '#cancelAddBookmarkBtn', function() {
                    resetBookmarkForm();
                });
                // stag为推荐的标签，当点击时添加到标签后面
                $(document).on('click', '.stag', function() {
                    // TODO: 应该判断是否重复，这个标签输入做得不好
                    $('#tags').val($('#tags').val() + ',' + $(this).text());
                });
                // 在添加书签时，点击“获取信息”按钮，获取书签的信息，填入表单
                $(document).on('click', '#getBookmarkInfoBtn', function() {
                    // Bootstrap JavaScript 改变按钮状态为"载入中..."
                    $getBookmarkInfoBtn.button('loading');
                    jQuery.getJSON('/bookmark/get_info', {
                        url: $("#url").val()
                    }).done(function(response) {
                        $getBookmarkInfoBtn.button('reset');
                        if (response.success === 'true') {
                            initBookmarkForm($("#url").val(), response);
                        } else {
                            alert('数据库返回错误');
                        }
                    });
                });
                // 点击提交按钮，添加书签
                $(document).on('click', '#addBookmarkBtn', function() {
                    var url = $('#url').val();
                    var title = $('#title').val();
                    $.ajax({
                        url: '/bookmark/add',
                        data: {
                            url: url,
                            favicon: '',
                            tags: $('#tags').val(),
                            note: $('#note').val()
                        },
                        dataType: 'json',
                        type: "POST"
                    }).done(function(response) {
                        if (response.success === 'true') {
                            if(lastEditor) {
                                lastEditor.replaceWith(response.bookmark_module);
                                lastEditor = null;
                            } else {
                                $('#bookmarkList').prepend(response.bookmark_module);
                            }
                            showArticle(url, title, response.article);
                            resetBookmarkForm();
                        } else {
                            alert('数据库返回错误');
                        }
                    });
                });
                // 更新书签信息，强制更新
                $(document).on('click', '.bookmark-refresh-btn', function() {
                    that = $(this);
                    var $bookmark_item = that.closest('.bookmark-item');
                    var url = $bookmark_item.find('.bookmark-favicon').attr('href');
                    // 更新按钮转动
                    var animateClass = "fa-spin";
                    that.find('.fa-refresh').addClass(animateClass);
                    jQuery.getJSON('/bookmark/refresh', {
                        url: url
                    }).done(function(response) {
                        if (response.success === 'true') {
                            $bookmark_item.replaceWith(response.bookmark_module);
                            // showArticle(url, response.title, response.article);
                        } else {
                            that.find('.fa-refresh').removeClass(animateClass);
                            alert('数据库返回错误');
                        }
                    });
                });
                // 加星
                $(document).on('click', '.bookmark-star-btn', function() {
                    var that = $(this);
                    $bookmark = that.closest('.bookmark-item');
                    var url = $bookmark.find('.bookmark-favicon').attr('href');
                    jQuery.getJSON('/bookmark/set_star', {
                        url: url
                    }).done(function(response) {
                        if (response.success === 'true') {
                            if (response.is_star === 0) {
                                oldclass = "fa-star";
                                newclass = "fa-star-o";
                            } else {
                                oldclass = "fa-star-o";
                                newclass = "fa-star";
                            }
                            that.find('i').removeClass(oldclass).addClass(newclass);
                        } else {
                            alert('数据库返回错误');
                        }
                    });
                });
                // 编辑书签
                $(document).on('click', '.bookmark-edit-btn', function() {
                    $('div.quickflip-wrapper').quickFlipper();
                    lastEditor = $(this).closest('.bookmark-item');
                    var url = lastEditor.find('.bookmark-favicon').attr('href');
                    jQuery.getJSON('/bookmark/get_detail', {
                        url: url
                    }).done(function(response) {
                        if (response.success === 'true') {
                            initBookmarkForm(url, response);
                        } else {
                            alert('数据库返回错误');
                        }
                    });
                });
                // 删除书签
                $(document).on('click', '.bookmark-del-btn', function() {
                    var $bookmark_item = $(this).closest('.bookmark-item');
                    var url = $bookmark_item.find('.bookmark-favicon').attr('href');
                    $.ajax({
                        url: '/bookmark/del',
                        data: {
                            url: url
                        },
                        dataType: 'json',
                        type: "POST"
                    }).done(function(response) {
                        if (response.success === 'true') {
                            $bookmark_item.remove();
                        } else {
                            alert('数据库返回错误');
                        }
                    });
                });
                // 随机获取书签
                $(document).on('click', '#randomBookmarksBtn', function() {
                    $('#randomBookmarks').empty().load('/random');
                });
                $(document).on('click', '.pagination li a', function() {
                    keywords = $('#pageBookmarkList').attr('keywords');
                    tag = $('#pageBookmarkList').attr('tag');
                    page = this.title;
                    $('#pageBookmarkList').empty().load('/bookmark', {
                        keywords: keywords,
                        tag: tag,
                        page: page
                    }, function() {
                        $("img.lazy").lazy({
                            bind: "event",
                            delay: 0
                        });
                    });
                });
                $(document).on('click', '.bookmark-read-btn', function() {
                    var $bookmark_item = $(this).closest('.bookmark-item');
                    var url = $bookmark_item.find('.bookmark-favicon').attr('href');
                    var $bookmark_article = $bookmark_item.find('.bookmark-article');
                    // 隐藏所有
                    $('.bookmark-article').hide();
                    jQuery.getJSON('/bookmark/get_article', {
                        url: url
                    }, function(response) {
                        if (response.success === 'true') {
                            $bookmark_article.html(response.article).append(empty_article_btn_html).slideDown("slow");
                        } else {
                            alert('数据库返回错误');
                        }
                    });
                });
                $(document).on('click', '.bookmark-article-empty-btn', function() {
                    $('.bookmark-article').slideUp("fast");
                });
                // getRandomBookmark();
            };
        return {
            init: init
        };
    })();
    App.init();
})(jQuery);
