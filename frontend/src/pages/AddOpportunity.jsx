import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { createOpportunity } from "../api";

const SECTORS = ["Government", "Oil & Gas", "Banking", "Telecoms", "FMCG", "International/NGO", "Mixed", "Other"];

export default function AddOpportunity() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [form, setForm] = useState({
    title: "", organization: "", sector: "", description: "",
    requirements: "", source_url: "", deadline: "", notes: "",
  });

  const mut = useMutation({
    mutationFn: createOpportunity,
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["opportunities"] });
      navigate(`/opportunities/${data.id}`);
    },
  });

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const field = (label, key, type = "text", props = {}) => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type={type}
        value={form[key]}
        onChange={(e) => set(key, e.target.value)}
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
        {...props}
      />
    </div>
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      ...form,
      source_type: "manual",
      deadline: form.deadline ? new Date(form.deadline).toISOString() : undefined,
      sector: form.sector || undefined,
    };
    mut.mutate(payload);
  };

  return (
    <div className="max-w-2xl">
      <h1 className="text-xl font-bold text-gray-900 mb-6">Add Opportunity Manually</h1>
      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
        {field("Tender / Bid Title *", "title", "text", { required: true })}
        {field("Organization *", "organization", "text", { required: true })}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Sector</label>
          <select
            value={form.sector}
            onChange={(e) => set("sector", e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="">Select sector</option>
            {SECTORS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        {field("Submission Deadline", "deadline", "date")}
        {field("Source URL", "source_url", "url", { placeholder: "https://..." })}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            rows={4}
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Requirements</label>
          <textarea
            rows={3}
            value={form.requirements}
            onChange={(e) => set("requirements", e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            placeholder="Documents needed, certifications, etc."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
          <textarea
            rows={2}
            value={form.notes}
            onChange={(e) => set("notes", e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>

        <button
          type="submit"
          disabled={mut.isPending}
          className="w-full bg-green-700 hover:bg-green-800 text-white font-medium py-2.5 rounded-lg disabled:opacity-60 transition-colors"
        >
          {mut.isPending ? "Saving..." : "Save Opportunity"}
        </button>

        {mut.isError && (
          <p className="text-sm text-red-600">Error: {mut.error?.message}</p>
        )}
      </form>
    </div>
  );
}
