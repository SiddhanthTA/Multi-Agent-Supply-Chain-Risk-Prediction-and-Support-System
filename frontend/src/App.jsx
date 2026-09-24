import { Routes, Route } from "react-router-dom";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import Dashboard from "@/pages/Dashboard";
import Events from "@/pages/Events";
import EventDetails from "@/pages/Events/EventDetails";
import Risks from "@/pages/Risks";
import RiskDetails from "@/pages/Risks/RiskDetails";
import Predictions from "@/pages/Predictions";
import PredictionDetails from "@/pages/Predictions/PredictionDetails";
import Recommendations from "@/pages/Recommendations";
import RecommendationDetails from "@/pages/Recommendations/RecommendationDetails";
import IntelligenceFeed from "@/pages/Feed";
import SystemHealth from "@/pages/SystemHealth";
import CorrelationIntelligence from "@/pages/Correlation";
import Profile from "@/pages/Profile";
import Login from "@/pages/Auth/Login";
import Register from "@/pages/Auth/Register";
import { ProtectedRoute } from "@/components/ProtectedRoute";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      <Route path="/" element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route index element={<Dashboard />} />
        <Route path="feed" element={<IntelligenceFeed />} />
        <Route path="correlation" element={<CorrelationIntelligence />} />
        
        <Route path="events" element={<Events />} />
        <Route path="events/:id" element={<EventDetails />} />
        
        <Route path="risks" element={<Risks />} />
        <Route path="risks/:id" element={<RiskDetails />} />
        
        <Route path="predictions" element={<Predictions />} />
        <Route path="predictions/:id" element={<PredictionDetails />} />
        
        <Route path="recommendations" element={<Recommendations />} />
        <Route path="recommendations/:id" element={<RecommendationDetails />} />
        
        <Route path="health" element={<SystemHealth />} />
        <Route path="profile" element={<Profile />} />
        
          {/* Fallback route */}
          <Route path="*" element={<div className="p-8 text-center flex flex-col items-center justify-center h-full"><h2 className="text-2xl font-bold">404</h2><p className="text-muted-foreground">Page not found</p></div>} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
