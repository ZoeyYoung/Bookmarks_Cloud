Bookmarks_Cloud
===============

![界面](http://zoeyyoung.gitcafe.com/static/images/20130807001420.jpg)

[更新历史](http://zoeyyoung.gitcafe.com/bookmarks-cloud-tornado-project.html)

### 安装

在安装Python与virtualenv的基础上

Windows下安装记录

    virtualenv Bookmarks_Cloud
    cd Bookmarks_Cloud/Scripts
    activate.bat
    cd ..
    pip install -r requirements.txt

安装[lxml](http://www.lfd.uci.edu/~gohlke/pythonlibs/), 复制安装文件(lxml和lxml-x.x.x-py3.3.egg-info文件夹)到**F:\Bookmarks_Cloud\Lib\site-packages**下

安装[MongoDB](http://www.mongodb.org/)

### 运行

    cd Bookmarks_Cloud/Scripts
    activate.bat
    cd ..
    python run.py

打开 http://localhost:8888/ 即可使用.

### 后台

Web框架使用[Tornado](https://github.com/facebook/tornado)

数据库使用[MongoDB](http://www.mongodb.org/)

正文提取在[readability-lxml](https://github.com/buriy/python-readability)基础上进行修改

分词采用[结巴分词](https://github.com/fxsjy/jieba/tree/jieba3k)

### 前端

界面以[Bootstrap 3](http://getbootstrap.com/)为基础进行设计

图标字体采用[FontAwesome](http://fontawesome.io/)

使用到的jQuery插件:

* 翻转插件[QuickFlip 2: The jQuery Flipping Plugin Made Faster and Simpler](http://jonraasch.com/blog/quickflip-2-jquery-plugin)
* [瀑布流插件](http://wlog.cn/waterfall/index-zh.html) —— 已删除
* 滚动条插件使用[nanoScrollerJS](https://github.com/jamesflorentino/nanoScrollerJS) —— 考虑更换

