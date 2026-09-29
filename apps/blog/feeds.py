from django.contrib.syndication.views import Feed
from django.urls import reverse

from .models import Post


class LatestPostsFeed(Feed):
    title = "Blog Inicia Legal"
    link = "/blog/"
    description = "Artículos y novedades legales para empresas y personas."

    def items(self):
        return Post.published.all()[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_pubdate(self, item):
        return item.published_at

    def item_author_name(self, item):
        return item.author_name

    def item_link(self, item):
        return reverse("blog:post_detail", args=[item.slug])
