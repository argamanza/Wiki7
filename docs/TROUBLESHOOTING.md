# Wiki7 Troubleshooting Guide

Common issues and their solutions for the Wiki7 project.

---

## Table of Contents

- [Docker Issues](#docker-issues)
- [Database Issues](#database-issues)
- [MediaWiki Issues](#mediawiki-issues)
- [Extension Conflicts](#extension-conflicts)
- [Skin Rendering Issues](#skin-rendering-issues)
- [AWS / CDK Issues](#aws--cdk-issues)
- [Data Pipeline Issues](#data-pipeline-issues)

---

## Docker Issues

### Port 8080 Already in Use

**Symptom:** `docker compose up` fails with "port is already allocated".

**Fix:** Either stop the conflicting process or change the port in `docker/docker-compose.yml`:
```yaml
ports:
  - "9090:80"   # Use port 9090 instead of 8080
```

Then access the wiki at `http://localhost:9090`.

---

### Container Exits Immediately After Starting

**Symptom:** `docker compose ps` shows the mediawiki container as "Exited".

**Diagnosis:**
```bash
cd docker
docker compose logs mediawiki
```

**Common causes:**
1. **Missing .env file:** Copy `.env.example` to `.env` and fill in values.
   ```bash
   cp .env.example .env
   ```
2. **Database not ready:** The mediawiki container depends on the db container health check. Wait and retry:
   ```bash
   docker compose down
   docker compose up -d
   ```
3. **Corrupted LocalSettings.php:** Verify the file exists at `docker/LocalSettings.php`.

---

### Docker Build Fails

**Symptom:** `docker compose build` fails during the Composer or extension installation step.

**Fixes:**
1. **Network issues:** Composer and git clone need internet access. Check your connection.
2. **Git submodules not initialized:**
   ```bash
   git submodule update --init --recursive
   ```
3. **Stale Docker cache:** Force a clean build:
   ```bash
   docker compose build --no-cache
   ```

---

### Permission Errors on Uploaded Images

**Symptom:** File uploads fail with "Could not create directory" or similar.

**Fix:**
```bash
cd docker
docker compose exec mediawiki chown -R www-data:www-data /var/www/html/images
docker compose exec mediawiki chmod -R 755 /var/www/html/images
```

---

### Out of Disk Space

**Symptom:** Docker operations fail with "no space left on device".

**Fix:**
```bash
# Remove unused Docker resources
docker system prune -a --volumes

# Check disk usage
docker system df
```

---

### Container Cannot Connect to Database

**Symptom:** MediaWiki shows "Database connection error" on startup.

**Diagnosis:**
```bash
cd docker
docker compose logs db
docker compose exec db mysqladmin ping -u root -p
```

**Fixes:**
1. Verify `MEDIAWIKI_DB_PASSWORD` in `.env` matches `MYSQL_PASSWORD`.
2. Ensure the database container is healthy:
   ```bash
   docker compose ps
   ```
3. Reset the database volume if corrupted:
   ```bash
   docker compose down -v
   docker compose up -d
   ```
   **Warning:** This deletes all database data.

---

## Database Issues

### "Table Not Found" Errors

**Symptom:** MediaWiki pages show "Table 'wikidb.xxx' doesn't exist".

**Fix:** Run the MediaWiki database updater:
```bash
cd docker
docker compose exec mediawiki php maintenance/run.php update
```

---

### MariaDB Fails to Initialize

**Symptom:** The `db` container fails health checks or won't start.

**Diagnosis:**
```bash
docker compose logs db
```

**Common causes:**
1. **Invalid root password:** If you changed `MYSQL_ROOT_PASSWORD` after the volume was created, the old password is baked into the data volume:
   ```bash
   docker compose down -v    # Removes the volume (DELETES DATA)
   docker compose up -d      # Fresh initialization
   ```
2. **Corrupted data volume:** Same fix as above.
3. **Memory limits too low:** The default is 512 MB. Increase in `docker-compose.yml` if needed.

---

### Slow Database Queries

**Symptom:** Pages load slowly, especially special pages or pages with many templates.

**Diagnosis (local):**
```bash
docker compose exec db mysql -u root -p -e "SHOW PROCESSLIST;"
```

**Fixes:**
1. **Run the MediaWiki updater** to ensure all indexes exist:
   ```bash
   docker compose exec mediawiki php maintenance/run.php update
   ```
2. **Rebuild Cargo tables** if Cargo is causing issues:
   ```bash
   docker compose exec mediawiki php maintenance/run.php runJobs
   ```
3. **Add MariaDB tuning** in a custom config file mounted into the db container.

---

### Database Encoding Issues (Hebrew Text)

**Symptom:** Hebrew characters appear as garbled text or question marks.

**Fix:** Verify the database uses `binary` charset (MediaWiki's default):
```bash
docker compose exec db mysql -u root -p -e "SELECT DEFAULT_CHARACTER_SET_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = 'wikidb';"
```

If it's not `binary`, the database was initialized incorrectly. The safest fix is to export, recreate, and reimport:
```bash
docker compose exec db mysqldump -u root -p wikidb > backup.sql
docker compose down -v
docker compose up -d
docker compose exec -T db mysql -u root -p wikidb < backup.sql
```

---

## MediaWiki Issues

### Blank White Page

**Symptom:** The wiki loads but shows a blank white page.

**Diagnosis:** Check PHP error logs:
```bash
cd docker
docker compose exec mediawiki cat /tmp/mediawiki-debug.log
docker compose logs mediawiki | tail -50
```

**Common causes:**
1. **PHP fatal error:** Often a missing extension or incompatible version. Check logs.
2. **Missing LocalSettings.php:** Verify the file exists and is mounted.
3. **Cache corruption:** Clear the cache:
   ```bash
   docker compose exec mediawiki rm -rf /var/www/html/cache/*
   ```

---

### "MediaWiki Internal Error" Page

**Symptom:** A page shows "MediaWiki internal error" with or without details.

**Fix:** In development mode (`WIKI_ENV=dev`), `$wgShowExceptionDetails` is true, so you should see the full error. If not:
```bash
docker compose exec mediawiki php maintenance/run.php eval 'echo "PHP is working\n";'
```

Common fixes:
- Run `php maintenance/run.php update` for missing tables.
- Check file permissions on `/var/www/html`.
- Verify all extensions listed in LocalSettings.php exist.

---

### Search Not Working

**Symptom:** Search returns no results or shows errors.

**Fix:**
1. Rebuild the search index:
   ```bash
   docker compose exec mediawiki php maintenance/run.php rebuildtextindex
   ```
2. If using CirrusSearch (Elasticsearch), ensure the search backend is running. The default setup uses MySQL-based search, which requires no extra services.

---

### File Uploads Fail

**Symptom:** "Upload error" or "Could not store file" when uploading images.

**Fixes:**
1. Check file type is allowed (png, gif, jpg, jpeg, webp, svg, pdf, ogg).
2. Check file size limits in LocalSettings.php and PHP config.
3. Fix permissions:
   ```bash
   docker compose exec mediawiki chown -R www-data:www-data /var/www/html/images
   ```
4. In production, verify S3 bucket permissions and IAM role.

---

## Extension Conflicts

### Cargo Extension Errors

**Symptom:** "Cargo table creation failed" or SQL errors related to Cargo tables.

**Fix:**
1. Recreate Cargo tables from Special:CargoTables in the wiki.
2. Run pending jobs:
   ```bash
   docker compose exec mediawiki php maintenance/run.php runJobs
   ```
3. If tables are corrupted, drop and recreate:
   ```bash
   docker compose exec db mysql -u root -p wikidb -e "DROP TABLE IF EXISTS cargo__<tablename>;"
   ```
   Then recreate from the wiki's Special:CargoTables page.

---

### VisualEditor Not Loading

**Symptom:** The "Edit" button opens the wikitext editor instead of VisualEditor, or VisualEditor shows a loading spinner forever.

**Fixes:**
1. Verify VisualEditor is loaded in LocalSettings.php:
   ```php
   wfLoadExtension( 'VisualEditor' );
   ```
2. Check that Parsoid is available (bundled with MediaWiki 1.45+):
   ```bash
   curl http://localhost:8080/rest.php/v1/page/Main_Page/html
   ```
3. Clear ResourceLoader cache:
   - Append `?action=purge` to any wiki page URL.
   - Or: `docker compose exec mediawiki php maintenance/run.php purgeResourceLoaderCache`

---

### PageForms Conflicts with Cargo

**Symptom:** Form submission fails or produces incorrect data in Cargo tables.

**Fix:**
1. Ensure Cargo and PageForms versions are compatible (both should be on REL1_43 or later).
2. Check the form template syntax matches the Cargo table schema.
3. Rebuild the specific Cargo table.

---

### Extension Not Found

**Symptom:** "Error: The extension 'X' could not be found" on wiki startup.

**Fix:**
1. Check if the extension directory exists:
   ```bash
   docker compose exec mediawiki ls extensions/
   ```
2. Initialize submodules:
   ```bash
   git submodule update --init --recursive
   ```
3. If the extension was manually added, verify it's copied in the Dockerfile.

---

## Skin Rendering Issues

### Wiki7 Skin Not Appearing

**Symptom:** The wiki falls back to Vector or another default skin.

**Fixes:**
1. Verify the skin is loaded in LocalSettings.php:
   ```php
   wfLoadSkin( 'Wiki7' );
   $wgDefaultSkin = 'Wiki7';
   ```
2. Verify the skin directory exists:
   ```bash
   docker compose exec mediawiki ls skins/Wiki7/skin.json
   ```
3. Check for PHP errors in the skin:
   ```bash
   docker compose exec mediawiki php -l skins/Wiki7/includes/SkinWiki7.php
   ```

---

### RTL Layout Broken

**Symptom:** Hebrew text renders left-to-right or layout is mirrored incorrectly.

**Fixes:**
1. Verify `$wgLanguageCode = "he"` in LocalSettings.php.
2. Clear ResourceLoader cache:
   ```bash
   docker compose exec mediawiki php maintenance/run.php purgeResourceLoaderCache
   ```
3. Check that Hebrew fonts are enabled:
   ```php
   $wgWiki7EnableHEFonts = true;
   ```

---

### Dark Theme Not Working

**Symptom:** Theme toggle does nothing or dark mode looks broken.

**Fixes:**
1. Verify preferences are enabled:
   ```php
   // In LocalSettings.php, check skin.json defaults
   // Wiki7EnablePreferences should be true
   ```
2. Clear browser localStorage:
   - Open browser DevTools -> Application -> Local Storage -> Clear.
3. Hard refresh the page (Ctrl+Shift+R / Cmd+Shift+R).

---

### Missing Icons or Fonts

**Symptom:** Icons appear as squares or text uses wrong font.

**Fixes:**
1. **Icons:** The skin uses OOUI icons. Ensure the `skins.wiki7.icons` module is registered in `skin.json`.
2. **Hebrew fonts:** Verify `wgWiki7EnableHEFonts` is `true` in LocalSettings.php.
3. **Resource loading:** Check the browser console for 404 errors on font or icon files.
4. **ResourceLoader cache:** Purge with `?action=purge` or:
   ```bash
   docker compose exec mediawiki php maintenance/run.php purgeResourceLoaderCache
   ```

---

### Sticky Header Not Showing

**Symptom:** The header does not become sticky when scrolling.

**Cause:** The sticky header relies on `IntersectionObserver` and scroll events in `skins.wiki7.scripts`.

**Fixes:**
1. Check for JavaScript errors in the browser console.
2. Ensure JavaScript is enabled and not blocked by CSP.
3. Hard refresh the page to reload JS modules.

---

## AWS / CDK Issues

### CDK Synth Fails

**Symptom:** `npx cdk synth` throws errors.

**Fixes:**
1. Install dependencies:
   ```bash
   cd cdk && npm ci
   ```
2. Check TypeScript compilation:
   ```bash
   cd cdk && npx tsc --noEmit
   ```
3. Verify context values are set (domainName, etc.).

---

### CDK Deploy Fails with "Resource Already Exists"

**Symptom:** CloudFormation reports a resource already exists.

**Fix:** This happens when a resource was created outside CDK or in a failed previous deployment:
1. Import the existing resource: `npx cdk import Wiki7CdkStack`
2. Or delete the conflicting resource manually and retry.

---

### SSM Parameter Not Found

**Symptom:** Main stack fails with "SSM parameter /wiki7/certificate/arn not found".

**Fix:** Deploy prerequisite stacks first:
```bash
npx cdk deploy Wiki7DnsStack
npx cdk deploy Wiki7CertificateStack
# Then:
npx cdk deploy Wiki7CdkStack
```

---

### CloudFront Returns 502

**Symptom:** Site returns "502 Bad Gateway" via CloudFront.

**Fixes:**
1. Verify the EC2 instance is running and healthy.
2. Check `origin.wiki7.co.il` DNS resolves to the correct EC2 public IP.
3. Verify Nginx is running on port 80 on the EC2 instance.
4. Check the `X-Origin-Verify` custom header matches between CloudFront and Nginx config.

---

## Data Pipeline Issues

### Scraper Fails to Connect

**Symptom:** Scrapy spiders fail with connection errors.

**Fix:**
1. Verify `SCRAPERAPI_KEY` is set in `.env`.
2. Check your ScraperAPI account has remaining credits.
3. Try running without ScraperAPI proxy first to isolate the issue.

---

### Poetry Install Fails

**Symptom:** `poetry install` in the `data/` directory fails.

**Fix:**
```bash
cd data
poetry env remove --all
poetry install
```

If Python version mismatch:
```bash
poetry env use python3.12
poetry install
```
