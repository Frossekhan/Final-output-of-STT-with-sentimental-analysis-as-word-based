"""
Database Models
PostgreSQL models for persistent storage
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """Session model"""
    id: str
    customer_id: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    lead_score: Optional[float]
    qualification: Optional[str]
    engine_type: str
    metadata: Dict[str, Any]


@dataclass
class Transcript:
    """Transcript model"""
    id: str
    session_id: str
    speaker: str
    text: str
    timestamp: datetime
    confidence: float
    emotion: Optional[str]
    emotion_confidence: Optional[float]


@dataclass
class AnalysisResult:
    """Analysis result model"""
    id: str
    transcript_id: str
    bant: Dict[str, Any]
    intent: Dict[str, Any]
    buying_signals: Dict[str, Any]
    objections: Dict[str, Any]
    emotion: Dict[str, Any]
    summary: Dict[str, Any]
    analyzed_at: datetime


@dataclass
class AudioFile:
    """Audio file model"""
    id: str
    session_id: str
    file_path: str
    duration: float
    sample_rate: int
    channels: int
    created_at: datetime


@dataclass
class CustomerProfile:
    """Customer profile model"""
    id: str
    name: Optional[str]
    company: Optional[str]
    role: Optional[str]
    industry: Optional[str]
    company_size: Optional[str]
    revenue_range: Optional[str]
    region: Optional[str]
    budget: Optional[float]
    authority_level: Optional[str]
    need_category: Optional[str]
    timeline: Optional[str]
    total_interactions: int
    avg_lead_score: float
    last_interaction: datetime
    created_at: datetime
    updated_at: datetime


class DatabaseManager:
    """
    Database manager for PostgreSQL
    
    Provides:
    - Session management
    - Transcript storage
    - Analysis result storage
    - Customer profile management
    - Audio file storage
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string or "postgresql://user:pass@localhost:5432/sales_intelligence"
        self.engine = None
        self.Session = None
        self.Transcript = None
        self.AnalysisResult = None
        self.AudioFile = None
        self.CustomerProfile = None
        
        # Try to initialize SQLAlchemy
        self._init_sqlalchemy()
    
    def _init_sqlalchemy(self):
        """Initialize SQLAlchemy ORM"""
        try:
            from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text, Boolean, ForeignKey
            from sqlalchemy.ext.declarative import declarative_base
            from sqlalchemy.orm import sessionmaker, relationship
            import uuid
            
            Base = declarative_base()
            
            # Create engine
            self.engine = create_engine(self.connection_string)
            self.SessionLocal = sessionmaker(bind=self.engine)
            
            # Define models
            class SessionModel(Base):
                __tablename__ = "sessions"
                
                id = Column(String, primary_key=True)
                customer_id = Column(String, nullable=True)
                started_at = Column(DateTime, default=datetime.now)
                ended_at = Column(DateTime, nullable=True)
                lead_score = Column(Float, nullable=True)
                qualification = Column(String, nullable=True)
                engine_type = Column(String, default="llm")
                metadata = Column(Text, nullable=True)
            
            class TranscriptModel(Base):
                __tablename__ = "transcripts"
                
                id = Column(String, primary_key=True)
                session_id = Column(String, ForeignKey("sessions.id"))
                speaker = Column(String)
                text = Column(Text)
                timestamp = Column(DateTime, default=datetime.now)
                confidence = Column(Float, default=0.0)
                emotion = Column(String, nullable=True)
                emotion_confidence = Column(Float, nullable=True)
            
            class AnalysisResultModel(Base):
                __tablename__ = "analysis_results"
                
                id = Column(String, primary_key=True)
                transcript_id = Column(String, ForeignKey("transcripts.id"))
                bant = Column(Text)  # JSON
                intent = Column(Text)  # JSON
                buying_signals = Column(Text)  # JSON
                objections = Column(Text)  # JSON
                emotion = Column(Text)  # JSON
                summary = Column(Text)  # JSON
                analyzed_at = Column(DateTime, default=datetime.now)
            
            class AudioFileModel(Base):
                __tablename__ = "audio_files"
                
                id = Column(String, primary_key=True)
                session_id = Column(String, ForeignKey("sessions.id"))
                file_path = Column(String)
                duration = Column(Float)
                sample_rate = Column(Integer)
                channels = Column(Integer, default=1)
                created_at = Column(DateTime, default=datetime.now)
            
            class CustomerProfileModel(Base):
                __tablename__ = "customer_profiles"
                
                id = Column(String, primary_key=True)
                name = Column(String, nullable=True)
                company = Column(String, nullable=True)
                role = Column(String, nullable=True)
                industry = Column(String, nullable=True)
                company_size = Column(String, nullable=True)
                revenue_range = Column(String, nullable=True)
                region = Column(String, nullable=True)
                budget = Column(Float, nullable=True)
                authority_level = Column(String, nullable=True)
                need_category = Column(String, nullable=True)
                timeline = Column(String, nullable=True)
                total_interactions = Column(Integer, default=0)
                avg_lead_score = Column(Float, default=0.0)
                last_interaction = Column(DateTime, default=datetime.now)
                created_at = Column(DateTime, default=datetime.now)
                updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
            
            # Store models
            self.Session = SessionModel
            self.Transcript = TranscriptModel
            self.AnalysisResult = AnalysisResultModel
            self.AudioFile = AudioFileModel
            self.CustomerProfile = CustomerProfileModel
            self.Base = Base
            
            # Create tables
            Base.metadata.create_all(self.engine)
            
            logger.info("Database initialized successfully")
        
        except Exception as e:
            logger.warning(f"SQLAlchemy not available: {e}")
            self.engine = None
    
    def create_session(self, session_id: str, customer_id: Optional[str] = None, engine_type: str = "llm") -> bool:
        """
        Create a new session
        
        Args:
            session_id: Session ID
            customer_id: Customer ID (optional)
            engine_type: Engine type (llm/rule-based)
            
        Returns:
            Success status
        """
        if not self.engine:
            return False
        
        try:
            db = self.SessionLocal()
            
            session = self.Session(
                id=session_id,
                customer_id=customer_id,
                started_at=datetime.now(),
                engine_type=engine_type,
                metadata=json.dumps({})
            )
            
            db.add(session)
            db.commit()
            db.close()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return False
    
    def end_session(self, session_id: str, lead_score: Optional[float] = None, qualification: Optional[str] = None):
        """
        End a session
        
        Args:
            session_id: Session ID
            lead_score: Final lead score
            qualification: Lead qualification (HOT/WARM/COLD)
        """
        if not self.engine:
            return
        
        try:
            db = self.SessionLocal()
            
            session = db.query(self.Session).filter_by(id=session_id).first()
            if session:
                session.ended_at = datetime.now()
                session.lead_score = lead_score
                session.qualification = qualification
                db.commit()
            
            db.close()
        
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
    
    def save_transcript(self, session_id: str, speaker: str, text: str, confidence: float = 0.0, 
                       emotion: Optional[str] = None, emotion_confidence: Optional[float] = None) -> bool:
        """
        Save transcript
        
        Args:
            session_id: Session ID
            speaker: Speaker (customer/salesperson)
            text: Transcript text
            confidence: Transcription confidence
            emotion: Detected emotion
            emotion_confidence: Emotion confidence
            
        Returns:
            Success status
        """
        if not self.engine:
            return False
        
        try:
            db = self.SessionLocal()
            
            transcript = self.Transcript(
                id=str(uuid.uuid4()),
                session_id=session_id,
                speaker=speaker,
                text=text,
                timestamp=datetime.now(),
                confidence=confidence,
                emotion=emotion,
                emotion_confidence=emotion_confidence
            )
            
            db.add(transcript)
            db.commit()
            db.close()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save transcript: {e}")
            return False
    
    def save_analysis_result(self, transcript_id: str, analysis: Dict) -> bool:
        """
        Save analysis result
        
        Args:
            transcript_id: Transcript ID
            analysis: Analysis dictionary
            
        Returns:
            Success status
        """
        if not self.engine:
            return False
        
        try:
            db = self.SessionLocal()
            
            result = self.AnalysisResult(
                id=str(uuid.uuid4()),
                transcript_id=transcript_id,
                bant=json.dumps(analysis.get("bant", {})),
                intent=json.dumps(analysis.get("intent", {})),
                buying_signals=json.dumps(analysis.get("buying_signals", {})),
                objections=json.dumps(analysis.get("objections", {})),
                emotion=json.dumps(analysis.get("emotion", {})),
                summary=json.dumps(analysis.get("summary", {})),
                analyzed_at=datetime.now()
            )
            
            db.add(result)
            db.commit()
            db.close()
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save analysis result: {e}")
            return False
    
    def get_session_transcripts(self, session_id: str) -> List[Dict]:
        """
        Get all transcripts for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of transcript dictionaries
        """
        if not self.engine:
            return []
        
        try:
            db = self.SessionLocal()
            
            transcripts = db.query(self.Transcript).filter_by(session_id=session_id).all()
            
            result = []
            for t in transcripts:
                result.append({
                    "id": t.id,
                    "speaker": t.speaker,
                    "text": t.text,
                    "timestamp": t.timestamp.isoformat(),
                    "confidence": t.confidence,
                    "emotion": t.emotion,
                    "emotion_confidence": t.emotion_confidence
                })
            
            db.close()
            return result
        
        except Exception as e:
            logger.error(f"Failed to get transcripts: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()


class DatabaseManagerFactory:
    """Factory for creating database manager instances"""
    
    @staticmethod
    def create(connection_string: Optional[str] = None) -> DatabaseManager:
        """
        Create database manager
        
        Args:
            connection_string: PostgreSQL connection string
            
        Returns:
            DatabaseManager instance
        """
        return DatabaseManager(connection_string=connection_string)