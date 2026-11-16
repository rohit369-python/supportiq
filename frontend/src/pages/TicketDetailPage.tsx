import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getTicket } from "../api/client";

export default function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: ticket, isLoading } = useQuery({
    queryKey: ["ticket", id],
    queryFn: () => getTicket(id!),
    enabled: !!id,
  });

  if (isLoading) return <div className="text-gray-400">Loading ticket...</div>;
  if (!ticket) return <div className="text-red-500">Ticket not found</div>;

  return (
    <div>
      <div className="mb-6">
        <p className="text-sm text-gray-400 font-mono">{ticket.ticket_number}</p>
        <h1 className="text-2xl font-bold text-gray-900 mt-1">{ticket.subject}</h1>
        <div className="flex gap-2 mt-2">
          <span className="text-xs px-2 py-1 rounded-full bg-blue-100 text-blue-700 capitalize">
            {ticket.priority}
          </span>
          <span className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-600 capitalize">
            {ticket.status.replace(/_/g, " ")}
          </span>
          {ticket.intent && (
            <span className="text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-700">
              {ticket.intent}
            </span>
          )}
          {ticket.ai_classified && (
            <span className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">
              AI classified ({Math.round((ticket.ai_confidence || 0) * 100)}%)
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-2">Description</h2>
            <p className="text-gray-600 whitespace-pre-wrap">{ticket.description}</p>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-3">AI Assistant</h2>
            <p className="text-sm text-gray-500 mb-3">
              Suggested replies and summaries will appear here when the full AI agent assistant module is connected.
            </p>
            <button className="text-sm bg-brand-50 text-brand-700 px-3 py-1.5 rounded-lg hover:bg-brand-100">
              Generate suggested reply
            </button>
          </div>
        </div>
        <div className="space-y-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h2 className="font-semibold text-gray-800 mb-3">Details</h2>
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Category</dt>
                <dd>{ticket.category || "—"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Source</dt>
                <dd className="capitalize">{ticket.source_channel}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd>{new Date(ticket.created_at).toLocaleString()}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Needs review</dt>
                <dd>{ticket.needs_human_review ? "Yes" : "No"}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
}