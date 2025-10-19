from django.contrib import admin
from django.utils.html import format_html
from .models import Hero

@admin.register(Hero)
class HeroAdmin(admin.ModelAdmin):
    list_display = ('hero_pic_thumb', 'name', 'hero_class')
    list_filter = ('hero_class',)
    search_fields = ('name', 'hero_class', 'slug')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('hero_class', 'name')
    fieldsets = (
        ('Identity', {
            'fields': ('hero_pic', 'name', 'slug', 'hero_class')}),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')}),
    )

    def hero_pic_thumb(self, obj):
        if getattr(obj, 'hero_pic') and getattr(obj.hero_pic, 'url'):
            return format_html('<img src="{}" style="height:24px;width:auto;border-radius:3px;object-fit:contain"/>', obj.hero_pic.url)
        return "(No Picture)"
    hero_pic_thumb.short_description = 'Hero Picture'