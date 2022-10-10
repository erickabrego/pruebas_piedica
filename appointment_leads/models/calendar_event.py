# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    x_sale_order_state = fields.Selection(string="Estado de orden de venta", selection=[("draft","Cotización"),("sent","Cotización enviada"),("sale","Orden de venta"),("done","Bloqueado"),("cancel","Cancelado")], compute="_get_sale_order_state",store=True)
    partner_ids = fields.Many2many(
        'res.partner', 'calendar_event_res_partner_rel',
        string='Attendees', default=False)
    x_personal_schedule_appointment = fields.Selection(string="¿Agendo cita presencial?", selection=[("Sí","Sí"),("No","No")])

    #Relaciona la oportunidad del contacto con la reuinión que se está creando
    @api.model
    def create(self, vals):
        res = super(CalendarEvent, self).create(vals)
        try:
            res.get_opportunity_partner()
        except Exception as e:
            _logger.info(e)
        return res

    def write(self, values):
        res = super(CalendarEvent, self).write(values)
        for rec in self:
            if values.get("x_studio_paciente_asisti_a_cita") and rec.x_studio_paciente_asisti_a_cita and rec.opportunity_id:
                crm_stage = self.env["crm.stage"].sudo().search([("name","=","Asiste a cita")],limit=1)
                if crm_stage:
                    rec.opportunity_id.stage_id = crm_stage.id
            elif values.get("x_personal_schedule_appointment") and rec.x_personal_schedule_appointment == "Sí" and rec.opportunity_id and rec.opportunity_id.stage_id.name == "Agenda cita virtual":
                crm_stage = self.env["crm.stage"].sudo().search([("name","=","Agenda cita")],limit=1)
                rec.opportunity_id.stage_id = crm_stage.id
            elif values.get("x_personal_schedule_appointment") and rec.x_personal_schedule_appointment == "No" and rec.opportunity_id and rec.opportunity_id.stage_id.name == "Agenda cita virtual":
                crm_stage = self.env["crm.stage"].sudo().search([("name","=","Contactado")],limit=1)
                rec.opportunity_id.stage_id = crm_stage.id
            if values.get("partner_ids"):
                try:
                    rec.get_opportunity_partner()
                except Exception as e:
                    _logger.info(e)
        return res

    @api.depends("opportunity_id","opportunity_id.order_ids","opportunity_id.order_ids.state")
    def _get_sale_order_state(self):
        for rec in self:
            if rec.opportunity_id and rec.opportunity_id.order_ids.filtered(lambda line: line.state not in ['draft', 'sent', 'cancel']):
                order_id = rec.opportunity_id.order_ids.filtered(lambda line: line.state not in ['draft', 'sent', 'cancel'])[0]
                rec.x_sale_order_state = "sale"
            elif rec.opportunity_id and rec.opportunity_id.order_ids.filtered(lambda line: line.state not in ['done', 'sale']):
                order_id = rec.opportunity_id.order_ids.filtered(lambda line: line.state not in ['done', 'sale'])[0]
                rec.x_sale_order_state = order_id.state
            else:
                rec.x_sale_order_state = False

    def get_opportunity_partner(self):
        for rec in self:
            if not rec.opportunity_id:
                partner_id = rec.partner_ids.sudo().filtered(lambda partner: partner.x_studio_es_paciente)
                stage_id = self.env["crm.stage"].sudo().search([("name", "=", "Agenda cita")], limit=1)
                if partner_id:
                    opportunity_ids = self.env["crm.lead"].sudo().search([("partner_id.id", "=", partner_id.id), (
                    "stage_id.name", "in", ["Contactado", "Cancela cita"])])
                    archived_opportunity = self.env["crm.lead"].sudo().search(
                        [("partner_id.id", "=", partner_id.id), ("active", "=", False)])
                    if opportunity_ids and stage_id:
                        for opportunity_id in opportunity_ids:
                            opportunity_id.stage_id = stage_id.id
                            rec["opportunity_id"] = opportunity_id.id
                    if archived_opportunity and stage_id:
                        for archived_oppo in archived_opportunity:
                            archived_oppo.stage_id = stage_id.id
                            archived_oppo.active = True
                            rec["opportunity_id"] = archived_opportunity.id