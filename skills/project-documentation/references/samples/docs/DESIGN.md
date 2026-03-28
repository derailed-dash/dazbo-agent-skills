# Design and UX Guide

This document defines the visual identity, frontend user interface components, and command-line experience for the **Dazbo Portfolio** application.

## Visual Identity

The portfolio follows a high-contrast, premium aesthetic branded as the **"Midnight" Theme**, a refined Material 3-inspired design.

*   **Typography**:
    *   **Main stack**: `'Inter'`, `'Roboto'`, sans-serif. 
    *   **Weights**: 400 (Regular), 500 (Medium/Active Links), 600 (Semi-Bold), 700 (Bold/Titles).
    *   **Rendering**: Optimized legibility with `-webkit-font-smoothing: antialiased`.
*   **Color Palette**:
    *   **Background**: `#000000` (Pure Black).
    *   **Surface/Cards**: `#FFFFFF` (White).
    *   **Primary Accent**: `#6200EE` (Purple).
    *   **Secondary/Action**: `#03DAC6` (Teal).
    *   **Branding Accent**: `#BB86FC` (Light Purple).
*   **Elevation**: Three distinct shadow levels (`--md-sys-elevation-1` through `3`) provide depth and interaction feedback for Material surfaces.

## Visual Effects

Key visual patterns that contribute to the premium feel:

### Glassmorphism

A core design pattern using `backdrop-filter: blur(10px)` and semi-transparent backgrounds:
*   **`.btn-glass`**: Transparent buttons with white borders and subtle hover glows.
*   **`.glass-card`**: Low-opacity containers for markdown content and background elements.
*   **`.glass-tag`**: High-contrast, blurred labels used for technology tags.

### Premium Interactions

*   **Custom Scrollbars**: Minimalist dark-themed scrollbars with smooth rounded thumbs (`#333` to `#555` on hover).
*   **Surface Transitions**: Material cards use a 0.3s ease-in-out transition for elevation shifts and a `translateY(-4px)` lift on hover.

## Frontend Implementation

The frontend is a single-page application (SPA) built with React and Vite. It is designed to be responsive, performant, and visually consistent with the Material Design system.

### Key Components

*   **`MainLayout`**: The top-level wrapper for all pages. It includes the `AppNavbar` (top), `Footer` (bottom), and the `ChatWidget`.
*   **`ShowcaseCarousel`**: A reusable component for displaying collections of items (blogs, projects, etc.).
    *   **Responsiveness**: On mobile, it displays 1 item per slide. On desktop, it displays a grid of 3 items per slide.
    *   **Navigation**: Includes custom-styled solid black "Previous" and "Next" controls with white borders and indicators.
*   **`ProjectCarousel`**: Specifically configured to sort GitHub projects, prioritising those updated within the last 45 days (must have >0 stars) to highlight active work, followed by a fallback sort based on star count.
*   **`ChatWidget`**: A floating action button (FAB) that expands into a chat interface. It currently serves as a shell for future agent integration.
*   **`AboutPage`**: A dedicated page for the professional profile, rendering Markdown content from Firestore with a glassmorphic UI design.

### Markdown Rendering (UX)

The application handles Markdown content from Firestore with a focus on professional presentation:
*   **Premium Blockquotes**: Features a left-border accent (`--md-sys-color-primary`), glassmorphic background, and distinct attribution styling (uppercase, semi-bold).
*   **Glass Tags**: Inline code is rendered as high-readability glassmorphic tags to visually set apart technical terms.

### Development Workflow

There are two primary ways to run the application locally:

#### 1. Process Mode (Rapid Frontend/Backend Iteration)

Ideal for daily development with hot-reloading.

1.  **Start the Backend**: `make local-backend` (port 8000).
2.  **Start the Frontend**: `make react-ui` (port 5173).
3.  **Access**: `http://localhost:5173`. Requests to `/api/*` are proxied to port 8000.

#### 2. Container Mode (Production Parity)

Ideal for verifying the final build and deployment configuration.
1.  **Build**: `make docker-build`.
2.  **Run**: `make docker-run`.
3.  **Access**: `http://localhost:8080`. Port 8080 serves both the UI and the API.

## Command-Line Experience (CLI UX)

The CLI tools are designed for immediate visual feedback and clarity when managing content.

### Console UX with Rich
The application uses the `rich` library to enhance the CLI experience with spinners, progress bars, and thread-safe logging. This ensures a clean and readable output during long-running ingestion tasks.
