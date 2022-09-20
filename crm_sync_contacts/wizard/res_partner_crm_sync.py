# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError
import requests

class ResPartnerCRMSync(models.TransientModel):
    _name = 'res.partner.crm.sync'
    _description = 'Sincronización con CRM'

    name = fields.Char(string="Nombre del paciente")
    birth_date = fields.Date(string="Fecha de nacimiento")
    email = fields.Char(string="Correo")
    patient_ids = fields.One2many("res.partner.crm.sync.line", "patient_id", string="Contactos CRM")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Paciente odoo")

    #Busqueda de los pacientes de crm
    def search_crm_contact(self):
        birthdate = self.birth_date.strftime('%Y-%m-%d') if self.birth_date else ""
        email = str(self.email).strip() if self.email else ""
        endpoint = f"https://crmpiedica.com/api/searchpatient.php?name={self.name}&birthdate={birthdate}&email={email}"
        response = requests.get(endpoint)
        response_json = response.json()
        if response.ok and response_json != "NO existe registro ...":
            for patient in response_json:
                data = {
                    "name": patient.get("nombre_completo"),
                    "crm_id": patient.get("id_paciente"),
                    "gender": patient.get("sexo"),
                    "birth_date": patient.get("fecha_nacimiento"),
                    "email": patient.get("email"),
                    "phone": patient.get("telefono"),
                    "mobile": patient.get("celular"),
                    "height": patient.get("estatura"),
                    "weight": patient.get("peso"),
                    "template_size": patient.get("id_tallacalzado"),
                }
                self.write({'patient_ids': [(0,0,data)]})
                return {
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'res_model': 'res.partner.crm.sync',
                    'name': ("Sincronización Odoo-CRM"),
                    'res_id': self.id,
                    'views': [(False, 'form')],
                }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': "No se encontraron registros con estas especificaciones.",
                }
            }

    #Relaciona el id CRM en Odoo dependiendo el paciente seleccionado
    def sync_contact_odoo(self):
        to_sync = self.patient_ids.filtered(lambda line: line.sync_id)
        patient = self.env["res.partner"].search([("id_crm","=",to_sync[0].crm_id)],limit=1)
        if to_sync:
            if patient:
                raise ValidationError(f"El paciente {patient.name} ya está sincronizado con el mismo id de CRM.")
            self.partner_id.id_crm = to_sync[0].crm_id
            return {'type': 'ir.actions.act_window_close'}