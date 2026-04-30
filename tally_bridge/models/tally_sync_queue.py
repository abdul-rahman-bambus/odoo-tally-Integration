from odoo import api, fields, models


class TallySyncQueue(models.Model):
    _name = "tally.sync.queue"
    _description = "Tally Sync Queue"
    _order = "id asc"

    name = fields.Char(required=True, default=lambda self: "New")
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    odoo_model = fields.Char(required=True)
    record_id = fields.Integer(required=True)
    operation = fields.Selection([("create", "Create"), ("update", "Update")], default="create", required=True)
    external_guid = fields.Char(required=True, index=True)
    payload_json = fields.Text(required=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("done", "Done"),
            ("failed", "Failed"),
            ("dead", "Dead"),
        ],
        default="pending",
        required=True,
        index=True,
    )
    attempt_count = fields.Integer(default=0)
    next_retry_at = fields.Datetime()
    last_error = fields.Text()
    tally_reference = fields.Char()
    processed_at = fields.Datetime()

    _sql_constraints = [
        ("uniq_external_guid", "unique(external_guid)", "External GUID must be unique."),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("tally.sync.queue") or "New"
        return super().create(vals_list)
