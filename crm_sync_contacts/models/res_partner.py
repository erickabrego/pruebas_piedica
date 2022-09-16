# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

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
