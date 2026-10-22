from django.contrib.contenttypes.models import ContentType
from policy.test_helpers import create_test_policy
from product.models import Product
from product.test_helpers import create_test_product

from insuree.test_helpers import create_test_insuree
from core.forms import User

from invoice.models import Bill, BillItem
from invoice.tests.helpers import create_test_bill
from invoice.tests.helpers.default_test_data import DEFAULT_TEST_BILL_LINE_ITEM_PAYLOAD


def create_test_bill_line_item(bill=None, line_item=None, user=None, **custom_props):
    payload = DEFAULT_TEST_BILL_LINE_ITEM_PAYLOAD.copy()
    payload['bill'] = bill or create_test_bill()
    payload['line'] = line_item or __create_test_policy()
    payload.update(**custom_props)

    BillItem.objects.filter(code=payload['code']).delete()

    user = user or __get_or_create_user()
    invoice = BillItem(**payload)
    invoice.save(username=user.username)

    return invoice


def __get_or_create_user():
    user = User.objects.filter(username='admin_invoice').first()
    if not user:
        user = User.objects.create_superuser(username='admin_invoice', password='S\/pe®Pąßw0rd™')
    return user


def __get_or_create_product():
    product = Product.objects.filter(code='InvLine').first()
    if not product:
        product = create_test_product("InvLine", custom_props={"insurance_period": 12})
    return product


def __create_test_policy():
    insuree = create_test_insuree(with_family=True)
    product = __get_or_create_product()
    return create_test_policy(
        product=product,
        insuree=insuree
    )
