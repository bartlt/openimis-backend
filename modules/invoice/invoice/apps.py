import logging

from django.apps import AppConfig
from core.utils import ConfigUtilMixin

MODULE_NAME = 'invoice'

DEFAULT_CONFIG = {
    "default_currency_code": "USD",
    "gql_invoice_search_perms": ["155101"],
    "gql_invoice_create_perms": ["155102"],
    "gql_invoice_update_perms": ["155103"],
    "gql_invoice_delete_perms": ["155104"],
    "gql_invoice_amend_perms": ["155109"],

    "gql_invoice_payment_search_perms": ["155201"],
    "gql_invoice_payment_create_perms": ["155202"],
    "gql_invoice_payment_update_perms": ["155203"],
    "gql_invoice_payment_delete_perms": ["155204"],
    "gql_invoice_payment_refund_perms": ["155206"],

    "gql_invoice_event_search_perms": ["155301"],
    "gql_invoice_event_create_perms": ["155302"],
    "gql_invoice_event_update_perms": ["155303"],
    "gql_invoice_event_delete_perms": ["155304"],
    "gql_invoice_event_create_message_perms": ["155306"],
    "gql_invoice_event_delete_my_message_perms": ["155307"],
    "gql_invoice_event_delete_all_message_perms": ["155308"],

    "gql_bill_search_perms": ["156101"],
    "gql_bill_create_perms": ["156102"],
    "gql_bill_update_perms": ["156103"],
    "gql_bill_delete_perms": ["156104"],
    "gql_bill_amend_perms": ["156109"],

    "gql_bill_payment_search_perms": ["156201"],
    "gql_bill_payment_create_perms": ["156202"],
    "gql_bill_payment_update_perms": ["156203"],
    "gql_bill_payment_delete_perms": ["156204"],
    "gql_bill_payment_refund_perms": ["156206"],

    "gql_bill_event_search_perms": ["156301"],
    "gql_bill_event_create_perms": ["156302"],
    "gql_bill_event_update_perms": ["156303"],
    "gql_bill_event_delete_perms": ["156304"],
    "gql_bill_event_create_message_perms": ["156306"],
    "gql_bill_event_delete_my_message_perms": ["156307"],
    "gql_bill_event_delete_all_message_perms": ["156308"],

    # Functions of type Callable[[QuerySet, User], QuerySet], to be used as custom user filters for bills and invoices
    # To be specified as "module_name.submodule.function_name"
    "bill_user_filter_function": None,
    "invoice_user_filter_function": None,
    "bill_code_pattern": "BIL-[YY]-[SEQ:10]",
}

logger = logging.getLogger(__name__)


class InvoiceConfig(AppConfig, ConfigUtilMixin):
    name = MODULE_NAME

    default_currency_code = None
    gql_invoice_search_perms = None
    gql_invoice_create_perms = None
    gql_invoice_update_perms = None
    gql_invoice_delete_perms = None
    gql_invoice_amend_perms = None
    gql_invoice_payment_search_perms = None
    gql_invoice_payment_create_perms = None
    gql_invoice_payment_update_perms = None
    gql_invoice_payment_delete_perms = None
    gql_invoice_payment_refund_perms = None
    gql_invoice_event_search_perms = None
    gql_invoice_event_create_perms = None
    gql_invoice_event_update_perms = None
    gql_invoice_event_delete_perms = None
    gql_invoice_event_create_message_perms = None
    gql_invoice_event_delete_my_message_perms = None
    gql_invoice_event_delete_all_message_perms = None
    gql_bill_search_perms = None
    gql_bill_create_perms = None
    gql_bill_update_perms = None
    gql_bill_delete_perms = None
    gql_bill_amend_perms = None
    gql_bill_payment_search_perms = None
    gql_bill_payment_create_perms = None
    gql_bill_payment_update_perms = None
    gql_bill_payment_delete_perms = None
    gql_bill_payment_refund_perms = None
    gql_bill_event_search_perms = None
    gql_bill_event_create_perms = None
    gql_bill_event_update_perms = None
    gql_bill_event_delete_perms = None
    gql_bill_event_create_message_perms = None
    gql_bill_event_delete_my_message_perms = None
    gql_bill_event_delete_all_message_perms = None

    bill_user_filter = None
    invoice_user_filter = None
    bill_code_pattern = None
    bill_trigger_synced = False

    def ready(self):
        from core.models import ModuleConfiguration
        cfg = ModuleConfiguration.get_or_default(MODULE_NAME, DEFAULT_CONFIG)
        self._load_config_fields(cfg)
        if cfg['bill_user_filter_function']:
            self._load_config_function('bill_user_filter', cfg['bill_user_filter_function'])
        if cfg['invoice_user_filter_function']:
            self._load_config_function('invoice_user_filter', cfg['invoice_user_filter_function'])
        self._sync_bill_trigger()
        self._connect_migrate_signal()
        self._connect_config_signal()

    def _sync_bill_trigger(self):
        try:
            from invoice.models import Bill
            from invoice.trigger_sync import sync_trigger
            sync_trigger(
                model=Bill,
                sequence_name='bill_code_seq',
                trigger_name='bill_code_trigger',
                code_column='Code',
                pattern=self.bill_code_pattern or DEFAULT_CONFIG['bill_code_pattern'],
                pg_function_name='set_bill_code',
            )
            InvoiceConfig.bill_trigger_synced = True
        except Exception as e:
            InvoiceConfig.bill_trigger_synced = False
            logger.error(f"Bill trigger sync failed: {e}", exc_info=True)

    def _connect_migrate_signal(self):
        # ready() runs before migrations, so on a fresh database the table the trigger
        # attaches to does not exist yet. Re-sync once migrations have created it.
        from django.db.models.signals import post_migrate
        post_migrate.connect(
            self._on_post_migrate, sender=self,
            dispatch_uid='invoice.bill_code_trigger_post_migrate',
        )

    @staticmethod
    def _on_post_migrate(sender, **kwargs):
        sender._sync_bill_trigger()

    def _connect_config_signal(self):
        from django.db.models.signals import post_save
        from core.models import ModuleConfiguration
        post_save.connect(
            self._on_config_change, sender=ModuleConfiguration,
            dispatch_uid='invoice.bill_code_trigger_sync',
        )

    @staticmethod
    def _on_config_change(sender, instance, **kwargs):
        import json
        if instance.module != MODULE_NAME or instance.layer != 'be':
            return
        try:
            cfg = json.loads(instance.config) if isinstance(instance.config, str) else instance.config
            pattern = cfg.get('bill_code_pattern') or DEFAULT_CONFIG['bill_code_pattern']
            from invoice.models import Bill
            from invoice.trigger_sync import sync_trigger, validate_pattern
            validate_pattern(pattern)
            InvoiceConfig.bill_code_pattern = pattern
            sync_trigger(
                model=Bill,
                sequence_name='bill_code_seq',
                trigger_name='bill_code_trigger',
                code_column='Code',
                pattern=pattern,
                pg_function_name='set_bill_code',
            )
            InvoiceConfig.bill_trigger_synced = True
            logger.info(f"Bill trigger updated after config change (pattern: {pattern})")
        except Exception as e:
            InvoiceConfig.bill_trigger_synced = False
            logger.error(f"Failed to sync bill trigger after config change: {e}", exc_info=True)
