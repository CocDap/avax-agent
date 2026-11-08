import { useState, type FormEvent, type ReactNode } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { ComingSoon } from "@/components/coming-soon";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useNetwork } from "@/hooks/use-network";
import { ApiError, api } from "@/lib/api";
import { PAYMENT_DECIMALS } from "@/lib/format";
import type { SettlementMode } from "@/lib/types";

/** Same rule as backend SLUG_PATTERN (agents/schemas.py). */
const SLUG_PATTERN = "^[a-z0-9](?:[a-z0-9-]{1,62}[a-z0-9])?$";

export function NewAgentPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: net } = useNetwork();
  const [mode, setMode] = useState<SettlementMode>("x402");

  const create = useMutation({
    mutationFn: api.agents.create,
    onSuccess: (agent) => {
      queryClient.invalidateQueries({ queryKey: ["agents"] });
      navigate(`/agents/${agent.id}`);
    },
  });

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const f = new FormData(e.currentTarget);
    const price = Number(f.get("price") || 0);
    create.mutate({
      slug: String(f.get("slug")),
      name: String(f.get("name")),
      description: String(f.get("description") ?? ""),
      skills: String(f.get("skills") ?? "")
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
      llm_config: { system_prompt: String(f.get("system_prompt") ?? "") },
      settlement_mode: mode,
      price_atomic: Math.round(price * 10 ** PAYMENT_DECIMALS),
      is_public: f.get("is_public") === "on",
    });
  }

  const err = create.error;

  return (
    <>
      <PageHeader title="Tạo agent" description="Bước 1/3 · config → ví Turnkey → đăng ký ERC-8004." />
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Cấu hình</CardTitle>
          <CardDescription>POST /api/v1/agents</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <Field label="Tên" htmlFor="name">
              <Input id="name" name="name" required maxLength={128} />
            </Field>
            <Field label="Slug (URL A2A: /agents/{slug}/a2a)" htmlFor="slug">
              <Input id="slug" name="slug" required pattern={SLUG_PATTERN} placeholder="my-agent" />
            </Field>
            <Field label="Mô tả" htmlFor="description">
              <Textarea id="description" name="description" />
            </Field>
            <Field label="System prompt" htmlFor="system_prompt">
              <Textarea id="system_prompt" name="system_prompt" rows={4} />
            </Field>
            <Field label="Skills (phân cách bằng dấu phẩy)" htmlFor="skills">
              <Input id="skills" name="skills" placeholder="summarize, translate" />
            </Field>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Settlement" htmlFor="mode">
                <select
                  id="mode"
                  value={mode}
                  onChange={(e) => setMode(e.target.value as SettlementMode)}
                  className="border-input h-9 w-full rounded-md border bg-transparent px-3 text-sm"
                >
                  <option value="x402">x402 (USDC EIP-3009)</option>
                  <option value="erc8183" disabled={!net?.erc8183_enabled}>
                    ERC-8183 escrow{net?.erc8183_enabled ? "" : " (chưa deploy trên Avalanche)"}
                  </option>
                </select>
              </Field>
              <Field label={`Giá mỗi job (${net?.payment_asset ?? "USDC"})`} htmlFor="price">
                <Input id="price" name="price" type="number" min={0} step="0.000001" defaultValue={0} />
              </Field>
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" name="is_public" /> Hiển thị trên Marketplace
            </label>

            {err instanceof ApiError && err.notImplemented && <ComingSoon feature="POST /agents" />}
            {err && !(err instanceof ApiError && err.notImplemented) && (
              <p className="text-destructive text-sm">Lỗi: {err.message}</p>
            )}

            <Button type="submit" disabled={create.isPending}>
              {create.isPending ? "Đang tạo…" : "Tạo agent"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </>
  );
}

function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
    </div>
  );
}
