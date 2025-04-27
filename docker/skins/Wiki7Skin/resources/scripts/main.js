/**
 * JavaScript for HapoelSkin
 */
( function () {
    'use strict';
    
    /**
     * Add mobile navigation toggle
     */
    function initMobileNav() {
        // Check if we're on a mobile device
        if (window.innerWidth <= 768) {
            var navToggle = document.createElement('button');
            navToggle.className = 'mw-nav-toggle';
            navToggle.textContent = 'Menu';
            
            var navContainer = document.getElementById('mw-navigation');
            if (navContainer) {
                // Insert the toggle button before the navigation
                navContainer.parentNode.insertBefore(navToggle, navContainer);
                
                // Initially hide the navigation
                navContainer.style.display = 'none';
                
                // Toggle the navigation when the button is clicked
                navToggle.addEventListener('click', function() {
                    if (navContainer.style.display === 'none') {
                        navContainer.style.display = 'block';
                        navToggle.textContent = 'Close';
                    } else {
                        navContainer.style.display = 'none';
                        navToggle.textContent = 'Menu';
                    }
                });
            }
        }
    }
    
    /**
     * Add smooth scrolling to TOC links
     */
    function initSmoothScroll() {
        // Get all links in the Table of Contents
        var tocLinks = document.querySelectorAll('.toc a');
        
        tocLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                // Get the target element's ID from the link's href
                var targetId = this.getAttribute('href').substring(1);
                var targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    e.preventDefault();
                    
                    // Smoothly scroll to the target element
                    window.scrollTo({
                        top: targetElement.offsetTop - 70, // Adjust for header height
                        behavior: 'smooth'
                    });
                    
                    // Update the URL
                    history.pushState(null, null, '#' + targetId);
                }
            });
        });
    }
    
    /**
     * Highlight the current section in TOC based on scroll position
     */
    function initTocHighlight() {
        var tocLinks = document.querySelectorAll('.toc a');
        var sections = [];
        
        // Get all sections referenced by TOC
        tocLinks.forEach(function(link) {
            var targetId = link.getAttribute('href').substring(1);
            var targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                sections.push({
                    id: targetId,
                    element: targetElement,
                    link: link
                });
            }
        });
        
        // Add scroll event listener
        window.addEventListener('scroll', function() {
            var scrollPosition = window.scrollY;
            
            // Find the current section
            var currentSection = null;
            sections.forEach(function(section) {
                if (section.element.offsetTop - 100 <= scrollPosition) {
                    currentSection = section;
                }
            });
            
            // Highlight the current section in TOC
            if (currentSection) {
                tocLinks.forEach(function(link) {
                    link.classList.remove('active');
                });
                currentSection.link.classList.add('active');
            }
        });
    }
    
    /**
     * Add collapsible sections for mobile view
     */
    function initCollapsibleSections() {
        var sidebarSections = document.querySelectorAll('#mw-panel > div');
        
        sidebarSections.forEach(function(section) {
            var heading = section.querySelector('h3, h4');
            
            if (heading && window.innerWidth <= 768) {
                var content = section.querySelector('ul, div');
                
                if (content) {
                    // Initially hide the content
                    content.style.display = 'none';
                    
                    // Make the heading clickable
                    heading.style.cursor = 'pointer';
                    heading.addEventListener('click', function() {
                        if (content.style.display === 'none') {
                            content.style.display = 'block';
                            heading.classList.add('expanded');
                        } else {
                            content.style.display = 'none';
                            heading.classList.remove('expanded');
                        }
                    });
                }
            }
        });
    }
    
    /**
     * Initialize the skin
     */
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'interactive' || document.readyState === 'complete') {
            initMobileNav();
            initSmoothScroll();
            initTocHighlight();
            initCollapsibleSections();
        } else {
            document.addEventListener('DOMContentLoaded', function() {
                initMobileNav();
                initSmoothScroll();
                initTocHighlight();
                initCollapsibleSections();
            });
        }
    }
    
    // Run initialization
    init();
    
} )();