import { RouterProvider } from "react-router-dom";
import { router } from "@/router";
import { useHealthPolling } from "@/hooks";

export function App() {
  useHealthPolling();
  return <RouterProvider router={router} />;
}
