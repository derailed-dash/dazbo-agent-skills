---
version: "1.0"
name: "Minimalism & Swiss Style"
description: "A high-contrast, grid-based design system inspired by 1950s Swiss typography."
colors:
  primary: "#000000"
  secondary: "#F5F1E8"
  tertiary: "#808080"
  surface: "#FFFFFF"
  background: "#F5F1E8"
  error: "#dc2626"
  success: "#16a34a"
  warning: "#d97706"
typography:
  display-lg:
    fontFamily: "Helvetica, Arial, sans-serif"
    fontSize: "64px"
    fontWeight: 700
    lineHeight: "1.1"
    letterSpacing: "-0.05em"
  body-md:
    fontFamily: "Helvetica, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: "1.6"
    letterSpacing: "0"
rounded:
  sm: "0px"
  md: "0px"
  lg: "0px"
  full: "0px"
spacing:
  sm: "4px"
  md: "8px"
  lg: "16px"
  xl: "32px"
components:
  button:
    borderRadius: "0px"
    padding: "8px 16px"
    border: "1px solid #000"
  card:
    background: "#FFFFFF"
    border: "1px solid #000"
    boxShadow: "none"
---

# Design System: Minimalism & Swiss Style

## Overview

This system is inspired by the International Typographic Style (Swiss Style) of the 1950s. It emphasizes cleanliness, readability, and objectivity through the use of asymmetric layouts, a rigid mathematical grid, and sans-serif typography.

## Colors

The palette is intentionally limited to create a strong, functional visual hierarchy.
- **Black (#000000)**: Used for all primary content, headlines, and structural lines.
- **White (#FFFFFF)**: Used for content surfaces and negative space.
- **Beige (#F5F1E8)**: The default background color, providing a warm, archival paper feel.
- **Grey (#808080)**: Used for secondary metadata and borders.

## Typography

Helvetica (or a clean sans-serif fallback) is the cornerstone of this system.
- **Headlines**: Oversized and bold. The goal is to make the typography itself a primary graphic element.
- **Body**: Set with generous leading (1.6) to ensure maximum legibility against the beige background.
- **Alignment**: Flush-left, ragged-right is preferred to maintain a modern, dynamic feel.

## Layout

A strict 8px baseline grid is used to align all elements.
- **Asymmetry**: Content should be balanced through white space rather than perfect symmetry.
- **Margins**: Large, consistent margins (xl spacing) are used to frame content.

## Elevation & Depth

This system is strictly 2D. 
- **No Shadows**: Depth is created through layering and size variation rather than drop shadows or blurs.
- **Borders**: 1px solid black lines are the only method for defining boundaries.

## Shapes

Sharp edges only.
- **Rounded Corners**: Banned. All UI elements (buttons, cards, inputs) must have a `0px` radius to maintain the geometric integrity of the system.

## Components

### Buttons
Buttons are simple rectangles with a 1px border. On hover, the background flips to solid black with white text.

### Cards
Cards use a white background and a 1px border. There is no hover elevation; instead, the border weight might increase to 2px.

## Do's and Don't's

- **Do**: Prioritize typography over images.
- **Do**: Use whitespace as a functional element.
- **Don't**: Use rounded corners, gradients, or shadows.
- **Don't**: Use more than two colors on a single screen besides black and white.
