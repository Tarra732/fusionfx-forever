# agents/models/q_network.py

import numpy as np
import pickle
import os
from pathlib import Path

class DeepQNetwork:
    """Simple Deep Q-Network implementation using numpy"""
    
    def __init__(self, input_dim, output_dim, hidden_dims=[64, 32], learning_rate=0.001):
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        
        # Initialize network weights
        self.weights = []
        self.biases = []
        
        # Input to first hidden layer
        dims = [input_dim] + hidden_dims + [output_dim]
        for i in range(len(dims) - 1):
            w = np.random.randn(dims[i], dims[i+1]) * np.sqrt(2.0 / dims[i])
            b = np.zeros((1, dims[i+1]))
            self.weights.append(w)
            self.biases.append(b)
        
        # Experience replay buffer
        self.memory = []
        self.memory_size = 10000
        
        # Model save path
        self.model_path = Path("models/q_network.pkl")
        self.model_path.parent.mkdir(exist_ok=True)
        
        # Load existing model if available
        self.load_model()
    
    def relu(self, x):
        """ReLU activation function"""
        return np.maximum(0, x)
    
    def relu_derivative(self, x):
        """Derivative of ReLU"""
        return (x > 0).astype(float)
    
    def forward(self, x):
        """Forward pass through the network"""
        if x.ndim == 1:
            x = x.reshape(1, -1)
        
        activations = [x]
        z_values = []
        
        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            z = np.dot(activations[-1], w) + b
            z_values.append(z)
            
            if i < len(self.weights) - 1:  # Hidden layers
                a = self.relu(z)
            else:  # Output layer (linear)
                a = z
            activations.append(a)
        
        return activations, z_values
    
    def predict(self, state):
        """Predict Q-values for a given state"""
        activations, _ = self.forward(state)
        q_values = activations[-1]
        return np.argmax(q_values[0])
    
    def get_q_values(self, state):
        """Get Q-values for a given state"""
        activations, _ = self.forward(state)
        return activations[-1][0]
    
    def train(self, state, action, reward, next_state, gamma=0.99):
        """Train the network using Q-learning"""
        # Add experience to memory
        experience = (state, action, reward, next_state)
        self.memory.append(experience)
        
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)
        
        # Train on current experience
        self._train_step(state, action, reward, next_state, gamma)
        
        # Occasionally train on random batch from memory
        if len(self.memory) > 32 and np.random.random() < 0.1:
            batch = np.random.choice(len(self.memory), size=min(32, len(self.memory)), replace=False)
            for idx in batch:
                s, a, r, ns = self.memory[idx]
                self._train_step(s, a, r, ns, gamma)
    
    def _train_step(self, state, action, reward, next_state, gamma):
        """Single training step"""
        # Forward pass for current state
        activations, z_values = self.forward(state)
        current_q = activations[-1][0]
        
        # Calculate target Q-value
        next_q_values = self.get_q_values(next_state)
        target_q = current_q.copy()
        target_q[action] = reward + gamma * np.max(next_q_values)
        
        # Backward pass
        self._backward(activations, z_values, target_q)
    
    def _backward(self, activations, z_values, target):
        """Backward pass to update weights"""
        # Calculate output layer error
        output_error = activations[-1] - target.reshape(1, -1)
        
        # Backpropagate errors
        errors = [output_error]
        for i in range(len(self.weights) - 2, -1, -1):
            error = np.dot(errors[0], self.weights[i+1].T) * self.relu_derivative(z_values[i])
            errors.insert(0, error)
        
        # Update weights and biases
        for i in range(len(self.weights)):
            self.weights[i] -= self.learning_rate * np.dot(activations[i].T, errors[i])
            self.biases[i] -= self.learning_rate * np.mean(errors[i], axis=0, keepdims=True)
    
    def save_model(self):
        """Save the model to disk"""
        model_data = {
            'weights': self.weights,
            'biases': self.biases,
            'memory': self.memory[-1000:],  # Save last 1000 experiences
            'input_dim': self.input_dim,
            'output_dim': self.output_dim,
            'hidden_dims': self.hidden_dims
        }
        
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self):
        """Load the model from disk"""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    model_data = pickle.load(f)
                
                self.weights = model_data['weights']
                self.biases = model_data['biases']
                self.memory = model_data.get('memory', [])
                
                print(f"[Q-Network] Loaded model from {self.model_path}")
            except Exception as e:
                print(f"[Q-Network] Failed to load model: {e}")
    
    def __del__(self):
        """Save model when object is destroyed"""
        try:
            self.save_model()
        except:
            pass