from django.conf import settings
from django.db import models


class Dashboard(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard",
    )
    bank_money = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cash_money = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dashboard for {self.user}"
