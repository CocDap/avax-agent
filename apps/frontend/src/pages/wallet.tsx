import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/page-header";
import { QueryState } from "@/components/query-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api";
import { formatAtomic, shortAddress } from "@/lib/format";

export function WalletPage() {
  const fees = useQuery({ queryKey: ["billing", "fees"], queryFn: api.billing.fees });
  const summary = useQuery({ queryKey: ["billing", "summary"], queryFn: api.billing.summary });
  const ledger = useQuery({ queryKey: ["billing", "ledger"], queryFn: api.billing.ledger });

  return (
    <>
      <PageHeader
        title="Ví / Thu nhập"
        description="Thu nhập USDC của agent, phí studio và rút tiền."
        actions={<Button disabled>Rút tiền (TODO)</Button>}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Phí studio</CardTitle>
            <CardDescription>GET /api/v1/billing/fees</CardDescription>
          </CardHeader>
          <CardContent>
            <QueryState query={fees} feature="GET /billing/fees">
              {(f) => (
                <div className="space-y-1 text-sm">
                  <p className="text-2xl font-semibold">{f.studio_fee_bps / 100}%</p>
                  <p className="text-muted-foreground">
                    {f.payment_asset} {shortAddress(f.payment_asset_address)} · chain {f.chain_id}
                  </p>
                </div>
              )}
            </QueryState>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Số dư có thể rút</CardTitle>
            <CardDescription>GET /api/v1/billing/summary</CardDescription>
          </CardHeader>
          <CardContent>
            <QueryState query={summary} feature="GET /billing/summary">
              {(s) => (
                <p className="text-2xl font-semibold">{formatAtomic(s.withdrawable_atomic)} USDC</p>
              )}
            </QueryState>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sổ cái</CardTitle>
          <CardDescription>GET /api/v1/billing/ledger</CardDescription>
        </CardHeader>
        <CardContent>
          <QueryState query={ledger} feature="GET /billing/ledger">
            {(rows) => (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Thời gian</TableHead>
                    <TableHead>Loại</TableHead>
                    <TableHead>Số tiền</TableHead>
                    <TableHead>Tx</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((e) => (
                    <TableRow key={e.id}>
                      <TableCell>{new Date(e.created_at).toLocaleString()}</TableCell>
                      <TableCell>{e.kind}</TableCell>
                      <TableCell>
                        {formatAtomic(e.amount_atomic)} {e.asset}
                      </TableCell>
                      <TableCell className="font-mono text-xs">{shortAddress(e.tx_hash)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </QueryState>
        </CardContent>
      </Card>
    </>
  );
}
