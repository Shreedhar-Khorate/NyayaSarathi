# NyayaSarathi Frontend

This is the user interface and interactive dashboard for the **NyayaSarathi** AI-Powered Judicial Case Intelligence & Decision Support System. It is built using **React**, **Vite**, and **Tailwind CSS v4**.

---

## 📁 Directory Structure

Here is a breakdown of the key files and folders in this directory:

*   **`src/`**: Contains the source code of the React application.
    *   **`src/App.jsx`**: The main application component. Houses the interactive Judicial Case Intelligence Simulator, landing hero sections, sample cases, and statistics dashboard.
    *   **`src/index.css`**: The main CSS entrypoint. In Tailwind CSS v4, this file configures the build using the native `@import "tailwindcss";` directive.
    *   **`src/main.jsx`**: Renders the React app and mounts it to the DOM (`#root`).
    *   **`src/App.css`**: Auxiliary CSS file (currently kept empty to avoid layout overrides in favor of Tailwind utility classes).
    *   **`src/assets/`**: Static image assets and icons.
*   **`index.html`**: The HTML entrypoint where Vite mounts the React app.
*   **`vite.config.js`**: Configuration file for Vite. Configured to use the React plugin and the native `@tailwindcss/vite` plugin for build integration.
*   **`.oxlintrc.json`**: Linter configuration for [Oxlint](https://oxc.rs/) which enables fast lint rules for React.
*   **`package.json`**: Defines scripts, dependencies (`react`, `react-dom`), and devDependencies (`vite`, `tailwindcss`, `@tailwindcss/vite`).

---

## 🛠️ Tech Stack & Styling

1.  **React + Vite**: Enables instant server start and lightning-fast Hot Module Replacement (HMR).
2.  **Tailwind CSS v4 (v4-Beta / v4-stable)**: Leverages native CSS imports, CSS variables, and zero-configuration building. No `tailwind.config.js` is needed, as all directives are compiled straight from Vite's builder.
3.  **UI Design**:
    *   **Dark Mode Palette**: Deep slate base (`bg-slate-950`) combined with curated indigo/violet accents.
    *   **Glassmorphism**: Backdrop blur filters (`backdrop-blur-xl bg-slate-900/60`) for modern visual hierarchies.
    *   **Interactive Simulation**: Users can select predefined case samples (Civil Force Majeure or Criminal Evidence) or paste their own case narratives to simulate AI-driven case analysis results in real time.

---

## 🚀 Getting Started

### Prerequisites

Ensure you have [Node.js](https://nodejs.org/) installed (version 18+ recommended).

### Running Locally

To run the development server, navigate to the frontend directory and run:

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies (if not already done)
npm install

# Start the Vite local development server
npm run dev
```

The application will run on `http://localhost:5173`.

### Building for Production

To build optimized production assets:

```bash
npm run build
```

This compiles static HTML, CSS, and JS assets into the `dist/` directory, optimized and ready for production deployment.
