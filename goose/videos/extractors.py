# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from goose.videos.videos import Video

VIDEOS_TAGS = ['iframe', 'embed', 'object', 'video']
VIDEO_PROVIDERS = ['youtube', 'vimeo', 'dailymotion', 'kewego']


class VideoExtractor(object):
    """\
    Extracts a list of video from Article top node
    """
    def __init__(self, article, config):
        # article
        self.article = article

        # config
        self.config = config

        # parser
        self.parser = self.config.get_parser()

        # candidates
        self.candidates = []

        # movies
        self.movies = []

    def get_embed_code(self, node):
        return "".join([line.strip() for line in self.parser.nodeToString(node).splitlines()])

    def get_embed_type(self, node):
        return self.parser.getTag(node)

    def get_width(self, node):
        return self.parser.getAttribute(node, 'width')

    def get_height(self, node):
        return self.parser.getAttribute(node, 'height')

    def get_src(self, node):
        return self.parser.getAttribute(node, 'src')

    def get_provider(self, src):
        if src:
            for provider in VIDEO_PROVIDERS:
                if provider in src:
                    return provider
        return None

    def get_video(self, node):
        """
        Create a video object from a video embed
        """
        video = Video()
        video.embed_code = self.get_embed_code(node)
        video.embed_type = self.get_embed_type(node)
        video.width = self.get_width(node)
        video.height = self.get_height(node)
        video.src = self.get_src(node)
        video.provider = self.get_provider(video.src)
        return video

    def get_iframe_tag(self, node):
        return self.get_video(node)

    def get_video_tag(self, node):
        """extract html video tags"""
        return Video()

    def get_embed_tag(self, node):
        # embed node may have an object node as parent
        # in this case we want to retrieve the object node
        # instead of the embed
        parent = self.parser.getParent(node)
        if parent is not None:
            parent_tag = self.parser.getTag(parent)
            if parent_tag == 'object':
                return self.get_object_tag(node)
        return self.get_video(node)

    def get_object_tag(self, node):
        # test if object tag has en embed child
        # in this case we want to remove the embed from
        # the candidate list to avoid parsing it twice
        child_embed_tag = self.parser.getElementsByTag(node, 'embed')
        if child_embed_tag and child_embed_tag[0] in self.candidates:
            self.candidates.remove(child_embed_tag[0])

        # get the object source
        # if wa don't have a src node don't coninue
        src_node = self.parser.getElementsByTag(node, tag="param", attr="name", value="movie")
        if not src_node:
            return None

        src = self.parser.getAttribute(src_node[0], "value")

        # check provider
        provider = self.get_provider(src)
        if not provider:
            return None

        video = self.get_video(node)
        video.provider = provider
        video.src = src
        return video

    def get_videos(self):
        # candidates node
        self.candidates = self.parser.getElementsByTags(self.article.top_node, VIDEOS_TAGS)

        # loop all candidates
        # and check if src attribute belongs to a video provider
        for candidate in self.candidates:
            tag = self.parser.getTag(candidate)
            attr = "get_%s_tag" % tag
            if hasattr(self, attr):
                movie = getattr(self, attr)(candidate)
                if movie is not None and movie.provider is not None:
                    self.movies.append(movie)

        # append movies list to article
        self.article.movies = list(self.movies)
