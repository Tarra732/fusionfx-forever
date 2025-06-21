import random
import logging
from strategies import StrategyGenePool
from backtester import validate_strategy
from deployment import deploy_new_strategy

class StrategistAgent:
    def __init__(self, dna_synthesis=True, max_strategies=5, backtest_validator="monte_carlo"):
        self.dna_synthesis = dna_synthesis
        self.max_strategies = max_strategies
        self.backtest_validator = backtest_validator
        self.gene_pool = StrategyGenePool()

    def evolution_cycle(self):
        logging.info("[StrategistAgent] Starting monthly evolution cycle")

        top_strategies = self.gene_pool.select_top_k(k=self.max_strategies)
        children = self.gene_pool.crossover(top_strategies)

        if self.dna_synthesis:
            logging.info("[StrategistAgent] Performing synthetic DNA mutation")
            children = [self.gene_pool.mutate(child, deep=True) for child in children]

        for candidate in children:
            score = validate_strategy(candidate, method=self.backtest_validator)
            if score >= 0.7:  # Sharpe ratio or other composite metric
                deploy_new_strategy(candidate)
                logging.info(f"[StrategistAgent] ✅ Deployed new strategy with score {score}")
            else:
                logging.warning(f"[StrategistAgent] ❌ Candidate rejected with score {score}")