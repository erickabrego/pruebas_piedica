from odoo import models, fields, api
import requests


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        for rec in self:
            if rec.state == "done" and rec.sale_id.folio_pedido:
                # Hacemos uso de la API externa para mandar la información del pedido y su etapa para marcar como enviado
                url = f"https://crmpiedica.com/api/api.php?id_pedido={rec.sale_id.folio_pedido}&id_etapa=6"
                response = requests.put(url)
                rec.sale_id.message_post(body=response.content)
                crm_status = self.env["crm.status"].search([("code", "=", "6")], limit=1)
                if crm_status:
                    rec.sale_id.write({'estatus_crm': crm_status.id})
                    rec.sale_id.create_estatus_crm()
        return res


    def add_qty_done_by_sale_line(self, sale_order_line_id, qty_done):
        self.ensure_one()

        found = False

        for move in self.move_ids_without_package:
            if move.sale_line_id.id == sale_order_line_id:
                move.write({'quantity_done': qty_done})
                found = True
                break

        if found:
            sucursal_category = self.env['res.partner.category'].search([('name', '=', 'Sucursal')])

            if (sucursal_category) and (sucursal_category[0] not in self.partner_id.category_id):
                res = self.button_validate()
