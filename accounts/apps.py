from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    # Keep the original app label so existing `users.0001_initial` migration
    # records and the `user_profiles` table remain valid after the package rename.
    label = "users"
