from django.contrib import admin

from .models import Dashboard


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "bank_money",
        "cash_money",
        "created_at",
        "updated_at",
    )
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("user__username",)

    def has_delete_permission(self, request, obj=None):
        return False
