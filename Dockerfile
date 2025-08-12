# Use a base image with Python and necessary build tools
FROM python:3.10-bullseye AS builder

# Set environment variables
ENV ODOO_VERSION 17.0
ENV ODOO_HOME /opt/odoo
ENV ODOO_USER odoo

# Install build dependencies
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
        fonts-liberation \
        fonts-dejavu \
        fonts-urw-base35 \
        xfonts-75dpi \
        xfonts-base \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.bullseye_amd64.deb \
    && apt install -y ./wkhtmltox_0.12.6.1-2.bullseye_amd64.deb \
    && rm wkhtmltox_0.12.6.1-2.bullseye_amd64.deb

# Refresh font cache
RUN fc-cache -fv

# Create Odoo user
RUN adduser --system --home=$ODOO_HOME --group $ODOO_USER

COPY requirements.txt $ODOO_HOME/

# Switch to the Odoo directory
WORKDIR $ODOO_HOME

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . $ODOO_HOME
# Set permissions
RUN chown -R $ODOO_USER:$ODOO_USER $ODOO_HOME

# Expose Odoo port
EXPOSE 8070

# Switch to non-root user
USER $ODOO_USER

# Set the entrypoint
CMD ["python", "odoo-bin", "-c", "odoo.conf"]


