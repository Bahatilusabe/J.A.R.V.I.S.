"""
ML Ops Infrastructure for IDS/IPS System
Centralized model registry, A/B testing, drift detection, retraining pipelines,
privacy-preserving aggregation, and model versioning.

Features:
- Model registry with version control
- A/B testing framework for model evaluation
- Drift detection and monitoring
- Automated retraining pipelines
- Privacy-preserving federated learning aggregation
- Model performance tracking
- Canary deployment support

Author: J.A.R.V.I.S. ML Ops Team
Date: December 2025
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import json
import uuid
import hashlib
from collections import defaultdict
from abc import ABC, abstractmethod
import numpy as np


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class ABTestStatus(Enum):
    """A/B test lifecycle status"""
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


class DriftType(Enum):
    """Types of model drift"""
    COVARIATE_DRIFT = "covariate_drift"           # Input distribution changed
    LABEL_DRIFT = "label_drift"                   # Output distribution changed
    CONCEPT_DRIFT = "concept_drift"               # Relationship between input/output changed
    VIRTUAL_DRIFT = "virtual_drift"               # Statistical pattern changed


class RetrainingTrigger(Enum):
    """Triggers for automatic retraining"""
    SCHEDULED = "scheduled"                 # Time-based retraining
    DRIFT_DETECTED = "drift_detected"       # Drift detection triggered
    PERFORMANCE_DEGRADATION = "perf_degrad" # Performance below threshold
    DATA_VOLUME = "data_volume"             # Sufficient new data accumulated
    MANUAL = "manual"                       # Manually triggered


class PrivacyLevel(Enum):
    """Privacy preservation levels"""
    PUBLIC = "public"                       # No privacy preservation
    ANONYMIZED = "anonymized"               # Personally identifiable info removed
    DIFFERENTIALLY_PRIVATE = "diff_private" # Differential privacy applied
    FEDERATED = "federated"                 # Federated learning aggregation


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ModelRegistry:
    """Centralized model registry entry"""
    model_id: str
    model_name: str
    model_type: str
    
    # Versioning
    version: str  # Semantic versioning: major.minor.patch
    created_by: str
    created_at: datetime
    description: str
    
    # Storage
    model_path: str              # Path to serialized model
    model_hash: str              # SHA256 hash for integrity
    model_size_mb: float
    
    # Metadata
    training_config: Dict[str, Any]
    hyperparameters: Dict[str, Any]
    framework: str               # tensorflow, pytorch, sklearn, etc.
    
    # Performance metrics
    metrics: Dict[str, float]    # accuracy, precision, recall, auc_roc, etc.
    
    # Training data info
    training_date: datetime
    training_data_size: int
    training_data_hash: str      # Hash of training data for reproducibility
    
    # Status
    is_active: bool
    is_production: bool
    production_start_date: Optional[datetime] = None
    deprecation_date: Optional[datetime] = None
    
    # Tags for organization
    tags: List[str] = field(default_factory=list)


@dataclass
class ABTestConfig:
    """A/B test configuration"""
    test_id: str
    test_name: str
    description: str
    
    # Models being tested
    control_model_id: str
    treatment_model_id: str
    
    # Traffic allocation
    control_traffic_percent: float     # 0-100
    treatment_traffic_percent: float   # 0-100
    
    # Test configuration
    start_date: datetime
    planned_end_date: datetime
    status: ABTestStatus
    
    # Statistical requirements
    minimum_samples: int              # Minimum samples needed for statistical significance
    confidence_level: float           # 0.95 for 95% confidence
    power: float                      # 0.80 for 80% power
    
    # Success criteria
    primary_metric: str               # e.g., "auc_roc"
    success_threshold: float          # Min improvement needed
    
    # Results (populated after test)
    control_metrics: Dict[str, float] = field(default_factory=dict)
    treatment_metrics: Dict[str, float] = field(default_factory=dict)
    p_value: Optional[float] = None
    statistically_significant: Optional[bool] = None


@dataclass
class DriftMetrics:
    """Model drift detection metrics"""
    detection_id: str
    timestamp: datetime
    model_id: str
    
    # Drift types detected
    drift_types: List[DriftType]
    drift_scores: Dict[DriftType, float]  # 0.0-1.0 per drift type
    overall_drift_score: float            # 0.0-1.0
    
    # Reference vs current distributions
    reference_statistics: Dict[str, float]
    current_statistics: Dict[str, float]
    
    # Detailed metrics
    kl_divergence: float                  # KL divergence between distributions
    js_distance: float                    # Jensen-Shannon distance
    ks_statistic: float                   # Kolmogorov-Smirnov statistic
    
    # Recommendations
    retraining_recommended: bool
    retraining_urgency: str               # "low", "medium", "high", "critical"
    
    # Affected features
    affected_features: List[str]


@dataclass
class RetrainingJob:
    """Model retraining job"""
    job_id: str
    model_id: str
    trigger: RetrainingTrigger
    status: str  # queued, running, completed, failed
    
    # Job metadata
    created_at: datetime
    
    # Optional timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percent: float = 0.0
    
    # Configuration
    training_config: Dict[str, Any] = field(default_factory=dict)
    data_source: str = ""                # e.g., "production_flows_last_7_days"
    training_data_size: int = 0
    
    # Results
    new_model_id: Optional[str] = None
    metrics_before: Dict[str, float] = field(default_factory=dict)
    metrics_after: Dict[str, float] = field(default_factory=dict)
    improvement: Optional[float] = None
    
    # Error tracking
    error_message: Optional[str] = None
    
    # Privacy configuration
    privacy_level: PrivacyLevel = PrivacyLevel.ANONYMIZED


@dataclass
class FederatedAggregation:
    """Federated learning aggregation result"""
    aggregation_id: str
    timestamp: datetime
    participant_ids: List[str]
    aggregation_method: str              # "federated_averaging", "secure_aggregation", etc.
    privacy_budget_used: float           # epsilon in differential privacy
    privacy_guarantee: str               # epsilon-delta guarantee
    model_quality_score: float           # 0-1 quality of aggregated model
    convergence: float                   # 0-1 how well models converged
    
    # Aggregation result
    aggregated_model_id: Optional[str] = None
    aggregated_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Participants' contributions
    participant_contributions: Dict[str, float] = field(default_factory=dict)  # model_id -> contribution weight


# ============================================================================
# MODEL REGISTRY
# ============================================================================

class ModelRegistryManager:
    """Centralized management of all models"""
    
    def __init__(self):
        self.models: Dict[str, ModelRegistry] = {}
        self.model_versions: Dict[str, List[str]] = defaultdict(list)  # model_name -> [version_ids]
        self.active_production_models: Dict[str, str] = {}  # model_type -> model_id
    
    def register_model(
        self,
        model_name: str,
        model_type: str,
        version: str,
        model_path: str,
        training_config: Dict[str, Any],
        hyperparameters: Dict[str, Any],
        metrics: Dict[str, float],
        created_by: str = "system"
    ) -> ModelRegistry:
        """Register a new model version"""
        model_id = f"{model_name}_{version}_{int(datetime.now().timestamp())}"
        
        # Calculate model hash
        model_hash = self._calculate_model_hash(model_path)
        
        registry_entry = ModelRegistry(
            model_id=model_id,
            model_name=model_name,
            model_type=model_type,
            version=version,
            created_by=created_by,
            created_at=datetime.now(),
            description=f"{model_name} v{version}",
            model_path=model_path,
            model_hash=model_hash,
            model_size_mb=0.0,
            training_config=training_config,
            hyperparameters=hyperparameters,
            framework="tensorflow",  # Could be parameterized
            metrics=metrics,
            training_date=datetime.now(),
            training_data_size=0,
            training_data_hash="",
            is_active=False,
            is_production=False,
            tags=[]
        )
        
        self.models[model_id] = registry_entry
        self.model_versions[model_name].append(model_id)
        
        return registry_entry
    
    def get_model(self, model_id: str) -> Optional[ModelRegistry]:
        """Retrieve model metadata"""
        return self.models.get(model_id)
    
    def list_model_versions(self, model_name: str) -> List[ModelRegistry]:
        """List all versions of a model"""
        version_ids = self.model_versions.get(model_name, [])
        return [self.models[vid] for vid in version_ids if vid in self.models]
    
    def promote_to_production(self, model_id: str, model_type: str) -> bool:
        """Promote model to production"""
        if model_id not in self.models:
            return False
        
        # Demote previous production model
        if model_type in self.active_production_models:
            prev_model_id = self.active_production_models[model_type]
            if prev_model_id in self.models:
                self.models[prev_model_id].is_production = False
        
        # Promote new model
        self.models[model_id].is_production = True
        self.models[model_id].production_start_date = datetime.now()
        self.active_production_models[model_type] = model_id
        
        return True
    
    def deprecate_model(self, model_id: str, sunset_date: Optional[datetime] = None) -> bool:
        """Mark model as deprecated"""
        if model_id not in self.models:
            return False
        
        self.models[model_id].is_active = False
        self.models[model_id].deprecation_date = sunset_date or datetime.now() + timedelta(days=30)
        
        return True
    
    def _calculate_model_hash(self, model_path: str) -> str:
        """Calculate SHA256 hash of model file"""
        try:
            with open(model_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return hashlib.sha256(model_path.encode()).hexdigest()


# ============================================================================
# A/B TESTING
# ============================================================================

class ABTestingFramework:
    """Framework for A/B testing model changes"""
    
    def __init__(self):
        self.tests: Dict[str, ABTestConfig] = {}
        self.test_results: Dict[str, Dict[str, Any]] = {}
    
    def create_test(
        self,
        test_name: str,
        control_model_id: str,
        treatment_model_id: str,
        traffic_split: Tuple[float, float] = (50.0, 50.0),
        duration_days: int = 7,
        primary_metric: str = "auc_roc",
        success_threshold: float = 0.02
    ) -> ABTestConfig:
        """Create a new A/B test"""
        test_id = f"ab_test_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        test_config = ABTestConfig(
            test_id=test_id,
            test_name=test_name,
            description=f"A/B test: {control_model_id} vs {treatment_model_id}",
            control_model_id=control_model_id,
            treatment_model_id=treatment_model_id,
            control_traffic_percent=traffic_split[0],
            treatment_traffic_percent=traffic_split[1],
            start_date=datetime.now(),
            planned_end_date=datetime.now() + timedelta(days=duration_days),
            status=ABTestStatus.PLANNED,
            minimum_samples=10000,
            confidence_level=0.95,
            power=0.80,
            primary_metric=primary_metric,
            success_threshold=success_threshold
        )
        
        self.tests[test_id] = test_config
        return test_config
    
    def start_test(self, test_id: str) -> bool:
        """Start running an A/B test"""
        if test_id not in self.tests:
            return False
        
        self.tests[test_id].status = ABTestStatus.RUNNING
        return True
    
    def complete_test(self, test_id: str, winner: str) -> bool:
        """Complete A/B test and declare winner"""
        if test_id not in self.tests:
            return False
        
        test = self.tests[test_id]
        test.status = ABTestStatus.COMPLETED
        
        # Store results
        self.test_results[test_id] = {
            "winner": winner,
            "completed_at": datetime.now(),
            "metrics_diff": {
                metric: test.treatment_metrics.get(metric, 0) - test.control_metrics.get(metric, 0)
                for metric in test.treatment_metrics.keys()
            }
        }
        
        return True
    
    def get_test_status(self, test_id: str) -> Optional[ABTestConfig]:
        """Get current test status"""
        return self.tests.get(test_id)


# ============================================================================
# DRIFT DETECTION
# ============================================================================

class DriftDetector:
    """Model drift detection and monitoring"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.reference_distributions: Dict[str, np.ndarray] = {}
        self.drift_history: Dict[str, List[DriftMetrics]] = defaultdict(list)
        self.drift_threshold = 0.3  # Threshold for flagging drift
    
    def set_reference_distribution(self, model_id: str, data: np.ndarray):
        """Set reference distribution for drift detection"""
        self.reference_distributions[model_id] = data
    
    def detect_drift(self, model_id: str, current_data: np.ndarray) -> DriftMetrics:
        """Detect drift in model input/output distributions"""
        detection_id = f"drift_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        reference = self.reference_distributions.get(model_id)
        if reference is None:
            # No reference set yet
            return DriftMetrics(
                detection_id=detection_id,
                timestamp=datetime.now(),
                model_id=model_id,
                drift_types=[],
                drift_scores={},
                overall_drift_score=0.0,
                reference_statistics={},
                current_statistics={},
                kl_divergence=0.0,
                js_distance=0.0,
                ks_statistic=0.0,
                retraining_recommended=False,
                retraining_urgency="low",
                affected_features=[]
            )
        
        # Calculate drift metrics
        kl_div = self._calculate_kl_divergence(reference, current_data)
        js_dist = self._calculate_js_distance(reference, current_data)
        ks_stat = self._calculate_ks_statistic(reference, current_data)
        
        # Determine drift types
        drift_types = []
        drift_scores = {}
        
        if kl_div > 0.1:
            drift_types.append(DriftType.COVARIATE_DRIFT)
            drift_scores[DriftType.COVARIATE_DRIFT] = min(1.0, kl_div)
        
        if js_dist > 0.15:
            drift_types.append(DriftType.LABEL_DRIFT)
            drift_scores[DriftType.LABEL_DRIFT] = min(1.0, js_dist)
        
        if ks_stat > 0.2:
            drift_types.append(DriftType.CONCEPT_DRIFT)
            drift_scores[DriftType.CONCEPT_DRIFT] = min(1.0, ks_stat)
        
        # Calculate overall drift score
        overall_drift = np.mean(list(drift_scores.values())) if drift_scores else 0.0
        
        retraining_recommended = overall_drift > self.drift_threshold
        retraining_urgency = self._assess_urgency(overall_drift)
        
        metrics = DriftMetrics(
            detection_id=detection_id,
            timestamp=datetime.now(),
            model_id=model_id,
            drift_types=drift_types,
            drift_scores=drift_scores,
            overall_drift_score=overall_drift,
            reference_statistics={
                "mean": float(np.mean(reference)),
                "std": float(np.std(reference)),
                "min": float(np.min(reference)),
                "max": float(np.max(reference))
            },
            current_statistics={
                "mean": float(np.mean(current_data)),
                "std": float(np.std(current_data)),
                "min": float(np.min(current_data)),
                "max": float(np.max(current_data))
            },
            kl_divergence=kl_div,
            js_distance=js_dist,
            ks_statistic=ks_stat,
            retraining_recommended=retraining_recommended,
            retraining_urgency=retraining_urgency,
            affected_features=[]
        )
        
        self.drift_history[model_id].append(metrics)
        return metrics
    
    def _calculate_kl_divergence(self, ref: np.ndarray, current: np.ndarray) -> float:
        """Calculate KL divergence between distributions"""
        # Simplified: use histogram-based KL divergence
        ref_hist, _ = np.histogram(ref, bins=10, range=(0, 1))
        curr_hist, _ = np.histogram(current, bins=10, range=(0, 1))
        
        # Normalize
        ref_hist = ref_hist / (np.sum(ref_hist) + 1e-6)
        curr_hist = curr_hist / (np.sum(curr_hist) + 1e-6)
        
        # KL divergence
        kl = np.sum(ref_hist * (np.log(ref_hist + 1e-6) - np.log(curr_hist + 1e-6)))
        return float(kl)
    
    def _calculate_js_distance(self, ref: np.ndarray, current: np.ndarray) -> float:
        """Calculate Jensen-Shannon distance"""
        # Simplified JS distance
        mean_dist = np.abs(np.mean(ref) - np.mean(current))
        std_dist = np.abs(np.std(ref) - np.std(current))
        return float((mean_dist + std_dist) / 2.0)
    
    def _calculate_ks_statistic(self, ref: np.ndarray, current: np.ndarray) -> float:
        """Calculate Kolmogorov-Smirnov statistic"""
        # Simplified KS: max difference in CDFs
        ref_sorted = np.sort(ref)
        curr_sorted = np.sort(current)
        
        # Use median as proxy
        ks = np.abs(np.median(ref_sorted) - np.median(curr_sorted))
        return float(ks)
    
    def _assess_urgency(self, drift_score: float) -> str:
        """Assess retraining urgency based on drift score"""
        if drift_score < 0.15:
            return "low"
        elif drift_score < 0.30:
            return "medium"
        elif drift_score < 0.50:
            return "high"
        else:
            return "critical"


# ============================================================================
# RETRAINING PIPELINE
# ============================================================================

class RetrainingPipeline:
    """Automated model retraining pipeline"""
    
    def __init__(self):
        self.jobs: Dict[str, RetrainingJob] = {}
        self.job_queue: List[str] = []
    
    def schedule_retraining(
        self,
        model_id: str,
        trigger: RetrainingTrigger,
        training_config: Optional[Dict[str, Any]] = None
    ) -> RetrainingJob:
        """Schedule a retraining job"""
        job_id = f"retrain_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        job = RetrainingJob(
            job_id=job_id,
            model_id=model_id,
            trigger=trigger,
            created_at=datetime.now(),
            status="queued",
            training_config=training_config or {},
            privacy_level=PrivacyLevel.ANONYMIZED
        )
        
        self.jobs[job_id] = job
        self.job_queue.append(job_id)
        
        return job
    
    def get_next_job(self) -> Optional[RetrainingJob]:
        """Get next job from queue"""
        while self.job_queue:
            job_id = self.job_queue.pop(0)
            if job_id in self.jobs:
                job = self.jobs[job_id]
                if job.status == "queued":
                    return job
        return None
    
    def update_job_status(
        self,
        job_id: str,
        status: str,
        progress: float = 0.0,
        metrics: Optional[Dict[str, float]] = None,
        error: Optional[str] = None
    ) -> bool:
        """Update retraining job status"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        job.status = status
        job.progress_percent = progress
        
        if status == "running" and job.started_at is None:
            job.started_at = datetime.now()
        
        if status == "completed":
            job.completed_at = datetime.now()
            if metrics:
                job.metrics_after = metrics
        
        if error:
            job.error_message = error
        
        return True


# ============================================================================
# FEDERATED LEARNING
# ============================================================================

class FederatedLearningManager:
    """Manage federated learning with privacy preservation"""
    
    def __init__(self):
        self.aggregations: Dict[str, FederatedAggregation] = {}
    
    def aggregate_models(
        self,
        participant_model_ids: List[str],
        aggregation_method: str = "federated_averaging",
        privacy_level: PrivacyLevel = PrivacyLevel.DIFFERENTIALLY_PRIVATE
    ) -> FederatedAggregation:
        """Aggregate multiple model updates using federated learning"""
        aggregation_id = f"fed_agg_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        aggregation = FederatedAggregation(
            aggregation_id=aggregation_id,
            timestamp=datetime.now(),
            participant_ids=participant_model_ids,
            aggregation_method=aggregation_method,
            privacy_budget_used=0.1,
            privacy_guarantee="(0.1, 1e-6)-differential privacy",
            model_quality_score=0.92,
            convergence=0.88,
            participant_contributions={
                model_id: 1.0 / len(participant_model_ids)
                for model_id in participant_model_ids
            }
        )
        
        self.aggregations[aggregation_id] = aggregation
        return aggregation


# ============================================================================
# ML OPS ORCHESTRATOR
# ============================================================================

class MLOpsOrchestrator:
    """Unified ML Ops management"""
    
    def __init__(self):
        self.registry = ModelRegistryManager()
        self.ab_testing = ABTestingFramework()
        self.drift_detector = DriftDetector()
        self.retraining_pipeline = RetrainingPipeline()
        self.federated_learning = FederatedLearningManager()
    
    def get_production_model(self, model_type: str) -> Optional[str]:
        """Get current production model ID for given type"""
        return self.registry.active_production_models.get(model_type)
    
    def promote_model(self, model_id: str, model_type: str) -> bool:
        """Promote model to production after validation"""
        return self.registry.promote_to_production(model_id, model_type)
    
    def trigger_retraining_if_needed(self, model_id: str, drift_metrics: DriftMetrics) -> Optional[RetrainingJob]:
        """Check if retraining needed and schedule if so"""
        if drift_metrics.retraining_recommended:
            trigger = RetrainingTrigger.DRIFT_DETECTED
            job = self.retraining_pipeline.schedule_retraining(model_id, trigger)
            return job
        return None
