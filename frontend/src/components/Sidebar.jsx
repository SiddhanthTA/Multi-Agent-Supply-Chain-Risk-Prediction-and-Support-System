import { NavLink } from "react-router-dom";
import { 
  LayoutDashboard, 
  AlertTriangle, 
  Activity, 
  BrainCircuit, 
  Lightbulb, 
  Radio, 
  HeartPulse, 
  Network
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Events", href: "/events", icon: Activity },
  { name: "Risks", href: "/risks", icon: AlertTriangle },
  { name: "Predictions", href: "/predictions", icon: BrainCircuit },
];

export function Sidebar() {
  return (
    <div className="hidden border-r bg-sidebar md:block w-64 flex-shrink-0 min-h-screen flex-col">
      <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
        <NavLink to="/" className="flex items-center gap-2 font-semibold text-lg text-primary">
          <BrainCircuit className="h-6 w-6" />
          <span className="">SupplySentry AI</span>
        </NavLink>
      </div>
      <div className="flex-1 overflow-auto py-2">
        <nav className="grid items-start px-2 text-sm font-medium lg:px-4">
          {navItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.href}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:bg-nav-hover hover:text-primary",
                  isActive ? "bg-nav-active text-primary font-semibold" : ""
                )
              }
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  );
}
