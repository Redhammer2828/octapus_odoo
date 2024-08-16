# Use a base image with Python and necessary build tools
FROM python:3.10-slim AS builder

# Set environment variables
ENV ODOO_VERSION 17.0
ENV ODOO_HOME /opt/odoo
ENV ODOO_USER odoo

# Install build dependencies
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        python3-dev \
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
    && rm -rf /var/lib/apt/lists/*

# Install wkhtmltopdf
# RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb \
#     && dpkg -i wkhtmltox_0.12.6-1.bionic_amd64.deb \
#     && apt-get -f install -y \
#     && rm wkhtmltox_0.12.6-1.bionic_amd64.deb

# Create Odoo user
RUN adduser --system --home=$ODOO_HOME --group $ODOO_USER

COPY . $ODOO_HOME

# Switch to the Odoo directory
WORKDIR $ODOO_HOME

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set permissions
RUN chown -R $ODOO_USER:$ODOO_USER $ODOO_HOME

# Expose Odoo port
EXPOSE 8070

# Switch to non-root user
USER $ODOO_USER

# Set the entrypoint
CMD ["python", "odoo-bin", "-c", "odoo.conf", "-d", "AAA-odoo-test", "-u", "all"]
