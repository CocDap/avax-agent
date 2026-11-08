import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

/** Chain + contract info from the control plane (`GET /api/v1/network`). */
export function useNetwork() {
  return useQuery({ queryKey: ["network"], queryFn: api.network, staleTime: Infinity });
}
