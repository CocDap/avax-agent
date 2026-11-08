# contracts/ (placeholder)

Bộ hợp đồng ERC-8183 (**AgenticCommerce**, **EvaluatorRouter**, **OptimisticPolicy**) hiện **chưa được deploy trên Avalanche C-Chain**. Nếu studio muốn dùng thanh toán escrow (`SettlementMode.ERC8183`) thay cho x402, studio phải tự deploy các hợp đồng này.

## Việc cần làm (TODO)

1. Lấy source contract từ upstream (BNB Chain / ERC-8183 reference implementation) và đưa vào đây, dùng Foundry hoặc Hardhat.
2. Cấu hình:
   - Payment token: USDC Fuji `0x5425890298aed601595a70AB815c96711a31Bc65`, hoặc USDC mainnet `0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E`.
   - Bỏ phần phụ thuộc MegaFuel/paymaster vì Avalanche không có.
3. Deploy lên Fuji (43113) trước, verify trên Snowtrace.
4. Đặt các biến môi trường cho backend: `COMMERCE_ADDRESS`, `ROUTER_ADDRESS`, `POLICY_ADDRESS`, `INDEXER_START_BLOCK` (block deploy).
5. Kiểm tra ABI trong `apps/backend/app/chain/abis/` khớp với bytecode đã deploy.

Trước khi làm xong các bước này, `settings.commerce_enabled == False`: indexer bỏ qua stream `erc8183.jobs`, settle bot không gọi `router.settle()`, và frontend khóa lựa chọn ERC-8183.
