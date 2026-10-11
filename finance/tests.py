from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APITestCase

from dashboard.models import Dashboard

from .models import MonthPage, Spend, SubPage, SubSpend


class MonthPageDashboardTests(APITestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="finance-owner",
            password="test-password",
        )
        self.dashboard = Dashboard.objects.create(
            user=self.user,
            bank_money=Decimal("100.00"),
            cash_money=Decimal("25.00"),
        )
        self.month_page = MonthPage.objects.create(
            user=self.user,
            title="October 2026",
            month=10,
            year=2026,
        )
        Spend.objects.create(
            month_page=self.month_page,
            title="Completed spend",
            amount=Decimal("5.00"),
            is_completed=True,
        )
        Spend.objects.create(
            month_page=self.month_page,
            title="Pending spend",
            amount=Decimal("30.00"),
        )
        self.client.force_authenticate(self.user)

    def test_month_page_response_includes_spend_totals(self):
        response = self.client.get("/finance/months/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["results"][0]["totals"],
            {
                "total": Decimal("35.00"),
                "spent": Decimal("5.00"),
                "to_spend": Decimal("30.00"),
            },
        )

    def test_cannot_create_duplicate_month_for_same_year(self):
        response = self.client.post(
            "/finance/months/",
            {
                "title": "Another October",
                "month": 10,
                "year": 2026,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("month", response.data["message"])

    def test_cannot_create_duplicate_title_in_same_year(self):
        response = self.client.post(
            "/finance/months/",
            {
                "title": "october 2026",
                "month": 11,
                "year": 2026,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.data["message"])

    def test_cannot_edit_month_to_duplicate_existing_month(self):
        another_month = MonthPage.objects.create(
            user=self.user,
            title="November 2026",
            month=11,
            year=2026,
        )

        response = self.client.patch(
            f"/finance/months/{another_month.pk}/",
            {"month": 10},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("month", response.data["message"])

    def test_cannot_edit_title_to_duplicate_title_in_same_year(self):
        another_month = MonthPage.objects.create(
            user=self.user,
            title="November 2026",
            month=11,
            year=2026,
        )

        response = self.client.patch(
            f"/finance/months/{another_month.pk}/",
            {"title": "october 2026"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.data["message"])

    def test_editing_month_without_creating_duplicate_is_allowed(self):
        response = self.client.patch(
            f"/finance/months/{self.month_page.pk}/",
            {"title": "October budget"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "October budget")

    def test_model_validation_rejects_duplicate_month_for_admin_forms(self):
        duplicate = MonthPage(
            user=self.user,
            title="Another October",
            month=10,
            year=2026,
        )

        with self.assertRaises(ValidationError) as error:
            duplicate.full_clean()

        self.assertIn("month", error.exception.message_dict)

    def test_model_validation_rejects_duplicate_title_for_admin_forms(self):
        duplicate = MonthPage(
            user=self.user,
            title="october 2026",
            month=11,
            year=2026,
        )

        with self.assertRaises(ValidationError) as error:
            duplicate.full_clean()

        self.assertIn("title", error.exception.message_dict)

    def test_soft_deleted_month_does_not_block_reuse(self):
        self.month_page.is_deleted = True
        self.month_page.save()
        replacement = MonthPage(
            user=self.user,
            title="October again",
            month=10,
            year=2026,
        )

        replacement.full_clean()

    def test_soft_deleting_month_soft_deletes_all_descendants(self):
        spend = Spend.objects.create(
            month_page=self.month_page,
            title="Food",
            amount=Decimal("100.00"),
        )
        sub_page = SubPage.objects.create(spend=spend, title="Food breakdown")
        sub_spend = SubSpend.objects.create(
            sub_page=sub_page,
            title="Groceries",
            amount=Decimal("50.00"),
        )

        response = self.client.delete(f"/finance/months/{self.month_page.pk}/")

        self.assertEqual(response.status_code, 204)
        self.month_page.refresh_from_db()
        spend.refresh_from_db()
        sub_page.refresh_from_db()
        sub_spend.refresh_from_db()
        self.assertTrue(self.month_page.is_deleted)
        self.assertTrue(spend.is_deleted)
        self.assertTrue(sub_page.is_deleted)
        self.assertTrue(sub_spend.is_deleted)

    def test_soft_deleting_spend_soft_deletes_subpage_and_subspends(self):
        sub_page = SubPage.objects.create(
            spend=Spend.objects.get(title="Pending spend"),
            title="Spend breakdown",
        )
        sub_spend = SubSpend.objects.create(
            sub_page=sub_page,
            title="Breakdown item",
            amount=Decimal("10.00"),
        )

        response = self.client.delete(
            f"/finance/spends/{sub_page.spend_id}/"
        )

        self.assertEqual(response.status_code, 204)
        spend = Spend.all_objects.get(pk=sub_page.spend_id)
        sub_page.refresh_from_db()
        sub_spend.refresh_from_db()
        self.assertTrue(spend.is_deleted)
        self.assertTrue(sub_page.is_deleted)
        self.assertTrue(sub_spend.is_deleted)

    def test_deduct_marks_remaining_spends_and_updates_selected_balance(self):
        response = self.client.post(
            f"/finance/months/{self.month_page.pk}/deduct/",
            {"source": "bank"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["deducted"], Decimal("30.00"))
        self.assertEqual(
            response.data["dashboard"]["bank_money"],
            Decimal("70.00"),
        )
        self.assertEqual(
            response.data["dashboard"]["cash_money"],
            Decimal("25.00"),
        )
        pending_spend = Spend.objects.get(title="Pending spend")
        self.assertTrue(pending_spend.is_completed)

    def test_insufficient_balance_leaves_balance_and_spends_unchanged(self):
        self.dashboard.bank_money = Decimal("10.00")
        self.dashboard.save()

        response = self.client.post(
            f"/finance/months/{self.month_page.pk}/deduct/",
            {"source": "bank"},
            format="json",
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["status_code"], 422)
        self.dashboard.refresh_from_db()
        self.assertEqual(self.dashboard.bank_money, Decimal("10.00"))
        self.assertFalse(Spend.objects.get(title="Pending spend").is_completed)
