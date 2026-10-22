'use client';

import { ReactNode, Suspense } from 'react';
import Loading from '@/app/loading';

export default function AppLoaderWrapper({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<Loading />}>
      {children}
    </Suspense>
  );
}
