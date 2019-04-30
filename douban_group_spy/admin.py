import json

from django.contrib import admin
from django.contrib.admin import ModelAdmin, SimpleListFilter
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


class KeywordFilter(SimpleListFilter):
    title = 'keyword_list'
    parameter_name = 'keyword_list'

    def lookups(self, request, model_admin):
        keyword_lists = model_admin.model.objects.values('keyword_list').distinct()
        return sorted([(k['keyword_list'], k['keyword_list']) for k in keyword_lists])

    def queryset(self, request, queryset):
        if self.value():
            qs = queryset.filter(keyword_list=json.loads(self.value()))
            return qs
        return queryset


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
    list_filter = ('group__name', 'is_matched', 'is_collected', KeywordFilter)
    search_fields = ('title', 'content')
    fields = (
        'post_id',
        'group',
        'title',
        'show_alt',
        'is_matched',
        'is_collected',
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
    readonly_fields = get_model_fields(Post, ['comment', 'is_collected']) + ['photos', 'show_alt']
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
