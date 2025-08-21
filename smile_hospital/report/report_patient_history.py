from odoo import models, api
from datetime import datetime, timedelta

class ReportPatientHistory(models.AbstractModel):
    _name = 'report.smile_hospital.report_patient_history_template'
    _description = 'Patient History Report'


    @api.model
    def _get_report_values(self, docids, data=None):
        patients = self.env['res.partner'].browse(docids)

        for patient in patients:
            prescriptions = self.env['dental.prescription'].search([
                ('patient_id', '=', patient.id)
            ])
            invoices = self.env['account.move'].search([
                ('partner_id', '=', patient.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ])
            payments = self.env['account.payment'].search([
                ('partner_id', '=', patient.id)
            ])

        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'docs': patients,
            'prescriptions': prescriptions,
            'invoices': invoices,
            'payments': payments,
        }
