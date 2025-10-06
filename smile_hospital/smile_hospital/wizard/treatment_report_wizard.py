from odoo import models, fields, api
from odoo.exceptions import UserError


class TreatmentReportWizard(models.TransientModel):
    _name = "treatment.report.wizard"
    _description = "Treatment Report Wizard"

    treatment_id = fields.Many2one("dental.treatment", string="Treatment")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")

    def action_print_pdf(self):
        domain = []
        if self.treatment_id:
            domain.append(('treatment_id', '=', self.treatment_id.id))
        if self.start_date:
            domain.append(('prescription_date', '>=', self.start_date))
        if self.end_date:
            domain.append(('prescription_date', '<=', self.end_date))

        prescriptions = self.env['dental.prescription'].search(domain)

        if not prescriptions:
            raise UserError("No prescriptions found for the selected criteria.")

        # Enrich each prescription with payment info
        for pres in prescriptions:
            self._calculate_payment_info(pres)

        # ✅ Compute totals
        total_cost = sum(prescriptions.mapped("treatment_cost"))
        total_paid = sum(prescriptions.mapped("amount_paid"))
        total_balance = total_cost - total_paid

        # ✅ add wizard filters + totals into context
        ctx = dict(self.env.context,
                   report_start_date=self.start_date,
                   report_end_date=self.end_date,
                   report_total_cost=total_cost,
                   report_total_paid=total_paid,
                   report_total_balance=total_balance)

        return self.with_context(ctx).env.ref(
            'smile_hospital.action_report_treatment_pdf'
        ).report_action(prescriptions)

    def _calculate_payment_info(self, prescription):
        total_cost = 0.0
        total_paid = 0.0

        # Loop through all treatments in the prescription
        for treatment in prescription.treatment_id:
            treatment_cost = treatment.cost or 0.0
            total_cost += treatment_cost

            payments = self.env['account.payment']
            if prescription.treatment_invoice_id:
                payments = self.env['account.payment'].search([
                    ('move_id', '=', prescription.treatment_invoice_id.id)
                ])

            # Fallback: search payments by partner + treatment name
            if not payments:
                payments = self.env['account.payment'].search([
                    ('partner_id', '=', prescription.patient_id.id),
                    ('treatment_name', '=', treatment.name)
                ])

            amount_paid = sum(payments.mapped('amount'))

            # Cap at treatment cost
            if amount_paid >= treatment_cost:
                amount_paid = treatment_cost

            total_paid += amount_paid

        # Save totals on prescription (for report)
        prescription.treatment_cost = total_cost
        prescription.amount_paid = total_paid

        return prescription
