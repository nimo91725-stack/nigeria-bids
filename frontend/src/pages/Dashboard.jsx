import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getOpportunities, scrapeAll } from "../api";
import OpportunityCard from "../components/OpportunityCard";
import FilterBar from "../components/FilterBar";
import { RefreshCw, Loader2 } from "lucide-react";

const STAT_STATUS = [
  { key: "new", label: "New", color: "bg-blue-500" },
  { key: "reviewing", label: "Reviewing", color: "bg-yellow-500" },
  { key: "bidding", label: "Bidding", color: "bg-orange-500" },
  { key: "submitted", label: "Submitted", color: "bg-purple-500" },
  { key: "won", label: "Won", color: "bg-green-500" },
];

export default function Dashboard() {
  const [filters, setFilters] = useState({ search: "", status: "", sector: "" });
  const [scrapeLog, setScrapeLog] = useState(null);
  const queryClient = useQueryClient();

  const { data: opps = [], isLoading } = useQuery({
    queryKey: ["opportunities", filters],
    queryFn: () => getOpportunities({
      search: filters.search || undefined,
      status: filters.status || undefined,
      sector: filters.sector || undefined,
    }),
  });

  const { data: allOpps = [] } = useQuery({
    queryKey: ["opportunities", {}],
    queryFn: () => getOpportunities({}),
  });

  const scrapeMut = useMutation({
    mutationFn: scrapeAll,
    onSuccess: (results) => {
      setScrapeLog(results);
      queryClient.invalidateQueries({ queryKey: ["opportunities"] });
    },
  });

  const statCounts = STAT_STATUS.map((s) => ({
    ...s,
    count: allOpps.filter((o) => o.status === s.key).length,
  }));

  return (
    <div className="space-y-6">
      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {statCounts.map((s) => (
          <div key={s.key} className="bg-white rounded-xl border border-gray-200 p-4 text-center shadow-sm">
            <div className={`text-2xl font-bold text-gray-900`}>{s.count}</div>
            <div className="text-xs text-gray-500 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <FilterBar filters={filters} onChange={setFilters} />
        <button
          onClick={() => scrapeMut.mutate()}
          disabled={scrapeMut.isPending}
          className="flex items-center gap-2 bg-green-700 hover:bg-green-800 text-white text-sm font-medium px-4 py-2 rounded-lg disabled:opacity-60 transition-colors"
        >
          {scrapeMut.isPending ? (
            <Loader2 size={15} className="animate-spin" />
          ) : (
            <RefreshCw size={15} />
          )}
          Fetch All Sources
        </button>
      </div>

      {/* Scrape log */}
      {scrapeLog && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-xs space-y-1">
          <p className="font-semibold text-gray-700 mb-1">Last fetch results:</p>
          {scrapeLog.map((r) => (
            <div key={r.source} className={`flex gap-3 ${r.error ? "text-red-600" : "text-gray-600"}`}>
              <span className="font-medium w-36">{r.source}</span>
              {r.error ? (
                <span>Error: {r.error}</span>
              ) : (
                <span>{r.new_count} new, {r.skipped_count} already known</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Opportunities grid */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 size={32} className="animate-spin text-green-600" />
        </div>
      ) : opps.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg font-medium">No opportunities found</p>
          <p className="text-sm mt-1">Click "Fetch All Sources" to pull the latest bids</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {opps.map((opp) => (
            <OpportunityCard key={opp.id} opp={opp} />
          ))}
        </div>
      )}
    </div>
  );
}
