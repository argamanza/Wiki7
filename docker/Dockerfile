# =============================================================================
# Stage 1: Build — install Composer dependencies and MediaWiki extensions
# =============================================================================
FROM mediawiki:1.45.1 AS builder

# Install build-only dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git=1:2.39.* \
    unzip=6.0-* \
    wget=1.21.* \
    && rm -rf /var/lib/apt/lists/*

# Install Composer with signature verification
# Uses the official programmatic installer with SHA-384 hash check
COPY --from=composer:2.8 /usr/bin/composer /usr/local/bin/composer

# Clone and configure the AWS S3 extension
ENV COMPOSER_ROOT_VERSION=1.45.0
WORKDIR /var/www/html
RUN git clone --depth 1 --branch v0.14.0 https://github.com/edwardspec/mediawiki-aws-s3.git extensions/AWS && \
    echo '{"extra":{"merge-plugin":{"include":["extensions/AWS/composer.json"]}}}' > composer.local.json && \
    composer update --no-dev --no-interaction --optimize-autoloader

# =============================================================================
# Stage 2: Runtime — lean production image
# =============================================================================
FROM mediawiki:1.45.1

# Install runtime-only dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    imagemagick=8:6.9.* \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html

# Copy Composer-installed vendor directory and AWS extension from builder
COPY --from=builder /var/www/html/extensions/AWS/ /var/www/html/extensions/AWS/
COPY --from=builder /var/www/html/vendor/ /var/www/html/vendor/
COPY --from=builder /var/www/html/composer.local.json /var/www/html/composer.local.json
COPY --from=builder /var/www/html/composer.json /var/www/html/composer.json
COPY --from=builder /var/www/html/composer.lock /var/www/html/composer.lock

# Copy .htaccess
COPY .htaccess /var/www/html/.htaccess

# Copy LocalSettings.php
COPY LocalSettings.php /var/www/html/LocalSettings.php

# Copy extensions
COPY extensions/Cargo/ /var/www/html/extensions/Cargo/
COPY extensions/PageForms/ /var/www/html/extensions/PageForms/

# Copy skins
COPY skins/Citizen/ /var/www/html/skins/Citizen/
COPY skins/Wiki7/ /var/www/html/skins/Wiki7/

# Fix permissions
RUN chown -R www-data:www-data /var/www/html
