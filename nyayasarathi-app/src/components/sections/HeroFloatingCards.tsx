'use client';

import React, { useRef, useState, useEffect } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import {
  Scale,
  FileText,
  ShieldAlert,
  CheckCircle2,
  Database,
  Search,
  Sparkles,
  Award,
  Link2,
  GitBranch,
  Layers,
  BookOpen,
  ChevronDown,
} from 'lucide-react';

/* ── Archival Wax / Rubber Stamp Component ── */
function ArchivalStamp({
  label,
  sublabel,
  color = 'red',
  rotate = -3,
}: {
  label: string;
  sublabel?: string;
  color?: 'red' | 'green' | 'brass';
  rotate?: number;
}) {
  const colorStyles = {
    red: 'border-[#8A2D3C] text-[#8A2D3C] bg-[#8A2D3C]/[0.06]',
    green: 'border-[#385E49] text-[#385E49] bg-[#385E49]/[0.06]',
    brass: 'border-[#8C6F34] text-[#8C6F34] bg-[#8C6F34]/[0.06]',
  };

  return (
    <div
      style={{ transform: `rotate(${rotate}deg)` }}
      className={`archival-stamp px-2.5 py-1 rounded-sm border-[1.5px] border-dashed ${colorStyles[color]} shadow-sm z-20`}
    >
      <span className="font-mono text-[8.5px] font-extrabold tracking-wider leading-none">
        {label}
      </span>
      {sublabel && (
        <span className="font-sans text-[7px] font-semibold tracking-widest opacity-85 mt-0.5">
          {sublabel}
        </span>
      )}
    </div>
  );
}

/* ── Antique Manuscript Texture & Stains Layer ── */
function AntiqueParchmentEffects({
  side,
  stainType = 'tea-ring',
}: {
  side: 'left' | 'right';
  stainType?: 'tea-ring' | 'water-spill' | 'mixed';
}) {
  return (
    <>
      {/* Dog-Eared Corner Fold Crease on Outer Top Corner */}
      {side === 'left' ? (
        <div className="dog-ear-left-top z-20" />
      ) : (
        <div className="dog-ear-right-top z-20" />
      )}

      {/* Red Archival Court Margin Ruling Line */}
      {side === 'left' ? (
        <div className="legal-margin-line-left z-10" />
      ) : (
        <div className="legal-margin-line-right z-10" />
      )}

      {/* Vintage Foxing Age Speckles */}
      <div className="foxing-speckles z-10" />

      {/* Realistic Organic Tea / Water Ring Stain */}
      {stainType === 'tea-ring' && (
        <div
          className={`tea-stain-ring z-10 ${
            side === 'left'
              ? 'w-24 h-24 sm:w-28 sm:h-28 -top-3 -right-3 opacity-75'
              : 'w-20 h-20 sm:w-24 sm:h-24 bottom-6 right-8 opacity-70'
          }`}
        />
      )}

      {stainType === 'water-spill' && (
        <div
          className={`water-spill-blot z-10 ${
            side === 'left'
              ? 'w-32 h-24 bottom-4 left-6 opacity-65'
              : 'w-28 h-20 top-8 right-6 opacity-60'
          }`}
        />
      )}

      {stainType === 'mixed' && (
        <>
          <div className="tea-stain-ring w-20 h-20 -bottom-3 right-10 opacity-70 z-10" />
          <div className="water-spill-blot w-24 h-16 top-10 left-6 opacity-55 z-10" />
        </>
      )}

      {/* Faded Registrar Docket Notation in Margin */}
      <div
        className={`absolute bottom-2 font-mono text-[7px] text-[#8C7A60]/45 tracking-wider pointer-events-none z-10 ${
          side === 'left' ? 'left-8' : 'right-8'
        }`}
      >
        № CR-2026/REG-9 • ARCHIVED
      </div>
    </>
  );
}

/* ── Page 1: EVIDENCE INGESTION (Exhibit A-12) ── */
function PageEvidenceIngestion() {
  return (
    <div className="h-full flex flex-col justify-between p-5 sm:p-7 select-none relative worn-corner-left">
      <div className="absolute top-0 bottom-0 right-0 w-1.5 binding-stitches pointer-events-none z-20" />
      <AntiqueParchmentEffects side="left" stainType="tea-ring" />

      <div className="relative z-10">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-[#D4C2A3] pb-2.5 mb-3.5">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#7A6B53] font-bold">
              Folio 01 • Exhibit Intake
            </span>
          </div>
          <span className="font-mono text-[9px] text-[#8C7A60] tracking-widest font-semibold">
            NODE 01/06
          </span>
        </div>

        {/* Title and Badge */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#8C6F34]" strokeWidth={1.75} />
              <h3 className="font-display text-lg sm:text-xl font-bold text-[#2A1E14] leading-none">
                Exhibit A-12
              </h3>
            </div>
            <p className="font-sans text-[11px] font-medium text-[#6B5A44] mt-0.5">
              Forensic PDF Scan &amp; Intake
            </p>
          </div>
          <ArchivalStamp label="SECURED DEPOSIT" sublabel="ARCHIVE DIVISION" color="brass" rotate={-2} />
        </div>

        {/* Legal Document Parchment Inset */}
        <div className="bg-[#EFE4CF]/90 border border-[#D8C6A7] rounded p-3 mb-3 relative overflow-hidden shadow-inner">
          <div className="absolute top-1.5 right-2 font-mono text-[8px] text-[#9A876D]">
            REF: CR-2022/841-A
          </div>
          <p className="font-mono text-[9px] uppercase tracking-wider text-[#8A4520] mb-1 font-semibold">
            CRIMINAL BRIEF EXTRACT:
          </p>
          <p className="font-legal text-xs sm:text-[13px] text-[#2F241A] leading-relaxed italic">
            &ldquo;Discrepancies noted in digital signature timestamps on page 42. Cryptographic audit indicates discrepancy with primary custody log.&rdquo;
          </p>
        </div>

        {/* Technical Ledger Metadata */}
        <div className="space-y-1.5 text-[10px] font-sans">
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">Custody Chain Verification:</span>
            <span className="font-mono font-medium text-[#2F241A]">Section 65B(4) Cert</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">Digest Checksum:</span>
            <span className="font-mono text-[9px] text-[#6E2634]">SHA256: 8f4b2e91...</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">Ingestion Protocol:</span>
            <span className="font-mono text-[#2F241A]">Lossless Optical OCR</span>
          </div>
        </div>
      </div>

      {/* Footer Status */}
      <div className="pt-3 border-t border-[#D4C2A3] flex items-center justify-between mt-auto relative z-10">
        <span className="font-mono text-[9px] tracking-wider text-[#7A6952]">
          STAGE: INTAKE &amp; PARSE
        </span>
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm bg-[#8C6F34]/15 border border-[#8C6F34]/40 font-mono text-[9px] font-bold text-[#6D5422]">
          <span className="w-1.5 h-1.5 rounded-full bg-[#8C6F34] animate-pulse" />
          Ready to Map
        </span>
      </div>
    </div>
  );
}

/* ── Page 2: PRECEDENT MATCH (State of MH v. K. Shah) ── */
function PagePrecedentMatch() {
  return (
    <div className="h-full flex flex-col justify-between p-5 sm:p-7 select-none relative worn-corner-right">
      <div className="absolute top-0 bottom-0 left-0 w-1.5 binding-stitches pointer-events-none z-20" />
      <AntiqueParchmentEffects side="right" stainType="water-spill" />

      <div className="relative z-10">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-[#D4C2A3] pb-2.5 mb-3.5">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#7A6B53] font-bold">
              Folio 02 • Precedent Search
            </span>
          </div>
          <span className="font-mono text-[9px] text-[#8C7A60] tracking-widest font-semibold">
            NODE 02/06
          </span>
        </div>

        {/* Title and Badge */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <Scale className="w-4 h-4 text-[#385E49]" strokeWidth={1.75} />
              <h3 className="font-display text-lg sm:text-xl font-bold text-[#2A1E14] leading-none">
                Precedent Match
              </h3>
            </div>
            <p className="font-sans text-[11px] font-medium text-[#4D6556] mt-0.5">
              State of MH v. K. Shah (2022)
            </p>
          </div>
          <ArchivalStamp label="98% CONFIDENT" sublabel="BM25 BENCHMARK" color="green" rotate={2} />
        </div>

        {/* Law Report Ratio Box */}
        <div className="bg-[#EFE4CF]/90 border border-[#D8C6A7] rounded p-3 mb-3 relative overflow-hidden shadow-inner">
          <div className="absolute top-1.5 right-2 font-mono text-[8px] text-[#9A876D]">
            CIT: (2022) 4 SCC 182
          </div>
          <p className="font-mono text-[9px] uppercase tracking-wider text-[#385E49] mb-1 font-semibold">
            CRIMINAL LAW JURISPRUDENCE:
          </p>
          <p className="font-legal text-xs sm:text-[13px] text-[#2F241A] leading-relaxed">
            &ldquo;Precedent governs admissibility of electronic records without certificate. <span className="legal-highlight font-semibold">Corroborated secondary evidence remains admissible upon judicial scrutiny.</span>&rdquo;
          </p>
        </div>

        {/* Precedent Rank Specs */}
        <div className="space-y-1.5 text-[10px] font-sans">
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">Corpus Search Pool:</span>
            <span className="font-mono font-medium text-[#2F241A]">12,400+ Judgments</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">BM25 Relevance Score:</span>
            <span className="font-mono font-bold text-[#385E49]">0.984 (Rank #1)</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">Bench Authority:</span>
            <span className="font-mono text-[#2F241A]">Division Bench, High Court</span>
          </div>
        </div>
      </div>

      {/* Footer Status */}
      <div className="pt-3 border-t border-[#D4C2A3] flex items-center justify-between mt-auto relative z-10">
        <span className="font-mono text-[9px] tracking-wider text-[#7A6952]">
          INDEX: BM25 LEXICAL
        </span>
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm bg-[#385E49]/15 border border-[#385E49]/40 font-mono text-[9px] font-bold text-[#2A4837]">
          <CheckCircle2 className="w-3 h-3 text-[#385E49]" />
          98% Confident
        </span>
      </div>
    </div>
  );
}

/* ── Page 3: VERITY CITATION (IPC Section 302 / BNS) ── */
function PageVerityCitation() {
  return (
    <div className="h-full flex flex-col justify-between p-5 sm:p-7 select-none relative worn-corner-left">
      <div className="absolute top-0 bottom-0 right-0 w-1.5 binding-stitches pointer-events-none z-20" />
      <AntiqueParchmentEffects side="left" stainType="mixed" />

      <div className="relative z-10">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-[#D4C2A3] pb-2.5 mb-3.5">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#7A6B53] font-bold">
              Folio 03 • Statutory Verification
            </span>
          </div>
          <span className="font-mono text-[9px] text-[#8C7A60] tracking-widest font-semibold">
            NODE 03/06
          </span>
        </div>

        {/* Title and Badge */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-[#8A2D3C]" strokeWidth={1.75} />
              <h3 className="font-display text-lg sm:text-xl font-bold text-[#2A1E14] leading-none">
                Verify Citation
              </h3>
            </div>
            <p className="font-sans text-[11px] font-medium text-[#7D3442] mt-0.5">
              IPC Section 302 ⇄ BNS Mapped
            </p>
          </div>
          <ArchivalStamp label="CROSS-VERIFIED" sublabel="GROUND TRUTH AUDIT" color="red" rotate={-1} />
        </div>

        {/* Verification Diagram Schema */}
        <div className="bg-[#EFE4CF]/90 border border-[#D8C6A7] rounded p-3 mb-3 relative overflow-hidden shadow-inner">
          <p className="font-mono text-[9px] uppercase tracking-wider text-[#8A2D3C] mb-2 font-semibold flex items-center gap-1.5">
            <Link2 className="w-3 h-3 text-[#8A2D3C]" />
            STATUTE HARMONIZATION TRACE:
          </p>

          <div className="grid grid-cols-3 gap-1.5 text-center font-mono text-[9px] mb-2">
            <div className="p-1.5 bg-[#FAF4E8] rounded border border-[#D5C2A4]">
              <div className="text-[7.5px] text-[#7A6952]">SOURCE</div>
              <div className="font-bold text-[#2A1E14]">IPC §302</div>
            </div>
            <div className="p-1.5 bg-[#FAF4E8] rounded border border-[#D5C2A4] flex flex-col justify-center">
              <div className="text-[7.5px] text-[#7A6952]">MAPPING</div>
              <div className="font-bold text-[#8A2D3C]">BNS §103(1)</div>
            </div>
            <div className="p-1.5 bg-[#FAF4E8] rounded border border-[#385E49]/40 text-[#2A4837] flex flex-col justify-center">
              <div className="text-[7.5px] text-[#385E49]">AUDIT</div>
              <div className="font-bold">VERIFIED ✓</div>
            </div>
          </div>

          <p className="font-legal text-xs text-[#2F241A] leading-relaxed italic">
            &ldquo;Ground Truth: Verifying corpus mapping against Bharatiya Nyaya Sanhita equivalents with zero hallucination guarantee.&rdquo;
          </p>
        </div>

        {/* Citation Metadata */}
        <div className="space-y-1.5 text-[10px] font-sans">
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">Statutory Cross-Check:</span>
            <span className="font-mono font-medium text-[#2F241A]">IPC to BNS Full Alignment</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">Hallucination Risk:</span>
            <span className="font-mono font-bold text-[#385E49]">0.00% (Strict Anchored)</span>
          </div>
        </div>
      </div>

      {/* Footer Status */}
      <div className="pt-3 border-t border-[#D4C2A3] flex items-center justify-between mt-auto relative z-10">
        <span className="font-mono text-[9px] tracking-wider text-[#7A6952]">
          AUDIT: DUAL CODE VERIFIED
        </span>
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm bg-[#8A2D3C]/12 border border-[#8A2D3C]/35 font-mono text-[9px] font-bold text-[#72202E]">
          Warning Checked
        </span>
      </div>
    </div>
  );
}

/* ── Page 4: CHUNK EXTRACTION (Paragraph 14 Analysis) ── */
function PageChunkExtraction() {
  return (
    <div className="h-full flex flex-col justify-between p-5 sm:p-7 select-none relative worn-corner-right">
      <div className="absolute top-0 bottom-0 left-0 w-1.5 binding-stitches pointer-events-none z-20" />
      <AntiqueParchmentEffects side="right" stainType="tea-ring" />

      <div className="relative z-10">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-[#D4C2A3] pb-2.5 mb-3.5">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#7A6B53] font-bold">
              Folio 04 • Context Chunking
            </span>
          </div>
          <span className="font-mono text-[9px] text-[#8C7A60] tracking-widest font-semibold">
            NODE 04/06
          </span>
        </div>

        {/* Title and Badge */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-[#7A6B53]" strokeWidth={1.75} />
              <h3 className="font-display text-lg sm:text-xl font-bold text-[#2A1E14] leading-none">
                Chunk Extraction
              </h3>
            </div>
            <p className="font-sans text-[11px] font-medium text-[#6B5A44] mt-0.5">
              Paragraph 14 Boundary Analysis
            </p>
          </div>
          <ArchivalStamp label="SEGMENTED" sublabel="NER RECOGNITION" color="brass" rotate={2} />
        </div>

        {/* Segmented Document Box with NER Tags */}
        <div className="bg-[#EFE4CF]/90 border border-[#D8C6A7] rounded p-3 mb-3 relative overflow-hidden shadow-inner">
          <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
            <span className="px-1.5 py-0.5 rounded bg-[#B59A68]/20 border border-[#B59A68]/50 text-[#5C4518] font-mono text-[8px] font-bold">
              JUDGE: &ldquo;A.K. Sen&rdquo;
            </span>
            <span className="px-1.5 py-0.5 rounded bg-[#71877A]/20 border border-[#71877A]/50 text-[#2E4839] font-mono text-[8px] font-bold">
              SECTION: 438 CrPC
            </span>
            <span className="px-1.5 py-0.5 rounded bg-[#8A3545]/20 border border-[#8A3545]/50 text-[#611C28] font-mono text-[8px] font-bold">
              JURISDICTION: Bombay HC
            </span>
          </div>
          <p className="font-legal text-xs sm:text-[13px] text-[#2F241A] leading-relaxed">
            &ldquo;RAG CONTEXT: Sentence boundaries parsed. <span className="legal-highlight font-semibold">The applicant has made out a prima facie case of non-bailable apprehension under Section 438</span> with no custodial recovery required.&rdquo;
          </p>
        </div>

        {/* Chunk Details */}
        <div className="space-y-1.5 text-[10px] font-sans">
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">Token Dimension / Length:</span>
            <span className="font-mono font-medium text-[#2F241A]">184 Tokens • 1536 Dim</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">Classifier Boundary:</span>
            <span className="font-mono text-[#2F241A]">Paragraph 14 [Lines 210-244]</span>
          </div>
        </div>
      </div>

      {/* Footer Status */}
      <div className="pt-3 border-t border-[#D4C2A3] flex items-center justify-between mt-auto relative z-10">
        <span className="font-mono text-[9px] tracking-wider text-[#7A6952]">
          CLASSIFIER: RECURSIVE NER
        </span>
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm bg-[#7A6B53]/15 border border-[#7A6B53]/40 font-mono text-[9px] font-bold text-[#453A2A]">
          <Layers className="w-3 h-3 text-[#7A6B53]" />
          Segmented
        </span>
      </div>
    </div>
  );
}

/* ── Page 5: SEMANTIC QUERY (Anticipatory Bail Scope) ── */
function PageSemanticQuery() {
  return (
    <div className="h-full flex flex-col justify-between p-5 sm:p-7 select-none relative worn-corner-left">
      <div className="absolute top-0 bottom-0 right-0 w-1.5 binding-stitches pointer-events-none z-20" />
      <AntiqueParchmentEffects side="left" stainType="water-spill" />

      <div className="relative z-10">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-[#D4C2A3] pb-2.5 mb-3.5">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#7A6B53] font-bold">
              Folio 05 • Semantic Vector Space
            </span>
          </div>
          <span className="font-mono text-[9px] text-[#8C7A60] tracking-widest font-semibold">
            NODE 05/06
          </span>
        </div>

        {/* Title and Badge */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-[#8C6F34]" strokeWidth={1.75} />
              <h3 className="font-display text-lg sm:text-xl font-bold text-[#2A1E14] leading-none">
                Semantic Query
              </h3>
            </div>
            <p className="font-sans text-[11px] font-medium text-[#6B5A44] mt-0.5">
              Anticipatory Bail Scope (Sec. 438)
            </p>
          </div>
          <ArchivalStamp label="VECTOR NEIGHBORS" sublabel="TOP-5 FITTED" color="brass" rotate={-2} />
        </div>

        {/* Vector Space Representation Box */}
        <div className="bg-[#EFE4CF]/90 border border-[#D8C6A7] rounded p-3 mb-3 relative overflow-hidden shadow-inner">
          <p className="font-mono text-[9px] uppercase tracking-wider text-[#8C6F34] mb-1 font-semibold flex items-center justify-between">
            <span>HIGH-DIMENSIONAL CLUSTER:</span>
            <span className="text-[#8A2D3C]">FILTER: JAIL &lt; 7 YRS</span>
          </p>

          {/* Graphical constellation on parchment */}
          <div className="my-2 p-2 bg-[#FAF4E8] rounded border border-[#D5C2A4] flex items-center justify-around font-mono text-[8px] text-[#3D2C1B]">
            <div className="flex flex-col items-center">
              <span className="w-2.5 h-2.5 rounded-full bg-[#8C6F34] animate-ping opacity-60" />
              <span className="font-bold text-[#6D5422] mt-0.5">QUERY NODE</span>
            </div>
            <div className="h-px w-8 bg-[#8C6F34]/50 border-t border-dashed border-[#8C6F34]" />
            <div className="flex flex-col items-center">
              <span className="w-2 h-2 rounded-full bg-[#385E49]" />
              <span className="text-[#2A4837] mt-0.5">Shah (2022)</span>
            </div>
            <div className="h-px w-8 bg-[#8C6F34]/50 border-t border-dashed border-[#8C6F34]" />
            <div className="flex flex-col items-center">
              <span className="w-2 h-2 rounded-full bg-[#8A2D3C]" />
              <span className="text-[#6B202D] mt-0.5">Arnesh Kumar</span>
            </div>
          </div>

          <p className="font-legal text-xs text-[#2F241A] leading-relaxed italic">
            &ldquo;SEARCH: Filtered for offenses with jail terms below 7 years under Section 438. Cosine similarity neighbors locked.&rdquo;
          </p>
        </div>

        {/* Vector Specs */}
        <div className="space-y-1.5 text-[10px] font-sans">
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">Embedding Model:</span>
            <span className="font-mono font-medium text-[#2F241A]">BGE-M3 Legal Fine-Tuned</span>
          </div>
          <div className="flex justify-between py-1 border-b border-[#DECFA4]/60">
            <span className="text-[#7A6952]">Cosine Proximity:</span>
            <span className="font-mono text-[#385E49] font-bold">0.962 (Tight Cluster)</span>
          </div>
        </div>
      </div>

      {/* Footer Status */}
      <div className="pt-3 border-t border-[#D4C2A3] flex items-center justify-between mt-auto relative z-10">
        <span className="font-mono text-[9px] tracking-wider text-[#7A6952]">
          RETRIEVAL: VECTOR DENSE
        </span>
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm bg-[#8C6F34]/15 border border-[#8C6F34]/40 font-mono text-[9px] font-bold text-[#6D5422]">
          <GitBranch className="w-3 h-3 text-[#8C6F34]" />
          Fitted
        </span>
      </div>
    </div>
  );
}

/* ── Page 6: VERIFIED ANSWER (Final Decision Support - The Climax) ── */
function PageVerifiedAnswer() {
  return (
    <div className="h-full flex flex-col justify-between p-5 sm:p-7 select-none bg-gradient-to-br from-[#FAF5E8] via-[#F5EDD8] to-[#E9DBBE] relative worn-corner-right">
      <div className="absolute top-0 bottom-0 left-0 w-1.5 binding-stitches pointer-events-none z-20" />
      <AntiqueParchmentEffects side="right" stainType="tea-ring" />

      <div className="relative z-10">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-[#D4C2A3] pb-2.5 mb-3.5">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[9px] uppercase tracking-widest text-[#385E49] font-bold">
              Folio 06 • Final Verdict Synthesis
            </span>
          </div>
          <span className="font-mono text-[9px] text-[#385E49] font-bold tracking-widest">
            NODE 06/06
          </span>
        </div>

        {/* Title and Grand Seal */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#385E49]" strokeWidth={2} />
              <h3 className="font-display text-lg sm:text-xl font-bold text-[#1E3327] leading-none">
                Verified Answer
              </h3>
            </div>
            <p className="font-sans text-[11px] font-semibold text-[#385E49] mt-0.5">
              Final Decision Support Synthesis
            </p>
          </div>
          <ArchivalStamp label="100% GROUNDED" sublabel="VERIFIED VERDICT" color="green" rotate={1} />
        </div>

        {/* Grand Synthesized Judicial Answer Box */}
        <div className="bg-[#FAF4E8] border-2 border-[#385E49]/50 rounded p-3 mb-3 relative overflow-hidden shadow-md">
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-mono text-[9px] uppercase tracking-wider text-[#385E49] font-bold flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-[#8C6F34]" />
              SOURCE-GROUNDED RAG SYNTHESIS:
            </span>
            <span className="px-1.5 py-0.5 rounded bg-[#385E49]/15 text-[#213F2F] font-mono text-[8px] font-extrabold">
              4 CITED PARAGRAPHS
            </span>
          </div>
          <p className="font-legal text-xs sm:text-[13px] text-[#1E2E24] leading-relaxed font-medium">
            &ldquo;Anticipatory bail is maintainable. As governed by <span className="underline decoration-[#385E49] decoration-1 font-semibold">State of MH v. K. Shah</span> and <span className="underline decoration-[#385E49] decoration-1 font-semibold">Paragraph 14</span>, electronic signature discrepancies do not nullify pre-arrest protections for offenses punishable under 7 years.&rdquo;
          </p>
        </div>

        {/* Pipeline Completion Badges */}
        <div className="grid grid-cols-2 gap-2 text-[10px] font-sans">
          <div className="p-2 rounded bg-[#FAF4E8] border border-[#D5C2A4] flex items-center gap-2">
            <Award className="w-4 h-4 text-[#8C6F34] shrink-0" />
            <div>
              <div className="font-bold text-[#2A1E14] text-[10px]">Citation Fidelity</div>
              <div className="font-mono text-[9px] text-[#385E49] font-semibold">100% Verified</div>
            </div>
          </div>
          <div className="p-2 rounded bg-[#FAF4E8] border border-[#D5C2A4] flex items-center gap-2">
            <Scale className="w-4 h-4 text-[#385E49] shrink-0" />
            <div>
              <div className="font-bold text-[#2A1E14] text-[10px]">Decision Ready</div>
              <div className="font-mono text-[9px] text-[#8C6F34] font-semibold">Court Bench Ready</div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer Status */}
      <div className="pt-3 border-t border-[#385E49]/30 flex items-center justify-between mt-auto relative z-10">
        <span className="font-mono text-[9px] tracking-wider text-[#385E49] font-semibold">
          PIPELINE: VERIFIED COMPLETED
        </span>
        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#385E49] text-[#FAF5EA] font-mono text-[9.5px] font-extrabold tracking-wide shadow-sm">
          <CheckCircle2 className="w-3.5 h-3.5 text-[#FAF5EA]" />
          Verified
        </span>
      </div>
    </div>
  );
}

/* ── Main Scroll-Linked Realistic 3D Case Book Component ── */
export default function HeroFloatingCards() {
  const containerRef = useRef<HTMLDivElement>(null);
  const bookStageRef = useRef<HTMLDivElement>(null);

  // Track scroll through the section
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  // Smooth, low-lag spring interpolation for immediate, controllable scroll response
  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 260,
    damping: 32,
    mass: 0.2,
    restDelta: 0.001,
  });

  /* ──────────────────────────────────────────────────────────
     Full Lifecycle Scroll Stages (Open -> Turn -> Close & Return):
     0.00 -> 0.05 : 3D Tome Lands on Bench (Closed Front Cover)
     0.05 -> 0.20 : Front Cover Opens (rotateY: 0deg to -180deg)
     0.20 -> 0.35 : Spread 1 Reading Zone (Folio 01 + Folio 02)
     0.35 -> 0.50 : Leaf 1 Turns (Folio 02 flips to Folio 03)
     0.50 -> 0.65 : Spread 2 Reading Zone (Folio 03 + Folio 04)
     0.65 -> 0.80 : Leaf 2 Turns (Folio 04 flips to Folio 05)
     0.80 -> 0.88 : Spread 3 Reading Zone (Folio 05 + Folio 06 - Final Verdict)
     0.88 -> 0.95 : Closing Book Cover (rotateY: -180deg to 0deg, Seals Tome)
     0.95 -> 1.00 : Closed Book Returns to Starting Elevated Stance
     ────────────────────────────────────────────────────────── */

  // 3D Cinematic Fly-In & Return-to-Start Transforms
  // At entry: settles from [scale: 0.88, y: 50, rotateX: 12, rotateZ: -2.5] -> flat on bench [1, 0, 0, 0]
  // At exit: returns to the exact starting elevated flight position [scale: 0.88, y: 50, rotateX: 12, rotateZ: -2.5]
  const bookFlyScale = useTransform(smoothProgress, [0, 0.05, 0.94, 1], [0.88, 1, 1, 0.88]);
  const bookFlyY = useTransform(smoothProgress, [0, 0.05, 0.94, 1], [50, 0, 0, 50]);
  const bookFlyRotateX = useTransform(smoothProgress, [0, 0.05, 0.94, 1], [12, 0, 0, 12]);
  const bookFlyRotateZ = useTransform(smoothProgress, [0, 0.05, 0.94, 1], [-2.5, 0, 0, -2.5]);
  const bookShadowScale = useTransform(smoothProgress, [0, 0.05, 0.94, 1], [0.8, 1, 1, 0.8]);
  const bookShadowOpacity = useTransform(smoothProgress, [0, 0.05, 0.94, 1], [0.6, 1, 1, 0.6]);

  // Front Cover Opening Rotation (0.05 -> 0.20)
  const coverRotateY = useTransform(smoothProgress, [0.05, 0.20], [0, -180]);
  const coverZIndex = useTransform(smoothProgress, (v) => (v < 0.12 ? 60 : 5));
  const leftCoverFade = useTransform(smoothProgress, [0.04, 0.15], [1, 0]);
  const promptOpacity = useTransform(smoothProgress, [0, 0.05], [1, 0]);

  // Turn Leaf 1 (0.35 -> 0.50)
  const leaf1RotateY = useTransform(smoothProgress, [0.35, 0.50], [0, -180]);
  const leaf1ZIndex = useTransform(smoothProgress, (v) => (v < 0.42 ? 40 : 25));

  // Turn Leaf 2 (0.65 -> 0.80)
  const leaf2RotateY = useTransform(smoothProgress, [0.65, 0.80], [0, -180]);
  const leaf2ZIndex = useTransform(smoothProgress, (v) => (v < 0.72 ? 35 : 30));

  // Closing Cover at the end of the evidence pipeline (0.88 -> 0.95: swings -180deg to 0deg to close book shut)
  const closeCoverRotateY = useTransform(smoothProgress, [0.88, 0.95], [-180, 0]);
  const closeCoverZIndex = useTransform(smoothProgress, (v) => (v < 0.91 ? 15 : 75));
  const closeCoverOpacity = useTransform(smoothProgress, [0.86, 0.88], [0, 1]);

  // Hide left-turned pages (Semantic Query, Verity Citation) when closing so nothing is left behind
  const leftTurnedLeavesOpacity = useTransform(smoothProgress, [0.87, 0.92], [1, 0]);

  // Left side conceal & scale for one-sided closed book
  const leftHalfOpacity = useTransform(smoothProgress, [0.88, 0.94], [1, 0]);
  const leftHalfScaleX = useTransform(smoothProgress, [0.88, 0.94], [1, 0]);

  // Book Centering: when closed at the end, center the single volume
  const bookCenterX = useTransform(
    smoothProgress,
    [0, 0.88, 0.94, 1],
    ['0%', '0%', '-25%', '-25%']
  );

  // Active spread tracking for dynamic indicator update
  const [activeSpread, setActiveSpread] = useState(0);

  useEffect(() => {
    const unsub = smoothProgress.on('change', (v) => {
      if (v < 0.12) setActiveSpread(0); // Cover Closed Start
      else if (v < 0.42) setActiveSpread(1); // Spread 1
      else if (v < 0.72) setActiveSpread(2); // Spread 2
      else if (v < 0.88) setActiveSpread(3); // Spread 3
      else setActiveSpread(4); // Closed & Sealed Final
    });
    return () => unsub();
  }, [smoothProgress]);

  // Scroll to spread helper for easy direct jumping
  const scrollToSpread = (targetIndex: number) => {
    if (!containerRef.current) return;
    const containerTop = containerRef.current.offsetTop;
    const containerHeight = containerRef.current.scrollHeight - window.innerHeight;
    const targetMap = [0.02, 0.28, 0.58, 0.84, 0.99];
    const targetScrollY = containerTop + containerHeight * targetMap[targetIndex];
    window.scrollTo({ top: targetScrollY, behavior: 'smooth' });
  };

  const spreadData = [
    {
      badge: 'CASE LEDGER • BENCH COPY',
      title: 'Supreme Court Archives • Official Case File',
      desc: 'Scroll down to open the antique judicial case book and begin the evidence stack inspection',
    },
    {
      badge: 'FOLIOS I & II',
      title: 'Evidence Intake & Precedent Matching',
      desc: 'Lossless OCR extraction parsed against 12,400+ BM25 precedent rulings',
    },
    {
      badge: 'FOLIOS III & IV',
      title: 'Statutory Verification & Context Extraction',
      desc: 'Strict IPC ⇄ BNS alignment trace with named entity recognition chunking',
    },
    {
      badge: 'FOLIOS V & VI',
      title: 'Dense Vector Search & Verified Verdict',
      desc: 'Multi-vector cosine neighbors synthesized into source-grounded decision support',
    },
    {
      badge: 'CASE FILE ARCHIVED & SEALED',
      title: 'Final Verdict Delivered • Official Ledger Closed',
      desc: 'Evidence pipeline completed with 100% citation fidelity. Case file sealed into court archives.',
    },
  ];

  return (
    <section
      ref={containerRef}
      id="evidence-book-section"
      className="relative h-[420vh] bg-[#121413] text-ivory select-none"
    >
      {/* Pinned 3D Viewport — smooth scroll translates into 3D page turns */}
      <div className="sticky top-0 h-screen w-full flex flex-col justify-between items-center overflow-hidden px-4 py-6 md:py-8">
        
        {/* Subtle Atmospheric Vignette */}
        <div className="pointer-events-none absolute inset-0 bg-radial-gradient from-transparent via-[#121413]/60 to-[#0A0C0B]" />
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#B59A68]/20 to-transparent" />

        {/* Section Header */}
        <div className="relative mx-auto max-w-4xl text-center z-10 shrink-0">
          <div className="mb-1.5 flex justify-center">
            <span className="section-label">
              <Scale className="h-3 w-3 text-[#B59A68]" strokeWidth={1.5} />
              Judicial Evidence Ledger &amp; Decision Pipeline
            </span>
          </div>

          <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold leading-tight text-ivory">
            Visualizing the Evidence Stack
          </h2>
          <p className="mx-auto mt-1 max-w-xl font-sans text-xs sm:text-sm text-stone leading-relaxed">
            Scroll down to open the antique case file and trace how raw exhibits, precedents, and statutes synthesize into a verified verdict.
          </p>

          {/* Active Folio Pill Indicator with Jump Controls */}
          <div className="mt-2.5 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#181B1A]/85 border border-[#B59A68]/40 backdrop-blur-sm shadow-sm">
            <BookOpen className="w-3 h-3 text-[#B59A68]" />
            <span className="font-mono text-[10.5px] font-bold text-[#B59A68] tracking-wider">
              {spreadData[activeSpread].badge}
            </span>
            <span className="text-stone/40">•</span>
            <span className="font-sans text-[11px] text-ivory/90 font-medium hidden sm:inline">
              {spreadData[activeSpread].title}
            </span>

            {/* Subtle Folio Stage Jump Dots */}
            <div className="ml-1.5 flex items-center gap-1.5 pl-1.5 border-l border-[#3B3A33]">
              {spreadData.map((_, i) => (
                <button
                  key={i}
                  onClick={() => scrollToSpread(i)}
                  title={`Jump to ${spreadData[i].badge}`}
                  className={`w-2 h-2 rounded-full transition-all duration-200 ${
                    activeSpread === i
                      ? 'bg-[#B59A68] scale-125'
                      : 'bg-stone/30 hover:bg-[#B59A68]/60'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Scroll Instruction Hint (Fades as book opens) */}
        <motion.div
          style={{ opacity: promptOpacity }}
          className="absolute top-[28%] z-30 pointer-events-none flex flex-col items-center gap-1"
        >
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#1D211F]/90 border border-[#B59A68]/40 text-[#B59A68] text-xs font-mono tracking-widest shadow-xl backdrop-blur-sm animate-pulse">
            <span>Scroll to open the case book</span>
            <ChevronDown className="w-3.5 h-3.5" />
          </div>
        </motion.div>

        {/* ── 3D REALISTIC TOME STAGE ── */}
        <div
          ref={bookStageRef}
          className="relative w-full flex items-center justify-center my-auto z-20 perspective-book"
        >
          {/* 3D Cinematic Fly-In Container */}
          <motion.div
            style={{
              scale: bookFlyScale,
              y: bookFlyY,
              rotateX: bookFlyRotateX,
              rotateZ: bookFlyRotateZ,
            }}
            className="relative w-full max-w-[940px] preserve-3d flex items-center justify-center"
          >
            {/* Ambient Heavy Drop Shadow under the physical book */}
            <motion.div
              style={{
                scale: bookShadowScale,
                opacity: bookShadowOpacity,
              }}
              className="absolute -inset-x-8 -bottom-10 h-16 rounded-full bg-black/95 blur-2xl pointer-events-none"
            />

            {/* Book Body Container with Dynamic Centering for One-Sided Closed Book */}
            <motion.div
              style={{ x: bookCenterX }}
              className="relative w-full preserve-3d flex items-center justify-center"
            >
              {/* ── HARDCOVER LEATHER BACK CASING (Overhanging with Brass Corners) ── */}
              <div className="relative w-[340px] sm:w-[580px] md:w-[780px] lg:w-[940px] h-[480px] sm:h-[500px] md:h-[530px] p-2.5 sm:p-3 md:p-3.5 book-hardcover-case book-shadow-ambient preserve-3d flex items-stretch">
                
                {/* Ornamental Brass Corner Protectors on Hardcover */}
                <div className="absolute top-1 left-1 w-6 h-6 border-t-2 border-l-2 border-[#B59A68] rounded-tl-sm pointer-events-none opacity-85" />
                <div className="absolute top-1 right-1 w-6 h-6 border-t-2 border-r-2 border-[#B59A68] rounded-tr-sm pointer-events-none opacity-85" />
                <div className="absolute bottom-1 left-1 w-6 h-6 border-b-2 border-l-2 border-[#B59A68] rounded-bl-sm pointer-events-none opacity-85" />
                <div className="absolute bottom-1 right-1 w-6 h-6 border-b-2 border-r-2 border-[#B59A68] rounded-br-sm pointer-events-none opacity-85" />

                {/* Antique Gold Tooling Inlay Border */}
                <div className="absolute inset-2 border border-[#B59A68]/35 rounded pointer-events-none" />

                {/* ── OPEN PARCHMENT BOOK BLOCK (Stacked Paper Edges) ── */}
                <div className="relative w-full h-full flex rounded-sm overflow-visible preserve-3d book-edge-stack-top book-edge-stack-bottom">
                  
                  {/* ═══════════════════════════════════════════════════════
                      LEFT BOOK HALF (Permanent Base: Folio 01 — Exhibit Intake)
                      ═══════════════════════════════════════════════════════ */}
                  <motion.div
                    style={{
                      opacity: leftHalfOpacity,
                      scaleX: leftHalfScaleX,
                      transformOrigin: 'right center',
                    }}
                    className="relative w-1/2 h-full parchment-sheet book-edge-stack-left rounded-l-sm overflow-hidden border-y border-l border-[#D2C0A0] shadow-md z-10"
                  >
                    <PageEvidenceIngestion />
                    {/* Natural concave page curve into spine */}
                    <div className="pointer-events-none absolute inset-0 page-curve-left" />

                    {/* Closed State Left Leather Cover (Fades smoothly out as book opens) */}
                    <motion.div
                      style={{ opacity: leftCoverFade }}
                      className="absolute inset-0 book-cover-leather rounded-l-sm overflow-hidden p-6 flex flex-col justify-between border-y border-l border-[#4A2D1B] shadow-2xl pointer-events-none z-20"
                    >
                      <div className="absolute inset-3.5 border-2 border-[#B59A68]/40 rounded pointer-events-none" />
                      <div className="absolute inset-5 border border-[#B59A68]/20 rounded pointer-events-none" />
                      <div className="flex flex-col items-center justify-center h-full text-center">
                        <span className="font-mono text-[8px] uppercase tracking-[0.25em] text-[#B59A68]/60 mb-2">
                          OFFICIAL JURISPRUDENCE ARCHIVE
                        </span>
                        <div className="w-10 h-px bg-[#B59A68]/40 mb-2" />
                        <p className="font-mono text-[9px] tracking-widest text-[#B59A68]/80">
                          VOLUME IX • BENCH COPY
                        </p>
                      </div>
                    </motion.div>
                  </motion.div>

                  {/* ═══════════════════════════════════════════════════════
                      RIGHT BOOK HALF (Permanent Base: Folio 06 — Final Verdict)
                      ═══════════════════════════════════════════════════════ */}
                  <div className="relative w-1/2 h-full parchment-sheet book-edge-stack-right rounded-r-sm overflow-hidden border-y border-r border-[#D2C0A0] shadow-md z-10">
                    <PageVerifiedAnswer />
                    {/* Natural concave page curve into spine */}
                    <div className="pointer-events-none absolute inset-0 page-curve-right" />
                  </div>

                  {/* ═══════════════════════════════════════════════════════
                      3D TURNING LEAF 2 (Turns Folio 04 onto Folio 05)
                      ═══════════════════════════════════════════════════════ */}
                  <motion.div
                    style={{
                      rotateY: leaf2RotateY,
                      transformOrigin: 'left center',
                      zIndex: leaf2ZIndex,
                    }}
                    className="absolute left-1/2 top-0 w-1/2 h-full preserve-3d"
                  >
                    {/* Front Face: Folio 04 (Chunk Extraction) */}
                    <div className="absolute inset-0 parchment-sheet book-edge-stack-right rounded-r-sm overflow-hidden border-y border-r border-[#D2C0A0] backface-hidden shadow-lg">
                      <PageChunkExtraction />
                      <div className="pointer-events-none absolute inset-0 page-curve-right" />
                    </div>

                    {/* Back Face: Folio 05 (Semantic Query - Fades cleanly on closing) */}
                    <motion.div
                      style={{
                        transform: 'rotateY(180deg)',
                        opacity: leftTurnedLeavesOpacity,
                      }}
                      className="absolute inset-0 parchment-sheet book-edge-stack-left rounded-l-sm overflow-hidden border-y border-l border-[#D2C0A0] backface-hidden shadow-lg"
                    >
                      <PageSemanticQuery />
                      <div className="pointer-events-none absolute inset-0 page-curve-left" />
                    </motion.div>
                  </motion.div>

                  {/* ═══════════════════════════════════════════════════════
                      3D TURNING LEAF 1 (Turns Folio 02 onto Folio 03)
                      ═══════════════════════════════════════════════════════ */}
                  <motion.div
                    style={{
                      rotateY: leaf1RotateY,
                      transformOrigin: 'left center',
                      zIndex: leaf1ZIndex,
                    }}
                    className="absolute left-1/2 top-0 w-1/2 h-full preserve-3d"
                  >
                    {/* Front Face: Folio 02 (Precedent Match) */}
                    <div className="absolute inset-0 parchment-sheet book-edge-stack-right rounded-r-sm overflow-hidden border-y border-r border-[#D2C0A0] backface-hidden shadow-lg">
                      <PagePrecedentMatch />
                      <div className="pointer-events-none absolute inset-0 page-curve-right" />
                    </div>

                    {/* Back Face: Folio 03 (Verity Citation - Fades cleanly on closing) */}
                    <motion.div
                      style={{
                        transform: 'rotateY(180deg)',
                        opacity: leftTurnedLeavesOpacity,
                      }}
                      className="absolute inset-0 parchment-sheet book-edge-stack-left rounded-l-sm overflow-hidden border-y border-l border-[#D2C0A0] backface-hidden shadow-lg"
                    >
                      <PageVerityCitation />
                      <div className="pointer-events-none absolute inset-0 page-curve-left" />
                    </motion.div>
                  </motion.div>

                  {/* ═══════════════════════════════════════════════════════
                      3D FRONT COVER (Swings open from center over to the left)
                      ═══════════════════════════════════════════════════════ */}
                  <motion.div
                    style={{
                      rotateY: coverRotateY,
                      transformOrigin: 'left center',
                      zIndex: coverZIndex,
                    }}
                    className="absolute left-1/2 top-0 w-1/2 h-full preserve-3d pointer-events-none"
                  >
                    {/* Front Cover Exterior: Antique Leather with Gold Tooling */}
                    <div className="absolute inset-0 book-cover-leather rounded-r-sm overflow-hidden p-6 md:p-8 flex flex-col justify-between backface-hidden shadow-2xl border-y border-r border-[#4A2D1B]">
                      {/* Antique Gold Filigree Border */}
                      <div className="absolute inset-3.5 border-2 border-[#B59A68]/50 rounded pointer-events-none" />
                      <div className="absolute inset-5 border border-[#B59A68]/30 rounded pointer-events-none" />

                      {/* Brass Corner Reinforcements */}
                      <div className="absolute top-4 left-4 w-4 h-4 border-t-2 border-l-2 border-[#B59A68]" />
                      <div className="absolute top-4 right-4 w-4 h-4 border-t-2 border-r-2 border-[#B59A68]" />
                      <div className="absolute bottom-4 left-4 w-4 h-4 border-b-2 border-l-2 border-[#B59A68]" />
                      <div className="absolute bottom-4 right-4 w-4 h-4 border-b-2 border-r-2 border-[#B59A68]" />

                      {/* Cover Header */}
                      <div className="relative text-center pt-2">
                        <span className="font-mono text-[9px] uppercase tracking-[0.25em] text-[#B59A68]/80 block">
                          SUPREME COURT ARCHIVES • BENCH COPY
                        </span>
                      </div>

                      {/* Cover Center Emblem & Title */}
                      <div className="relative flex flex-col items-center text-center my-auto">
                        {/* NyayaSarathi Scales of Justice Logo */}
                        <div className="w-16 h-16 rounded-full bg-[#180E08] border border-[#B59A68]/60 flex items-center justify-center mb-4 shadow-inner">
                          <Scale className="w-9 h-9 text-[#B59A68]" strokeWidth={1.4} />
                        </div>

                        <h3 className="font-display text-2xl sm:text-3xl md:text-4xl font-bold tracking-[0.08em] text-[#EAD8B8] drop-shadow-md">
                          NYAYASARATHI
                        </h3>

                        <div className="flex items-center gap-3 my-2.5">
                          <div className="w-8 h-px bg-gradient-to-r from-transparent to-[#B59A68]" />
                          <span className="font-mono text-[9px] tracking-widest text-[#B59A68]">◆</span>
                          <div className="w-8 h-px bg-gradient-to-l from-transparent to-[#B59A68]" />
                        </div>

                        <p className="font-mono text-[10px] sm:text-[11px] uppercase tracking-[0.2em] text-[#C9B38B] font-semibold">
                          INTELLIGENCE &amp; EVIDENCE
                        </p>
                        <p className="font-mono text-[9px] uppercase tracking-[0.25em] text-[#8A7558] mt-0.5">
                          CASE FILE NO. 2026/IN-DL
                        </p>
                      </div>

                      {/* Cover Footer */}
                      <div className="relative text-center pb-1">
                        <p className="font-legal italic text-xs text-[#A99477]/80">
                          &ldquo;Fiat justitia ruat caelum&rdquo;
                        </p>
                        <span className="font-mono text-[8px] uppercase tracking-widest text-[#7A674D] block mt-1">
                          VERIFIABLE CITATION PIPELINE
                        </span>
                      </div>
                    </div>

                    {/* Back Face of Cover (Swung open onto the left, hidden under the page stack) */}
                    <div
                      style={{ transform: 'rotateY(180deg)' }}
                      className="absolute inset-0 bg-[#1A0F0A] rounded-l-sm backface-hidden p-6 border-y border-l border-[#3D2516] shadow-2xl"
                    />
                  </motion.div>

                  {/* ═══════════════════════════════════════════════════════
                      3D CLOSING BACK COVER (Swings closed from left to right at end)
                      ═══════════════════════════════════════════════════════ */}
                  <motion.div
                    style={{
                      rotateY: closeCoverRotateY,
                      transformOrigin: 'left center',
                      zIndex: closeCoverZIndex,
                      opacity: closeCoverOpacity,
                    }}
                    className="absolute left-1/2 top-0 w-1/2 h-full preserve-3d pointer-events-none"
                  >
                    {/* Front Face: Closed Leather Seal (Shown when book is closed shut at end) */}
                    <div className="absolute inset-0 book-cover-leather rounded-r-sm overflow-hidden p-6 md:p-8 flex flex-col justify-between backface-hidden shadow-2xl border-y border-r border-[#4A2D1B]">
                      {/* Antique Gold Filigree Border */}
                      <div className="absolute inset-3.5 border-2 border-[#B59A68]/50 rounded pointer-events-none" />
                      <div className="absolute inset-5 border border-[#B59A68]/30 rounded pointer-events-none" />

                      {/* Brass Corner Reinforcements */}
                      <div className="absolute top-4 left-4 w-4 h-4 border-t-2 border-l-2 border-[#B59A68]" />
                      <div className="absolute top-4 right-4 w-4 h-4 border-t-2 border-r-2 border-[#B59A68]" />
                      <div className="absolute bottom-4 left-4 w-4 h-4 border-b-2 border-l-2 border-[#B59A68]" />
                      <div className="absolute bottom-4 right-4 w-4 h-4 border-b-2 border-r-2 border-[#B59A68]" />

                      {/* Cover Header */}
                      <div className="relative text-center pt-2">
                        <span className="font-mono text-[9px] uppercase tracking-[0.25em] text-[#385E49] font-bold block">
                          CASE FILE VERIFIED &amp; SEALED
                        </span>
                      </div>

                      {/* Center Archival Grand Seal */}
                      <div className="relative flex flex-col items-center text-center my-auto">
                        <div className="w-16 h-16 rounded-full bg-[#180E08] border-2 border-[#385E49] flex items-center justify-center mb-3 shadow-inner">
                          <CheckCircle2 className="w-9 h-9 text-[#385E49]" strokeWidth={2} />
                        </div>

                        <h3 className="font-display text-xl sm:text-2xl md:text-3xl font-bold tracking-[0.08em] text-[#EAD8B8]">
                          DECISION RECORDED
                        </h3>

                        <div className="flex items-center gap-3 my-2">
                          <div className="w-8 h-px bg-gradient-to-r from-transparent to-[#385E49]" />
                          <span className="font-mono text-[9px] text-[#385E49]">✓</span>
                          <div className="w-8 h-px bg-gradient-to-l from-transparent to-[#385E49]" />
                        </div>

                        <p className="font-mono text-[9.5px] uppercase tracking-[0.2em] text-[#B59A68] font-semibold">
                          100% GROUND TRUTH VERIFIED
                        </p>
                        <p className="font-mono text-[8.5px] uppercase tracking-[0.25em] text-[#8A7558] mt-0.5">
                          OFFICIAL JUDICIAL DISPOSITION
                        </p>
                      </div>

                      {/* Cover Footer */}
                      <div className="relative text-center pb-1">
                        <p className="font-legal italic text-xs text-[#A99477]/80">
                          &ldquo;Fiat justitia ruat caelum&rdquo;
                        </p>
                        <span className="font-mono text-[8px] uppercase tracking-widest text-[#7A674D] block mt-1">
                          ARCHIVE RECORD COMPLETE
                        </span>
                      </div>
                    </div>

                    {/* Back Face of Closing Cover */}
                    <div
                      style={{ transform: 'rotateY(180deg)' }}
                      className="absolute inset-0 bg-[#1A0F0A] rounded-l-sm backface-hidden p-6 border-y border-l border-[#3D2516] shadow-2xl"
                    />
                  </motion.div>

                  {/* ═══════════════════════════════════════════════════════
                      REALISTIC 3D CENTER LEATHER SPINE & STITCHED RIBS
                      ═══════════════════════════════════════════════════════ */}
                  <div className="absolute left-1/2 top-0 bottom-0 w-[14px] -ml-[7px] bg-gradient-to-r from-[#1F120A] via-[#3E2416] to-[#1F120A] z-40 pointer-events-none shadow-2xl flex flex-col justify-around py-3">
                    {/* Top Archival Headband */}
                    <div className="absolute top-0 inset-x-0 h-1 bg-[#8C6F34] shadow-sm" />
                    
                    {/* 4 Stitched Leather Ribs (Raised Bands) */}
                    <div className="h-1.5 w-full bg-[#180C07] border-y border-[#B59A68]/40 spine-ridge rounded-sm" />
                    <div className="h-1.5 w-full bg-[#180C07] border-y border-[#B59A68]/40 spine-ridge rounded-sm" />
                    <div className="h-1.5 w-full bg-[#180C07] border-y border-[#B59A68]/40 spine-ridge rounded-sm" />
                    <div className="h-1.5 w-full bg-[#180C07] border-y border-[#B59A68]/40 spine-ridge rounded-sm" />

                    {/* Bottom Archival Headband */}
                    <div className="absolute bottom-0 inset-x-0 h-1 bg-[#8C6F34] shadow-sm" />
                  </div>

                  {/* ═══════════════════════════════════════════════════════
                      REALISTIC SATIN BOOKMARK RIBBON (Trailing out bottom)
                      ═══════════════════════════════════════════════════════ */}
                  <div className="absolute left-1/2 top-0 w-[10px] -ml-[5px] h-[calc(100%+32px)] ribbon-bookmark z-50 pointer-events-none rounded-t-sm" />
                </div>
              </div>
            </motion.div>
          </motion.div>
        </div>

        {/* Bottom Micro Description */}
        <div className="relative z-10 text-center pb-2 shrink-0 max-w-lg">
          <p className="font-sans text-[11px] text-stone/60">
            {spreadData[activeSpread].desc}
          </p>
        </div>
      </div>
    </section>
  );
}
