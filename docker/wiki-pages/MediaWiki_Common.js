/* ===================================================================
 * ויקישבע — Main Page JavaScript
 * Lightweight vanilla JS slider (no external dependencies)
 * =================================================================== */

( function () {
    'use strict';

    /**
     * Initialize the homepage slider with auto-play, dots, and swipe.
     */
    function initSlider() {
        var slider = document.querySelector( '.wiki7-slider' );
        if ( !slider ) return;

        var track = slider.querySelector( '.wiki7-slider__track' );
        var slides = slider.querySelectorAll( '.wiki7-slider__slide' );
        var dotsContainer = slider.querySelector( '.wiki7-slider__dots' );

        if ( !track || slides.length === 0 ) return;

        var currentIndex = 0;
        var slideCount = slides.length;
        var autoPlayInterval = null;
        var autoPlayDelay = 6000; // 6 seconds per slide
        var touchStartX = 0;
        var touchEndX = 0;

        // Create dots
        if ( dotsContainer ) {
            for ( var i = 0; i < slideCount; i++ ) {
                var dot = document.createElement( 'button' );
                dot.className = 'wiki7-slider__dot' + ( i === 0 ? ' wiki7-slider__dot--active' : '' );
                dot.setAttribute( 'aria-label', 'שקופית ' + ( i + 1 ) + ' מתוך ' + slideCount );
                dot.dataset.index = i;
                dot.addEventListener( 'click', function () {
                    goToSlide( parseInt( this.dataset.index, 10 ) );
                    resetAutoPlay();
                } );
                dotsContainer.appendChild( dot );
            }
        }

        // Create arrow navigation zones
        function createArrowZone( direction ) {
            var zone = document.createElement( 'div' );
            zone.className = 'wiki7-slider__arrow-zone wiki7-slider__arrow-zone--' + direction;

            var btn = document.createElement( 'button' );
            btn.className = 'wiki7-slider__arrow-btn';
            btn.setAttribute( 'aria-label', direction === 'prev' ? 'השקופית הקודמת' : 'השקופית הבאה' );
            btn.setAttribute( 'type', 'button' );

            var icon = document.createElement( 'span' );
            icon.className = 'wiki7-slider__arrow-icon wiki7-slider__arrow-icon--' + direction;
            btn.appendChild( icon );

            btn.addEventListener( 'click', function ( e ) {
                e.stopPropagation();
                if ( direction === 'prev' ) {
                    prevSlide();
                } else {
                    nextSlide();
                }
                resetAutoPlay();
            } );

            zone.appendChild( btn );
            slider.appendChild( zone );
        }

        createArrowZone( 'prev' );
        createArrowZone( 'next' );

        function goToSlide( index ) {
            if ( index < 0 ) index = slideCount - 1;
            if ( index >= slideCount ) index = 0;
            currentIndex = index;

            // RTL: use positive translateX since direction is reversed
            var direction = document.documentElement.dir === 'rtl' ? 1 : -1;
            track.style.transform = 'translateX(' + ( direction * currentIndex * 100 ) + '%)';

            // Update dots
            var dots = dotsContainer ? dotsContainer.querySelectorAll( '.wiki7-slider__dot' ) : [];
            for ( var j = 0; j < dots.length; j++ ) {
                dots[ j ].classList.toggle( 'wiki7-slider__dot--active', j === currentIndex );
            }
        }

        function nextSlide() {
            goToSlide( currentIndex + 1 );
        }

        function prevSlide() {
            goToSlide( currentIndex - 1 );
        }

        // Auto-play
        function startAutoPlay() {
            autoPlayInterval = setInterval( nextSlide, autoPlayDelay );
        }

        function stopAutoPlay() {
            if ( autoPlayInterval ) {
                clearInterval( autoPlayInterval );
                autoPlayInterval = null;
            }
        }

        function resetAutoPlay() {
            stopAutoPlay();
            startAutoPlay();
        }

        // Pause on hover
        slider.addEventListener( 'mouseenter', stopAutoPlay );
        slider.addEventListener( 'mouseleave', startAutoPlay );

        // Touch/swipe support
        slider.addEventListener( 'touchstart', function ( e ) {
            touchStartX = e.changedTouches[ 0 ].screenX;
        }, { passive: true } );

        slider.addEventListener( 'touchend', function ( e ) {
            touchEndX = e.changedTouches[ 0 ].screenX;
            var diff = touchStartX - touchEndX;
            var threshold = 50;

            // RTL: swipe directions are reversed
            var isRTL = document.documentElement.dir === 'rtl';

            if ( Math.abs( diff ) > threshold ) {
                if ( ( diff > 0 && !isRTL ) || ( diff < 0 && isRTL ) ) {
                    nextSlide();
                } else {
                    prevSlide();
                }
                resetAutoPlay();
            }
        }, { passive: true } );

        // Keyboard navigation when slider is focused
        slider.setAttribute( 'tabindex', '0' );
        slider.addEventListener( 'keydown', function ( e ) {
            var isRTL = document.documentElement.dir === 'rtl';
            if ( e.key === 'ArrowLeft' ) {
                isRTL ? nextSlide() : prevSlide();
                resetAutoPlay();
            } else if ( e.key === 'ArrowRight' ) {
                isRTL ? prevSlide() : nextSlide();
                resetAutoPlay();
            }
        } );

        // Start auto-play
        startAutoPlay();

        // Pause auto-play when tab is not visible
        document.addEventListener( 'visibilitychange', function () {
            if ( document.hidden ) {
                stopAutoPlay();
            } else {
                startAutoPlay();
            }
        } );
    }

    /**
     * Initialize quick-access icon shortcuts in the header bar.
     */
    function initHeaderQuickAccess() {
        var header = document.querySelector( '.wiki7-header' );
        if ( !header ) return;

        var headerInner = header.querySelector( '.wiki7-header__inner' );
        if ( !headerInner ) return;

        var items = [
            { id: 'team',      label: 'הקבוצה',       desc: 'דף המועדון הראשי',     href: '/wiki/הפועל_באר_שבע' },
            { id: 'players',   label: 'שחקנים',       desc: 'שחקני המועדון',         href: '/wiki/קטגוריה:שחקנים' },
            { id: 'seasons',   label: 'עונות',        desc: 'עונות המועדון',         href: '/wiki/קטגוריה:עונות' },
            { id: 'trophies',  label: 'תארים',        desc: 'תארים והישגים',         href: '/wiki/תארים' },
            { id: 'stadium',   label: 'האצטדיון',     desc: 'אצטדיון טוטו טרנר',     href: '/wiki/אצטדיון_טוטו_טרנר' },
            { id: 'transfers', label: 'העברות',       desc: 'מעברי שחקנים',          href: '/wiki/קטגוריה:העברות' },
            { id: 'stats',     label: 'סטטיסטיקות',   desc: 'נתונים וסטטיסטיקות',    href: '/wiki/סטטיסטיקות' }
        ];

        var container = document.createElement( 'div' );
        container.className = 'wiki7-header__quick-access';

        for ( var i = 0; i < items.length; i++ ) {
            var item = items[ i ];
            var link = document.createElement( 'a' );
            link.className = 'wiki7-header__quick-link';
            link.href = item.href;
            link.setAttribute( 'aria-label', item.label );
            link.setAttribute( 'data-tooltip', item.label );

            var icon = document.createElement( 'span' );
            icon.className = 'wiki7-header__quick-link-icon wiki7-header__quick-link-icon--' + item.id;
            link.appendChild( icon );

            // Mini card preview
            var card = document.createElement( 'div' );
            card.className = 'wiki7-header__quick-card';

            var cardTitle = document.createElement( 'div' );
            cardTitle.className = 'wiki7-header__quick-card-title';
            cardTitle.textContent = item.label;
            card.appendChild( cardTitle );

            var cardDesc = document.createElement( 'div' );
            cardDesc.className = 'wiki7-header__quick-card-desc';
            cardDesc.textContent = item.desc;
            card.appendChild( cardDesc );

            link.appendChild( card );
            container.appendChild( link );
        }

        header.insertBefore( container, headerInner );
    }

    // Initialize when DOM is ready
    if ( document.readyState === 'loading' ) {
        document.addEventListener( 'DOMContentLoaded', function () {
            initSlider();
            initHeaderQuickAccess();
        } );
    } else {
        initSlider();
        initHeaderQuickAccess();
    }
}() );
