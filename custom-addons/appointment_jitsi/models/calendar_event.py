# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import _, api, fields, models
import uuid


class CalendarEvent(models.Model):
    """
    Inherited model to add Jitsi integration to calendar events.
    """
    _inherit = "calendar.event"

    jitsi_link = fields.Text(
        string="Jitsi Link", 
        store=True, 
        copy=True, 
        compute='_compute_jitsi_link'
    )
    
    is_jitsi = fields.Boolean(
        string="Enable Jitsi Integration", 
        default=False
    )

    def generate_jitsi_link(self):
        """
        Generate a new Jitsi link for the event.
        """
        self._compute_jitsi_link()

    def clear_jitsi_link(self):
        """
        Clear the Jitsi link for the event.
        """
        self.jitsi_link = False

    @api.depends('access_token')
    def _compute_jitsi_link(self):
        """
        Compute and set the Jitsi link based on the access token.
        """
        get_param = self.env['ir.config_parameter'].sudo().get_param
        is_jitsi_enabled = get_param('is_jitsi_param')
        company_param_id = get_param('company_param')
        company_param = self.env['res.company'].sudo().search([('id', '=', company_param_id)], limit=1)
        company_param = company_param.name if company_param else 'Record not found'
        
        if is_jitsi_enabled:
            jitsi_base_url = 'https://meet.jit.si'
            company_name = company_param
            
            for rec in self:
                if not rec.access_token:
                    rec.access_token = uuid.uuid4().hex
                rec.jitsi_link = f"{jitsi_base_url}/{company_name}/{company_name}-{rec.access_token}"
                rec.videocall_location = f"{jitsi_base_url}/{company_name}/{company_name}-{rec.access_token}"
        else:
            for rec in self:
                rec._set_discuss_videocall_location()

    def action_join_video_call(self):
        """
        Return an action to join the video call.
        """
        return {
            'type': 'ir.actions.act_url',
            'url': self.jitsi_link if self.is_jitsi else self.videocall_location,
            'target': 'new'
        }

    @api.model
    def create(self, values):
        """
        Create a new calendar event, ensuring the Jitsi link is properly set.
        """
        if 'is_jitsi' in values:
            values['access_token'] = uuid.uuid4().hex if values.get('is_jitsi') else False
        return super().create(values)

class ResConfigSettings(models.TransientModel):
    """
    Inherited model for configuring Jitsi integration settings.
    """
    _inherit = 'res.config.settings'
    
    is_jitsi = fields.Boolean(
        "Enable Jitsi Integration", 
        config_parameter='is_jitsi_param'
    )
    company_param = fields.Many2one(
        'res.company', 
        string="Company", 
        config_parameter='company_param',
        default=lambda self: self.env.company
    )
