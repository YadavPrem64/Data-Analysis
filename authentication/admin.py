from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, LoginAttempt


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_email_verified', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'userprofile__email_verified')
    
    def get_email_verified(self, obj):
        try:
            return obj.userprofile.email_verified
        except UserProfile.DoesNotExist:
            return False
    get_email_verified.boolean = True
    get_email_verified.short_description = 'Email Verified'


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'username', 'success', 'timestamp')
    list_filter = ('success', 'timestamp')
    search_fields = ('ip_address', 'username')
    readonly_fields = ('ip_address', 'username', 'success', 'timestamp')
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        # Prevent manual addition of login attempts
        return False
    
    def has_change_permission(self, request, obj=None):
        # Prevent editing of login attempts
        return False


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
