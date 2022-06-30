from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tests.common import Form
from odoo.exceptions import UserError, ValidationError

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    type_of_charge = fields.Selection([
        ('fixed', 'Fixed'),
        ('km_price', 'Km/Price'),
    ])

class BrothersTripSheet(models.Model):
    _name = 'brothers.trip.sheet'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, default='New', readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle Id")
    vehicle_number = fields.Char(string="Vehicle Number")
    total_bags = fields.Integer(string="Total Bags")
    total_kms = fields.Integer(string="Total Km's")
    company_type = fields.Selection([('internal', 'Internal'), ('external', 'External'), ('branches', 'Branches')],
                                    )
    internal_company = fields.Many2one('res.company',string="Internal Company")
    partner_id = fields.Many2one('res.partner',string="Vendor")
    final_invoice_amount = fields.Float(string="Final Amount",compute='_compute_invoice_amount')
    betta_charge = fields.Float(string="Betta Charge")
    km_charge = fields.Float(string="Km Charge")
    company_id = fields.Many2one('res.company',string="Company Name")
    create_date = fields.Date(string="Date")
    from_invoice = fields.Many2one('account.move',string="Invoice")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('assign_mtc', 'MTC'),
        ('draft', 'Draft'),
        ('done', 'Done')], default='draft')
    type_of_charge = fields.Selection([
        ('fixed', 'Fixed'),
        ('km_price', 'Km/Price'),
    ])
    trip_invoice_id = fields.Many2one('account.move',string="Trip Invoice")
    transport_receipt = fields.Char(string='Transport Receipt no')
    gate_pass = fields.Char(string='Gate Pass No')
    location = fields.Char(string='Location')
    addition_price = fields.Float(string="Additional Price")
    no_of_times = fields.Integer(string="No of Times", default=1)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'brothers.trip.sheet') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('brothers.trip.sheet') or _('New')
        return super(BrothersTripSheet, self).create(vals)

    @api.depends('type_of_charge','km_charge','betta_charge')
    def _compute_invoice_amount(self):
        for each in self:
            each.final_invoice_amount = each.betta_charge+each.km_charge

    @api.onchange('type_of_charge')
    def onchange_type_of_charge(self):
        if self.type_of_charge:
            if self.type_of_charge == 'fixed':
                km_ch = self.env['trip.configuration'].search([('type_of_charge', '=', 'fixed')])
                if km_ch:
                    self.km_charge = km_ch.fixed_price
            if self.type_of_charge == 'km_price':
                km_ch = self.env['trip.configuration'].search([('type_of_charge', '=', 'km_price')])
                if km_ch:
                    for line in km_ch.km_lines:
                        if line.from_kilo_meter <= self.total_kms <= line.to_kilo_meter:
                           self.km_charge = line.price

    def action_trip_marked(self):
        if self.partner_id:
            journal_id = self.env['account.journal'].sudo().search(
                [('name', '=', 'Vendor Bills'),('company_id', '=', self.internal_company.id)]).id,
            account_id = self.env['account.account'].search(
                [('name', '=', 'Purchase Expense'), ('company_id', '=', self.internal_company.id)])
            list = []
            product = self.env['product.product'].search([('name','=','Trip Vehicle')])
            if product:
                # for line in self.inter_company_lines:
                dict = (0, 0, {
                    'name': product.name,
                    'account_id': account_id.id,
                    'price_unit':self.final_invoice_amount,
                    'quantity':1,
                    'product_uom_id': product.uom_id.id,
                    'product_id': product.id,
                })
                list.append(dict)

                invoice = self.env['account.move'].sudo().create({
                    'partner_id': self.partner_id.id,
                    'move_type': 'in_invoice',
                    'state': 'draft',
                    'company_id': self.internal_company.id,
                    'invoice_date': datetime.today().date(),
                    'vehicle_number': self.vehicle_number,
                    'journal_id': journal_id,
                    'invoice_line_ids': list,
                    'brothers_sheet_id': self.id,

                })
                self.trip_invoice_id = invoice
            else:
                raise UserError(_("Please create Product Trip Vehicle"))


    def action_trip_invoices(self):
        return {
            'name': _('Journal Entries'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.sudo().trip_invoice_id.ids)],
        }


class AccountInvoice(models.Model):
    _inherit = "account.move"

    brothers_sheet_id = fields.Many2one('brothers.trip.sheet',string="Brothers Sheet")
    br_trip_id = fields.Many2one('brothers.trip.date')
    vehicle_number = fields.Char(string="Vehicle Number")


    def action_generate_trip(self):
        fleet = self.env['fleet.vehicle'].sudo().search([('license_plate', '=', self.vehicle_number)])
        total_bag = sum(self.invoice_line_ids.filtered(lambda a: a.is_rounding_line_enz != True).mapped('quantity'))
        bitta = self.env['bitta.configuration'].search([('to_bag','>=',total_bag)])
        if bitta:
            bitta = bitta[0]
        if fleet:
            if fleet.type_of_charge:
                km_charge = 0
                if fleet.type_of_charge == 'fixed':
                    km_ch = self.env['trip.configuration'].search([('type_of_charge', '=', 'fixed')])
                    if km_ch:
                        km_charge = km_ch.fixed_price
                if fleet.type_of_charge == 'km_price':
                    km_ch = self.env['trip.configuration'].search([('type_of_charge', '=', 'km_price')])
                    if km_ch:
                        for line in km_ch.km_lines:
                            if line.from_kilo_meter <= self.distance<= line.to_kilo_meter:
                                km_charge = line.price

            self.env['brothers.trip.sheet'].create({
                'vehicle_id':fleet.id,
                'vehicle_number':self.vehicle_number,
                'total_bags':total_bag,
                'total_kms':self.distance,
                'company_type':fleet.company_type,
                'internal_company':fleet.internal_comapny.id,
                'partner_id':fleet.internal_comapny.partner_id.id,
                'company_id':self.company_id.id,
                'create_date':datetime.today().date(),
                'betta_charge':bitta.price,
                'type_of_charge':fleet.type_of_charge,
                'km_charge':km_charge,
                'from_invoice':self.id,
            })

        else:
            raise UserError(_("This Vehicle Number Not belongs to Vehicle in system"))




class brothersTripDateReport(models.Model):
    _name = 'brothers.trip.date'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, copy=False, default='New', readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle Id")
    create_date = fields.Date(string='Create Date', default=fields.Date.context_today, required=True)
    date_lines = fields.One2many('brothers.trip.lines','trip_date_id')
    trip_invoice_ids = fields.One2many('account.move','br_trip_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')], default='draft')
    type = fields.Selection([
        ('all', 'ALL'),
        ('vehicle', 'Vehicle Wise')], default='all')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'brothers.trip.date') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('brothers.trip.date') or _('New')
        return super(brothersTripDateReport, self).create(vals)

    def action_trip_invoices(self):
        return {
            'name': _('Journal Entries'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.sudo().trip_invoice_ids.ids)],
        }


    @api.onchange('create_date','type','vehicle_id')
    def check_create_date(self):

        all = self.env['brothers.trip.sheet']
        if self.type == 'all':
            all = self.env['brothers.trip.sheet'].search([('state','=','assign_mtc'),('create_date', '=', self.create_date)])

        if self.type == 'vehicle':
            if self.vehicle_id:
               all = self.env['brothers.trip.sheet'].search([('state','=','assign_mtc'),('create_date', '=', self.create_date),('vehicle_id','=',self.vehicle_id.id)])
        list = []
        for each in all:
            # each.write({'state':'done'})
            list_dict= (0,0,{
                    'vehicle_id': each.vehicle_id.id,
                    'vehicle_number': each.vehicle_number,
                    'total_bags': each.total_bags,
                    'total_kms': each.total_kms,
                    'company_type': each.company_type,
                     'trip_rec_id':each,
                    'internal_company': each.internal_company.id,
                    'partner_id': each.partner_id.id,
                    # 'company_id': each.company_id.id,
                    'company_id': each.company_id.id,
                    'create_date': each.create_date,
                    'betta_charge': each.betta_charge,
                    'type_of_charge': each.type_of_charge,
                    'km_charge':each.km_charge,
                    'from_invoice': each.from_invoice.id,
                    'final_invoice_amount': each.final_invoice_amount,
                })
            list.append(list_dict)
        self.date_lines = False
        self.date_lines = list

    def action_trip_marked(self):
        for partner_wise in self.date_lines.mapped('partner_id'):
            list = []
            final_amount = 0
            company_id = self.env['res.company']
            journal_id = self.env['account.journal']
            account_id = self.env['account.account']
            for all in self.date_lines:
                all.trip_rec_id.write({'state':'done'})
                if all.company_id:
                    company_id = all.internal_company
                if all.partner_id == partner_wise:
                    final_amount += all.final_invoice_amount
                journal_id = self.env['account.journal'].sudo().search(
                    [('name', '=', 'Vendor Bills'),('company_id', '=', all.company_id.id)]).id,
                account_id = self.env['account.account'].search(
                    [('name', '=', 'Purchase Expense'), ('company_id', '=', all.company_id.id)])

            product = self.env['product.product'].search([('name','=','Trip Vehicle')])
            if product:
                # for line in self.inter_company_lines:
                dict = (0, 0, {
                    'name': product.name,
                    'account_id': account_id.id,
                    'price_unit':final_amount,
                    'quantity':1,
                    'product_uom_id': product.uom_id.id,
                    'product_id': product.id,
                })
                list.append(dict)
            if list:
                invoice = self.env['account.move'].sudo().create({
                    'partner_id': partner_wise.id,
                    'move_type': 'in_invoice',
                    'state': 'draft',
                    'company_id': company_id.id,
                    'invoice_date': self.create_date,
                    'journal_id': journal_id,
                    'invoice_line_ids': list,
                    # 'brothers_sheet_id': self.id,

                })
                print(invoice,'invoice')
                self.trip_invoice_ids += invoice
                self.write({'state':'done'})



class brothersTripDateLines(models.Model):
    _name = 'brothers.trip.lines'

    trip_date_id = fields.Many2one('brothers.trip.date')
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle Id")
    vehicle_number = fields.Char(string="Vehicle Number")
    trip_rec_id = fields.Many2one('brothers.trip.sheet')
    total_bags = fields.Integer(string="Total Bags")
    total_kms = fields.Integer(string="Total Km's")
    company_type = fields.Selection([('internal', 'Internal'), ('external', 'External'), ('branches', 'Branches')],)
    internal_company = fields.Many2one('res.company', string="Internal Company")
    partner_id = fields.Many2one('res.partner', string="Vendor")
    final_invoice_amount = fields.Float(string="Final Amount")
    betta_charge = fields.Float(string="Betta Charge")
    km_charge = fields.Float(string="Km Charge")
    company_id = fields.Many2one('res.company', string="Company Name")
    create_date = fields.Date(string="Date")
    from_invoice = fields.Many2one('account.move', string="Invoice")
    type_of_charge = fields.Selection([
        ('fixed', 'Fixed'),
        ('km_price', 'Km/Price'),
    ])


