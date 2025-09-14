# -*- coding: utf-8 -*-
# from odoo import http


# class HrisAttendanceGps(http.Controller):
#     @http.route('/hris_attendance_gps/hris_attendance_gps', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hris_attendance_gps/hris_attendance_gps/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hris_attendance_gps.listing', {
#             'root': '/hris_attendance_gps/hris_attendance_gps',
#             'objects': http.request.env['hris_attendance_gps.hris_attendance_gps'].search([]),
#         })

#     @http.route('/hris_attendance_gps/hris_attendance_gps/objects/<model("hris_attendance_gps.hris_attendance_gps"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hris_attendance_gps.object', {
#             'object': obj
#         })

