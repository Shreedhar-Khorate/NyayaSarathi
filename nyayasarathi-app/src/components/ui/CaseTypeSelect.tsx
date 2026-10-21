'use client';

import React, { useState, useRef, useEffect, useId } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown,
  Check,
  Search,
  Scale,
  ShieldAlert,
  Landmark,
  Building2,
  ScrollText,
  Briefcase,
  SlidersHorizontal,
  X
} from 'lucide-react';

export interface CaseSubOption {
  value: string;
  label: string;
  statuteTag?: string;
}

export interface CaseCategoryGroup {
  id: string;
  label: string;
  icon: React.ReactNode;
  iconEmoji: string;
  description: string;
  options: CaseSubOption[];
}

export const CASE_CATEGORY_GROUPS: CaseCategoryGroup[] = [
  {
    id: 'bail',
    label: 'Bail & Personal Liberty Matters',
    iconEmoji: '⚖️',
    icon: <Scale className="w-4 h-4 text-[#B59A68]" />,
    description: 'Pre-trial release, anticipatory protection, and quashing petitions',
    options: [
      { value: 'Bail', label: 'Regular Bail', statuteTag: 'CrPC 437/439 · BNSS 479/483' },
      { value: 'Anticipatory Bail', label: 'Anticipatory Bail', statuteTag: 'CrPC 438 · BNSS 484' },
      { value: 'Interim Bail', label: 'Interim Bail / Extension of Bail', statuteTag: 'Interim Relief' },
      { value: 'Bail Cancellation', label: 'Cancellation of Bail Application', statuteTag: 'CrPC 439(2)' },
      { value: 'Quashing of FIR', label: 'Quashing of FIR / Proceedings', statuteTag: 'CrPC 482 · BNSS 528' },
      { value: 'Discharge Application', label: 'Discharge Application', statuteTag: 'CrPC 227/239/245' },
    ],
  },
  {
    id: 'criminal',
    label: 'Criminal Law & Statutory Offenses',
    iconEmoji: '🚨',
    icon: <ShieldAlert className="w-4 h-4 text-[#8A3545]" />,
    description: 'Statutory offenses, special acts, trials, and appellate revisions',
    options: [
      { value: 'Criminal Appeal', label: 'Criminal Appeal', statuteTag: 'Against Conviction / Acquittal' },
      { value: 'Criminal Revision', label: 'Criminal Revision Petition', statuteTag: 'CrPC 397/401' },
      { value: 'SLP Criminal', label: 'Special Leave Petition - Criminal', statuteTag: 'Art 136 · SLP Crl' },
      { value: 'PMLA Offense', label: 'PMLA / Money Laundering', statuteTag: 'ED · Sec 45 PMLA' },
      { value: 'NDPS Act', label: 'NDPS Act Offense', statuteTag: 'Sec 37 NDPS Strict Bail' },
      { value: 'POCSO Act', label: 'POCSO Act Offense', statuteTag: 'Protection of Children' },
      { value: 'Prevention of Corruption', label: 'Prevention of Corruption Act', statuteTag: 'CBI / Anti-Corruption' },
      { value: 'Cheque Bounce NI 138', label: 'Cheque Bounce / Dishonour', statuteTag: 'NI Act Sec 138' },
      { value: 'Cyber Crime IT Act', label: 'Cyber Crime & IT Act Offenses', statuteTag: 'IT Act 2000' },
      { value: 'UAPA Offense', label: 'UAPA / Anti-Terrorism Matters', statuteTag: 'Sec 43D(5) UAPA' },
      { value: 'Economic Offenses', label: 'Economic Offenses & Fraud', statuteTag: 'IPC 420/406/467 · BNS' },
    ],
  },
  {
    id: 'civil',
    label: 'Civil Law & Property Disputes',
    iconEmoji: '🏛️',
    icon: <Landmark className="w-4 h-4 text-[#71877A]" />,
    description: 'Title disputes, appeals, injunctions, and possession matters',
    options: [
      { value: 'Civil Original Suit', label: 'Civil Original Suit', statuteTag: 'Recovery / Specific Performance' },
      { value: 'Regular First Appeal', label: 'Regular First Appeal (RFA)', statuteTag: 'CPC Sec 96' },
      { value: 'Regular Second Appeal', label: 'Regular Second Appeal (RSA)', statuteTag: 'CPC Sec 100' },
      { value: 'Civil Revision', label: 'Civil Revision Petition (CRP)', statuteTag: 'CPC Sec 115' },
      { value: 'Property Partition Title', label: 'Property Title, Partition & Possession', statuteTag: 'Partition Act · TPA' },
      { value: 'Land Acquisition Appeal', label: 'Land Acquisition & Compensation', statuteTag: 'RFCTLARR Act' },
      { value: 'RERA Real Estate', label: 'RERA Regulatory Appeal', statuteTag: 'RERA Act 2016' },
      { value: 'Injunction Suit', label: 'Injunction Suit (Temp / Permanent)', statuteTag: 'Order 39 CPC' },
      { value: 'Rent Eviction Suit', label: 'Rent Control & Eviction Matters', statuteTag: 'Rent Control Act' },
    ],
  },
  {
    id: 'commercial',
    label: 'Commercial & Financial Law',
    iconEmoji: '🏢',
    icon: <Building2 className="w-4 h-4 text-[#B59A68]" />,
    description: 'Commercial disputes, contracts, debt recovery, and company law',
    options: [
      { value: 'Commercial Suit', label: 'Commercial Suit', statuteTag: 'Commercial Courts Act 2015' },
      { value: 'Breach of Contract', label: 'Breach of Contract & Damages', statuteTag: 'Indian Contract Act' },
      { value: 'Insolvency IBC NCLT', label: 'Insolvency & Bankruptcy (IBC)', statuteTag: 'NCLT · Sec 7/9 IBC' },
      { value: 'DRT Debt Recovery', label: 'Debt Recovery & SARFAESI', statuteTag: 'DRT / DRAT' },
      { value: 'NCLAT Company Law', label: 'Corporate & Companies Act', statuteTag: 'NCLAT Appeal' },
      { value: 'Consumer Protection', label: 'Consumer Protection Forum', statuteTag: 'CPA 2019 · NCDRC' },
    ],
  },
  {
    id: 'constitutional',
    label: 'Constitutional & Writ Jurisdiction',
    iconEmoji: '📜',
    icon: <ScrollText className="w-4 h-4 text-[#B59A68]" />,
    description: 'High Court & Supreme Court extraordinary writ remedies',
    options: [
      { value: 'Writ Habeas Corpus', label: 'Writ Petition - Habeas Corpus', statuteTag: 'Art 226 / 32' },
      { value: 'Writ Mandamus', label: 'Writ Petition - Mandamus', statuteTag: 'Art 226 / 32' },
      { value: 'Writ Certiorari', label: 'Writ Petition - Certiorari / Prohibition', statuteTag: 'Art 226 / 32' },
      { value: 'Public Interest Litigation', label: 'Public Interest Litigation (PIL)', statuteTag: 'Art 226 / 32' },
      { value: 'SLP Civil', label: 'Special Leave Petition - Civil', statuteTag: 'Art 136 · Supreme Court' },
      { value: 'Contempt of Court', label: 'Contempt of Court Petition', statuteTag: 'Contempt of Courts Act' },
    ],
  },
  {
    id: 'tribunals',
    label: 'Special Tribunals, Arbitration & Family',
    iconEmoji: '💼',
    icon: <Briefcase className="w-4 h-4 text-[#71877A]" />,
    description: 'Arbitration awards, family disputes, labor, taxation, and motor accidents',
    options: [
      { value: 'Arbitration Interim Sec 9', label: 'Arbitration Interim Relief', statuteTag: 'Sec 9 Arb Act' },
      { value: 'Arbitration Sec 34 Setting Aside', label: 'Arbitration Award Challenge', statuteTag: 'Sec 34 Arb Act' },
      { value: 'Intellectual Property IP', label: 'Intellectual Property Dispute', statuteTag: 'Patent / Trademark / IP' },
      { value: 'Matrimonial Divorce Custody', label: 'Matrimonial, Divorce & Custody', statuteTag: 'HMA / Family Court' },
      { value: 'Domestic Violence DV Act', label: 'Domestic Violence Matter', statuteTag: 'DV Act 2005' },
      { value: 'Labor Industrial Dispute', label: 'Labor & Industrial Disputes', statuteTag: 'Industrial Disputes Act' },
      { value: 'MACT Motor Accident', label: 'Motor Accident Claims (MACT)', statuteTag: 'Motor Vehicles Act' },
      { value: 'Taxation GST Income Tax', label: 'Taxation Appeals', statuteTag: 'ITAT / GST / Customs' },
      { value: 'Custom', label: 'Custom / Other Filing Type...', statuteTag: 'Custom Input' },
    ],
  },
];

export const ALL_KNOWN_CASE_TYPES = CASE_CATEGORY_GROUPS.flatMap((g) =>
  g.options.map((o) => o.value)
);

interface CaseTypeSelectProps {
  value: string;
  onChange: (val: string) => void;
  required?: boolean;
}

export function CaseTypeSelect({ value, onChange, required }: CaseTypeSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const selectId = useId();

  // Find currently selected option information
  const selectedInfo = React.useMemo(() => {
    for (const group of CASE_CATEGORY_GROUPS) {
      const match = group.options.find((opt) => opt.value === value);
      if (match) {
        return {
          group,
          option: match,
          isCustom: false,
        };
      }
    }
    // If not matched directly but has value
    if (value && value.trim()) {
      return {
        group: null,
        option: { value, label: value, statuteTag: 'Custom Filing' },
        isCustom: true,
      };
    }
    // Default fallback to first option
    return {
      group: CASE_CATEGORY_GROUPS[0],
      option: CASE_CATEGORY_GROUPS[0].options[0],
      isCustom: false,
    };
  }, [value]);

  // Handle outside clicks to close dropdown
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when opening
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 50);
    } else {
      setSearchQuery('');
    }
  }, [isOpen]);

  // Filter groups and options based on search query and category filter
  const filteredGroups = React.useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    return CASE_CATEGORY_GROUPS.map((group) => {
      // Check category tab filter
      if (activeCategory !== 'all' && group.id !== activeCategory) {
        return null;
      }

      if (!q) {
        return group;
      }

      const matchingOptions = group.options.filter(
        (opt) =>
          opt.label.toLowerCase().includes(q) ||
          opt.value.toLowerCase().includes(q) ||
          (opt.statuteTag && opt.statuteTag.toLowerCase().includes(q))
      );

      // If group label matches, show all its options, otherwise only matching options
      const groupMatches = group.label.toLowerCase().includes(q);
      if (groupMatches) {
        return group;
      }

      if (matchingOptions.length > 0) {
        return {
          ...group,
          options: matchingOptions,
        };
      }

      return null;
    }).filter(Boolean) as CaseCategoryGroup[];
  }, [searchQuery, activeCategory]);

  return (
    <div ref={containerRef} className="relative w-full">
      {/* Hidden input for HTML form validation compatibility */}
      <input
        type="text"
        id={selectId}
        value={value}
        onChange={() => { }}
        required={required}
        className="sr-only"
        tabIndex={-1}
        aria-hidden="true"
      />

      {/* Main Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full text-left rounded-lg bg-[#151716] border px-3.5 py-2.5 text-sm transition-all flex items-center justify-between gap-3 group ${isOpen
          ? 'border-[#B59A68] ring-1 ring-[#B59A68]/30 shadow-lg shadow-black/40'
          : 'border-[#3B3A33] hover:border-[#B59A68]/60 hover:bg-[#1D211F]/70'
          }`}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          {/* Main Section Icon Tag */}
          <span className="flex items-center justify-center w-6 h-6 rounded bg-[#242925] border border-[#3B3A33] text-xs shrink-0 shadow-inner">
            {selectedInfo.group ? selectedInfo.group.iconEmoji : '⚖️'}
          </span>

          <div className="flex flex-col min-w-0">
            {/* Main Section Label Indicator */}
            {selectedInfo.group && (
              <span className="text-[10px] font-semibold tracking-wider text-[#B59A68] uppercase truncate flex items-center gap-1">
                <span>{selectedInfo.group.label}</span>
                <span className="text-stone/40">›</span>
              </span>
            )}

            {/* Sub Section (Selected Item) */}
            <div className="flex items-center gap-2 truncate">
              <span className="text-sm font-medium text-[#F4EFE5] truncate">
                {selectedInfo.option.label}
              </span>
              {selectedInfo.option.statuteTag && (
                <span className="hidden sm:inline-block text-[10px] px-1.5 py-0.5 rounded bg-[#242925] border border-[#3B3A33] text-stone/80 shrink-0 font-mono">
                  {selectedInfo.option.statuteTag}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Dropdown Chevron */}
        <div className="flex items-center gap-1 shrink-0 text-stone group-hover:text-[#F4EFE5]">
          <ChevronDown
            className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180 text-[#B59A68]' : ''
              }`}
          />
        </div>
      </button>

      {/* Floating Dropdown Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 4, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 4, scale: 0.98 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="absolute left-0 right-0 top-full mt-2 z-50 rounded-xl bg-[#151716] border border-[#3B3A33] shadow-2xl shadow-black/80 backdrop-blur-xl overflow-hidden flex flex-col"
            style={{ maxHeight: '420px' }}
          >
            {/* Header: Search Box & Category Filter */}
            <div className="p-2.5 border-b border-[#3B3A33] bg-[#1D211F]/90 shrink-0 space-y-2">
              <div className="relative flex items-center">
                <Search className="w-3.5 h-3.5 text-stone/70 absolute left-3 pointer-events-none" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search sub-sections or statutes (e.g., 438, Bail, PMLA, Writ, NI 138)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-8 pr-7 py-1.5 rounded-md bg-[#151716] border border-[#3B3A33] text-xs text-[#F4EFE5] placeholder:text-stone/50 focus:outline-none focus:border-[#B59A68] transition-colors"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => setSearchQuery('')}
                    className="absolute right-2.5 text-stone/70 hover:text-[#F4EFE5]"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Quick Category Filter Pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 scrollbar-none text-[11px]">
                <button
                  type="button"
                  onClick={() => setActiveCategory('all')}
                  className={`px-2 py-0.5 rounded-full whitespace-nowrap transition-colors ${activeCategory === 'all'
                    ? 'bg-[#B59A68] text-[#151716] font-semibold'
                    : 'bg-[#242925] text-stone hover:text-[#F4EFE5] border border-[#3B3A33]'
                    }`}
                >
                  All ({CASE_CATEGORY_GROUPS.reduce((acc, g) => acc + g.options.length, 0)})
                </button>
                {CASE_CATEGORY_GROUPS.map((grp) => (
                  <button
                    key={grp.id}
                    type="button"
                    onClick={() => setActiveCategory(grp.id)}
                    className={`px-2 py-0.5 rounded-full whitespace-nowrap transition-colors flex items-center gap-1 ${activeCategory === grp.id
                      ? 'bg-[#B59A68] text-[#151716] font-semibold'
                      : 'bg-[#242925] text-stone hover:text-[#F4EFE5] border border-[#3B3A33]'
                      }`}
                  >
                    <span>{grp.iconEmoji}</span>
                    <span>{grp.label.split(' ')[0]}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Scrollable Groups & Sub-sections */}
            <div className="overflow-y-auto flex-1 divide-y divide-[#3B3A33]/50 p-1.5">
              {filteredGroups.length === 0 ? (
                <div className="py-8 text-center text-xs text-stone/70">
                  <p>No legal matter found matching "{searchQuery}".</p>
                  <button
                    type="button"
                    onClick={() => {
                      onChange(searchQuery || 'Custom');
                      setIsOpen(false);
                    }}
                    className="mt-2 text-[#B59A68] hover:underline font-medium inline-block"
                  >
                    Use "{searchQuery}" as custom filing type →
                  </button>
                </div>
              ) : (
                filteredGroups.map((group) => (
                  <div key={group.id} className="py-2 first:pt-1 last:pb-1">
                    {/* ── MAIN SECTION HEADER ──────────────────────────── */}
                    <div className="px-2.5 py-1.5 mb-1 rounded-md bg-[#1D211F] border border-[#3B3A33]/60 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm shrink-0">{group.iconEmoji}</span>
                        <div>
                          <h4 className="text-[11px] font-bold uppercase tracking-wider text-[#B59A68]">
                            {group.label}
                          </h4>
                          <p className="text-[10px] text-stone/60 leading-none mt-0.5 hidden sm:block">
                            {group.description}
                          </p>
                        </div>
                      </div>
                      <span className="text-[10px] font-semibold text-stone/70 bg-[#242925] px-1.5 py-0.5 rounded border border-[#3B3A33] shrink-0">
                        {group.options.length} matters
                      </span>
                    </div>

                    {/* ── SUB-SECTIONS (INDENTED UNDER MAIN SECTION) ────── */}
                    <div className="space-y-0.5 pl-2 sm:pl-3 border-l-2 border-[#3B3A33]/60 ml-3 my-1">
                      {group.options.map((option) => {
                        const isSelected = value === option.value;
                        return (
                          <button
                            key={option.value}
                            type="button"
                            onClick={() => {
                              if (option.value === 'Custom') {
                                onChange('');
                              } else {
                                onChange(option.value);
                              }
                              setIsOpen(false);
                            }}
                            className={`w-full text-left px-2.5 py-1.5 rounded-md text-xs transition-all flex items-center justify-between gap-2 group/item ${isSelected
                              ? 'bg-[#B59A68]/20 text-[#F4EFE5] font-medium border border-[#B59A68]/40 shadow-sm'
                              : 'text-stone hover:text-[#F4EFE5] hover:bg-[#242925] hover:border hover:border-[#3B3A33]'
                              }`}
                          >
                            <div className="flex items-center gap-2 min-w-0">
                              {/* Sub-section indicator dot or check */}
                              <div
                                className={`w-1.5 h-1.5 rounded-full shrink-0 transition-colors ${isSelected
                                  ? 'bg-[#B59A68] ring-2 ring-[#B59A68]/40'
                                  : 'bg-stone/40 group-hover/item:bg-[#B59A68]'
                                  }`}
                              />
                              <span
                                className={`truncate ${isSelected
                                  ? 'text-[#F4EFE5] font-semibold'
                                  : 'group-hover/item:text-[#F4EFE5]'
                                  }`}
                              >
                                {option.label}
                              </span>
                            </div>

                            <div className="flex items-center gap-1.5 shrink-0">
                              {option.statuteTag && (
                                <span
                                  className={`text-[10px] px-1.5 py-0.5 rounded font-mono transition-colors ${isSelected
                                    ? 'bg-[#B59A68]/30 text-[#F4EFE5] border border-[#B59A68]/50'
                                    : 'bg-[#151716] text-stone/70 border border-[#3B3A33] group-hover/item:text-stone/90'
                                    }`}
                                >
                                  {option.statuteTag}
                                </span>
                              )}
                              {isSelected && (
                                <Check className="w-3.5 h-3.5 text-[#B59A68] shrink-0 stroke-[2.5]" />
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Footer Bar */}
            <div className="px-3 py-1.5 bg-[#1D211F]/90 border-t border-[#3B3A33] flex items-center justify-between text-[11px] text-stone/60 shrink-0">
              <span>Hierarchical Categorization</span>
              <span className="font-mono text-[#B59A68]">16+ Indian Legal Domains</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
