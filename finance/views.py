from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from dashboard.services import build_dashboard_summary

from . import services
from .models import Income, Loan, MonthPage, Spend, SubPage, SubSpend
from .serializers import (
    DeductSpendingSerializer,
    IncomeSerializer,
    LoanSerializer,
    MonthPageSerializer,
    SpendSerializer,
    SubPageSerializer,
    SubSpendSerializer,
)


class FinanceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]

    def perform_destroy(self, instance):
        services.soft_delete(instance)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"success": True, "message": "Resource deleted successfully."},
            status=status.HTTP_200_OK,
        )


class MonthPageViewSet(FinanceViewSet):
    serializer_class = MonthPageSerializer
    filterset_fields = ["month", "year", "is_completed"]

    def get_queryset(self):
        return MonthPage.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def deduct(self, request, pk=None):
        month_page = self.get_object()
        serializer = DeductSpendingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.deduct_month_spending(
            month_page,
            serializer.validated_data["source"],
        )
        return Response(
            {
                "source": result["source"],
                "deducted": result["deducted"],
                "dashboard": build_dashboard_summary(result["dashboard"]),
            }
        )


class SpendViewSet(FinanceViewSet):
    serializer_class = SpendSerializer
    filterset_fields = ["month_page", "is_completed", "has_subpage"]

    def get_queryset(self):
        return Spend.objects.filter(
            month_page__user=self.request.user,
            month_page__is_deleted=False,
        )


class SubPageViewSet(FinanceViewSet):
    serializer_class = SubPageSerializer
    filterset_fields = ["spend", "is_completed"]

    def get_queryset(self):
        return SubPage.objects.filter(
            spend__month_page__user=self.request.user,
            spend__month_page__is_deleted=False,
            spend__is_deleted=False,
        )

    def perform_create(self, serializer):
        serializer.instance = services.create_sub_page(serializer.validated_data)

    def perform_update(self, serializer):
        serializer.instance = services.update_sub_page(
            serializer.instance,
            serializer.validated_data,
        )

    def perform_destroy(self, instance):
        services.soft_delete_sub_page(instance)


class SubSpendViewSet(FinanceViewSet):
    serializer_class = SubSpendSerializer
    filterset_fields = ["sub_page", "is_completed"]

    def get_queryset(self):
        return SubSpend.objects.filter(
            sub_page__spend__month_page__user=self.request.user,
            sub_page__spend__month_page__is_deleted=False,
            sub_page__spend__is_deleted=False,
            sub_page__is_deleted=False,
        )


class LoanViewSet(FinanceViewSet):
    serializer_class = LoanSerializer
    filterset_fields = ["type", "status"]

    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IncomeViewSet(FinanceViewSet):
    serializer_class = IncomeSerializer
    filterset_fields = ["is_received", "expected_date"]

    def get_queryset(self):
        return Income.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
