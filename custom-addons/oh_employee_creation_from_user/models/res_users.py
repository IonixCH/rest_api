# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ResUsers(models.Model):
    """ Inherited class of res user to override the create function"""
    _inherit = 'res.users'

    employee_id = fields.Many2one('hr.employee',
                                  string='Related Employee',
                                  ondelete='restrict', auto_join=True,
                                  help='Related employee based on the'
                                       ' data of the user')

    @api.model_create_multi
    def create(self, vals):
        """Overrides the default 'create' method to create an employee record
        when a new user is created."""
        result = super(ResUsers, self).create(vals)
        
        # Get default company
        default_company = self.env['res.company'].search([], limit=1)
        if not default_company:
            default_company = self.env.ref('base.main_company')
        
        # Create resource first
        resource = self.env['resource.resource'].sudo().create({
            'name': result['name'],
            'user_id': result['id'],
            'company_id': default_company.id,
            'tz': 'Asia/Jakarta',
        })
        
        result['employee_id'] = self.env['hr.employee'].sudo().create({
            'name': result['name'],
            'user_id': result['id'],
            'private_street': result['partner_id'].id,
            'company_id': default_company.id,
            'resource_id': resource.id,
        })
        return result
