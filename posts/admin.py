from django.contrib import admin

from .models import Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "pub_date", "author", "group",)
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = "-пусто-"


admin.site.register(Post, PostAdmin)


class GroupAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "description",)
    prepopulated_fields = {"slug": ("title",)}
    search_field = ("title",)
    empty_value_display = "-пусто-"


admin.site.register(Group, GroupAdmin)
