# Packaging Wiki7Skin

This document provides instructions on how to package the Wiki7Skin for distribution or installation.

## Creating an Archive

You can package all the skin files into a single archive file for easy distribution. Here are commands for different operating systems:

### Linux/MacOS

```bash
# Navigate to your MediaWiki skins directory
cd /path/to/mediawiki/skins

# Create a ZIP archive
zip -r Wiki7Skin.zip Wiki7Skin

# Or create a tarball
tar -czvf Wiki7Skin.tar.gz Wiki7Skin
```

### Windows

```
# Using PowerShell
Compress-Archive -Path .\Wiki7Skin -DestinationPath Wiki7Skin.zip

# Or use a graphical tool like 7-Zip or WinRAR
# Right-click on the Wiki7Skin folder and select "Add to archive..."
```

## Directory Structure to Include

Make sure your archive includes all these files in the correct structure:

```
Wiki7Skin/
├── Wiki7Skin.php
├── skin.json
├── README.md
├── INSTALLATION.md
├── PACKAGING.md
├── resources/
│   ├── images/
│   │   └── logo.svg
│   ├── scripts/
│   │   └── main.js
│   └── styles/
│       ├── Wiki7Skin.less
│       └── Wiki7Skin.rtl.less
├── templates/
│   ├── skin.mustache
│   └── Menu.mustache
└── i18n/
    ├── en.json
    └── he.json
```

## Installation from the Archive

### Installing from ZIP

1. Download the ZIP file to your computer
2. Extract the contents to the `skins` directory of your MediaWiki installation
3. Make sure the extracted folder is named `Wiki7Skin` (not `Wiki7Skin-master` or similar)
4. Follow the standard installation instructions in INSTALLATION.md

### Installing from tarball (Linux/MacOS)

```bash
# Navigate to your MediaWiki skins directory
cd /path/to/mediawiki/skins

# Extract the archive
tar -xzvf /path/to/Wiki7Skin.tar.gz

# Set proper permissions
chmod -R 755 Wiki7Skin
```

## For Docker Environment

If you're using MediaWiki in a Docker container:

1. You can either mount the skin directory from the host into the container:
   ```
   -v /path/on/host/Wiki7Skin:/var/www/html/skins/Wiki7Skin
   ```

2. Or you can copy the archive into the container and extract it:
   ```bash
   docker cp Wiki7Skin.zip mediawiki_container:/tmp/
   docker exec -it mediawiki_container bash
   cd /var/www/html/skins
   unzip /tmp/Wiki7Skin.zip
   ```

## Verifying the Installation

After installing from the archive, make sure to:

1. Update your LocalSettings.php file as described in INSTALLATION.md
2. Rebuild the MediaWiki cache
3. Check that the skin appears in your preferences

## Troubleshooting Archive Installation

If you encounter issues:

1. Check file permissions (files should be readable by the web server)
2. Make sure all files were extracted correctly with the proper directory structure
3. Verify that no files are missing
4. Check MediaWiki logs for any errors