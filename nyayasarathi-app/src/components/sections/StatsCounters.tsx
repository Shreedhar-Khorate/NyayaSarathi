'use client';

import { useEffect, useRef } from 'react';
import { motion, useInView, animate } from 'framer-motion';

const STATS = [
  { value: 85,  suffix: '%', label: 'Research time saved per case brief' },
  { value: 100, suffix: '%', label: 'Citation verifiability — every claim traceable' },
  { value: 2,   suffix: '',  label: 'Hybrid RAG engine — vector + lexical, fused', isText: true },
];

function Counter({ value, suffix }: { value: number; suffix: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-40px' });

  useEffect(() => {
    if (!isInView || !ref.current) return;
    const node = ref.current;
    const controls = animate(0, value, {
      duration: 1.8,
      ease: [0.16, 1, 0.3, 1],
      onUpdate(latest) {
        node.textContent = Math.round(latest).toString();
      },
    });
    return () => controls.stop();
  }, [isInView, value]);

  return (
    <span className="font-display text-[#B59A68] text-6xl font-semibold tabular-nums md:text-7xl">
      <span ref={ref}>0</span>
      {suffix}
    </span>
  );
}

export default function StatsCounters() {
  return (
    <section className="relative border-y border-[#3B3A33] py-24 bg-[#151716]">
      <div className="relative mx-auto max-w-6xl px-6">
        {/* Section label */}
        <div className="mb-14">
          <span className="section-label">By the Numbers</span>
        </div>

        <div className="grid grid-cols-1 gap-0 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-[#3B3A33]">
          {STATS.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.55, delay: i * 0.12 }}
              className="py-10 md:py-0 md:px-14 first:pl-0 last:pr-0"
            >
              {stat.isText ? (
                <span className="font-display text-[#B59A68] text-6xl font-semibold md:text-7xl">
                  Hybrid RAG
                </span>
              ) : (
                <Counter value={stat.value} suffix={stat.suffix} />
              )}
              <p className="mt-3 font-sans text-sm leading-relaxed text-stone max-w-[24ch]">
                {stat.label}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
