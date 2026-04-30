---
version: "1.0"
name: "Midnight Portfolio Theme"
description: "A premium, high-contrast Material 3-inspired design system for professional portfolios."
colors:
  primary: "#6200EE"
  secondary: "#03DAC6"
  tertiary: "#BB86FC"
  surface: "#FFFFFF"
  background: "#000000"
  error: "#B3261E"
  on-primary: "#FFFFFF"
  on-surface: "#000000"
typography:
  display-lg:
    fontFamily: "Inter, Roboto, sans-serif"
    fontSize: "57px"
    fontWeight: 700
    lineHeight: "64px"
    letterSpacing: "-0.25px"
  body-md:
    fontFamily: "Inter, Roboto, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: "24px"
    letterSpacing: "0.5px"
rounded:
  sm: "4px"
  md: "8px"
  lg: "16px"
  full: "9999px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  glass-card:
    background: "rgba(255, 255, 255, 0.05)"
    backdropFilter: "blur(10px)"
    border: "1px solid rgba(255, 255, 255, 0.1)"
---

# Design and UX Guide

This document defines the visual identity, frontend user interface components, and command-line experience for the **Midnight Portfolio** application.

## Overview

The "Midnight" theme is designed to convey a premium, technical, and professional atmosphere. It leverages deep blacks and vibrant accents to create a high-impact visual experience that prioritizes readability and modern aesthetics.

## Colors

The palette is anchored by a pure black background (`#000000`) to provide maximum contrast for primary and secondary accents. 
- **Primary Purple (`#6200EE`)**: Used for brand-level elements and primary actions.
- **Secondary Teal (`#03DAC6`)**: Used for success states, active links, and complementary interactions.
- **Surface White (`#FFFFFF`)**: Used sparingly for card backgrounds to provide "islands" of content against the dark void.

## Typography

The system uses **Inter** as the primary typeface for its exceptional legibility at all scales. **Roboto** serves as a secondary fallback.
- **Headlines**: Use heavy weights (700) with tight tracking to create a bold, authoritative feel.
- **Body Text**: Uses a standard 16px size with a generous 1.5 line-height for long-form reading comfort.
- **UI Labels**: Rendered at 14px with medium weight (500) for clarity in navigation.

## Layout

The layout follows a centered 12-column grid with a maximum container width of 1280px.
- **Gutter**: 24px (Large spacing token).
- **Side Padding**: 16px on mobile, scaling to 32px on desktop.
- **Vertical Rhythm**: Built using the 8px base unit (`sm` spacing).

## Elevation & Depth

Midnight utilizes Material 3 elevation principles, but adapts them for a dark theme:
- **Level 1**: Subtle 1px border stroke.
- **Level 2**: Tonal overlay (5% white opacity).
- **Level 3**: Soft glow shadow using the primary color at 10% opacity.

## Shapes

Corners are consistently rounded using the defined tokens:
- **Buttons**: `md` (8px) for a modern, approachable feel.
- **Cards**: `lg` (16px) to clearly define content containers.
- **Tags/Pills**: `full` (9999px) for secondary metadata.

## Components

### Glassmorphism Pattern

A core design pattern using `backdrop-filter: blur(10px)` and semi-transparent backgrounds.
- **`.glass-card`**: Low-opacity containers for markdown content and background elements.
- **`.glass-tag`**: High-contrast, blurred labels used for technology tags.

### Showcase Carousel

- **Responsiveness**: 1 item on mobile, 3 items on desktop.
- **UX**: Solid black navigation controls with white borders to ensure visibility against varied content backgrounds.

## Do's and Don't's

- **Do**: Use pure black for the main background to maintain the theme's high-contrast identity.
- **Do**: Use Teal for positive actions and Purple for brand-specific highlights.
- **Don't**: Use soft gradients or drop shadows that decrease contrast on dark surfaces.
- **Don't**: Use serif fonts for body text as they conflict with the technical "Inter" aesthetic.

## Development CLI UX

The CLI experience is enhanced using the `rich` library:
- **Spinners**: Used during long-running ingestion or build tasks.
- **Progress Bars**: Provide real-time feedback for batch processes.
- **Tables**: All metadata and configuration lists are rendered in clean, bordered console tables.
