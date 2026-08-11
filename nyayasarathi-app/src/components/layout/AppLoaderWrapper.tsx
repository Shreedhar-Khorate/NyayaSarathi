'use client';

import { useState, useEffect, ReactNode, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Loading from '@/app/loading';

export default function AppLoaderWrapper({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Dismiss initial loader immediately on client mount without artificial delay
    setLoading(false);
  }, []);

  return (
    <>
      <AnimatePresence mode="wait">
        {loading && (
          <motion.div
            key="app-initial-loader"
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5, ease: 'easeInOut' }}
            className="fixed inset-0 z-[9999]"
          >
            <Loading />
          </motion.div>
        )}
      </AnimatePresence>
      <Suspense fallback={<Loading />}>
        {children}
      </Suspense>
    </>
  );
}
