import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getOpportunity, updateOpportunity, deleteOpportunity } from "../api";
import { format } from "date-fns";
import { ArrowLeft, ExternalLink, Trash2 } from "lucide-react";
import { useState } from "react";

const STATUSES = ["new", "reviewing", "bidding", "submitted", "won", "lost", "expired"];

export default function OpportunityDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [notes, setNotes] = useState("");

  const { data: opp, isLoading } = useQuery({
    queryKey: ["opportunity", id],
    queryFn: () => getOpportunity(id),
    onSuccess: (data) => setNotes(data.notes || ""),
  });

  const updateMut = useMutation({
    mutationFn: (data) => updateOpportunity(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["opportunity", id] }),
  });

  const deleteMut = useMutation({
    mutationFn: () => deleteOpportunity(id),
    onSuccess: () => navigate("/"),
  });

  if (isLoading) return <div className="py-16 text-center text-gray-400">Loading...</div>;
  if (!opp) return <div className="py-16 text-center text-gray-400">Not found</div>;

  return (
    <div className="max-w-3xl space-y-6">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800"
      >
        <ArrowLeft size={15} /> Back
      </button>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-xl font-bold text-gray-900 leading-snug">{opp.title}</h1>
          <button
            onClick={() => { if (confirm("Delete this opportunity?")) deleteMut.mutate(); }}
            className="text-red-400 hover:text-red-600 shrink-0"
          >
            <Trash2 size={18} />
          </button>
        </div>

        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
          <div>
            <dt className="text-gray-500">Organization</dt>
            <dd className="font-medium">{opp.organization}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Sector</dt>
            <dd className="font-medium">{opp.sector || "—"}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Source</dt>
            <dd>{opp.source_name || opp.source_type}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Deadline</dt>
            <dd className="font-medium">
              {opp.deadline ? format(new Date(opp.deadline), "dd MMM yyyy") : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-gray-500">Published</dt>
            <dd>{opp.published_at ? format(new Date(opp.published_at), "dd MMM yyyy") : "—"}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Relevance Score</dt>
            <dd>{opp.relevance_score}</dd>
          </div>
        </dl>

        {opp.source_url && (
          <a
            href={opp.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-green-700 hover:underline text-sm font-medium"
          >
            <ExternalLink size={14} /> View Original Tender
          </a>
        )}

        {opp.description && (
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Description</p>
            <p className="text-sm text-gray-700 whitespace-pre-line">{opp.description}</p>
          </div>
        )}

        {/* Status update */}
        <div className="flex items-center gap-3 pt-2 border-t">
          <label className="text-sm text-gray-600 font-medium">Status:</label>
          <select
            value={opp.status}
            onChange={(e) => updateMut.mutate({ status: e.target.value })}
            className="px-3 py-1.5 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
            ))}
          </select>
        </div>

        {/* Notes */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">Internal Notes</label>
          <textarea
            rows={4}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full border border-gray-300 rounded-lg text-sm p-2.5 focus:outline-none focus:ring-2 focus:ring-green-500"
            placeholder="Add notes, contact names, deadlines reminders..."
          />
          <button
            onClick={() => updateMut.mutate({ notes })}
            disabled={updateMut.isPending}
            className="bg-green-700 hover:bg-green-800 text-white text-sm px-4 py-1.5 rounded-lg disabled:opacity-60"
          >
            Save Notes
          </button>
        </div>
      </div>
    </div>
  );
}
