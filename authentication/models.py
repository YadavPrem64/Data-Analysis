from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class UserProfile(models.Model):
    """Extended user profile with additional fields."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Profile"


class LoginAttempt(models.Model):
    """Track login attempts for rate limiting."""
    ip_address = models.GenericIPAddressField()
    username = models.CharField(max_length=150, blank=True, null=True)
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.ip_address} - {status} - {self.timestamp}"

    @classmethod
    def get_recent_failures(cls, ip_address, minutes=15):
        """Get failed login attempts for an IP in the last N minutes."""
        cutoff_time = timezone.now() - timezone.timedelta(minutes=minutes)
        return cls.objects.filter(
            ip_address=ip_address,
            success=False,
            timestamp__gte=cutoff_time
        ).count()
