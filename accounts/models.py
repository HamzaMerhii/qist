from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        MANAGER = "MANAGER", "Manager"
        CASHIER = "CASHIER", "Cashier"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CASHIER,
    )

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        role = UserProfile.Role.ADMIN if instance.is_superuser else UserProfile.Role.CASHIER
        UserProfile.objects.create(user=instance, role=role)
    else:
        UserProfile.objects.get_or_create(user=instance)
        instance.profile.save()
