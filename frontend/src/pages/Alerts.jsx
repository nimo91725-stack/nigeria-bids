import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAlerts, createAlert, deleteAlert } from "../api";
import { Trash2, Bell } from "lucide-react";

export default function Alerts() {
  const qc = useQueryClient();
  const [email, setEmail] = useState("");
  const [keywords, setKeywords] = useState("travel,TMC,tour,airline,hotel,logistics");

  const { data: alerts = [] } = useQuery({ queryKey: ["alerts"], queryFn: getAlerts });

  const createMut = useMutation({
    mutationFn: createAlert,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["alerts"] });
      setEmail("");
    },
  });

  const deleteMut = useMutation({
    mutationFn: deleteAlert,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-xl font-bold text-gray-900">Email Alerts</h1>
      <p className="text-sm text-gray-500">
        Get notified when new matching opportunities are found. Add an email below to subscribe.
      </p>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 space-y-4">
        <h2 className="font-semibold text-gray-800">Add Alert Subscription</h2>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@yourcompany.com"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Keywords (comma-separated)</label>
          <input
            type="text"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
        <button
          onClick={() => createMut.mutate({ email, keywords })}
          disabled={!email || createMut.isPending}
          className="bg-green-700 hover:bg-green-800 text-white text-sm font-medium px-5 py-2 rounded-lg disabled:opacity-60"
        >
          {createMut.isPending ? "Subscribing..." : "Subscribe"}
        </button>
      </div>

      {alerts.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
          <h2 className="font-semibold text-gray-800 mb-4">Active Subscriptions</h2>
          <ul className="space-y-3">
            {alerts.map((a) => (
              <li key={a.id} className="flex items-center justify-between text-sm">
                <div>
                  <span className="font-medium text-gray-800">{a.email}</span>
                  <span className="text-gray-400 ml-2">— {a.keywords}</span>
                </div>
                <button
                  onClick={() => deleteMut.mutate(a.id)}
                  className="text-red-400 hover:text-red-600"
                >
                  <Trash2 size={15} />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
