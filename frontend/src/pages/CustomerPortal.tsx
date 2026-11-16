export default function CustomerPortal() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Customer Portal</h1>
      <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
        <p className="text-gray-500 mb-4">
          Customer self-service portal for creating tickets, viewing history, and chatting with AI.
        </p>
        <p className="text-sm text-gray-400">
          Use the AI Chatbot page to experience the customer-facing assistant. Full portal screens
          (ticket creation form, knowledge search) follow the same patterns as the agent workspace.
        </p>
      </div>
    </div>
  );
}