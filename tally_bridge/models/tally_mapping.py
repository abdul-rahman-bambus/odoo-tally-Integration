from odoo import fields, models


class TallyMapping(models.Model):
    _name = "tally.mapping"
    _description = "Odoo to Tally Mapping"

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    odoo_model = fields.Char(required=True)
    odoo_key = fields.Char(required=True)
    tally_value = fields.Char(required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "uniq_mapping",
            "unique(company_id, odoo_model, odoo_key)",
            "Mapping already exists for this company/model/key.",
        )
    ]
