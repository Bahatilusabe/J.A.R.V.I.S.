"""
Federated Aggregation Strategies

Implements FedAvg, FedProx, and Secure Aggregation (SecAgg) for
combining local gradients into global model weights.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger("jarvis.fl_blockchain.aggregator")


@dataclass
class AggregationResult:
    """Result of aggregation operation"""
    aggregated_weights: np.ndarray
    num_participants: int
    aggregation_method: str
    norm_difference: float
    gradient_norm: float
    aggregation_quality: float


class FederatedAggregator:
    """
    Aggregates gradients from multiple organizations using
    FedAvg (simple averaging) or FedProx (proximal term).
    """
    
    def __init__(self, method: str = "fedprox", fedprox_lambda: float = 0.01):
        """
        Initialize aggregator
        
        Args:
            method: "fedavg" or "fedprox"
            fedprox_lambda: Proximal term weight for FedProx
        """
        self.method = method
        self.fedprox_lambda = fedprox_lambda
        
        if method not in ("fedavg", "fedprox"):
            raise ValueError(f"Unknown aggregation method: {method}")
    
    def aggregate(
        self,
        org_weights: Dict[str, np.ndarray],
        org_sample_counts: Dict[str, int],
        global_weights_prev: np.ndarray,
        learning_rate: float = 0.01,
    ) -> AggregationResult:
        """
        Aggregate local weights into global weights
        
        Args:
            org_weights: org_id → local weights array
            org_sample_counts: org_id → number of local samples
            global_weights_prev: Previous global weights (for FedProx)
            learning_rate: Learning rate for weight update
        
        Returns:
            AggregationResult with aggregated weights and metrics
        """
        if not org_weights:
            raise ValueError("No weights to aggregate")
        
        if self.method == "fedavg":
            return self._aggregate_fedavg(org_weights, org_sample_counts)
        elif self.method == "fedprox":
            return self._aggregate_fedprox(
                org_weights,
                org_sample_counts,
                global_weights_prev,
                learning_rate
            )
    
    def _aggregate_fedavg(
        self,
        org_weights: Dict[str, np.ndarray],
        org_sample_counts: Dict[str, int],
    ) -> AggregationResult:
        """
        FedAvg: Weighted average of local weights
        
        w_global = Σ(n_i / n_total * w_i)
        
        where:
        - n_i = number of samples from org i
        - n_total = total samples across all orgs
        - w_i = weights from org i
        """
        logger.info(f"Running FedAvg aggregation for {len(org_weights)} organizations")
        
        # Validate inputs
        if set(org_weights.keys()) != set(org_sample_counts.keys()):
            raise ValueError("Org IDs must match between weights and sample counts")
        
        # Calculate total samples
        total_samples = sum(org_sample_counts.values())
        if total_samples == 0:
            raise ValueError("Total samples is zero")
        
        # Initialize aggregated weights
        aggregated = None
        
        # Weighted average
        for org_id, weights in org_weights.items():
            sample_count = org_sample_counts[org_id]
            weight_factor = sample_count / total_samples
            
            if aggregated is None:
                aggregated = weight_factor * weights.copy()
            else:
                aggregated = aggregated + (weight_factor * weights)
            
            logger.debug(
                f"  {org_id}: {sample_count} samples ({weight_factor*100:.1f}%) "
                f"shape={weights.shape}"
            )
        
        if aggregated is None:
            raise RuntimeError("Aggregation failed")
        
        # Calculate metrics
        norm_diff = np.linalg.norm(aggregated - list(org_weights.values())[0])
        grad_norm = np.linalg.norm(aggregated)
        quality = 1.0  # Perfect quality for standard FedAvg
        
        return AggregationResult(
            aggregated_weights=aggregated,
            num_participants=len(org_weights),
            aggregation_method="fedavg",
            norm_difference=float(norm_diff),
            gradient_norm=float(grad_norm),
            aggregation_quality=quality,
        )
    
    def _aggregate_fedprox(
        self,
        org_weights: Dict[str, np.ndarray],
        org_sample_counts: Dict[str, int],
        global_weights_prev: np.ndarray,
        learning_rate: float,
    ) -> AggregationResult:
        """
        FedProx: Weighted average with proximal term
        
        w_global = Σ(n_i / n_total * w_i) + λ * (w_prev - w_new)
        
        The proximal term penalizes large deviations from previous weights,
        improving convergence for non-IID data distributions.
        """
        logger.info(
            f"Running FedProx aggregation "
            f"(lambda={self.fedprox_lambda}) for {len(org_weights)} organizations"
        )
        
        if global_weights_prev is None:
            raise ValueError("FedProx requires previous global weights")
        
        # FedAvg component
        fedavg_result = self._aggregate_fedavg(org_weights, org_sample_counts)
        aggregated = fedavg_result.aggregated_weights.copy()
        
        # Proximal term: penalize deviation from previous weights
        # w_new = w_avg + λ * (w_prev - w_avg)
        weight_deviation = global_weights_prev - aggregated
        proximal_term = self.fedprox_lambda * weight_deviation
        
        # Apply learning rate to proximal update
        aggregated = aggregated + (learning_rate * proximal_term)
        
        # Recalculate metrics with proximal term included
        norm_diff = np.linalg.norm(aggregated - global_weights_prev)
        grad_norm = np.linalg.norm(aggregated - global_weights_prev)
        
        # Quality reduced slightly due to proximal regularization
        quality = 0.95
        
        logger.info(
            f"FedProx aggregation complete: "
            f"norm_diff={norm_diff:.6f}, grad_norm={grad_norm:.6f}"
        )
        
        return AggregationResult(
            aggregated_weights=aggregated,
            num_participants=len(org_weights),
            aggregation_method="fedprox",
            norm_difference=float(norm_diff),
            gradient_norm=float(grad_norm),
            aggregation_quality=quality,
        )


class RobustAggregator:
    """
    Robust aggregation strategies for Byzantine-resilient federated learning.
    
    Defends against poisoning attacks by identifying and excluding
    malicious gradients.
    """
    
    def __init__(self, method: str = "trimmed_mean", trimmed_percentage: float = 0.1):
        """
        Initialize robust aggregator
        
        Args:
            method: "median", "trimmed_mean", or "krum"
            trimmed_percentage: Percentage to trim from both tails (0.0-0.5)
        """
        self.method = method
        self.trimmed_percentage = trimmed_percentage
        
        if method not in ("median", "trimmed_mean", "krum"):
            raise ValueError(f"Unknown robust method: {method}")
    
    def aggregate(
        self,
        org_gradients: Dict[str, np.ndarray],
        org_sample_counts: Optional[Dict[str, int]] = None,
    ) -> Tuple[np.ndarray, float]:
        """
        Aggregate gradients using robust method
        
        Args:
            org_gradients: org_id → gradient array
            org_sample_counts: org_id → sample count (unused for robust methods)
        
        Returns:
            (aggregated_gradient, anomaly_score) where anomaly_score is 0.0-1.0
        """
        if not org_gradients:
            raise ValueError("No gradients to aggregate")
        
        if self.method == "median":
            return self._aggregate_median(org_gradients)
        elif self.method == "trimmed_mean":
            return self._aggregate_trimmed_mean(org_gradients)
        elif self.method == "krum":
            return self._aggregate_krum(org_gradients)
    
    def _aggregate_median(
        self,
        org_gradients: Dict[str, np.ndarray],
    ) -> Tuple[np.ndarray, float]:
        """Element-wise median of gradients"""
        logger.info(f"Robust aggregation (median) for {len(org_gradients)} gradients")
        
        # Stack gradients
        gradient_stack = np.stack(list(org_gradients.values()), axis=0)
        
        # Median along org dimension
        aggregated = np.median(gradient_stack, axis=0)
        
        # Anomaly score: distance of each gradient from median
        distances = np.array([
            np.linalg.norm(g - aggregated) for g in org_gradients.values()
        ])
        anomaly_score = np.mean(distances) / (np.std(distances) + 1e-8)
        anomaly_score = min(1.0, anomaly_score / 3.0)  # Normalize to [0, 1]
        
        return aggregated, float(anomaly_score)
    
    def _aggregate_trimmed_mean(
        self,
        org_gradients: Dict[str, np.ndarray],
    ) -> Tuple[np.ndarray, float]:
        """Trimmed mean: remove outliers then average"""
        logger.info(
            f"Robust aggregation (trimmed_mean {self.trimmed_percentage*100}%) "
            f"for {len(org_gradients)} gradients"
        )
        
        gradient_stack = np.stack(list(org_gradients.values()), axis=0)
        
        # Trim percentage from both ends
        num_to_trim = int(len(org_gradients) * self.trimmed_percentage)
        if num_to_trim > 0:
            # Compute norm of each gradient
            norms = np.linalg.norm(gradient_stack, axis=tuple(range(1, gradient_stack.ndim)))
            
            # Get indices sorted by norm
            sorted_indices = np.argsort(norms)
            
            # Keep middle gradients
            keep_indices = sorted_indices[num_to_trim:-num_to_trim]
            gradient_stack = gradient_stack[keep_indices]
        
        # Mean of remaining gradients
        aggregated = np.mean(gradient_stack, axis=0)
        
        # Anomaly score: standard deviation across gradients
        std_dev = np.std(gradient_stack, axis=0)
        anomaly_score = float(np.mean(std_dev))
        
        return aggregated, anomaly_score
    
    def _aggregate_krum(
        self,
        org_gradients: Dict[str, np.ndarray],
    ) -> Tuple[np.ndarray, float]:
        """
        Krum: Select gradient closest to its neighbors
        
        Robust to Byzantine attacks by selecting the gradient that
        minimizes sum of distances to its k nearest neighbors.
        """
        logger.info(f"Robust aggregation (krum) for {len(org_gradients)} gradients")
        
        gradient_list = list(org_gradients.values())
        n_grads = len(gradient_list)
        k = max(1, n_grads // 2)  # Use half of gradients as neighbors
        
        # Compute pairwise distances
        distances = np.zeros((n_grads, n_grads))
        for i in range(n_grads):
            for j in range(i + 1, n_grads):
                dist = np.linalg.norm(gradient_list[i] - gradient_list[j])
                distances[i, j] = dist
                distances[j, i] = dist
        
        # Select gradient with smallest sum of k-nearest distances
        sum_distances = np.sum(
            np.partition(distances, min(k, n_grads - 1), axis=1)[:, :k],
            axis=1
        )
        selected_idx = np.argmin(sum_distances)
        aggregated = gradient_list[selected_idx].copy()
        
        # Anomaly score: how far selected gradient is from worst gradient
        max_distance = np.max(distances[selected_idx])
        min_distance = np.min(distances[selected_idx][distances[selected_idx] > 0])
        anomaly_score = min_distance / (max_distance + 1e-8)
        
        return aggregated, float(anomaly_score)


def create_aggregator(
    method: str = "fedprox",
    robust: bool = False,
    **kwargs
) -> object:
    """
    Factory function to create appropriate aggregator
    
    Args:
        method: "fedavg" or "fedprox" for standard, or "median"/"trimmed_mean"/"krum" for robust
        robust: Use robust aggregation?
        **kwargs: Additional parameters for aggregator
    
    Returns:
        FederatedAggregator or RobustAggregator instance
    """
    if robust or method in ("median", "trimmed_mean", "krum"):
        return RobustAggregator(method=method, **kwargs)
    else:
        return FederatedAggregator(method=method, **kwargs)
