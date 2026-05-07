# Odoo 19 ↔ TallyPrime Integration — Project Handover Notes

This file captures the current understanding, completed work, decisions, and next-phase plan before archiving the current branch and continuing from a new branch.

## 1) Current project understanding

We are building an **Odoo 19 ↔ TallyPrime integration** for both **Odoo Community** and **Odoo Enterprise**.

The agreed implementation direction is:

```text
Odoo 19 → Odoo tally_bridge Queue/API → Windows Local Tally Agent → TallyPrime XML HTTP Server
```

Important design decisions:
- Start with **one-way sync only**: Odoo → Tally.
- Do **not** expose TallyPrime directly to the internet.
- Use a **local Windows agent** on the Tally machine/network to push data to `http://localhost:9000`.
- Use queue-based async processing in Odoo.
- Use deterministic idempotency keys (`external_guid`) to avoid duplicates.
- Deliver work phase by phase and archive stable milestones before proceeding.

## 2) What is completed in this branch

### Phase 1A — Odoo Bridge Foundation

Status: **Completed / ready to archive after local validation**.

Completed items:
- Created installable Odoo addon: `tally_bridge`.
- Confirmed addon target: Odoo 19 Community and Enterprise.
- Added base module metadata and initialization files.
- Added Odoo models:
  - `tally.config`
  - `tally.mapping`
  - `tally.sync.queue`
- Added queue states:
  - `draft`
  - `pending`
  - `processing`
  - `done`
  - `failed`
  - `dead`
- Added API endpoints for the local agent:
  - `GET /tally/pending`
  - `POST /tally/result`
- Added token-based API validation using the `X-API-Token` request header.
- Added Tally Bridge user groups:
  - Tally Bridge User
  - Tally Bridge Manager
- Added Odoo user access-rights category so the groups appear on the user form.
- Added model access rules.
- Added Odoo menus:
  - Tally Bridge
  - Configuration
  - Operations
  - Configurations
  - Mappings
  - Sync Queue
- Added Odoo 19-compatible list views using `<list>` instead of deprecated `<tree>` tags.
- Added retry cron baseline for failed queue records.
- Added queue sequence support for readable queue references.
- Fixed Odoo 19 installation issues found during testing:
  - Removed unsupported `ir.cron.numbercall` field.
  - Replaced deprecated tree views with Odoo 19 list views.
  - Added group category so roles appear in user access rights.
- Updated the README with architecture, runbook, phase roadmap, archive checklist, and next steps.

### Phase 1B — Customer/Vendor Queue Hooks

Status: **Started / available in this branch but can also be continued from a new branch if desired**.

Completed/started items:
- Added `res.partner` hooks for customer/vendor create/update events.
- Added partner payload preparation for the queue.
- Added reusable `tally.sync.queue.enqueue_record()` helper.
- Existing partner queue jobs are refreshed instead of duplicated using `external_guid = res.partner:<id>`.
- Phase 1B does **not** require live Tally credentials because it only creates Odoo-side queue jobs.

## 3) What is not completed yet

The following items are still pending and should be handled in new phase branches:

- Windows Local Tally Agent.
- Tally XML conversion logic.
- Real posting to TallyPrime XML HTTP endpoint.
- Ledger and tax sync.
- Sales invoice sync.
- Purchase bill sync.
- Payment sync.
- Credit note sync.
- Debit note sync.
- Stronger retry/dead-letter handling.
- Reconciliation reports.
- Production packaging and deployment automation.

## 4) Local Tally Agent understanding

The local agent is required to complete actual Odoo → Tally posting.

Recommended platform:
- Windows machine where TallyPrime is installed/running.

Recommended first implementation:
- Python polling worker first.
- Package as `.exe` later.
- Convert to Windows Service after the logic is stable.

Agent responsibilities:
1. Read config:
   - Odoo base URL
   - Odoo API token
   - Tally URL, usually `http://localhost:9000`
   - Poll interval
   - Batch limit
2. Poll Odoo API: `GET /tally/pending`.
3. Convert Odoo JSON payload to Tally XML.
4. Post XML to TallyPrime.
5. Send result back to Odoo using `POST /tally/result`.
6. Log success/failure for troubleshooting.

Important note:
- Tally usually does not need normal API username/password credentials for XML HTTP posting.
- TallyPrime must be running, the correct company should be open, and the XML/HTTP interface must be enabled and reachable.

## 5) Complete project phase plan

### Phase 1A — Odoo Bridge Foundation

Archive baseline containing:
- Module installability.
- Configuration/mapping/queue models.
- Menus/access rights.
- API endpoint foundation.
- README/runbook.

### Phase 1B — Customer/Vendor Master Queue Hooks

Goal:
- Queue customer/vendor master data from Odoo.

Deliverables:
- Partner create/update hooks.
- Customer/vendor queue payloads.
- Queue validation from Odoo UI/API.

Tally credentials:
- Not required.

### Phase 1C — Windows Local Tally Agent MVP

Goal:
- First end-to-end Odoo queue → TallyPrime push.

Deliverables:
- Agent config.
- Odoo API client.
- Tally XML HTTP client.
- Customer/vendor ledger XML transformer.
- Polling loop.
- Result callback.
- Logs.

Tally access:
- Required for real end-to-end validation.

### Phase 1D — Ledger and Tax Master Sync

Goal:
- Sync required accounting masters before transaction sync.

Deliverables:
- Ledger queue hooks.
- Tax queue hooks.
- Tally XML for ledgers/taxes.
- Mapping validation.

### Phase 1E — Invoice and Bill Sync

Goal:
- Sync posted accounting documents as Tally vouchers.

Deliverables:
- Sales invoice sync.
- Purchase bill sync.
- Credit note sync.
- Debit note sync.
- Voucher XML generation.

### Phase 1F — Payment Sync

Goal:
- Sync customer/vendor payments.

Deliverables:
- Customer payment sync.
- Vendor payment sync.
- Bank/cash ledger mapping.
- Payment voucher XML generation.

### Phase 1G — Reliability, Reconciliation, and UAT

Goal:
- Make the one-way sync production-ready.

Deliverables:
- Retry threshold logic.
- Dead-letter handling.
- Manual reprocess actions.
- Reconciliation reports.
- Logging/monitoring.
- UAT checklist.

### Phase 2 — Optional Advanced / Two-Way Sync

Possible future scope:
- Tally reference import.
- Reconciliation import.
- Two-way sync.
- Multi-company routing.
- Advanced conflict handling.

## 6) Recommended branch/archive plan

Recommended action now:
1. Archive the current branch as **Phase 1A foundation** after validating the checklist.
2. Create a new branch for the next milestone.

Suggested branch names:
- `phase_1b_customer_vendor_queue_hooks`
- `phase_1c_windows_tally_agent`
- `phase_1d_ledger_tax_sync`
- `phase_1e_invoice_bill_sync`
- `phase_1f_payment_sync`
- `phase_1g_reliability_uat`

Suggested next branch if continuing with the Windows agent:

```text
phase_1c_windows_tally_agent
```

Suggested next branch if continuing Odoo-side master hooks first:

```text
phase_1b_customer_vendor_queue_hooks
```

## 7) Phase 1A archive checklist

Before archiving this branch, verify in Odoo:

- App installs/upgrades without traceback.
- Tally Bridge groups are visible on user access rights.
- User can be assigned Tally Bridge Manager.
- Tally Bridge menu is visible.
- Configurations menu opens.
- Mappings menu opens.
- Sync Queue menu opens.
- A configuration record can be created.
- A mapping record can be created.
- README and this handover file are committed.

## 8) Immediate next recommendation

If your goal is to prove real sync into Tally, the next practical milestone should be:

```text
Phase 1C — Windows Local Tally Agent MVP
```

If your goal is to complete Odoo-side queue generation first, continue with:

```text
Phase 1B — Customer/Vendor Master Queue Hooks
```

Recommended order:
1. Archive current branch as Phase 1A.
2. Start new branch for Phase 1C Windows agent MVP if TallyPrime test access is available.
3. Otherwise, continue Phase 1B and complete Odoo-side master queue hooks first.
