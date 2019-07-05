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
