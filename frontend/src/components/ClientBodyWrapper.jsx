'use client';

import { usePathname } from 'next/navigation';

export default function ClientBodyWrapper({ children }) {
  const pathname = usePathname();
  // Check if current path is a urns page
  const isUrnPage = pathname?.startsWith('/urns/');

  return (
    <div className={isUrnPage ? "" : "pb-20"}>
      {children}
    </div>
  );
}
