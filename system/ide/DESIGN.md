# Design System Specification: High-Tech IDE

## 1. Overview & Creative North Star
**Creative North Star: "The Kinetic Monolith"**

In high-performance engineering, tools should feel like high-precision instruments—cold, sharp, and undeniably powerful. This design system departs from the "browser-tab" aesthetic of modern IDEs to embrace a cinematic, editorial technicality. We achieve this by breaking the rigid, boxed-in grid of traditional development environments. 

Instead of a flat sea of panels, we utilize **Intentional Asymmetry** and **Tonal Depth**. Navigation elements are offset, and code editors are treated as the "Hero" of the layout, framed by deep navy voids. This is not just a tool; it is a high-tech cockpit that prioritizes focus through "The Darkest Dark" and "The Sharpest Sharp."

---

## 2. Colors & Surface Logic

The palette is anchored in deep oceanic navies (`#0d141d`) and electrified by high-contrast blues (`#adc7ff`). 

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to section off UI areas (e.g., separating the file tree from the editor). Boundaries must be defined solely through background color shifts or subtle tonal transitions.
*   **Editor Background:** `surface` (#0d141d)
*   **Sidebar/Panel Background:** `surface_container_low` (#151c26)
*   **Floating Modals:** `surface_container_highest` (#2e353f)

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. Use the `surface_container` tiers to create "nested" depth:
*   **Base Layer:** `surface_dim` (#0d141d) – The foundation.
*   **Interaction Layer:** `surface_container_low` (#151c26) – Sidebars and non-active panels.
*   **Active Layer:** `surface_container_high` (#242a34) – Active tabs or highlighted code blocks.

### The "Glass & Gradient" Rule
To move beyond a "standard" dark mode, use Glassmorphism for floating UI elements like command palettes or hover-tooltips.
*   **Formula:** `surface_container_highest` at 80% opacity + 20px Backdrop Blur.
*   **Signature Textures:** Apply a subtle linear gradient to Primary CTAs: `primary` (#adc7ff) to `primary_container` (#4a8eff) at a 135° angle.

---

## 3. Typography: The Technical Voice

We utilize **Space Grotesk** for all structural and display elements to lean into the "High-Tech" aesthetic. Its idiosyncratic letterforms provide a signature "NASA-spec" look.

*   **Display (Display-LG/MD):** Used for version numbers, major project headers, or empty-state titles. It should feel authoritative.
*   **Headline & Title:** Used for panel titles (e.g., "TERMINAL", "DEBUGGER"). Use all-caps with `0.05em` letter spacing for a professional, modular feel.
*   **Body (Inter):** While Space Grotesk handles the brand, **Inter** is used for the actual code and body text (`body-md`) to ensure maximum legibility during 12-hour coding sessions. 
*   **Labels (Label-SM):** Used for status bars and micro-metadata.

---

## 4. Elevation & Depth

Hierarchy is achieved through **Tonal Layering** rather than structural lines.

### The Layering Principle
Depth is achieved by "stacking" the surface-container tiers. Place a `surface_container_lowest` (#080f18) terminal area inside a `surface_container_low` (#151c26) main window to create a "recessed" feel.

### Ambient Shadows
For floating elements (Modals, Context Menus), use ultra-diffused shadows:
*   **Blur:** 40px - 60px.
*   **Opacity:** 15%.
*   **Color:** `on_surface` (#dce3f0) tinted toward the background navy to simulate ambient light bleed.

### The "Ghost Border" Fallback
If an edge *must* be defined for accessibility, use a **Ghost Border**:
*   Token: `outline_variant` (#414754) at 15% opacity. Never use 100% opaque lines.

---

## 5. Components

### Buttons
*   **Primary:** Gradient of `primary` to `primary_container`. Text color: `on_primary` (#002e68). No border. Roundedness: `sm` (0.125rem) for a sharp, technical edge.
*   **Tertiary (Ghost):** No background. Text: `primary`. On hover, use `surface_bright` (#333a44) at 10% opacity.

### The "Code Block" Card
Forbid the use of divider lines between lines of code or files. Use vertical white space (`spacing.2`) and a `surface_container_highest` background on hover to indicate selection.

### Chips & Badges
*   **Success Indicator:** `tertiary` (#00e639) text on a `tertiary_container` (#00a827) background at 20% opacity. This "vibrant green" should pop against the navy.

### Input Fields
*   **State:** Unfocused inputs should have no border, only a `surface_container_lowest` background. 
*   **Focus State:** A 1px "Ghost Border" of `primary` and a subtle glow (4px blur) using the `primary` color.

### Custom IDE Components:
*   **The Activity Bar:** Icons should use `on_surface_variant` (#c1c6d7). The active icon uses `tertiary` (#00e639) with a small 2px glow dot.
*   **The Minimap:** Use a highly desaturated version of the syntax colors to prevent visual clutter in the periphery.

---

## 6. Do’s and Don’ts

### Do:
*   **Do** use asymmetrical margins. If the left sidebar is `spacing.10`, the right utility panel should be `spacing.8` to break the "standard" feel.
*   **Do** use `tertiary` (Vibrant Green) sparingly. It is a "Success" and "Active" beacon, not a primary decorative color.
*   **Do** leverage backdrop blurs for overlapping panels to maintain a sense of space.

### Don't:
*   **Don't** use 1px solid lines to separate panels. Use color-blocking.
*   **Don't** use pure black (#000000). The deepest depth must always be our signature navy `surface_container_lowest` (#080f18).
*   **Don't** use "Standard" Material Design shadows. They are too soft for this high-tech, high-contrast aesthetic. Focus on tonal shifts.