from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True


class MonthPage(SoftDeleteModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="month_pages",
    )
    title = models.CharField(max_length=100)
    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    year = models.IntegerField(validators=[MinValueValidator(1)])
    is_completed = models.BooleanField(default=False)

    def clean(self):
        super().clean()
        if not self.user_id or self.month is None or self.year is None or not self.title:
            return

        duplicate_pages = MonthPage.objects.filter(
            user_id=self.user_id,
            year=self.year,
        )
        if self.pk:
            duplicate_pages = duplicate_pages.exclude(pk=self.pk)

        errors = {}
        if duplicate_pages.filter(month=self.month).exists():
            errors["month"] = "A month page already exists for this month and year."
        if duplicate_pages.filter(title__iexact=self.title).exists():
            errors["title"] = "A month page with this title already exists in this year."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title


class Spend(SoftDeleteModel):
    month_page = models.ForeignKey(
        MonthPage,
        related_name="spends",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_completed = models.BooleanField(default=False)
    has_subpage = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}: {self.amount}"


class SubPage(SoftDeleteModel):
    spend = models.OneToOneField(
        Spend,
        related_name="sub_page",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class SubSpend(SoftDeleteModel):
    sub_page = models.ForeignKey(
        SubPage,
        related_name="subspends",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}: {self.amount}"


class Loan(SoftDeleteModel):
    class LoanType(models.TextChoices):
        BORROWED = "borrowed", "Borrowed"
        LENT = "lent", "Lent"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAID = "paid", "Paid"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="loans",
    )
    person_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=20, choices=LoanType.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    def __str__(self):
        return f"{self.person_name}: {self.amount}"


class Income(SoftDeleteModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="incomes",
    )
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    expected_date = models.DateField()
    is_received = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}: {self.amount}"
