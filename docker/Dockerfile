FROM mediawiki:1.43

# Install tools for image handling and extensions
RUN apt-get update && apt-get install -y \
    git unzip wget imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Download Composer
RUN wget -cO - https://getcomposer.org/composer-2.phar > composer.phar \
    && mv composer.phar /usr/local/bin/composer \
    && chmod +x /usr/local/bin/composer

# Clone and configure the AWS extension
ENV COMPOSER_ROOT_VERSION=1.43.0
RUN cd /var/www/html && \
git clone --depth 1 https://github.com/edwardspec/mediawiki-aws-s3.git extensions/AWS && \
echo '{"extra":{"merge-plugin":{"include":["extensions/AWS/composer.json"]}}}' > composer.local.json && \
composer update --no-dev

# Set working directory
WORKDIR /var/www/html

# Copy .htaccess
COPY .htaccess /var/www/html/.htaccess

# Copy LocalSettings.php
COPY LocalSettings.php /var/www/html/LocalSettings.php

# Copy extensions
COPY extensions/Cargo/ /var/www/html/extensions/Cargo/
COPY extensions/PageSchemas/ /var/www/html/extensions/PageSchemas/
COPY extensions/PageForms/ /var/www/html/extensions/PageForms/

# Copy skins
COPY skins/Citizen/ /var/www/html/skins/Citizen/
COPY skins/Wiki7/ /var/www/html/skins/Wiki7/

# Fix permissions
RUN chown -R www-data:www-data /var/www/html