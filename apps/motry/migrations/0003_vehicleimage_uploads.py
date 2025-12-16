from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("motry", "0002_favoritevehicle"),
    ]

    operations = [
        migrations.AddField(
            model_name="vehicleimage",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="vehicles/%Y/%m/"),
        ),
        migrations.AlterField(
            model_name="vehicleimage",
            name="image_url",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
