from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    latitude = fields.Float(
        string='Latitude',
        digits=(16, 7),
        help='GPS Latitude coordinate for office location'
    )
    longitude = fields.Float(
        string='Longitude', 
        digits=(16, 7),
        help='GPS Longitude coordinate for office location'
    )
    
    # Default coordinates (example: Jakarta, Indonesia)
    @api.model
    def _get_default_coordinates(self):
        """Set default coordinates if not specified"""
        companies_without_coords = self.search([
            '|',
            ('latitude', '=', False),
            ('longitude', '=', False)
        ])
        
        for company in companies_without_coords:
            if not company.latitude:
                company.latitude = -6.969182
            if not company.longitude:
                company.longitude = 107.629251
