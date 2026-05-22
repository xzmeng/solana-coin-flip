# Solana Coin Flip

一个运行在 Solana 上的可证明公平的掷硬币游戏。

## 游戏流程

1. 玩家将任意金额的 SOL 转入庄家地址
2. 后台检测到到账后自动判定输赢
3. **赢**（50% 概率）→ 返还 2× SOL；**输** → 金额归庄家

## 可证明公平原理

采用 **Commit-Reveal（承诺揭露）方案**：

| 时机 | 内容 |
|------|------|
| 启动时 | 生成随机 `server_seed`，公布 `sha256(server_seed)` 作为承诺 |
| 下注时 | 玩家发起转账，链上产生唯一 `tx_signature` |
| 判定时 | `result = sha256(server_seed + ":" + tx_signature)`，首字节 < 128 则赢 |
| 结束时 | 揭露 `server_seed`，任何人可自行验证每局结果 |

玩家验证步骤：
```
uv run coinflip-verify
```
输入揭露的 seed、启动时的 seed hash、以及交易签名，即可独立验证结果。

---

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 生成庄家钱包

```bash
uv run coinflip-new-wallet
```

将输出的私钥填入 `.env`。

### 3. 配置环境

```bash
cp .env.example .env
# 编辑 .env，填入 HOUSE_PRIVATE_KEY
```

### 4. 给庄家钱包充值

**Devnet（测试）：**
```bash
solana airdrop 2 <house-address> --url devnet
```

**Mainnet（正式）：** 直接转入真实 SOL。

### 5. 启动监听

```bash
uv run coinflip
```

启动后会显示庄家地址和 server seed hash。将这两个信息告知玩家，让他们在下注前记录 hash。

---

## 切换网络

只需修改 `.env` 中的 `NETWORK`：

```bash
# 测试网
NETWORK=devnet

# 正式网
NETWORK=mainnet-beta
```

如需使用自定义 RPC 节点（推荐 mainnet 使用），额外设置：
```bash
RPC_URL=https://your-rpc-endpoint.com
```

---

## 配置说明

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `NETWORK` | `devnet` | `devnet` / `testnet` / `mainnet-beta` |
| `RPC_URL` | （由 NETWORK 决定） | 自定义 RPC 端点 |
| `HOUSE_PRIVATE_KEY` | — | Base58 编码的私钥（必填） |
| `MIN_BET_LAMPORTS` | `1000000` | 最小下注额（0.001 SOL） |
| `POLL_INTERVAL_SECONDS` | `5` | 轮询间隔（秒） |

---

## 命令一览

| 命令 | 说明 |
|------|------|
| `uv run coinflip` | 启动监听，开始接受下注 |
| `uv run coinflip-new-wallet` | 生成新钱包 |
| `uv run coinflip-verify` | 验证某局游戏结果 |

## License

MIT
