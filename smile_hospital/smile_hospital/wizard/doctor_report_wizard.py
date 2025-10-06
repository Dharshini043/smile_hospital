from odoo import api, fields, models
from odoo.exceptions import UserError


class DoctorReportWizard(models.TransientModel):
    _name = 'doctor.report.wizard'
    _description = 'Doctor Wise Treatment Report Wizard'

    doctor_id = fields.Many2one(
        'hr.employee',
        domain=[('is_dentist', '=', True)],
        string="Doctor",
        help="Filter report for a specific doctor"
    )
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def action_print_pdf(self):
        domain = []
        if self.doctor_id:
            domain.append(('prescribed_doctor_id', '=', self.doctor_id.id))
        if self.start_date:
            domain.append(('prescription_date', '>=', self.start_date))
        if self.end_date:
            domain.append(('prescription_date', '<=', self.end_date))

        prescriptions = self.env['dental.prescription'].search(domain)

        if not prescriptions:
            raise UserError("No prescriptions found for the selected criteria.")

        # ✅ push filters into context (not data)
        return self.with_context(
            report_doctor=self.doctor_id.name if self.doctor_id else "All Doctors",
            report_start_date=self.start_date,
            report_end_date=self.end_date,
        ).env.ref(
            'smile_hospital.action_report_doctor_treatment_pdf'
        ).report_action(prescriptions)
