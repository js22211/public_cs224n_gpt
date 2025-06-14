import torch

from einops import rearrange
from torch import nn

# multi-head self Attention을 직접 구현한다. 
class CausalSelfAttention(nn.Module):
  def __init__(self, config):
    super().__init__() # 초기화 함수

    # 헤드 차원의 설정
    self.num_attention_heads = config.num_attention_heads
    self.attention_head_size = int(config.hidden_size / config.num_attention_heads)
    self.all_head_size = self.num_attention_heads * self.attention_head_size

    # Initialize the linear transformation layers for key, value, query.
    self.query = nn.Linear(config.hidden_size, self.all_head_size)
    self.key = nn.Linear(config.hidden_size, self.all_head_size)
    self.value = nn.Linear(config.hidden_size, self.all_head_size)
    # This dropout is applied to normalized attention scores following the original
    # implementation of transformer. Although it is a bit unusual, we empirically
    # observe that it yields better performance.
    self.dropout = nn.Dropout(config.attention_probs_dropout_prob)

  # 입력 벡터 x를 linear layer를 통해 변환하고 멀티 헤드 어텐션을 위해 [b, t, h, d] 형태로 변환한다.
  def transform(self, x, linear_layer):
    # The corresponding linear_layer of k, v, q are used to project the hidden_state (x).
    proj = linear_layer(x)
    # Next, we need to produce multiple heads for the proj. This is done by spliting the
    # hidden state to self.num_attention_heads, each of size self.attention_head_size.
    proj = rearrange(proj, 'b t (h d) -> b t h d', h=self.num_attention_heads)
    # By proper transpose, we have proj of size [bs, num_attention_heads, seq_len, attention_head_size].
    proj = rearrange(proj, 'b t h d -> b h t d')
    return proj

  def attention(self, key, query, value, attention_mask):

    ### YOUR CODE HERE
    seq_len = query.size(-2)
    causal_mask = torch.tril(
        torch.ones(seq_len, seq_len, device=query.device, dtype=torch.bool)
    ).view(1, 1, seq_len, seq_len)  # shape: [1, 1, T, T]

    # Scaled dot product
    attention_scores = torch.matmul(query, key.transpose(-1, -2))
    attention_scores = attention_scores / (self.attention_head_size ** 0.5)

    # Causal mask: block future tokens
    attention_scores = attention_scores.masked_fill(~causal_mask, float('-inf'))

    # Padding mask: added directly (already shaped [B, 1, 1, T])
    attention_scores = attention_scores + attention_mask

    # Softmax + dropout
    attention_probs = torch.softmax(attention_scores, dim=-1)
    attention_probs = self.dropout(attention_probs)

    # Weighted sum
    attn_value = torch.matmul(attention_probs, value)
    attn_value = rearrange(attn_value, 'b h t d -> b t (h d)')

    return attn_value
    ### END YOUR CODE HERE
    raise NotImplementedError


  def forward(self, hidden_states, attention_mask):
    """
    hidden_states: [bs, seq_len, hidden_state]
    attention_mask: [bs, 1, 1, seq_len]
    output: [bs, seq_len, hidden_state]
    """
    # First, we have to generate the key, value, query for each token for multi-head attention
    # using self.transform (more details inside the function).
    # Size of *_layer is [bs, num_attention_heads, seq_len, attention_head_size].
    key_layer = self.transform(hidden_states, self.key)
    value_layer = self.transform(hidden_states, self.value)
    query_layer = self.transform(hidden_states, self.query)
    
    # Calculate the multi-head attention.
    attn_value = self.attention(key_layer, query_layer, value_layer, attention_mask)
    return attn_value
