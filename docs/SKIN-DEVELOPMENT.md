# Wiki7 Skin Development Guide

## Overview

Wiki7 is a custom MediaWiki skin based on **Citizen v3.1.0**, built for the Hapoel Beer Sheva FC fan wiki at wiki7.co.il. It is a responsive, mobile-friendly skin that extends Citizen with custom branding, Hebrew RTL support, and team-specific features.

- **MediaWiki requirement:** >= 1.45.0
- **License:** GPL-3.0-or-later
- **Skin class:** `MediaWiki\Skins\Wiki7\SkinWiki7` (extends `SkinMustache`)
- **Config prefix:** `wgWiki7` (all configuration keys are prefixed with this)

The skin lives at `docker/skins/Wiki7/` and is registered via `skin.json`.

---

## Directory Structure

```
docker/skins/Wiki7/
├── skin.json                  # Skin registration, config, ResourceLoader modules
├── includes/                  # PHP classes
│   ├── SkinWiki7.php          # Main skin class (extends SkinMustache)
│   ├── GetConfigTrait.php     # Shared config-reading trait
│   ├── Api/                   # Custom API modules
│   │   ├── ApiWebappManifest.php
│   │   └── ApiWebappManifestFormatJson.php
│   ├── Components/            # Template data providers (Wiki7Component interface)
│   │   ├── Wiki7Component.php           # Interface: getTemplateData(): array
│   │   ├── Wiki7ComponentFooter.php
│   │   ├── Wiki7ComponentKeyboardHint.php
│   │   ├── Wiki7ComponentLink.php
│   │   ├── Wiki7ComponentMainMenu.php
│   │   ├── Wiki7ComponentMenu.php
│   │   ├── Wiki7ComponentMenuListItem.php
│   │   ├── Wiki7ComponentPageFooter.php
│   │   ├── Wiki7ComponentPageHeading.php
│   │   ├── Wiki7ComponentPageSidebar.php
│   │   ├── Wiki7ComponentPageTools.php
│   │   ├── Wiki7ComponentSearchBox.php
│   │   ├── Wiki7ComponentSiteStats.php
│   │   └── Wiki7ComponentUserInfo.php
│   ├── Hooks/                 # MediaWiki hook handlers
│   │   ├── SkinHooks.php      # Page display, sidebar, edit section, navigation hooks
│   │   └── ResourceLoaderHooks.php  # Passes config to JS modules
│   └── Partials/              # Side-effect helpers (not template data)
│       ├── Partial.php        # Abstract base class for partials
│       ├── BodyContent.php    # Decorates body content HTML
│       ├── Metadata.php       # Adds <meta> tags to the page
│       └── Theme.php          # Handles theme switching (light/dark/auto)
├── templates/                 # Mustache templates (36 files)
│   ├── skin.mustache          # Root template
│   ├── Header.mustache        # Site header (logo, search, drawer, user menu)
│   ├── PageHeader.mustache    # Page heading + page tools
│   ├── PageSidebar.mustache   # Table of contents sidebar
│   ├── PageFooter.mustache    # Per-page footer (last modified, credits)
│   ├── Footer.mustache        # Site-wide footer
│   └── ...                    # 30 more partial templates
├── resources/                 # Frontend modules (JS, LESS, fonts)
│   ├── mediawiki.less/        # LESS variable overrides for MediaWiki core
│   ├── mixins.less            # Shared LESS mixins
│   ├── skins.wiki7.scripts/   # Main JS module
│   ├── skins.wiki7.search/    # Search typeahead module
│   ├── skins.wiki7.preferences/ # Client-side preferences (theme, font size, width)
│   ├── skins.wiki7.commandPalette/ # Experimental command palette (Vue + Pinia)
│   ├── skins.wiki7.serviceWorker/  # Service worker for offline caching
│   ├── skins.wiki7.styles/    # Core LESS styles
│   │   ├── skin.less          # Entry point — imports everything
│   │   ├── layout.less        # Page layout
│   │   ├── tokens.less        # Design tokens
│   │   ├── tokens-wiki7.less  # Wiki7-specific token overrides
│   │   ├── tokens-theme-base.less  # Base theme tokens
│   │   ├── tokens-theme-dark.less  # Dark theme tokens
│   │   ├── tokens-codex.less  # Codex design system tokens
│   │   ├── fonts.less         # Font face declarations (Roboto Flex)
│   │   ├── common/            # Typography, content, features, print styles
│   │   ├── components/        # Component-specific styles (Header, Footer, etc.)
│   │   ├── skinning/          # Content area styling overrides
│   │   ├── fonts/             # Roboto Flex woff2 font files
│   │   └── images/            # SVG icons
│   ├── skins.wiki7.styles.fonts.he/  # Hebrew font resources (Noto Sans Hebrew)
│   ├── skins.wiki7.styles.fonts.ar/  # Arabic font resources (Noto Naskh Arabic)
│   └── skins.wiki7.styles.fonts.cjk/ # CJK font resources (Noto Sans CJK)
├── skinStyles/                # Override styles for MediaWiki core + extensions
│   ├── mediawiki/             # Overrides for core MediaWiki modules
│   │   ├── action/            # Edit, history, file page styles
│   │   ├── special/           # Special page styles
│   │   ├── ui/                # MediaWiki UI element overrides
│   │   └── debug/             # Debug toolbar styles
│   ├── extensions/            # Overrides for 60+ extensions
│   │   ├── VisualEditor/
│   │   ├── Echo/
│   │   ├── SemanticMediaWiki/
│   │   ├── Cargo/
│   │   └── ...
│   ├── ooui/                  # OOUI widget style overrides
│   ├── jquery/                # jQuery plugin style overrides
│   ├── jquery.spinner/
│   └── lib/                   # Third-party library overrides (leaflet, tippy)
├── i18n/                      # Internationalization message files
│   ├── en.json                # English (default)
│   ├── he.json                # Hebrew
│   └── qqq.json               # Message documentation
└── licenses/                  # Font license files
    ├── Noto Sans CJK LICENSE
    └── Roboto Flex LICENSE
```

---

## Template Hierarchy

The skin uses Mustache templates. `skin.mustache` is the root template, and all others are included as partials via `{{>TemplateName}}`.

```
skin.mustache (root)
├── {{>Header}}
│   ├── {{>Header__logo}}
│   ├── {{>Search}}
│   │   └── {{>Search__button}}
│   ├── {{>Drawer}}
│   │   ├── {{>Drawer__button}}
│   │   ├── {{>Drawer__logo}}
│   │   ├── {{>MainMenu}}
│   │   │   └── {{>Menu}} → {{>MenuContents}} → {{>MenuListItem}}
│   │   ├── {{>SiteStats}}
│   │   └── {{>Wordmark}}
│   ├── {{>Preferences}}
│   ├── {{>Menu}} (notifications)
│   └── {{>UserMenu}}
│       └── {{>UserInfo}}
├── <main> (page container)
│   ├── {{>PageHeader}}
│   │   ├── {{>PageHeading}}
│   │   │   └── {{>Indicators}}
│   │   └── {{>PageTools}}
│   │       ├── {{>PageTools__languages}}
│   │       └── {{>PageTools__more}}
│   ├── (body content — html-body-content--formatted)
│   ├── {{>PageSidebar}} (table of contents, if enabled)
│   │   └── {{>TableOfContents}}
│   │       └── {{>TableOfContents__list}} → {{>TableOfContents__line}}
│   └── {{>PageFooter}}
│       └── {{>PageFooter__item}}
└── {{>Footer}}
    └── {{>Footer__row}}
```

Key points:
- `skin.mustache` wraps the page in `<div class="wiki7-page-container">`.
- The `<main>` element is the `.mw-body` content area.
- Table of contents sidebar only renders when `toc-enabled` is true.
- The Footer is site-wide; PageFooter is per-page (last modified, credits, copyright).

---

## PHP Components

### The Wiki7Component Interface

All template data providers implement the `Wiki7Component` interface:

```php
namespace MediaWiki\Skins\Wiki7\Components;

interface Wiki7Component {
    public function getTemplateData(): array;
}
```

Each component is responsible for gathering and formatting data that a specific Mustache template needs.

### How Components Are Used

In `SkinWiki7::getTemplateData()`, components are instantiated and their data is merged into the template context:

```php
$components = [
    'data-footer'       => new Wiki7ComponentFooter($localizer, $parentData['data-footer']),
    'data-main-menu'    => new Wiki7ComponentMainMenu($parentData['data-portlets-sidebar']),
    'data-page-footer'  => new Wiki7ComponentPageFooter($localizer, ...),
    'data-page-heading' => new Wiki7ComponentPageHeading($services, $localizer, ...),
    'data-page-sidebar' => new Wiki7ComponentPageSidebar($localizer, $out, ...),
    'data-page-tools'   => new Wiki7ComponentPageTools($config, $localizer, ...),
    'data-search-box'   => new Wiki7ComponentSearchBox($localizer, ...),
    'data-site-stats'   => new Wiki7ComponentSiteStats($config, $localizer, ...),
    'data-user-info'    => new Wiki7ComponentUserInfo($isRegistered, $isTemp, ...),
];

foreach ($components as $key => $component) {
    if ($component) {
        $parentData[$key] = $component->getTemplateData();
    }
}
```

The returned associative arrays become available to Mustache templates. For example, `data-page-heading` is used in `PageHeading.mustache` via `{{#data-page-heading}}`.

### Component List

| Component | Template | Purpose |
|-----------|----------|---------|
| `Wiki7ComponentFooter` | `Footer.mustache` | Site footer with custom tagline and description |
| `Wiki7ComponentMainMenu` | `MainMenu.mustache` | Drawer sidebar navigation |
| `Wiki7ComponentPageFooter` | `PageFooter.mustache` | Per-page last modified, credits, copyright |
| `Wiki7ComponentPageHeading` | `PageHeading.mustache` | Page title, tagline, indicators |
| `Wiki7ComponentPageSidebar` | `PageSidebar.mustache` | Table of contents panel |
| `Wiki7ComponentPageTools` | `PageTools.mustache` | Edit, history, languages, actions buttons |
| `Wiki7ComponentSearchBox` | `Search.mustache` | Search input and keyboard hints |
| `Wiki7ComponentSiteStats` | `SiteStats.mustache` | Article/file/user/edit counts in drawer |
| `Wiki7ComponentUserInfo` | `UserInfo.mustache` | User avatar, name, registration date |
| `Wiki7ComponentMenu` | `Menu.mustache` | Generic menu renderer |
| `Wiki7ComponentMenuListItem` | `MenuListItem.mustache` | Single menu item with icon |
| `Wiki7ComponentLink` | `Link.mustache` | Generic link renderer |
| `Wiki7ComponentKeyboardHint` | `KeyboardHint.mustache` | Keyboard shortcut hint badge |

### Partials (Side-Effect Classes)

Unlike components, partials do not return template data. They extend the abstract `Partial` class and modify the page through side effects:

| Partial | Purpose |
|---------|---------|
| `BodyContent` | Decorates `html-body-content` (wraps tables, adds overflow handling) |
| `Metadata` | Adds `<meta>` tags (theme-color, manifest, viewport) |
| `Theme` | Configures theme switching (light, dark, auto) and CSS class injection |

### Hooks

**SkinHooks** (`includes/Hooks/SkinHooks.php`) handles:
- `BeforePageDisplay` -- Injects inline JS for theme preferences
- `OutputPageAfterGetHeadLinksArray` -- Customizes viewport meta tag
- `SidebarBeforeOutput` / `SkinBuildSidebar` -- Adds icons and custom links to sidebar
- `SkinEditSectionLinks` -- Adds icons to edit section links
- `SkinPageReadyConfig` -- Disables default MW search wiring (Wiki7 has its own)
- `onSkinTemplateNavigation` -- Customizes all navigation menus (views, actions, user, notifications)

**ResourceLoaderHooks** (`includes/Hooks/ResourceLoaderHooks.php`) passes config to JS:
- `getWiki7ResourceLoaderConfig()` -- Preferences, overflow classes, search module, command palette toggle
- `getWiki7PreferencesResourceLoaderConfig()` -- Default theme
- `getWiki7SearchResourceLoaderConfig()` -- Search gateway, description source, max results
- `getWiki7CommandPaletteResourceLoaderConfig()` -- Search cache expiry

---

## JavaScript Modules

The skin registers 5 ResourceLoader modules (plus 2 supplementary ones) in `skin.json`:

### 1. `skins.wiki7.scripts` (Core)

**Entry point:** `resources/skins.wiki7.scripts/skin.js`

The main script module, loaded on every page. Handles:

| File | Purpose |
|------|---------|
| `skin.js` | Entry point: initializes dropdown, search, echo, lastModified, share; defers observers |
| `config.json` | Runtime config injected by `ResourceLoaderHooks` |
| `deferUntilFrame.js` | Utility to defer work until a specific animation frame |
| `dropdown.js` | Dropdown menu behavior |
| `echo.js` | Echo notification badge integration |
| `inline.js` | Inline script for early theme preference detection (injected into `<head>`) |
| `lastModified.js` | Formats "last modified" timestamps |
| `overflowElements.js` | Wraps overflowing tables/elements for horizontal scroll |
| `resizeObserver.js` | ResizeObserver utility |
| `scrollObserver.js` | Scroll position observer for sticky header |
| `search.js` | Search module loader (loads `skins.wiki7.search` or command palette) |
| `sectionObserver.js` | Tracks which section heading is in viewport (for TOC highlighting) |
| `sections.js` | Collapsible section toggling |
| `setupObservers.js` | Initializes all IntersectionObserver and ResizeObserver instances |
| `share.js` | "Share this page" button with clipboard API |
| `speculationRules.js` | Adds `<script type="speculationrules">` for prefetching |
| `stickyHeader.js` | Sticky header show/hide on scroll |
| `tableOfContents.js` | Dynamic table of contents with active section tracking |

### 2. `skins.wiki7.search` (Typeahead Search)

**Entry point:** `resources/skins.wiki7.search/main.js`

A custom search typeahead that replaces MediaWiki's default search suggestion. Features:
- Multiple search backends: `mwActionApi`, `mwRestApi`, `smwAskApi` (Semantic MediaWiki)
- Search history tracking via `mediawiki.storage`
- Result types: page results, full-text search, edit/create page, advanced search, media search
- Mustache templates for typeahead rendering

### 3. `skins.wiki7.preferences` (Client Preferences)

**Entry point:** `resources/skins.wiki7.preferences/skins.wiki7.preferences.js`

Manages client-side user preferences stored in browser:
- **Theme:** light / dark / auto
- **Auto-hide navigation:** on / off
- **Pure black mode:** on / off (for OLED dark theme)
- **Font size:** small / standard / large
- **Page width:** standard / wide / full

Preferences are applied via CSS class toggling on `<html>` using the `clientpref-` convention (e.g., `wiki7-feature-pure-black-clientpref-0`).

### 4. `skins.wiki7.commandPalette` (Experimental)

**Entry point:** `resources/skins.wiki7.commandPalette/init.js`

A Ctrl+K / Cmd+K command palette built with **Vue 3** and **Pinia**, using Codex UI components. Features:
- Page search, namespace filtering, action commands
- Recent items history
- Related articles provider
- Keyboard navigation

Disabled by default (`Wiki7EnableCommandPalette: false`). Uses `MediaWiki\ResourceLoader\CodexModule`.

### 5. `skins.wiki7.serviceWorker`

**Entry point:** `resources/skins.wiki7.serviceWorker/sw.js`

A service worker registered when `wgScriptPath` is at root (`/`). Provides basic offline caching. Registered from `skin.js` via `registerServiceWorker()`.

### Supplementary Modules

- **`skins.wiki7.icons`** -- OOUIIconPack module providing 60+ OOUI icons used throughout the skin
- **`skins.wiki7.commandPalette.codex`** -- Codex component dependencies for the command palette (CdxButton, CdxIcon, CdxTextInput, etc.)

---

## LESS/CSS Architecture

### How ResourceLoader Compiles LESS

MediaWiki's ResourceLoader compiles LESS files at runtime (with caching). The entry point for the main styles module is:

```
skin.json → ResourceModules → skins.wiki7.styles → styles → resources/skins.wiki7.styles/skin.less
```

`skin.less` imports all other LESS files:
- `tokens.less` / `tokens-wiki7.less` / `tokens-theme-*.less` -- Design tokens (CSS custom properties)
- `layout.less` -- Grid layout for page container, sidebar, body
- `fonts.less` -- @font-face for Roboto Flex
- `common/` -- Typography, content formatting, features, print styles, view transitions
- `components/` -- Individual UI component styles (Header, Footer, Search, TOC, etc.)
- `skinning/` -- Overrides for MediaWiki's default content styling (links, tables, thumbnails, etc.)

### Adding or Modifying Styles

1. **Component styles:** Edit files in `resources/skins.wiki7.styles/components/` (e.g., `Header.less`)
2. **Design tokens:** Modify `tokens-wiki7.less` for Wiki7-specific values, `tokens-theme-dark.less` for dark theme
3. **Content styling:** Edit files in `resources/skins.wiki7.styles/skinning/`
4. **New LESS file:** Add it to the appropriate directory and import it from `skin.less`
5. **Extension skin styles:** Add overrides in `skinStyles/extensions/<ExtensionName>/` and register them in `skin.json` under `ResourceModuleSkinStyles`

### LESS Variables and Mixins

- `resources/mediawiki.less/mediawiki.skin.variables.less` overrides MediaWiki's default LESS variables
- `resources/mixins.less` provides shared LESS mixins used across the skin

### skinStyles (Extension Overrides)

The `skinStyles/` directory contains LESS overrides for 60+ MediaWiki extensions and core modules. These are registered in `skin.json` under `ResourceModuleSkinStyles` and are automatically loaded by ResourceLoader when the corresponding module is active.

Naming convention: the key in `skin.json` matches the target module name with a `+` prefix (meaning "append to"), and the value points to the override file.

Example:
```json
"+ext.visualEditor.core": "skinStyles/extensions/VisualEditor/ext.visualEditor.core.less"
```

---

## Internationalization (i18n)

### Message Files

The skin ships with three i18n files in `i18n/`:

| File | Purpose |
|------|---------|
| `en.json` | English messages (default/fallback) |
| `he.json` | Hebrew translations |
| `qqq.json` | Message documentation (describes each message key for translators) |

### Message Format

Each file is a JSON object with an `@metadata` header and key-value message pairs:

```json
{
    "@metadata": {
        "authors": ["Author Name"]
    },
    "skinname-wiki7": "Wiki7",
    "wiki7-drawer-toggle": "Toggle menu",
    "wiki7-search-toggle": "Toggle search"
}
```

All message keys are prefixed with `wiki7-` (except `skinname-wiki7`).

### Adding Hebrew Translations

1. Open `i18n/he.json`
2. Add the key with its Hebrew translation:
   ```json
   "wiki7-new-feature-label": "תווית חדשה"
   ```
3. Add documentation in `i18n/qqq.json`:
   ```json
   "wiki7-new-feature-label": "Label for the new feature button shown in the toolbar"
   ```
4. Add the English default in `i18n/en.json`:
   ```json
   "wiki7-new-feature-label": "New feature"
   ```

### Using Messages

**In PHP:**
```php
$localizer->msg('wiki7-drawer-toggle')->text()
```

**In Mustache templates:**
```mustache
{{msg-wiki7-drawer-toggle}}
```

**In JavaScript (via ResourceLoader):**
```js
mw.msg('wiki7-drawer-toggle')
```

Messages must be declared in the `messages` array of the relevant ResourceLoader module in `skin.json` to be available in JavaScript.

---

## Configuration Options

All skin configuration is defined in `skin.json` under `config` with the `wgWiki7` prefix. Key options:

| Config Key | Default | Description |
|-----------|---------|-------------|
| `ThemeDefault` | `"auto"` | Default theme: `"light"`, `"dark"`, or `"auto"` |
| `ThemeColor` | `"#0d0e12"` | `<meta name="theme-color">` value |
| `EnableManifest` | `true` | Enable web app manifest |
| `SearchModule` | `"skins.wiki7.search"` | Search module to use |
| `SearchGateway` | `"mwRestApi"` | Search backend: `mwActionApi`, `mwRestApi`, or custom |
| `SearchDescriptionSource` | `"textextracts"` | Source for search result descriptions |
| `MaxSearchResults` | `10` | Maximum search suggestions shown |
| `EnableCollapsibleSections` | `true` | Enable collapsible content sections |
| `EnablePreferences` | `true` | Enable client preferences panel |
| `EnableCJKFonts` | `false` | Load Noto Sans CJK fonts |
| `EnableARFonts` | `false` | Load Noto Naskh Arabic fonts |
| `EnableHEFonts` | `false` | Load Hebrew fonts (only for Hebrew content pages) |
| `EnableCommandPalette` | `false` | Enable experimental Ctrl+K command palette |
| `TableOfContentsCollapseAtCount` | `28` | Heading count threshold to collapse TOC |

---

## Customizations from Citizen

Wiki7 is a fork of the [Citizen skin](https://www.mediawiki.org/wiki/Skin:Citizen) v3.1.0 with the following customizations:

1. **Rebranding:** All class names, config keys, and module names have been renamed from `citizen-` / `Citizen` to `wiki7-` / `Wiki7` throughout the codebase.

2. **Hebrew RTL Support:**
   - Dedicated Hebrew font module (`skins.wiki7.styles.fonts.he`) with Noto Sans Hebrew
   - Hebrew font loading is conditional on the page content language being `he`
   - Full Hebrew translation in `i18n/he.json` (80+ messages)

3. **Theme Colors:** Custom dark theme color (`#0d0e12`) matching Hapoel Beer Sheva FC branding.

4. **Configuration Prefix:** All configuration keys use `wgWiki7` instead of `wgCitizen`.

5. **Namespace:** PHP namespace is `MediaWiki\Skins\Wiki7` instead of `MediaWiki\Skins\Citizen`.

When upgrading, changes from upstream Citizen should be carefully merged to preserve these customizations. The upstream Citizen skin is currently at v3.13.0 (12 versions ahead), so upgrading will require significant effort.
