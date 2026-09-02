# HDFC Bank Custom LLM Development Pipeline — Component Guidelines

> **Standard Operating Procedures for Component Engineering**  
> **Target Framework:** Next.js 16 (App Router) / React 19 / Tailwind CSS v4  
> **Audience:** Frontend Engineers, UI/UX Developers, Contributors  

---

## 📌 Table of Contents

1. [Purpose](#1-purpose)
2. [Component Classification](#2-component-classification)
3. [Component Directory Structure](#3-component-directory-structure)
4. [Component Naming Conventions](#4-component-naming-conventions)
5. [Component Design Principles](#5-component-design-principles)
6. [Props Guidelines](#6-props-guidelines)
7. [Reusable UI Component Guidelines (`components/ui`)](#7-reusable-ui-component-guidelines-componentsui)
8. [Feature Component Guidelines (`components/<feature>`)](#8-feature-component-guidelines-componentsfeature)
9. [Layout Component Guidelines (`components/layout`)](#9-layout-component-guidelines-componentslayout)
10. [Form Component Guidelines (`components/form`)](#10-form-component-guidelines-componentsform)
11. [Table Component Guidelines (`components/tables`)](#11-table-component-guidelines-componentstables)
12. [Chart Component Guidelines (`components/charts`)](#12-chart-component-guidelines-componentscharts)
13. [Loading State Guidelines](#13-loading-state-guidelines)
14. [Error State Guidelines](#14-error-state-guidelines)
15. [Empty State Guidelines](#15-empty-state-guidelines)
16. [Component Communication](#16-component-communication)
17. [Component Reusability Rules](#17-component-reusability-rules)
18. [Recommended Component Template](#18-recommended-component-template)
19. [Component Review Checklist](#19-component-review-checklist)

---

# 1. Purpose

This document establishes the official component standards and architectural conventions for the **HDFC Bank Custom LLM Development Pipeline** frontend. Adhering to these guidelines ensures consistency, maintainability, type safety, and seamless onboarding across all UI engineering tasks.

---

# 2. Component Classification

Components in the codebase are divided into six distinct architectural layers:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Page Components (src/app/**/page.jsx)                              │
│    • Route handlers, data orchestration, title/metadata injection      │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Layout Shell Components (src/components/layout/)                   │
│    • Navbar, Sidebar, Footer, Navigation items                         │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Feature Domain Components (src/components/<domain>/)                │
│    • Training modals, Evaluation cards, Model drawers, Playground      │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Reusable UI Primitives (src/components/ui/)                        │
│    • Button, Badge, Breadcrumbs, StatCard, ActivityCard, LineageCard   │
├────────────────────────────────────────────────────────────────────────┤
│ 5. Form Components (src/components/form/)                             │
│    • FormField, SelectField, TextAreaField, FileUpload                │
├────────────────────────────────────────────────────────────────────────┤
│ 6. Data Display & Visualization (src/components/tables/ & charts/)    │
│    • ModelsTable, LineChart, Table Column Renderers                    │
└────────────────────────────────────────────────────────────────────────┘
```

---

# 3. Component Directory Structure

All components must reside inside `src/components/` grouped by domain responsibility:

```text
src/components/
├── auth/                       # Security & Guard components (ProtectedRoute.jsx)
├── charts/                     # Recharts data visualizers (LineChart.jsx)
├── deployment/                 # Deployment cards, modals, and operational controls
├── evaluation/                 # Evaluation metric grids and score breakdown cards
├── form/                       # Form controls (FormField, SelectField, FileUpload)
├── layout/                     # Application shell (Navbar, Sidebar, Footer)
├── metaGrid/                   # Generic metadata grid displays
├── model/                      # Model Registry cards, drawers, and logs modals
├── playground/                 # Chat interface, message bubbles, parameter sliders
├── qualityMetrics/             # Dataset quality score widgets
├── tables/                     # Universal table components (ModelsTable.jsx)
├── training/                   # Training run configuration modal & job stats
└── ui/                         # Atomic design UI primitives (Button, Badge, StatCard)
```

---

# 4. Component Naming Conventions

* **Files & Components:** Always use **PascalCase** for React component files and function names:
  * ✅ `Button.jsx`, `NewTrainingModal.jsx`, `ModelsTable.jsx`
  * ❌ `button.jsx`, `new-training-modal.jsx`, `models_table.jsx`
* **Directories:** Use **camelCase** or domain descriptors:
  * ✅ `src/components/ui/`, `src/components/qualityMetrics/`
* **Export Pattern:** Use `export default function ComponentName(...)` for all single-component files:
  ```jsx
  "use client";
  
  export default function StatCard({ statData }) {
    // ...
  }
  ```

---

# 5. Component Design Principles

1. **Single Responsibility Principle (SRP):** Each component must perform one well-defined task (e.g., rendering a metric card or displaying a table column).
2. **Presentational vs. Container Separation:**
   * **Presentational Components** (`src/components/ui/`): Stateless, receive data exclusively via props, and trigger callbacks.
   * **Container Components** (`src/app/**/page.jsx`): Coordinate API calls, hold state, and assemble presentational components.
3. **Strict Tailwind Utility Styling:** Never use ad-hoc inline styles for properties supported by Tailwind CSS.

---

# 6. Props Guidelines

* **Destructure with Defaults:** Always destructure props in the function signature with explicit default values:
  ```jsx
  export default function Button({
    icon: Icon,
    children,
    variant = "default",
    className = "",
    disabled = false,
    ...props
  }) {
    // ...
  }
  ```
* **Event Handler Naming:** Prefix callback props with `on` (e.g. `onMenuClick`, `onFilterChange`, `onRetry`, `onClose`).

---

# 7. Reusable UI Component Guidelines (`components/ui`)

Components in `components/ui/` must have **zero domain business logic** and zero direct API dependencies.

### Available UI Primitives:
* **`Button.jsx`:** Supports `variant="default"` (light border) and `variant="primary"` (HDFC blue `#002B55`).
* **`Badge.jsx`:** Supports semantic color variants: `success`, `warning`, `danger`, `info`, `neutral`, `purple`.
* **`StatCard.jsx`:** Renders top-level KPI widgets with top-border color accents, icons, and status pills.
* **`Breadcrumbs.jsx`:** Renders hierarchical navigation path breadcrumbs.
* **`ActivityCard.jsx`:** Renders chronological timeline events with icons and status tags.

---

# 8. Feature Component Guidelines (`components/<feature>`)

Feature components encapsulate domain workflows:
* Modals must accept `isOpen` (boolean) and `onClose` (function) props.
* Modals should handle their own internal form validation before delegating submission to parent pages via callbacks (e.g. `onSubmit(payload)`).

---

# 9. Layout Component Guidelines (`components/layout`)

* **`Sidebar.jsx`:** Enforces responsive behavior. Hidden on mobile (`hidden lg:flex`) unless toggled open via `isOpen`.
* **`Navbar.jsx`:** Fixed to top (`fixed top-0 z-30 w-full`), contains global search, role badges, and mobile hamburger button.
* **`Footer.jsx`:** Pushed to the bottom with `mt-auto` and offset with `lg:ml-[280px]` to prevent overlapping the sidebar.

---

# 10. Form Component Guidelines (`components/form`)

* **`FormField.jsx`:** Encapsulates label, input box, focus rings, and required asterisk (`*`).
* **`SelectField.jsx`:** Standardized dropdown select with options array.
* **`TextAreaField.jsx`:** Multi-line text input.
* **`FileUpload.jsx`:** Drag-and-drop zone with file type validation (`.csv`, `.xlsx`, `.json`, `.jsonl`) and file size preview.

---

# 11. Table Component Guidelines (`components/tables`)

All tabular views should utilize **`ModelsTable.jsx`**:
* **Smart Pagination:** Automatically computes total pages and displays ellipses (`...`) for large page counts.
* **Sorting & Filtering:** Accepts `filterOptions`, `selectedFilter`, and `onFilterChange`.
* **Built-in States:** Handles `loading` (spinner), `error` (retry button), and `emptyMessage`.

```jsx
<ModelsTable
  title="Fine-Tuning Runs"
  data={trainingRuns}
  columns={TrainingColumns}
  loading={loading}
  error={error}
  onRetry={fetchRuns}
  pageSize={10}
/>
```

---

# 12. Chart Component Guidelines (`components/charts`)

Visualizations must use **`LineChart.jsx`**:
* Provide `xKey` (e.g. `"step"` or `"date"`) and a list of line definitions with distinct stroke colors.
* Always wrap charts in `<ResponsiveContainer width="100%" height={height}>`.

---

# 13. Loading State Guidelines

* When an entire page is loading, render a centered `Loader2` spinner from `lucide-react`:
  ```jsx
  if (loading) {
    return (
      <div className="flex h-96 w-full items-center justify-center lg:ml-[280px]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }
  ```
* Buttons performing asynchronous operations should show a spinning icon and be `disabled={isSubmitting}`.

---

# 14. Error State Guidelines

* Catch API errors using `getApiErrorMessage(error)` from `apiClient.js`.
* Show non-blocking alert banners with retry buttons for failed sections:
  ```jsx
  {error && (
    <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700 flex items-center justify-between">
      <div className="flex items-center gap-2">
        <AlertCircle className="h-5 w-5" />
        <span>{error}</span>
      </div>
      <Button variant="default" onClick={onRetry}>Retry</Button>
    </div>
  )}
  ```

---

# 15. Empty State Guidelines

When lists or queries return zero records:
* Do not leave the card or table blank.
* Display a descriptive empty state message with a clear call-to-action (e.g., `"No datasets found. Upload your first dataset to start training."`).

---

# 16. Component Communication

```text
┌────────────────────────────────────────────────────────────┐
│                    Parent Page (State)                     │
│               src/app/training/page.jsx                    │
└──────────────┬──────────────────────────────▲──────────────┘
               │ Pass data (props)            │ Trigger action (callbacks)
               ▼                              │
┌──────────────────────────────┐ ┌────────────┴──────────────┐
│       ModelsTable.jsx        │ │    NewTrainingModal.jsx   │
│  (Displays rows & columns)   │ │ (Submits run configuration│
└──────────────────────────────┘ └───────────────────────────┘
```

---

# 17. Component Reusability Rules

Before creating a new component, check the decision matrix:

1. **Used in 2+ feature domains?** ──► Place in `src/components/ui/` or `src/components/form/`.
2. **Specific to a single MLOps domain?** ──► Place in `src/components/<feature>/`.
3. **Page-specific one-off layout?** ──► Inline or extract as a sub-component within `src/app/<feature>/`.

---

# 18. Recommended Component Template

Use this canonical template when creating new components:

```jsx
"use client";

import { useMemo } from "react";
import PropTypes from "prop-types";
import { LucideIcon } from "lucide-react";

/**
 * Standard Feature Card Component
 */
export default function FeatureCard({
  title,
  description = "",
  icon: Icon = null,
  status = "neutral",
  children,
  className = "",
}) {
  return (
    <div className={`rounded-xl border border-gray-200 bg-white p-6 shadow-sm ${className}`}>
      <div className="flex items-center justify-between border-b border-gray-100 pb-4 mb-4">
        <div className="flex items-center gap-3">
          {Icon && (
            <div className="h-10 w-10 rounded-lg bg-blue-50 text-blue-900 flex items-center justify-center">
              <Icon className="h-5 w-5" />
            </div>
          )}
          <div>
            <h3 className="font-bold text-gray-900 text-base tracking-tight">{title}</h3>
            {description && <p className="text-xs text-gray-500 mt-0.5">{description}</p>}
          </div>
        </div>
      </div>
      <div className="text-sm text-gray-700">{children}</div>
    </div>
  );
}
```

---

# 19. Component Review Checklist

Before opening a pull request or committing a component:

* [ ] Is the component file in **PascalCase** inside the correct directory?
* [ ] Does the component start with `"use client";` if it uses hooks, state, or browser APIs?
* [ ] Are all props destructured with explicit default fallbacks?
* [ ] Are loading, error, and empty states handled?
* [ ] Is responsive behavior verified across mobile (`<640px`) and desktop (`>1024px`)?
* [ ] Are all colors aligned with the HDFC brand design palette (`#002B55`, `#07477F`, `#D90000`)?
* [ ] Are there zero hardcoded API calls inside presentational `ui/` components?
