# HDFC Bank Custom LLM Development Pipeline — UI Guidelines

> **Visual Design System & User Interface Specification**  
> **Target Brand:** HDFC Bank Corporate Design & Theme Guidelines  
> **Styling Framework:** Tailwind CSS v4 / Merriweather Serif Typography  

---

## 📌 Table of Contents

1. [UI Design Philosophy](#1-ui-design-philosophy)
2. [Design System Overview](#2-design-system-overview)
3. [Color System & Brand Tokens](#3-color-system--brand-tokens)
4. [Typography](#4-typography)
5. [Spacing System](#5-spacing-system)
6. [Layout Guidelines](#6-layout-guidelines)
7. [Responsive Design & Breakpoints](#7-responsive-design--breakpoints)
8. [Button Guidelines](#8-button-guidelines)
9. [Form & Input Guidelines](#9-form--input-guidelines)
10. [Card Guidelines](#10-card-guidelines)
11. [Table Guidelines](#11-table-guidelines)
12. [Modal & Dialog Guidelines](#12-modal--dialog-guidelines)
13. [Navigation Guidelines](#13-navigation-guidelines)
14. [Status & Badge Guidelines](#14-status--badge-guidelines)
15. [Loading State Guidelines](#15-loading-state-guidelines)
16. [Error State Guidelines](#16-error-state-guidelines)
17. [Empty State Guidelines](#17-empty-state-guidelines)
18. [Icons Guidelines](#18-icons-guidelines)
19. [Accessibility Guidelines](#19-accessibility-guidelines)
20. [Dark Mode](#20-dark-mode)
21. [UI Consistency Rules](#21-ui-consistency-rules)
22. [UI Review Checklist](#22-ui-review-checklist)

---

# 1. UI Design Philosophy

The **HDFC Bank Custom LLM Development Pipeline** UI delivers a professional, clean, high-trust enterprise banking experience:
* **Clarity & Information Density:** Interfaces present complex machine learning telemetry (training step losses, parameter sizes, token latencies) with high visual legibility.
* **Corporate Banking Identity:** Clean white cards, slate borders, deep corporate navy blue tones, and signature red accents.
* **Predictable Navigation:** Persistent left sidebar navigation and unified top search/action header.

---

# 2. Design System Overview

The visual design system is built using **Tailwind CSS v4** configured with corporate color tokens, typography scales, and modular presentational components.

---

# 3. Color System & Brand Tokens

The color palette is derived directly from corporate brand colors and semantic UI requirements:

| Color Token | Hex / Class | Primary Usage in Codebase |
| :--- | :--- | :--- |
| **HDFC Primary Navy** | `#002B55` | Primary buttons, active card accents, heading titles |
| **HDFC Secondary Blue** | `#07477F` | Active sidebar navigation item background, hover states |
| **HDFC Dark Navy** | `#001C38` | Sidebar background shell, brand containers |
| **HDFC Brand Red** | `#D90000` / `#ED1C24` | Active navigation indicator bar, error alerts, live training badges |
| **HDFC Accent Red Tint** | `#FFCDC9` | Active training stat card top border |
| **Canvas Background** | `#F9FAFB` (`bg-gray-50`) | Global page background behind cards and tables |
| **Card Surface** | `#FFFFFF` (`bg-white`) | Content containers, modal dialogs, data table backgrounds |
| **Border Slate** | `#E2E8F0` (`border-gray-200`) | Card outlines, table dividers, form borders |
| **Success Green** | `#16A34A` / `text-green-700` | Completed training runs, active deployments, safe datasets |
| **Warning Amber** | `#D97706` / `text-amber-700` | Queued jobs, review required, role warning notices |
| **Danger Red** | `#DC2626` / `text-red-700` | Failed training runs, safety violations, destructive actions |

---

# 4. Typography

Typography is powered by Google's **Merriweather** serif font via `next/font/google`:

```css
@theme {
    --font-merriweather: "Merriweather", serif;
}
```

### Type Scale & Hierarchy:

| Element | Tailwind Classes | Font Weight | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Page Title (H1)** | `text-2xl lg:text-3xl` | `font-extrabold` | `leading-tight` | Main page heading |
| **Section Title (H2)**| `text-xl lg:text-2xl` | `font-bold` | `leading-snug` | Major dashboard sections |
| **Card Title (H3)** | `text-lg font-semibold` | `font-semibold` | `leading-normal`| Table titles, modal headers |
| **Metric Value** | `text-2xl lg:text-3xl` | `font-extrabold` | `leading-none` | StatCard numeric KPIs |
| **Body Text** | `text-sm text-gray-700` | `font-normal` | `leading-relaxed`| Descriptions, paragraphs |
| **Label / Metadata** | `text-xs uppercase font-medium` | `font-semibold` | `tracking-wider` | Form labels, card subheadings |

---

# 5. Spacing System

The layout follows Tailwind's 4px base unit spacing scale:
* **Micro Spacing:** `gap-2` (8px), `gap-3` (12px), `gap-4` (16px) inside cards and form fields.
* **Component Padding:** `p-4` (16px) to `p-6` (24px) for cards and modals.
* **Page Padding:** `px-4 lg:px-8 py-6` with top header clearance `pt-20` and sidebar offset `lg:ml-[280px]`.

---

# 6. Layout Guidelines

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Fixed Navbar (H: 64px, Z-Index: 30, Fixed Top)                        │
├──────────────┬─────────────────────────────────────────────────────────┤
│ Fixed        │ Main Content Container (Margin-Left: 280px on desktop)  │
│ Sidebar      │                                                         │
│ (W: 280px)   │   Page Header (Breadcrumbs + Title + Action Buttons)    │
│              │   ───────────────────────────────────────────────────   │
│ • Navigation │   KPI StatCards Grid (1 to 4 columns)                   │
│ • User Role  │   ───────────────────────────────────────────────────   │
│ • Sign Out   │   Main Section (Data Table / Loss Chart / Forms)        │
│              │   ───────────────────────────────────────────────────   │
│              │   Footer (Copyright & Pipeline Info)                    │
└──────────────┴─────────────────────────────────────────────────────────┘
```

---

# 7. Responsive Design & Breakpoints

* **Mobile (`<640px`):** Off-canvas drawer sidebar, full-width single column cards, stacked table action buttons.
* **Tablet (`640px - 1024px`):** 2-column KPI grids, visible search bar in navbar.
* **Desktop (`≥1024px`):** Permanent 280px sidebar rail, 4-column metric cards, expansive dual-pane playground.

---

# 8. Button Guidelines

Buttons are rendered via `src/components/ui/Button.jsx`:

* **Primary (`variant="primary"`):**
  * Class: `bg-[#002B55] text-white hover:bg-[#07477F] border border-[#002B55]`
  * Usage: Primary calls-to-action (e.g. `"Start Training"`, `"Deploy Model"`).
* **Default / Outline (`variant="default"`):**
  * Class: `bg-white text-gray-700 hover:bg-gray-100 border border-gray-300`
  * Usage: Secondary actions (e.g. `"Cancel"`, `"Filter"`, `"Download"`).

---

# 9. Form & Input Guidelines

* **Label:** `text-[14px] font-medium uppercase tracking-wide text-[#002B5C]`.
* **Input Box:** `h-9 w-full rounded-sm border border-slate-300 bg-white px-3 text-sm text-slate-700 focus:border-[#004C97] focus:ring-1 focus:ring-[#004C97]`.
* **Required Indicator:** Red asterisk `<span className="text-red-500">*</span>`.

---

# 10. Card Guidelines

Standard cards follow the elevated white surface pattern:
```jsx
<div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm hover:shadow-md transition-all duration-200">
  {/* Card Content */}
</div>
```

---

# 11. Table Guidelines

Tables are styled with crisp lines and subtle hover highlights:
* **Header:** `bg-gray-50 text-xs font-semibold text-gray-600 uppercase tracking-wider py-3.5 px-4`.
* **Row:** `border-b border-gray-100 hover:bg-blue-50/40 transition-colors py-4 px-4 text-sm`.
* **Pagination:** Bottom rail with page number buttons, item counts, and next/prev arrows.

---

# 12. Modal & Dialog Guidelines

* **Backdrop:** `fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4`.
* **Modal Body:** `bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6`.

---

# 13. Navigation Guidelines

* **Active Item:** `bg-[#07477F] text-white font-bold` with a red left accent border `bg-red-500 w-1`.
* **Inactive Item:** `text-gray-200 hover:bg-[#063967] transition-all`.

---

# 14. Status & Badge Guidelines

Badges use standardized semantic variants from `src/components/ui/Badge.jsx`:

| State | Badge Variant | Background & Text Classes |
| :--- | :--- | :--- |
| **Completed / Active / Safe** | `variant="success"` | `border-green-200 bg-green-50 text-green-700` |
| **Running / In-Progress** | `variant="info"` | `border-blue-200 bg-blue-50 text-blue-700` |
| **Queued / Pending** | `variant="warning"` | `border-yellow-200 bg-yellow-50 text-yellow-700` |
| **Failed / Rejected / Unsafe** | `variant="danger"` | `border-red-200 bg-red-50 text-red-700` |
| **Archived / Inactive** | `variant="neutral"` | `border-slate-200 bg-slate-50 text-slate-600` |

---

# 15. Loading State Guidelines

* Full-screen and card loads render a smooth spinning indicator:
  ```jsx
  <Loader2 className="h-8 w-8 animate-spin text-blue-900" />
  ```

---

# 16. Error State Guidelines

* Display inline feedback with red alert containers:
  ```jsx
  <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700 flex items-center gap-2">
    <AlertCircle className="h-5 w-5 shrink-0" />
    <span className="text-sm font-medium">{errorMessage}</span>
  </div>
  ```

---

# 17. Empty State Guidelines

* Empty views display an icon, friendly title, and call to action:
  ```jsx
  <div className="py-12 text-center">
    <Database className="mx-auto h-12 w-12 text-gray-300 mb-3" />
    <h4 className="text-sm font-semibold text-gray-700">No records found</h4>
    <p className="text-xs text-gray-500 mt-1">Get started by creating your first entry.</p>
  </div>
  ```

---

# 18. Icons Guidelines

* **Icon Set:** `lucide-react` icons.
* **Standard Size:** `size={18}` or `size={20}` with `strokeWidth={2}`.

---

# 19. Accessibility Guidelines

### Currently Implemented:
* Form fields use explicit `htmlFor` and `id` linking.
* Semantic buttons with hover/focus cursor states.

### Recommended Production Improvements:
* Add `aria-expanded` and `aria-controls` attributes to mobile drawer toggles.
* Ensure all interactive icon-only buttons include `aria-label` attributes.

---

# 20. Dark Mode

> ⚠️ **Notice:** The application currently operates exclusively in **Light Mode** to adhere to standard banking corporate portal guidelines. Dark mode is not confirmed in the current implementation.

---

# 21. UI Consistency Rules

1. Always use `src/components/ui/Button.jsx` and `Badge.jsx` rather than creating raw inline buttons or tags.
2. Maintain the `lg:ml-[280px]` margin offset on all main page containers to avoid overlapping the fixed sidebar.
3. Use HDFC primary navy (`#002B55`) for key headings and main action buttons.
4. Always wrap tabular views in `ModelsTable.jsx`.

---

# 22. UI Review Checklist

* [ ] Color tokens align with HDFC brand palette (`#002B55`, `#07477F`, `#D90000`).
* [ ] Typography uses the Merriweather font variable.
* [ ] Margin offset `lg:ml-[280px]` is present on page containers.
* [ ] Badges use the canonical `Badge.jsx` component with semantic variants.
* [ ] Loading spinner and empty states are provided for data tables.
* [ ] Form fields have labels, required indicators, and focus rings.
