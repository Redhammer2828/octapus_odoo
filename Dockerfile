# Use a base image with Python and necessary build tools
FROM python:3.10-slim AS builder

# Set environment variables
ENV ODOO_VERSION 17.0
ENV ODOO_HOME /opt/odoo

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
    && rm -rf /var/lib/apt/lists/*

COPY . $ODOO_HOME

# Switch to the Odoo directory
WORKDIR $ODOO_HOME

# Install Python dependencies
RUN pip install -r requirements.txt


# Expose Odoo port
EXPOSE 8070


# Run odoo-bin with the specified arguments
CMD ["python", "odoo-bin", "-c", "odoo.conf", "-d", "AAA-odoo", "-u", "customer"]

