from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="dashboard",
            name="fixed_deposit_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
        migrations.AddField(
            model_name="dashboard",
            name="flexible_savings_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
        ),
    ]
