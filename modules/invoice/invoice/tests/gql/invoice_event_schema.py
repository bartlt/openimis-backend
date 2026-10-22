import uuid

from core.models import MutationLog
from invoice.models import InvoiceEventMutation, InvoiceEvent
from invoice.tests.gql.base import InvoiceGQLTestCase




class InvoiceEventGQLTest(InvoiceGQLTestCase):


    search_for_message = '''
    query {{
  invoiceEvent(message_Istartswith: "{message_content}") {{
    edges {{
      node {{
        message
      }}
    }}
  }}
}}
'''

    create_mutation_str = '''  
mutation {{
  createInvoiceEventMessage(input:{{invoiceId: "{invoice_id}", message:"Some message with type", eventType: 0, clientMutationId: "{mutation_id}"}}) {{
    internalId, 
    clientMutationId
  }}
}}
'''

    def test_fetch_invoice_query(self):
        mutation_client_id = str(uuid.uuid4())
        mutation = self.create_mutation_str.format(invoice_id=self.invoice.id, mutation_id=mutation_client_id)
        self.graph_client.execute(mutation, context=self.user_context.get_request())

        output = self.graph_client.execute(
            self.search_for_message.format(message_content="Some message with"), context=self.user_context.get_request()
        )

        expected = \
            {'data': {
                'invoiceEvent': {
                    'edges': [
                        {'node': {
                            'message': 'Some message with type'
        }}]}}}
        self.assertEqual(output, expected)

    def test_create_payment_mutation(self):
        mutation_client_id = str(uuid.uuid4())
        mutation = self.create_mutation_str.format(invoice_id=self.invoice.id, mutation_id=mutation_client_id)
        self.graph_client.execute(mutation, context=self.user_context.get_request())
        mutation_log = MutationLog.objects.filter(client_mutation_id=mutation_client_id).first()
        obj: InvoiceEvent = InvoiceEventMutation.objects.get(mutation_id=mutation_log.id).invoice_event
        self.assertEqual(obj.invoice, self.invoice)
        self.assertEqual(obj.message, "Some message with type")
        self.assertEqual(obj.event_type, InvoiceEvent.EventType.MESSAGE)
