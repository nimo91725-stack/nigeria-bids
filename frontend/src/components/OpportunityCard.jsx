import { Link } from "react-router-dom";
import { format, isPast, differenceInDays } from "date-fns";
import { ExternalLink, Calendar, Building2, Tag } from "lucide-react";

const STATUS_COLORS = {
  new: "bg-blue-100 text-blue-800",
  reviewing: "bg-yellow-100 text-yellow-800",
  bidding: "bg-orange-100 text-orange-800",
  submitted: "bg-purple-100 text-purple-800",
  won: "bg-green-100 text-green-800",
  lost: "bg-red-100 text-red-800",
  expired: "bg-gray-100 text-gray-500",
};

const SOURCE_COLORS = {
  scraped: "bg-indigo-50 text-indigo-700",
  rss: "bg-teal-50 text-teal-700",
  email: "bg-pink-50 text-pink-700",
  manual: "bg-gray-100 text-gray-600",
};

export default function OpportunityCard({ opp }) {
  const deadline = opp.deadline ? new Date(opp.deadline) : null;
  const daysLeft = deadline ? differenceInDays(deadline, new Date()) : null;
  const isUrgent = daysLeft !== null && daysLeft >= 0 && daysLeft <= 5;
  const isExpired = deadline && isPast(deadline);

  return (
    <div className={`bg-white rounded-xl border shadow-sm p-4 hover:shadow-md transition-shadow ${isUrgent ? "border-orange-300" : "border-gray-200"}`}>
      <div className="flex items-start justify-between gap-2">
        <Link to={`/opportunities/${opp.id}`} className="flex-1 group">
          <h3 className="font-semibold text-gray-900 group-hover:text-green-700 leading-snug line-clamp-2">
            {opp.title}
          </h3>
        </Link>
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap ${STATUS_COLORS[opp.status] || "bg-gray-100"}`}>
          {opp.status}
        </span>
      </div>

      <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
        <span className="flex items-center gap-1">
          <Building2 size={12} /> {opp.organization}
        </span>
        {opp.sector && (
          <span className="flex items-center gap-1">
            <Tag size={12} /> {opp.sector}
          </span>
        )}
        {deadline && (
          <span className={`flex items-center gap-1 ${isExpired ? "text-red-500" : isUrgent ? "text-orange-600 font-semibold" : ""}`}>
            <Calendar size={12} />
            {isExpired
              ? "Expired"
              : daysLeft === 0
              ? "Due today"
              : `${daysLeft}d left`}{" "}
            ({format(deadline, "dd MMM yyyy")})
          </span>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <span className={`text-xs px-2 py-0.5 rounded ${SOURCE_COLORS[opp.source_type] || "bg-gray-100"}`}>
          {opp.source_name || opp.source_type}
        </span>
        {opp.source_url && (
          <a
            href={opp.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-green-600 hover:text-green-800"
          >
            <ExternalLink size={14} />
          </a>
        )}
      </div>
    </div>
  );
}
