FROM odoo:18.0

USER root

# 1. Instalar utilidades y dependencias de Python (PANDAS incluido)
RUN apt-get update && apt-get install -y sudo git build-essential python3-dev     && pip3 install pandas openpyxl     && rm -rf /var/lib/apt/lists/*

# 2. Configurar la Shell bash (para VS Code)
RUN usermod -s /bin/bash odoo

# 3. [TRUCO DE ARQUITECTO] Alinear el UID de Odoo con el tuyo (1000)
# Esto hace que el contenedor y tú sean "la misma persona" a nivel de archivos.
# Usamos '|| true' para evitar errores si el ID ya está ocupado, pero en Odoo suele funcionar.
RUN usermod -u 1000 odoo && groupmod -g 1000 odoo

# 4. Dar permisos de sudo y asegurar propiedad de carpetas críticas
RUN echo "odoo ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/odoo     && chown -R odoo:odoo /var/lib/odoo /mnt/extra-addons

USER odoo
