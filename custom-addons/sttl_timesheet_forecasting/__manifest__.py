{
    "name": "Timesheet Forecasting Report",
    "version": "17.0.1.0",
    "category": "Analytic",
    "summary": "AI module predicts Timesheet metrics, enhancing decision-making and optimizing project management.",
    "description": """
        Provides Timesheet Forecasting Reports
    """,
    "author": "Silver Touch Technologies Limited",
    "website": "https://www.silvertouch.com",
    "support": "",
    "depends": ["base", "hr_timesheet"],
    "data": [
        # DATA
        "data/forecasting_cron.xml",
        
        # SECURITY
        "security/ir.model.access.csv",

        # VIEWS
        "views/timesheet_forecasting_view.xml",
        "views/menus.xml",
    ],
    "price": 0,
    "currency": "USD",
    "license": "LGPL-3",
    "installable": True,
    'images': ['static/description/banner.png'],
}
