from odoo import models

class PatientReport(models.AbstractModel):
    _name = 'report.smile_hospital.report_patient_document'
    _description = 'Patient Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['patient.report.wizard'].browse(docids)
        result = []
        for wizard in docs:
            appointments = self.env['dental.appointment'].search([
                ('patient_id', '=', wizard.patient_id.id)
            ])
            result.append({
                'wizard': wizard,
                'patient': wizard.patient_id,
                'appointments': appointments,
            })
        return {
            'doc_ids': docids,
            'doc_model': 'patient.report.wizard',
            'docs': result,
        }
