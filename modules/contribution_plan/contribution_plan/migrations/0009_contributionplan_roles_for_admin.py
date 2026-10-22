import logging

from django.db import migrations

from core.utils import insert_role_right_for_system

logger = logging.getLogger(__name__)


def add_rights(apps, schema_editor):
    insert_role_right_for_system(64, 151101, apps)  # Contribution plan and bundle
    insert_role_right_for_system(64, 151102, apps)  # update
    insert_role_right_for_system(64, 151103, apps)  # delete
    insert_role_right_for_system(64, 151104, apps)  # update
    insert_role_right_for_system(64, 151106, apps)  # update
    insert_role_right_for_system(64, 151201, apps)  # Contribution plan
    insert_role_right_for_system(64, 151202, apps)  # Contribution plan
    insert_role_right_for_system(64, 151203, apps)  # Contribution plan
    insert_role_right_for_system(64, 151204, apps)  # Contribution plan
    insert_role_right_for_system(64, 151206, apps)  # Contribution plan


class Migration(migrations.Migration):
    dependencies = [
        ('contribution_plan', '0008_historicalpaymentplan_paymentplan')
    ]

    operations = [
        migrations.RunPython(add_rights),
    ]
