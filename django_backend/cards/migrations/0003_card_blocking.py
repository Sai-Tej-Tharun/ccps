from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cards", "0002_card_credit_limit"),
    ]

    operations = [
        migrations.AddField(
            model_name="card",
            name="is_blocked",
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name="card",
            name="blocked_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]