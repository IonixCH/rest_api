from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    latitude = fields.Float(string='Latitude', digits=(16, 6), help='Latitude kantor utama')
    longitude = fields.Float(string='Longitude', digits=(16, 6), help='Longitude kantor utama')
