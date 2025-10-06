# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DentalPrescription(models.Model):
    """Prescription of patient from the dental clinic"""
    _name = 'dental.prescription'
    _description = "Dental Prescription"
    _inherit = ['mail.thread']
    _rec_name = "sequence_no"

    sequence_no = fields.Char(string='Sequence No', required=True,
                              readonly=True, default=lambda self: _('New'),
                              help="Sequence number of the dental prescription")
    appointment_ids = fields.Many2many('dental.appointment',
                                       string="Appointment",
                                       compute="_compute_appointment_ids",
                                       help="All appointments created")
    appointment_id = fields.Many2one('dental.appointment',
                                     string="Appointment",
                                     domain="[('id','in',appointment_ids)]",

                                     help="All appointments created")
    patient_id = fields.Many2one(related="appointment_id.patient_id",
                                 string="Patient",
                                 required=True,
                                 readonly=False,
                                 help="name of the patient")
    # token_no = fields.Integer(related="appointment_id.token_no",
    #                           string="Token Number",
    #                           help="Token number of the patient")
    treatment_id = fields.Many2many(
        'dental.treatment',
        string="Treatments",
        help="Name of the treatments done for patient"
    )

    treatment_cost = fields.Float(
        string="Treatment Cost",
        compute="_compute_treatment_cost",
        store=True,
        readonly=True
    )
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id,
                                  required=True,
                                  help="To add the currency type in cost")
    prescribed_doctor_id = fields.Many2one(related="appointment_id.dentist_id",
                                           string='Prescribed Doctor',
                                           required=True,
                                           readonly=False,
                                           help="Doctor who is prescribed")
    prescription_date = fields.Date(default=fields.date.today(),
                                    string='Prescription Date',
                                    required=True,
                                    help="Date of the prescription")
    state = fields.Selection([('new', 'New'),
                              ('done', 'Prescribed'),
                              ('invoiced', 'Invoiced')],
                             default="new",
                             string="state",
                             help="state of the appointment")
    medicine_ids = fields.One2many('dental.prescription_lines',
                                   'prescription_id',
                                   string="Medicine",
                                   help="medicines")
    invoice_data_id = fields.Many2one(comodel_name="account.move", string="Invoice Data",
                                      help="Invoice Data")
    treatment_invoice_id = fields.Many2one('account.move', string="Treatment Invoice")
    prescription_invoice_id = fields.Many2one('account.move', string="Prescription Invoice")
    selected_teeth = fields.Char(string="Selected Teeth",help="Selected Teeth")
    referred_dentist_id = fields.Many2one(
        'hr.employee', string='Referred Dentist',
        domain="[('is_dentist', '=', True)]",
        help="Select a different dentist if referring the patient"
    )
    next_appointment_date = fields.Date(
        string="Next Appointment Date",
        help="Date for the next appointment"
    )
    # treatment_cost = fields.Float(string="Treatment Cost", readonly=True)
    amount_paid = fields.Float(string="Amount Paid", readonly=True)
    balance_amount = fields.Float(string="Balance", readonly=True)
    payment_status = fields.Char(string="Payment Status", readonly=True)

    # grand_total = fields.Float(compute="_compute_grand_total",
    #                            string="Grand Total",
    #                            help="Get the grand total amount")

    @api.depends('treatment_id')
    def _compute_treatment_cost(self):
        for rec in self:
            rec.treatment_cost = sum(rec.treatment_id.mapped('cost'))

    @api.model_create_multi
    def create(self, vals):
        """Ensure the next appointment is updated/created when a prescription is created."""
        vals = vals[0]
        if vals.get('sequence_no', _('New')) == _('New'):
                vals['sequence_no'] = self.env['ir.sequence'].next_by_code('dental.prescriptions') or _('New')
        records = super(DentalPrescription, self).create(vals)
        for record in records:
            record._update_or_create_appointment()
        return records

    def write(self, vals):
        """Ensure the next appointment is updated when a prescription is modified."""
        res = super(DentalPrescription, self).write(vals)
        if 'next_appointment_date' in vals or 'referred_dentist_id' in vals:
            for record in self:
                record._update_or_create_appointment()
        return res

    def _update_or_create_appointment(self):
        """Creates a new appointment instead of modifying the current one."""
        if not self.next_appointment_date or not self.patient_id:
            return  # Skip if no next appointment date is given

        assigned_dentist = self.referred_dentist_id or self.prescribed_doctor_id
        if not assigned_dentist:
            return  # Skip if no doctor is assigned

        today_appointment = self.env['dental.appointment'].search([
            ('patient_id', '=', self.patient_id.id),
            ('appointment_date', '=', fields.Date.today()),
            ('state', '!=', 'done')
        ], limit=1)

        # Ensure that today's appointment is not modified
        if today_appointment:
            # Create a new appointment for the next visit
            self.env['dental.appointment'].create({
                'patient_id': self.patient_id.id,
                'appointment_date': self.next_appointment_date,
                'dentist_id': assigned_dentist.id,
                'state': 'draft',  # Set as draft since it's a future appointment
            })
        else:
            # If no active appointment exists today, update or create as usual
            upcoming_appointment = self.env['dental.appointment'].search([
                ('patient_id', '=', self.patient_id.id),
                ('appointment_date', '>', fields.Date.today()),
                ('state', '!=', 'done')
            ], limit=1, order="appointment_date asc")

            if upcoming_appointment:
                upcoming_appointment.write({
                    'appointment_date': self.next_appointment_date,
                    'dentist_id': assigned_dentist.id
                })
            else:
                # Create a new future appointment
                self.env['dental.appointment'].create({
                    'patient_id': self.patient_id.id,
                    'appointment_date': self.next_appointment_date,
                    'dentist_id': assigned_dentist.id,
                    'state': 'draft',
                })

    @api.depends('appointment_id')
    def _compute_appointment_ids(self):
        """Computes and assigns the `appointment_ids` field for each record.
        This method searches for all `dental.appointment` records that have
        a state of `new` and a date equal to today's date. It then updates
        the `appointment_ids` field of each `DentalPrescription` record
        with the IDs of these found appointments."""
        for rec in self:
            rec.appointment_ids = self.env['dental.appointment'].search(
                [('state', '=', 'confirmed'), ('appointment_date', '=', fields.Date.today())]).ids

    def action_prescribed(self):
        """Marks the prescription and its associated appointment as `done`.
        This method updates the state of both the DentalPrescription instance
        and its linked dental.appointment instance to `done`, indicating that
        the prescription has been finalized and the appointment has been completed.
        """
        self.state = 'done'
        self.appointment_id.state = 'done'

    def create_invoice(self):
        """Create invoices for treatments and prescribed medicines safely."""
        self.ensure_one()  # Ensure we are processing one prescription at a time

        # ---------- TREATMENT INVOICE ----------
        if not self.treatment_id:
            raise UserError(_("No treatment selected."))

        treatment_lines = []
        for treatment in self.treatment_id:
            treatment_lines.append(fields.Command.create({
                'name': treatment.name,
                'quantity': 1,
                'price_unit': treatment.cost,
            }))

        treatment_invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.id,
            'state': 'draft',
            'invoice_line_ids': treatment_lines,
            'is_treatment_invoice': True,
            'doctor_id': self.prescribed_doctor_id.id,
        }
        treatment_invoice = self.env['account.move'].create(treatment_invoice_vals)

        # ---------- MEDICINE INVOICE ----------
        medicine_lines = []
        stock_moves = []
        for line in self.medicine_ids:
            product = self.env['product.product'].search(
                [('product_tmpl_id', '=', line.medicament_id.id)], limit=1
            )
            if product:
                medicine_lines.append(fields.Command.create({
                    'product_id': product.id,
                    'name': line.display_name,
                    'quantity': line.quantity,
                    'price_unit': line.price,
                }))

                # Track stock movement for consumables
                if product.type in ('consu', 'product'):
                    stock_moves.append({
                        'product': product,
                        'quantity': line.quantity,
                    })

        if not medicine_lines:
            raise UserError(_("No valid medicines to invoice."))

        prescription_invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.patient_id.id,
            'state': 'draft',
            'invoice_line_ids': medicine_lines,
        }
        prescription_invoice = self.env['account.move'].create(prescription_invoice_vals)

        # ---------- STOCK MOVEMENT ----------
        if stock_moves:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.env.company.id)], limit=1
            )
            if not warehouse:
                raise UserError(_("No warehouse found for the company. Please configure a warehouse."))

            source_location = warehouse.lot_stock_id
            customer_location = self.env.ref('stock.stock_location_customers')

            for move in stock_moves:
                self.env['stock.move'].create({
                    'name': f'Prescription {self.sequence_no}',
                    'product_id': move['product'].id,
                    'product_uom_qty': move['quantity'],
                    'quantity': move['quantity'],
                    'product_uom': move['product'].uom_id.id,
                    'location_id': source_location.id,
                    'location_dest_id': customer_location.id,
                    'state': 'done',
                })

        # ---------- LINK INVOICES ----------
        self.invoice_data_id = treatment_invoice.id
        self.state = 'invoiced'

        # ---------- RETURN ACTION ----------
        return {
            'type': 'ir.actions.act_window',
            'name': 'Treatment & Prescription Invoices',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', [treatment_invoice.id, prescription_invoice.id])],
            'context': "{'move_type':'out_invoice'}",
        }

    def action_view_invoice(self):
        """Invoice view"""
        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_data_id.id,
        }
    def action_print_prescription(self):
        return self.env.ref('smile_hospital.report_pdf_dental_prescription').report_action(self)

    def action_open_patient_payments(self):
        self.ensure_one()
        return self.patient_id.with_context({
            'default_treatment_name': self.treatment_id.name,
            'default_treatment_cost': self.cost
        }).action_open_patient_payments()




class DentalPrescriptionLines(models.Model):
    """Prescription lines of the dental clinic prescription"""
    _name = 'dental.prescription_lines'
    _description = "Dental Prescriptions Lines"
    _rec_name = "medicament_id"

    medicament_id = fields.Many2one('product.template',
                                    domain="[('is_medicine', '=', True)]",
                                    string="Medicament",
                                    help="Name of the medicine")
    generic_name = fields.Char(string="Generic Name",
                               related="medicament_id.generic_name",
                               help="Generic name of the medicament")
    dosage_strength = fields.Integer(string="Dosage Strength",
                                     related="medicament_id.dosage_strength",
                                     help="Dosage strength of medicament")
    medicament_form = fields.Selection([('tablet', 'Tablets'),
                             ('capsule', 'Capsules'),
                             ('liquid', 'Liquid'),
                             ('injection', 'Injections')],
                            string="Medicament Form",
                            required=True,
                            help="Add the form of the medicine")
    quantity = fields.Integer(string="Quantity",
                              required=True,
                              help="Quantity of medicine")
    # frequency_id = fields.Many2one('medicine.frequency',
    #                                string="Frequency",
    #                                required=True,
    #                                help="Frequency of medicine")
    price = fields.Float(related='medicament_id.list_price',
                          string="Price",
                          help="Cost of medicine")
    prescription_id = fields.Many2one('dental.prescription',
                                      help="Relate the model with dental_prescription")
    morning = fields.Boolean(string="Morning")
    noon = fields.Boolean(string="After Noon")
    night = fields.Boolean(string="Night")
    medicine_take = fields.Selection([
        ('before', 'Before Food'),
        ('after', 'After Food')
    ], string='Medicine Take',default='after')
    days = fields.Float(string='Days')
    onhand_qty = fields.Float(
        string="On-hand Quantity",
        compute="_compute_onhand_qty",
        store=False,
        help="Available stock for the selected medicine"
    )

    @api.depends('medicament_id')
    def _compute_onhand_qty(self):
        for rec in self:
            rec.onhand_qty = 0.0
            if rec.medicament_id:
                product = self.env['product.product'].search(
                    [('product_tmpl_id', '=', rec.medicament_id.id)], limit=1
                )
                if product:
                    rec.onhand_qty = product.qty_available




