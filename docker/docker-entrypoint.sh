#!/bin/bash
set -e

# 1. Wait for DB to be reachable (max 60s)
echo "Waiting for database..."
for i in $(seq 1 30); do
  if mysqladmin ping -h "$MEDIAWIKI_DB_HOST" -u "$MEDIAWIKI_DB_USER" \
     -p"$MEDIAWIKI_DB_PASSWORD" --skip-ssl --silent 2>/dev/null; then
    echo "Database is ready."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "ERROR: Database not reachable after 60s. Exiting."
    exit 1
  fi
  echo "Attempt $i/30 — DB not ready, waiting 2s..."
  sleep 2
done

# 2. Check if MediaWiki is already installed (core `page` table exists)
TABLE_EXISTS=$(mysql -h "$MEDIAWIKI_DB_HOST" -u "$MEDIAWIKI_DB_USER" \
  -p"$MEDIAWIKI_DB_PASSWORD" --skip-ssl "$MEDIAWIKI_DB_NAME" \
  -sse "SELECT COUNT(*) FROM information_schema.tables \
        WHERE table_schema='$MEDIAWIKI_DB_NAME' AND table_name='page';" 2>/dev/null || echo "0")

if [ "$TABLE_EXISTS" = "0" ]; then
  echo "=== Fresh database detected. Running MediaWiki install... ==="
  # install.php refuses to run if LocalSettings.php exists — move it aside
  mv /var/www/html/LocalSettings.php /var/www/html/LocalSettings.php.bak

  php maintenance/run.php install \
    --dbserver="$MEDIAWIKI_DB_HOST" \
    --dbname="$MEDIAWIKI_DB_NAME" \
    --dbuser="$MEDIAWIKI_DB_USER" \
    --dbpass="$MEDIAWIKI_DB_PASSWORD" \
    --server="https://wiki7.co.il" \
    --scriptpath="" \
    --lang=he \
    --pass="$MEDIAWIKI_ADMIN_PASSWORD" \
    "ויקישבע" "Admin"

  # install.php generates a new LocalSettings.php — restore our custom one
  cp /var/www/html/LocalSettings.php.custom /var/www/html/LocalSettings.php
  echo "=== Install complete. Restored custom LocalSettings.php ==="
fi

# 3. Always run update.php (idempotent — handles schema migrations for extensions)
echo "=== Running update.php for schema migrations... ==="
php maintenance/run.php update --quick

# 4. Import default wiki pages (main page, templates, CSS/JS)
#    Auto-detects content changes via hash comparison in updatelog table
echo "=== Importing default wiki pages... ==="
php maintenance/run.php /var/www/html/import-pages.php

# 5. Create ALL Cargo SQL tables from declaration templates.
#    Query page_props for CargoTableName entries set by #cargo_declare.
echo "=== Creating Cargo tables... ==="
CARGO_TABLES=$(mysql -h "$MEDIAWIKI_DB_HOST" -u "$MEDIAWIKI_DB_USER" \
  -p"$MEDIAWIKI_DB_PASSWORD" --skip-ssl "$MEDIAWIKI_DB_NAME" \
  -N -e "SELECT DISTINCT pp_value FROM page_props WHERE pp_propname='CargoTableName';" 2>/dev/null || echo "")

if [ -z "$CARGO_TABLES" ]; then
  echo "  No Cargo declaration templates found. Skipping table creation."
else
  for tbl in $CARGO_TABLES; do
    echo "  Creating Cargo table: $tbl"
    php extensions/Cargo/maintenance/cargoRecreateData.php --table="$tbl" --quiet 2>&1 || true
  done
fi

# 6. Re-parse sample data pages so #cargo_store fires (tables now exist)
echo "=== Populating Cargo data from sample pages... ==="
php maintenance/run.php /var/www/html/cargo-repopulate.php

echo "=== Database initialization complete. Starting Apache... ==="

# 7. Hand off to Apache
exec docker-php-entrypoint apache2-foreground
