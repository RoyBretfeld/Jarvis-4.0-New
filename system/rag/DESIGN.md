# Design System Strategy: The Intelligent Stratum

This document defines the visual and interaction language for our RAG (Retrieval-Augmented Generation) ecosystem. It moves beyond standard "SaaS Dark Mode" into a high-end, editorial-inspired "Enterprise Dark" aesthetic. The goal is to make complex data retrieval feel effortless, authoritative, and deeply layered.

---

## 1. Creative North Star: "The Digital Curator"
The core philosophy of this design system is **The Digital Curator**. Unlike standard dashboards that overwhelm with grids, this system treats AI-generated insights as premium content. We avoid the "template" look by using intentional asymmetry, generous negative space, and a "layered glass" approach to depth. 

We don't just display data; we architect an environment where the AI’s "thoughts" (retrieval) and "outputs" (generation) exist on distinct physical planes.

---

## 2. Color & Tonal Architecture
The palette is rooted in `background: #060e20`, a deep, nocturnal slate that provides a high-contrast stage for vibrant accents.

### The "No-Line" Rule
To achieve a signature premium feel, **1px solid borders are prohibited for sectioning.** Structural boundaries must be defined through background shifts. 
*   **Implementation:** Place a `surface_container_low` sidebar against the `background` main stage. The shift in tone creates a boundary that is felt rather than seen, reducing visual noise.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. Use the following tiers to denote "elevation" through color rather than shadows:
*   **Base:** `surface` (#060e20)
*   **Inactive/Recessed:** `surface_container_low` (#091328)
*   **Active/Standard:** `surface_container` (#0f1930)
*   **Elevated/Focus:** `surface_container_highest` (#192540)

### The "Glass & Gradient" Rule
For RAG-specific features (like a floating chat input or a source citation popover), use Glassmorphism. Combine `surface_variant` at 60% opacity with a `backdrop-blur` of 12px. 
*   **Signature Textures:** For primary actions, use a linear gradient from `primary` (#78b0ff) to `primary_container` (#5ba2ff) at a 135° angle. This adds a "lithographic" quality to buttons that flat colors lack.

---

## 3. Typography: The Editorial Edge
We utilize **Inter** for its mathematical precision and high X-height, ensuring legibility in dense data environments.

*   **Display Scale (`display-lg` to `display-sm`):** Reserved for high-level system status (e.g., "99.9% Accuracy"). These should be set with tight tracking (-0.02em) to feel authoritative.
*   **Headline & Title:** Use `headline-md` for AI-generated headers. Pair these with `on_surface_variant` sub-labels to create a clear "Reading Gravity."
*   **Body & Label:** Use `body-md` for the primary RAG output. To differentiate "Retrieved Sources" from "Generated Text," set sources in `label-md` with `secondary` (#70fda7) accents.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are too "web 2.0" for this system. We use **Ambient Illumination**.

*   **The Layering Principle:** Instead of a shadow, place a `surface_container_lowest` card inside a `surface_container_high` section. This creates a "carved out" effect that feels integrated into the hardware.
*   **Ambient Shadows:** For floating modals, use a blur value of `32px` with the color `on_surface` at only 4% opacity. This mimics a soft, natural glow from the screen rather than a muddy grey shadow.
*   **The Ghost Border Fallback:** If a container requires a border (e.g., an input field), use `outline_variant` (#40485d) at **20% opacity**. It should be a whisper, not a shout.

---

## 5. Signature Components

### The Intelligence Input (Search/Query)
*   **Style:** A `surface_container_highest` pill with a `9999px` radius. 
*   **Focus State:** Instead of a thick border, use a subtle outer glow using `primary` at 15% opacity and a `1px` Ghost Border of `primary_dim`.

### Source Citations (The "R" in RAG)
*   **Style:** Minimalist chips using `secondary_container` backgrounds and `on_secondary_fixed` text. 
*   **Interaction:** On hover, the chip should transition to `secondary` with a subtle `primary` shadow to indicate "Ready for Deep Dive."

### Data Cards
*   **Constraint:** **Forbid divider lines.** Separate the header from the body using a `2.5` (0.5rem) spacing gap and a slight tonal shift from `surface_container` to `surface_container_low`.
*   **Edge Case:** Use `outline_variant` at 10% opacity only if cards are placed on top of an identical color.

### Primary Actions
*   **Buttons:** All buttons use the `md` (0.375rem) roundedness scale. Primary buttons use the "Signature Gradient" (Primary to Primary Container).
*   **Tertiary/Ghost:** Use `on_surface_variant` text. No background. Interaction is shown through a slight increase in text brightness to `on_surface`.

---

## 6. Do’s and Don’ts

### Do
*   **Do use asymmetric layouts:** Align RAG sources to a narrow right column while the generated text takes a wider left column to create editorial interest.
*   **Do use Emerald Greens (`secondary`):** Use these strictly for "Successful Retrieval" or "System Healthy" indicators.
*   **Do embrace breathing room:** Use the `16` (3.5rem) spacing token between major content blocks to prevent "Dashboard Fatigue."

### Don’t
*   **Don't use pure white:** Never use `#FFFFFF`. Always use `on_surface` (#dee5ff) or `on_surface_variant` (#a3aac4) to maintain the "Enterprise Dark" eye-comfort.
*   **Don't use 100% opaque borders:** They break the "Glass & Fluidity" illusion of the system.
*   **Don't use standard tooltips:** Tooltips must be `surface_container_highest` with a backdrop blur; they should feel like they are floating in front of the UI, not stuck to it.