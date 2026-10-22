from django.db import migrations, models

from core.datetimes.ad_datetime import datetime


class Migration(migrations.Migration):
    dependencies = [
        ('contribution', '0006_add_source_field_to_contribution'),
    ]
    #this migration was useless, better remove it and correct in next migration
    operations = [
    ]
