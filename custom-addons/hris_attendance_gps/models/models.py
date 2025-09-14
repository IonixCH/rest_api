# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class hris_attendance_gps(models.Model):
#     _name = 'hris_attendance_gps.hris_attendance_gps'
#     _description = 'hris_attendance_gps.hris_attendance_gps'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

