from torch import nn

import torch.nn.functional as F

from modules.attention import CausalSelfAttention

class GPT2Layer(nn.Module):
  def __init__(self, config):
    super().__init__()
    # Multi-head attention.
    self.self_attention = CausalSelfAttention(config)
    # Add-norm for multi-head attention.
    self.attention_dense = nn.Linear(config.hidden_size, config.hidden_size)
    self.attention_layer_norm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
    self.attention_dropout = nn.Dropout(config.hidden_dropout_prob)
    # Feed forward.
    self.interm_dense = nn.Linear(config.hidden_size, config.intermediate_size)
    self.interm_af = F.gelu
    # Add-norm for feed forward.
    self.out_dense = nn.Linear(config.intermediate_size, config.hidden_size)
    self.out_layer_norm = nn.LayerNorm(config.hidden_size, eps=config.layer_norm_eps)
    self.out_dropout = nn.Dropout(config.hidden_dropout_prob)

  def add(self, input, output, dense_layer, dropout):
    """
    TODO: Implement this helper method for the forward function.
      - This function is applied after the multi-head attention layer as well as after the feed forward layer.
      - GPT-2 layer applies dropout to the transformed output of each sub-layer,
        before it is added to the sub-layer input. WE DO NOT APPLY THE LAYER NORM
        IN THIS FUNCTION.
    """
    output = dense_layer(output) # Attention output is transformed by a linear layer.
    output = dropout(output)
    output = input + output
    return output
    raise NotImplementedError


  def forward(self, hidden_states, attention_mask):
    """
    TODO: Implement the forward pass. Some key points to consider:
           - A multi-head attention layer (CausalSelfAttention) that computes self-attention based on masked inputs.
           - Layer normalization applied *before* the attention layer and feed-forward layer.
           - Apply dropout, residual connection, and layer normalization according to the plot in the assignment. (Use self.add)
           - A feed-forward layer that applies transformations to further refine the hidden states.
    """
    # Self-Attention block
    normed_input = self.attention_layer_norm(hidden_states) # Normalize the input before self-attention
    attn_output = self.self_attention(normed_input, attention_mask) # Causal self-attention
    hidden_states = self.add(hidden_states, attn_output, self.attention_dense, self.attention_dropout) # Dense-dropout-add for attention output

    # Feed Forward block
    normed_input = self.out_layer_norm(hidden_states) # attention output is normalized before feed forward
    ff_output = self.interm_af(self.interm_dense(normed_input)) # Feed forward layer with activation
    hidden_states = self.add(hidden_states, ff_output, self.out_dense, self.out_dropout) # second Dense-dropout-add for feed forward output
    
    return hidden_states
    ### YOUR CODE HERE
    raise NotImplementedError

