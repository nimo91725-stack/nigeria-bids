import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import AddOpportunity from "./pages/AddOpportunity";
import OpportunityDetail from "./pages/OpportunityDetail";
import Alerts from "./pages/Alerts";
import { LayoutDashboard, Plus, Bell, RefreshCw } from "lucide-react";

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-green-700 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-6">
          <span className="font-bold text-lg tracking-tight">
            Nigeria Bids <span className="text-green-300 text-sm font-normal">Travel TMC</span>
          </span>
          <div className="flex gap-1 ml-4">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  isActive ? "bg-green-900" : "hover:bg-green-600"
                }`
              }
            >
              <LayoutDashboard size={15} /> Dashboard
            </NavLink>
            <NavLink
              to="/add"
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  isActive ? "bg-green-900" : "hover:bg-green-600"
                }`
              }
            >
              <Plus size={15} /> Add Opportunity
            </NavLink>
            <NavLink
              to="/alerts"
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                  isActive ? "bg-green-900" : "hover:bg-green-600"
                }`
              }
            >
              <Bell size={15} /> Alerts
            </NavLink>
          </div>
        </div>
      </nav>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/add" element={<AddOpportunity />} />
          <Route path="/opportunities/:id" element={<OpportunityDetail />} />
          <Route path="/alerts" element={<Alerts />} />
        </Routes>
      </main>

      <footer className="text-center text-xs text-gray-400 py-3 border-t">
        Nigeria Bids Aggregator — Travel Management Services
      </footer>
    </div>
  );
}
