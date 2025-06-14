# Learn API Documentation

This document provides detailed API documentation for the Learn neural network library.

## Table of Contents

- [Global Functions](#global-functions)
- [Tensor Class](#tensor-class)
- [Model Module](#model-module)
- [Layer Module](#layer-module)
- [Transfer Module](#transfer-module)
- [Criterion Module](#criterion-module)

## Global Functions

### `learn.gaussian(mean, sd)`

Returns a random sample from a Gaussian distribution.

**Parameters:**
- `mean` (number): Mean of the distribution
- `sd` (number): Standard deviation

**Returns:**
- (number): Random sample from the specified Gaussian distribution

**Example:**
```lua
local random_weight = learn.gaussian(0.0, 1.0)
```

### `learn.normalize(samples)`

Normalizes a dataset by dividing all values by the maximum absolute value found.

**Parameters:**
- `samples` (table): Array of feature vectors

**Returns:**
- (number): The maximum absolute value used for normalization

**Example:**
```lua
local data = {{1, 2}, {3, 4}, {5, 6}}
local max_val = learn.normalize(data)
-- data is now normalized in-place
```

### `learn.unormalize(samples, max)`

Reverses normalization by multiplying all values by the provided maximum.

**Parameters:**
- `samples` (table): Array of normalized feature vectors
- `max` (number): The maximum value used during normalization

**Example:**
```lua
learn.unormalize(predictions, max_val)
```

### `learn.test()`

Runs the built-in unit tests for the library.

## Tensor Class

### Constructor: `learn.tensor(params)`

Creates a new 2D tensor for matrix operations.

**Parameters:**
- `params` (table):
  - `data` (table, optional): Flat array of values
  - `size` (table, optional): Array with two elements [rows, cols]. Default: {#data, 1}

**Example:**
```lua
local t = learn.tensor({
  data = {1, 2, 3, 4},
  size = {2, 2}
})
-- Creates a 2x2 matrix:
-- 1 2
-- 3 4
```

### Methods

#### `tensor.set(value, x, y)`
Sets the value at position (x, y).

**Parameters:**
- `value` (number): Value to set
- `x` (number): Row index (1-based)
- `y` (number): Column index (1-based)

#### `tensor.get(x, y)`
Gets the value at position (x, y).

**Parameters:**
- `x` (number): Row index (1-based)
- `y` (number): Column index (1-based)

**Returns:**
- (number): Value at the specified position

#### `tensor.copy()`
Creates a deep copy of the tensor.

**Returns:**
- (tensor): New tensor with copied values

#### `tensor.each(func)`
Applies a function to each element.

**Parameters:**
- `func` (function): Function called with (value, x, y) for each element

**Returns:**
- (tensor): Self (for chaining)

#### `tensor.map(func)`
Transforms each element using the provided function.

**Parameters:**
- `func` (function): Function called with (value, x, y) that returns new value

**Returns:**
- (tensor): Self (modified in-place)

#### `tensor.add(b)`
Element-wise addition.

**Parameters:**
- `b` (tensor): Tensor to add

**Returns:**
- (tensor): Self (modified in-place)

#### `tensor.sub(b)`
Element-wise subtraction.

**Parameters:**
- `b` (tensor): Tensor to subtract

**Returns:**
- (tensor): Self (modified in-place)

#### `tensor.mul(b)`
Element-wise multiplication.

**Parameters:**
- `b` (tensor): Tensor to multiply

**Returns:**
- (tensor): Self (modified in-place)

#### `tensor.div(b)`
Element-wise division.

**Parameters:**
- `b` (tensor): Tensor to divide by

**Returns:**
- (tensor): Self (modified in-place)

#### `tensor.scale(s)`
Multiplies all elements by a scalar.

**Parameters:**
- `s` (number): Scalar value

**Returns:**
- (tensor): Self (modified in-place)

#### `tensor.pow(e)`
Raises each element to the power e.

**Parameters:**
- `e` (number): Exponent

**Returns:**
- (tensor): Self (modified in-place)

#### `tensor.sum(result)`
Sums all elements in the tensor.

**Parameters:**
- `result` (tensor, optional): Tensor to store result in

**Returns:**
- (tensor): 1x1 tensor containing the sum

#### `tensor.dot(b, result)`
Matrix multiplication.

**Parameters:**
- `b` (tensor): Right-hand tensor
- `result` (tensor, optional): Tensor to store result in

**Returns:**
- (tensor): Result of matrix multiplication

**Example:**
```lua
local a = learn.tensor({data = {1, 2, 3, 4}, size = {2, 2}})
local b = learn.tensor({data = {5, 6, 7, 8}, size = {2, 2}})
local c = a.dot(b)  -- Matrix multiplication
```

#### `tensor.transpose()`
Returns the transpose of the tensor.

**Returns:**
- (tensor): New transposed tensor

#### `tensor.string()`
Returns a string representation of the tensor.

**Returns:**
- (string): Human-readable representation

## Model Module

### `learn.model.nnet(params)`

Creates a neural network model.

**Parameters:**
- `params` (table):
  - `modules` (table): Array of layer/transfer modules
  - `criterion` (criterion, optional): Loss function. Default: MSE
  - `n_input` (number, optional): Number of input features
  - `n_output` (number, optional): Number of output features

**Example:**
```lua
local model = learn.model.nnet({
  modules = {
    learn.layer.linear({n_input = 2, n_output = 4}),
    learn.transfer.sigmoid({}),
    learn.layer.linear({n_input = 4, n_output = 1}),
    learn.transfer.sigmoid({})
  }
})
```

### Methods

#### `model.forward(input)`
Performs forward propagation through the network.

**Parameters:**
- `input` (tensor): Input tensor

**Returns:**
- (tensor): Output tensor

#### `model.backward(input, gradients)`
Performs backward propagation of gradients.

**Parameters:**
- `input` (tensor): Original input
- `gradients` (tensor): Gradient tensor from loss function

#### `model.update(input, learning_rate)`
Updates network weights using the computed gradients.

**Parameters:**
- `input` (tensor): Original input
- `learning_rate` (number): Learning rate for weight updates

#### `model.fit(features, labels, epochs, learning_rate, verbose)`
Trains the model on the provided data.

**Parameters:**
- `features` (table): Array of input feature vectors
- `labels` (table): Array of target label vectors
- `epochs` (number): Number of training epochs
- `learning_rate` (number, optional): Learning rate. Default: 0.01
- `verbose` (boolean, optional): Print training progress

**Returns:**
- (number): Final average error

**Example:**
```lua
local error = model.fit(train_features, train_labels, 1000, 0.5, true)
```

#### `model.predict(features)`
Makes predictions on new data.

**Parameters:**
- `features` (table): Array of input feature vectors

**Returns:**
- (table): Array of prediction vectors

## Layer Module

### `learn.layer.linear(params)`

Creates a fully connected linear layer.

**Parameters:**
- `params` (table):
  - `n_input` (number): Number of input units
  - `n_output` (number): Number of output units
  - `weight_init` (function, optional): Weight initialization function. Default: Gaussian(0, 1)
  - `weights` (tensor, optional): Pre-initialized weight tensor
  - `gradients` (tensor, optional): Gradient tensor

**Example:**
```lua
local layer = learn.layer.linear({
  n_input = 10,
  n_output = 5,
  weight_init = function() return learn.gaussian(0.0, 0.1) end
})
```

### Methods

#### `layer.forward(input)`
Computes the layer's output.

**Parameters:**
- `input` (tensor): Input tensor

**Returns:**
- (tensor): Output tensor (weights × input)

#### `layer.backward(input, gradients)`
Computes gradients for backpropagation.

**Parameters:**
- `input` (tensor): Original input
- `gradients` (tensor): Gradient from next layer

**Returns:**
- `input` (tensor): Original input
- `gradients` (tensor): Gradients to propagate backward

#### `layer.update(input, learning_rate)`
Updates the layer's weights.

**Parameters:**
- `input` (tensor): Original input
- `learning_rate` (number): Learning rate

**Returns:**
- (tensor): Layer output

## Transfer Module

### Base Transfer Function

#### `learn.transfer.transfer(params)`
Base class for all transfer functions.

**Parameters:**
- `params` (table): Configuration parameters

### Activation Functions

#### `learn.transfer.sigmoid(params)`
Sigmoid activation function: f(x) = 1 / (1 + e^(-x))

**Parameters:**
- `params` (table): Configuration parameters

**Example:**
```lua
local sigmoid = learn.transfer.sigmoid({})
```

#### `learn.transfer.tanh(params)`
Hyperbolic tangent activation: f(x) = (e^x - e^(-x)) / (e^x + e^(-x))

**Parameters:**
- `params` (table): Configuration parameters

#### `learn.transfer.relu(params)`
Rectified Linear Unit: f(x) = max(0, x)

**Parameters:**
- `params` (table): Configuration parameters

### Transfer Function Methods

All transfer functions share these methods:

#### `transfer.forward(input)`
Applies the activation function.

**Parameters:**
- `input` (tensor): Input tensor

**Returns:**
- (tensor): Activated output

#### `transfer.backward(input, gradients)`
Computes gradients using the derivative.

**Parameters:**
- `input` (tensor): Original input
- `gradients` (tensor): Gradient from next layer

**Returns:**
- `output` (tensor): Derivative values
- `gradients` (tensor): Gradients to propagate

#### `transfer.update(input)`
No-op for transfer functions (no weights to update).

**Returns:**
- (tensor): Layer output

## Criterion Module

### `learn.criterion.mse(params)`

Mean Squared Error loss function.

**Parameters:**
- `params` (table): Configuration parameters

**Example:**
```lua
local criterion = learn.criterion.mse({})
```

### Methods

#### `criterion.forward(predictions, target)`
Computes the loss value.

**Parameters:**
- `predictions` (tensor): Model predictions
- `target` (tensor): Target values

**Returns:**
- (number): Mean squared error loss

#### `criterion.backward(predictions, target)`
Computes gradients of the loss.

**Parameters:**
- `predictions` (tensor): Model predictions
- `target` (tensor): Target values

**Returns:**
- (tensor): Gradient tensor for backpropagation

## Complete Example

```lua
require("learn/learn")

-- Prepare data
local features = {{0, 0}, {0, 1}, {1, 0}, {1, 1}}
local labels = {{0}, {1}, {1}, {0}}

-- Create model
local model = learn.model.nnet({
  modules = {
    learn.layer.linear({n_input = 2, n_output = 3}),
    learn.transfer.sigmoid({}),
    learn.layer.linear({n_input = 3, n_output = 1}),
    learn.transfer.sigmoid({})
  },
  criterion = learn.criterion.mse({})
})

-- Train
local final_error = model.fit(features, labels, 1000, 0.5, true)
print("Final error: " .. final_error)

-- Predict
local predictions = model.predict(features)
for i, pred in ipairs(predictions) do
  print(string.format("Input: [%d, %d], Predicted: %.3f, Target: %d",
    features[i][1], features[i][2], pred[1], labels[i][1]))
end
```