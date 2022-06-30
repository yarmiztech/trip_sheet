from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tests.common import Form
from odoo.exceptions import UserError, ValidationError


class TripConfiguration(models.Model):
    _name = 'trip.configuration'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, default='New', readonly=True)
    type_of_charge = fields.Selection([
        ('fixed', 'Fixed'),
        ('km_price', 'Km/Price'),
    ])
    km_lines = fields.One2many('trip.km.lines','km_conf_id')
    fixed_price = fields.Float(string="Fixed Price")
    km_sign = fields.Char(string='KM',default="Km")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'trip.configuration') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('trip.configuration') or _('New')
        return super(TripConfiguration, self).create(vals)

    # @api.constrains('km_lines')
    # def constrains_to_kilo_meter(self):
    #     for line in self.km_lines:
    #         for l_line in self.km_lines-line:
    #                 if  line.from_kilo_meter <= l_line.from_kilo_meter and l_line.to_kilo_meter <= line.to_kilo_meter:
    #                     raise UserError(_("Km declarations duplication occur please check"))



class TripConfigurationLines(models.Model):
    _name = 'trip.km.lines'

    km_conf_id = fields.Many2one('trip.configuration')
    from_kilo_meter = fields.Integer(string="From=>KM")
    to_kilo_meter = fields.Integer(string="To=>KM")
    price = fields.Float(string="Price")
    currency_id = fields.Many2one('res.currency', related='km_conf_id.company_id.currency_id')

    # @api.depends('from_kilo_meter')
    # @api.onchange('from_kilo_meter')
    # def onchange_from_kilo_meter(self):
    #     if self.from_kilo_meter:
    #         for all in self.km_conf_id.km_lines-self:
    #             if all.from_kilo_meter <= self.from_kilo_meter <= all.to_kilo_meter:
    #                 raise UserError(_("Km declarations duplication occur please check"))
    #
    # @api.depends('to_kilo_meter')
    # @api.onchange('to_kilo_meter')
    # def onchange_to_kilo_meter(self):
    #     if self.to_kilo_meter:
    #         if self.from_kilo_meter > self.to_kilo_meter:
    #             raise UserError(_("To Km should be greater than from Km"))
    #
    #         for all in self.km_conf_id.km_lines-self:
    #             if all.from_kilo_meter <= self.to_kilo_meter <= all.to_kilo_meter:
    #                 raise UserError(_("Km declarations duplication occur please check"))
    #
    #


class BasicTrip(models.Model):
    _name = 'basic.trip'

    from_kilo_meter = fields.Integer(string="From KM")
    to_kilo_meter = fields.Integer(string="To KM")
    basic_bags = fields.Integer(string="Basic Bags")
    price = fields.Float(string="Basic Price")
    additional_price = fields.Float(string="Additional Price")
