from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    insole_size = fields.Char(string='Talla')
    top_cover_id = fields.Many2one('product.product', string='Top Cover', domain="[('matTopLayer', '=', True), ('qty_available', '>', 0),('is_material','=',True)]")
    design_type = fields.Selection([
        ('1', 'Comfort'),
        ('2', 'Clinical'),
        ('3', 'Medical')
    ], string='Tipo de diseño')
