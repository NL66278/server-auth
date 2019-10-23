# -*- coding: utf-8 -*-
# Copyright 2013-2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    template_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Template for users on partners",
    )
    enable_autocreate = fields.Boolean(
        help="When set users will be automatically created if possible.",
    )
