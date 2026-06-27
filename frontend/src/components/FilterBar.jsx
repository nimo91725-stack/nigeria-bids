import { Search, X } from "lucide-react";

const STATUSES = ["new", "reviewing", "bidding", "submitted", "won", "lost", "expired"];
const SECTORS = ["Government", "Oil & Gas", "Banking", "Telecoms", "FMCG", "International/NGO", "Mixed", "Email"];

export default function FilterBar({ filters, onChange }) {
  const set = (key, val) => onChange({ ...filters, [key]: val });
  const clear = () => onChange({ search: "", status: "", sector: "" });
  const hasFilters = filters.search || filters.status || filters.sector;

  return (
    <div className="flex flex-wrap gap-3 items-center">
      <div className="relative">
        <Search size={15} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search bids..."
          value={filters.search}
          onChange={(e) => set("search", e.target.value)}
          className="pl-8 pr-3 py-1.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 w-56"
        />
      </div>

      <select
        value={filters.status}
        onChange={(e) => set("status", e.target.value)}
        className="px-3 py-1.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
      >
        <option value="">All Statuses</option>
        {STATUSES.map((s) => (
          <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
        ))}
      </select>

      <select
        value={filters.sector}
        onChange={(e) => set("sector", e.target.value)}
        className="px-3 py-1.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
      >
        <option value="">All Sectors</option>
        {SECTORS.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>

      {hasFilters && (
        <button
          onClick={clear}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-red-600"
        >
          <X size={13} /> Clear
        </button>
      )}
    </div>
  );
}
