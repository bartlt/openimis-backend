from datetime import date
from unittest.mock import MagicMock

from core.service_signals import ServiceSignalBindType
from core.signals import REGISTERED_SERVICE_SIGNALS
from invoice.services import InvoiceService
from invoice.tests import DEFAULT_TEST_INVOICE_PAYLOAD
from invoice.tests.gql.base import InvoiceGQLTestCase


class InvoiceGQLTest(InvoiceGQLTestCase):

    create_invoice_mutation = '''
mutation {
  generateInvoicesForTimePeriod(input: {dateFrom: "2021-01-01", dateTo:"2021-10-01"}){
    internalId
    clientMutationId
  }
}    
'''

    search_for_invoice_query = F'''
query {{ 
	invoice(
        code_Iexact:"{DEFAULT_TEST_INVOICE_PAYLOAD['code']}",
        subjectTypeFilter: "contract",
        thirdpartyTypeFilter: "insuree"
    ){{
    edges {{
      node {{
        isDeleted,
        code,
        codeTp,
        codeExt,
        subjectId,
        subjectType,
        thirdpartyId,
        thirdpartyType,
      }}
    }}
  }}
}}
'''

    def test_mutation_invoice_generate_for_time_frame(self):
        signal_receiver_mock = MagicMock(return_value='123')
        date_from = date(2021, 1, 1)
        date_to = date(2021, 10, 1)
        self.setup_test_signal(signal_receiver_mock)
        _expected_call_args = {
            'signal': REGISTERED_SERVICE_SIGNALS['invoice_creation_from_calculation'].after_service_signal,
            'sender': InvoiceService,
            'cls_': InvoiceService,
            'data': [(), {'user': self.user, 'from_date': date_from, 'to_date': date_to}],
            'context': None,
            'result': None
        }
        mutation = self.create_invoice_mutation
        self.graph_client.execute(mutation, context=self.user_context.get_request())
        signal_receiver_mock.assert_called_once_with(**_expected_call_args)

    def test_fetch_invoice_query(self):
        output = self.graph_client.execute(self.search_for_invoice_query, context=self.user_context.get_request())
        expected = {
            'data': {
                'invoice': {
                    'edges': [
                        {'node': {
                            'code': F'{DEFAULT_TEST_INVOICE_PAYLOAD["code"]}',
                            'codeExt': F'{DEFAULT_TEST_INVOICE_PAYLOAD["code_ext"]}',
                            'codeTp': F'{DEFAULT_TEST_INVOICE_PAYLOAD["code_tp"]}',
                            'isDeleted': False,
                            'thirdpartyId': F'{self.invoice.thirdparty.id}',
                            'thirdpartyType': self.invoice.thirdparty_type.id,
                            'subjectId': F'{self.invoice.subject.id}',
                            'subjectType': self.invoice.subject_type.id
                        }}
                    ]
                }
            }
        }

        self.assertEqual(output, expected)

    def setup_test_signal(self, receiver_mock):
        """
        Mutation doesn't provide logic for generating invoices, just invokes signal.
        """
        from core.signals import bind_service_signal
        bind_service_signal(
            'invoice_creation_from_calculation',
            receiver_mock,
            bind_type=ServiceSignalBindType.AFTER
        )