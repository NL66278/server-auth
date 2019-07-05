#-*- coding: utf-8 -*-
# Copyright 2013-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,protected-access
from odoo import _, api, fields, models


class WizardCreateUser(models.TransientModel):
    _name = 'wizard.create.user'
    _description = "Create user for existing partner"

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True, readonly=True)
    template_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Template user')
    login = fields.Char('Login')

    @api.multi
    def action_create_user(self):
        """Create user for partner, using email as login."""
        self.ensure_one()
        user_model = self.env['res.users']
        user_model.create_for_partner(
            self.partner_id, template_user=self.template_user_id,
            login=self.login)
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def create_action_window(self, partner):
        """Return a popup window for this wizard."""
        user_model = self.env['res.users']
        template_user = user_model.get_template_user(partner)
        vals = {
            'partner_id': partner.id,
            'template_user_id': template_user.id,
            'login': partner.email}
        wizard = self.create(vals)
        return {
            'name': self._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'domain': [],
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': wizard.id,
            'nodestroy': True}
