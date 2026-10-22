import uuid

from unittest import skip

from core.models import MutationLog
from invoice.models import InvoicePayment, InvoicePaymentMutation
from invoice.tests.gql.base import InvoiceGQLTestCase
from invoice.tests.helpers import DEFAULT_TEST_INVOICE_PAYMENT_PAYLOAD, DEFAULT_TEST_INVOICE_PAYLOAD


class InvoicePaymentGQLTest(InvoiceGQLTestCase):

    search_for_invoice_payment_query = F'''
query {{ 
	invoicePayment(invoice_Code:"{DEFAULT_TEST_INVOICE_PAYLOAD['code']}", 
	amountPayed: {DEFAULT_TEST_INVOICE_PAYMENT_PAYLOAD['amount_payed']}){{
    edges {{
      node {{
        isDeleted,
        amountPayed,
        amountReceived,
        invoice {{
            code
        }},
        datePayment,
        status,
        fees
      }}
    }}
  }}
}}
'''

    create_mutation_str = '''  
mutation {{
  createInvoicePayment(input:{{status: 1, codeExt:"{payment_code}", codeTp:"gqlTp", codeReceipt:"gqlRec", 
  label:"gql label", invoiceId:"{invoice_id}", amountPayed: "10.0", fees: "10.0", amountReceived: "20.0", 
  datePayment:"2021-10-10", clientMutationId: "{mutation_id}"}}) {{
    internalId
    clientMutationId
  }}
}}
'''

    delete_mutation_str = '''  
mutation {{
  deleteInvoicePayment(input:{{uuids:["{payment_uuid}"], clientMutationId: "{mutation_id}"}}) {{
    internalId
    clientMutationId
  }}
}}
'''

    update_mutation_str = '''  
mutation {{
	updateInvoicePayment(input:{{id:"{payment_uuid}", codeExt:"updExt", clientMutationId: "{mutation_id}"}}){{
    internalId
    clientMutationId
  }}
}}
'''

    @skip("This is related to old payment approach model - depreceated")
    def test_fetch_invoice_query(self):
        output = self.graph_client.execute(self.search_for_invoice_payment_query,
                                           context=self.BaseTestContext(self.user))
        expected = \
            {'data': {
                'invoicePayment': {
                    'edges': [
                        {'node': {
                            'isDeleted': False,
                            'amountPayed': f"{DEFAULT_TEST_INVOICE_PAYMENT_PAYLOAD['amount_payed']}",
                            'amountReceived': f"{DEFAULT_TEST_INVOICE_PAYMENT_PAYLOAD['amount_received']}",
                            'invoice': {'code': F'{DEFAULT_TEST_INVOICE_PAYLOAD["code"]}'},
                            'datePayment': '2021-10-10',
                            'status': 'A_1',
                            'fees': f"{DEFAULT_TEST_INVOICE_PAYMENT_PAYLOAD['fees']}",
        }}]}}}
        self.assertEqual(output, expected)

    @skip("This is related to old payment approach model - depreceated")
    def test_create_payment_mutation(self):
        payment_code = "GQLCOD"
        mutation_client_id = str(uuid.uuid4())
        mutation = self.create_mutation_str.format(
            payment_code=payment_code, invoice_id=self.invoice.id, mutation_id=mutation_client_id
        )
        self.graph_client.execute(mutation, context=self.BaseTestContext(self.user))
        expected = InvoicePayment.objects.get(code_ext=payment_code)
        mutation_log = MutationLog.objects.filter(client_mutation_id=mutation_client_id).first()
        obj = InvoicePaymentMutation.objects.get(mutation_id=mutation_log.id).invoice_payment
        self.assertEqual(obj, expected)

    @skip("This is related to old payment approach model - depreceated")
    def test_delete_payment_mutation(self):
        payment_code = "GQLCOD"
        mutation_client_id = str(uuid.uuid4())
        mutation = self.create_mutation_str.format(
            payment_code=payment_code, invoice_id=self.invoice.id, mutation_id=mutation_client_id
        )
        self.graph_client.execute(mutation, context=self.BaseTestContext(self.user))
        expected = InvoicePayment.objects.get(code_ext=payment_code)
        mutation_client_id = str(uuid.uuid4())
        mutation = self.delete_mutation_str.format(payment_uuid=expected.id, mutation_id=mutation_client_id)
        self.graph_client.execute(mutation, context=self.BaseTestContext(self.user))
        # TODO: Currently deleted entries are not filtered by manager, only in GQL Query. Should we change this?
        payment = InvoicePayment.objects.filter(code_ext=payment_code).all()
        mutation_ = InvoicePaymentMutation.objects.filter(invoice_payment=payment[0]).all()
        self.assertEqual(len(payment), 1)
        self.assertTrue(payment[0].is_deleted)
        self.assertTrue(len(mutation_) == 2)

    @skip("This is related to old payment approach model - depreceated")
    def test_update_payment_mutation(self):
        payment_code = "GQLCOD"
        mutation_client_id = str(uuid.uuid4())
        mutation = self.create_mutation_str.format(
            payment_code=payment_code, invoice_id=self.invoice.id, mutation_id=mutation_client_id
        )
        self.graph_client.execute(mutation, context=self.BaseTestContext(self.user))

        created = InvoicePayment.objects.get(code_ext=payment_code)
        mutation_client_id = str(uuid.uuid4())
        mutation = self.update_mutation_str.format(payment_uuid=created.id, mutation_id=mutation_client_id)
        self.graph_client.execute(mutation, context=self.BaseTestContext(self.user))

        expected_code_ext = "updExt"
        mutation_log = MutationLog.objects.filter(client_mutation_id=mutation_client_id).first()
        obj: InvoicePayment = InvoicePaymentMutation.objects.get(mutation_id=mutation_log.id).invoice_payment
        self.assertEqual(obj.code_ext, expected_code_ext)
