'use client';

import { RefObject, useEffect, useState } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';

interface BackgroundVideoProps {
  targetRef: RefObject<HTMLElement | null>;
  sources?: { src: string; type: string }[];
  posterSrc?: string;
}

export default function BackgroundVideo({
  targetRef,
  sources = [
    { src: '/video/court.mp4', type: 'video/mp4' },
  ],
  posterSrc,
}: BackgroundVideoProps) {
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mq.matches);
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const { scrollYProgress } = useScroll({
    target: targetRef,
    offset: ['start start', 'end start'],
  });

  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 90,
    damping: 24,
    mass: 0.6,
  });

  const progressSource = reducedMotion ? undefined : smoothProgress;
  const scale = useTransform(progressSource ?? smoothProgress, [0, 1], reducedMotion ? [1, 1] : [1, 1.15]);
  const y = useTransform(progressSource ?? smoothProgress, [0, 1], reducedMotion ? ['0%', '0%'] : ['0%', '16%']);
  const opacity = useTransform(
    progressSource ?? smoothProgress,
    [0, 0.6, 1],
    reducedMotion ? [0.35, 0.35, 0.35] : [0.45, 0.3, 0.06]
  );
  const overlayOpacity = useTransform(
    progressSource ?? smoothProgress,
    [0, 1],
    reducedMotion ? [0.75, 0.75] : [0.6, 0.95]
  );

  return (
    <div className="absolute inset-0 overflow-hidden">
      <motion.video
        className="h-full w-full object-cover"
        style={{ scale, y, opacity, willChange: 'transform, opacity' }}
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
        poster={posterSrc}
      >
        {sources.map((s) => (
          <source key={s.src} src={s.src} type={s.type} />
        ))}
      </motion.video>

      {/* Deep ink overlay — no blue tones, pure documentary archival feel */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-b from-[#151716]/90 via-[#151716]/60 to-[#151716]"
        style={{ opacity: overlayOpacity }}
      />
      {/* Static base tint */}
      <div className="absolute inset-0 bg-[#151716]/40" />
    </div>
  );
}
