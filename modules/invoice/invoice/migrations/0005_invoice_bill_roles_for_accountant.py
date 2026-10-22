import logging

from django.db import migrations

from core.utils import insert_role_right_for_system

logger = logging.getLogger(__name__)


def add_rights(apps, schema_editor):
    insert_role_right_for_system(4, 155101, apps)  # Invoice search
    insert_role_right_for_system(4, 155102, apps)  # Invoice create
    insert_role_right_for_system(4, 155103, apps)  # Invoice update
    insert_role_right_for_system(4, 155104, apps)  # Invoice delete
    insert_role_right_for_system(4, 155109, apps)  # Invoice amend
    insert_role_right_for_system(4, 155201, apps)  # Invoice payment search
    insert_role_right_for_system(4, 155202, apps)  # Invoice payment create
    insert_role_right_for_system(4, 155203, apps)  # Invoice payment update
    insert_role_right_for_system(4, 155204, apps)  # Invoice payment delete
    insert_role_right_for_system(4, 155206, apps)  # Invoice payment refund
    insert_role_right_for_system(4, 155301, apps)  # Invoice Event search
    insert_role_right_for_system(4, 155302, apps)  # Invoice Event create
    insert_role_right_for_system(4, 155303, apps)  # Invoice Event update
    insert_role_right_for_system(4, 155304, apps)  # Invoice Event delete
    insert_role_right_for_system(4, 155306, apps)  # Invoice Event message
    insert_role_right_for_system(4, 155307, apps)  # Invoice Event delete my message
    insert_role_right_for_system(4, 155308, apps)  # Invoice Event delete all messages
    insert_role_right_for_system(4, 156101, apps)  # Bill search
    insert_role_right_for_system(4, 156102, apps)  # Bill create
    insert_role_right_for_system(4, 156103, apps)  # Bill update
    insert_role_right_for_system(4, 156104, apps)  # Bill delete
    insert_role_right_for_system(4, 156109, apps)  # Bill amend
    insert_role_right_for_system(4, 156201, apps)  # Bill Payment search
    insert_role_right_for_system(4, 156202, apps)  # Bill Payment create
    insert_role_right_for_system(4, 156203, apps)  # Bill Payment update
    insert_role_right_for_system(4, 156204, apps)  # Bill Payment delete
    insert_role_right_for_system(4, 156206, apps)  # Bill Payment refund
    insert_role_right_for_system(4, 156301, apps)  # Bill Event search
    insert_role_right_for_system(4, 156302, apps)  # Bill Event create
    insert_role_right_for_system(4, 156303, apps)  # Bill Event update
    insert_role_right_for_system(4, 156304, apps)  # Bill Event delete
    insert_role_right_for_system(4, 156306, apps)  # Bill Event create message
    insert_role_right_for_system(4, 156307, apps)  # Bill Event delete my message
    insert_role_right_for_system(4, 156308, apps)  # Bill Event delete all messages


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0004_invoice_bill_roles_for_admin')
    ]

    operations = [
        migrations.RunPython(add_rights),
    ]
