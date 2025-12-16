from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("motry", "0003_vehicleimage_uploads"),
    ]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="parent",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name="replies", to="motry.comment"),
        ),
    ]
