# Odoo 19 ↔ TallyPrime Integration (Technical Documentation)

This repository documents a production-oriented, **agent-driven integration** between **Odoo 19** (Enterprise/Community) and **TallyPrime** using Tally's local XML HTTP interface.

> **Current implementation direction:** Start with **one-way accounting sync (Odoo → Tally)** only.

---

## 1) Objective

Build a reliable bridge that exports accounting events from Odoo to TallyPrime without exposing Tally to the internet.

**High-level flow:**

`Odoo (Queue + API) → Local Tally Agent (FastAPI) → TallyPrime XML HTTP Server`

---

## 2) Architecture

### 2.1 Components

1. **Odoo Module: `tally_bridge`**
   - Captures accounting/business events.
   - Creates queue records for sync.
   - Exposes APIs for agent polling and result callbacks.

2. **Local Agent: Python FastAPI service**
   - Polls Odoo for pending events.
   - Converts Odoo JSON payloads to Tally XML envelopes.
   - Submits XML to TallyPrime (`http://localhost:9000`).
   - Reports success/failure back to Odoo.

3. **TallyPrime**
   - Accepts XML requests via local HTTP interface.
   - Creates/updates ledgers, vouchers, and other accounting entities.

### 2.2 Why Local Agent?

- Avoids direct cloud-to-local connectivity.
- Keeps Tally reachable only within local network.
- Enables transformation, retry, throttling, and observability in one control point.


## 2.3 Deployment Topology (Reference)

```text
+-------------------+        HTTPS API        +------------------------+
|   Odoo 19 Cloud   |  -------------------->  |   Local Tally Agent    |
| (Enterprise/Comm) |                         | (Python/FastAPI/Node)  |
+-------------------+  <--------------------  +-----------+------------+
        |                     Sync result                  |
        |                                                  |
        v                                                  v
+-------------------+                         +------------------------+
|  Odoo Accounting  |                         |     TallyPrime         |
|  + Custom Module  |                         | (localhost:9000 XML)   |
+-------------------+                         +------------------------+
```

Notes:
- Odoo can be cloud-hosted while TallyPrime remains on-prem/local.
- The local agent is the only component that talks to both Odoo APIs and Tally XML endpoint.
- Agent runtime can be Python/FastAPI (recommended) or Node.js, as long as API contract and idempotency guarantees are preserved.

---

## 3) Core Integration Principles

- **Queue-first asynchronous sync** for resilience.
- **Idempotent processing** for safe retries.
- **Deterministic ordering** when needed (e.g., master before transaction).
- **Least-privilege security** across APIs and hosts.
- **Auditability** through queue history and status callbacks.

---

## 4) Odoo Data Model (Planned)

- `tally.sync.queue` — outbound event queue with state machine.
- `tally.mapping` — Odoo↔Tally master/code mappings.
- `tally.config` — runtime config (token, endpoints, batch sizes, retry policy).

### 4.1 Suggested queue states

- `draft` → created but not ready
- `pending` → ready for agent pickup
- `processing` → currently locked by agent
- `done` → synced successfully
- `failed` → sync attempt failed
- `dead` → exceeded retry threshold (manual intervention)

---

## 5) API Contract (Odoo ↔ Agent)

### 5.1 `GET /tally/pending`
Returns pending events in small batches.

**Suggested query params:**
- `limit` (default 50)
- `entity` (optional filter)
- `company_id` (optional)

**Response (example):**

```json
{
  "items": [
    {
      "queue_id": 1024,
      "entity": "account.move",
      "operation": "create",
      "record_id": 5567,
      "external_guid": "account.move:5567",
      "payload": {"move_type": "out_invoice"},
      "attempt_count": 0,
      "created_at": "2026-04-30T09:10:00Z"
    }
  ]
}
```

### 5.2 `POST /tally/result`
Agent posts execution status per queue item.

**Request (example):**

```json
{
  "queue_id": 1024,
  "external_guid": "account.move:5567",
  "status": "done",
  "tally_ref": "VCH-000123",
  "message": "Voucher created",
  "raw_response": "optional-string-or-trace",
  "processed_at": "2026-04-30T09:10:05Z"
}
```

---

## 6) Idempotency Strategy

Use a stable external key:

`external_guid = odoo_model + ':' + record_id`

Examples:
- `res.partner:301`
- `account.move:5567`

On retry, the same key must be reused so duplicates are prevented both in Odoo queue logic and in Tally-side reference handling.

---

## 7) Security Model

- **Token auth** for Agent → Odoo API calls.
- **IP allowlisting** where possible.
- **No public exposure** of Tally endpoint.
- **Secrets outside code** (env vars or secure config store).
- **Signed/traceable logs** for troubleshooting and audits.

---

## 8) Tally XML Integration

### 8.1 Minimal XML snippet

```xml
<VOUCHER VCHTYPE="Sales">
  <DATE>YYYYMMDD</DATE>
</VOUCHER>
```

### 8.2 Transformation responsibility

Agent owns transformation:
- Odoo JSON → Tally XML tags
- date/amount/tax normalization
- party/ledger name mapping lookup

---

## 9) Supported Scope

### 9.1 Initial one-way scope (Phase 1)

Sync from **Odoo → Tally** for:
- Customers
- Vendors
- Ledgers
- Taxes
- Sales invoices
- Purchase bills
- Payments
- Credit notes
- Debit notes

### 9.2 Supported accounting modules (initial)
- Sales Invoice
- Purchase Invoice
- Payments
- Ledgers

---

## 10) Process Runbook

### Step 1 — Configure Odoo

- Install `tally_bridge`.
- Configure `tally.config`:
  - Agent URL
  - API token
  - Batch size
  - Poll window
  - Retry/backoff policy
- Maintain master mappings in `tally.mapping`.

### Step 2 — Run Local Agent

- Deploy agent on host/network with TallyPrime access.
- Configure agent via env/config:
  - `ODOO_BASE_URL`
  - `ODOO_API_TOKEN`
  - `POLL_INTERVAL_SEC`
  - `TALLY_URL=http://localhost:9000`
  - `BATCH_LIMIT`

### Step 3 — Enable TallyPrime HTTP XML

- Enable XML over HTTP in TallyPrime.
- Confirm listening port (default `9000`).
- Validate from agent host with a test request.

### Step 4 — Execute Sync Cycle

1. Agent fetches `GET /tally/pending`.
2. Agent maps/transforms each item to Tally XML.
3. Agent submits XML to TallyPrime.
4. Agent posts `POST /tally/result`.
5. Odoo updates queue status and audit trail.

### Step 5 — Retry & Failure Policy

- Retry transient failures with exponential backoff.
- Move permanent failures to `dead` after threshold.
- Keep detailed error codes/messages for reprocessing.

### Step 6 — Monitoring

Track:
- Queue depth (`pending`, `failed`, `dead`)
- Average processing latency
- Success/failure ratio by entity
- Top mapping/validation errors

---

## 11) Operational Guidelines

- Process **masters before vouchers** where dependency exists.
- Keep mapping tables versioned and reviewable.
- Introduce new entities behind feature flags.
- Reconcile daily counts between Odoo and Tally for early detection.

---

## 12) Change Management (Mandatory)

If process/API/schema/sync rules change, **update this README in the same change set**.

At minimum, revise:
- Architecture section
- API contract examples
- Queue states/retry behavior
- Supported scope list
- Runbook steps

This README is the source of truth for implementation and support handover.


---


## 13) Odoo Module Blueprint (`tally_bridge`)

Based on your shared process, this section defines how to implement it as an Odoo module.

### 13.1 Module purpose

`tally_bridge` is an outbound accounting integration module that:
- captures supported accounting events,
- writes integration jobs into a queue,
- exposes agent-facing APIs,
- records sync outcomes for audit and reprocessing.

### 13.2 Suggested module structure

```text
addons/tally_bridge/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── tally_config.py
│   ├── tally_mapping.py
│   └── tally_sync_queue.py
├── controllers/
│   └── tally_api.py
├── security/
│   ├── ir.model.access.csv
│   └── security.xml
├── data/
│   └── ir_cron_data.xml
└── views/
    ├── tally_config_views.xml
    ├── tally_mapping_views.xml
    └── tally_sync_queue_views.xml
```

### 13.3 Model responsibilities

- `tally.config`
  - Stores API token, enabled companies, batch size, retry limits, and agent callback settings.
- `tally.mapping`
  - Maps Odoo masters/codes to Tally names or group references.
- `tally.sync.queue`
  - One record per sync job with payload snapshot, status, retry count, and error log.

### 13.4 Queue fields (recommended)

- `name` (job reference)
- `company_id`
- `odoo_model`
- `record_id`
- `operation` (`create`/`update`)
- `external_guid` (`odoo_model:record_id`)
- `payload_json`
- `state` (`draft`, `pending`, `processing`, `done`, `failed`, `dead`)
- `attempt_count`
- `next_retry_at`
- `last_error`
- `tally_reference`
- `processed_at`

### 13.5 API endpoints implemented by module

- `GET /tally/pending`
  - Returns `pending` jobs in deterministic order with lock/lease strategy.
- `POST /tally/result`
  - Accepts agent callback to mark `done` / `failed`, store response and error details.

### 13.6 Business hooks (event creation)

Create queue jobs when these records are posted/validated:
- Customers
- Vendors
- Ledgers
- Taxes
- Sales invoices
- Purchase bills
- Payments
- Credit notes
- Debit notes

### 13.7 Cron + agent coordination

- Optional cron can pre-build payload snapshots and mark records `pending`.
- Agent remains the executor that polls and pushes XML to Tally.
- Cron must never post to Tally directly.

### 13.8 Access control

- Only integration/admin groups can modify config and mappings.
- Queue records are read-only for normal users except audit views.
- API endpoints must require token validation.

### 13.9 Definition of done for module

- Queue records are created for all Phase-1 entities.
- Phase 1B customer hooks enqueue top-level `res.partner` customer records when customer-facing fields change.
- `GET /tally/pending` and `POST /tally/result` are stable and documented.
- Retries and dead-letter behavior work as configured.
- Audit trail can answer: what was sent, when, by whom, and with what result.


## 14) Current Implementation Status (Phase 1 Started)

A starter Odoo addon `tally_bridge` is now scaffolded for **Odoo 19** and designed to work with both:
- **Odoo 19 Community**
- **Odoo 19 Enterprise**

Implemented baseline:
- Manifest + module init
- Core models: `tally.config`, `tally.mapping`, `tally.sync.queue`
- API controllers for `GET /tally/pending` and `POST /tally/result`
- Security groups + model access file
- Basic queue retry cron
- Initial list views for config, mapping, and queue

Phase 1B customer hook status:
- Top-level `res.partner` customers (`customer_rank > 0`) are queued automatically after creation and after customer-facing field updates.
- Customer payload snapshots include company, identity, contact details, address details, and the company-specific receivable account.
- Queue creation is idempotent by `external_guid`, so later customer edits refresh the existing queue job and return it to `pending` for agent pickup.

Next step: extend entity-specific queue hooks to **Vendors** and **Ledgers**.
