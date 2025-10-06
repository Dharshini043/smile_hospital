from odoo import models, fields

class DentalDiagnosis(models.Model):
    _name = "dental.diagnosis"
    _description = "Dental Diagnosis"

    patient_id = fields.Many2one("res.partner", string="Patient", required=True, ondelete="cascade")

    # Intra oral - Hard tissue
    dental_caries = fields.Text(string="Dental Caries")
    filling = fields.Text(string="Filling")
    missing = fields.Text(string="Missing Teeth")
    other_findings = fields.Text(string="Other Findings")

    # Intra oral - Soft tissue
    soft_tissue = fields.Text(string="Soft Tissue Findings")

    # Extra oral findings
    extra_oral_findings = fields.Text(string="Extra Oral Findings")

    # Treatment plan
    treatment_plan = fields.Text(string="Treatment Plan")

    # Optional PDF upload
    treatment_plan_pdf = fields.Binary(string="Treatment Plan (PDF)")
    treatment_plan_pdf_name = fields.Char(string="Filename")
