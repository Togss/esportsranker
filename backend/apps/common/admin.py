from django.contrib import admin
from django.core.exceptions import PermissionDenied
from apps.accounts.models import UserRole


class RoleProtectedAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        # Controls if this app shows up in the sidebar
        if not request.user.is_authenticated:
            return False
        if not request.user.is_staff:
            return False
        return True

    def has_view_permission(self, request, obj=None):
        # Can they see list/detail views?
        if not request.user.is_authenticated or not request.user.is_staff:
            return False
        return True

    def has_add_permission(self, request):
        # Who can create records?
        if not request.user.is_authenticated or not request.user.is_staff:
            return False
        return request.user.role in {UserRole.ADMIN, UserRole.MODERATOR}

    def has_change_permission(self, request, obj=None):
        # Who can edit existing records?
        if not request.user.is_authenticated or not request.user.is_staff:
            return False
        return request.user.role in {UserRole.ADMIN}

    def has_delete_permission(self, request, obj=None):
        # Who can delete?
        if not request.user.is_authenticated or not request.user.is_staff:
            return False
        return request.user.role in {UserRole.ADMIN}

    def get_queryset(self, request):
        # You already had this, just returning qs.
        qs = super().get_queryset(request)
        return qs
    
    # Hard Stops : If someone tries to edit via code bypassing admin UI
    def save_model(self, request, obj, form, change):
        if not self.has_change_permission(request, obj):
            raise PermissionDenied
        return super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        if not self.has_delete_permission(request, obj):
            raise PermissionDenied
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        if not self.has_delete_permission(request):
            raise PermissionDenied
        return super().delete_queryset(request, queryset)