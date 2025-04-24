FROM mediawiki:1.43

# Install additional dependencies (optional)
RUN apt-get update && apt-get install -y \
    git unzip imagemagick \
    && rm -rf /var/lib/apt/lists/*

# You can copy your customized LocalSettings.php here if needed
# COPY ./LocalSettings.php /var/www/html/LocalSettings.php
