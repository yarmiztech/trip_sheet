from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tests.common import Form
from odoo.exceptions import UserError, ValidationError


class BattaConfiguration(models.Model):
    _name = 'bitta.configuration'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, default='New', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    from_bag = fields.Integer(string="From Bag")
    to_bag = fields.Integer(string="To Bag")
    price = fields.Float(string="Charge")
    _sql_constraints = [
        (
            "to_bag_uniq",
            "unique(to_bag)",
            "Bags must be only once !",
        ),
    ]

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'bitta.configuration') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('bitta.configuration') or _('New')
        return super(BattaConfiguration, self).create(vals)






