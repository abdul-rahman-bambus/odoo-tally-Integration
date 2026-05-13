import json

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestTallyCustomerQueue(TransactionCase):
    def _queue_for(self, record):
        return self.env["tally.sync.queue"].search(
            [("external_guid", "=", f"{record._name}:{record.id}")],
            limit=1,
        )

    def test_customer_create_enqueues_pending_job_with_payload(self):
        customer = self.env["res.partner"].create(
            {
                "name": "Test Tally Customer",
                "customer_rank": 1,
                "email": "customer@example.com",
                "phone": "+1 555 0100",
                "street": "100 Test Street",
                "city": "Test City",
                "zip": "12345",
            }
        )

        queue = self._queue_for(customer)
        self.assertTrue(queue, "Customer creation should create a Tally queue job.")
        self.assertEqual(queue.state, "pending")
        self.assertEqual(queue.operation, "create")
        self.assertEqual(queue.odoo_model, "res.partner")
        self.assertEqual(queue.record_id, customer.id)

        payload = json.loads(queue.payload_json)
        self.assertEqual(payload["entity_type"], "customer")
        self.assertEqual(payload["name"], "Test Tally Customer")
        self.assertEqual(payload["email"], "customer@example.com")
        self.assertEqual(payload["address"]["city"], "Test City")
        self.assertEqual(payload["external_guid"], queue.external_guid)

    def test_customer_update_refreshes_existing_queue_job(self):
        customer = self.env["res.partner"].create(
            {
                "name": "Update Me Customer",
                "customer_rank": 1,
                "email": "before@example.com",
            }
        )
        queue = self._queue_for(customer)
        queue.write(
            {
                "state": "processing",
                "attempt_count": 2,
                "last_error": "temporary failure",
                "tally_reference": "OLD-TALLY-REF",
            }
        )

        customer.write({"email": "after@example.com"})

        refreshed_queue = self._queue_for(customer)
        self.assertEqual(refreshed_queue.id, queue.id)
        self.assertEqual(refreshed_queue.state, "pending")
        self.assertEqual(refreshed_queue.operation, "update")
        self.assertEqual(refreshed_queue.attempt_count, 0)
        self.assertFalse(refreshed_queue.last_error)
        self.assertFalse(refreshed_queue.tally_reference)
        self.assertEqual(json.loads(refreshed_queue.payload_json)["email"], "after@example.com")

    def test_non_customer_and_child_contacts_do_not_enqueue(self):
        prospect = self.env["res.partner"].create(
            {
                "name": "Prospect Not Synced",
                "email": "prospect@example.com",
            }
        )
        self.assertFalse(self._queue_for(prospect))

        customer = self.env["res.partner"].create(
            {
                "name": "Parent Customer",
                "customer_rank": 1,
            }
        )
        child = self.env["res.partner"].create(
            {
                "name": "Child Contact Not Synced Separately",
                "parent_id": customer.id,
                "customer_rank": 1,
                "email": "child@example.com",
            }
        )
        self.assertFalse(self._queue_for(child))

    def test_irrelevant_partner_update_does_not_enqueue_new_job(self):
        prospect = self.env["res.partner"].create(
            {
                "name": "Prospect Still Not Synced",
            }
        )

        prospect.write({"comment": "Internal-only note should not enqueue."})

        self.assertFalse(self._queue_for(prospect))
