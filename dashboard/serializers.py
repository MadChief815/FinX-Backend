from rest_framework import serializers

from .models import Dashboard


class DashboardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dashboard
        fields = [
            "bank_money",
            "cash_money",
            "fixed_deposit_money",
            "flexible_savings_money",
        ]
