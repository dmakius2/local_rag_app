import { useEffect, useRef } from "react";

/** Keeps the returned ref pinned to the bottom whenever `dep` changes
 * (e.g. the chat message count), so new messages stay in view. */
export function useAutoScroll<T extends HTMLElement>(dep: unknown): React.RefObject<T> {
  const ref = useRef<T>(null);

  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: "smooth" });
  }, [dep]);

  return ref;
}
