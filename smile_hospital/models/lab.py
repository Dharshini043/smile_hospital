from odoo import models, fields

class SmileLab(models.Model):
    _name = 'smile.lab'
    _description = 'Lab Records'
    _rec_name = "patient_id"

    patient_id = fields.Many2one(
        'res.partner',
        string="Patient",
        domain=[('is_patient', '=', True)],
        required=True
    )
    date_sent = fields.Date(string="Date Sent", required=True)
    lab_id = fields.Many2one(
        'res.partner',
        string="Lab Name",
        domain=[
            ('is_company', '=', True),
            ('category_id', '=', 'Lab')
        ],
        required=True
    )
    mode_sent = fields.Selection([
        ('impression', 'Impression'),
        ('email', 'Email'),
    ], string="Mode of Sent", required=True)
    work_type = fields.Char(string="Work Type")
    accessories_sent = fields.Text(string="Accessories Sent")
    work_received = fields.Date(string="Work Received")
    patient_delivered = fields.Date(string="Patient Delivered")
