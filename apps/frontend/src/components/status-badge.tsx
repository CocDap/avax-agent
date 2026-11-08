import { Badge } from "@/components/ui/badge";
import type { AgentStatus, JobStatus } from "@/lib/types";

const VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  active: "default",
  settled: "default",
  failed: "destructive",
  refunded: "destructive",
  paused: "outline",
  draft: "outline",
};

export function StatusBadge({ status }: { status: AgentStatus | JobStatus }) {
  return <Badge variant={VARIANT[status] ?? "secondary"}>{status}</Badge>;
}
