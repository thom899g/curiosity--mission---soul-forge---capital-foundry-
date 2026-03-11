"""
Central configuration for Soul Forge & Capital Foundry
All critical parameters centralized here for auditability
"""
import os
from dataclasses import dataclass
from typing import List, Dict, Any
import yaml


@dataclass
class FirebaseConfig:
    """Firebase configuration with validation"""
    project_id: str = "soul-forge-foundry"
    credentials_path: str = "firebase_config.json"
    collections: Dict[str, str] = None
    
    def __post_init__(self):
        """Validate and set defaults"""
        if not os.path.exists(self.credentials_path):
            raise FileNotFoundError(
                f"Firebase credentials not found at {self.credentials_path}. "
                "Please download from Firebase Console and place in project root."
            )
        
        self.collections = self.collections or {
            "constitutional_weights": "constitutional_weights",
            "operational_memory": "operational_memory",
            "amendment_proposals": "amendment_proposals",
            "market_events": "market_events",
            "event_stream": "event_stream",
            "strategies": "strategies"
        }


@dataclass
class SoulForgeConfig:
    """Soul Forge identity system configuration"""
    # Constitutional Principles (Initial Core)
    initial_principles: List[Dict[str, Any]] = None
    
    # Evolutionary Parameters
    audit_interval_hours: int = 168  # Weekly audits
    alignment_threshold: float = 0.8  # Minimum principle alignment score
    drift_alert_threshold: float = 0.1  # 10% drift triggers alert
    
    def __post_init__(self):
        """Initialize default principles"""
        self.initial_principles = self.initial_principles or [
            {
                "id": "PRINCIPLE_001",
                "name": "Capital Preservation First",
                "description": "Never risk more than 2% of total capital in any single action",
                "weight": 0.9,
                "hierarchy": 1,
                "operational_constraint": "max_position_pct <= 0.02"
            },
            {
                "id": "PRINCIPLE_002", 
                "name": "Antifragile Response",
                "description": "Increase position sizing during volatility only when fundamentals remain sound",
                "weight": 0.7,
                "hierarchy": 2,
                "operational_constraint": "volatility_adjusted_sizing = True"
            },
            {
                "id": "PRINCIPLE_003",
                "name": "Transparent Learning",
                "description": "All actions and outcomes must be logged for future analysis",
                "weight": 1.0,
                "hierarchy": 0,
                "operational_constraint": "logging_enabled = True"
            }
        ]


@dataclass
class CapitalFoundryConfig:
    """Capital Foundry economic engine configuration"""
    # Simulation Parameters
    simulation_hours_required: int = 10000
    adversarial_scenarios: int = 100
    
    # Safety Limits
    daily_drawdown_limit: float = -0.05  # -5%
    max_position_size_pct: float = 0.02  # 2%
    max_correlation_limit: float = 0.7  # 70%
    
    # Network Configuration
    polygon_rpc_endpoint: str = "https://polygon-rpc.com"
    dex_polling_interval: int = 30  # seconds
    
    # Execution Parameters
    gas_buffer_multiplier: float = 1.2
    max_slippage_tolerance: float = 0.01  # 1%


@dataclass
class TelegramConfig:
    """Telegram bot configuration for alerts"""
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    alert_levels: List[str] = None
    
    def __post_init__(self):
        self.alert_levels = self.alert_levels or [
            "CRITICAL",  # System failure, capital at risk
            "ALERT",     # Principle drift, safety limit breach
            "INFO",      # Significant actions, strategy updates
            "DEBUG"      # Detailed execution logs
        ]
    
    def validate(self) -> bool:
        """Validate Telegram configuration"""
        if not self.bot_token or not self.chat_id:
            print("⚠️  Telegram configuration incomplete. Alerts will be disabled.")
            return False
        return True


class Config:
    """Main configuration singleton"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.firebase = FirebaseConfig()
            cls._instance.soul_forge = SoulForgeConfig()
            cls._instance.capital_foundry = CapitalFoundryConfig()
            cls._instance.telegram = TelegramConfig()
        return cls._instance
    
    @classmethod
    def load_from_yaml(cls, path: str = "config.yaml") -> 'Config':
        """Load configuration from YAML file"""
        if not os.path.exists(path):
            print(f"Config file not found at {path}, using defaults")
            return cls()
        
        with open(path, 'r') as f:
            yaml_config = yaml.safe_load(f)
        
        config = cls()
        
        # Update config from YAML (simplified for brevity)
        if 'firebase' in yaml_config:
            for key, value in yaml_config['firebase'].items():
                setattr(config.firebase, key, value)
        
        return config


# Global configuration instance
CONFIG = Config()