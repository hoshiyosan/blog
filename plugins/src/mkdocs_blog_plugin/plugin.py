import json
import os
import shutil
from datetime import date
from typing import Set

from jinja2 import Template
from mkdocs.plugins import BasePlugin
from mkdocs.structure.pages import File

PACKAGE_FOLDER = os.path.abspath(os.path.join(__file__, ".."))
TEMPLATES_FOLDER = os.path.join(PACKAGE_FOLDER, "templates")


def fallback_serializer(o):
    if isinstance(o, date):
        return o.isoformat()
    raise TypeError("Fallback serializer can't serialize type: %s" % type(o))


def get_template(template_name: str) -> Template:
    template_path = os.path.join(TEMPLATES_FOLDER, template_name)
    with open(template_path) as template_file:
        return Template(template_file.read())


def file_from_static(static_path: str):
    return File()


class DynamicPage:
    def __init__(self, title: str, url: str):
        self.title = title
        self.url = url
        print("create dynamic page", title)

    def get_markdown(self, page, config, files):
        """Implement this function"""
        return ""

    def get_file(self, config):
        src_dir = os.path.abspath(os.path.join(".mkdocs-build"))
        src_file = os.path.abspath(os.path.join(src_dir, self.url))
        file_dir = os.path.join(src_dir, os.path.dirname(src_file))

        os.makedirs(file_dir, exist_ok=True)
        # create an empty file
        print("writing file", self.title)
        with open(src_file + ".md", "w") as file:
            file.write("---\n")
            file.write("title: %s\n" % self.title)
            file.write("---\n")

        return File(self.url + ".md", src_dir, config["site_dir"], use_directory_urls=True)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.url == other
        return False

    def __hash__(self):
        return hash(self.url)


class RecentArticlesIndex(DynamicPage):
    def __init__(self, title: str, url: str, max_articles: int):
        super().__init__(title, url)
        self.max_articles = max_articles
        self.articles = []

    def add_article(self, article: dict):
        if len(self.articles) == self.max_articles:
            if article["creation_date"] <= self.articles[-1]["creation_date"]:
                return
            self.articles.pop()

        i = 0
        while i < len(self.articles) and article["creation_date"] < self.articles[i]["creation_date"]:
            i += 1

        self.articles.insert(i, article)

    def get_markdown(self, page, config, files):
        # update page metadata
        # page.title = self.title
        page.meta["template"] = "articles_index"
        # render template
        template = get_template("articles_index.html.j2")
        return template.render(articles=self.articles)


class SuggestionsPage(DynamicPage):
    def __init__(self, title: str, url: str):
        super().__init__(title, url)

    def get_markdown(self, page, config, files):
        # update page metadata
        # page.title = self.title
        page.meta["template"] = "articles_index"
        # render template
        template = get_template("suggestions.html")
        return template.render()


class MkdocsBlogPlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__()
        self.articles = []
        self.dynamic_pages: Set[DynamicPage] = set()

    def add_dynamic_page(self, files, config, page: DynamicPage):
        self.dynamic_pages.add(page)
        files.append(page.get_file(config))

    def get_dynamic_page(self, url: str):
        try:
            return next(page for page in self.dynamic_pages if page.url == url.strip("/"))
        except StopIteration:
            return None

    def on_files(self, files, config):
        self.recent_articles_page = RecentArticlesIndex("Recent Articles", "recent-articles", max_articles=3)
        self.add_dynamic_page(files, config, self.recent_articles_page)
        self.add_dynamic_page(files, config, SuggestionsPage("Suggested articles", "suggestions"))

    def on_config(self, config, **kwargs):
        layout_folder = os.path.join(PACKAGE_FOLDER, "layout")
        config.theme.dirs.insert(0, layout_folder)
        return config

    def register_article(self, page):
        article_data = {
            "title": page.title,
            "link": "/" + page.url,
            "summary": page.meta["summary"],
            "author": page.meta["author"],
            "creation_date": page.meta["creation_date"],
            "revision_date": page.meta["revision_date"],
            "topics": page.meta["topics"],
        }
        self.recent_articles_page.add_article(article_data)
        self.articles.append(article_data)

    def on_page_markdown(self, markdown, page, config, files):
        dynamic_page = self.get_dynamic_page(page.url)
        if dynamic_page:
            print("dynamic page", page.title, page)
            return dynamic_page.get_markdown(page, config, files)

        if page.meta.get("template") == "article":
            self.register_article(page)

        return markdown

    def on_post_build(self, *, config) -> None:
        with open(os.path.join(config["site_dir"], "search/articles.json"), "w") as articles_index:
            json.dump({"articles": self.articles}, articles_index, default=fallback_serializer)
        # shutil.rmtree(".mkdocs-build", ignore_errors=True)
