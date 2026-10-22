import re

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q

from invoice.models import (
    DetailPaymentInvoice,
    Invoice,
    InvoiceLineItem,
    Bill,
    BillItem
)

camel_pat = re.compile(r'([A-Z])')
under_pat = re.compile(r'_([a-z])')


def camel_to_underscore(name):
    return camel_pat.sub(lambda x: '_' + x.group(1).lower(), name)


def underscore_to_camel(name):
    return under_pat.sub(lambda x: x.group(1).upper(), name)


def resolve_payment_details(payment_invoice):
    invoice_list = _retrieve_list_of_invoices_bills(payment_invoice, Invoice)
    invoice_line_item_list = _retrieve_list_of_invoices_bills(payment_invoice, InvoiceLineItem)
    invoices = Invoice.objects.filter(Q(id__in=invoice_list) | Q(line_items__id__in=invoice_line_item_list))
    bill_list = _retrieve_list_of_invoices_bills(payment_invoice, Bill)
    bill_line_item_list = _retrieve_list_of_invoices_bills(payment_invoice, BillItem)
    bills = Bill.objects.filter(Q(id__in=bill_list) | Q(line_items_bill__id__in=bill_line_item_list))
    return invoices, bills


def _retrieve_list_of_invoices_bills(payment_invoice, model_type):
    return list(DetailPaymentInvoice.objects.filter(
        payment=payment_invoice,
        subject_type=ContentType.objects.get_for_model(model_type).id
    ).values_list('subject_id', flat=True))
