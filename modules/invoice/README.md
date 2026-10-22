# openimis-be-invoice_py

OpenIMIS backend module for invoices, bills, and payments.

## Bill Code Auto-Generation

`Bill.code` is auto-assigned by a database trigger and sequence when `code` is `NULL` or empty. Explicitly supplied codes are preserved.

### Default format

```
BIL-YY-XXXXXXXXXX
```

- `YY` — two-digit year (e.g. `26` for 2026)
- `XXXXXXXXXX` — zero-padded 10-digit sequence number

Example: `BIL-26-0000000042`

### Custom code patterns

The code format is configurable via `ModuleConfiguration` (DB or `openimis.json`):

```json
{
  "bill_code_pattern": "CUSTOM-[YYYY][MM]-[SEQ:8]"
}
```

Available tokens (free positioning):

| Token | Description | Example output |
|-------|-------------|----------------|
| `[SEQ:N]` | Zero-padded sequence number, N digits | `00000042` |
| `[SEQ]` | Sequence number, no padding | `42` |
| `[YY]` | 2-digit year | `26` |
| `[YYYY]` | 4-digit year | `2026` |
| `[MM]` | 2-digit month | `03` |

Pattern examples:
- `BIL-[YY]-[SEQ:10]` → `BIL-26-0000000042` (default)
- `INV/[YYYY]/[SEQ:6]` → `INV/2026/000042`
- `CUSTOM-[YYYY][MM]-[SEQ:8]` → `CUSTOM-202603-00000042`
- `[SEQ:12]` → `000000000042`

`[SEQ]` or `[SEQ:N]` is required (exactly once). All other text is literal.

### How it works

| Database | Mechanism |
|----------|-----------|
| PostgreSQL | `BEFORE INSERT` trigger on `tblBill`; calls `nextval('bill_code_seq')` |
| MSSQL | `INSTEAD OF INSERT` trigger on `tblBill`; uses `NEXT VALUE FOR bill_code_seq` |

On first apply, the migration advances the sequence past the current maximum to avoid collisions.

### Trigger auto-sync

The MSSQL trigger lists every column explicitly. To keep it in sync with schema and config changes, a trigger sync service runs automatically:

1. **On startup** — `InvoiceConfig.ready()` compares the DB trigger against the current model columns and code pattern. Recreates if different.
2. **On config change** — A `post_save` signal on `ModuleConfiguration` re-syncs when `bill_code_pattern` is updated via the API or admin UI.
3. **Manual** — Management command for explicit sync without server restart:

```bash
python manage.py sync_code_triggers                    # sync all (bill + benefit)
python manage.py sync_code_triggers --module invoice   # sync bill trigger only
python manage.py sync_code_triggers --module payroll   # sync benefit trigger only
python manage.py sync_code_triggers --dry-run          # show what would change
```

The sync compares structured components (column set, code pattern expression) rather than raw SQL text, so formatting differences don't cause false updates.

### Migration

`invoice/migrations/0014_bill_code_sequence.py` — uses `RunPython` with vendor detection. Fails fast on unsupported DB vendors.

To reverse: `python manage.py migrate invoice 0013`

### Bulk creation

`BillService.bulk_create_bills()` and `bulk_create_bill_items()` use `bulk_create_with_history` from `django-simple-history` for performance with audit trail. After bulk insert, DB-assigned codes are re-fetched and patched into both the in-memory instances and their history records. Queries are chunked to stay under MSSQL's parameter limit.
