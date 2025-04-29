FROM mediawiki:1.43

# Install tools for image handling and extensions
RUN apt-get update && apt-get install -y \
    git unzip imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /var/www/html

# Copy .htaccess
COPY .htaccess /var/www/html/.htaccess

# Copy LocalSettings.php
COPY LocalSettings.php /var/www/html/LocalSettings.php

# Fix permissions
RUN chown -R www-data:www-data /var/www/html