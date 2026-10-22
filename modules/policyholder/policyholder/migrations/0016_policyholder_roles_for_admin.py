import logging

from django.db import migrations

from core.utils import insert_role_right_for_system

logger = logging.getLogger(__name__)


def add_rights(apps, schema_editor):
    insert_role_right_for_system(64, 150101, apps)  # search
    insert_role_right_for_system(64, 150102, apps)  # create
    insert_role_right_for_system(64, 150103, apps)  # update
    insert_role_right_for_system(64, 150104, apps)  # delete

    insert_role_right_for_system(64, 150201, apps)  # search
    insert_role_right_for_system(64, 150202, apps)  # create
    insert_role_right_for_system(64, 150203, apps)  # update
    insert_role_right_for_system(64, 150204, apps)  # delete
    insert_role_right_for_system(64, 150206, apps)  # refund

    insert_role_right_for_system(64, 150301, apps)  # search
    insert_role_right_for_system(64, 150302, apps)  # create
    insert_role_right_for_system(64, 150303, apps)  # update
    insert_role_right_for_system(64, 150304, apps)  # delete
    insert_role_right_for_system(64, 150306, apps)  # message

    insert_role_right_for_system(64, 150401, apps)  # search
    insert_role_right_for_system(64, 150402, apps)  # create
    insert_role_right_for_system(64, 150403, apps)  # update
    insert_role_right_for_system(64, 150404, apps)  # delete
    insert_role_right_for_system(64, 150406, apps)  # message


class Migration(migrations.Migration):
    dependencies = [
        ('policyholder', '0015_auto_20210624_1243')
    ]

    operations = [
        migrations.RunPython(add_rights),
    ]
