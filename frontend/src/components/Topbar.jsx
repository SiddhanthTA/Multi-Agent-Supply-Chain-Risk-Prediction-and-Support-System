import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/components/ThemeProvider";
import { Button } from "@/components/ui/Button";
import { LogOut, Moon, Sun, User } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

export function Topbar() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/') return 'Dashboard';
    if (path === '/feed') return 'Intelligence Feed';
    if (path === '/events') return 'Events';
    if (path === '/risks') return 'Risks';
    if (path === '/risk-trends') return 'Risk Trends';
    if (path.endsWith('/investigation')) return 'Risk Detail';
    if (path.endsWith('/response-plan')) return 'Risk Detail';
    if (path.endsWith('/correlations')) return 'Risk Detail';
    if (path.endsWith('/impact')) return 'Risk Detail';
    if (path.startsWith('/risks/')) return 'Risk Detail';
    if (path === '/predictions') return 'Predictions';
    if (path === '/recommendations') return 'Recommendations';
    if (path === '/correlation') return 'Correlation';
    if (path === '/health') return 'System Health';
    if (path === '/company-profile') return 'Company Profile';
    if (path === '/profile') return 'Profile';
    return 'Dashboard';
  };

  return (
    <header className="flex h-14 items-center gap-4 border-b bg-card px-4 lg:h-[60px] lg:px-6 justify-between">
      <div className="flex items-center gap-3 md:hidden">
        <span className="select-none text-[15px] font-semibold tracking-tight">
          <span className="text-muted-foreground">Supply</span>
          <span>Sentry</span>
        </span>
      </div>

      <div className="hidden md:flex flex-1 items-center gap-4">
        <h1 className="text-[15px] font-semibold tracking-tight">{getPageTitle()}</h1>
      </div>

      <div className="flex items-center gap-1.5">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          title="Toggle Theme"
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all duration-200 dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all duration-200 dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>

        <div className="ml-1 flex items-center gap-1 border-l border-border pl-2">
          <button
            type="button"
            onClick={() => navigate('/profile')}
            className="flex items-center gap-2 rounded-lg px-2 py-1.5 transition-colors duration-150 hover:bg-muted focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary">
              <User className="h-3.5 w-3.5" />
            </span>
            <span className="hidden text-sm font-medium lg:block">
              {user?.full_name || user?.username || "User"}
            </span>
          </button>
          <Button variant="ghost" size="icon" onClick={logout} title="Log out" className="text-muted-foreground hover:text-destructive">
            <LogOut className="h-4 w-4" />
            <span className="sr-only">Log out</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
