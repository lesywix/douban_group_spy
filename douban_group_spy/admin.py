from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from douban_group_spy.const import HREF_FORMAT, IMG_FORMAT
from douban_group_spy.models import Post, Group


def get_model_fields(model, exclude=None):
    if not exclude:
        return [f.name for f in model._meta.get_fields()]
    fields = []
    for f in model._meta.get_fields():
        if f.name not in exclude:
            fields.append(f.name)
    return fields


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = (
        'post_id',
        'get_group_name',
        'title',
        'show_alt',
        'is_matched',
        'keyword_list',
        'comment',
        'created',
        'updated'
    )
    list_filter = ('group__name', 'is_matched', 'keyword_list')
    search_fields = ('title', 'content')
    fields = (
        'post_id',
        'group',
        'title',
        'show_alt',
        'is_matched',
        'keyword_list',
        'rent',
        'subway',
        'contact',
        'content',
        'created',
        'updated',
        'created_at',
        'photos',
        'comment',
    )
    readonly_fields = get_model_fields(Post, 'comment') + ['photos', 'show_alt']
    ordering = ('created', 'updated')

    def get_group_name(self, obj):
        return obj.group.name

    get_group_name.short_description = 'Group name'
    get_group_name.admin_order_field = 'group__name'

    def show_alt(self, obj):
        return mark_safe(format_html(HREF_FORMAT, url=obj.alt))
    show_alt.short_description = 'Alt'
    show_alt.allow_tags = True

    def photos(self, obj):
        result = ''
        for i in obj.photo_list:
            result += IMG_FORMAT.format(url=i)
        return mark_safe(result)
    photos.allow_tags = True


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    list_display = ('id', 'name', 'show_alt', 'member_count', 'created')

    def show_alt(self, obj):
        return format_html(HREF_FORMAT, url=obj.alt)
    show_alt.short_description = 'Alt'
