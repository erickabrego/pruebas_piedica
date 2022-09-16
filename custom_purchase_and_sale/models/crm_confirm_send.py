from odoo import api, fields, models

class CRMConfirmSend(models.TransientModel):
    _inherit = 'crm.confirm.send'

    x_is_branch_order = fields.Boolean(string="Orden sucursal?")

    #Se modifica la función para poder seguir el flujo de crm dentro de odoo por medio de sucursal y fabrica
    def _validate_order_data(self, data):
        if self.x_is_branch_order:
            gender = self.sale_order.partner_shipping_id.x_studio_gnero
            data["datos_paciente"] = {
                'nombre': str(self.sale_order.partner_shipping_id.name).upper(),
                'a_paterno': '',
                'a_materno': '',
                'sexo': str(dict(self.sale_order.partner_shipping_id._fields["x_studio_gnero"].selection).get(gender)).upper(),
                'fecha_nacimiento': self.sale_order.partner_shipping_id.x_studio_cumpleaos,
                'email': self.sale_order.partner_shipping_id.email,
                'telefono': self.sale_order.partner_shipping_id.phone,
                'celular': self.sale_order.partner_shipping_id.mobile,
                'estatura': self.sale_order.partner_shipping_id.x_studio_altura_cm,
                'peso': self.sale_order.partner_shipping_id.x_studio_peso_kgs,
                'id_tallacalzado': float(self.sale_order.partner_shipping_id.x_studio_talla),
                'id_sucursal': self.sale_order.branch_id.id,
                "nombre_prescripcion": "",
                "link_prescripcion":""
            }
        res = super(CRMConfirmSend, self)._validate_order_data(data)
        return res


