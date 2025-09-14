FROM odoo:17.0

USER root
RUN pip install pandas geopy
USER odoo