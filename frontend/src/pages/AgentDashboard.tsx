import { useQuery } from "@tanstack/react-query";
import { listTickets } from "../api/client";
import { Ticket, Clock, AlertTriangle, CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";

export default function AgentDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ["tickets", { page_size: 10 }],
    queryFn: () => listTickets({ page_size: 10 }),
  });

  const tickets = data?.items || [];
  const openCount = tickets.filter((t: any) =>
    ["new", "open", "in_progress"].includes(t.status)
  ).length;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Agent Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        {[
          { label: "Open Tickets", value: openCount, icon: Ticket, color: "bg-blue-500" },
          { label: "Awaiting Reply", value: "—", icon: Clock, color: "bg-amber-500" },
          { label: "SLA Risk", value: "—", icon: AlertTriangle, color: "bg-red-500" },
          { label: "Resolved Today", value: "—", icon: CheckCircle, color: "bg-green-500" },
        ].map((card) => (
          <div key={card.label} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center gap-3">
              <div className={`${card.color} p-2.5 rounded-lg text-white`}>
                <card.icon size={20} />
              </div>
              <div>
                <p className="text-sm text-gray-500">{card.label}</p>
                <p className="text-2xl font-semibold text-gray-900">{card.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="font-semibold text-gray-800">Recent Tickets</h2>
          <Link to="/tickets" className="text-sm text-brand-600 hover:underline">
            View all
          </Link>
        </div>
        {isLoading ? (
          <div className="p-8 text-center text-gray-400">Loading...</div>
        ) : tickets.length === 0 ? (
          <div className="p-8 text-center text-gray-400">
            No tickets yet. Seed demo data or create one.
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {tickets.map((t: any) => (
              <li key={t.id}>
                <Link
                  to={`/tickets/${t.id}`}
                  className="flex items-center justify-between px-5 py-3.5 hover:bg-gray-50"
                >
                  <div>
                    <span className="text-xs font-mono text-gray-400 mr-2">
                      {t.ticket_number}
                    </span>
                    <span className="text-sm font-medium text-gray-800">
                      {t.subject}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <PriorityBadge priority={t.priority} />
                    <StatusBadge status={t.status} />
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    low: "bg-gray-100 text-gray-600",
    medium: "bg-blue-100 text-blue-700",
    high: "bg-orange-100 text-orange-700",
    critical: "bg-red-100 text-red-700",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[priority] || colors.medium}`}>
      {priority}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-medium">
      {status.replace(/_/g, " ")}
    </span>
  );
}