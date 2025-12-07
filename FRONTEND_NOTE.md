# Frontend Implementation Note

## Current Situation

The existing frontend in `resyft-frontend/` is designed for a **school productivity application** (class management, document uploads, AI study assistant). This is a different application than Antibody.

## What Antibody Frontend Should Include

According to the technical specification, the Antibody frontend should have:

### Required Pages

1. **Landing Page** (`/`)
   - Hero section explaining Antibody
   - Live statistics (total claims monitored, vulnerabilities detected, remediations completed)
   - Call-to-action to view dashboard

2. **Dashboard** (`/dashboard`)
   - Main triage interface
   - Vulnerability queue table
   - Graph explorer
   - Search functionality

3. **Graph Explorer** (`/graph/{claimId}`)
   - Interactive D3.js force-directed graph visualization
   - Shows claim dependency network
   - Zoom, pan, click-to-expand
   - Color-coded by vulnerability level

4. **Article View** (`/article/{articleId}`)
   - All extracted claims from a single article
   - Individual health scores per claim

### Required Components

1. **VulnerabilityQueue** - Sortable, filterable table of vulnerable claims
2. **DependencyGraph** - D3.js visualization of claim dependencies
3. **ClaimCard** - Displays claim with sources, decay forecast, contradictions
4. **SearchBar** - Semantic search with language and date filters
5. **MetricsPanel** - Real-time statistics and trend charts

## Recommended Approach

### Option 1: Build New Frontend (Recommended)

Create a new Antibody-specific frontend following the technical specification:

```bash
cd /Users/jadenryu/Desktop/resyft_2
npx create-next-app@latest antibody-frontend --typescript --tailwind --app

cd antibody-frontend

# Install required dependencies
npm install d3 @types/d3 recharts lucide-react
npm install @shadcn/ui
```

Then build the components and pages according to the spec.

### Option 2: Adapt Existing Frontend

If you want to reuse the existing `resyft-frontend` structure:

**Major Changes Needed:**
- Replace "classes" concept with "articles"
- Replace "documents" with "claims"
- Replace chat interface with vulnerability queue
- Add D3.js dependency graph visualization
- Rebuild landing page with Antibody messaging
- Add triage workflow UI
- Connect to new backend API endpoints

**This would require substantial refactoring** - nearly a complete rebuild while keeping only the UI component library (shadcn/ui) and styling system.

## Quick Start for New Frontend

If building new:

1. Create component structure:
```
antibody-frontend/
├── app/
│   ├── page.tsx                    # Landing page
│   ├── dashboard/
│   │   └── page.tsx               # Main dashboard
│   ├── graph/
│   │   └── [claimId]/
│   │       └── page.tsx           # Graph explorer
│   └── article/
│       └── [articleId]/
│           └── page.tsx           # Article view
├── components/
│   ├── VulnerabilityQueue.tsx
│   ├── DependencyGraph.tsx
│   ├── ClaimCard.tsx
│   ├── SearchBar.tsx
│   └── MetricsPanel.tsx
└── lib/
    ├── api.ts                     # API client
    └── utils.ts
```

2. Update API calls to point to new backend:
```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function getVulnerableClaims(limit = 50, offset = 0) {
  const response = await fetch(
    `${API_BASE_URL}/api/graph/vulnerable?limit=${limit}&offset=${offset}`
  )
  return response.json()
}

export async function getClaimWithDependencies(claimId: string) {
  const response = await fetch(
    `${API_BASE_URL}/api/graph/claim/${claimId}`
  )
  return response.json()
}
```

3. Implement D3.js graph visualization:
```bash
npm install d3 @types/d3
```

## Current Frontend Status

The `resyft-frontend/` directory:
- ✅ Has excellent UI component library (shadcn/ui)
- ✅ Has clean styling with Tailwind CSS
- ✅ Has good TypeScript setup
- ❌ Is designed for a different application (school productivity)
- ❌ Would need 80%+ of code rewritten for Antibody

## Recommendation

**Build a new Antibody-specific frontend** using the same tech stack (Next.js 14, TypeScript, Tailwind, shadcn/ui) but with the proper pages and components for the knowledge integrity platform.

You can reference the existing frontend for:
- Component styling patterns
- shadcn/ui integration
- Layout structures
- Tailwind configuration

But the core application logic and page structure should be rebuilt to match the Antibody specification.

---

**Would you like me to create the new Antibody frontend structure?** Let me know and I can scaffold the proper pages and components according to the technical specification.
