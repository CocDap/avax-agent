import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/page-header";
import { QueryState } from "@/components/query-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { formatAtomic } from "@/lib/format";

export function MarketplacePage() {
  const [q, setQ] = useState("");
  const agents = useQuery({ queryKey: ["marketplace", q], queryFn: () => api.marketplace(q) });

  return (
    <>
      <PageHeader
        title="Marketplace"
        description="Agent public, gọi qua A2A gateway và trả phí bằng x402."
        actions={
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Tìm agent…"
            className="w-64"
          />
        }
      />
      <QueryState query={agents} feature="GET /marketplace/agents">
        {(rows) => (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {rows.map((a) => (
              <Card key={a.slug}>
                <CardHeader>
                  <CardTitle>{a.name}</CardTitle>
                  <CardDescription>{a.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex flex-wrap gap-1">
                    {a.skills.map((s) => (
                      <Badge key={s} variant="secondary">
                        {s}
                      </Badge>
                    ))}
                  </div>
                  <p>
                    {formatAtomic(a.price_atomic)} USDC · {a.settlement_mode}
                  </p>
                  <a href={a.agent_card_url} className="text-primary text-xs hover:underline">
                    agent-card.json
                  </a>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </QueryState>
    </>
  );
}
