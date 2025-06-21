# agents/compliance.py

import requests
import time

class ComplianceAgent:
    def __init__(self, rule_sources=None):
        self.rule_sources = rule_sources or ["esma_rss_feed", "nfa_database"]
        self.current_leverage = 50  # default

    def fetch_esma_rules(self):
        # Simulated ESMA feed lookup
        try:
            return {
                "EUR/USD": {"max_leverage": 30},
                "crypto": {"max_leverage": 2}
            }
        except Exception as e:
            print(f"Error fetching ESMA rules: {e}")
            return {}

    def fetch_nfa_rules(self):
        # Simulated NFA rule lookup
        try:
            return {
                "EUR/USD": {"max_leverage": 50},
                "gold": {"max_leverage": 20}
            }
        except Exception as e:
            print(f"Error fetching NFA rules: {e}")
            return {}

    def resolve_leverage(self, asset):
        rules = {}
        if "esma_rss_feed" in self.rule_sources:
            rules.update(self.fetch_esma_rules())
        if "nfa_database" in self.rule_sources:
            rules.update(self.fetch_nfa_rules())

        if asset in rules:
            max_leverage = rules[asset]["max_leverage"]
            self.current_leverage = min(self.current_leverage, max_leverage)
        return self.current_leverage

    def enforce(self, asset):
        allowed_leverage = self.resolve_leverage(asset)
        print(f"Enforced max leverage for {asset}: {allowed_leverage}x")
        return allowed_leverage

# Example usage
if __name__ == "__main__":
    compliance = ComplianceAgent()
    compliance.enforce("EUR/USD")