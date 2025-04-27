# Wiki7Skin

A custom MediaWiki skin for the Wiki7 Hapoel Beer Sheva Fan Wiki project. This skin is designed to create a modern, responsive wiki experience with a design inspired by Maccabipedia and Wikipoel, featuring the team colors (red and white) of Hapoel Beer Sheva FC.

## Project Structure

```
Wiki7Skin/
├── Wiki7Skin.php              # Main skin PHP file
├── skin.json                   # Skin metadata and registration
├── README.md                   # This file
├── INSTALLATION.md             # Installation instructions
├── resources/                  # CSS, JavaScript, and image files
│   ├── images/                 # Images used by the skin
│   │   └── logo.svg           # Default logo
│   ├── scripts/                # JavaScript files
│   │   └── main.js            # Main JavaScript file
│   └── styles/                 # CSS files
│       ├── Wiki7Skin.less     # Main stylesheet
│       └── Wiki7Skin.rtl.less # RTL stylesheet for Hebrew
├── templates/                  # Template files
│   ├── skin.mustache          # Main template
│   └── Menu.mustache          # Menu template
└── i18n/                      # Internationalization files
    ├── en.json                # English translations
    └── he.json                # Hebrew translations
```

## Features

- Responsive design that works on desktop and mobile devices
- Team colors integration (red and white)
- RTL support for Hebrew language
- Consistent navigation menus
- Mobile-friendly navigation with collapsible sections
- Enhanced TOC (Table of Contents) with smooth scrolling
- Modern, clean layout inspired by contemporary wiki designs
- Customizable through MediaWiki preferences and LocalSettings.php

## Design Principles

1. **Team Identity**: Emphasizes Hapoel Beer Sheva's colors and branding
2. **Readability**: Clean typography and spacing for improved content consumption
3. **Mobile-First**: Responsive design that works well on all devices
4. **Bilingual Support**: Full support for both Hebrew and English
5. **Performance**: Optimized CSS and JavaScript for fast loading

## Browser Compatibility

- Chrome 60+
- Firefox 60+
- Safari 11+
- Edge 79+
- Opera 47+
- Mobile Safari and Chrome for Android

## Customization

See `INSTALLATION.md` for detailed customization options including:

- Custom CSS additions
- Custom JavaScript
- Logo customization
- Site name and tagline configuration

## Development

To contribute to this skin:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the GPL-2.0-or-later license - see [MediaWiki's licensing](https://www.mediawiki.org/wiki/Special:MyLanguage/License) for details.

## Credits

This skin was developed for the Wiki7 - Hapoel Beer Sheva Fan Wiki project.

## Related Projects

- [MediaWiki](https://www.mediawiki.org/)
- [AWS Deployment for MediaWiki](https://aws.amazon.com/blogs/architecture/field-notes-how-to-scale-a-mediaserver-like-mediawiki-using-aws/)