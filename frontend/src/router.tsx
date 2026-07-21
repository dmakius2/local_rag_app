import { createBrowserRouter } from "react-router-dom";
import { ChatPage } from "@/pages/ChatPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

/** A single "/" route for now. Routing is already wired so a future release
 * can add per-conversation routes (e.g. "/chat/:conversationId") for
 * multiple conversations without restructuring the app shell. */
export const router = createBrowserRouter([
  { path: "/", element: <ChatPage /> },
  { path: "*", element: <NotFoundPage /> },
]);
