"""
Federated Models: TGNN and RL

Federated implementations of Temporal Graph Neural Networks and Reinforcement Learning
for distributed threat detection and policy optimization across organizations.
"""

from typing import Dict, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger("jarvis.fl_blockchain.models")


class FederatedTGNNModel:
    """
    Federated Temporal Graph Neural Network

    Threat detection model that operates on temporal threat graphs:
    - Nodes: threats, hosts, users (local)
    - Edges: relationships (temporal)
    - Federated aggregation: shares node embeddings, not raw data

    Each organization maintains:
    - Local graph structure (threat relationships)
    - Local feature embeddings
    - Aggregated global embeddings (shared weights)
    """
    
    def __init__(self, embedding_dim: int = 128):
        """
        Initialize Federated TGNN
        
        Args:
            embedding_dim: Dimension of threat embeddings
        """
        self.embedding_dim = embedding_dim
        
        # Shared global embeddings (aggregated across organizations)
        self.global_threat_embeddings: Optional[np.ndarray] = None  # shape: (num_threat_types, embedding_dim)
        self.global_relationship_weights: Optional[np.ndarray] = None
        
        logger.info(f"FederatedTGNNModel initialized (embedding_dim={embedding_dim})")
    
    def initialize_embeddings(self, num_threat_types: int) -> None:
        """Initialize global embeddings"""
        self.global_threat_embeddings = np.random.randn(num_threat_types, self.embedding_dim) * 0.01
        self.global_relationship_weights = np.eye(num_threat_types) * 0.5
    
    def local_forward_pass(
        self,
        local_graph_features: np.ndarray,
        local_adjacency: np.ndarray,
    ) -> np.ndarray:
        """
        Local forward pass (at each organization)
        
        Args:
            local_graph_features: Local threat embeddings
            local_adjacency: Adjacency matrix for local threats
        
        Returns:
            Updated local embeddings after graph convolution
        """
        if self.global_threat_embeddings is None:
            raise RuntimeError("Embeddings not initialized")
        
        # Graph convolution: h' = σ(A @ W @ h)
        aggregated = local_adjacency @ self.global_threat_embeddings
        
        return aggregated
    
    def compute_local_gradients(
        self,
        predictions: np.ndarray,
        targets: np.ndarray,
    ) -> np.ndarray:
        """
        Compute local gradients (at each organization)
        
        Args:
            predictions: Model predictions on local data
            targets: Ground truth labels
        
        Returns:
            Gradient of loss w.r.t. embeddings
        """
        # Simple MSE loss: L = ||pred - target||^2
        error = predictions - targets
        gradient = 2.0 * error  # dL/d(pred)
        
        return gradient


class FederatedRLPolicy:
    """
    Federated Reinforcement Learning Policy

    Policy for optimizing interventions across organizations:
    - State: Current threat situation (aggregated threat intelligence)
    - Action: Intervention strategy (block, quarantine, alert, etc.)
    - Reward: Impact on threat reduction
    - Federated update: Organizations share policy gradients

    Each organization learns locally, shares gradients globally.
    """
    
    def __init__(self, state_dim: int = 64, action_dim: int = 8):
        """
        Initialize Federated RL Policy
        
        Args:
            state_dim: Dimension of threat state representation
            action_dim: Number of intervention actions
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Policy network weights (shared across organizations)
        self.policy_weights = np.random.randn(state_dim, action_dim) * 0.01
        
        # Learning rate for policy gradient updates
        self.learning_rate = 0.01
        
        logger.info(f"FederatedRLPolicy initialized (state_dim={state_dim}, action_dim={action_dim})")
    
    def select_action(
        self,
        state: np.ndarray,
        epsilon_greedy: float = 0.1,
    ) -> Tuple[int, float]:
        """
        Select intervention action given state
        
        Args:
            state: Current threat state (size: state_dim)
            epsilon_greedy: Exploration probability
        
        Returns:
            (action_id, action_value)
        """
        if np.random.rand() < epsilon_greedy:
            # Explore: random action
            action = np.random.randint(0, self.action_dim)
        else:
            # Exploit: argmax action
            action_values = state @ self.policy_weights
            action = np.argmax(action_values)
        
        action_value = (state @ self.policy_weights)[action]
        return action, float(action_value)
    
    def compute_policy_gradient(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        gamma: float = 0.99,
    ) -> np.ndarray:
        """
        Compute policy gradient (for one transition)
        
        Args:
            state: Current state
            action: Taken action
            reward: Received reward
            next_state: Resulting state
            gamma: Discount factor
        
        Returns:
            Policy gradient (shape: state_dim × action_dim)
        """
        # Q-learning: Q(s,a) = r + γ * max(Q(s',a'))
        current_q = (state @ self.policy_weights)[action]
        next_q = np.max(next_state @ self.policy_weights)
        target_q = reward + (gamma * next_q)
        
        # TD error
        td_error = target_q - current_q
        
        # Policy gradient: ∂L/∂W = -state ⊗ action_one_hot * td_error
        action_one_hot = np.zeros(self.action_dim)
        action_one_hot[action] = 1.0
        
        gradient = -np.outer(state, action_one_hot) * td_error
        
        return gradient


class FederatedModelState:
    """
    Manages shared model state across federation
    """
    
    def __init__(self):
        """Initialize federated model state"""
        self.tgnn_model = FederatedTGNNModel()
        self.rl_policy = FederatedRLPolicy()
        self.model_version = "v1.0"
        self.last_update = None
    
    def aggregate_tgnn_gradients(
        self,
        org_gradients: Dict[str, np.ndarray],
        weights: Dict[str, float],
    ) -> np.ndarray:
        """Aggregate TGNN gradients across organizations"""
        aggregated = None
        total_weight = sum(weights.values())
        
        for org_id, gradient in org_gradients.items():
            weight = weights.get(org_id, 0.0) / total_weight
            if aggregated is None:
                aggregated = weight * gradient
            else:
                aggregated = aggregated + (weight * gradient)
        
        return aggregated
    
    def aggregate_rl_gradients(
        self,
        org_gradients: Dict[str, np.ndarray],
        weights: Dict[str, float],
    ) -> np.ndarray:
        """Aggregate RL policy gradients across organizations"""
        return self.aggregate_tgnn_gradients(org_gradients, weights)
    
    def update_tgnn(self, aggregated_gradient: np.ndarray, learning_rate: float = 0.01) -> None:
        """Update TGNN weights with aggregated gradient"""
        if self.tgnn_model.global_threat_embeddings is None:
            return
        
        self.tgnn_model.global_threat_embeddings = (
            self.tgnn_model.global_threat_embeddings - (learning_rate * aggregated_gradient)
        )
    
    def update_rl_policy(self, aggregated_gradient: np.ndarray, learning_rate: float = 0.01) -> None:
        """Update RL policy weights with aggregated gradient"""
        self.rl_policy.policy_weights = (
            self.rl_policy.policy_weights - (learning_rate * aggregated_gradient)
        )
