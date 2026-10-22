from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0014_bill_code_sequence'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='code',
            field=models.CharField(blank=True, db_column='Code', default='', max_length=255),
        ),
    ]
