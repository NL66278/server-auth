# Copyright 2013-2019 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,protected-access
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.multi
    def _compute_partner_management(self):
        """Selection of applicable partner management.

        Record rules should take care that user is shown only
        a configuration she is entitled to.
        """
        for this in self:
            if not this.partner_management_id:
                this.can_create_user = False
                this.can_sent_password_reset_mail = False
                continue
            management = this.partner_management_id
            this.can_create_user = (
                True if management.allow_create_user and not this.user_ids else False
            )
            this.can_sent_password_reset_mail = (
                True
                if management.allow_password_reset_mail and this.user_ids
                else False
            )

    partner_management_id = fields.One2many(
        string="Applicable partner management configuration",
        compute="_compute_partner_management",
        help="Active partner management will depend on logged in user",
    )
    can_create_user = fields.Boolean(
        string="Can create user now?", compute="_compute_partner_management"
    )
    can_sent_password_reset_mail = fields.Boolean(
        string="Can sent password reset mail?", compute="_compute_partner_management"
    )

    @api.multi
    def action_create_user(self):
        """Start wizard to create user for partner."""
        self.ensure_one()
        user_model = self.env["res.users"]
        user_model.create_for_partner(self.partner_id)

    @api.multi
    def action_show_user(self):
        """Start wizard to show user for partner."""
        self.ensure_one()
        return {
            "name": "User",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "res.users",
            "domain": [],
            "context": self.env.context,
            "type": "ir.actions.act_window",
            "target": "blank",
            "res_id": self.user_ids[0].id,
        }

    @api.multi
    def _get_login(self):
        """Get login name for user."""
        self.ensure_one()
        return self.email or False
