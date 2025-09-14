from odoo import api, fields, models
from .forecasting import timesheet_forecasting

class TotalTimesheetForecast(models.Model):

    # ---------------------------------------- Private Attributes ---------------------------------
    _name = "total_timesheet.forecast"
    _description = "Total Timesheet Forecast"

    # --------------------------------------- Fields Declaration ----------------------------------
    forecasted_hrs = fields.Float("Total Hours")
    forecasting_dates = fields.Date("Date")

    # ---------------------------------------- Action Methods -------------------------------------
    def total_timesheet_forecasting(self):
        cr = self.env.cr

        cr.execute("""delete from total_timesheet_forecast""")

        query_total_timesheet_data = """
            SELECT DATE(date) AS Dates, SUM(unit_amount) AS Total
            FROM account_analytic_line aal 
            WHERE date  <= CURRENT_DATE + INTERVAL '1 DAY'
            GROUP BY Dates
            ORDER BY Dates;
        """
        cr.execute(query_total_timesheet_data)
        forecasted_timesheet_data = timesheet_forecasting(cr.fetchall())

        Obj = self.env['total_timesheet.forecast']
        if forecasted_timesheet_data is not None:
            for item in forecasted_timesheet_data:
                info = dict()

                info['forecasting_dates'] = item['Month'].strftime('%Y-%m-%d')

                total_value = item['Total']
                info['forecasted_hrs'] = 0.0 if total_value < 0.0 else total_value

                try:
                    Obj.sudo().create(info)
                except Exception as e:
                    print("Error Creating Record:", e)
        else:
            print("Insufficient Data")


class ProjectTimesheetForecast(models.Model):

    # ---------------------------------------- Private Attributes ---------------------------------
    _name = "project_timesheet.forecast"
    _description = "Project Timesheet Forecast"

    # --------------------------------------- Fields Declaration ----------------------------------
    
    # Basic
    forecasted_hrs = fields.Float("Total Hours")
    forecasting_dates = fields.Date("Date")

    # Relational
    project_id = fields.Many2one('project.project', string="Project")

    # ---------------------------------------- Action Methods -------------------------------------
    def project_timesheet_forecasting(self):
        cr = self.env.cr

        cr.execute("""delete from project_timesheet_forecast""")

        query_project_timesheet_data = """
            SELECT DATE(date) AS Dates, project_id , SUM(unit_amount) AS Total
            FROM account_analytic_line aal 
            WHERE date <= CURRENT_DATE + INTERVAL '1 DAY'
            GROUP BY Dates, project_id
            ORDER BY Dates, project_id;
        """

        cr.execute(query_project_timesheet_data)
        forecasted_project_timesheet_data = timesheet_forecasting(cr.fetchall())

        Obj = self.env['project_timesheet.forecast']

        if forecasted_project_timesheet_data is not None:
            for item in forecasted_project_timesheet_data:
                info = dict()

                info['forecasting_dates'] = item['Month'].strftime('%Y-%m-%d')

                info['project_id'] = item['Responsible']

                total_value = item['Total']
                info['forecasted_hrs'] = 0.0 if total_value < 0.0 else total_value

                try:
                    Obj.sudo().create(info)
                except Exception as e:
                    print("Error Creating Record:", e)
        else:
            print("Insufficient Data")


class EmployeeTimesheetForecast(models.Model):

    # ---------------------------------------- Private Attributes ---------------------------------
    _name = "employee_timesheet.forecast"
    _description = "Employee Timesheet Forecast"

    # --------------------------------------- Fields Declaration ----------------------------------
    
    # Basic
    forecasted_hrs = fields.Float("Total Hours")
    forecasting_dates = fields.Date("Date")

    # Relational
    employee_id = fields.Many2one('hr.employee', string="Project")

    # ---------------------------------------- Action Methods -------------------------------------
    def employee_timesheet_forecasting(self):
        cr = self.env.cr

        cr.execute("""delete from employee_timesheet_forecast""")

        query_employee_timesheet_data = """
            SELECT DATE(date) AS Dates, employee_id  , SUM(unit_amount) AS Total
            FROM account_analytic_line aal 
            WHERE date <= CURRENT_DATE + INTERVAL '1 DAY'
            GROUP BY Dates, employee_id
            ORDER BY Dates, employee_id;
        """

        cr.execute(query_employee_timesheet_data)
        forecasted_employee_timesheet_data = timesheet_forecasting(cr.fetchall())

        Obj = self.env['employee_timesheet.forecast']

        if forecasted_employee_timesheet_data is not None:
            for item in forecasted_employee_timesheet_data:
                info = dict()

                info['forecasting_dates'] = item['Month'].strftime('%Y-%m-%d')

                info['employee_id'] = item['Responsible']

                total_value = item['Total']
                info['forecasted_hrs'] = 0.0 if total_value < 0.0 else total_value

                try:
                    Obj.sudo().create(info)
                except Exception as e:
                    print("Error Creating Record:", e)
        else:
            print("Insufficient Data")


class TaskTimesheetForecast(models.Model):

    # ---------------------------------------- Private Attributes ---------------------------------
    _name = "task_timesheet.forecast"
    _description = "Task Timesheet Forecast"

    # --------------------------------------- Fields Declaration ----------------------------------
    
    # Basic
    forecasted_hrs = fields.Float("Total Hours")
    forecasting_dates = fields.Date("Date")

    # Relational
    task_id = fields.Many2one('project.task', string="Task")

    # ---------------------------------------- Action Methods -------------------------------------
    def task_timesheet_forecasting(self):
        cr = self.env.cr

        cr.execute("""delete from task_timesheet_forecast""")

        query_task_timesheet_data = """
            SELECT DATE(date) AS Dates, task_id  , SUM(unit_amount) AS Total
            FROM account_analytic_line aal 
            WHERE date <= CURRENT_DATE + INTERVAL '1 DAY'
            GROUP BY Dates, task_id
            ORDER BY Dates, task_id;
        """

        cr.execute(query_task_timesheet_data)
        forecasted_task_timesheet_data = timesheet_forecasting(cr.fetchall())

        Obj = self.env['task_timesheet.forecast']

        if forecasted_task_timesheet_data is not None:
            for item in forecasted_task_timesheet_data:
                info = dict()

                info['forecasting_dates'] = item['Month'].strftime('%Y-%m-%d')

                info['task_id'] = item['Responsible']

                total_value = item['Total']
                info['forecasted_hrs'] = 0.0 if total_value < 0.0 else total_value

                try:
                    Obj.sudo().create(info)
                except Exception as e:
                    print("Error Creating Record:", e)
        else:
            print("Insufficient Data")