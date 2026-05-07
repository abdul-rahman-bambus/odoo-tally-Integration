import json

from odoo import fields, http
from odoo.http import request


class TallyAPIController(http.Controller):
    def _authorize(self):
        token = request.httprequest.headers.get("X-API-Token")
        config = request.env["tally.config"].sudo().search([("active", "=", True)], limit=1)
        return bool(config and token and token == config.api_token)

    @http.route("/tally/pending", type="json", auth="none", methods=["GET"], csrf=False)
    def get_pending(self, limit=50, **kwargs):
        if not self._authorize():
            return {"error": "unauthorized"}

        queue_items = request.env["tally.sync.queue"].sudo().search([("state", "=", "pending")], limit=int(limit), order="id asc")
        payload = []
        for item in queue_items:
            item.state = "processing"
            payload.append(
                {
                    "queue_id": item.id,
                    "entity": item.odoo_model,
                    "operation": item.operation,
                    "record_id": item.record_id,
                    "external_guid": item.external_guid,
                    "payload": json.loads(item.payload_json or "{}"),
                    "attempt_count": item.attempt_count,
                    "created_at": item.create_date,
                }
            )
        return {"items": payload}

    @http.route("/tally/result", type="json", auth="none", methods=["POST"], csrf=False)
    def post_result(self, **kwargs):
        if not self._authorize():
            return {"error": "unauthorized"}

        queue_id = kwargs.get("queue_id")
        status = kwargs.get("status")
        queue = request.env["tally.sync.queue"].sudo().browse(queue_id)
        if not queue.exists():
            return {"error": "queue_not_found"}

        values = {
            "tally_reference": kwargs.get("tally_ref"),
            "last_error": kwargs.get("message") if status != "done" else False,
            "processed_at": fields.Datetime.now(),
        }
        if status == "done":
            values["state"] = "done"
        else:
            values.update({"state": "failed", "attempt_count": queue.attempt_count + 1})
        queue.write(values)
        return {"ok": True}
