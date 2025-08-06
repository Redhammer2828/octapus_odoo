# Use a base image with Python and necessary build tools
FROM python:3.10-slim AS builder

# Set environment variables
ENV ODOO_VERSION 17.0
ENV ODOO_HOME /opt/odoo
ENV ODOO_USER odoo

# Install build dependencies and wkhtmltopdf dependencies
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        python3-dev \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
        libevent-dev \
        libsasl2-dev \
        libldap2-dev \
        libssl-dev \
        libpq-dev \
        wget \
        git \
        curl \
        xz-utils \
        fontconfig \
        libfreetype6 \
        libjpeg62-turbo \
        libx11-6 \
        libxcb1 \
        libxext6 \
        libxrender1 \
        zlib1g \
        wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Add Odoo system user
RUN adduser --system --home=$ODOO_HOME --group $ODOO_USER

# Copy Odoo source code and custom modules
COPY . $ODOO_HOME

# Copy custom font to system font directory
COPY custom/customer/static/src/fonts/Roboto-Regular.ttf /usr/share/fonts/truetype/Roboto-Regular.ttf

# Rebuild font cache
RUN fc-cache -fv

# Switch to Odoo directory
WORKDIR $ODOO_HOME

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set ownership permissions
RUN chown -R $ODOO_USER:$ODOO_USER $ODOO_HOME

# Expose Odoo port
EXPOSE 8070

# Switch to non-root user
USER $ODOO_USER

# Set the entrypoint
CMD ["python", "odoo-bin", "-c", "odoo.conf"]
