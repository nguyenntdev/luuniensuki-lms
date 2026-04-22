'use client';

import { usePathname } from 'next/navigation';

export default function ClientBodyWrapper({ children }) {
  const pathname = usePathname();
  const isUrnPage = pathname?.startsWith('/urns/');
  const isQuizPage = /^\/motif\/[^/]+\/quiz/.test(pathname || '');
  const isExamPage = /^\/urns\/[^/]+\/exam/.test(pathname || '');
  // Quiz/exam pages hide FloatingNavbar, so no bottom padding needed
  const noPadding = isUrnPage || isQuizPage || isExamPage;
  return (
    <div className={noPadding ? "" : "pb-20"}>
      {children}
    </div>
  );
}
