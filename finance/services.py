from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from dashboard.models import Dashboard

from .models import MonthPage, Spend, SubPage, SubSpend


ZERO = Decimal("0.00")


class InsufficientBalanceError(Exception):
    pass


def _totals(total, spent):
    total = total or ZERO
    spent = spent or ZERO
    return {
        "total": total,
        "spent": spent,
        "to_spend": total - spent,
    }


def calculate_month_totals(month_page):
    totals = Spend.objects.filter(month_page=month_page).aggregate(
        total=Sum("amount"),
        spent=Sum("amount", filter=Q(is_completed=True)),
    )
    return _totals(totals["total"], totals["spent"])


def calculate_month_totals_for_pages(month_pages):
    page_ids = [page.pk for page in month_pages]
    if not page_ids:
        return {}

    aggregates = (
        Spend.objects.filter(month_page_id__in=page_ids)
        .values("month_page_id")
        .annotate(
            total=Sum("amount"),
            spent=Sum("amount", filter=Q(is_completed=True)),
        )
    )
    totals_by_page = {
        aggregate["month_page_id"]: _totals(
            aggregate["total"],
            aggregate["spent"],
        )
        for aggregate in aggregates
    }
    return {
        page_id: totals_by_page.get(page_id, _totals(ZERO, ZERO))
        for page_id in page_ids
    }


@transaction.atomic
def deduct_month_spending(month_page, source):
    month_page = MonthPage.objects.select_for_update().get(pk=month_page.pk)
    dashboard, _ = Dashboard.objects.get_or_create(user=month_page.user)
    dashboard = Dashboard.objects.select_for_update().get(pk=dashboard.pk)

    incomplete_spends = Spend.objects.filter(
        month_page=month_page,
        is_completed=False,
    )
    list(incomplete_spends.select_for_update().values_list("pk", flat=True))
    amount = incomplete_spends.aggregate(total=Sum("amount"))["total"] or ZERO

    balance_field = f"{source}_money"
    balance = getattr(dashboard, balance_field)
    if balance < amount:
        raise InsufficientBalanceError(
            f"The {source} balance is insufficient for this month's remaining spends."
        )

    setattr(dashboard, balance_field, balance - amount)
    dashboard.save(update_fields=[balance_field, "updated_at"])
    incomplete_spends.update(is_completed=True, updated_at=timezone.now())

    return {
        "source": source,
        "deducted": amount,
        "dashboard": dashboard,
    }


@transaction.atomic
def create_sub_page(validated_data):
    spend = Spend.objects.select_for_update().get(
        pk=validated_data["spend"].pk,
    )
    validated_data["spend"] = spend
    sub_page = SubPage.all_objects.filter(spend=spend).first()

    if sub_page is None:
        sub_page = SubPage.objects.create(**validated_data)
    else:
        sub_page.title = validated_data["title"]
        sub_page.is_completed = validated_data.get("is_completed", False)
        sub_page.is_deleted = False
        sub_page.save()

    if not spend.has_subpage:
        spend.has_subpage = True
        spend.save(update_fields=["has_subpage", "updated_at"])
    _sync_spend_amount(spend)
    return sub_page


@transaction.atomic
def update_sub_page(sub_page, validated_data):
    for field, value in validated_data.items():
        setattr(sub_page, field, value)
    sub_page.save()
    return sub_page


def _sync_spend_amount(spend):
    amount = (
        SubSpend.objects.filter(sub_page__spend=spend).aggregate(total=Sum("amount"))[
            "total"
        ]
        or ZERO
    )
    spend.amount = amount
    spend.save(update_fields=["amount", "updated_at"])


@transaction.atomic
def create_sub_spend(validated_data):
    sub_page = validated_data["sub_page"]
    spend = Spend.objects.select_for_update().get(pk=sub_page.spend_id)
    sub_spend = SubSpend.objects.create(**validated_data)
    _sync_spend_amount(spend)
    return sub_spend


@transaction.atomic
def update_sub_spend(sub_spend, validated_data):
    sub_spend = SubSpend.objects.select_for_update().get(pk=sub_spend.pk)
    old_spend_id = sub_spend.sub_page.spend_id
    new_sub_page = validated_data.get("sub_page", sub_spend.sub_page)
    spend_ids = sorted({old_spend_id, new_sub_page.spend_id})
    spends = list(
        Spend.objects.select_for_update()
        .filter(pk__in=spend_ids)
        .order_by("pk")
    )

    for field, value in validated_data.items():
        setattr(sub_spend, field, value)
    sub_spend.save()

    for spend in spends:
        _sync_spend_amount(spend)
    return sub_spend


@transaction.atomic
def soft_delete_sub_page(sub_page):
    soft_delete(sub_page)


@transaction.atomic
def soft_delete(instance):
    if instance.is_deleted:
        return

    now = timezone.now()
    if isinstance(instance, MonthPage):
        SubSpend.all_objects.filter(
            sub_page__spend__month_page=instance,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now)
        SubPage.all_objects.filter(
            spend__month_page=instance,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now)
        Spend.all_objects.filter(
            month_page=instance,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now)
    elif isinstance(instance, Spend):
        SubSpend.all_objects.filter(
            sub_page__spend=instance,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now)
        SubPage.all_objects.filter(
            spend=instance,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now)
    elif isinstance(instance, SubPage):
        SubSpend.all_objects.filter(
            sub_page=instance,
            is_deleted=False,
        ).update(is_deleted=True, updated_at=now)

        spend = instance.spend
        if spend.has_subpage:
            spend.has_subpage = False
            spend.save(update_fields=["has_subpage", "updated_at"])
    elif isinstance(instance, SubSpend):
        spend = Spend.objects.select_for_update().get(
            pk=instance.sub_page.spend_id,
        )

    instance.is_deleted = True
    instance.save(update_fields=["is_deleted", "updated_at"])
    if isinstance(instance, SubSpend):
        _sync_spend_amount(spend)
