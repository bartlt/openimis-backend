import uuid

from core.models import MutationLog
from invoice.models import (
    DetailPaymentInvoice,
    DetailPaymentInvoiceMutation,
    Invoice,
    InvoiceLineItem
)
from invoice.tests.gql.base import InvoiceGQLTestCase
from invoice.tests.helpers import (
    DEFAULT_TEST_PAYMENT_INVOICE_PAYLOAD,
    create_test_payment_invoice_without_details
)


class DetailPaymentInvoiceGQLTest(InvoiceGQLTestCase):
    search_for_detail_payment_invoice_query = F'''
query {{ 
	detailPaymentInvoice(payment_CodeTp_Iexact:"{DEFAULT_TEST_PAYMENT_INVOICE_PAYLOAD['code_tp']}"){{
    edges {{
      node {{
        isDeleted,
        amount,
        status,
        fees,
        subjectTypeName,
        subjectId
      }}
    }}
  }}
}}
'''

    create_mutation_str = '''  
mutation {{
  createDetailPaymentInvoice(input:{{status: 1, fees: "12.00", amount: "91.50", 
  paymentId: "{payment_uuid}", subjectType: "invoice", subjectId: "{subject_uuid}", 
  clientMutationId: "{mutation_id}"}}) {{
    internalId
    clientMutationId
  }}
}}
'''

    delete_mutation_str = '''  
mutation {{
  deleteDetailPaymentInvoice(input:{{uuids:["{payment_uuid}"], clientMutationId: "{mutation_id}"}}) {{
    internalId
    clientMutationId
  }}
}}
'''

    update_mutation_str = '''  
mutation {{
	updateDetailPaymentInvoice(input:{{id:"{detail_payment_uuid}", 
	  status: 1, fees: "12.00", amount: "91.50", 
      clientMutationId: "{mutation_id}"}}){{
    internalId
    clientMutationId
  }}
}}
'''

    def test_fetch_detail_payment_invoice_query(self):
        payment, invoice, invoice_item = create_test_payment_invoice_without_details()
        mutation_client_id = str(uuid.uuid4())
        mutation = self.create_mutation_str.format(
            payment_uuid=payment.id, subject_uuid=invoice.id, mutation_id=mutation_client_id
        )
        self.graph_client.execute(mutation, context=self.user_context.get_request())
        output = self.graph_client.execute(self.search_for_detail_payment_invoice_query,
                                           context=self.user_context.get_request())
        expected = \
            {'data': {
                'detailPaymentInvoice': {
                    'edges': [
                        {'node': {
                            'amount': '91.50',
                            'fees': '12.00',
                            'isDeleted': False,
                            'status': 'A_1',
                            'subjectId': f"{invoice.id}",
                            'subjectTypeName': "invoice",
                        }}]}}}
        self.assertEqual(output, expected)
        InvoiceLineItem.objects.filter(id=invoice_item.id).delete()
        Invoice.objects.filter(id=invoice.id).delete()

    def test_create_detail_payment_mutation(self):
        payment, invoice, invoice_item = create_test_payment_invoice_without_details()
        mutation_client_id = str(uuid.uuid4())
        mutation = self.create_mutation_str.format(
            payment_uuid=payment.id, subject_uuid=invoice.id, mutation_id=mutation_client_id
        )
        self.graph_client.execute(mutation, context=self.user_context.get_request())
        expected = DetailPaymentInvoice.objects.get(payment__id=payment.id)
        mutation_log = MutationLog.objects.filter(client_mutation_id=mutation_client_id).first()
        obj = DetailPaymentInvoiceMutation.objects.get(mutation_id=mutation_log.id).detail_payment_invoice
        self.assertEqual(obj, expected)
        InvoiceLineItem.objects.filter(id=invoice_item.id).delete()
        Invoice.objects.filter(id=invoice.id).delete()

    def test_delete_detail_payment_mutation(self):
        payment, invoice, invoice_item = create_test_payment_invoice_without_details()
        mutation_client_id = str(uuid.uuid4())
        mutation = self.create_mutation_str.format(
            payment_uuid=payment.id, subject_uuid=invoice.id, mutation_id=mutation_client_id
        )
        self.graph_client.execute(mutation, context=self.user_context.get_request())
        expected = DetailPaymentInvoice.objects.get(payment__id=payment.id)
        mutation_client_id = str(uuid.uuid4())
        mutation = self.delete_mutation_str.format(payment_uuid=expected.id, mutation_id=mutation_client_id)
        self.graph_client.execute(mutation, context=self.user_context.get_request())
        # TODO: Currently deleted entries are not filtered by manager, only in GQL Query. Should we change this?
        detail_payment = DetailPaymentInvoice.objects.filter(payment__id=payment.id).all()
        mutation_ = DetailPaymentInvoiceMutation.objects.filter(detail_payment_invoice=detail_payment[0]).all()
        self.assertEqual(len(detail_payment), 1)
        self.assertTrue(detail_payment[0].is_deleted)
        self.assertTrue(len(mutation_) == 2)
        InvoiceLineItem.objects.filter(id=invoice_item.id).delete()
        Invoice.objects.filter(id=invoice.id).delete()

    def test_update_detail_payment_mutation(self):
        payment, invoice, invoice_item = create_test_payment_invoice_without_details()
        mutation_client_id = str(uuid.uuid4())
        mutation = self.create_mutation_str.format(
            payment_uuid=payment.id, subject_uuid=invoice.id, mutation_id=mutation_client_id
        )
        self.graph_client.execute(mutation, context=self.user_context.get_request())

        created = DetailPaymentInvoice.objects.get(payment__id=payment.id)
        mutation_client_id = str(uuid.uuid4())
        mutation = self.update_mutation_str.format(detail_payment_uuid=created.id, mutation_id=mutation_client_id)
        self.graph_client.execute(mutation, context=self.user_context.get_request())

        expected_fees = "12.00"
        mutation_log = MutationLog.objects.filter(client_mutation_id=mutation_client_id).first()
        obj: DetailPaymentInvoice = DetailPaymentInvoiceMutation.objects.get(
            mutation_id=mutation_log.id).detail_payment_invoice
        self.assertEqual(str(obj.fees), str(expected_fees))
        InvoiceLineItem.objects.filter(id=invoice_item.id).delete()
        Invoice.objects.filter(id=invoice.id).delete()
