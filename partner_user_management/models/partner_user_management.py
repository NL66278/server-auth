# Copyright 2019 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-docstring,protected-access,invalid-name
import logging
import time

from odoo import _, api, fields, models
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class PartnerUserManagement(models.Model):
    _name = "partner.user.management"
    _description = "Configuration of user-management by partner-managers."
    _order = 'sequence, name'

    name = fields.Char()
    sequence = fields.Integer(string="Priority", default=5, required=True)
    # Fields to limit the application of this configuration.
    must_have_email = fields.Boolean(
        default=True,
        help="Only partners with an email address, can or will be created.",
    )
    category_id = fields.Many2one(
        comodel_name="res.partner.category",
        help="Partner category to which this configuration applies",
    )
    partner_domain = fields.Char(
        default='[]',
        help="Domain on partner, to apply in addition to possible category and email",
    )
    # What can be done with partner / users for this configuration.
    template_user_id = fields.Many2one(
        comodel_name="res.users", string="Template for users on partners"
    )
    allow_create_user = fields.Boolean(string="Allow partner managers to create users")
    allow_password_reset_mail = fields.Boolean(
        string="Sending of passport reset mail allowed",
        help="Allow partner managers to send password reset mail",
    )
    auto_create_user = fields.Boolean(
        string="Create user automatically",
        help="Create user automatically if conditions met.\n"
        " Conditions like right category and email valid.",
    )
    auto_reset_mail = fields.Boolean(
        string="Send password reset mail automatically",
        help="Send password reset mail automatically as soon as user is created.",
    )
    reset_mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        help="Mail template to use for password reset",
    )
    # Who can manage users (default all partner managers).
    partner_manager_ids = fields.Many2many(
        comodel_name="res.users",
        domain=lambda self: [
            ("groups_id", "=", self.env.ref("base.group_partner_manager").id)
        ],
        help="Users allowed to manage other users for this configuration",
    )

    def default_get(self, fields_list):
        """Set defaults."""
        result = super.default_get(fields_list)
        if 'template_user_id' in fields_list:
            result['template_user_id'] = \
                self.env.ref("auth_signup.default_template_user").id
        if 'reset_mail_template_id' in fields_list:
            result['reset_mail_template_id'] = \
                self.env.ref("auth_signup.set_password_email").id
        return result

    @api.model
    def cron_user_auto_creation(self):
        """Automatically create users for partners if enabled from configuration.

        Users will be created if partner has no user. This functionality
        is applicable to a multi-company setting as well.

        As user-creation is very resource intensive, only a limited number of users
        will be created at a time.
        """
        # First update management configuration in partners.
        self.update_partner_user_management()
        partner_model = self.env['res.partner']
        user_model = self.env['res.users']
        auto_create_records = self.env['res.company'].search([
            ('auto_create_user', '=', True),
        ])
        for this in auto_create_records:
            partners = partner_model.search(
                [('partner_management_id', '=', this.id), ('user_ids', '=', False)],
                limit=256
            )
            for partner in partners:
                login = this._get_login()
                if not login:
                    continue
                _logger.info(
                    "Creating user for partner %s with login %s for definition %s.",
                    partner.display_name,
                    login,
                    this.display_name,
                )
                user_model.with_context(
                    tracking_disable=True,
                    install_mode=True,
                    no_reset_password=this.auto_reset_mail,
                )._create_for_partner(
                    partner,
                    template_user=this.template_user_id,
                    login=login,
                )

    @api.model
    def update_partner_user_management(self):
        """Set the right partner management configuration on all partners."""
        partner_model = self.env['res.partner']
        partner_management_link = {
            id: False for id in partner_model.search([]).ids
        }
        for record in self.search([]):
            partner_domain = record._get_partner_domain()
            for partner in partner_model.search(partner_domain):
                if not partner_management_link[partner.id]:
                    partner_management_link[partner.id] = record.id
                    if partner.partner_management_id != record.id:
                        _logger.info(
                            _("Account for partner %s now managed by %s."),
                            partner.display_name,
                            record.display_name
                        )
                        partner.write({
                            'partner_management_id', record.id,
                        })
        # Now check for all partners that should have management unset.
        for partner in partner_model.search([('partner_management_id', '!=', False)]):
            if not partner_management_link[partner.id]:
                # Should no longer be managed.
                _logger.info(
                    _("Account for partner %s no longer managed by %s."),
                    partner.display_name,
                    partner.partner_management_id.display_name
                )
                partner.write({
                    'partner_management_id', False,
                })

    @api.multi
    def _get_partner_domain(self):
        """Get domain to select the partners to which this configuration applies."""
        self.ensure_one()
        partner_domain = []
        if self.must_have_email:
            partner_domain.append(('email', '!=', False))
        if self.category_id:
            partner_domain.append(('category_id', '=', self.category_id.id))
        if self.partner_domain:
            eval_context = self._get_eval_context()
            eval_context['partner_management_id'] = self
            partner_domain.append(safe_eval(self.partner_domain, eval_context))
        return partner_domain

    @api.model
    def _get_eval_context(self):
        """Returns a dictionary to use as evaluation context for partner_domain."""
        # use an empty context for 'user' to make the domain evaluation
        # independent from the context
        return {'user': self.env.user.with_context({}), 'time': time}
