# -*- coding: utf-8 -*-
# Copyright 2013-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,protected-access
from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def action_wizard_create_user(self):
        """Start wizard to create user for partner."""
        self.ensure_one()
        wizard_model = self.env['wizard.create.user']
        return wizard_model.create_action_window(self)

    @api.model
    def cron_res_partner_user_creation(self):
        """Automatically create users for partners if enabled.

        Users will be created if partner has no user, and this is enabled
        on the company for the partner, or else the company of the current
        user.

        As user-creation is very resource intensive, only 128 users will be
        created at a time.
        """
        partners = self.search([('user_ids', '=', False)], limit=128)
        partners.check_autocreate()

    @api.multi
    def check_autocreate(self):
        user_model = self.env['res.users']
        for this in self:
            if this.user_ids:
                continue
            company = this.company_id or self.env.user.company_id
            if not company.enable_autocreate:
                continue
            login = this._get_login()
            if not login:
                continue
            user_model.create_for_partner(this, login=login)

    @api.multi
    def _get_login(self):
        """Get login name for user."""
        self.ensure_one()
        return self.email or False
