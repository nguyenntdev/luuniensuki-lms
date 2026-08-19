'use client';

import type { ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { isShellRoute } from '@/lib/shellRoutes';

interface ClientBodyWrapperProps {
  children: ReactNode;
}

export default function ClientBodyWrapper({ children }: ClientBodyWrapperProps) {
  const pathname = usePathname();
  // When the shell (sticky header + fixed mobile bottom nav) is hidden, no
  // extra bottom clearance is needed. Otherwise the mobile bottom nav floats
  // over content, so we reserve space below it on small screens.
  const showShell = isShellRoute(pathname);
  return (
    <div className={showShell ? 'pb-24 md:pb-0' : ''}>
      {children}
    </div>
  );
}