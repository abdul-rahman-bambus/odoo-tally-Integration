from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_tally_partner_roles(self):
        self.ensure_one()
        roles = []
        if self.customer_rank > 0:
            roles.append("customer")
        if self.supplier_rank > 0:
            roles.append("vendor")
        return roles

    def _prepare_tally_partner_payload(self):
        self.ensure_one()
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "roles": self._get_tally_partner_roles(),
            "email": self.email,
            "phone": self.phone,
            "mobile": self.mobile,
            "vat": self.vat,
            "street": self.street,
            "street2": self.street2,
            "city": self.city,
            "zip": self.zip,
            "state": self.state_id.name,
            "country": self.country_id.name,
            "is_company": self.is_company,
            "company_id": self.company_id.id or self.env.company.id,
        }

    def _enqueue_tally_partner_sync(self, operation="create"):
        queue_model = self.env["tally.sync.queue"].sudo()
        for partner in self:
            if partner._get_tally_partner_roles():
                queue_model.enqueue_record(partner, partner._prepare_tally_partner_payload(), operation=operation)

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        partners._enqueue_tally_partner_sync(operation="create")
        return partners

    def write(self, vals):
        result = super().write(vals)
        sync_fields = {
            "name",
            "email",
            "phone",
            "mobile",
            "vat",
            "street",
            "street2",
            "city",
            "zip",
            "state_id",
            "country_id",
            "is_company",
            "customer_rank",
            "supplier_rank",
            "company_id",
        }
        if sync_fields.intersection(vals):
            self._enqueue_tally_partner_sync(operation="update")
        return result
