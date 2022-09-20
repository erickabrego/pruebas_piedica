# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import logging
_logger = logging.getLogger(__name__)
import requests


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, vals_list):
        res = super(ResPartner, self).create(vals_list)
        if res.x_studio_es_paciente:
            for rec in res:
                rec.create_contact_to_crm()
        return res

    def update_crm_id(self, args):
        self.write({"id_crm": args.get("crm_id")})
        return {
            'status': 'success'
        }

    def create_crm_contact(self, args):
        try:
            id_crm = args.get('id_crm')
            if id_crm:
                crm_exist = self.sudo().search([("id_crm", "=", id_crm)], limit=1)
                if crm_exist:
                    return {
                        'status': 'error',
                        'message': f"El id {id_crm} de CRM ya existe en Odoo, favor de verificar"
                    }
            data = {
                'name': args.get("name"),
                'parent_id': int(args.get('parent_id')) if args.get('parent_id') else False,
                'id_crm': args.get('id_crm'),
                'email': args.get('email'),
                'phone': args.get('phone'),
                'mobile': args.get('mobile'),
                'company_type': 'person',
                'x_studio_es_paciente': True,
                'x_studio_cumpleaos': args.get('fecha_nac'),
                'x_studio_altura_cm': args.get('estatura'),
                'x_studio_peso_kgs': args.get('peso'),
                'type': 'private',
                'street_name': args.get('direccion'),
                'x_studio_gnero': args.get('genero'),
                'x_studio_nombre_de_la_clnica': args.get('nombre_clinica'),
                'x_studio_compaa': args.get('nombre_campaña')
            }
            partner = self.sudo().create(data)
            return {
                'status': 'success',
                "id_odoo": partner.id
            }
        except Exception as error:
            return {
                'status': 'error',
                'message': error
            }

    # Abrir el wizard de sincronización
    def sync_contact_crm(self):
        if self.name:
            name = self.name.split(" ")
            if "" in name:
                name.remove("")
            patient_vals = {
                "name": name[0] if self.name else "",
                "email": str(self.email).strip() if self.email else "",
                "birth_date": self.x_studio_cumpleaos,
                "partner_id": self.id
            }
            patient_id = self.env["res.partner.crm.sync"].sudo().create(patient_vals)
            result = patient_id.search_crm_contact()
            if result != "success":
                return result
            return {
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_model': 'res.partner.crm.sync',
                'name': _("Sincronización Odoo-CRM"),
                'res_id': patient_id.id,
                'views': [(False, 'form')],
            }

    def create_contact_to_crm(self):
        endpoint = f"https://crmpiedica.com/api/searchpatient.php"
        data = {
            "nombre": str(self.name).upper(),
            "sexo": str(dict(self._fields["x_studio_gnero"].selection).get(self.x_studio_gnero)).upper(),
            "fecha_nacimiento": str(self.x_studio_cumpleaos),
            "email": self.email,
            "telefono": self.phone,
            "celular": self.mobile,
            "estatura": self.x_studio_altura_cm,
            "peso": self.x_studio_peso_kgs,
            "talla": float(self.x_studio_talla),
            "id_sucursal": self.x_studio_sucursal.id,
            "prescripcion": "",
            "link_prescripcion": "www.google.com",
            "patologia": self.other_complaints,
            "tipo_referencia": self.x_studio_cmo_nos_contacta,
            "referencia": "www.google.com",
            "id_odoo": self.id,
            "dolores": [
                {
                    "espalda": 1 if "Dolor de espalda" in self.main_complaints.mapped("name") else 0,
                    "rodilla": 1 if "Dolor de rodillas" in self.main_complaints.mapped("name") else 0,
                    "tobillo": 1 if "Dolor de tobillos" in self.main_complaints.mapped("name") else 0,
                    "cadera": 1 if "Dolor de cadera" in self.main_complaints.mapped("name") else 0,
                    "pies": 1 if "Dolor de pies" in self.main_complaints.mapped("name") else 0
                }
            ],
            "direccion": [
                {
                    "calle": self.street,
                    "colonia": self.l10n_mx_edi_colony,
                    "municipio": self.city_id.name,
                    "ciudad": self.city_id.name,
                    "pais": self.country_id.name,
                    "estado": self.state_id.name,
                    "cp": self.zip,
                    'alias': 'DEFAULT'
                }
            ]
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(endpoint, headers=headers ,json=data)
        message = response.content.decode("utf-8")
        if response.status_code != 200:
            message = f"La creación del paciente en CRM no fue posible debido al siguiente error: {response.reason}, favor de sincronizar el contacto."
            self.message_post(message)
        elif "Error" in response.content.decode("utf-8"):
            message = f"La creación no fue posible, debido al siguiente error: {message}"
            self.message_post(message)
        else:
            message = f"La creación del contacto fue exitosa."
            self.message_post(message)