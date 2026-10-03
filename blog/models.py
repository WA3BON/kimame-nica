from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from cloudinary.models import CloudinaryField


class Tag(models.Model):
    name = models.CharField(_('タグ名'), max_length=50, unique=True)
    slug = models.SlugField(_('URL用の名前'), max_length=60, unique=True, blank=True, allow_unicode=True)

    class Meta:
        ordering = ['name']
        verbose_name = _('タグ')
        verbose_name_plural = _('タグ')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True) or 'tag'
            slug = base_slug
            n = 1
            while Tag.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base_slug}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)


class Post(models.Model):
    title = models.CharField(_('タイトル'), max_length=200)
    slug = models.SlugField(_('URL用の名前'), max_length=220, unique=True, blank=True, allow_unicode=True)
    excerpt = models.CharField(_('概要'), max_length=300, blank=True, help_text=_('一覧に表示する短い紹介文'))
    content = models.TextField(_('本文'), help_text=_('本文(改行はそのまま反映されます)'))
    thumbnail = CloudinaryField(_('サムネイル'), folder='blog/', blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('投稿者'))
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True, verbose_name=_('タグ'))
    is_published = models.BooleanField(_('公開'), default=True)
    published_at = models.DateTimeField(_('公開日時'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新日時'), auto_now=True)

    class Meta:
        ordering = ['-published_at']
        verbose_name = _('ブログ記事')
        verbose_name_plural = _('ブログ記事')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True) or 'post'
            slug = base_slug
            n = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base_slug}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)
