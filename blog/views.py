from django.db.models import Q
from django.views.generic import ListView, DetailView

from .models import Post, Tag


class PostListView(ListView):
    model = Post
    template_name = "blog/post_list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        qs = Post.objects.filter(is_published=True).prefetch_related("tags")

        self.selected_tag = self.request.GET.get("tag", "").strip()
        if self.selected_tag:
            qs = qs.filter(tags__slug=self.selected_tag)

        self.query = self.request.GET.get("q", "").strip()
        if self.query:
            qs = qs.filter(
                Q(title__icontains=self.query)
                | Q(excerpt__icontains=self.query)
                | Q(content__icontains=self.query)
            )

        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tags"] = Tag.objects.all()
        context["selected_tag"] = self.selected_tag
        context["query"] = self.query
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return Post.objects.filter(is_published=True)
