# Tally Bridge Phase 1B Test Data and Test Cases

This document provides the sample data needed to configure and validate the current Phase 1B customer queue implementation.

## 1. Demo data included in the addon

When Odoo is started or the module is installed with demo data enabled, `tally_bridge/demo/tally_bridge_demo.xml` creates:

| Type | External ID | Purpose |
| --- | --- | --- |
| Configuration | `tally_bridge.tally_config_demo` | Local agent API/token settings for testing. |
| Mapping | `tally_bridge.tally_mapping_customer_group` | Maps Odoo customers to Tally `Sundry Debtors`. |
| Mapping | `tally_bridge.tally_mapping_receivable_account` | Maps Odoo receivable accounts to Tally `Sundry Debtors`. |
| Mapping | `tally_bridge.tally_mapping_tax_gst_output` | Sample GST output tax mapping. |
| Customer | `tally_bridge.res_partner_tally_demo_customer` | Customer that should create a pending Tally queue job. |
| Prospect | `tally_bridge.res_partner_tally_demo_non_customer` | Non-customer control record that should not create a customer queue job. |

## 2. Demo configuration values

Use these values for local development only. Replace the token before using any shared or production database.

| Field | Value |
| --- | --- |
| Configuration name | `Demo Tally Agent Configuration` |
| Company | `base.main_company` |
| Agent URL | `http://localhost:8000` |
| API token | `demo-tally-token-change-me` |
| Batch limit | `10` |
| Retry limit | `3` |
| Poll interval | `30` seconds |

## 3. Manual customer test data

If demo data is not loaded, create this customer manually in Odoo Contacts:

| Field | Value |
| --- | --- |
| Name | `Tally Demo Customer Pvt Ltd` |
| Customer rank / Is a customer | enabled / customer |
| Street | `221B Integration Street` |
| Street 2 | `Phase 1B Test Block` |
| City | `Bengaluru` |
| ZIP | `560001` |
| Country | `India` |
| GSTIN / VAT | `29ABCDE1234F1Z5` |
| Email | `accounts.customer@example.com` |
| Phone | `+91 80 4000 1000` |
| Mobile | `+91 90000 10000` |

Expected result: one `tally.sync.queue` record with `odoo_model = res.partner`, `state = pending`, and a JSON payload containing the customer identity, address, contact details, company, and receivable account.

## 4. Manual mapping test data

Create these `tally.mapping` rows when configuring a database without demo data:

| Name | Odoo model | Odoo key | Tally value |
| --- | --- | --- | --- |
| Customers / Sundry Debtors | `res.partner` | `customer_group` | `Sundry Debtors` |
| Account Receivable / Sundry Debtors | `account.account` | `account_receivable` | `Sundry Debtors` |
| Output GST 18% | `account.tax` | `output_gst_18` | `Output GST @ 18%` |

## 5. Agent API smoke test

After creating the sample customer, the local agent can poll pending jobs with the demo token:

```bash
curl -X GET \
  -H "Content-Type: application/json" \
  -H "X-API-Token: demo-tally-token-change-me" \
  http://localhost:8069/tally/pending
```

Expected response shape:

```json
{
  "items": [
    {
      "entity": "res.partner",
      "operation": "create",
      "external_guid": "res.partner:<customer-id>",
      "payload": {
        "entity_type": "customer",
        "name": "Tally Demo Customer Pvt Ltd"
      }
    }
  ]
}
```

Post a successful result callback with the returned `queue_id`:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Token: demo-tally-token-change-me" \
  -d '{"queue_id": 1, "status": "done", "tally_ref": "LEDGER-TALLY-DEMO-CUSTOMER", "message": "Ledger created"}' \
  http://localhost:8069/tally/result
```

Expected result: the queue record moves to `done` and stores `LEDGER-TALLY-DEMO-CUSTOMER` in `tally_reference`.

## 6. Functional test cases

| Case | Steps | Expected result |
| --- | --- | --- |
| Customer creation queues a job | Create a top-level customer with `customer_rank > 0`. | A single pending `tally.sync.queue` job is created with `operation = create`. |
| Customer update refreshes job | Change a customer-facing field such as email or VAT. | The same queue record is updated, `operation = update`, `state = pending`, old error/reference fields are cleared. |
| Prospect is ignored | Create a partner without customer status. | No Tally queue job is created. |
| Child contact is ignored | Create a contact under a customer, even with customer rank. | No separate queue job is created for the child contact. |
| Internal-only update is ignored | Update a non-sync field such as an internal note. | No new customer queue job is created. |
