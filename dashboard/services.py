import calendar
from decimal import Decimal

from django.db.models import Sum

from finance.models import Income, Loan, MonthPage
from finance.services import calculate_month_totals_for_pages


ZERO = Decimal("0.00")


def build_dashboard_summary(dashboard):
    user = dashboard.user

    loan_total = (
        Loan.objects.filter(
            user=user,
            type=Loan.LoanType.BORROWED,
            status=Loan.Status.ACTIVE,
        ).aggregate(total=Sum("amount"))["total"]
        or ZERO
    )
    income_total = (
        Income.objects.filter(user=user, is_received=False)
        .aggregate(total=Sum("amount"))["total"]
        or ZERO
    )

    month_pages = list(
        MonthPage.objects.filter(user=user).order_by("year", "month")
    )
    month_totals = calculate_month_totals_for_pages(month_pages)
    months = {
        f"{calendar.month_name[page.month]} {page.year}": month_totals[page.pk]
        for page in month_pages
    }

    bank_money = dashboard.bank_money
    cash_money = dashboard.cash_money
    return {
        "bank_money": bank_money,
        "cash_money": cash_money,
        "fixed_deposit_money": dashboard.fixed_deposit_money,
        "flexible_savings_money": dashboard.flexible_savings_money,
        "total_available": bank_money + cash_money,
        "loan_total": loan_total,
        "income_total": income_total,
        "months": months,
    }
