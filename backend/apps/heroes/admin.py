from django.contrib import admin
from django.utils.html import format_html
from .models import Hero

@admin.register(Hero)
class HeroAdmin(admin.ModelAdmin):
    list_display = (
        'icon_thumb',
        'name',
        'class_combo'
    )
    list_filter = ('primary_class',)
    search_fields = (
        'name',
        'primary_class',
        'slug'
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'icon_preview'
    )
    prepopulated_fields = {'slug': ('name',)}
    ordering = (
        'primary_class',
        'name'
    )
    fieldsets = (
        ('Identity', {
            'fields': (
                'hero_icon',
                'icon_preview',
                'name',
                'slug',
                'primary_class',
                'secondary_class'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    list_display_links = ('icon_thumb', 'name',)

    @admin.display(description='Hero Icon')
    def icon_thumb(self, obj: Hero):
        if obj.hero_icon:
            return format_html(
                '<img src="{}" style="height:24px;width:auto;border-radius:3px;object-fit:cover"/>',
                obj.hero_icon.url)
        return format_html(
            '<div style="height:24px;width:24px;border-radius:3px;background-color:#ccc;display:flex;align-items:center;justify-content:center;color:#666;font-size:12px;">N/A</div>'
        )
    
    @admin.display(description='Icon Preview', ordering='hero_icon')
    def icon_preview(self, obj: Hero):
        if obj.hero_icon:
            return format_html(
                '<img src="{}" style="height:100px;width:auto;border-radius:5px;object-fit:cover"/>',
                obj.hero_icon.url)
        return format_html(
            '<div style="height:100px;width:100px;border:1px dashed #ccc;display:flex;align-items:center;justify-content:center;color:#888;">No Icon</div>'
        )

    @admin.display(description='Class', ordering='primary_class')
    def class_combo(self, obj: Hero):
        return ' / '.join(obj.classes) if obj.classes else "-"