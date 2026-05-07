from odoo import api, models


CUSTOMER_SYNC_FIELDS = {
    "active",
    "city",
    "company_id",
    "country_id",
    "customer_rank",
    "email",
    "mobile",
    "name",
    "parent_id",
    "phone",
    "property_account_receivable_id",
    "state_id",
    "street",
    "street2",
    "vat",
    "zip",
}


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        partners._tally_enqueue_customer_changes("create")
        return partners

    def write(self, vals):
        result = super().write(vals)
        if CUSTOMER_SYNC_FIELDS.intersection(vals):
            self._tally_enqueue_customer_changes("update")
        return result

    def _tally_enqueue_customer_changes(self, operation):
        customers = self.filtered(lambda partner: partner._tally_is_customer())
        for partner in customers:
            self.env["tally.sync.queue"].sudo().enqueue_record(
                record=partner,
                operation=operation,
                payload=partner._tally_customer_payload(),
            )

    def _tally_is_customer(self):
        self.ensure_one()
        return not self.parent_id and self.customer_rank > 0

    def _tally_customer_payload(self):
        self.ensure_one()
        company = self.company_id or self.env.company
        receivable_account = self.with_company(company).property_account_receivable_id
        return {
            "entity_type": "customer",
            "odoo_model": self._name,
            "record_id": self.id,
            "external_guid": f"{self._name}:{self.id}",
            "company": {
                "id": company.id,
                "name": company.name,
            },
            "name": self.name,
            "active": self.active,
            "vat": self.vat,
            "email": self.email,
            "phone": self.phone,
            "mobile": self.mobile,
            "address": {
                "street": self.street,
                "street2": self.street2,
                "city": self.city,
                "state": self.state_id.name,
                "country": self.country_id.name,
                "zip": self.zip,
            },
            "receivable_account": {
                "id": receivable_account.id,
                "code": receivable_account.code,
                "name": receivable_account.name,
                "display_name": receivable_account.display_name,
            }
            if receivable_account
            else False,
        }
