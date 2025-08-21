from odoo import models, fields

class DentalProcedure(models.Model):
    _name = 'dental.procedure'
    _description = 'Dental Procedure'

    date = fields.Date(string='Date', required=True)

    doctor_id = fields.Many2one(
        'hr.employee',
        string='Doctor',
        domain=[('is_dentist', '=', True)],
        required=True
    )

    status = fields.Selection([
        ('incomplete', 'Incomplete'),
        ('cancel', 'Cancel'),
        ('done', 'Done'),
    ], string='Status', default='', required=True)

    reason = fields.Text(string='Procedure Reason')
    patient_id = fields.Many2one('res.partner', string="Patient", domain=[('is_patient', '=', True)])
    treatment_id = fields.Many2one('dental.treatment', string="Treatment")
    treatment_cost = fields.Float(
        string="Treatment Cost",
        related="treatment_id.cost",
        store=True
    )