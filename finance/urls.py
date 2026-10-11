from rest_framework.routers import DefaultRouter

from .views import (
    IncomeViewSet,
    LoanViewSet,
    MonthPageViewSet,
    SpendViewSet,
    SubPageViewSet,
    SubSpendViewSet,
)


router = DefaultRouter()
router.register("months", MonthPageViewSet, basename="month-page")
router.register("spends", SpendViewSet, basename="spend")
router.register("subpages", SubPageViewSet, basename="subpage")
router.register("subspends", SubSpendViewSet, basename="subspend")
router.register("loans", LoanViewSet, basename="loan")
router.register("incomes", IncomeViewSet, basename="income")

urlpatterns = router.urls
