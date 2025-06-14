# Learn - Pure Lua Neural Network Library

Learn is a lightweight, pure Lua implementation of neural networks designed for flexibility and portability. It provides an API similar to [Torch](http://torch.ch/) and [Scikit Learn](http://scikit-learn.org/stable/), making it easy to get started with neural networks in Lua without external dependencies.

## Features

- **Pure Lua**: No external dependencies or C bindings required
- **Portable**: Works anywhere Lua runs
- **Flexible**: Modular architecture for building custom neural networks
- **Educational**: Clean, readable code perfect for learning neural network internals
- **MIT Licensed**: Free for commercial and non-commercial use

## Important Note

Learn is designed for educational purposes and small-scale projects. It is **not** multithreaded and does **not** use hardware acceleration. For high-performance production use, consider [Torch](http://torch.ch/) instead.

## Installation

### As a Git Submodule

```bash
git submodule add https://github.com/Polkm/learn.git learn
```

### Manual Installation

Simply clone or download the repository and place it in your project directory:

```bash
git clone https://github.com/Polkm/learn.git
```

## Quick Start

```lua
-- Load the library
require("learn/learn")

-- XOR training data
local train_features = {{0, 0}, {0, 1}, {1, 0}, {1, 1}}
local train_labels = {{0}, {1}, {1}, {0}}

-- Define network dimensions
local n_input = #train_features[1]
local n_output = #train_labels[1]

-- Create a neural network model
local model = learn.model.nnet({modules = {
  learn.layer.linear({n_input = n_input, n_output = n_input * 3}),
  learn.transfer.sigmoid({}),
  learn.layer.linear({n_input = n_input * 3, n_output = n_output}),
  learn.transfer.sigmoid({}),
}})

-- Train the model
local epochs = 1000
local error = model.fit(train_features, train_labels, epochs)

-- Make predictions
for _, prediction in pairs(model.predict(train_features)) do
  print(table.concat(prediction, ", "))
end
```

## Core Components

### Tensors
Learn includes a simple 2D tensor class for matrix operations:

```lua
-- Create a tensor
local t = learn.tensor({data = {1, 2, 3, 4}, size = {2, 2}})

-- Basic operations
local t2 = t.add(another_tensor)  -- Element-wise addition
local t3 = t.dot(another_tensor)  -- Matrix multiplication
local t4 = t.transpose()          -- Transpose
```

### Layers
- **Linear Layer**: Fully connected layer with learnable weights
  ```lua
  learn.layer.linear({n_input = 10, n_output = 5})
  ```

### Transfer Functions
- **Sigmoid**: Classic sigmoid activation
  ```lua
  learn.transfer.sigmoid({})
  ```
- **Tanh**: Hyperbolic tangent activation
  ```lua
  learn.transfer.tanh({})
  ```
- **ReLU**: Rectified Linear Unit
  ```lua
  learn.transfer.relu({})
  ```

### Loss Functions
- **MSE**: Mean Squared Error (default for regression)
  ```lua
  learn.criterion.mse({})
  ```

## Advanced Usage

### Custom Network Architecture

```lua
-- Multi-layer network with different activation functions
local model = learn.model.nnet({modules = {
  learn.layer.linear({n_input = 784, n_output = 128}),
  learn.transfer.relu({}),
  learn.layer.linear({n_input = 128, n_output = 64}),
  learn.transfer.relu({}),
  learn.layer.linear({n_input = 64, n_output = 10}),
  learn.transfer.sigmoid({}),
}})
```

### Training with Custom Parameters

```lua
local epochs = 1000
local learning_rate = 0.5
local verbose = true  -- Print training progress

local final_error = model.fit(
  train_features, 
  train_labels, 
  epochs, 
  learning_rate, 
  verbose
)
```

### Data Normalization

Learn automatically normalizes input features and labels during training to improve convergence. The normalization is reversed when making predictions.

## Examples

### Regression Example

```lua
-- Training data: simple linear relationship
local train_features = {{1}, {2}, {3}, {4}, {5}}
local train_labels = {{2}, {4}, {6}, {8}, {10}}

-- Create a simple linear model
local model = learn.model.nnet({modules = {
  learn.layer.linear({n_input = 1, n_output = 1})
}})

-- Train the model
model.fit(train_features, train_labels, 100)

-- Test predictions
local predictions = model.predict({{6}, {7}})
-- Should output values close to {12}, {14}
```

### Multi-Output Example

```lua
-- Training data with multiple outputs
local train_features = {{0, 0}, {0, 1}, {1, 0}, {1, 1}}
local train_labels = {{0, 0}, {0, 1}, {1, 0}, {1, 1}}

-- Network with 2 inputs and 2 outputs
local model = learn.model.nnet({modules = {
  learn.layer.linear({n_input = 2, n_output = 4}),
  learn.transfer.tanh({}),
  learn.layer.linear({n_input = 4, n_output = 2}),
  learn.transfer.tanh({}),
}})

model.fit(train_features, train_labels, 1000)
```

## Testing

Run the built-in test suite:

```lua
learn.test()
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Author

Created by Matthew Nichols

## See Also

- [API Documentation](API.md) - Detailed API reference
- [Torch](http://torch.ch/) - High-performance neural network library
- [Scikit Learn](http://scikit-learn.org/stable/) - Python machine learning library