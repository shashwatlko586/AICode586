# User Guide — Architect Copilot
## AI Co-pilot for Adaptive Retail Layout Design

**Audience:** Retail architects, store planners, and design reviewers at Blue Retail Ventures  
**Application:** Shashwat Capstone Retail (Architect Copilot)  
**Version:** 1.0

---

## 1. Introduction

The **Architect Copilot** helps you produce a **first-pass conceptual store layout** for new Blue Retail locations. It combines:

- **Local market trends** (what shoppers in your city/state are searching for)
- **Official design documents** (brand book, fixture catalog, building code, leasing terms)
- **AI reasoning** to propose zones, fixtures, and compliance checks

The output is a **2D layout diagram** and a **structured JSON plan** you can review, refine, or pass to CAD tools.

> **Important:** Output is **conceptual**, not construction-ready. Always validate critical compliance and leasing clauses with legal and facilities teams.

---

## 2. Getting Started

### 2.1 Access the Application

Your administrator will provide:

| Access | URL / command |
|--------|---------------|
| **Streamlit UI** | `http://<VM-IP>:8501` or local URL |
| **Cloud Run API** | `https://shashwat-capstone-retail-….run.app` |

### 2.2 Start the UI (VM)

```bash
cd ~/Desktop/C_AgenticAI_PRJ11/shashwat-capstone-retail
source .venv/bin/activate
set -a && source .env && set +a
./start-ui.sh
```

Ensure `.env` contains the correct `CLOUD_RUN_API_URL` pointing to your deployed API.

---

## 3. Using the Streamlit Workbench

### 3.1 Main Screen

When you open the app, you see:

- **Title:** Shashwat Capstone Retail
- **Sidebar:** Store parameters
- **Main area:** Generate button and results (after generation)

### 3.2 Step-by-Step Workflow

#### Step 1 — Enter store parameters

| Field | Description | Example |
|-------|-------------|---------|
| **City** | Target city for trends and layout | `Surat` |
| **Store name** | Display name on layout | `Blue Retail Surat` |
| **Floor area (sqm)** | Total sales floor area | `120` |
| **Trend keywords** | Products to track in Google Shopping trends | `iPhone 15, gaming laptop, …` |
| **Google Trends geo** | Country code | `IN` |
| **State geo** | State-level proxy | `IN-GJ` (Gujarat) |
| **API URL** | Backend service (pre-filled by admin) | Cloud Run URL |

#### Step 2 — Click **Generate layout**

The system runs three AI agents in sequence:

1. **Market Analyst** — fetches trends and writes a market summary  
2. **Layout Strategist** — retrieves design rules and generates a JSON layout  
3. **AI Draftsman** — renders the 2D PNG diagram  

Progress is shown as a spinner. Generation typically takes **30–120 seconds** on Cloud Run.

#### Step 3 — Review results

After completion, you see four sections:

| Section | What to look for |
|---------|------------------|
| **2D layout** | Color-coded zones, fixture IDs, entrance marker |
| **Market insights** | Narrative + top trending products |
| **Layout plan (JSON)** | Full structured plan for export/integration |
| **Warnings** | Parse retries, fallback layout notices |

---

## 4. Understanding the Layout Output

### 4.1 Zone Types & Colors

| Zone type | Meaning | Brand rule |
|-----------|---------|------------|
| **Decompression zone** | Entry buffer | Keep uncluttered; 3–5 m inside entrance |
| **Power wall** | High-impact wall (usually right of entrance) | Place hero / trending SKUs |
| **Circulation path** | Main customer loop | Counter-clockwise flow; min 1800 mm width |
| **Experience zone** | Interactive demos | Laptops, gaming, try-before-buy |
| **Checkout** | Payment area | Typically near entrance side |
| **Merchandising** | General product areas | Standard shelving/display |

### 4.2 Fixture IDs

Fixtures reference the **Fixture Catalog Q3 2025**, for example:

| ID | Description |
|----|-------------|
| `BRV-FX-HP03` | Hero Product Pedestal |
| `BRV-FX-IDT02` | Interactive Display Table |

Cross-check **width, depth, and rotation** in the catalog before approving placement.

### 4.3 Compliance Checks

Each layout includes a `compliance_checks` array:

| Status | Action |
|--------|--------|
| **pass** | Requirement met per retrieved documents |
| **warn** | Review manually — may need architect judgment |
| **fail** | Escalate to legal/facilities before proceeding |

Sources include NBC accessibility excerpts and leasing agreement text from the RAG corpus.

### 4.4 Design Rationale

Read the `design_rationale` field in JSON for a 2–4 sentence explanation of why zones and products were placed as shown.

---

## 5. Interpreting Market Insights

The **Market Analyst** agent reports:

- **Top trending products** ranked by combined national + state search interest
- **Narrative** recommending placement (e.g. headphones on power wall, laptops in experience zone)

### Limitations

| Limitation | Implication |
|------------|-------------|
| Trends reflect **search interest**, not sales | Validate with merchandising data |
| Rate limits on Google Trends | Admin may enable mock trends for demos |
| Geo proxy (IN-GJ for Surat) | Approximates local demand; not city-level precision |

---

## 6. Using the REST API Directly

For integrations with other tools:

```bash
curl -X POST https://YOUR-CLOUD-RUN-URL/generate_layout \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Surat",
    "store_name": "Blue Retail Surat",
    "floor_area_sqm": 120,
    "keywords": ["iPhone 15", "gaming laptop"],
    "geo": "IN",
    "sub_geo": "IN-GJ"
  }'
```

### Response fields

| Field | Use |
|-------|-----|
| `layout_image_base64` | Decode to PNG for reports |
| `layout_plan` | Import into downstream systems |
| `layout_plan_valid` | `false` if fallback layout was used |
| `trace_id` | Include in support tickets |
| `errors` | Non-fatal warnings |

Interactive API docs: `https://YOUR-URL/docs`

---

## 7. Best Practices for Architects

### Before generating

1. Confirm **floor area** matches leasing CAD or survey  
2. Choose **keywords** relevant to the store format (electronics vs. mixed)  
3. Ensure RAG documents are ingested (admin responsibility)

### After generating

1. Verify **decompression zone** is clear at entrance  
2. Confirm **power wall** placement matches brand standard (customer's right)  
3. Check **circulation width** against NBC minimums  
4. Validate **fixture dimensions** fit within zone boundaries  
5. Review **compliance_checks** with `fail` or `warn` status  
6. Treat output as **draft v0.1** — refine in your CAD workflow

### When results look wrong

| Symptom | Likely cause | What to do |
|---------|--------------|------------|
| Generic / template layout | JSON parse failed; fallback used | Check warnings; retry with smaller floor area |
| Empty market insights | Trends rate limit | Retry later or ask admin to enable mock trends |
| Missing brand rules | RAG corpus incomplete | Ask admin to re-ingest documents |
| API error in UI | Backend issue | Copy error text; share `trace_id` with support |

---

## 8. Glossary

| Term | Definition |
|------|------------|
| **RAG** | Retrieval-Augmented Generation — AI answers grounded in your documents |
| **Power wall** | First major merchandising surface seen after entering |
| **Decompression zone** | Transition space inside the entrance |
| **LangGraph** | Framework orchestrating the three agents |
| **Trace ID** | Unique ID for observability/debugging |

---

## 9. Support & Feedback

When reporting issues, include:

1. City, store name, and floor area used  
2. Screenshot of layout (if generated)  
3. **Trace ID** from the UI footer  
4. Full API error message (if shown)  
5. Timestamp of the request  

Contact your GCP lab administrator for Vertex AI or Cloud Run access issues.

---

## 10. Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│  ARCHITECT COPILOT — QUICK STEPS                        │
├─────────────────────────────────────────────────────────┤
│  1. Open Streamlit UI                                   │
│  2. Enter City + Floor area (sqm)                       │
│  3. Click "Generate layout"                             │
│  4. Review 2D image + JSON + compliance checks           │
│  5. Export JSON / PNG for design review meeting         │
└─────────────────────────────────────────────────────────┘
```
