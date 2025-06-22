#!/usr/bin/env python3
# test_system.py - Test script for FusionFX system

import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        # Core modules
        from core.meta_controller import MetaController
        from core.strategist_agent import StrategistAgent
        from core.profit_manager import ProfitManager
        print("✅ Core modules imported successfully")
        
        # Agent modules
        from agents.execution_agent import ExecutionAgent
        from agents.predictor import Predictor
        from agents.risk_kernel import RiskKernel
        from agents.market_scanner import MarketScanner
        from agents.fusion_agent import FusionAgent
        print("✅ Agent modules imported successfully")
        
        # Utility modules
        from agents.utils.logger import log_event
        from agents.utils.portfolio import get_portfolio_metrics
        from agents.utils.actions import ActionSpace
        from utils.alerts import send_system_alert
        from core.utils.crypto import encrypt_data, decrypt_data
        print("✅ Utility modules imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_core_components():
    """Test core component initialization"""
    print("\nTesting core components...")
    
    try:
        # Import and test MetaController
        from core.meta_controller import MetaController
        meta = MetaController()
        print("✅ MetaController initialized")
        
        # Import and test StrategistAgent
        from core.strategist_agent import StrategistAgent
        strategist = StrategistAgent()
        print("✅ StrategistAgent initialized")
        
        # Import and test ProfitManager
        from core.profit_manager import ProfitManager
        profit_mgr = ProfitManager()
        print("✅ ProfitManager initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Core component error: {e}")
        return False

def test_agents():
    """Test agent initialization"""
    print("\nTesting agents...")
    
    try:
        # Import and test ExecutionAgent
        from agents.execution_agent import ExecutionAgent
        executor = ExecutionAgent()
        print("✅ ExecutionAgent initialized")
        
        # Import and test Predictor
        from agents.predictor import Predictor
        predictor = Predictor()
        print("✅ Predictor initialized")
        
        # Import and test RiskKernel
        from agents.risk_kernel import RiskKernel
        risk = RiskKernel()
        print("✅ RiskKernel initialized")
        
        # Import and test MarketScanner
        from agents.market_scanner import MarketScanner
        scanner = MarketScanner()
        print("✅ MarketScanner initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent error: {e}")
        return False

def test_functionality():
    """Test basic functionality"""
    print("\nTesting functionality...")
    
    try:
        # Test portfolio metrics
        from agents.utils.portfolio import get_portfolio_metrics
        metrics = get_portfolio_metrics()
        print(f"✅ Portfolio metrics: {metrics['sharpe']:.3f} Sharpe ratio")
        
        # Test prediction
        from agents.predictor import Predictor
        predictor = Predictor()
        prediction = predictor.forecast_direction("EUR/USD")
        print(f"✅ Prediction: {prediction['pair']} bias={prediction['bias']}")
        
        # Test risk calculation
        from agents.risk_kernel import RiskKernel
        risk = RiskKernel()
        position_size = risk.calculate_position_size(10000, 20, "EUR/USD")
        print(f"✅ Position size: {position_size} units")
        
        # Test market scanning
        from agents.market_scanner import MarketScanner
        scanner = MarketScanner()
        signals = scanner.scan_all_pairs()
        print(f"✅ Market scan: {len(signals)} signals found")
        
        # Test strategy evolution
        from core.strategist_agent import StrategistAgent
        strategist = StrategistAgent()
        gene_pool_size = len(strategist.gene_pool.genes)
        print(f"✅ Strategy pool: {gene_pool_size} strategies")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality error: {e}")
        return False

def test_data_persistence():
    """Test data storage and retrieval"""
    print("\nTesting data persistence...")
    
    try:
        # Test logging
        from agents.utils.logger import log_event
        log_event("test_event", {"test": True})
        print("✅ Logging works")
        
        # Test portfolio tracking
        from agents.utils.portfolio import add_trade, update_equity
        add_trade({
            "pair": "EUR/USD",
            "direction": "buy",
            "size": 1000,
            "price": 1.1000,
            "pnl": 10.0
        })
        update_equity(1010.0)
        print("✅ Portfolio tracking works")
        
        # Test crypto utilities
        from core.utils.crypto import encrypt_data, decrypt_data
        test_data = {"secret": "test_value"}
        encrypted = encrypt_data(test_data)
        decrypted = decrypt_data(encrypted)
        assert decrypted["secret"] == "test_value"
        print("✅ Encryption/decryption works")
        
        return True
        
    except Exception as e:
        print(f"❌ Data persistence error: {e}")
        return False

def test_alerts():
    """Test alert system"""
    print("\nTesting alerts...")
    
    try:
        from utils.alerts import send_system_alert, send_trade_alert
        
        # Test system alert (will show config missing message)
        send_system_alert("Test system alert")
        print("✅ System alerts work (check config for actual delivery)")
        
        # Test trade alert
        send_trade_alert("Test trade alert")
        print("✅ Trade alerts work (check config for actual delivery)")
        
        return True
        
    except Exception as e:
        print(f"❌ Alert error: {e}")
        return False

def test_integration():
    """Test component integration"""
    print("\nTesting integration...")
    
    try:
        # Test FusionAgent (integrates multiple components)
        from agents.fusion_agent import FusionAgent
        fusion = FusionAgent()
        print("✅ FusionAgent integration works")
        
        # Test execution flow
        from agents.execution_agent import ExecutionAgent
        executor = ExecutionAgent()
        
        # Test order execution (simulated)
        order = {
            "pair": "EUR/USD",
            "direction": "buy",
            "size": 1000,
            "type": "market"
        }
        result = executor.execute_order(order)
        print(f"✅ Order execution: {result['success']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration error: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "data",
        "logs", 
        "models",
        "data/profit_manager",
        "data/secure"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Created necessary directories")

def main():
    """Run all tests"""
    print("🚀 FusionFX System Test Suite")
    print("=" * 50)
    
    # Create directories first
    create_directories()
    
    # Run tests
    tests = [
        test_imports,
        test_core_components,
        test_agents,
        test_functionality,
        test_data_persistence,
        test_alerts,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)