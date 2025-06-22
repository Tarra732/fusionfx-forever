# core/strategist_agent.py

import random
import logging
import numpy as np
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.utils.logger import log_event
from utils.alerts import send_system_alert

class StrategyGene:
    """Individual strategy gene with parameters"""
    
    def __init__(self, params=None):
        if params is None:
            self.params = self.generate_random_params()
        else:
            self.params = params
        
        self.fitness = 0.0
        self.age = 0
        self.trades_executed = 0
        self.sharpe_ratio = 0.0
        self.max_drawdown = 0.0
    
    def generate_random_params(self):
        """Generate random strategy parameters"""
        return {
            "timeframe": random.choice(["15M", "1H", "4H", "1D"]),
            "ma_fast": random.randint(5, 20),
            "ma_slow": random.randint(21, 100),
            "rsi_period": random.randint(10, 30),
            "rsi_oversold": random.randint(20, 35),
            "rsi_overbought": random.randint(65, 80),
            "stop_loss": random.uniform(0.005, 0.02),  # 0.5% to 2%
            "take_profit": random.uniform(0.01, 0.05),  # 1% to 5%
            "risk_per_trade": random.uniform(0.01, 0.05),  # 1% to 5%
            "max_positions": random.randint(1, 5),
            "trend_filter": random.choice([True, False]),
            "volatility_filter": random.choice([True, False]),
            "news_filter": random.choice([True, False])
        }
    
    def mutate(self, mutation_rate=0.1):
        """Mutate strategy parameters"""
        new_params = self.params.copy()
        
        for key, value in new_params.items():
            if random.random() < mutation_rate:
                if key == "timeframe":
                    new_params[key] = random.choice(["15M", "1H", "4H", "1D"])
                elif key in ["ma_fast", "ma_slow", "rsi_period"]:
                    new_params[key] = max(1, int(value + random.gauss(0, value * 0.2)))
                elif key in ["rsi_oversold", "rsi_overbought"]:
                    new_params[key] = max(0, min(100, int(value + random.gauss(0, 5))))
                elif key in ["stop_loss", "take_profit", "risk_per_trade"]:
                    new_params[key] = max(0.001, value + random.gauss(0, value * 0.3))
                elif key == "max_positions":
                    new_params[key] = max(1, min(10, int(value + random.gauss(0, 1))))
                elif key in ["trend_filter", "volatility_filter", "news_filter"]:
                    new_params[key] = random.choice([True, False])
        
        return StrategyGene(new_params)

class StrategyGenePool:
    """Pool of strategy genes for evolution"""
    
    def __init__(self, pool_size=20):
        self.pool_size = pool_size
        self.genes = []
        self.generation = 0
        self.data_file = Path("data/strategy_pool.json")
        self.data_file.parent.mkdir(exist_ok=True)
        
        self.load_pool()
        
        # Initialize pool if empty
        if not self.genes:
            self.initialize_pool()
    
    def initialize_pool(self):
        """Initialize the gene pool with random strategies"""
        self.genes = [StrategyGene() for _ in range(self.pool_size)]
        log_event("strategy_pool_initialized", {"pool_size": self.pool_size})
    
    def save_pool(self):
        """Save the gene pool to disk"""
        pool_data = {
            "generation": self.generation,
            "genes": [
                {
                    "params": gene.params,
                    "fitness": gene.fitness,
                    "age": gene.age,
                    "trades_executed": gene.trades_executed,
                    "sharpe_ratio": gene.sharpe_ratio,
                    "max_drawdown": gene.max_drawdown
                }
                for gene in self.genes
            ]
        }
        
        with open(self.data_file, "w") as f:
            json.dump(pool_data, f, indent=2)
    
    def load_pool(self):
        """Load the gene pool from disk"""
        if self.data_file.exists():
            try:
                with open(self.data_file, "r") as f:
                    pool_data = json.load(f)
                
                self.generation = pool_data.get("generation", 0)
                self.genes = []
                
                for gene_data in pool_data.get("genes", []):
                    gene = StrategyGene(gene_data["params"])
                    gene.fitness = gene_data.get("fitness", 0.0)
                    gene.age = gene_data.get("age", 0)
                    gene.trades_executed = gene_data.get("trades_executed", 0)
                    gene.sharpe_ratio = gene_data.get("sharpe_ratio", 0.0)
                    gene.max_drawdown = gene_data.get("max_drawdown", 0.0)
                    self.genes.append(gene)
                
                log_event("strategy_pool_loaded", {"generation": self.generation, "genes": len(self.genes)})
            except Exception as e:
                log_event("strategy_pool_load_error", {"error": str(e)})
    
    def select_top_k(self, k=5):
        """Select top k strategies by fitness"""
        sorted_genes = sorted(self.genes, key=lambda g: g.fitness, reverse=True)
        return sorted_genes[:k]
    
    def crossover(self, parent_genes):
        """Create offspring through crossover"""
        children = []
        
        for i in range(len(parent_genes)):
            for j in range(i + 1, len(parent_genes)):
                parent1, parent2 = parent_genes[i], parent_genes[j]
                
                # Create child by mixing parameters
                child_params = {}
                for key in parent1.params:
                    if random.random() < 0.5:
                        child_params[key] = parent1.params[key]
                    else:
                        child_params[key] = parent2.params[key]
                
                child = StrategyGene(child_params)
                children.append(child)
        
        return children
    
    def evolve(self):
        """Perform one evolution cycle"""
        self.generation += 1
        
        # Select top performers
        top_genes = self.select_top_k(k=self.pool_size // 4)
        
        # Create offspring
        children = self.crossover(top_genes)
        
        # Mutate offspring
        mutated_children = [child.mutate() for child in children]
        
        # Add some random new genes for diversity
        random_genes = [StrategyGene() for _ in range(self.pool_size // 10)]
        
        # Combine and select new population
        all_candidates = top_genes + mutated_children + random_genes
        
        # Keep best genes and fill with new ones
        self.genes = sorted(all_candidates, key=lambda g: g.fitness, reverse=True)[:self.pool_size]
        
        # Age all genes
        for gene in self.genes:
            gene.age += 1
        
        self.save_pool()
        
        log_event("strategy_evolution", {
            "generation": self.generation,
            "top_fitness": self.genes[0].fitness if self.genes else 0,
            "avg_fitness": np.mean([g.fitness for g in self.genes]) if self.genes else 0
        })

class StrategistAgent:
    """Main strategist agent that evolves trading strategies"""
    
    def __init__(self, dna_synthesis=True, max_strategies=5, evolution_interval_days=30):
        self.dna_synthesis = dna_synthesis
        self.max_strategies = max_strategies
        self.evolution_interval_days = evolution_interval_days
        self.gene_pool = StrategyGenePool()
        self.last_evolution = datetime.utcnow()
        
        log_event("strategist_initialized", {
            "dna_synthesis": dna_synthesis,
            "max_strategies": max_strategies,
            "evolution_interval_days": evolution_interval_days
        })
    
    def should_evolve(self):
        """Check if it's time for evolution"""
        time_since_evolution = datetime.utcnow() - self.last_evolution
        return time_since_evolution.days >= self.evolution_interval_days
    
    def validate_strategy(self, gene, method="sharpe_ratio"):
        """Validate a strategy using backtesting or simulation"""
        # Simplified validation - in real implementation, this would run backtests
        
        # Simulate some performance metrics
        base_score = random.uniform(0.3, 1.2)  # Base Sharpe ratio
        
        # Penalize extreme parameters
        penalties = 0
        if gene.params["stop_loss"] > 0.015:  # Too high stop loss
            penalties += 0.1
        if gene.params["risk_per_trade"] > 0.03:  # Too high risk
            penalties += 0.2
        if gene.params["ma_fast"] >= gene.params["ma_slow"]:  # Invalid MA setup
            penalties += 0.5
        
        final_score = max(0, base_score - penalties)
        
        # Update gene metrics
        gene.fitness = final_score
        gene.sharpe_ratio = final_score
        gene.max_drawdown = random.uniform(0.05, 0.25)
        gene.trades_executed += random.randint(10, 100)
        
        return final_score
    
    def deploy_strategy(self, gene):
        """Deploy a validated strategy"""
        strategy_data = {
            "id": f"strategy_{int(time.time())}",
            "params": gene.params,
            "fitness": gene.fitness,
            "deployed_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        # Save strategy to deployment file
        strategies_file = Path("data/deployed_strategies.json")
        strategies_file.parent.mkdir(exist_ok=True)
        
        if strategies_file.exists():
            with open(strategies_file, "r") as f:
                strategies = json.load(f)
        else:
            strategies = []
        
        strategies.append(strategy_data)
        
        # Keep only the latest strategies
        strategies = strategies[-self.max_strategies:]
        
        with open(strategies_file, "w") as f:
            json.dump(strategies, f, indent=2)
        
        log_event("strategy_deployed", strategy_data)
        send_system_alert(f"New strategy deployed with fitness {gene.fitness:.3f}")
        
        return True
    
    def evolution_cycle(self):
        """Perform one complete evolution cycle"""
        log_event("evolution_cycle_start", {"generation": self.gene_pool.generation})
        send_system_alert("Starting strategy evolution cycle...")
        
        # Evolve the gene pool
        self.gene_pool.evolve()
        
        # Get top candidates
        top_candidates = self.gene_pool.select_top_k(k=self.max_strategies * 2)
        
        deployed_count = 0
        for candidate in top_candidates:
            score = self.validate_strategy(candidate)
            
            if score >= 0.7:  # Minimum fitness threshold
                if self.deploy_strategy(candidate):
                    deployed_count += 1
                    log_event("strategy_accepted", {
                        "fitness": score,
                        "params": candidate.params
                    })
                
                if deployed_count >= self.max_strategies:
                    break
            else:
                log_event("strategy_rejected", {
                    "fitness": score,
                    "params": candidate.params
                })
        
        self.last_evolution = datetime.utcnow()
        
        log_event("evolution_cycle_complete", {
            "deployed_strategies": deployed_count,
            "generation": self.gene_pool.generation
        })
        
        send_system_alert(f"Evolution cycle complete. Deployed {deployed_count} new strategies.")
    
    def run(self):
        """Main run loop for the strategist agent"""
        log_event("strategist_started", {})
        send_system_alert("Strategist Agent started")
        
        while True:
            try:
                if self.should_evolve():
                    self.evolution_cycle()
                
                # Sleep for 1 hour before checking again
                time.sleep(3600)
                
            except Exception as e:
                log_event("strategist_error", {"error": str(e)})
                send_system_alert(f"Strategist error: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    strategist = StrategistAgent()
    strategist.run()