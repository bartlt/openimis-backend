from decimal import Decimal

from invoice.tests.gql.base import InvoiceGQLTestCase
from invoice.tests.helpers import DEFAULT_TEST_INVOICE_LINE_ITEM_PAYLOAD, DEFAULT_TEST_INVOICE_PAYLOAD


class InvoiceLineItemGQLTest(InvoiceGQLTestCase):

    search_for_invoice_query = F'''
query {{ 
	invoiceLineItem(invoice_Code:"{DEFAULT_TEST_INVOICE_PAYLOAD['code']}", 
	amountTotal:"{DEFAULT_TEST_INVOICE_LINE_ITEM_PAYLOAD['amount_total']}"){{
    edges {{
      node {{
        isDeleted,
        code,
        amountNet,
        amountTotal,
        taxRate,
        lineId,
        lineType
      }}
    }}
  }}
}}
'''

    def test_fetch_invoice_query(self):
        output = self.graph_client.execute(self.search_for_invoice_query, context=self.user_context.get_request())
        expected = \
            {'data': {
                'invoiceLineItem': {
                    'edges': [
                        {'node': {
                            'isDeleted': False,
                            'code': 'LineItem1',
                            'amountNet': "89.50",
                            'amountTotal': "91.50",
                            'taxRate': None,
                            'lineId': F'{self.invoice_line_item.line.id}',
                            'lineType': self.invoice_line_item.line_type.id
                        }}]}}}
        self.assertEqual(output, expected)
