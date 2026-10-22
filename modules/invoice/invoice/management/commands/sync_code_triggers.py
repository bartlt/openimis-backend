"""
Management command to sync DB code-generation triggers with current model schema and config.

Usage:
    python manage.py sync_code_triggers              # sync all
    python manage.py sync_code_triggers --module invoice   # sync bill trigger only
    python manage.py sync_code_triggers --module payroll   # sync benefit trigger only
    python manage.py sync_code_triggers --dry-run          # show what would change
"""
from django.core.management.base import BaseCommand

from invoice.trigger_sync import sync_trigger, DEFAULT_BILL_CODE_PATTERN, DEFAULT_BENEFIT_CODE_PATTERN


class Command(BaseCommand):
    help = 'Sync DB code-generation triggers with current model schema and config patterns'

    def add_arguments(self, parser):
        parser.add_argument(
            '--module', choices=['invoice', 'payroll'],
            help='Sync only the specified module trigger',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would change without applying',
        )

    def handle(self, *args, **options):
        module = options.get('module')
        dry_run = options.get('dry_run', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be applied\n'))

        results = []

        if module in (None, 'invoice'):
            results.append(('bill', self._sync_bill(dry_run)))

        if module in (None, 'payroll'):
            results.append(('benefit', self._sync_benefit(dry_run)))

        for name, updated in results:
            if updated is True:
                self.stdout.write(self.style.SUCCESS(f'  {name}: trigger {"would be " if dry_run else ""}updated'))
            elif updated is False:
                self.stdout.write(f'  {name}: already in sync')
            else:
                self.stdout.write(self.style.WARNING(f'  {name}: skipped (unsupported vendor or error)'))

    def _sync_bill(self, dry_run):
        try:
            from invoice.models import Bill
            from invoice.apps import InvoiceConfig
            pattern = InvoiceConfig.bill_code_pattern or DEFAULT_BILL_CODE_PATTERN
            self.stdout.write(f'Bill trigger (pattern: {pattern})')
            return sync_trigger(
                model=Bill,
                sequence_name='bill_code_seq',
                trigger_name='bill_code_trigger',
                code_column='Code',
                pattern=pattern,
                pg_function_name='set_bill_code',
                dry_run=dry_run,
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'  bill: error — {e}'))
            return None

    def _sync_benefit(self, dry_run):
        try:
            from payroll.models import BenefitConsumption
            from payroll.apps import PayrollConfig
            pattern = PayrollConfig.benefit_code_pattern or DEFAULT_BENEFIT_CODE_PATTERN
            self.stdout.write(f'Benefit trigger (pattern: {pattern})')
            return sync_trigger(
                model=BenefitConsumption,
                sequence_name='benefit_code_seq',
                trigger_name='benefit_code_trigger',
                code_column='code',
                pattern=pattern,
                pg_function_name='set_benefit_code',
                dry_run=dry_run,
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'  benefit: error — {e}'))
            return None
