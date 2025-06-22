## Project Overview

FusionFX is an autonomous, AI-driven Forex trading system designed to **compound an initial capital of $300 into $1.5 million within approximately 60 days** under live trading conditions. Beyond this rapid growth phase, the system is architected to **continue generating profits autonomously and sustainably over the next 50 years and beyond**, adapting and evolving to changing market conditions without manual intervention.

This powerful combination of short-term exponential growth and long-term resilience makes FusionFX a truly set-and-forget wealth engine using advanced reinforcement learning, Darwinian strategy evolution, and DAO-governed updates.

---

## 📁 Folder Structure

```
fusionfx-forever/
├── agents/                # Agent logic (strategist, cloud_nomad, etc)
├── core/                  # Meta-controller, profit engine, RL models
├── crew/                  # CrewAI configuration and agent manifest
├── deployment/            # VPS setup and Docker orchestration
├── contracts/             # DAO smart contracts (Solidity)
├── docs/                  # Setup instructions and long-term roadmap
```

---

## 🚀 Quick Start (Demo Mode)

```bash
# 1. Provision a Hetzner VPS (Ubuntu 22.04)
bash deployment/cloud_init_hetzner.sh

# 2. Start all agents with Docker
cd deployment
docker-compose up --detach --scale strategist=3
```

*Note: Demo mode runs with paper trading on OANDA’s demo server.*

---

## 🧠 Core Components

| File | Description |
|------|-------------|
| `meta_controller.py` | RL-powered CEO that learns and adjusts bot behavior autonomously |
| `strategist_agent.py` | Strategy generator that evolves trading logic using genetic algorithms |
| `profit_manager.py` | Handles profit sweeps to crypto exchanges and DeFi vaults |
| `dao_governor.mjs` | Decentralized maintenance execution via blockchain smart contract |
| `cloud_nomad.py` | Detects infrastructure degradation and triggers cloud migration |
| `depin_manager.py` | Connects to DePIN compute networks (e.g., Akash) for decentralized hosting |

---

## 💰 Financial Logic

- **Initial Capital**: $100 (or $300 optionally)
- **Exchange**: OANDA (demo & live)
- **Fallback Broker**: Forex.com
- **Leverage**: Adaptive, risk-weighted based on volatility
- **Currency Pairs**: Starts with EUR/USD, expands autonomously
- **Withdrawals**: Auto-sweeps every time balance ≥ $10,000
- **Destination**: Binance (fallbacks: Kraken, Coinbase)

---

## 🔐 Security & Resilience

- Quantum-resistant key rotation (Kyber-1024 every 90 days)
- MPC wallets with multi-exchange redundancy
- DAO-controlled upgrade approvals
- Dead man's switch → Transfers to DAO if user goes inactive 12+ months
- Geographic wallet sharding: Frankfurt, Singapore, Virginia

---

## 📬 Notification System

| Event | Channel | Requires Manual Action? |
|-------|---------|--------------------------|
| Profit sweep failure | Telegram + SMS | ✅ (optional) |
| Exchange outage | Telegram | ❌ |
| DAO vote pending | Telegram | ❌ |
| Strategy evolution deployed | Email | ❌ |
| Dead man switch timeout | SMS + Email | ✅ |

---

## 🛠️ Deployment Checklist

- [x] OANDA API Key active
- [x] VPS setup on Hetzner (or Akash)
- [x] Binance wallet address linked
- [x] `.env` file created from `.env.sample`
- [x] CrewAI config completed (`fusionfx_crew.yaml`)
- [x] Docker environment built with `docker-compose up`

---

## 🔮 Lifetime Execution Roadmap

| Phase | Years | Objective |
|-------|-------|-----------|
| Boot | 2025–2026 | Launch with 1 strategy, test RL feedback loop |
| Growth | 2026–2029 | Add new pairs, initiate DAO voting, connect to DeFi |
| Expansion | 2030–2035 | Migrate to DePIN, rotate keys, deploy MPC upgrades |
| Legacy | 2036–2075 | Self-manage via DAO, zero-touch trustless performance |

---

## 🧠 Autonomous Intelligence Stack

- **CrewAI Agents**: 11 active agents managing finance, ops, infra, strategy
- **RL Engine**: Deep Q-Network with reward modulation via Sharpe/Sortino blend
- **Genetic Framework**: Strategy evolution every 30–60 days
- **Profit Engine**: Handles exchanges, thresholds, and yield farming integration

---

## 🪙 Supported Exchanges

- **Forex Brokers**: OANDA (primary), Forex.com (fallback)
- **Crypto**: Binance (primary), Kraken & Coinbase (fallbacks)
- **DeFi Vaults**: Aave, EigenLayer, Pendle (for idle capital ≥ $10K)

---

## 📄 Related Docs

- [`50_year_roadmap.pdf`](./50_year_roadmap.pdf) – Phase-by-phase evolution timeline and implementation strategy

## 📁 Folder Structure

```
fusionfx-forever/
├── agents/                # Agent logic (strategist, cloud_nomad, etc)
├── core/                  # Meta-controller, profit engine, RL models
├── crew/                  # CrewAI configuration and agent manifest
├── deployment/            # VPS setup and Docker orchestration
├── contracts/             # DAO smart contracts (Solidity)
├── docs/                  # Setup instructions and long-term roadmap
```

---

## 🚀 Quick Start (Demo Mode)

```bash
# 1. Provision a Hetzner VPS (Ubuntu 22.04)
bash deployment/cloud_init_hetzner.sh

# 2. Start all agents with Docker
cd deployment
docker-compose up --detach --scale strategist=3
```

*Note: Demo mode runs with paper trading on OANDA’s demo server.*

---

## 🧠 Core Components

| File | Description |
|------|-------------|
| `meta_controller.py` | RL-powered CEO that learns and adjusts bot behavior autonomously |
| `strategist_agent.py` | Strategy generator that evolves trading logic using genetic algorithms |
| `profit_manager.py` | Handles profit sweeps to crypto exchanges and DeFi vaults |
| `dao_governor.mjs` | Decentralized maintenance execution via blockchain smart contract |
| `cloud_nomad.py` | Detects infrastructure degradation and triggers cloud migration |
| `depin_manager.py` | Connects to DePIN compute networks (e.g., Akash) for decentralized hosting |

---

## 💰 Financial Logic

- **Initial Capital**: $100 (or $300 optionally)
- **Exchange**: OANDA (demo & live)
- **Fallback Broker**: Forex.com
- **Leverage**: Adaptive, risk-weighted based on volatility
- **Currency Pairs**: Starts with EUR/USD, expands autonomously
- **Withdrawals**: Auto-sweeps every time balance ≥ $10,000
- **Destination**: Binance (fallbacks: Kraken, Coinbase)

---

## 🔐 Security & Resilience

- Quantum-resistant key rotation (Kyber-1024 every 90 days)
- MPC wallets with multi-exchange redundancy
- DAO-controlled upgrade approvals
- Dead man's switch → Transfers to DAO if user goes inactive 12+ months
- Geographic wallet sharding: Frankfurt, Singapore, Virginia

---

## 📬 Notification System

| Event | Channel | Requires Manual Action? |
|-------|---------|--------------------------|
| Profit sweep failure | Telegram + SMS | ✅ (optional) |
| Exchange outage | Telegram | ❌ |
| DAO vote pending | Telegram | ❌ |
| Strategy evolution deployed | Email | ❌ |
| Dead man switch timeout | SMS + Email | ✅ |

---

## 🛠️ Deployment Checklist

- [x] OANDA API Key active
- [x] VPS setup on Hetzner (or Akash)
- [x] Binance wallet address linked
- [x] `.env` file created from `.env.sample`
- [x] CrewAI config completed (`fusionfx_crew.yaml`)
- [x] Docker environment built with `docker-compose up`

---

## 🔮 Lifetime Execution Roadmap

| Phase | Years | Objective |
|-------|-------|-----------|
| Boot | 2025–2026 | Launch with 1 strategy, test RL feedback loop |
| Growth | 2026–2029 | Add new pairs, initiate DAO voting, connect to DeFi |
| Expansion | 2030–2035 | Migrate to DePIN, rotate keys, deploy MPC upgrades |
| Legacy | 2036–2075 | Self-manage via DAO, zero-touch trustless performance |

---

## 🧠 Autonomous Intelligence Stack

- **CrewAI Agents**: 11 active agents managing finance, ops, infra, strategy
- **RL Engine**: Deep Q-Network with reward modulation via Sharpe/Sortino blend
- **Genetic Framework**: Strategy evolution every 30–60 days
- **Profit Engine**: Handles exchanges, thresholds, and yield farming integration

---

## 🪙 Supported Exchanges

- **Forex Brokers**: OANDA (primary), Forex.com (fallback)
- **Crypto**: Binance (primary), Kraken & Coinbase (fallbacks)
- **DeFi Vaults**: Aave, EigenLayer, Pendle (for idle capital ≥ $10K)

---

## 📄 Related Docs

- 📄 [View the 50-Year Autonomy Roadmap](docs/50_year_plan.md) – Phase-by-phase evolution timeline and implementation strategy