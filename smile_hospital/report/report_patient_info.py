from odoo import models

class PatientReport(models.AbstractModel):
    _name = 'report.smile_hospital.report_patient_document'
    _description = 'Patient Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['patient.report.wizard'].browse(docids)

        extra_data = {}
        for wizard in docs:
            appointments = self.env['dental.appointment'].search([
                ('patient_id', '=', wizard.patient_id.id)
            ])
            extra_data[wizard.id] = {
                'appointments': appointments,
                'appointment_count': len(appointments),
            }

        return {
            'doc_ids': docids,
            'doc_model': 'patient.report.wizard',
            'docs': docs,           # keep recordset for external_layout
            'extra_data': extra_data,  # store appointments + count
        }
