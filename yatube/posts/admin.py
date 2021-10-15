from django.contrib import admin

from .models import Group, Post

EMPTY = '-пусто-'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'image',
        'pub_date',
        'author',
        'group',
    )

    list_editable = ('group', 'author', 'image')
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = EMPTY


@admin.register(Group)
class PostGroup(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'description',
        'slug',
    )

    list_editable = ('title', 'description', 'slug')
    search_fields = ('title',)
    empty_value_display = EMPTY
