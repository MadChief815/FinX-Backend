from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Income, Loan, MonthPage, Spend, SubPage, SubSpend
from .services import calculate_month_totals


class UserScopedPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def __init__(self, *args, owner_lookup="user", owner_filters=None, **kwargs):
        self.owner_lookup = owner_lookup
        self.owner_filters = owner_filters or {}
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.context.get("request")
        if queryset is None or request is None or not request.user.is_authenticated:
            return queryset.none() if queryset is not None else None
        return queryset.filter(
            **{self.owner_lookup: request.user},
            **self.owner_filters,
        )


class PositiveAmountSerializerMixin:
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


class MonthPageSerializer(serializers.ModelSerializer):
    totals = serializers.SerializerMethodField()

    class Meta:
        model = MonthPage
        fields = [
            "id",
            "title",
            "month",
            "year",
            "is_completed",
            "totals",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_totals(self, month_page):
        return calculate_month_totals(month_page)

    def validate(self, attrs):
        request = self.context["request"]
        title = attrs.get("title", self.instance.title if self.instance else None)
        month = attrs.get("month", self.instance.month if self.instance else None)
        year = attrs.get("year", self.instance.year if self.instance else None)
        month_page = MonthPage(
            user=request.user,
            title=title,
            month=month,
            year=year,
        )
        if self.instance is not None:
            month_page.pk = self.instance.pk
        try:
            month_page.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        return attrs


class DeductSpendingSerializer(serializers.Serializer):
    source = serializers.ChoiceField(choices=["bank", "cash"])


class SpendSerializer(PositiveAmountSerializerMixin, serializers.ModelSerializer):
    month_page = UserScopedPrimaryKeyRelatedField(
        queryset=MonthPage.objects.all(),
        owner_filters={"is_deleted": False},
    )

    class Meta:
        model = Spend
        fields = [
            "id",
            "month_page",
            "title",
            "amount",
            "is_completed",
            "has_subpage",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "has_subpage", "created_at", "updated_at"]


class SubPageSerializer(serializers.ModelSerializer):
    spend = UserScopedPrimaryKeyRelatedField(
        queryset=Spend.objects.all(),
        owner_lookup="month_page__user",
        owner_filters={
            "month_page__is_deleted": False,
            "is_deleted": False,
        },
    )

    class Meta:
        model = SubPage
        fields = [
            "id",
            "spend",
            "title",
            "is_completed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_fields(self):
        fields = super().get_fields()
        if self.instance is not None:
            fields["spend"].read_only = True
        return fields

    def validate_spend(self, spend):
        request = self.context.get("request")
        if request is not None and SubPage.objects.filter(
            spend=spend,
            spend__month_page__user=request.user,
        ).exists():
            raise serializers.ValidationError(
                "This spend already has an active subpage."
            )
        return spend


class SubSpendSerializer(PositiveAmountSerializerMixin, serializers.ModelSerializer):
    sub_page = UserScopedPrimaryKeyRelatedField(
        queryset=SubPage.objects.all(),
        owner_lookup="spend__month_page__user",
        owner_filters={
            "spend__month_page__is_deleted": False,
            "spend__is_deleted": False,
            "is_deleted": False,
        },
    )

    class Meta:
        model = SubSpend
        fields = [
            "id",
            "sub_page",
            "title",
            "amount",
            "is_completed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class LoanSerializer(PositiveAmountSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = [
            "id",
            "person_name",
            "amount",
            "type",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class IncomeSerializer(PositiveAmountSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = [
            "id",
            "title",
            "amount",
            "expected_date",
            "is_received",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
