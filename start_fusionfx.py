#!/usr/bin/env python3
# start_fusionfx.py - Main startup script for FusionFX autonomous trading system

import sys
import os
import time
import threading
import signal
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.utils.logger import log_event
from utils.alerts import send_system_alert, send_critical_alert

class FusionFXSystem:
    """Main system orchestrator for FusionFX"""
    
    def __init__(self):
        self.agents = {}
        self.running = False
        self.startup_time = datetime.utcnow()
        
        # Create necessary directories
        self._create_directories()
        
        log_event("fusionfx_system_initializing", {
            "startup_time": self.startup_time.isoformat(),
            "python_version": sys.version,
            "working_directory": os.getcwd()
        })
    
    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            "data", "logs", "models", "data/profit_manager", 
            "data/secure", "data/strategies", "data/trades"
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def _start_agent(self, agent_name, agent_class, *args, **kwargs):
        """Start an individual agent in a separate thread"""
        try:
            agent = agent_class(*args, **kwargs)
            self.agents[agent_name] = {
                "instance": agent,
                "thread": None,
                "status": "initialized"
            }
            
            # Start agent in separate thread
            thread = threading.Thread(
                target=self._run_agent,
                args=(agent_name, agent),
                daemon=True
            )
            thread.start()
            
            self.agents[agent_name]["thread"] = thread
            self.agents[agent_name]["status"] = "running"
            
            log_event("agent_started", {"agent": agent_name})
            print(f"✅ Started {agent_name}")
            
            return True
            
        except Exception as e:
            log_event("agent_start_error", {"agent": agent_name, "error": str(e)})
            print(f"❌ Failed to start {agent_name}: {e}")
            return False
    
    def _run_agent(self, agent_name, agent):
        """Run an agent with error handling"""
        try:
            if hasattr(agent, 'run'):
                agent.run()
            else:
                log_event("agent_no_run_method", {"agent": agent_name})
        except Exception as e:
            log_event("agent_runtime_error", {"agent": agent_name, "error": str(e)})
            self.agents[agent_name]["status"] = "error"
            send_critical_alert(f"Agent {agent_name} crashed: {str(e)}")
    
    def start_core_agents(self):
        """Start the core trading agents"""
        print("🚀 Starting FusionFX Core Agents...")
        
        # Import agents
        from core.meta_controller import MetaController
        from core.strategist_agent import StrategistAgent
        from core.profit_manager import ProfitManager
        from agents.execution_agent import ExecutionAgent
        from agents.predictor import Predictor
        from agents.risk_kernel import RiskKernel
        from agents.market_scanner import MarketScanner
        
        # Start agents in order of importance
        agents_to_start = [
            ("risk_kernel", RiskKernel),
            ("execution_agent", ExecutionAgent),
            ("predictor", Predictor),
            ("market_scanner", MarketScanner),
            ("strategist", StrategistAgent),
            ("profit_manager", ProfitManager),
            ("meta_controller", MetaController)
        ]
        
        started_count = 0
        for agent_name, agent_class in agents_to_start:
            if self._start_agent(agent_name, agent_class):
                started_count += 1
            time.sleep(2)  # Brief pause between starts
        
        print(f"✅ Started {started_count}/{len(agents_to_start)} core agents")
        return started_count == len(agents_to_start)
    
    def start_fusion_agent(self):
        """Start the main fusion agent that coordinates trading"""
        print("🔥 Starting FusionFX Trading Agent...")
        
        try:
            from agents.fusion_agent import FusionAgent
            
            # Start fusion agent
            if self._start_agent("fusion_agent", FusionAgent):
                print("✅ FusionFX Trading Agent started")
                return True
            else:
                print("❌ Failed to start FusionFX Trading Agent")
                return False
                
        except Exception as e:
            print(f"❌ Error starting FusionFX Trading Agent: {e}")
            return False
    
    def monitor_system(self):
        """Monitor system health and agent status"""
        print("📊 Starting system monitoring...")
        
        while self.running:
            try:
                # Check agent health
                healthy_agents = 0
                total_agents = len(self.agents)
                
                for agent_name, agent_info in self.agents.items():
                    thread = agent_info["thread"]
                    if thread and thread.is_alive():
                        healthy_agents += 1
                        agent_info["status"] = "running"
                    else:
                        agent_info["status"] = "stopped"
                        log_event("agent_stopped", {"agent": agent_name})
                
                # Log system status
                uptime = datetime.utcnow() - self.startup_time
                log_event("system_health_check", {
                    "healthy_agents": healthy_agents,
                    "total_agents": total_agents,
                    "uptime_seconds": uptime.total_seconds(),
                    "agent_status": {name: info["status"] for name, info in self.agents.items()}
                })
                
                # Send alert if agents are failing
                if healthy_agents < total_agents * 0.8:  # Less than 80% healthy
                    send_critical_alert(f"System health degraded: {healthy_agents}/{total_agents} agents running")
                
                # Sleep for 5 minutes
                time.sleep(300)
                
            except Exception as e:
                log_event("monitor_error", {"error": str(e)})
                time.sleep(60)
    
    def start(self):
        """Start the complete FusionFX system"""
        print("🌟 FusionFX Autonomous Trading System")
        print("=" * 50)
        
        self.running = True
        
        # Send startup notification
        send_system_alert("🚀 FusionFX System starting up...")
        
        # Start core agents
        if not self.start_core_agents():
            print("❌ Failed to start core agents. Aborting.")
            return False
        
        # Start fusion trading agent
        if not self.start_fusion_agent():
            print("❌ Failed to start trading agent. Aborting.")
            return False
        
        # Start system monitoring
        monitor_thread = threading.Thread(target=self.monitor_system, daemon=True)
        monitor_thread.start()
        
        # System is now running
        print("\n🎉 FusionFX System is now LIVE!")
        print("📈 Autonomous trading has begun...")
        print("📊 Monitor logs in the 'logs' directory")
        print("💰 Profit sweeps will occur automatically when thresholds are met")
        print("\nPress Ctrl+C to stop the system")
        
        send_system_alert("✅ FusionFX System is LIVE and trading autonomously!")
        
        log_event("fusionfx_system_started", {
            "agents_running": len(self.agents),
            "startup_duration": (datetime.utcnow() - self.startup_time).total_seconds()
        })
        
        return True
    
    def stop(self):
        """Stop the FusionFX system"""
        print("\n🛑 Stopping FusionFX System...")
        
        self.running = False
        
        # Log shutdown
        log_event("fusionfx_system_stopping", {
            "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds(),
            "agents_to_stop": len(self.agents)
        })
        
        send_system_alert("🛑 FusionFX System shutting down...")
        
        # Wait for threads to finish (with timeout)
        for agent_name, agent_info in self.agents.items():
            thread = agent_info["thread"]
            if thread and thread.is_alive():
                print(f"⏳ Waiting for {agent_name} to stop...")
                thread.join(timeout=10)
        
        print("✅ FusionFX System stopped")
        send_system_alert("✅ FusionFX System stopped safely")
        
        log_event("fusionfx_system_stopped", {
            "total_uptime": (datetime.utcnow() - self.startup_time).total_seconds()
        })

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n📡 Received signal {signum}")
    if 'fusion_system' in globals():
        fusion_system.stop()
    sys.exit(0)

def main():
    """Main entry point"""
    global fusion_system
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Create and start the system
        fusion_system = FusionFXSystem()
        
        if fusion_system.start():
            # Keep the main thread alive
            while fusion_system.running:
                time.sleep(1)
        else:
            print("❌ Failed to start FusionFX System")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⌨️  Keyboard interrupt received")
        if 'fusion_system' in locals():
            fusion_system.stop()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        log_event("fatal_error", {"error": str(e)})
        send_critical_alert(f"Fatal system error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()