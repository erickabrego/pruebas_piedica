from odoo import api, fields, models
import requests

class SaleOrderCRMSync(models.TransientModel):
    _name = 'sale.order.crm.sync'
    _description = 'Pedidos de CRM'

    order_id = fields.Many2one(comodel_name="sale.order", string="Venta")
    name = fields.Char(string="Orden", related="order_id.name")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Cliente", related="order_id.partner_id")
    order_ids = fields.One2many("sale.order.crm.sync.line", "order_id", string="Pedidos")

    def search_crm_orders(self):
        endpoint = f"https://crmpiedica.com/api/searchorderpatient.php?id={self.partner_id.id}"
        response = requests.get(endpoint)
        response_json = response.json()
        for order in response_json:
            data = {
                "id_crm": order.get("id_pedido"),
                "order_id": self.id,
            }
            self.env["sale.order.crm.sync.line"].sudo().create(data)