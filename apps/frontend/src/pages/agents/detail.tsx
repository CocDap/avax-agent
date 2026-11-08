import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import { PageHeader } from "@/components/page-header";
import { QueryState } from "@/components/query-state";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { formatAtomic, shortAddress } from "@/lib/format";

export function AgentDetailPage() {
  const { id = "" } = useParams();
  const agent = useQuery({ queryKey: ["agents", id], queryFn: () => api.agents.get(id) });
  const wallet = useQuery({ queryKey: ["agents", id, "wallet"], queryFn: () => api.agents.wallet(id) });
  const registration = useQuery({
    queryKey: ["agents", id, "registration"],
    queryFn: () => api.agents.registration(id),
  });

  return (
    <>
      <PageHeader title="Agent" description={id} />

      <Card>
        <CardHeader>
          <CardTitle>Config</CardTitle>
          <CardDescription>GET /api/v1/agents/{"{id}"}</CardDescription>
        </CardHeader>
        <CardContent>
          <QueryState query={agent} feature="GET /agents/{id}">
            {(a) => (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold">{a.name}</span>
                  <StatusBadge status={a.status} />
                </div>
                <p className="text-muted-foreground">{a.description}</p>
                <p>
                  {a.settlement_mode} · {formatAtomic(a.price_atomic)} USDC · model {a.llm_config.model}
                </p>
              </div>
            )}
          </QueryState>
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Ví (Turnkey sub-org)</CardTitle>
            <CardDescription>GET /api/v1/agents/{"{id}"}/wallet</CardDescription>
          </CardHeader>
          <CardContent>
            <QueryState query={wallet} feature="GET /agents/{id}/wallet">
              {(w) => (
                <div className="space-y-1 text-sm">
                  <p className="font-mono">{shortAddress(w.address)}</p>
                  <p className="text-muted-foreground">
                    Cap/call {formatAtomic(w.policy.max_value_per_call_atomic)} · Budget/ngày{" "}
                    {formatAtomic(w.policy.daily_budget_atomic)} USDC
                  </p>
                </div>
              )}
            </QueryState>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>ERC-8004 identity</CardTitle>
            <CardDescription>GET /api/v1/agents/{"{id}"}/registration</CardDescription>
          </CardHeader>
          <CardContent>
            <QueryState query={registration} feature="GET /agents/{id}/registration">
              {(r) => (
                <div className="space-y-1 text-sm">
                  <p>
                    {r.state} {r.erc8004_agent_id != null && `· #${r.erc8004_agent_id}`}
                  </p>
                  <p className="text-muted-foreground font-mono text-xs">{r.agent_uri ?? "—"}</p>
                </div>
              )}
            </QueryState>
          </CardContent>
        </Card>
      </div>
    </>
  );
}
