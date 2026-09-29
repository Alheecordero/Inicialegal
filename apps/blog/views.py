from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm
from .models import Category, Post, Tag


def _sidebar_context():
    return {
        "categories": Category.objects.annotate(
            n=Count("posts", filter=Q(posts__status=Post.PUBLISHED))
        ).filter(n__gt=0),
        "popular_tags": Tag.objects.annotate(n=Count("posts")).filter(n__gt=0).order_by("-n")[:15],
        "recent_posts": Post.published.select_related("category")[:4],
    }


def _paginate(request, queryset):
    paginator = Paginator(queryset, settings.BLOG_PAGINATE_BY)
    return paginator.get_page(request.GET.get("page"))


def post_list(request):
    from apps.core.models import HeroSlide

    qs = Post.published.select_related("category", "author").prefetch_related("tags")
    query = request.GET.get("q", "").strip()
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(content__icontains=query))
    featured = None if query else Post.published.filter(is_featured=True).first()
    if featured and not request.GET.get("page"):
        qs = qs.exclude(pk=featured.pk)
    else:
        featured = None
    banner = None if query else HeroSlide.objects.filter(key="banners", is_active=True).first()
    context = {"page_obj": _paginate(request, qs), "featured": featured, "query": query, "blog_banner": banner, **_sidebar_context()}
    return render(request, "blog/post_list.html", context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    qs = Post.published.filter(category=category).select_related("category", "author")
    context = {"page_obj": _paginate(request, qs), "category": category, **_sidebar_context()}
    return render(request, "blog/post_list.html", context)


def tag_detail(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    qs = Post.published.filter(tags=tag).select_related("category", "author")
    context = {"page_obj": _paginate(request, qs), "tag": tag, **_sidebar_context()}
    return render(request, "blog/post_list.html", context)


def post_detail(request, slug):
    base = Post.objects.select_related("category", "author").prefetch_related("tags", "areas")
    if request.user.is_staff:
        post = get_object_or_404(base, slug=slug)  # el staff puede previsualizar borradores
    else:
        post = get_object_or_404(base.filter(status=Post.PUBLISHED), slug=slug)
        if not post.is_published:
            from django.http import Http404
            raise Http404

    if post.is_published:
        Post.objects.filter(pk=post.pk).update(views=F("views") + 1)

    form = CommentForm()
    if request.method == "POST" and post.allow_comments:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            parent_id = request.POST.get("parent")
            if parent_id and parent_id.isdigit():
                comment.parent = post.comments.filter(pk=int(parent_id), is_approved=True).first()
            comment.save()
            messages.success(request, "Gracias por tu comentario. Será publicado una vez revisado por nuestro equipo.")
            return redirect(post.get_absolute_url() + "#comentarios")
        messages.error(request, "Revisa los campos del formulario de comentarios.")

    related = Post.published.exclude(pk=post.pk)
    if post.category_id:
        related = related.filter(Q(category=post.category) | Q(tags__in=post.tags.all())).distinct()
    context = {
        "post": post,
        "related": related[:3],
        "comments": post.approved_comments().prefetch_related("replies"),
        "form": form,
        "prev_post": Post.published.filter(published_at__lt=post.published_at).first(),
        "next_post": Post.published.filter(published_at__gt=post.published_at).order_by("published_at").first(),
        **_sidebar_context(),
    }
    return render(request, "blog/post_detail.html", context)
