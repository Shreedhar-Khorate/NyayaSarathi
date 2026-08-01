# NyayaSarathi — AI-Powered Judicial Case Intelligence

Production-ready Next.js (App Router) landing page featuring a cinematic dark hero with scroll-driven parallax video, a self-drawing "verification thread" pipeline, capability bento grid, animated stat counters, and a live split-screen research workspace mockup with click-to-verify citations.

## Tech Stack

- **Framework:** Next.js 16 (App Router, Turbopack)
- **Language:** TypeScript
- **Styling:** Tailwind CSS 3
- **Animations:** Framer Motion
- **Icons:** Lucide React

## Project Structure

```
nyayasarathi-app/
├── src/
│   ├── app/
│   │   ├── globals.css              # Design tokens, grain overlay, glass utilities, keyframes
│   │   ├── layout.tsx               # Root layout, next/font loading, metadata
│   │   └── page.tsx                 # Composes all landing page sections
│   │
│   └── components/
│       ├── layout/
│       │   ├── NavAndFooter.tsx     # Scroll-aware navbar + footer
│       │   └── SmoothScroll.tsx     # Butter-smooth Lenis scroll integration
│       │
│       ├── sections/
│       │   ├── Hero.tsx             # Staggered headline reveal + ambient canvas + dual CTA
│       │   ├── HeroFloatingCards.tsx # Floating interactive card cluster
│       │   ├── VerificationThread.tsx # Scroll-scrubbed SVG "thread" linking 6 processing stages
│       │   ├── StatsCounters.tsx    # Count-up stats, triggered on scroll into view
│       │   ├── CapabilitiesBento.tsx # Tilt-on-hover bento grid of core features
│       │   └── WorkspaceMockup.tsx  # Split document reader + AI drawer with citation sync
│       │
│       └── ui/
│           ├── AmbientCanvas.tsx    # Dependency-free canvas citation-graph animation
│           └── BackgroundVideo.tsx  # Scroll-parallax background video with spring physics
│
├── public/
│   └── video/
│       └── hero-bg.mp4         # Hero background video
│
├── tailwind.config.ts           # Color tokens, font families, custom shadows
├── postcss.config.mjs           # PostCSS + Tailwind + Autoprefixer
├── tsconfig.json                # TypeScript config with @/* path alias
└── package.json                 # Dependencies and scripts
```

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Design Notes

- **Color palette:** Obsidian/slate background, amber/gold accent (CTAs, icons, key numbers), indigo/cobalt for secondary glow and data accents.
- **No three.js.** The hero ambient background is a lightweight ~120-line dependency-free `<canvas>` citation graph — cheaper than WebGL, thematically closer to "legal knowledge graph."
- **Signature element:** The self-drawing gold "verification thread" in `PipelineSection.tsx` — an SVG line whose `pathLength` is scrubbed by scroll progress.
- **Workspace mockup** uses static demo data — wire `activeCite`/citation click handlers to your real RAG backend when integrating.
- All motion respects `prefers-reduced-motion`.
- Fonts are loaded via `next/font/google` for optimal performance (no render-blocking requests).
