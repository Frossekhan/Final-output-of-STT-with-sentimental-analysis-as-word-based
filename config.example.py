"""
Configuration File for Sales Intelligence Platform
Copy this to config.py and customize for your deployment
"""

import os
from typing import Dict, List

# ============================================================================
# SERVER CONFIGURATION
# ============================================================================

class ServerConfig:
    """FastAPI server configuration"""
    
    # Server host and port
    HOST = "0.0.0.0"
    PORT = 8000
    
    # CORS settings
    CORS_ORIGINS = ["*"]
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]
    
    # Logging
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE = "sales-intelligence.log"
    
    # WebSocket settings
    WEBSOCKET_MAX_CONNECTIONS = 100
    WEBSOCKET_HEARTBEAT_INTERVAL = 30  # seconds
    SESSION_TIMEOUT = 3600  # 1 hour
    
    # HTTPS/SSL (optional)
    USE_HTTPS = False
    SSL_KEYFILE = None
    SSL_CERTFILE = None
    
    # Rate limiting
    RATE_LIMIT_ENABLED = False
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_PERIOD = 60  # seconds

# ============================================================================
# AUDIO CONFIGURATION
# ============================================================================

class AudioConfig:
    """Audio capture and processing configuration"""
    
    # Sample rate (Hz)
    SAMPLE_RATE = 16000  # 16kHz standard for Whisper
    
    # Chunk settings
    CHUNK_DURATION = 2.0  # seconds per chunk
    CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
    
    # Audio format
    CHANNELS = 1  # mono
    DTYPE = 'float32'
    
    # Audio preprocessing
    NORMALIZE_AUDIO = True
    REMOVE_SILENCE = False
    SILENCE_THRESHOLD = -40  # dB
    
    # Compression (if needed)
    ENABLE_COMPRESSION = False
    COMPRESSION_LEVEL = 9

# ============================================================================
# SPEECH-TO-TEXT CONFIGURATION
# ============================================================================

class WhisperConfig:
    """Faster-Whisper model configuration"""
    
    # Model size
    MODEL_SIZE = "base"  # tiny, base, small, medium, large
    
    # Device and compute type
    DEVICE = "auto"  # auto, cpu, cuda
    COMPUTE_TYPE = "int8"  # float32, float16, int8
    
    # Model parameters
    LANGUAGE = None  # None for auto-detect
    TASK = "transcribe"  # transcribe or translate
    
    # Beam search settings
    BEAM_SIZE = 5
    BEST_OF = 5
    PATIENCE = 1.0
    TEMPERATURE = 0.0
    
    # Thresholds
    COMPRESSION_RATIO_THRESHOLD = 2.4
    NO_SPEECH_THRESHOLD = 0.6
    
    # Model cache
    MODEL_CACHE_DIR = ".cache/whisper"
    
    # Performance
    NUM_WORKERS = 1
    BATCH_SIZE = 1

# ============================================================================
# EMOTION RECOGNITION CONFIGURATION
# ============================================================================

class EmotionConfig:
    """Speech emotion recognition configuration"""
    
    # Features
    ENABLE_EMOTION_DETECTION = True
    FRAME_DURATION = 0.025  # seconds (25ms)
    HOP_LENGTH = 0.010  # seconds (10ms)
    
    # Energy thresholds
    SILENCE_THRESHOLD = -40  # dB
    NOISE_THRESHOLD = -30  # dB
    
    # Model settings
    EMOTION_CATEGORIES = 10
    CONFIDENCE_THRESHOLD = 0.5
    
    # Averaging (smooth emotion changes)
    EMOTION_SMOOTHING = True
    SMOOTHING_WINDOW = 3

# ============================================================================
# BANT EXTRACTION CONFIGURATION
# ============================================================================

class BANTConfig:
    """BANT (Budget, Authority, Need, Timeline) configuration"""
    
    # Enable components
    EXTRACT_BUDGET = True
    EXTRACT_AUTHORITY = True
    EXTRACT_NEED = True
    EXTRACT_TIMELINE = True
    
    # Currency support
    SUPPORTED_CURRENCIES = [
        'INR', 'USD', 'EUR', 'GBP',
        'JPY', 'AUD', 'CAD', 'CHF'
    ]
    
    # Default currency (if not specified)
    DEFAULT_CURRENCY = "INR"
    
    # Confidence thresholds
    MIN_CONFIDENCE = 0.6
    
    # Custom patterns (add your own)
    CUSTOM_BUDGET_PATTERNS = []
    CUSTOM_AUTHORITY_PATTERNS = []
    CUSTOM_NEED_PATTERNS = []
    CUSTOM_TIMELINE_PATTERNS = []

# ============================================================================
# INTENT DETECTION CONFIGURATION
# ============================================================================

class IntentConfig:
    """Intent detection configuration"""
    
    # Intent categories to detect
    INTENT_CATEGORIES = [
        'pricing',
        'demo',
        'purchase',
        'negotiation',
        'support',
        'cancellation',
        'renewal',
        'information',
        'objection',
        'competitor'
    ]
    
    # Confidence threshold
    MIN_INTENT_CONFIDENCE = 0.5
    
    # Custom intents (add your own)
    CUSTOM_INTENTS = {}
    
    # Intent weighting
    INTENT_WEIGHTS = {
        'pricing': 1.0,
        'purchase': 1.5,
        'demo': 1.0
    }

# ============================================================================
# BUYING SIGNALS CONFIGURATION
# ============================================================================

class BuyingSignalConfig:
    """Buying signal detection configuration"""
    
    # Signals to detect
    DETECT_BUYING_SIGNALS = True
    
    # Signal weights (importance)
    SIGNAL_WEIGHTS = {
        'request_quotation': 0.95,
        'discuss_contract': 0.90,
        'budget_confirmation': 0.87,
        'commitment_language': 0.85,
        'request_demo': 0.85,
        'request_reference': 0.82,
        'decision_maker_engagement': 0.80,
        'discuss_timeline': 0.80,
        'urgency_indicators': 0.72,
        'discuss_pricing': 0.78,
        'discuss_features': 0.70,
        'request_meeting': 0.75
    }
    
    # Readiness thresholds
    READY_TO_BUY_THRESHOLD = 0.80
    LIKELY_TO_BUY_THRESHOLD = 0.50
    CONSIDERING_THRESHOLD = 0.20

# ============================================================================
# OBJECTION DETECTION CONFIGURATION
# ============================================================================

class ObjectionConfig:
    """Objection detection configuration"""
    
    # Detect objections
    DETECT_OBJECTIONS = True
    
    # Objection severity levels
    CRITICAL_OBJECTIONS = ['price', 'security', 'budget']
    HIGH_OBJECTIONS = ['authority', 'competitor', 'trust']
    MEDIUM_OBJECTIONS = ['need', 'timing', 'features', 'integration', 'implementation']
    LOW_OBJECTIONS = ['support']
    
    # Handling strategies
    OBJECTION_STRATEGIES = {
        'price': 'Emphasize value and ROI. Discuss payment options.',
        'budget': 'Explore phased implementation. Discuss budget timeline.',
        'authority': 'Request meeting with decision maker.',
        'trust': 'Share customer testimonials and case studies.'
    }

# ============================================================================
# ICP (IDEAL CUSTOMER PROFILE) CONFIGURATION
# ============================================================================

class ICPConfig:
    """ICP matching configuration"""
    
    # Criteria weights
    CRITERIA_WEIGHTS = {
        'industry': 0.25,
        'size': 0.20,
        'revenue': 0.25,
        'region': 0.15,
        'role': 0.15
    }
    
    # Ideal profile definition
    IDEAL_INDUSTRIES = [
        'technology',
        'finance',
        'healthcare'
    ]
    
    IDEAL_COMPANY_SIZES = [
        'medium',
        'enterprise'
    ]
    
    IDEAL_REVENUE_RANGES = [
        'large',
        'medium'
    ]
    
    IDEAL_REGIONS = [
        'asia',
        'north_america',
        'europe'
    ]
    
    IDEAL_ROLES = [
        'c_level',
        'director'
    ]
    
    # Tiers
    TIERS = {
        'A+': 90,
        'A': 80,
        'B': 70,
        'C': 60,
        'D': 0
    }

# ============================================================================
# LEAD SCORING CONFIGURATION
# ============================================================================

class LeadScoringConfig:
    """Lead scoring and qualification configuration"""
    
    # Component weights in lead score
    COMPONENT_WEIGHTS = {
        'emotion': 0.15,
        'bant': 0.20,
        'intent': 0.15,
        'buying_signals': 0.25,
        'icp': 0.15,
        'quality': 0.10
    }
    
    # Qualification thresholds
    HOT_THRESHOLD = 75  # >= 75%
    WARM_THRESHOLD = 50  # 50-74%
    COLD_THRESHOLD = 0   # < 50%
    
    # Confidence levels
    MIN_CONFIDENCE = 0.5
    HIGH_CONFIDENCE = 0.8
    
    # Ensemble settings
    USE_ENSEMBLE = True
    ENSEMBLE_METHOD = "weighted_average"  # weighted_average, voting, stacking
    
    # Trend detection
    TRACK_SCORE_TRENDS = True
    TREND_WINDOW = 5  # last N scores

# ============================================================================
# DATABASE CONFIGURATION (if using)
# ============================================================================

class DatabaseConfig:
    """Database configuration for storing results"""
    
    # Database type
    DB_TYPE = "sqlite"  # sqlite, mysql, postgresql, mongodb
    
    # Connection details
    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_NAME = "sales_intelligence"
    DB_USER = "user"
    DB_PASSWORD = "password"
    
    # SQLite specific
    SQLITE_PATH = "sales_intelligence.db"
    
    # Connection pooling
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    
    # Logging
    ECHO = False  # Log SQL queries

# ============================================================================
# EXPORT CONFIGURATION
# ============================================================================

class ExportConfig:
    """Configuration for exporting results"""
    
    # Export formats
    EXPORT_JSON = True
    EXPORT_CSV = True
    EXPORT_PDF = False
    
    # Export destinations
    EXPORT_LOCAL = True
    EXPORT_S3 = False
    EXPORT_GCS = False
    
    # S3 settings (if using)
    S3_BUCKET = "sales-intelligence"
    S3_PREFIX = "exports/"
    
    # File retention
    RETENTION_DAYS = 90
    AUTO_CLEANUP = True

# ============================================================================
# CRM INTEGRATION CONFIGURATION
# ============================================================================

class CRMIntegrationConfig:
    """CRM integration settings"""
    
    # Salesforce
    SALESFORCE_ENABLED = False
    SALESFORCE_INSTANCE_URL = "https://your-instance.salesforce.com"
    SALESFORCE_CLIENT_ID = "your-client-id"
    SALESFORCE_CLIENT_SECRET = "your-client-secret"
    
    # HubSpot
    HUBSPOT_ENABLED = False
    HUBSPOT_API_KEY = "your-api-key"
    
    # Pipedrive
    PIPEDRIVE_ENABLED = False
    PIPEDRIVE_COMPANY_DOMAIN = "your-company"
    PIPEDRIVE_API_TOKEN = "your-api-token"
    
    # Auto-sync settings
    AUTO_SYNC_ENABLED = False
    AUTO_SYNC_DELAY = 5  # seconds after analysis
    SYNC_CONFIDENCE_THRESHOLD = 0.75

# ============================================================================
# NOTIFICATION CONFIGURATION
# ============================================================================

class NotificationConfig:
    """Notification settings"""
    
    # Email notifications
    EMAIL_ENABLED = False
    EMAIL_ON_HOT_LEAD = True
    EMAIL_ON_OBJECTION = False
    EMAIL_SMTP_SERVER = "smtp.gmail.com"
    EMAIL_SMTP_PORT = 587
    EMAIL_USERNAME = "your-email@gmail.com"
    EMAIL_PASSWORD = "your-app-password"
    EMAIL_RECIPIENTS = ["sales@company.com"]
    
    # Webhook notifications
    WEBHOOK_ENABLED = False
    WEBHOOK_URL = "https://your-webhook.com/sales-intelligence"
    WEBHOOK_TIMEOUT = 5  # seconds
    
    # Slack notifications
    SLACK_ENABLED = False
    SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    SLACK_CHANNEL = "#sales-alerts"
    SLACK_ON_HOT_LEAD = True
    SLACK_ON_OBJECTION = True

# ============================================================================
# MASTER CONFIG CLASS
# ============================================================================

class Config:
    """Master configuration class"""
    
    # Environment
    ENV = os.getenv("ENV", "development")  # development, staging, production
    DEBUG = ENV == "development"
    
    # Configurations
    server = ServerConfig()
    audio = AudioConfig()
    whisper = WhisperConfig()
    emotion = EmotionConfig()
    bant = BANTConfig()
    intent = IntentConfig()
    buying_signal = BuyingSignalConfig()
    objection = ObjectionConfig()
    icp = ICPConfig()
    lead_scoring = LeadScoringConfig()
    database = DatabaseConfig()
    export = ExportConfig()
    crm = CRMIntegrationConfig()
    notification = NotificationConfig()

# ============================================================================
# USAGE
# ============================================================================

# In your code:
"""
from config import Config

# Access configuration
sample_rate = Config.audio.SAMPLE_RATE
model_size = Config.whisper.MODEL_SIZE
hot_threshold = Config.lead_scoring.HOT_THRESHOLD
"""
