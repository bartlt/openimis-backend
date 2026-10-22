from django.db import migrations, models
from django.db.utils import ProgrammingError, OperationalError

def check_field_exists(apps, schema_editor, field_name):
    Premium = apps.get_model('contribution', 'Premium')
    db_alias = schema_editor.connection.alias
    
    try:
        Premium.objects.using(db_alias).values(field_name).first()
        return True
    except (ProgrammingError, OperationalError):
        return False

def add_field_if_not_exists(apps, schema_editor, field_name, field):
    if not check_field_exists(apps, schema_editor, field_name):
        schema_editor.add_field(
            model=apps.get_model('contribution', 'Premium'),
            field=field
        )

class Migration(migrations.Migration):

    dependencies = [
        ('contribution', '0005_alter_created_date'),
    ]

    operations = [
        migrations.RunPython(
            lambda apps, schema_editor: add_field_if_not_exists(
                apps, 
                schema_editor, 
                'source',
                models.CharField(db_column="Source", max_length=50, blank=True, null=True)
            ),
            reverse_code=migrations.RunPython.noop
        ),
        migrations.RunPython(
            lambda apps, schema_editor: add_field_if_not_exists(
                apps, 
                schema_editor, 
                'source_version',
                models.CharField(db_column="SourceVersion", max_length=15, blank=True, null=True)
            ),
            reverse_code=migrations.RunPython.noop
        ),
    ]