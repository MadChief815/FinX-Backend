from django.contrib import admin

from .models import Income, Loan, MonthPage, Spend, SubPage, SubSpend


class FinanceModelAdmin(admin.ModelAdmin):
    readonly_fields = ("is_deleted", "created_at", "updated_at")

    def get_queryset(self, request):
        return self.model.all_objects.get_queryset()


@admin.register(MonthPage)
class MonthPageAdmin(FinanceModelAdmin):
    list_display = (
        "title",
        "user",
        "month",
        "year",
        "is_completed",
        "is_deleted",
        "created_at",
    )
    list_filter = ("year", "month", "is_completed", "is_deleted")
    search_fields = ("title", "user__username", "user__email")
    ordering = ("-year", "-month", "title")


@admin.register(Spend)
class SpendAdmin(FinanceModelAdmin):
    list_display = (
        "title",
        "month_page",
        "amount",
        "is_completed",
        "has_subpage",
        "is_deleted",
        "created_at",
    )
    list_filter = ("is_completed", "has_subpage", "is_deleted")
    search_fields = ("title", "month_page__title", "month_page__user__username")
    ordering = ("month_page__year", "month_page__month", "title")


@admin.register(SubPage)
class SubPageAdmin(FinanceModelAdmin):
    list_display = (
        "title",
        "spend",
        "is_completed",
        "is_deleted",
        "created_at",
    )
    list_filter = ("is_completed", "is_deleted")
    search_fields = ("title", "spend__title", "spend__month_page__user__username")
    ordering = ("title",)


@admin.register(SubSpend)
class SubSpendAdmin(FinanceModelAdmin):
    list_display = (
        "title",
        "sub_page",
        "amount",
        "is_completed",
        "is_deleted",
        "created_at",
    )
    list_filter = ("is_completed", "is_deleted")
    search_fields = (
        "title",
        "sub_page__title",
        "sub_page__spend__month_page__user__username",
    )
    ordering = ("sub_page__title", "title")


@admin.register(Loan)
class LoanAdmin(FinanceModelAdmin):
    list_display = (
        "person_name",
        "user",
        "amount",
        "type",
        "status",
        "is_deleted",
        "created_at",
    )
    list_filter = ("type", "status", "is_deleted")
    search_fields = ("person_name", "user__username", "user__email")
    ordering = ("-created_at",)


@admin.register(Income)
class IncomeAdmin(FinanceModelAdmin):
    list_display = (
        "title",
        "user",
        "amount",
        "expected_date",
        "is_received",
        "is_deleted",
        "created_at",
    )
    list_filter = ("is_received", "expected_date", "is_deleted")
    search_fields = ("title", "user__username", "user__email")
    ordering = ("expected_date", "title")
