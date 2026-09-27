import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  AlertTriangle,
  Activity,
  TrendingUp,
  Building2,
  CheckCircle2,
  CloudRain
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Events", href: "/events", icon: Activity },
  { name: "Risks", href: "/risks", icon: AlertTriangle },
  { name: "Resolved Risks", href: "/resolved-risks", icon: CheckCircle2 },
  { name: "Risk Trends", href: "/risk-trends", icon: TrendingUp },
  { name: "Company Profile", href: "/company-profile", icon: Building2 },
  { name: "Weather Monitoring", href: "/weather", icon: CloudRain },
];

export function Sidebar() {
  return (
    <div className="sticky top-0 hidden h-screen w-64 flex-shrink-0 flex-col border-r bg-sidebar md:flex">
      <div className="flex h-14 items-center border-b px-5 lg:h-[60px]">
        <NavLink
          to="/"
          className="group flex items-center gap-2.5 rounded-md outline-none transition-opacity duration-150 hover:opacity-85"
        >
          <span
            aria-hidden="true"
            className="flex h-6 w-6 items-center justify-center rounded-[7px] bg-primary/12 ring-1 ring-inset ring-primary/30 transition-colors duration-150 group-hover:bg-primary/20"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
          </span>
          <span className="select-none text-[15px] font-semibold tracking-tight">
            <span className="text-muted-foreground">Supply</span>
            <span className="text-foreground">Sentry</span>
          </span>
        </NavLink>
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="grid items-start gap-0.5 px-3 text-sm font-medium lg:px-4">
          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all duration-150 ease-out hover:bg-nav-hover hover:text-foreground",
                  isActive && "bg-nav-active font-medium text-foreground"
                )
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    aria-hidden="true"
                    className={cn(
                      "absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-primary transition-opacity duration-150",
                      isActive ? "opacity-100" : "opacity-0"
                    )}
                  />
                  <item.icon
                    className={cn(
                      "h-4 w-4 shrink-0 transition-colors duration-150",
                      isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                    )}
                  />
                  {item.name}
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
}
