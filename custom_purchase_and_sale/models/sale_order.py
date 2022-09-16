# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    x_branch_order_id = fields.Many2one(comodel_name="sale.order", string="Orden sucursal", copy=False)

    def write(self, values):
        res = super(SaleOrder, self).write(values)
        for rec in self:
            if rec.x_branch_order_id:
                if values.get("crm_status_history"):
                    rec.x_branch_order_id.sudo().write({'crm_status_history': [(0, 0, {'status': values.get("estatus_crm"), 'date': datetime.datetime.now()})]})
                if values.get("estatus_crm"):
                    rec.x_branch_order_id.sudo().write({'estatus_crm': values.get("estatus_crm")})
        return res

    def action_confirm(self):
        for rec in self:
            mrp_lines = rec.order_line.filtered(lambda line: 'Fabricar' in line.product_id.route_ids.mapped('name'))
            rule_id = rec.env["branch.factory"].sudo().search([("branch_id.id","=",rec.company_id.id)], limit=1)
            if rule_id:
                rec.p_ask_for_send_to_crm = False

            res = super(SaleOrder, rec).action_confirm()
            if rule_id:
                purchase_id = (rec.procurement_group_id.stock_move_ids.created_purchase_line_id.order_id | rec.procurement_group_id.stock_move_ids.move_orig_ids.purchase_line_id.order_id).ids
                purchase_id = self.env["purchase.order"].sudo().browse(purchase_id)
                purchase_id = purchase_id[0] if purchase_id else rec.create_branch_purchase_order(rule_id, mrp_lines)
                if purchase_id:
                    purchase_id.write({'department_id': rule_id.department_id.id, 'partner_ref': rec.name,'user_id':rec.user_id.id})
                    purchase_id.button_confirm()
                    sale = rec.create_factory_sale_order(rule_id, purchase_id)
                    if self.partner_shipping_id.id != self.company_id.partner_id.id:
                        self.picking_ids.action_cancel()
                        for line in self.order_line:
                            purchase_line = purchase_id.order_line.filtered(lambda p_line: p_line.product_id.id == line.product_id.id and line.product_uom_qty == p_line.product_qty)
                            purchase_line["sale_line_id"] = line.id
            return res

    def create_branch_purchase_order(self, rule_id, mrp_lines):
        if self.partner_id.x_studio_es_paciente and mrp_lines and rule_id:
            purchase_data = {
                "partner_id": rule_id.factory_id.partner_id.id,
                "company_id": self.company_id.id,
                "partner_ref": self.name,
                "department_id": rule_id.department_id.id,
                "user_id": self.user_id.id
            }
            purchase_id = self.env["purchase.order"].sudo().create(purchase_data)
            for order_line in mrp_lines:
                purchase_line = {
                    "product_id": order_line.product_id.id,
                    "product_qty": order_line.product_uom_qty,
                    "product_uom": order_line.product_uom.id,
                }
                purchase_id.order_line = [(0, 0, purchase_line)]
            return purchase_id

    def create_factory_sale_order(self,rule_id, purchase_id):
        if not self.partner_id.id_crm:
            raise ValidationError(f"El paciente {self.partner_id} no cuenta con un id de CRM, favor de sincronizar e intentar de nuevo.")
        sale_data = {
            "partner_id": self.company_id.partner_id.id,
            "partner_shipping_id": self.partner_shipping_id.id,
            "branch_id": self.company_id.partner_id.id,
            "x_studio_selection_field_waqzv": "Otros",
            "company_id": rule_id.factory_id.id,
            "team_id": False,
            "observations": self.observations,
            "user_id": self.user_id.id,
            "p_ask_for_send_to_crm": False,
            "client_order_ref": purchase_id.name,
            "payment_term_id": self.payment_term_id.id,
            "x_branch_order_id": self.id
        }
        sale_order = self.env["sale.order"].sudo().create(sale_data)
        for order_line in purchase_id.order_line:
            sale_line = {
                "product_id": order_line.product_id.id,
                "product_uom_qty": order_line.product_uom_qty,
                "product_uom": order_line.product_uom.id,
            }
            sale_order.order_line = [(0,0,sale_line)]

        confirme_send_obj = self.env["crm.confirm.send"].sudo().create({"sale_order": sale_order.id, "x_is_branch_order":True})
        notification = confirme_send_obj.sudo().send_to_crm()
        if notification['params']['type'] == 'success':
            self.folio_pedido = sale_order.folio_pedido
            self.estatus_crm = sale_order.estatus_crm
            self.crm_status_history = sale_order.crm_status_history
        return notification