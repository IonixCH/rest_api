from odoo import models, fields, api

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    selfie_photo = fields.Binary('Selfie Photo')
    latitude = fields.Char('Latitude')
    longitude = fields.Char('Longitude')
    working_hours = fields.Char('Working Hours', default='00:00:00')

    def write(self, vals):
        """Override write to calculate working_hours when check_out is updated"""
        result = super().write(vals)
        
        # Calculate working hours if check_out is set
        if 'check_out' in vals:
            for record in self:
                if record.check_in and record.check_out:
                    duration = record.check_out - record.check_in
                    hours = int(duration.total_seconds() // 3600)
                    minutes = int((duration.total_seconds() % 3600) // 60)
                    seconds = int(duration.total_seconds() % 60)
                    working_hours = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                    # Use sudo() to avoid permission issues
                    record.sudo().write({'working_hours': working_hours})
        
        return result