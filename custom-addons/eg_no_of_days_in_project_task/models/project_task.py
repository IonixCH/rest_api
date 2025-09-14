from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class ProjectTask(models.Model):
    _inherit = 'project.task'

    number_of_days = fields.Integer(string='Number of Days', compute='_compute_number_of_day', search='_search_number_of_days')

    @api.depends('create_date')
    def _compute_number_of_day(self):
        today = datetime.today()
        for rec in self:
            if rec.create_date:
                frm_create_date = datetime.strftime(rec.create_date, DEFAULT_SERVER_DATETIME_FORMAT)
                create_date = datetime.strptime(frm_create_date, DEFAULT_SERVER_DATETIME_FORMAT)
                days = (today - create_date).days
                rec.number_of_days = days

    def _search_number_of_days(self, operator, value):
        if operator == "<":
            date_from = datetime.strftime(datetime.today() - timedelta(days=int(value)), DEFAULT_SERVER_DATETIME_FORMAT)
            order_ids = self.search([('create_date', '>=', date_from)])
            return [('id', 'in', order_ids.ids)]
        elif operator == ">":
            date_to = datetime.strftime(datetime.today() - timedelta(days=int(value + 1)),
                                        DEFAULT_SERVER_DATETIME_FORMAT)
            order_ids = self.search([('create_date', '<=', date_to)])
            return [('id', 'in', order_ids.ids)]
        elif operator == "<=":
            date_from = datetime.strftime(datetime.today() - timedelta(days=int(value + 1)),
                                          DEFAULT_SERVER_DATETIME_FORMAT)
            order_ids = self.search([('create_date', '>=', date_from)])
            return [('id', 'in', order_ids.ids)]
        elif operator == ">=":
            date_to = datetime.strftime(datetime.today() - timedelta(days=int(value)), DEFAULT_SERVER_DATETIME_FORMAT)
            order_ids = self.search([('create_date', '<=', date_to)])
            return [('id', 'in', order_ids.ids)]
        elif operator == "!=":
            date_one = datetime.strftime(datetime.today() - timedelta(days=int(value - 1)),
                                         DEFAULT_SERVER_DATETIME_FORMAT)
            order_one_ids = self.search([('create_date', '>=', date_one)])
            date_two = datetime.strftime(datetime.today() - timedelta(days=int(value + 1)),
                                         DEFAULT_SERVER_DATETIME_FORMAT)
            order_two_ids = self.search([('create_date', '<=', date_two)])
            order_ids = order_one_ids + order_two_ids
            return [('id', 'in', order_ids.ids)]
        else:
            date_to = datetime.strftime(datetime.today() - timedelta(days=int(value)), DEFAULT_SERVER_DATETIME_FORMAT)
            date_from = datetime.strftime(datetime.today() - timedelta(days=int(value + 1)),
                                          DEFAULT_SERVER_DATETIME_FORMAT)
            order_ids = self.search([('create_date', '>=', date_from), ('create_date', '<=', date_to)])
            return [('id', 'in', order_ids.ids)]
