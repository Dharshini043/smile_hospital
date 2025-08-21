from odoo import models, fields,api

class AccountMove(models.Model):
    _inherit = 'account.move'

    # Boolean field to control whether this invoice should be included in the payment log
    is_treatment_invoice = fields.Boolean(string='Treatment Invoice', default=False)
    doctor_id = fields.Many2one('hr.employee', string="Prescribed Doctor")
