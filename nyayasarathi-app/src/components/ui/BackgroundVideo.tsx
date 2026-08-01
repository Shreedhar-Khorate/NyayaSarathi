'use client';

import { RefObject, useEffect, useState } from 'react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';

interface BackgroundVideoProps {
  /** The section the scroll progress is measured against (usually the hero wrapper) */
  targetRef: RefObject<HTMLElement | null>;
  /** MP4/WebM sources — put real files in /public/video and point here */
  sources?: { src: string; type: string }[];
  posterSrc?: string;
}

/**
 * Cinematic scroll-parallax video:
 * - Scales up slightly and drifts as the user scrolls through the hero (smoothed with a spring,
 *   so it never feels like it's snapping to the scroll position).
 * - Fades + darkens on the way out so the next section reads cleanly.
 * - Respects prefers-reduced-motion: parallax transforms are skipped, video still plays.
 */
export default function BackgroundVideo({
  targetRef,
  sources = [
    { src: '/video/hero-bg.mp4', type: 'video/mp4' },
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

  // Smooth out the raw scroll progress so the parallax glides instead of tracking 1:1
  const smoothProgress = useSpring(scrollYProgress, {
    stiffness: 90,
    damping: 24,
    mass: 0.6,
  });

  const progressSource = reducedMotion ? undefined : smoothProgress;
  const scale = useTransform(progressSource ?? smoothProgress, [0, 1], reducedMotion ? [1, 1] : [1, 1.18]);
  const y = useTransform(progressSource ?? smoothProgress, [0, 1], reducedMotion ? ['0%', '0%'] : ['0%', '18%']);
  const opacity = useTransform(
    progressSource ?? smoothProgress,
    [0, 0.6, 1],
    reducedMotion ? [0.45, 0.45, 0.45] : [0.55, 0.4, 0.08]
  );
  const overlayOpacity = useTransform(
    progressSource ?? smoothProgress,
    [0, 1],
    reducedMotion ? [0.7, 0.7] : [0.55, 0.92]
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

      {/* Legibility scrim — deepens as the video parallaxes out */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-b from-obsidian/80 via-obsidian/55 to-obsidian"
        style={{ opacity: overlayOpacity }}
      />
      {/* Static base tint so text stays readable even at the top of scroll */}
      <div className="absolute inset-0 bg-obsidian/35" />
    </div>
  );
}
