'use client';

import { usePathname } from 'next/navigation';

export default function ClientBodyWrapper({ children }) {
  const pathname = usePathname();
  const isUrnPage = pathname?.startsWith('/urns/');
  const isQuizPage = /^\/motif\/[^/]+\/quiz/.test(pathname || '');
  const isExamPage = /^\/urns\/[^/]+\/exam/.test(pathname || '');
  // Quiz/exam pages hide FloatingNavbar, so no bottom padding needed.
  // Desktop navigation is now top-fixed; mobile keeps the bottom command bar.
  const noPadding = isUrnPage || isQuizPage || isExamPage;
  return (
    <div className={noPadding ? "" : "pb-24 md:pb-0"}>
      {children}
    </div>
  );
}
