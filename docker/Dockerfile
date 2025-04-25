FROM mediawiki:1.43

# Install optional dependencies (for image processing, debugging, etc.)
RUN apt-get update && apt-get install -y \
    git unzip imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Copy LocalSettings.php (uncomment if bundling in image for prod)
COPY LocalSettings.php /var/www/html/LocalSettings.php

# Set a working directory explicitly (not required, but nice to be explicit)
WORKDIR /var/www/html
