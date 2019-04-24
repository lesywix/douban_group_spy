from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.html import format_html

from douban_group_spy.const import ALT_FORMAT
from douban_group_spy.models import Post, Group


@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ('post_id', 'get_group_name', 'title', 'show_alt', 'is_matched', 'keyword_list', 'created', 'updated')

    def get_group_name(self, obj):
        return obj.group.group_name
    get_group_name.short_description = 'Group name'
    get_group_name.admin_order_field = 'group__group_name'

    def show_alt(self, obj):
        return format_html(ALT_FORMAT, url=obj.alt)
    show_alt.short_description = 'Alt'


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    list_display = ('id', 'group_name', 'show_alt', 'member_count', 'created')

    def show_alt(self, obj):
        return format_html(ALT_FORMAT, url=obj.alt)
    show_alt.short_description = 'Alt'
