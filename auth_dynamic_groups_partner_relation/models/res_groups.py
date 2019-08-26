# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,invalid-name
import logging

from odoo import _, api, fields, models


_logger = logging.getLogger(__name__)

COUNT_RELATION_STATEMENT = """\
SELECT COUNT(*) AS kount
 FROM dynamic_group_relation_type_rel rel
 JOIN res_partner_relation_all AS rpra
   ON rel.type_selection_id = rpra.type_selection_id
 WHERE rel.gid = %s
   AND rpra.this_partner_id = %s
   AND (rpra.date_start IS NULL or rpra.date_start <= CURRENT_DATE)
   AND (rpra.date_end IS NULL or rpra.date_end >= CURRENT_DATE)
"""


class ResGroups(models.Model):
    _inherit = 'res.groups'

    group_type = fields.Selection(
        selection_add=[('relation', 'Based on relations with other partners')])
    relation_type_ids = fields.Many2many(
        comodel_name='res.partner.relation.type.selection',
        relation='dynamic_group_relation_type_rel',
        column1='gid', column2='type_selection_id',
        string="Relation types that grant group membership",
        help="Specify the relations types that, if a user is connected"
             " with another partner through such a relation, grants the"
             "  user membership of this group.")
    allow_companies = fields.Boolean(
        help="Normally users should be persons, and therefore only the"
             " side of relations that apply to persons should be selectable.\n"
             "Allowing companies as users, will make all relations"
             " available for selection.")

    @api.onchange('allow_companies')
    def _onchange_allow_companies(self):
        self.ensure_one()
        relation_type_domain = [(1, '=', 1)]
        if not self.allow_companies:
            relation_type_domain = [
                '|',
                ('contact_type_this', '=', 'p'),
                ('contact_type_this', '=', False)]
        return {'domain': {'relation_type_ids': relation_type_domain}}

    @api.multi
    def should_be_in(self, user):
        """Determine wether user should be in group."""
        self.ensure_one()
        if self.group_type == 'relation':
            return self.has_user_relation(user)
        return super(ResGroups, self).should_be_in(user)

    @api.multi
    def has_user_relation(self, user):
        """Check wether user has an active contract that gives group access."""
        self.ensure_one()
        self.env.cr.execute(
            COUNT_RELATION_STATEMENT, (self.id, user.partner_id.id))
        kount = self.env.cr.fetchone()[0]
        _logger.info(
            _("User %s has %d relations qualifying for dynamic group %s"),
            user.display_name, kount, self.display_name)
        return kount > 0
