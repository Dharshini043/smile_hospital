from odoo import models, fields

class PatientReportWizard(models.TransientModel):
    _name = "patient.report.wizard"
    _description = "Patient Report Wizard"

    patient_id = fields.Many2one(
        'res.partner',
        string="Patient",
        domain=[('is_patient', '=', True)],  # if you have a flag for patients
        required=True
    )

    def action_print_report(self):
        return self.env.ref('smile_hospital.action_patient_report').report_action(self)