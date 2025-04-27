# Wiki7Skin Installation Guide

This document guides you through setting up the Wiki7Skin custom skin for your MediaWiki 1.43 installation.

## Prerequisites

- MediaWiki 1.43 installed and working
- Access to the MediaWiki file system
- Permissions to modify MediaWiki configuration files

## Installation Steps

### 1. Copy Skin Files

Clone or download the Wiki7Skin files to your MediaWiki `skins` directory:

```bash
cd /path/to/your/mediawiki/skins
git clone [your-repository-url] Wiki7Skin
```

Or manually create the directory structure and add all the files as shown in the project structure.

### 2. Update LocalSettings.php

Add the following code to your `LocalSettings.php` file to enable the skin:

```php
# Load Wiki7Skin
wfLoadSkin( 'Wiki7Skin' );

# Optional: Set Wiki7Skin as the default
$wgDefaultSkin = 'wiki7skin';
```

### 3. Create Custom Logo

Replace the placeholder logo in `resources/images/logo.svg` with your own logo for Hapoel Beer Sheva. This will automatically be used by the skin.

Alternatively, you can set a different logo path in your `LocalSettings.php`:

```php
$wgLogos = [
    '1x' => "$wgResourceBasePath/skins/Wiki7Skin/resources/images/your-custom-logo.png",
    'svg' => "$wgResourceBasePath/skins/Wiki7Skin/resources/images/your-custom-logo.svg"
];
```

### 4. Configure Site Name and Tagline

In your `LocalSettings.php`, set the site name:

```php
$wgSitename = "Wiki7 - הפועל באר שבע";
```

The tagline is set through the skin's translation files, but you can override it:

```php
$wgHooks['SkinTemplateOutputPageBeforeExec'][] = function( $skin, &$template ) {
    $template->set( 'msg-tagline', wfMessage( 'custom-tagline' )->text() );
    return true;
};
```

Then add the message in your `LocalSettings.php`:

```php
$wgMessagesDirs['MyMessages'] = __DIR__ . '/my-messages';
```

And create a file `my-messages/en.json` with:

```json
{
    "custom-tagline": "Your custom tagline here"
}
```

### 5. Clear MediaWiki Cache

Run the maintenance script to clear the cache:

```bash
php /path/to/your/mediawiki/maintenance/rebuildLocalisationCache.php
```

Also, purge the browser cache by adding `?action=purge` to any wiki page URL.

### 6. Verify Installation

1. Go to your wiki's Special:Preferences page
2. In the "Appearance" tab, ensure "Wiki7Skin" is listed as an available skin
3. Select it and save your preferences to view the site with the new skin

## Customization

### Custom CSS

To add custom CSS without modifying the skin files, add the following to your `LocalSettings.php`:

```php
$wgHooks['BeforePageDisplay'][] = function( $out, $skin ) {
    if ( $skin->getSkinName() == 'wiki7skin' ) {
        $out->addInlineStyle( '
            /* Your custom CSS here */
            body { 
                /* Example: */ 
                /* font-family: "Alef", sans-serif; */
            }
        ' );
    }
    return true;
};
```

### Custom JavaScript

Similarly, for custom JavaScript:

```php
$wgHooks['BeforePageDisplay'][] = function( $out, $skin ) {
    if ( $skin->getSkinName() == 'wiki7skin' ) {
        $out->addInlineScript( '
            // Your custom JavaScript here
            document.addEventListener("DOMContentLoaded", function() {
                // Example:
                // console.log("Custom script loaded");
            });
        ' );
    }
    return true;
};
```

## Troubleshooting

If the skin doesn't appear in the preferences:

1. Ensure the skin files are in the correct location
2. Check for errors in your MediaWiki log
3. Verify that you've updated `LocalSettings.php` correctly
4. Make sure file permissions allow MediaWiki to read the skin files
5. Run `php maintenance/update.php` to update the database if needed

## RTL Support

For right-to-left language support (Hebrew), the skin automatically detects the language direction. To improve RTL support, consider adding RTL-specific styles in `resources/styles/Wiki7Skin.rtl.less`.

## Additional Resources

- [MediaWiki Skin Documentation](https://www.mediawiki.org/wiki/Manual:Skinning)
- [MediaWiki Skin Development](https://www.mediawiki.org/wiki/Manual:Skinning_Part_1)
- [MediaWiki i18n Documentation](https://www.mediawiki.org/wiki/Localisation)