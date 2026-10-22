from datetime import date

from django.contrib.contenttypes.models import ContentType

from contract.tests.helpers import create_test_contract
from policyholder.tests.helpers import create_test_policy_holder
from insuree.test_helpers import create_test_insuree
from core.forms import User

from invoice.models import Bill
from invoice.tests.helpers.default_test_data import DEFAULT_TEST_BILL_PAYLOAD


def __get_or_create_user():
    user = User.objects.filter(username='admin_invoice').first()
    if not user:
        user = User.objects.create_superuser(username='admin_invoice', password='S\/pe®Pąßw0rd™')
    return user


def create_test_bill(subject=None, thirdparty=None, user=None, **custom_props):
    subject = subject or __create_test_subject()
    thirdparty = thirdparty or __create_test_thirdparty()
    payload = DEFAULT_TEST_BILL_PAYLOAD.copy()
    payload['subject'] = subject
    payload['subject_type'] = ContentType.objects.get_for_model(subject)
    payload['thirdparty'] = thirdparty
    payload['thirdparty_type'] = ContentType.objects.get_for_model(thirdparty)
    payload.update(**custom_props)
    user = user or __get_or_create_user()

    if Bill.objects.filter(code=payload['code']).exists():
        b = Bill.objects.filter(code=payload['code']).first()
        b.payments_bill.all().delete()
        b.line_items_bill.all().delete()
        Bill.objects.filter(code=payload['code']).delete()

    bill = Bill(**payload)
    bill.save(username=user.username)

    return bill


def __create_test_subject():
    policy_holder = create_test_policy_holder()
    return create_test_contract(policy_holder)


def __create_test_thirdparty():
    return create_test_insuree(with_family=False)
