# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# pylint: disable=protected-access,too-few-public-methods
from odoo.tests.common import TransactionCase


class TestPartnerManagement(TransactionCase):
    """Test Partner Account Management."""

    def test_auto_create(self):
        """test automatic user creation."""
        management_model = self.env['partner.user.management']
        partner_model = self.env['res.partner']
        # Create management config with auto-configuration.
        vals = management_model.default_get()
        vals.update({
            'name': 'Test management config',
            'sequence': 1,  # Hugh priority for testing
            'auto_create_user': True,
            'partner_domain': str([('ref', '=', 'PUM0001')]),
        })
        test_management = management_model.create(vals)
        # Create partner first without email address.
        vals = partner_model.default_get()
        vals.update({
            'is_company': False,
            'name': 'Jan Boezeroen',
            'ref': 'PUM0001',
        })
        test_partner = partner_model.create(vals)
        # Partner should not satisfy criteria because of no email.
        partner_domain = test_management._get_partner_domain()
        self.assertEqual(
            partner_domain,
            [('email', '!=', False), ('ref', '=', 'PUM0001')]
        )
        management_model.update_partner_user_management()
        self.assertFalse(test_partner.partner_management_id.id)
        # Now set email on partner. Criteria for inclusion should be satisfied.
        test_partner.write({'email': 'janboezeroen@example.com'})
        management_model.update_partner_user_management()
        self.assertEqual(
            test_partner.partner_management_id,
            test_management
        )
        # Running the cronjob should create the partner.
        management_model.cron_user_auto_creation()
        self.assertTrue(bool(test_partner.user_ids))
