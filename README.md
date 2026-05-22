# Solana Coin Flip

A simple coin flip game built on Solana.

## Overview

This project implements a provably fair coin flip game on the Solana blockchain. Players can bet SOL on heads or tails, with results determined on-chain.

## Features

- On-chain randomness using recent blockhash
- Instant settlement
- Provably fair results

## Getting Started

### Prerequisites

- [Rust](https://www.rust-lang.org/tools/install)
- [Solana CLI](https://docs.solana.com/cli/install-solana-cli-tools)
- [Anchor](https://www.anchor-lang.com/docs/installation)
- [Node.js](https://nodejs.org/)

### Install

```bash
npm install
```

### Build

```bash
anchor build
```

### Test

```bash
anchor test
```

## License

MIT
