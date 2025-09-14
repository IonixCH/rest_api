# # -*- coding: utf-8 -*-
# from odoo import http
#
#
# class AppointmentController(http.Controller):
#     @http.route('/calendar/join_jitsi/<string:access_token>', auth='public')
#     def appointment_join_jitsi(self, access_token, **kw):
#         # check the controller have token or not
#         access_token = "Access token: {}".format(access_token)
#         html_content = """
#                         <!DOCTYPE html>
#                         <html lang="en">
#                         <head>
#                         <meta charset="UTF-8">
#                         <meta name="viewport" content="width=device-width, initial-scale=1.0">
#                         <title>Jitsi Meet Doodex</title>
#                         <!-- Include Jitsi Meet API -->
#                         <script src='https://meet.jit.si/external_api.js'></script>
#                         <style>
#                             #meet {
#                                 position: fixed;
#                                 top: 0;
#                                 left: 0;
#                                 width: 100%;
#                                 height: 100%;
#                                 overflow: hidden;/* Avoids scrolling if Jitsi Meet content is larger than the viewport */
#                             }
#                         </style>
#                         </head>
#                         <body>
#                             <div id="meet"></div>
#
#                             <script>
#                                 // Configure Jitsi Meet
#                                 const domain = 'meet.jit.si';
#                                 const options = {
#                                     roomName: 'PT. Doodex',
#                                     parentNode: document.querySelector('#meet'),
#                                     width: '100%',
#                                     height: '100%'
#
#                                 };
#
#                                 // Initialisation API Jitsi Meet
#                                 const api = new JitsiMeetExternalAPI(domain, options);
#                             </script>
#                         </body>
#                         </html>
#                """
#         return html_content
