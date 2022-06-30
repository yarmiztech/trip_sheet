from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class SaleEstimateLines(models.Model):
    _inherit = "sale.estimate.lines"

    addition_price = fields.Float(string="Additional Price")
    basic_km = fields.Float(string="Basic KM")
    no_of_times = fields.Integer(string="No of Times", default=1)
    bag_sum = fields.Float(string="Trip Amount", compute='compute_trip_amount')
    trip_amount = fields.Float(string="Trip Amount", compute='compute_trip_amount')
    trip_config = fields.Many2one('basic.trip')

    @api.depends('trip_amount', 'no_of_times', 'addition_price', 'sub_customers', 'basic_km')
    def compute_trip_amount(self):
        for each in self:
            print('ffffff')
            each.bag_sum = 0
            each.trip_amount = 0
            for lines in each.sub_customers:
                each.bag_sum += lines.quantity
            each.trip_amount = each.bag_sum
            basic_config = self.env['basic.trip'].search(
                [('from_kilo_meter', '<=', self.basic_km), ('to_kilo_meter', '>=', self.basic_km)])
            if basic_config:
                self.trip_config = basic_config
                if each.trip_amount > basic_config.basic_bags:
                    extra_bags = each.trip_amount - basic_config.basic_bags
                    extra_add = extra_bags * basic_config.additional_price
                    self.trip_amount = basic_config.price + extra_add + each.addition_price
                if each.trip_amount < basic_config.basic_bags:
                    self.trip_amount = basic_config.price + each.addition_price


class SaleEstimate(models.Model):
    _inherit = 'sale.estimate'

    def action_approve(self):
        res = super(SaleEstimate, self).action_approve()
        for line in self.estimate_ids:
            # fleet = self.env['fleet.vehicle'].sudo().search([('license_plate', '=', line.vehicle_number)])

            self.env['brothers.trip.sheet'].create({
                'vehicle_id': line.vahicle.id,
                'vehicle_number': line.vahicle.license_plate,
                'total_bags': line.bag_sum,
                'estimate_id': self.id,
                'total_kms': line.basic_km,
                # 'company_type':line.vahicle.type or False,
                'internal_company': line.vahicle.company_id.id or False,
                'partner_id': line.vahicle.company_id.partner_id.id,
                'company_id': self.company_id.id,
                'create_date': datetime.today().date(),
                # 'betta_charge':basic_config.price,
                # 'type_of_charge':fleet.type_of_charge,
                # 'km_charge':km_charge,
                'from_invoice': self.invoice_ids.filtered(lambda a: a.company_id == line.company_ids[0]).id,
                'final_invoice_amount': line.trip_amount
            })


class SalesReportComp(models.Model):
    _inherit = "sale.report.custom"

    @api.onchange('from_date', 'product_categ', 'product_groups', 'product_ids', 'product_type', 'style', 'month',
                  'product_group', 'product_id', 'to_date', 'report_type', 'area', 'partner_id', 'vehicle_id')
    def onchange_form_date(self):
        if self.style != 'monthly':

            self.report_lines = False
            if self.report_type == 'area':
                self.report_lines = False
                if self.area:
                    if self.product_groups and not self.product_ids and not self.product_categ:

                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('area', '=', self.area.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                product_line = (0, 0, {
                                    'date': each_coll.date,
                                    'address': each_coll.address,
                                    'invoice_id': each_coll.invoice_id.id,
                                    'partner_id': each_coll.partner_id.id,
                                    'product_id': each_coll.product_id.id,
                                    'company_id': each_coll.company_id.id,
                                    'price_units': each_coll.price_units,
                                    'uom': each_coll.uom.id,
                                    'rate': each_coll.rate,
                                    'credit': each_coll.credit,
                                    'area': each_coll.area.id,
                                    'debit': each_coll.debit,
                                    'in_vehicle_id': self.vehicle_id.license_plate,
                                    'transport_receipt': each_coll.transport_receipt,
                                    'gate_pass': each_coll.gate_pass,
                                    'location': each_coll.location,
                                    'description': each_coll.description,
                                    'account_journal': each_coll.account_journal.id,
                                    'account': each_coll.account.id,
                                    'paid_date': each_coll.paid_date

                                })
                                today_total_cheques.append(product_line)
                    elif self.product_ids and not self.product_categ and not self.product_groups:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('product_id', '=', self.product_ids.id), ('company_id', '=', 1),
                                 ('area', '=', self.area.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'address': each_coll.address,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'debit': each_coll.debit,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'transport_receipt': each_coll.transport_receipt,
                                'gate_pass': each_coll.gate_pass,
                                'location': each_coll.location,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                    elif self.product_categ and not self.product_ids and not self.product_groups:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('area', '=', self.area.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.categ_id == self.product_categ:
                                product_line = (0, 0, {
                                    'date': each_coll.date,
                                    'address': each_coll.address,
                                    'invoice_id': each_coll.invoice_id.id,
                                    'partner_id': each_coll.partner_id.id,
                                    'product_id': each_coll.product_id.id,
                                    'company_id': each_coll.company_id.id,
                                    'price_units': each_coll.price_units,
                                    'uom': each_coll.uom.id,
                                    'rate': each_coll.rate,
                                    'credit': each_coll.credit,
                                    'in_vehicle_id': self.vehicle_id.license_plate,
                                    'transport_receipt': each_coll.transport_receipt,
                                    'gate_pass': each_coll.gate_pass,
                                    'location': each_coll.location,
                                    'area': each_coll.area.id,
                                    'debit': each_coll.debit,
                                    'description': each_coll.description,
                                    'account_journal': each_coll.account_journal.id,
                                    'account': each_coll.account.id,
                                    'paid_date': each_coll.paid_date

                                })
                                today_total_cheques.append(product_line)
                    elif self.product_groups and self.product_categ and not self.product_ids:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('area', '=', self.area.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                if each_coll.product_id.categ_id == self.product_categ:
                                    product_line = (0, 0, {
                                        'date': each_coll.date,
                                        'address': each_coll.address,
                                        'invoice_id': each_coll.invoice_id.id,
                                        'partner_id': each_coll.partner_id.id,
                                        'product_id': each_coll.product_id.id,
                                        'company_id': each_coll.company_id.id,
                                        'price_units': each_coll.price_units,
                                        'uom': each_coll.uom.id,
                                        'rate': each_coll.rate,
                                        'credit': each_coll.credit,
                                        'area': each_coll.area.id,
                                        'in_vehicle_id': self.vehicle_id.license_plate,
                                        'transport_receipt': each_coll.transport_receipt,
                                        'gate_pass': each_coll.gate_pass,
                                        'location': each_coll.location,
                                        'debit': each_coll.debit,
                                        'description': each_coll.description,
                                        'account_journal': each_coll.account_journal.id,
                                        'account': each_coll.account.id,
                                        'paid_date': each_coll.paid_date

                                    })
                                    today_total_cheques.append(product_line)
                    elif self.product_groups and self.product_categ and self.product_ids:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('product_id', '=', self.product_ids.id), ('company_id', '=', 1),
                                 ('area', '=', self.area.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                if each_coll.product_id.categ_id == self.product_categ:
                                    product_line = (0, 0, {
                                        'date': each_coll.date,
                                        'address': each_coll.address,
                                        'invoice_id': each_coll.invoice_id.id,
                                        'partner_id': each_coll.partner_id.id,
                                        'product_id': each_coll.product_id.id,
                                        'company_id': each_coll.company_id.id,
                                        'price_units': each_coll.price_units,
                                        'uom': each_coll.uom.id,
                                        'rate': each_coll.rate,
                                        'credit': each_coll.credit,
                                        'area': each_coll.area.id,
                                        'debit': each_coll.debit,
                                        'in_vehicle_id': self.vehicle_id.license_plate,
                                        'transport_receipt': each_coll.transport_receipt,
                                        'gate_pass': each_coll.gate_pass,
                                        'location': each_coll.location,
                                        'description': each_coll.description,
                                        'account_journal': each_coll.account_journal.id,
                                        'account': each_coll.account.id,
                                        'paid_date': each_coll.paid_date

                                    })
                                    today_total_cheques.append(product_line)
                    elif self.product_groups and not self.product_categ and self.product_ids:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('product_id', '=', self.product_ids.id), ('company_id', '=', 1),
                                 ('area', '=', self.area.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                product_line = (0, 0, {
                                    'date': each_coll.date,
                                    'address': each_coll.address,
                                    'invoice_id': each_coll.invoice_id.id,
                                    'partner_id': each_coll.partner_id.id,
                                    'product_id': each_coll.product_id.id,
                                    'company_id': each_coll.company_id.id,
                                    'price_units': each_coll.price_units,
                                    'uom': each_coll.uom.id,
                                    'rate': each_coll.rate,
                                    'credit': each_coll.credit,
                                    'area': each_coll.area.id,
                                    'in_vehicle_id': self.vehicle_id.license_plate,
                                    'transport_receipt': each_coll.transport_receipt,
                                    'gate_pass': each_coll.gate_pass,
                                    'location': each_coll.location,
                                    'debit': each_coll.debit,
                                    'description': each_coll.description,
                                    'account_journal': each_coll.account_journal.id,
                                    'account': each_coll.account.id,
                                    'paid_date': each_coll.paid_date

                                })
                                today_total_cheques.append(product_line)




                    else:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('area', '=', self.area.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'address': each_coll.address,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'credit': each_coll.credit,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'transport_receipt': each_coll.transport_receipt,
                                'gate_pass': each_coll.gate_pass,
                                'location': each_coll.location,
                                'area': each_coll.area.id,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)

                else:
                    today_total_cheques = []
                    for each_coll in self.env['partner.ledgers.customer'].search(
                            [('company_id', '=', 1), ('date', '>=', self.from_date),
                             ('date', '<=', self.to_date)]):
                        product_line = (0, 0, {
                            'date': each_coll.date,
                            'invoice_id': each_coll.invoice_id.id,
                            'address': each_coll.address,
                            'partner_id': each_coll.partner_id.id,
                            'product_id': each_coll.product_id.id,
                            'company_id': each_coll.company_id.id,
                            'price_units': each_coll.price_units,
                            'uom': each_coll.uom.id,
                            'rate': each_coll.rate,
                            'credit': each_coll.credit,
                            'area': each_coll.area.id,
                            'debit': each_coll.debit,
                            'in_vehicle_id': self.vehicle_id.license_plate,
                            'transport_receipt': each_coll.transport_receipt,
                            'gate_pass': each_coll.gate_pass,
                            'location': each_coll.location,
                            'description': each_coll.description,
                            'account_journal': each_coll.account_journal.id,
                            'account': each_coll.account.id,
                            'paid_date': each_coll.paid_date

                        })
                        today_total_cheques.append(product_line)
                self.report_lines = today_total_cheques
            if self.report_type == 'partner':
                self.report_lines = False
                if self.partner_id:
                    if self.product_groups and not self.product_ids and not self.product_categ:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('partner_id', '=', self.partner_id.id),
                                 ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                product_line = (0, 0, {
                                    'date': each_coll.date,
                                    'address': each_coll.address,
                                    'invoice_id': each_coll.invoice_id.id,
                                    'partner_id': each_coll.partner_id.id,
                                    'product_id': each_coll.product_id.id,
                                    'company_id': each_coll.company_id.id,
                                    'price_units': each_coll.price_units,
                                    'uom': each_coll.uom.id,
                                    'rate': each_coll.rate,
                                    'in_vehicle_id': self.vehicle_id.license_plate,
                                    'transport_receipt': each_coll.transport_receipt,
                                    'gate_pass': each_coll.gate_pass,
                                    'location': each_coll.location,
                                    'credit': each_coll.credit,
                                    'area': each_coll.area.id,
                                    'debit': each_coll.debit,
                                    'description': each_coll.description,
                                    'account_journal': each_coll.account_journal.id,
                                    'account': each_coll.account.id,
                                    'paid_date': each_coll.paid_date

                                })
                                today_total_cheques.append(product_line)
                    elif self.product_ids and not self.product_categ and not self.product_groups:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('product_id', '=', self.product_ids.id), ('company_id', '=', 1),
                                 ('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'address': each_coll.address,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'debit': each_coll.debit,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'transport_receipt': each_coll.transport_receipt,
                                'gate_pass': each_coll.gate_pass,
                                'location': each_coll.location,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                    elif self.product_categ and not self.product_ids and not self.product_groups:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('partner_id', '=', self.partner_id.id),
                                 ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.categ_id == self.product_categ:
                                product_line = (0, 0, {
                                    'date': each_coll.date,
                                    'address': each_coll.address,
                                    'invoice_id': each_coll.invoice_id.id,
                                    'partner_id': each_coll.partner_id.id,
                                    'product_id': each_coll.product_id.id,
                                    'company_id': each_coll.company_id.id,
                                    'price_units': each_coll.price_units,
                                    'uom': each_coll.uom.id,
                                    'rate': each_coll.rate,
                                    'credit': each_coll.credit,
                                    'area': each_coll.area.id,
                                    'debit': each_coll.debit,
                                    'in_vehicle_id': self.vehicle_id.license_plate,
                                    'transport_receipt': each_coll.transport_receipt,
                                    'gate_pass': each_coll.gate_pass,
                                    'location': each_coll.location,
                                    'description': each_coll.description,
                                    'account_journal': each_coll.account_journal.id,
                                    'account': each_coll.account.id,
                                    'paid_date': each_coll.paid_date

                                })
                                today_total_cheques.append(product_line)
                    elif self.product_groups and self.product_categ and not self.product_ids:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('partner_id', '=', self.partner_id.id),
                                 ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                if each_coll.product_id.categ_id == self.product_categ:
                                    product_line = (0, 0, {
                                        'date': each_coll.date,
                                        'address': each_coll.address,
                                        'invoice_id': each_coll.invoice_id.id,
                                        'partner_id': each_coll.partner_id.id,
                                        'product_id': each_coll.product_id.id,
                                        'company_id': each_coll.company_id.id,
                                        'price_units': each_coll.price_units,
                                        'uom': each_coll.uom.id,
                                        'rate': each_coll.rate,
                                        'in_vehicle_id': self.vehicle_id.license_plate,
                                        'transport_receipt': each_coll.transport_receipt,
                                        'gate_pass': each_coll.gate_pass,
                                        'location': each_coll.location,
                                        'credit': each_coll.credit,
                                        'area': each_coll.area.id,
                                        'debit': each_coll.debit,
                                        'description': each_coll.description,
                                        'account_journal': each_coll.account_journal.id,
                                        'account': each_coll.account.id,
                                        'paid_date': each_coll.paid_date

                                    })
                                    today_total_cheques.append(product_line)
                    elif self.product_groups and self.product_categ and self.product_ids:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('product_id', '=', self.product_ids.id), ('company_id', '=', 1),
                                 ('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                if each_coll.product_id.categ_id == self.product_categ:
                                    product_line = (0, 0, {
                                        'date': each_coll.date,
                                        'address': each_coll.address,
                                        'invoice_id': each_coll.invoice_id.id,
                                        'partner_id': each_coll.partner_id.id,
                                        'product_id': each_coll.product_id.id,
                                        'company_id': each_coll.company_id.id,
                                        'price_units': each_coll.price_units,
                                        'uom': each_coll.uom.id,
                                        'rate': each_coll.rate,
                                        'credit': each_coll.credit,
                                        'in_vehicle_id': self.vehicle_id.license_plate,
                                        'transport_receipt': each_coll.transport_receipt,
                                        'gate_pass': each_coll.gate_pass,
                                        'location': each_coll.location,
                                        'area': each_coll.area.id,
                                        'debit': each_coll.debit,
                                        'description': each_coll.description,
                                        'account_journal': each_coll.account_journal.id,
                                        'account': each_coll.account.id,
                                        'paid_date': each_coll.paid_date

                                    })
                                    today_total_cheques.append(product_line)
                    elif self.product_groups and not self.product_categ and self.product_ids:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('product_id', '=', self.product_ids.id), ('company_id', '=', 1),
                                 ('partner_id', '=', self.partner_id.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                product_line = (0, 0, {
                                    'date': each_coll.date,
                                    'address': each_coll.address,
                                    'invoice_id': each_coll.invoice_id.id,
                                    'partner_id': each_coll.partner_id.id,
                                    'product_id': each_coll.product_id.id,
                                    'company_id': each_coll.company_id.id,
                                    'price_units': each_coll.price_units,
                                    'uom': each_coll.uom.id,
                                    'in_vehicle_id': self.vehicle_id.license_plate,
                                    'transport_receipt': each_coll.transport_receipt,
                                    'gate_pass': each_coll.gate_pass,
                                    'location': each_coll.location,
                                    'rate': each_coll.rate,
                                    'credit': each_coll.credit,
                                    'area': each_coll.area.id,
                                    'debit': each_coll.debit,
                                    'description': each_coll.description,
                                    'account_journal': each_coll.account_journal.id,
                                    'account': each_coll.account.id,
                                    'paid_date': each_coll.paid_date

                                })
                                today_total_cheques.append(product_line)



                    else:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('partner_id', '=', self.partner_id.id),
                                 ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'address': each_coll.address,
                                'rate': each_coll.rate,
                                'credit': each_coll.credit,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'transport_receipt': each_coll.transport_receipt,
                                'gate_pass': each_coll.gate_pass,
                                'location': each_coll.location,
                                'area': each_coll.area.id,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                else:
                    today_total_cheques = []
                    for each_coll in self.env['partner.ledgers.customer'].search(
                            [('company_id', '=', 1), ('date', '>=', self.from_date),
                             ('date', '<=', self.to_date)]):
                        product_line = (0, 0, {
                            'date': each_coll.date,
                            'invoice_id': each_coll.invoice_id.id,
                            'partner_id': each_coll.partner_id.id,
                            'product_id': each_coll.product_id.id,
                            'company_id': each_coll.company_id.id,
                            'price_units': each_coll.price_units,
                            'address': each_coll.address,
                            'uom': each_coll.uom.id,
                            'rate': each_coll.rate,
                            'in_vehicle_id': self.vehicle_id.license_plate,
                            'transport_receipt': each_coll.transport_receipt,
                            'gate_pass': each_coll.gate_pass,
                            'location': each_coll.location,
                            'credit': each_coll.credit,
                            'area': each_coll.area.id,
                            'debit': each_coll.debit,
                            'description': each_coll.description,
                            'account_journal': each_coll.account_journal.id,
                            'account': each_coll.account.id,
                            'paid_date': each_coll.paid_date

                        })
                        today_total_cheques.append(product_line)
                self.report_lines = today_total_cheques
            if self.report_type == 'vehicle':
                self.report_lines = False
                if self.vehicle_id:
                    if self.product_groups and not self.product_ids and not self.product_categ:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('vehicle_id', '=', self.vehicle_id.id),
                                 ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                product_line = (0, 0, {
                                    'date': each_coll.date,
                                    'address': each_coll.address,
                                    'invoice_id': each_coll.invoice_id.id,
                                    'partner_id': each_coll.partner_id.id,
                                    'product_id': each_coll.product_id.id,
                                    'company_id': each_coll.company_id.id,
                                    'price_units': each_coll.price_units,
                                    'uom': each_coll.uom.id,
                                    'rate': each_coll.rate,
                                    'credit': each_coll.credit,
                                    'area': each_coll.area.id,
                                    'debit': each_coll.debit,
                                    'in_vehicle_id': self.vehicle_id.license_plate,
                                    'transport_receipt':each_coll.transport_receipt,
                                    'gate_pass':each_coll.gate_pass,
                                    'location':each_coll.location,
                                    'description': each_coll.description,
                                    'account_journal': each_coll.account_journal.id,
                                    'account': each_coll.account.id,
                                    'paid_date': each_coll.paid_date

                                })
                                today_total_cheques.append(product_line)
                    elif self.product_ids and not self.product_categ and not self.product_groups:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('product_id', '=', self.product_ids.id), ('company_id', '=', 1),
                                 ('vehicle_id', '=', self.vehicle_id.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'address': each_coll.address,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'debit': each_coll.debit,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'transport_receipt': each_coll.transport_receipt,
                                'gate_pass': each_coll.gate_pass,
                                'location': each_coll.location,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                    elif self.product_categ and not self.product_ids and not self.product_groups:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('vehicle_id', '=', self.vehicle_id.id),
                                 ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.categ_id == self.product_categ:
                                product_line = (0, 0, {
                                    'date': each_coll.date,
                                    'address': each_coll.address,
                                    'invoice_id': each_coll.invoice_id.id,
                                    'partner_id': each_coll.partner_id.id,
                                    'product_id': each_coll.product_id.id,
                                    'company_id': each_coll.company_id.id,
                                    'price_units': each_coll.price_units,
                                    'uom': each_coll.uom.id,
                                    'in_vehicle_id': self.vehicle_id.license_plate,
                                    'transport_receipt':each_coll.transport_receipt,
                                    'gate_pass':each_coll.gate_pass,
                                    'location':each_coll.location,
                                    'rate': each_coll.rate,
                                    'credit': each_coll.credit,
                                    'area': each_coll.area.id,
                                    'debit': each_coll.debit,
                                    'description': each_coll.description,
                                    'account_journal': each_coll.account_journal.id,
                                    'account': each_coll.account.id,
                                    'paid_date': each_coll.paid_date

                                })
                                today_total_cheques.append(product_line)
                    elif self.product_groups and self.product_categ and not self.product_ids:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('vehicle_id', '=', self.vehicle_id.id),
                                 ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                if each_coll.product_id.categ_id == self.product_categ:
                                    product_line = (0, 0, {
                                        'date': each_coll.date,
                                        'address': each_coll.address,
                                        'invoice_id': each_coll.invoice_id.id,
                                        'partner_id': each_coll.partner_id.id,
                                        'product_id': each_coll.product_id.id,
                                        'company_id': each_coll.company_id.id,
                                        'price_units': each_coll.price_units,
                                        'uom': each_coll.uom.id,
                                        'rate': each_coll.rate,
                                        'credit': each_coll.credit,
                                        'in_vehicle_id': self.vehicle_id.license_plate,
                                        'transport_receipt': each_coll.transport_receipt,
                                        'gate_pass': each_coll.gate_pass,
                                        'location': each_coll.location,
                                        'area': each_coll.area.id,
                                        'debit': each_coll.debit,
                                        'description': each_coll.description,
                                        'account_journal': each_coll.account_journal.id,
                                        'account': each_coll.account.id,
                                        'paid_date': each_coll.paid_date

                                    })
                                    today_total_cheques.append(product_line)
                    elif self.product_groups and self.product_categ and self.product_ids:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('product_id', '=', self.product_ids.id), ('company_id', '=', 1),
                                 ('vehicle_id', '=', self.vehicle_id.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                if each_coll.product_id.categ_id == self.product_categ:
                                    product_line = (0, 0, {
                                        'date': each_coll.date,
                                        'address': each_coll.address,
                                        'invoice_id': each_coll.invoice_id.id,
                                        'partner_id': each_coll.partner_id.id,
                                        'product_id': each_coll.product_id.id,
                                        'company_id': each_coll.company_id.id,
                                        'price_units': each_coll.price_units,
                                        'uom': each_coll.uom.id,
                                        'in_vehicle_id': self.vehicle_id.license_plate,
                                        'transport_receipt': each_coll.transport_receipt,
                                        'gate_pass': each_coll.gate_pass,
                                        'location': each_coll.location,
                                        'rate': each_coll.rate,
                                        'credit': each_coll.credit,
                                        'area': each_coll.area.id,
                                        'debit': each_coll.debit,
                                        'description': each_coll.description,
                                        'account_journal': each_coll.account_journal.id,
                                        'account': each_coll.account.id,
                                        'paid_date': each_coll.paid_date

                                    })
                                    today_total_cheques.append(product_line)
                    elif self.product_groups and not self.product_categ and self.product_ids:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('product_id', '=', self.product_ids.id), ('company_id', '=', 1),
                                 ('vehicle_id', '=', self.vehicle_id.id), ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            if each_coll.product_id.parent_id == self.product_groups:
                                product_line = (0, 0, {
                                    'date': each_coll.date,
                                    'address': each_coll.address,
                                    'invoice_id': each_coll.invoice_id.id,
                                    'partner_id': each_coll.partner_id.id,
                                    'product_id': each_coll.product_id.id,
                                    'company_id': each_coll.company_id.id,
                                    'price_units': each_coll.price_units,
                                    'uom': each_coll.uom.id,
                                    'rate': each_coll.rate,
                                    'in_vehicle_id': self.vehicle_id.license_plate,
                                    'transport_receipt':each_coll.transport_receipt,
                                    'gate_pass':each_coll.gate_pass,
                                    'location':each_coll.location,
                                    'credit': each_coll.credit,
                                    'area': each_coll.area.id,
                                    'debit': each_coll.debit,
                                    'description': each_coll.description,
                                    'account_journal': each_coll.account_journal.id,
                                    'account': each_coll.account.id,
                                    'paid_date': each_coll.paid_date

                                })
                                today_total_cheques.append(product_line)

                    else:
                        today_total_cheques = []
                        for each_coll in self.env['partner.ledgers.customer'].search(
                                [('company_id', '=', 1), ('vehicle_id', '=', self.vehicle_id.id),
                                 ('date', '>=', self.from_date),
                                 ('date', '<=', self.to_date)]):
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'address': each_coll.address,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'transport_receipt':each_coll.transport_receipt,
                                'gate_pass':each_coll.gate_pass,
                                'location':each_coll.location,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                else:
                    today_total_cheques = []
                    for each_coll in self.env['partner.ledgers.customer'].search(
                            [('company_id', '=', 1), ('date', '>=', self.from_date),
                             ('date', '<=', self.to_date)]):
                        product_line = (0, 0, {
                            'date': each_coll.date,
                            'invoice_id': each_coll.invoice_id.id,
                            'partner_id': each_coll.partner_id.id,
                            'product_id': each_coll.product_id.id,
                            'company_id': each_coll.company_id.id,
                            'price_units': each_coll.price_units,
                            'uom': each_coll.uom.id,
                            'address': each_coll.address,
                            'rate': each_coll.rate,
                            'credit': each_coll.credit,
                            'area': each_coll.area.id,
                            'debit': each_coll.debit,
                            'in_vehicle_id': self.vehicle_id.license_plate,
                            'transport_receipt': each_coll.transport_receipt,
                            'gate_pass': each_coll.gate_pass,
                            'location': each_coll.location,
                            'description': each_coll.description,
                            'account_journal': each_coll.account_journal.id,
                            'account': each_coll.account.id,
                            'paid_date': each_coll.paid_date

                        })
                        today_total_cheques.append(product_line)

                self.report_lines = today_total_cheques
            if self.report_type == 'product':
                self.report_lines = False
                if self.product_id:
                    today_total_cheques = []
                    for each_coll in self.env['partner.ledgers.customer'].search(
                            [('company_id', '=', 1), ('product_id', '=', self.product_id.id),
                             ('date', '>=', self.from_date),
                             ('date', '<=', self.to_date)]):
                        product_line = (0, 0, {
                            'date': each_coll.date,
                            'invoice_id': each_coll.invoice_id.id,
                            'partner_id': each_coll.partner_id.id,
                            'product_id': each_coll.product_id.id,
                            'company_id': each_coll.company_id.id,
                            'price_units': each_coll.price_units,
                            'uom': each_coll.uom.id,
                            'in_vehicle_id': self.vehicle_id.license_plate,
                            'transport_receipt': each_coll.transport_receipt,
                            'gate_pass': each_coll.gate_pass,
                            'location': each_coll.location,
                            'address': each_coll.address,
                            'rate': each_coll.rate,
                            'credit': each_coll.credit,
                            'area': each_coll.area.id,
                            'debit': each_coll.debit,
                            'description': each_coll.description,
                            'account_journal': each_coll.account_journal.id,
                            'account': each_coll.account.id,
                            'paid_date': each_coll.paid_date

                        })
                        today_total_cheques.append(product_line)
                else:
                    today_total_cheques = []
                    for each_coll in self.env['partner.ledgers.customer'].search(
                            [('company_id', '=', 1), ('date', '>=', self.from_date),
                             ('date', '<=', self.to_date)]):
                        product_line = (0, 0, {
                            'date': each_coll.date,
                            'invoice_id': each_coll.invoice_id.id,
                            'partner_id': each_coll.partner_id.id,
                            'product_id': each_coll.product_id.id,
                            'company_id': each_coll.company_id.id,
                            'price_units': each_coll.price_units,
                            'uom': each_coll.uom.id,
                            'in_vehicle_id': self.vehicle_id.license_plate,
                            'transport_receipt': each_coll.transport_receipt,
                            'gate_pass': each_coll.gate_pass,
                            'location': each_coll.location,
                            'address': each_coll.address,
                            'rate': each_coll.rate,
                            'credit': each_coll.credit,
                            'area': each_coll.area.id,
                            'debit': each_coll.debit,
                            'description': each_coll.description,
                            'account_journal': each_coll.account_journal.id,
                            'account': each_coll.account.id,
                            'paid_date': each_coll.paid_date

                        })
                        today_total_cheques.append(product_line)

                self.report_lines = today_total_cheques
            if self.report_type == 'grouped':
                self.report_lines = False
                if self.product_group:
                    today_total_cheques = []
                    for each_coll in self.env['partner.ledgers.customer'].search(
                            [('company_id', '=', 1), ('date', '>=', self.from_date),
                             ('date', '<=', self.to_date)]):
                        if each_coll.product_id.parent_id == self.product_group:
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'address': each_coll.address,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'transport_receipt': each_coll.transport_receipt,
                                'gate_pass': each_coll.gate_pass,
                                'location': each_coll.location,
                                'rate': each_coll.rate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                else:
                    today_total_cheques = []
                    for each_coll in self.env['partner.ledgers.customer'].search(
                            [('company_id', '=', 1), ('date', '>=', self.from_date),
                             ('date', '<=', self.to_date)]):
                        product_line = (0, 0, {
                            'date': each_coll.date,
                            'invoice_id': each_coll.invoice_id.id,
                            'partner_id': each_coll.partner_id.id,
                            'product_id': each_coll.product_id.id,
                            'company_id': each_coll.company_id.id,
                            'address': each_coll.address,
                            'price_units': each_coll.price_units,
                            'uom': each_coll.uom.id,
                            'rate': each_coll.rate,
                            'in_vehicle_id': self.vehicle_id.license_plate,
                            'transport_receipt': each_coll.transport_receipt,
                            'gate_pass': each_coll.gate_pass,
                            'location': each_coll.location,
                            'credit': each_coll.credit,
                            'area': each_coll.area.id,
                            'debit': each_coll.debit,
                            'description': each_coll.description,
                            'account_journal': each_coll.account_journal.id,
                            'account': each_coll.account.id,
                            'paid_date': each_coll.paid_date

                        })
                        today_total_cheques.append(product_line)

                self.report_lines = today_total_cheques
        else:
            self.report_lines = False
            all = self.env['partner.ledgers.customer'].search([('company_id', '=', 1)]).filtered(
                lambda a: a.month == self.month)
            if all:
                if self.report_type == 'area':
                    self.report_lines = False
                    if self.area:
                        today_total_cheques = []
                        self.report_lines = False
                        for each_coll in all.filtered(lambda a: a.area == self.area):
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'transport_receipt': each_coll.transport_receipt,
                                'gate_pass': each_coll.gate_pass,
                                'location': each_coll.location,
                                'address': each_coll.address,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                    else:
                        self.report_lines = False
                        today_total_cheques = []
                        for each_coll in all:
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'address': each_coll.address,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'transport_receipt': each_coll.transport_receipt,
                                'gate_pass': each_coll.gate_pass,
                                'location': each_coll.location,
                                'rate': each_coll.rate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                    self.report_lines = today_total_cheques
                if self.report_type == 'partner':
                    self.report_lines = False
                    if self.partner_id:
                        self.report_lines = False
                        today_total_cheques = []
                        for each_coll in all.filtered(lambda a: a.partner_id == self.partner_id):
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'debit': each_coll.debit,
                                'address': each_coll.address,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'transport_receipt': each_coll.transport_receipt,
                                'gate_pass': each_coll.gate_pass,
                                'location': each_coll.location,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                    else:
                        today_total_cheques = []
                        self.report_lines = False
                        for each_coll in all:
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'credit': each_coll.credit,
                                'address': each_coll.address,
                                'area': each_coll.area.id,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                    self.report_lines = today_total_cheques
                if self.report_type == 'vehicle':
                    self.report_lines = False
                    if self.vehicle_id:
                        self.report_lines = False
                        today_total_cheques = []
                        for each_coll in all.filtered(lambda a: a.vehicle_id == self.vehicle_id):
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'address': each_coll.address,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                    else:
                        today_total_cheques = []
                        self.report_lines = False
                        for each_coll in all:
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'address': each_coll.address,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)

                    self.report_lines = today_total_cheques
                if self.report_type == 'grouped':
                    self.report_lines = False
                    if self.product_group:
                        self.report_lines = False
                        today_total_cheques = []
                        for each_coll in all:
                            if each_coll.product_id.parent_id == self.product_group:
                                product_line = (0, 0, {
                                    'date': each_coll.date,
                                    'invoice_id': each_coll.invoice_id.id,
                                    'partner_id': each_coll.partner_id.id,
                                    'product_id': each_coll.product_id.id,
                                    'company_id': each_coll.company_id.id,
                                    'price_units': each_coll.price_units,
                                    'uom': each_coll.uom.id,
                                    'rate': each_coll.rate,
                                    'in_vehicle_id': self.vehicle_id.license_plate,
                                    'credit': each_coll.credit,
                                    'area': each_coll.area.id,
                                    'address': each_coll.address,
                                    'debit': each_coll.debit,
                                    'description': each_coll.description,
                                    'account_journal': each_coll.account_journal.id,
                                    'account': each_coll.account.id,
                                    'paid_date': each_coll.paid_date

                                })
                                today_total_cheques.append(product_line)
                    else:
                        today_total_cheques = []
                        self.report_lines = False
                        for each_coll in all:
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'address': each_coll.address,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)

                    self.report_lines = today_total_cheques
                if self.report_type == 'product':
                    self.report_lines = False
                    if self.product_id:
                        self.report_lines = False
                        today_total_cheques = []
                        for each_coll in all.filtered(lambda a: a.product_id == self.product_id):
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'address': each_coll.address,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)
                    else:
                        today_total_cheques = []
                        self.report_lines = False
                        for each_coll in all:
                            product_line = (0, 0, {
                                'date': each_coll.date,
                                'invoice_id': each_coll.invoice_id.id,
                                'partner_id': each_coll.partner_id.id,
                                'product_id': each_coll.product_id.id,
                                'company_id': each_coll.company_id.id,
                                'price_units': each_coll.price_units,
                                'uom': each_coll.uom.id,
                                'rate': each_coll.rate,
                                'credit': each_coll.credit,
                                'area': each_coll.area.id,
                                'in_vehicle_id': self.vehicle_id.license_plate,
                                'address': each_coll.address,
                                'debit': each_coll.debit,
                                'description': each_coll.description,
                                'account_journal': each_coll.account_journal.id,
                                'account': each_coll.account.id,
                                'paid_date': each_coll.paid_date

                            })
                            today_total_cheques.append(product_line)

                    self.report_lines = today_total_cheques


class SalesReportCompLine(models.Model):
    _inherit = "sale.report.custom.line"

    location = fields.Char(string="Location")


class BrothersTripSheet(models.Model):
    _inherit = 'brothers.trip.sheet'

    estimate_id = fields.Many2one('sale.estimate')
    addition_price = fields.Float(string="Additional Price")
    no_of_times = fields.Integer(string="No of Times", default=1)
    def action_trip_marked(self):
        if self.partner_id:
            journal_id = self.env['account.journal'].sudo().search(
                [('name', '=', 'Tax Invoices'),('company_id', '=', self.vehicle_id.company_id.id)]).id,
            account_id = self.env['account.account'].search(
                [('name', '=', 'Purchase Expense'), ('company_id', '=', self.vehicle_id.company_id.id)])
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
                    'partner_id': self.company_id.partner_id.id,
                    'move_type': 'out_invoice',
                    'state': 'draft',
                    'company_id': self.vehicle_id.company_id.id,
                    'invoice_date': datetime.today().date(),
                    'vehicle_number': self.vehicle_number,
                    'journal_id': journal_id,
                    'invoice_line_ids': list,
                    'brothers_sheet_id': self.id,

                })
                self.trip_invoice_id = invoice
                invoice.action_post()
            else:
                raise UserError(_("Please create Product Trip Vehicle"))


    def assign_to_mtc(self):
        self.write({'state':'assign_mtc'})
        if self.estimate_id:
            for each in self.env['partner.ledger.customer'].sudo().search([('estimate_id','=',self.estimate_id.id)]):
                each.sudo().transport_receipt = self.transport_receipt
                each.sudo().gate_pass = self.gate_pass
                each.sudo().location = self.location
                for each_s in self.env['partner.ledgers.customer'].sudo().search([('invoice_id','=',each.invoice_id.id)]):
                    each_s.sudo().transport_receipt = self.transport_receipt
                    each_s.sudo().gate_pass = self.gate_pass
                    each_s.sudo().location = self.location

    @api.depends('type_of_charge','km_charge','betta_charge','total_bags','total_kms','addition_price','no_of_times')
    def _compute_invoice_amount(self):
        for each in self:
            each.final_invoice_amount = 0
            basic_config = self.env['basic.trip'].search(
                [('from_kilo_meter', '<=', each.total_kms), ('to_kilo_meter', '>=', each.total_kms)])
            if basic_config:
                # self.trip_config = basic_config
                if each.total_bags > basic_config.basic_bags:
                    extra_bags = each.total_bags - basic_config.basic_bags
                    extra_add = extra_bags * basic_config.additional_price
                    each.final_invoice_amount = basic_config.price + extra_add + each.addition_price
                if each.total_bags < basic_config.basic_bags:
                    each.final_invoice_amount = basic_config.price + each.addition_price


class PartnerLedgerCustom(models.Model):
    _inherit = 'partner.ledger.customer'

    transport_receipt = fields.Char(string='Transport Receipt no')
    gate_pass = fields.Char(string='Gate Pass No')
    location = fields.Char(string='Location')


class PartnerLedgersCustom(models.Model):
    _inherit = 'partner.ledgers.customer'

    transport_receipt = fields.Char(string='Transport Receipt no')
    gate_pass = fields.Char(string='Gate Pass No')
    location = fields.Char(string='Location')


class brothersTripDateReport(models.Model):
    _inherit = 'brothers.trip.date'

    def action_trip_marked(self):
        for partner_wise in self.date_lines.mapped('company_id'):
            list = []
            final_amount = 0
            company_id = self.env['res.company']
            vehicle_company = self.env['res.company']
            journal_id = self.env['account.journal']
            account_id = self.env['account.account']
            for all in self.date_lines:
                if all.vehicle_id:
                   vehicle_company = all.vehicle_id.company_id
                all.trip_rec_id.write({'state': 'done'})
                if all.company_id:
                    # company_id = all.internal_company
                    company_id = all.company_id
                if all.company_id == partner_wise:
                    final_amount += all.final_invoice_amount
                journal_id = self.env['account.journal'].sudo().search(
                    [('name', '=', 'Tax Invoices'), ('company_id', '=', all.vehicle_id.company_id.id)]).id,
                account_id = self.env['account.account'].search(
                    [('name', '=', 'Purchase Expense'), ('company_id', '=', all.vehicle_id.company_id.id)])

            product = self.env['product.product'].search([('name', '=', 'Trip Vehicle')])
            if product:
                # for line in self.inter_company_lines:
                dict = (0, 0, {
                    'name': product.name,
                    'account_id': account_id.id,
                    'price_unit': final_amount,
                    'quantity': 1,
                    'product_uom_id': product.uom_id.id,
                    'product_id': product.id,
                })
                list.append(dict)
            if list:
                invoice = self.env['account.move'].sudo().create({
                    # 'partner_id': self.env['res.partner'].search([('name','=','BROTHERS GROUPS OF COMPANY')]).id,
                    'partner_id': self.env['res.partner'].search([('name','=',company_id.name)]).id,
                    'move_type': 'out_invoice',
                    'state': 'draft',
                    'company_id': vehicle_company.id,
                    'invoice_date': self.create_date,
                    'journal_id': journal_id,
                    'invoice_line_ids': list,
                    # 'brothers_sheet_id': self.id,

                })
                print(invoice, 'invoice')
                invoice.action_post()
                self.trip_invoice_ids += invoice
                self.write({'state': 'done'})




class FundTransferBTCompanies(models.Model):

    _inherit = "fund.transfer.companies"
    _description = "Fund Transfer"
    _order = "id desc"


    def receiver_fund_confirmed(self):
        for line in self.fund_lines:
            stmt = self.env['account.bank.statement']
            payment_list = []
            if not stmt:
                if self.env['account.bank.statement'].search([('company_id','=',line.journal_id.company_id.id),('journal_id', '=', line.journal_id.id)]):
                    bal = self.env['account.bank.statement'].search([('company_id','=',line.journal_id.company_id.id),('journal_id', '=', line.journal_id.id)])[0].balance_end_real
                else:
                    bal = 0

                stmt = self.env['account.bank.statement'].create({'name': self.name,
                                                                  'balance_start': bal,
                                                                  'journal_id': line.journal_id.id,
                                                                  'balance_end_real': bal-line.amount

                                                                  })

            product_line = (0, 0, {
                'date': self.create_date,
                'name': self.name,
                'partner_id': line.to_journal_id.company_id.partner_id.id,
                'payment_ref': self.name,
                'amount': -line.amount
            })
            payment_list.append(product_line)
            j = self.env['account.payment.method'].search([('name', '=', 'Manual')])[0]
            journal = line.journal_id
            pay_id = self.env['account.payment'].create({'partner_id': line.to_journal_id.company_id.partner_id.id,
                                                         'amount': line.amount,
                                                         'partner_type': 'supplier',
                                                         'payment_type': 'outbound',
                                                         'payment_method_id': j.id,
                                                         'journal_id': journal.id,
                                                         'ref': 'Fund Transfer',
                                                         # 'invoice_ids': [(6, 0, check_inv.ids)]
                                                         })
            # pay_id.post()
            pay_id.action_post()
            pay_id_list = []
            # for k in pay_id.move_line_ids:
            for k in pay_id.line_ids:
                pay_id_list.append(k.id)

            stmt.line_ids = payment_list
            # stmt.move_line_ids = pay_id_list
            # stmt.button_post()
            # stmt.write({'state': 'confirm'})
            if line.journal_id.type == 'cash':
                if not self.env['cash.book.info'].sudo().search([('account', '=', line.account_id.id)]):
                    acc = self.env['account.move.line'].sudo().search([('account_id', '=', line.account_id.id)])
                    complete = sum(acc.mapped('debit')) - sum(acc.mapped('credit'))
                    acc_sub = self.env['account.move.line'].sudo().search([('account_id', '=', line.to_account.id)])
                    complete_sub = sum(acc.mapped('debit')) - sum(acc.mapped('credit'))

                else:
                    complete = self.env['cash.book.info'].sudo().search([('account', '=', line.account_id.id)])[-1].balance
                    # complete_sub = self.env['cash.book.info'].sudo().search([('account', '=', line.to_account.id)])[-1].balance

                debit = 0
                credit = 0
                complete_new = 0
                # acc = self.env['account.account']
                # if self.payment_type == 'outbound':
                # credit = self.amount
                # complete_new = complete - credit
                # acc = line.journal_id.payment_credit_account_id.id
                # if self.payment_type == 'inbound':
                #     debit = self.amount
                #     complete_new = complete + debit
                #     acc = self.journal_id.default_debit_account_id.id
                complete_new = complete
                self.env['cash.book.info'].sudo().create({
                    'date': datetime.today().date(),
                    'account_journal': line.sudo().journal_id.id,
                    # 'partner_id': line.partner_id.id,
                    'company_id': 1,
                    # 'description': self.communication,
                    'description': self.name,
                    'payment_type': 'outbound',
                    'partner_type': 'customer',
                    'debit': 0,
                    'credit': line.amount,
                    'account': line.sudo().account_id.id,
                    # 'payment_id': self.id,
                    'balance': complete_new-line.amount

                })


    def action_post(self):
        self.write({'state': 'send'})
        self.sudo().receiver_fund()
        # for line in self.fund_lines:
        #     stmt = self.env['account.bank.statement']
        #     payment_list = []
        #     if not stmt:
        #         if self.env['account.bank.statement'].search([('company_id','=',line.journal_id.company_id.id),('journal_id', '=', line.journal_id.id)]):
        #             bal = self.env['account.bank.statement'].search([('company_id','=',line.journal_id.company_id.id),('journal_id', '=', line.journal_id.id)])[0].balance_end_real
        #         else:
        #             bal = 0
        #
        #         stmt = self.env['account.bank.statement'].create({'name': self.name,
        #                                                           'balance_start': bal,
        #                                                           'journal_id': line.journal_id.id,
        #                                                           'balance_end_real': bal-line.amount
        #
        #                                                           })
        #
        #     product_line = (0, 0, {
        #         'date': self.create_date,
        #         'name': self.name,
        #         'partner_id': line.journal_id.company_id.partner_id.id,
        #         'payment_ref': self.name,
        #         'amount': -line.amount
        #     })
        #     payment_list.append(product_line)
        #     j = self.env['account.payment.method'].search([('name', '=', 'Manual')])[0]
        #     journal = line.journal_id
        #     pay_id = self.env['account.payment'].create({'partner_id': self.company_id.partner_id.id,
        #                                                  'amount': line.amount,
        #                                                  'partner_type': 'supplier',
        #                                                  'payment_type': 'outbound',
        #                                                  'payment_method_id': j.id,
        #                                                  'journal_id': journal.id,
        #                                                  'ref': 'Fund Transfer',
        #                                                  # 'invoice_ids': [(6, 0, check_inv.ids)]
        #                                                  })
        #     # pay_id.post()
        #     pay_id.action_post()
        #     pay_id_list = []
        #     # for k in pay_id.move_line_ids:
        #     for k in pay_id.line_ids:
        #         pay_id_list.append(k.id)
        #
        #     stmt.line_ids = payment_list
        #     # stmt.move_line_ids = pay_id_list
        #     # stmt.button_post()
        #     # stmt.write({'state': 'confirm'})
        #     if line.journal_id.type == 'cash':
        #         if not self.env['cash.book.info'].sudo().search([('account', '=', line.account_id.id)]):
        #             acc = self.env['account.move.line'].sudo().search([('account_id', '=', line.account_id.id)])
        #             complete = sum(acc.mapped('debit')) - sum(acc.mapped('credit'))
        #             acc_sub = self.env['account.move.line'].sudo().search([('account_id', '=', line.to_account.id)])
        #             complete_sub = sum(acc.mapped('debit')) - sum(acc.mapped('credit'))
        #
        #         else:
        #             complete = self.env['cash.book.info'].sudo().search([('account', '=', line.account_id.id)])[-1].balance
        #             # complete_sub = self.env['cash.book.info'].sudo().search([('account', '=', line.to_account.id)])[-1].balance
        #
        #         debit = 0
        #         credit = 0
        #         complete_new = 0
        #         # acc = self.env['account.account']
        #         # if self.payment_type == 'outbound':
        #         # credit = self.amount
        #         # complete_new = complete - credit
        #         # acc = line.journal_id.payment_credit_account_id.id
        #         # if self.payment_type == 'inbound':
        #         #     debit = self.amount
        #         #     complete_new = complete + debit
        #         #     acc = self.journal_id.default_debit_account_id.id
        #         complete_new = complete
        #         self.env['cash.book.info'].sudo().create({
        #             'date': datetime.today().date(),
        #             'account_journal': line.sudo().journal_id.id,
        #             # 'partner_id': line.partner_id.id,
        #             'company_id': 1,
        #             # 'description': self.communication,
        #             'description': self.name,
        #             'payment_type': 'outbound',
        #             'partner_type': 'customer',
        #             'debit': 0,
        #             'credit': line.amount,
        #             'account': line.sudo().account_id.id,
        #             # 'payment_id': self.id,
        #             'balance': complete_new
        #
        #         })

class FundReceiverCompanies(models.Model):

    _inherit = "fund.receiver.companies"

    def action_post(self):
        self.write({'state': 'done'})
        self.fund_id.write({'state':'received'})
        self.fund_id.sudo().receiver_fund_confirmed()

        # for line in self.fund_lines:
        #     self.env['bank.transfer.lines'].create({
        #         'date': datetime.today().date(),
        #         'freight_ids': self.id,
        #         'reason': line.reason,
        #         'amount': line.amount,
        #         'from_acc_company': line.from_acc_company.id,
        #         'to_acc_company': line.to_acc_company.id,
        #         'journal_id': line.journal_id.id,
        #         'account_id': line.account_id.id,
        #         'to_account': line.to_account.id,
        #         'balance': line.balance,
        #         'to_balance': line.to_balance
        #     })
        #
        #     j = self.env['account.payment.method'].search([('name', '=', 'Manual')])[0].id
        #     vals = {
        #         'journal_id': line.journal_id.id,
        #         'state': 'draft',
        #         'ref': self.name
        #     }
        #     pay_id_list = []
        #     move_id = self.env['account.move'].create(vals)
        #     label = self.name
        #     temp = (0, 0, {
        #         # 'account_id': acc.id,
        #         'account_id': line.account_id.id,
        #         'name': label,
        #         'move_id': move_id.id,
        #         'date': datetime.today().date(),
        #         # 'partner_id': line.partner_id.id,
        #         'debit': 0,
        #         'credit': line.amount,
        #     })
        #     pay_id_list.append(temp)
        #     temp = (0, 0, {
        #         'account_id': line.to_account.id,
        #         'name': label,
        #         'move_id': move_id.id,
        #         'date': datetime.today().date(),
        #         'debit': line.amount,
        #         'credit': 0,
        #     })
        #     pay_id_list.append(temp)
        #
        #     move_id.line_ids = pay_id_list
        #     move_id.action_post()
        #
        #     if line.journal_id.type == 'cash':
        #         if not self.env['cash.book.info'].search([('account', '=', line.account_id.id)]):
        #             acc = self.env['account.move.line'].sudo().search([('account_id', '=', line.account_id.id)])
        #             complete = sum(acc.mapped('debit')) - sum(acc.mapped('credit'))
        #             acc_sub = self.env['account.move.line'].sudo().search([('account_id', '=', line.to_account.id)])
        #             complete_sub = sum(acc.mapped('debit')) - sum(acc.mapped('credit'))
        #
        #         else:
        #             complete = self.env['cash.book.info'].search([('account', '=', line.account_id.id)])[-1].balance
        #             complete_sub = self.env['cash.book.info'].search([('account', '=', line.to_account.id)])[-1].balance
        #
        #         debit = 0
        #         credit = 0
        #         complete_new = 0
        #         # acc = self.env['account.account']
        #         # if self.payment_type == 'outbound':
        #         # credit = self.amount
        #         # complete_new = complete - credit
        #         # acc = line.journal_id.payment_credit_account_id.id
        #         # if self.payment_type == 'inbound':
        #         #     debit = self.amount
        #         #     complete_new = complete + debit
        #         #     acc = self.journal_id.default_debit_account_id.id
        #         complete_new = complete
        #         self.env['cash.book.info'].create({
        #             'date': datetime.today().date(),
        #             'account_journal': line.journal_id.id,
        #             # 'partner_id': line.partner_id.id,
        #             'company_id': 1,
        #             # 'description': self.communication,
        #             'description': self.name,
        #             'payment_type': 'outbound',
        #             'partner_type': 'customer',
        #             'debit': 0,
        #             'credit': line.amount,
        #             'account': line.account_id.id,
        #             # 'payment_id': self.id,
        #             'balance': complete_new
        #
        #         })

        for line in self.fund_lines:
            stmt = self.env['account.bank.statement']
            payment_list = []
            if not stmt:
                # _get_payment_info_JSON
                # bal = sum(
                #     self.env['account.move.line'].search([('journal_id', '=', line.journal_id.id)]).mapped(
                #         'debit'))
                # bal = self.env['account.bank.statement'].search([('journal_id', '=', line.journal_id.id)]).balance_end_real

                if self.env['account.bank.statement'].search([('company_id','=',line.to_journal_id.company_id.id),('journal_id', '=', line.to_journal_id.id)]):
                    bal = self.env['account.bank.statement'].search([('company_id','=',line.to_journal_id.company_id.id),('journal_id', '=', line.to_journal_id.id)])[0].balance_end_real
                else:
                    bal = 0

                stmt = self.env['account.bank.statement'].create({'name': self.name,
                                                                  'balance_start': bal,
                                                                  'journal_id': line.to_journal_id.id,
                                                                  'balance_end_real': bal+line.amount

                                                                  })
            payment_list = []
            product_line = (0, 0, {
                'date': self.create_date,
                'name': self.name,
                'partner_id': line.from_acc_company.partner_id.id,
                'payment_ref': self.name,
                'amount': line.amount
            })
            payment_list.append(product_line)
            j = self.env['account.payment.method'].search([('name', '=', 'Manual')])[0]
            journal = line.to_journal_id
            pay_id = self.env['account.payment'].create({'partner_id': line.from_acc_company.partner_id.id,
                                                         'amount': line.amount,
                                                         'partner_type': 'customer',
                                                          'payment_type': 'inbound',
                                                         'payment_method_id': j.id,
                                                         'journal_id': journal.id,
                                                         'ref': 'Fund Received',
                                                         # 'invoice_ids': [(6, 0, check_inv.ids)]
                                                         })
            # pay_id.post()
            pay_id.action_post()
            pay_id_list = []
            # for k in pay_id.move_line_ids:
            for k in pay_id.line_ids:
                pay_id_list.append(k.id)

            stmt.line_ids = payment_list
            # stmt.move_line_ids = pay_id_list
            # stmt.button_post()
            # stmt.write({'state': 'confirm'})
            if line.to_journal_id.type == 'cash' and line.to_journal_id.company_id.id == 1:
                if not self.env['cash.book.info'].sudo().search([('account', '=', line.to_account.id)]):
                    acc = self.env['account.move.line'].sudo().search([('account_id', '=', line.to_account.id)])
                    complete = sum(acc.mapped('debit')) - sum(acc.mapped('credit'))
                    # acc_sub = self.env['account.move.line'].sudo().search([('account_id', '=', line.to_account.id)])
                    # complete_sub = sum(acc.mapped('debit')) - sum(acc.mapped('credit'))

                else:
                    complete = self.env['cash.book.info'].sudo().search([('account', '=', line.to_account.id)])[-1].balance
                    complete_sub = self.env['cash.book.info'].sudo().search([('account', '=', line.to_account.id)])[-1].balance

                debit = 0
                credit = 0
                complete_new = 0
                # acc = self.env['account.account']
                # if self.payment_type == 'outbound':
                # credit = self.amount
                # complete_new = complete - credit
                # acc = line.journal_id.payment_credit_account_id.id
                # if self.payment_type == 'inbound':
                #     debit = self.amount
                #     complete_new = complete + debit
                #     acc = self.journal_id.default_debit_account_id.id
                complete_new = complete
                self.env['cash.book.info'].sudo().create({
                    'date': datetime.today().date(),
                    'account_journal': line.sudo().to_journal_id.id,
                    # 'partner_id': line.partner_id.id,
                    'company_id': 1,
                    # 'description': self.communication,
                    'description': self.name,
                    'payment_type': 'inbound',
                    'partner_type': 'customer',
                    'debit': 0,
                    'credit': line.amount,
                    'account': line.sudo().to_account.id,
                    # 'payment_id': self.id,
                    'balance': complete_new+line.amount

                })
