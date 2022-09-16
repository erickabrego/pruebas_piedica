import datetime

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'


    def get_available_coupon(self):
        domain = ['&', '&', '|', ('state', '=', 'new'), ('state', '=', 'sent'), ('partner_id', '=', self.id), ('p_type', '=', 'renovacion')]
        coupons = self.env['coupon.coupon'].search(domain)
        today = datetime.date.today()
        coupons_list = []

        # Los registros no se pueden obtener de manera ordenada por la fecha de
        # expiración ya que dicho campo es computado, entonces se ordenan de
        # otra manera. Se guardan los registros en una lista para poder
        # ordenarla por fecha de expiración, con la finalidad de devolver el
        # cupón con la fecha de expiración más próxima a la fecha actual
        for coupon in coupons:
            coupons_list.append(coupon)

        coupons_list.sort(key=lambda coupon: coupon.expiration_date)

        for coupon in coupons_list:
            if coupon.expiration_date >= today:
                return coupon

        return None
