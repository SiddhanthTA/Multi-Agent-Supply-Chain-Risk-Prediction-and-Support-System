import { useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";

export function DashboardLayout() {
  const location = useLocation();

  // Every navigation starts at the top. The app scrolls the window (not a
  // nested container), so a route change resets the window scroll position and
  // also clears focus so the new page does not appear mid-document.
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen w-full bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 p-4 md:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
