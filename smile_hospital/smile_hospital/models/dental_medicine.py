# -*- coding: utf-8 -*-

from odoo import fields, models,api


class DentalMedicine(models.Model):
    """For creating the medicines used in the dental clinic"""
    _inherit = 'product.template'

    is_medicine = fields.Boolean('Is Medicine',
                                 help="If the product is a Medicine")
    generic_name = fields.Char(string="Generic Name",

                               help="Generic name of the medicament")
    dosage_strength = fields.Integer(string="Dosage Strength",

                                     help="Dosage strength of medicament")

    @api.onchange('is_medicine')
    def _onchange_is_medicine(self):
        """When ticking 'Is Medicine', set default UoM to Tablet"""
        if self.is_medicine:
            tablet_uom = self.env.ref('smile_hospital.uom_tablet', raise_if_not_found=False)
            if tablet_uom:
                self.uom_id = tablet_uom.id
                self.uom_po_id = tablet_uom.id  # purchase UoM also