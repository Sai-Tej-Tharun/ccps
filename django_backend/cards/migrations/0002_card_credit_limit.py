from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cards", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="card",
            name="credit_limit",
            field=models.DecimalField(decimal_places=2, default=5000, max_digits=12),
        ),
    ]