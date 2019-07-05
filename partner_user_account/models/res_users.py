# -*- coding: utf-8 -*-
# Copyright 2013-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,protected-access,no-self-use
from odoo import _, api, exceptions, models


class Resusers(models.Model):
    _inherit = 'res.users'

    @api.model
    def create_for_partner(
            self, partner, template_user=False, login=False):
        """Create user for partner.

        Needs authorization o read template user, but will use sudo()
        for actual user creation.
        """
        login = login or partner.email
        template_user = template_user or self.get_template_user(partner)
        if partner.user_ids:
            raise exceptions.UserError(
                _('Partner %s already has a user account') %
                partner.display_name)
        existing_user = self.search([('login', '=', login)], limit=1)
        if existing_user:
            raise exceptions.UserError(
                _('Partner %s already has a user account with login %s') %
                (existing_user.partner_id.display_name, login))
        vals = {
            'partner_id': partner.id,
            'login': login,
            'active': True}
        if template_user:
            return template_user.sudo().copy(default=vals)
        return self.sudo().create(vals)

    @api.model
    def get_template_user(self, partner):
        """Get user to use as template for creation.

        It is very unlikely that this function will not return a template
        user, but it might happen if the default users have been deleted.
        """
        company = partner.company_id or self._get_company()
        return company.template_user_id or self.env.ref(
            'auth_signup.default_template_user',
            raise_if_not_found=False) or self.env.ref(
                'base.default_user', raise_if_not_found=False) or False
