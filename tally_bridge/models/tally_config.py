from odoo import fields, models


class TallyConfig(models.Model):
    _name = "tally.config"
    _description = "Tally Integration Configuration"

    name = fields.Char(default="Default", required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    api_token = fields.Char(required=True)
    agent_url = fields.Char(required=True)
    batch_limit = fields.Integer(default=50)
    retry_limit = fields.Integer(default=5)
    poll_interval_sec = fields.Integer(default=30)
