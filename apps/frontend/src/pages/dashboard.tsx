import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { QueryState } from "@/components/query-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useNetwork } from "@/hooks/use-network";
import { api } from "@/lib/api";
import { formatAtomic, shortAddress } from "@/lib/format";

export function DashboardPage() {
  const network = useNetwork();
  const summary = useQuery({ queryKey: ["billing", "summary"], queryFn: api.billing.summary });

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Tạo, đăng ký và vận hành AI agent trên Avalanche C-Chain."
        actions={
          <Button asChild>
            <Link to="/agents/new">
              <Plus /> Tạo agent
            </Link>
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Network</CardTitle>
          <CardDescription>GET /api/v1/network</CardDescription>
        </CardHeader>
        <CardContent>
          <QueryState query={network} feature="GET /network">
            {(n) => (
              <dl className="grid gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
                <Item k="Network" v={`${n.network} (${n.chain_id})`} />
                <Item k="Identity Registry (ERC-8004)" v={shortAddress(n.identity_registry)} />
                <Item k="Payment asset" v={`${n.payment_asset} ${shortAddress(n.payment_asset_address)}`} />
                <Item k="Settlement" v={n.erc8183_enabled ? "x402 + ERC-8183" : "x402 (USDC EIP-3009)"} />
              </dl>
            )}
          </QueryState>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Thu nhập</CardTitle>
          <CardDescription>GET /api/v1/billing/summary</CardDescription>
        </CardHeader>
        <CardContent>
          <QueryState query={summary} feature="GET /billing/summary">
            {(s) => (
              <div className="grid gap-4 sm:grid-cols-4">
                <Stat label="Gross" value={formatAtomic(s.gross_income_atomic)} />
                <Stat label="Phí studio" value={formatAtomic(s.studio_fees_atomic)} />
                <Stat label="Đã rút" value={formatAtomic(s.paid_out_atomic)} />
                <Stat label="Có thể rút" value={formatAtomic(s.withdrawable_atomic)} />
              </div>
            )}
          </QueryState>
        </CardContent>
      </Card>
    </>
  );
}

function Item({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-4 border-b py-1.5">
      <dt className="text-muted-foreground">{k}</dt>
      <dd className="font-mono text-xs">{v}</dd>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-muted-foreground text-xs">{label}</p>
      <p className="text-xl font-semibold">{value}</p>
    </div>
  );
}
