from datetime import date

from django.contrib.contenttypes.models import ContentType

from contract.tests.helpers import create_test_contract
from policyholder.tests.helpers import create_test_policy_holder
from insuree.test_helpers import create_test_insuree
from core.test_helpers import LogInHelper

from invoice.models import Invoice

DEFAULT_TEST_INVOICE_PAYLOAD = {
    'subject_type': 'contract',
    'subject_id': None,
    'thirdparty_type': 'insuree',
    'thirdparty_id': None,
    'code': 'INVOICE_CODE',
    'code_tp': 'INVOICE_CODE_TP',
    'code_ext': 'INVOICE_CODE_EXT',
    'date_due': date(2021, 9, 13),
    'date_invoice': date(2021, 9, 11),
    'date_payed': date(2021, 9, 12),
    'amount_discount': 20.1,
    'amount_net': 20.1,
    'tax_analysis': {'lines': [{'code': 'c', 'label': 'l', 'base': '0.1', 'amount': '2.01'}], 'total': '2.01'},
    'amount_total': 20.1,
    'status': 0,  # Draft
    'note': 'NOTE',
    'terms': 'TERMS',
    'payment_reference': 'payment reference'
}


def __get_or_create_user():
    return LogInHelper().get_or_create_user_api(username='admin_invoice')


def create_test_invoice(subject=None, thirdparty=None, user=None, **custom_props):
    subject = subject or __create_test_subject()
    thirdparty = thirdparty or __create_test_thirdparty()
    payload = DEFAULT_TEST_INVOICE_PAYLOAD.copy()
    payload['subject'] = subject
    payload['subject_type'] = ContentType.objects.get_for_model(subject)
    payload['thirdparty'] = thirdparty
    payload['thirdparty_type'] = ContentType.objects.get_for_model(thirdparty)
    payload.update(**custom_props)

    Invoice.objects.filter(code=payload['code']).delete()

    user = user or __get_or_create_user()
    invoice = Invoice(**payload)
    invoice.save(username=user.username)

    return invoice


def __create_test_subject():
    policy_holder = create_test_policy_holder()
    return create_test_contract(policy_holder)


def __create_test_thirdparty():
    return create_test_insuree(with_family=False)
