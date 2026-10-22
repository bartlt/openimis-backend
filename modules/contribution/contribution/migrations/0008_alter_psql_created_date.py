from django.db import migrations, models
from django.conf import settings

from datetime import datetime

class Migration(migrations.Migration):
    dependencies = [
        ('contribution', '0007_add_missing_fields_not_mssql'),
    ]
    operations = [
            migrations.AlterField(
                model_name='premium',
                name='created_date',
                field=models.DateTimeField(db_column='CreatedDate', default=datetime.now),
            ) 
    ]
        
