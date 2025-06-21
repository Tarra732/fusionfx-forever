# core/meta_controller.py

import numpy as np
from agents.utils.portfolio import get_portfolio_metrics
from agents.utils.logger import log_event
from agents.utils.actions import ActionSpace
from agents.models.q_network import DeepQNetwork
import time

class MetaController:
    def __init__(self):
        self.q_network = DeepQNetwork(input_dim=12, output_dim=8)
        self.action_space = ActionSpace({
            "risk_appetite": [0.05, 0.1, 0.2, 0.3],
            "pair_expansion": [0, 1, 2],
            "retrain_frequency": [7, 14, 30],
            "leverage_tuning": [10, 20, 30, 50],
            "execution_style": ["limit", "market"],
        })
        self.state_window = []
        self.gamma = 0.98
        self.exploration_rate = 0.05

    def get_state(self):
        metrics = get_portfolio_metrics()
        state = np.array([
            metrics['sharpe'],
            metrics['sortino'],
            metrics['drawdown'],
            metrics['vix'],
            metrics['equity_curve'][-1] - metrics['equity_curve'][0],
            len(metrics['active_pairs']),
            int(metrics['is_trending']),
            metrics['win_rate'],
            metrics['avg_return'],
            metrics['volatility'],
            metrics['trade_frequency'],
            time.time() % (3600 * 24) / (3600 * 24)  # time of day (normalized)
        ])
        return state

    def compute_reward(self, state):
        sharpe = state[0]
        sortino = state[1]
        dd_penalty = state[2]
        reward = sharpe * 0.6 + sortino * 0.4 - dd_penalty * 0.3
        return reward

    def decide_and_execute(self):
        state = self.get_state()
        action_idx = self.q_network.predict(state)

        if np.random.rand() < self.exploration_rate:
            action_idx = np.random.randint(self.action_space.size)

        action = self.action_space.decode(action_idx)
        reward = self.compute_reward(state)

        # Log action and reward
        log_event("meta_controller_action", {"action": action, "reward": reward})

        # Execute decision (pseudo-code, will call respective APIs)
        self.adjust_risk(action["risk_appetite"])
        self.expand_pairs(action["pair_expansion"])
        self.set_retrain_schedule(action["retrain_frequency"])
        self.tune_leverage(action["leverage_tuning"])
        self.switch_execution_mode(action["execution_style"])

        # Train Q-network
        next_state = self.get_state()
        self.q_network.train(state, action_idx, reward, next_state, self.gamma)

    def adjust_risk(self, risk_level):
        log_event("risk_update", {"new_risk": risk_level})
        # TODO: Connect to RiskKernel agent

    def expand_pairs(self, new_pairs_count):
        log_event("pair_expansion", {"count": new_pairs_count})
        # TODO: Notify StrategistAgent to add new pairs

    def set_retrain_schedule(self, days):
        log_event("model_retrain", {"interval_days": days})
        # TODO: Trigger predictor schedule

    def tune_leverage(self, leverage):
        log_event("leverage_tuned", {"new_leverage": leverage})
        # TODO: Update Compliance agent or broker settings

    def switch_execution_mode(self, mode):
        log_event("execution_style", {"mode": mode})
        # TODO: Update ExecutionAgent parameters


if __name__ == "__main__":
    meta = MetaController()
    while True:
        meta.decide_and_execute()
        time.sleep(3600)  # Run hourly decisions