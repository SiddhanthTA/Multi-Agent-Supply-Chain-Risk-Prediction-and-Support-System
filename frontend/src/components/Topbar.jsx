import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/components/ThemeProvider";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { LogOut, Moon, Sun, User, Search } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";

export function Topbar() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const navigate = useNavigate();

  const getPageTitle = () => {
    switch(location.pathname) {
      case '/': return 'Dashboard Overview';
      case '/feed': return 'Intelligence Feed';
      case '/events': return 'Events';
      case '/risks': return 'Risks';
      case '/predictions': return 'Predictions';
      case '/recommendations': return 'Recommendations';
      case '/correlation': return 'Correlation';
      case '/health': return 'System Health';
      case '/profile': return 'Profile';
      default: return 'Dashboard Overview';
    }
  };

  return (
    <header className="flex h-14 items-center gap-4 border-b bg-card px-4 lg:h-[60px] lg:px-6 justify-between">
      <div className="flex items-center gap-4 md:hidden">
        <span className="font-semibold text-primary">SupplySentry AI</span>
      </div>
      
      <div className="hidden md:flex flex-1 items-center gap-4">
        <h1 className="text-xl font-semibold tracking-tight">{getPageTitle()}</h1>
      </div>
      
      <div className="flex items-center gap-4">
        <div className="relative hidden md:block mr-2">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input type="search" placeholder="Search..." className="w-64 pl-9 bg-background/50 border-muted" />
        </div>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          title="Toggle Theme"
        >
          <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
        
        <div className="flex items-center gap-2 border-l border-border pl-4 ml-1">
          <div 
            className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => navigate('/profile')}
          >
            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <User className="h-4 w-4" />
            </div>
            <span className="text-sm font-medium hidden lg:block mr-2">
              {user?.full_name || user?.username || "User"}
            </span>
          </div>
          <Button variant="ghost" size="icon" onClick={logout} title="Log out" className="text-muted-foreground hover:text-destructive">
            <LogOut className="h-4 w-4" />
            <span className="sr-only">Log out</span>
          </Button>
        </div>
      </div>
    </header>
  );
}
