// Canvas generator for NyayaSarathi Core Platform Features
// Renders large, high-contrast, crystal-clear typography easily readable directly on the book without magnifying glass.

export interface LegalSpread {
  id: string;
  folio: string;
  title: string;
  category: string;
  desc: string;
  route: string;
  url: string;
}

export const SPREAD_METADATA = [
  {
    id: 'feature-01',
    folio: 'Feature 01',
    title: 'Judgment Predictor',
    category: 'Decision Intelligence',
    desc: 'Evaluates case arguments, outcome patterns, and relevant judicial precedents.',
    route: '/predictor',
  },
  {
    id: 'feature-02',
    folio: 'Feature 02',
    title: 'Legal Research',
    category: 'Hybrid RAG Search',
    desc: 'Query in plain language to retrieve ranked judgments by legal meaning using fused vector and BM25 indexes.',
    route: '/legal-research',
  },
  {
    id: 'feature-03',
    folio: 'Feature 03',
    title: 'Legal OCR',
    category: 'Document Ingestion',
    desc: 'Extracts clean text, entities, and tables from degraded scanned court orders, police FIRs, and charge sheets.',
    route: '/ocr',
  },
  {
    id: 'feature-04',
    folio: 'Feature 04',
    title: 'Legal Drafting',
    category: 'Court Pleading Generator',
    desc: 'Generates court-ready petitions, bail pleas, affidavits, and notices formatted to court practice rules.',
    route: '/legal-drafting',
  },
  {
    id: 'feature-05',
    folio: 'Feature 05',
    title: 'War Room',
    category: 'Trial Strategy Simulator',
    desc: 'Multi-agent adversarial simulation where an AI opposing counsel challenges your arguments before trial.',
    route: '/war-room',
  },
  {
    id: 'feature-06',
    folio: 'Feature 06',
    title: 'Contract Analyzer',
    category: 'Risk & Compliance Audit',
    desc: 'Audits agreements for dangerous clauses, hidden liabilities, one-sided indemnities, and termination traps.',
    route: '/contracts',
  },
  {
    id: 'feature-07',
    folio: 'Feature 07',
    title: 'Legal News',
    category: 'Real-Time Dispatches',
    desc: 'Curated 2-minute digests of Supreme Court orders, High Court rulings, and statutory gazette amendments.',
    route: '/news',
  },
];

// 2x Retina dimensions based on 1760x1240 base units
export const BASE_W = 1760;
export const BASE_H = 1240;
export const CANVAS_W = BASE_W; // 1760
export const CANVAS_H = BASE_H; // 1240

// Exact geometric coordinates in 1760x1240 units
export const BOOK_X0 = 90;
export const BOOK_Y0 = 270;
export const BOOK_W = 1580;
export const BOOK_H = 700;
export const GUTTER_X = 880;

// High-legibility clean system font stack
const FONT_SANS = '"Manrope", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
const FONT_MONO = '"Courier New", Consolas, monospace';

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function wrapText(
  ctx: CanvasRenderingContext2D,
  text: string,
  maxWidth: number
): string[] {
  const words = text.split(' ');
  const lines: string[] = [];
  let currentLine = '';

  for (let i = 0; i < words.length; i++) {
    const testLine = currentLine ? currentLine + ' ' + words[i] : words[i];
    const metrics = ctx.measureText(testLine);
    if (metrics.width > maxWidth && currentLine) {
      lines.push(currentLine);
      currentLine = words[i];
    } else {
      currentLine = testLine;
    }
  }
  if (currentLine) lines.push(currentLine);
  return lines;
}

function drawStamp(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  label: string,
  sublabel: string,
  color: string,
  angleRad: number = -0.02
) {
  ctx.save();
  ctx.translate(x + w / 2, y + h / 2);
  ctx.rotate(angleRad);
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 2.4;
  ctx.setLineDash([7, 3.5]);

  roundRect(ctx, -w / 2, -h / 2, w, h, 6);
  ctx.stroke();

  ctx.setLineDash([]);
  ctx.lineWidth = 1.2;
  roundRect(ctx, -w / 2 + 4, -h / 2 + 4, w - 8, h - 8, 4);
  ctx.stroke();

  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.font = `900 15px ${FONT_MONO}`;
  ctx.fillText(label, 0, sublabel ? -7 : 0);

  if (sublabel) {
    ctx.font = `800 11.5px ${FONT_SANS}`;
    ctx.fillText(sublabel, 0, 10);
  }
  ctx.restore();
}

function drawCourtSeal(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  radius: number,
  title: string
) {
  ctx.save();
  ctx.translate(cx, cy);

  ctx.strokeStyle = '#997E4F';
  ctx.fillStyle = '#997E4F';
  ctx.lineWidth = 2;

  ctx.beginPath();
  ctx.arc(0, 0, radius, 0, Math.PI * 2);
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(0, 0, radius - 3.5, 0, Math.PI * 2);
  ctx.stroke();

  // Scales icon
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  ctx.moveTo(0, -radius * 0.45);
  ctx.lineTo(0, radius * 0.45);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(-radius * 0.45, -radius * 0.2);
  ctx.lineTo(radius * 0.45, -radius * 0.2);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(-radius * 0.45, -radius * 0.2);
  ctx.lineTo(-radius * 0.55, radius * 0.1);
  ctx.lineTo(-radius * 0.35, radius * 0.1);
  ctx.closePath();
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(radius * 0.45, -radius * 0.2);
  ctx.lineTo(radius * 0.35, radius * 0.1);
  ctx.lineTo(radius * 0.55, radius * 0.1);
  ctx.closePath();
  ctx.stroke();

  ctx.font = `900 10.5px ${FONT_SANS}`;
  ctx.textAlign = 'center';
  ctx.fillText(title, 0, -radius * 0.55);

  ctx.restore();
}

function drawBookBase(ctx: CanvasRenderingContext2D) {
  const x0 = BOOK_X0;
  const y0 = BOOK_Y0;
  const bookW = BOOK_W;
  const bookH = BOOK_H;
  const gutterX = GUTTER_X;

  // 1. Dark Oxblood Leather Casing
  ctx.save();
  ctx.shadowColor = 'rgba(0,0,0,0.55)';
  ctx.shadowBlur = 24;
  ctx.shadowOffsetY = 10;
  ctx.fillStyle = '#1A120B';
  roundRect(ctx, x0 - 14, y0 - 10, bookW + 28, bookH + 20, 12);
  ctx.fill();
  ctx.restore();

  // Leather border
  ctx.strokeStyle = '#382216';
  ctx.lineWidth = 2.5;
  roundRect(ctx, x0 - 14, y0 - 10, bookW + 28, bookH + 20, 12);
  ctx.stroke();

  // Brass Corner Caps
  const corners = [
    [x0 - 14, y0 - 10],
    [x0 + bookW + 14, y0 - 10],
    [x0 - 14, y0 + bookH + 10],
    [x0 + bookW + 14, y0 + bookH + 10],
  ];
  ctx.fillStyle = '#B59A68';
  corners.forEach(([cx, cy], idx) => {
    ctx.beginPath();
    const sx = idx % 2 === 0 ? 1 : -1;
    const sy = idx < 2 ? 1 : -1;
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + sx * 26, cy);
    ctx.lineTo(cx, cy + sy * 26);
    ctx.closePath();
    ctx.fill();
  });

  // 2. Stacked Deckle Paper Edges
  ctx.strokeStyle = '#D4C4A8';
  ctx.lineWidth = 1;
  for (let i = 0; i < 3; i++) {
    ctx.beginPath();
    ctx.moveTo(x0 - 2 - i * 2.5, y0 + 8);
    ctx.lineTo(x0 - 2 - i * 2.5, y0 + bookH - 8);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(x0 + bookW + 2 + i * 2.5, y0 + 8);
    ctx.lineTo(x0 + bookW + 2 + i * 2.5, y0 + bookH - 8);
    ctx.stroke();
  }

  // 3. Left Page Parchment
  const leftGrad = ctx.createLinearGradient(x0, 0, gutterX, 0);
  leftGrad.addColorStop(0.0, '#E8DFC9');
  leftGrad.addColorStop(0.03, '#FDFBF4');
  leftGrad.addColorStop(0.92, '#FDFBF4');
  leftGrad.addColorStop(0.98, '#EAE0C8');
  leftGrad.addColorStop(1.0, '#C2AF8E');

  ctx.fillStyle = leftGrad;
  ctx.beginPath();
  ctx.moveTo(x0, y0 + 5);
  ctx.quadraticCurveTo(x0, y0, x0 + 5, y0);
  ctx.lineTo(gutterX, y0);
  ctx.lineTo(gutterX, y0 + bookH);
  ctx.lineTo(x0 + 5, y0 + bookH);
  ctx.quadraticCurveTo(x0, y0 + bookH, x0, y0 + bookH - 5);
  ctx.closePath();
  ctx.fill();

  // 4. Right Page Parchment
  const rightGrad = ctx.createLinearGradient(gutterX, 0, x0 + bookW, 0);
  rightGrad.addColorStop(0.0, '#C2AF8E');
  rightGrad.addColorStop(0.02, '#EAE0C8');
  rightGrad.addColorStop(0.08, '#FDFBF4');
  rightGrad.addColorStop(0.97, '#FDFBF4');
  rightGrad.addColorStop(1.0, '#E8DFC9');

  ctx.fillStyle = rightGrad;
  ctx.beginPath();
  ctx.moveTo(gutterX, y0);
  ctx.lineTo(x0 + bookW - 5, y0);
  ctx.quadraticCurveTo(x0 + bookW, y0, x0 + bookW, y0 + 5);
  ctx.lineTo(x0 + bookW, y0 + bookH - 5);
  ctx.quadraticCurveTo(x0 + bookW, y0 + bookH, x0 + bookW - 5, y0 + bookH);
  ctx.lineTo(gutterX, y0 + bookH);
  ctx.closePath();
  ctx.fill();

  // 5. Margin Ruling Lines (Oxblood court rule)
  ctx.strokeStyle = 'rgba(138, 45, 60, 0.45)';
  ctx.lineWidth = 1.6;
  ctx.beginPath();
  ctx.moveTo(x0 + 80, y0 + 20);
  ctx.lineTo(x0 + 80, y0 + bookH - 20);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(x0 + bookW - 80, y0 + 20);
  ctx.lineTo(x0 + bookW - 80, y0 + bookH - 20);
  ctx.stroke();

  // 6. Subtle Notebook Ruled Lines
  ctx.strokeStyle = 'rgba(43, 39, 33, 0.04)';
  ctx.lineWidth = 0.8;
  const lineStartY = y0 + 70;
  const lineEndY = y0 + bookH - 40;
  const lineStep = 26;

  for (let ly = lineStartY; ly <= lineEndY; ly += lineStep) {
    ctx.beginPath();
    ctx.moveTo(x0 + 20, ly);
    ctx.lineTo(gutterX - 18, ly);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(gutterX + 18, ly);
    ctx.lineTo(x0 + bookW - 20, ly);
    ctx.stroke();
  }

  // 7. Center Spine Deep Shadow Crease & Stitches
  const spineGrad = ctx.createLinearGradient(gutterX - 50, 0, gutterX + 50, 0);
  spineGrad.addColorStop(0.0, 'rgba(30, 20, 10, 0)');
  spineGrad.addColorStop(0.4, 'rgba(30, 20, 10, 0.2)');
  spineGrad.addColorStop(0.5, 'rgba(20, 12, 6, 0.45)');
  spineGrad.addColorStop(0.6, 'rgba(30, 20, 10, 0.2)');
  spineGrad.addColorStop(1.0, 'rgba(30, 20, 10, 0)');

  ctx.fillStyle = spineGrad;
  ctx.fillRect(gutterX - 50, y0, 100, bookH);

  // Stitched binding
  ctx.strokeStyle = 'rgba(181, 154, 104, 0.7)';
  ctx.lineWidth = 2;
  ctx.setLineDash([7, 12]);
  ctx.beginPath();
  ctx.moveTo(gutterX - 4, y0 + 16);
  ctx.lineTo(gutterX - 4, y0 + bookH - 16);
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(gutterX + 4, y0 + 16);
  ctx.lineTo(gutterX + 4, y0 + bookH - 16);
  ctx.stroke();
  ctx.setLineDash([]);

  // Silk ribbon bookmark
  ctx.save();
  ctx.fillStyle = '#6E2634';
  ctx.beginPath();
  ctx.moveTo(gutterX - 6, y0);
  ctx.lineTo(gutterX + 6, y0);
  ctx.lineTo(gutterX + 10, y0 + bookH + 50);
  ctx.lineTo(gutterX, y0 + bookH + 36);
  ctx.lineTo(gutterX - 10, y0 + bookH + 50);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
  ctx.fillRect(gutterX - 2, y0, 4, bookH + 40);
  ctx.restore();
}

// ─────────────────────────────────────────────────────────────────────────────
// FEATURE SPREAD RENDERER (Clean, Large, Bold & Visible Without Magnifier)
// ─────────────────────────────────────────────────────────────────────────────

interface FeaturePageData {
  folioNumber: string;
  featureTitle: string;
  routeUrl: string;
  tagline: string;
  inShortDescription: string;
  coreHighlights: Array<{ label: string; detail: string }>;
  stampText: string;
  stampSubtext: string;
  stampColor: string;
  stepsTitle: string;
  steps: Array<{ stepNum: string; title: string; desc: string }>;
  liveCardTitle: string;
  liveCardContent: string;
}

function renderFeatureSpread(
  ctx: CanvasRenderingContext2D,
  data: FeaturePageData
) {
  drawBookBase(ctx);
  const x0 = BOOK_X0;
  const y0 = BOOK_Y0;
  const gutterX = GUTTER_X;

  // ═══════════════════════════════════════════════════════════════════════════
  // LEFT PAGE: Large, Bold Title, Route Badge, Description & Capabilities
  // ═══════════════════════════════════════════════════════════════════════════
  const leftX = x0 + 95;
  const leftMaxW = gutterX - leftX - 28;

  // Top Category Tag
  ctx.font = `800 15px ${FONT_SANS}`;
  ctx.fillStyle = '#8C6F34';
  ctx.fillText(data.folioNumber.toUpperCase() + ' • PLATFORM CAPABILITY', leftX, y0 + 36);
  ctx.textAlign = 'right';
  ctx.fillText('NYAYASARATHI AI', gutterX - 28, y0 + 36);
  ctx.textAlign = 'left';

  // Feature Title Box with High-Contrast Route Badge
  ctx.fillStyle = 'rgba(110, 38, 52, 0.08)';
  ctx.strokeStyle = 'rgba(110, 38, 52, 0.38)';
  ctx.lineWidth = 1.6;
  roundRect(ctx, leftX, y0 + 48, leftMaxW, 84, 6);
  ctx.fill();
  ctx.stroke();

  // Big, bold feature title (Deep oxblood, crisp and unmistakable!)
  ctx.font = `900 34px ${FONT_SANS}`;
  ctx.fillStyle = '#5A1724';
  ctx.fillText(data.featureTitle, leftX + 16, y0 + 84);

  // Route pill
  ctx.fillStyle = '#1D211F';
  roundRect(ctx, leftX + 16, y0 + 96, 245, 25, 4);
  ctx.fill();

  ctx.font = `800 13px ${FONT_MONO}`;
  ctx.fillStyle = '#D6BA7E';
  ctx.fillText('ROUTE: ' + data.routeUrl, leftX + 26, y0 + 113);

  // Tagline
  ctx.font = `700 15px ${FONT_SANS}`;
  ctx.fillStyle = '#3E342B';
  ctx.fillText(data.tagline, leftX + 274, y0 + 113);

  // Section: What It Does (In Short)
  ctx.font = `900 18px ${FONT_SANS}`;
  ctx.fillStyle = '#5A1724';
  ctx.fillText('WHAT IT DOES (IN SHORT):', leftX, y0 + 158);

  // Description text - BOLD 20px font, deep rich black #0F0E0D
  ctx.font = `700 20px ${FONT_SANS}`;
  ctx.fillStyle = '#0F0E0D';
  const descLines = wrapText(ctx, data.inShortDescription, leftMaxW);
  descLines.forEach((line, i) => {
    ctx.fillText(line, leftX, y0 + 185 + i * 27);
  });

  // Section: Key Capabilities
  const hlStartY = y0 + 185 + descLines.length * 27 + 16;
  ctx.font = `900 18px ${FONT_SANS}`;
  ctx.fillStyle = '#5A1724';
  ctx.fillText('KEY CAPABILITIES:', leftX, hlStartY);

  data.coreHighlights.forEach((hl, idx) => {
    const cardY = hlStartY + 12 + idx * 52;
    ctx.fillStyle = '#FFFFFF';
    ctx.strokeStyle = '#D4C4A8';
    ctx.lineWidth = 1.4;
    roundRect(ctx, leftX, cardY, leftMaxW, 44, 5);
    ctx.fill();
    ctx.stroke();

    // Bold label
    ctx.font = `900 16px ${FONT_SANS}`;
    ctx.fillStyle = '#5A1724';
    ctx.fillText('• ' + hl.label, leftX + 14, cardY + 28);
    const labelWidth = ctx.measureText('• ' + hl.label).width;

    // Detail text
    ctx.font = `700 15px ${FONT_SANS}`;
    ctx.fillStyle = '#1F1B16';
    ctx.fillText(hl.detail, leftX + 14 + labelWidth + 10, cardY + 28);
  });

  // Left Stamp (Audited & Verified)
  drawStamp(
    ctx,
    leftX,
    y0 + BOOK_H - 74,
    330,
    50,
    data.stampText,
    data.stampSubtext,
    data.stampColor,
    -0.02
  );

  // ═══════════════════════════════════════════════════════════════════════════
  // RIGHT PAGE: Step-by-Step Working & Live Working Example
  // ═══════════════════════════════════════════════════════════════════════════
  const rightX = gutterX + 28;
  const rightMaxW = x0 + BOOK_W - rightX - 95;

  // Top header bar
  ctx.font = `800 15px ${FONT_SANS}`;
  ctx.fillStyle = '#8C6F34';
  ctx.fillText('HOW IT WORKS • 4-STEP PIPELINE', rightX, y0 + 36);
  ctx.textAlign = 'right';
  ctx.fillText('SYSTEM ARCHITECTURE', rightX + rightMaxW, y0 + 36);
  ctx.textAlign = 'left';

  // Section Heading
  ctx.font = `900 19px ${FONT_SANS}`;
  ctx.fillStyle = '#0F0E0D';
  ctx.fillText(data.stepsTitle, rightX, y0 + 64);

  // 4 Steps Cards (Prominent, clean, high-contrast)
  let stepY = y0 + 78;
  data.steps.forEach((st) => {
    ctx.fillStyle = '#FFFFFF';
    ctx.strokeStyle = '#D4C4A8';
    ctx.lineWidth = 1.4;
    roundRect(ctx, rightX, stepY, rightMaxW, 58, 5);
    ctx.fill();
    ctx.stroke();

    // Step Number Badge
    ctx.fillStyle = '#5A1724';
    roundRect(ctx, rightX + 8, stepY + 9, 30, 30, 15);
    ctx.fill();

    ctx.font = `900 15px ${FONT_MONO}`;
    ctx.fillStyle = '#FFFFFF';
    ctx.textAlign = 'center';
    ctx.fillText(st.stepNum, rightX + 23, stepY + 29);
    ctx.textAlign = 'left';

    // Step Title
    ctx.font = `900 16.5px ${FONT_SANS}`;
    ctx.fillStyle = '#0F0E0D';
    ctx.fillText(st.title, rightX + 48, stepY + 24);

    // Step Description
    ctx.font = `700 14px ${FONT_SANS}`;
    ctx.fillStyle = '#2A241D';
    const sLines = wrapText(ctx, st.desc, rightMaxW - 58);
    sLines.slice(0, 2).forEach((sl, sli) => {
      ctx.fillText(sl, rightX + 48, stepY + 44 + sli * 16);
    });

    stepY += 66;
  });

  // Live Output / Working Preview Card
  const liveCardY = stepY + 8;
  ctx.fillStyle = 'rgba(46, 94, 70, 0.08)';
  ctx.strokeStyle = '#225B3D';
  ctx.lineWidth = 1.6;
  roundRect(ctx, rightX, liveCardY, rightMaxW, 76, 5);
  ctx.fill();
  ctx.stroke();

  ctx.font = `900 13px ${FONT_MONO}`;
  ctx.fillStyle = '#1D5337';
  ctx.fillText('LIVE ENGINE PREVIEW: ' + data.liveCardTitle.toUpperCase(), rightX + 14, liveCardY + 22);

  ctx.font = `800 15px ${FONT_SANS}`;
  ctx.fillStyle = '#0D0C0A';
  const cLines = wrapText(ctx, data.liveCardContent, rightMaxW - 28);
  cLines.slice(0, 2).forEach((cl, cli) => {
    ctx.fillText(cl, rightX + 14, liveCardY + 44 + cli * 19);
  });

  // Official Seal
  drawCourtSeal(ctx, rightX + rightMaxW - 38, y0 + BOOK_H - 50, 34, 'NYAYASARATHI');

  ctx.font = `italic 14px ${FONT_SANS}`;
  ctx.fillStyle = '#3E2A1A';
  ctx.fillText('Autonomous Judicial Decision Support Pipeline', rightX, y0 + BOOK_H - 55);
  ctx.font = `800 12px ${FONT_MONO}`;
  ctx.fillStyle = '#8C6F34';
  ctx.fillText('100% CITATION-VERIFIABLE • GROUND TRUTH AUDITED', rightX, y0 + BOOK_H - 38);
}

// ─────────────────────────────────────────────────────────────────────────────
// SPREAD RENDERERS FOR ALL 7 PLATFORM FEATURES
// ─────────────────────────────────────────────────────────────────────────────

// 1. JUDGMENT PREDICTOR
function renderFeaturePredictor(ctx: CanvasRenderingContext2D) {
  renderFeatureSpread(ctx, {
    folioNumber: 'Feature 01',
    featureTitle: 'JUDGMENT PREDICTOR',
    routeUrl: '/predictor',
    tagline: 'Judicial Precedent Analysis & Outcome Patterns',
    inShortDescription:
      'Analyzes case arguments, procedural grounds, and statutory provisions against historical court rulings to surface argument vulnerabilities and precedent trends.',
    coreHighlights: [
      { label: 'Precedent Patterns:', detail: 'Evaluates outcomes of similar disputes across High Courts.' },
      { label: 'Statutory Mapping:', detail: 'Identifies relevant case precedents cited under applicable Acts.' },
      { label: 'Vulnerability Analysis:', detail: 'Surfaces missing statutory ingredients and opposing doctrines.' },
    ],
    stampText: 'DECISION SUPPORT',
    stampSubtext: 'HISTORICAL PRECEDENT ANALYSIS',
    stampColor: '#8A2D3C',
    stepsTitle: 'HOW PRECEDENT ANALYSIS WORKS (4 STEPS):',
    steps: [
      { stepNum: '1', title: 'Fact & Ground Ingestion', desc: 'Ingests petition facts, statutory sections, and causes of action.' },
      { stepNum: '2', title: 'Precedent Matching', desc: 'Retrieves relevant judicial rulings matching case facts and sections.' },
      { stepNum: '3', title: 'Factor Weighting', desc: 'Identifies supporting versus opposing statutory considerations.' },
      { stepNum: '4', title: 'Assessment Report', desc: 'Summarizes key precedents, ratio decidendi, and legal grounds.' },
    ],
    liveCardTitle: 'COMMERCIAL INJUNCTION ANALYSIS',
    liveCardContent:
      'Precedent trend: Injunctions on unconditional bank guarantees typically require clear proof of egregious fraud; citations mapped.',
  });
}

// 2. LEGAL RESEARCH
function renderFeatureResearch(ctx: CanvasRenderingContext2D) {
  renderFeatureSpread(ctx, {
    folioNumber: 'Feature 02',
    featureTitle: 'LEGAL RESEARCH',
    routeUrl: '/legal-research',
    tagline: 'Natural Language Case Law Search via Hybrid Vector RAG',
    inShortDescription:
      'Search Indian case law in plain conversational language. Retrieves judgments by legal doctrine and meaning, eliminating the limitations of fragile exact keyword matching.',
    coreHighlights: [
      { label: 'Plain-English Queries:', detail: 'Ask "anticipatory bail in economic offenses" without booleans.' },
      { label: 'Vector + BM25 Fusion:', detail: 'Dense embeddings find legal concepts; BM25 matches exact sections.' },
      { label: 'Paragraph Precision:', detail: 'Takes you straight to exact paragraph holding the ratio decidendi.' },
    ],
    stampText: 'HYBRID RAG RETRIEVAL',
    stampSubtext: 'VECTOR + BM25 CO-INDEXED',
    stampColor: '#2E5E46',
    stepsTitle: 'HOW LEGAL RESEARCH WORKS (4 STEPS):',
    steps: [
      { stepNum: '1', title: 'Natural Language Parsing', desc: 'Understands legal intent, acts, remedies, and jurisdiction from plain queries.' },
      { stepNum: '2', title: 'Dense Semantic Vector Search', desc: 'Embeds query into legal semantic space to locate conceptually related cases.' },
      { stepNum: '3', title: 'Reciprocal Rank Fusion (RRF)', desc: 'Blends semantic similarity with exact section and citation keyword ranks.' },
      { stepNum: '4', title: 'Synthesized Legal Brief', desc: 'Returns a structured summary with citations linked to primary paragraphs.' },
    ],
    liveCardTitle: 'SAMPLE SEARCH RESULT',
    liveCardContent:
      'Query: "Delay in FIR under Sec. 420" → Retrieved State v. Sharma (2019) with exact Para 14 ratio decidendi.',
  });
}

// 3. LEGAL OCR
function renderFeatureOCR(ctx: CanvasRenderingContext2D) {
  renderFeatureSpread(ctx, {
    folioNumber: 'Feature 03',
    featureTitle: 'LEGAL OCR',
    routeUrl: '/ocr',
    tagline: 'Layout-Aware Ingestion for Court Orders & FIR Scans',
    inShortDescription:
      'Engineered specifically for degraded Indian court records, police FIRs, charge sheets, and legacy petitions. Reconstructs complex layouts, tables, and seals into structured text.',
    coreHighlights: [
      { label: 'Degraded Scan Cleanup:', detail: 'Removes faint ink bleeds, stamps, watermarks, and page skewing.' },
      { label: 'Bilingual English & Hindi:', detail: 'Accurate text extraction across Latin and Devanagari court scripts.' },
      { label: 'Entity Auto-Extraction:', detail: 'Auto-tags Judges, Advocates, FIR Nos, Sections, and Dates.' },
    ],
    stampText: 'LAYOUT-AWARE OCR',
    stampSubtext: 'MULTI-FORMAT RECORD INGEST',
    stampColor: '#B59A68',
    stepsTitle: 'HOW LEGAL OCR WORKS (4 STEPS):',
    steps: [
      { stepNum: '1', title: 'Multi-Format Ingestion', desc: 'Accepts scanned PDFs, smartphone photos, DOCX, and legacy paper scans.' },
      { stepNum: '2', title: 'Denoising & De-skewing', desc: 'Neural filters clean stamp overlaps, punch holes, and scan skewing.' },
      { stepNum: '3', title: 'Layout Reconstruction', desc: 'Preserves cause titles, two-column formats, tabular exhibits, and notes.' },
      { stepNum: '4', title: 'Entity Recognition (NER)', desc: 'Identifies and indexes acts, criminal sections, parties, and dates.' },
    ],
    liveCardTitle: 'SCANNED CHARGESHEET INTAKE',
    liveCardContent:
      'Ingested 48-page scanned chargesheet: Extracted 14 accused entities, 6 penal sections, and 24 exhibits in 3.1s.',
  });
}

// 4. LEGAL DRAFTING
function renderFeatureDrafting(ctx: CanvasRenderingContext2D) {
  renderFeatureSpread(ctx, {
    folioNumber: 'Feature 04',
    featureTitle: 'LEGAL DRAFTING',
    routeUrl: '/legal-drafting',
    tagline: 'Court-Ready Pleadings, Petitions & Notice Synthesis',
    inShortDescription:
      'Draft court-compliant legal pleadings in minutes. Synthesizes writ petitions, bail applications, affidavits, legal notices, and rejoinders formatted to court rules.',
    coreHighlights: [
      { label: 'Court-Ready Pleadings:', detail: 'Creates complete petitions with facts, grounds, and prayers.' },
      { label: 'Procedural Rules Format:', detail: 'Matches High Court and Supreme Court practice directions.' },
      { label: 'Verified Citations:', detail: 'Automatically inserts verified case citations into legal grounds.' },
    ],
    stampText: 'COURT DRAFTING ENGINE',
    stampSubtext: 'FORMAT RULES VERIFIED',
    stampColor: '#8A2D3C',
    stepsTitle: 'HOW LEGAL DRAFTING WORKS (4 STEPS):',
    steps: [
      { stepNum: '1', title: 'Case Input & Reliefs', desc: 'Select pleading type, enter parties, facts, and prayers sought before court.' },
      { stepNum: '2', title: 'Clause & Grounds Synthesis', desc: 'Auto-generates structured grounds of law and fact statements.' },
      { stepNum: '3', title: 'Citation Enrichment', desc: 'Injects controlling Supreme Court precedents supporting your plea.' },
      { stepNum: '4', title: 'One-Click Export', desc: 'Export formatted court-ready documents directly to DOCX or PDF.' },
    ],
    liveCardTitle: 'REGULAR BAIL SYNTHESIS',
    liveCardContent:
      'Generated 14 grounds of law, Satender Antil parity doctrine plea, and prayer clause in 14.2 seconds.',
  });
}

// 5. WAR ROOM
function renderFeatureWarRoom(ctx: CanvasRenderingContext2D) {
  renderFeatureSpread(ctx, {
    folioNumber: 'Feature 05',
    featureTitle: 'WAR ROOM',
    routeUrl: '/war-room',
    tagline: 'Multi-Agent Adversarial Trial Strategy Simulator',
    inShortDescription:
      'A multi-agent adversarial strategy simulator. An AI opposing counsel agent attacks your legal arguments, tests bench skepticism, and finds vulnerabilities before you go to court.',
    coreHighlights: [
      { label: 'Adversarial Simulation:', detail: 'AI plays opposing counsel to challenge your evidence and claims.' },
      { label: 'Vulnerability Heatmap:', detail: 'Flags weak precedents, procedural bars, and missing elements.' },
      { label: 'Cross-Examination Prep:', detail: 'Suggests counter-arguments and bench questions to anticipate.' },
    ],
    stampText: 'WAR ROOM TESTED',
    stampSubtext: 'ADVERSARIAL TRIAL SIMULATOR',
    stampColor: '#2E5E46',
    stepsTitle: 'HOW THE WAR ROOM WORKS (4 STEPS):',
    steps: [
      { stepNum: '1', title: 'Submit Pleading or Brief', desc: 'Upload your draft petition, written statement, or strategy notes.' },
      { stepNum: '2', title: 'Multi-Agent Roleplay', desc: 'Opposing counsel and judge agents scrutinize your legal claims.' },
      { stepNum: '3', title: 'Adversarial Attack Phase', desc: 'Opposing agent challenges jurisdiction, delay, and substantive merits.' },
      { stepNum: '4', title: 'Fortified Strategy Brief', desc: 'Delivers counter-rebuttals and strengthened arguments to win in court.' },
    ],
    liveCardTitle: 'WAR ROOM DEBATE SIMULATION',
    liveCardContent:
      'Opposing Agent spotted limitation period objection → System automatically reinforced plea with Section 14 grounds.',
  });
}

// 6. CONTRACT ANALYZER
function renderFeatureContracts(ctx: CanvasRenderingContext2D) {
  renderFeatureSpread(ctx, {
    folioNumber: 'Feature 06',
    featureTitle: 'CONTRACT ANALYZER',
    routeUrl: '/contracts',
    tagline: 'Automated Agreement Audit & Risk Redlining',
    inShortDescription:
      'Automated contract review and risk auditing. Scans agreements for dangerous clauses, hidden liabilities, one-sided indemnities, termination traps, and non-compliance flags.',
    coreHighlights: [
      { label: 'High-Risk Clause Detection:', detail: 'Flags unlimited liabilities, harsh lock-ins, and penalties.' },
      { label: 'Deviation Benchmarking:', detail: 'Compares clauses against standard market benchmarks.' },
      { label: 'Redline Recommendations:', detail: 'Generates alternative protective phrasing in one click.' },
    ],
    stampText: 'CONTRACT AUDIT',
    stampSubtext: 'STATUTORY RISK AUDIT',
    stampColor: '#B59A68',
    stepsTitle: 'HOW CONTRACT ANALYSIS WORKS (4 STEPS):',
    steps: [
      { stepNum: '1', title: 'Agreement Upload', desc: 'Ingests NDAs, MSAs, vendor contracts, or lease agreements (PDF/DOCX).' },
      { stepNum: '2', title: 'Clause Decomposition', desc: 'Automatically splits agreements into standardized clause types.' },
      { stepNum: '3', title: 'Risk Scoring & Benchmarking', desc: 'Rates each clause: Safe (Green), Caution (Amber), High Risk (Red).' },
      { stepNum: '4', title: 'Redline Suggestions', desc: 'Provides lawyer-reviewed alternate clauses to balance legal risk.' },
    ],
    liveCardTitle: 'MSA CLAUSE AUDIT RESULT',
    liveCardContent:
      'Identified one-sided uncapped indemnity in Master Service Agreement → Generated balanced mutual cap clause.',
  });
}

// 7. LEGAL NEWS
function renderFeatureNews(ctx: CanvasRenderingContext2D) {
  renderFeatureSpread(ctx, {
    folioNumber: 'Feature 07',
    featureTitle: 'LEGAL NEWS',
    routeUrl: '/news',
    tagline: 'Real-Time Court Dispatches & Gazette Intelligence',
    inShortDescription:
      'Stay ahead with real-time Indian legal news. Curates and summarizes landmark Supreme Court judgments, High Court rulings, gazette notifications, and statutory law amendments.',
    coreHighlights: [
      { label: 'Live Court Dispatches:', detail: 'Real-time coverage of active Supreme Court constitution benches.' },
      { label: 'AI Judgment Summaries:', detail: '2-minute bullet summaries of 100+ page complex court orders.' },
      { label: 'Gazette & Act Alerts:', detail: 'Instant updates on statutory notifications and new rules.' },
    ],
    stampText: 'REAL-TIME LEGAL NEWS',
    stampSubtext: 'VERIFIED COURT DISPATCHES',
    stampColor: '#8A2D3C',
    stepsTitle: 'HOW LEGAL NEWS WORKS (4 STEPS):',
    steps: [
      { stepNum: '1', title: 'Multi-Court Ingestion', desc: 'Monitors Supreme Court, High Courts, and Gazette feeds 24/7.' },
      { stepNum: '2', title: 'AI Story Grouping', desc: 'Deduplicates and clusters related court orders and legal reactions.' },
      { stepNum: '3', title: 'Ratio & Issue Extraction', desc: 'Condenses multi-page rulings into facts, holding, and ratio.' },
      { stepNum: '4', title: 'Topic & Court Filtering', desc: 'Filter by Constitutional, Criminal, Corporate, or Tax Law.' },
    ],
    liveCardTitle: 'LATEST GAZETTE UPDATE',
    liveCardContent:
      'Gazette Notification: Bharatiya Nagarik Suraksha Sanhita procedural rules notified with instant AI impact analysis.',
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Master Generator Function (2x Retina with 1760x1240 coordinate system)
// ─────────────────────────────────────────────────────────────────────────────
export function generateLegalSpreads(): LegalSpread[] {
  if (typeof window === 'undefined') return [];

  const canvas = document.createElement('canvas');
  canvas.width = CANVAS_W;
  canvas.height = CANVAS_H;
  const ctx = canvas.getContext('2d');
  if (!ctx) return [];

  // Enable crisp subpixel rendering
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';

  const renderers = [
    renderFeaturePredictor,
    renderFeatureResearch,
    renderFeatureOCR,
    renderFeatureDrafting,
    renderFeatureWarRoom,
    renderFeatureContracts,
    renderFeatureNews,
  ];

  return SPREAD_METADATA.map((meta, index) => {
    ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);
    ctx.save();
    renderers[index](ctx);
    ctx.restore();

    const dataUrl = canvas.toDataURL('image/png');
    return {
      ...meta,
      url: dataUrl,
    };
  });
}
