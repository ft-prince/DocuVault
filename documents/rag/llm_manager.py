"""
LLM (Large Language Model) management module
Handles loading and inference with quantized models
"""

import torch
from typing import List, Dict
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from .config import RAGConfig


class LLMManager:
    """Manages LLM loading, tokenization, and text generation"""
    
    def __init__(self, config: RAGConfig = None):
        """
        Initialize LLM manager
        
        Args:
            config: RAGConfig instance. If None, uses default.
        """
        self.config = config or RAGConfig()
        self.model = None
        self.tokenizer = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    def load_model(self):
        """Load the LLM model with 8-bit quantization"""
        if self.model is not None:
            print("LLM model already loaded")
            return
        
        print(f"Loading LLM: {self.config.LLM_MODEL}")
        print("This may take a few minutes...")
        
        # Configure 8-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_8bit=self.config.USE_8BIT_QUANTIZATION,
            llm_int8_threshold=self.config.LLM_INT8_THRESHOLD,
            llm_int8_enable_fp32_cpu_offload=False
        )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.LLM_MODEL,
            trust_remote_code=True
        )
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.LLM_MODEL,
            quantization_config=bnb_config if self.config.USE_8BIT_QUANTIZATION else None,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16
        )
        
        # Set padding token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        
        memory_footprint = self.model.get_memory_footprint() / 1e9
        print(f"✅ Model loaded! Memory footprint: {memory_footprint:.2f} GB")
    
    def generate(self, messages: List[Dict[str, str]], max_new_tokens: int = None,
                temperature: float = None, do_sample: bool = True) -> str:
        """
        Generate text response from messages
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_new_tokens: Maximum tokens to generate. If None, uses config.
            temperature: Sampling temperature. If None, uses config.
            do_sample: Whether to use sampling
            
        Returns:
            Generated text
        """
        if self.model is None:
            self.load_model()
        
        if max_new_tokens is None:
            max_new_tokens = self.config.MAX_NEW_TOKENS
        
        if temperature is None:
            temperature = self.config.TEMPERATURE
        
        # Apply chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=4096
        ).to(self.model.device)
        
        input_length = inputs["input_ids"].shape[1]
        
        # Prepare stop token IDs
        stop_token_ids = [self.tokenizer.eos_token_id] + self.config.STOP_TOKEN_IDS
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=self.config.TOP_P if do_sample else None,
                do_sample=do_sample,
                repetition_penalty=self.config.REPETITION_PENALTY,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=stop_token_ids
            )
        
        # Decode only the generated tokens
        response_tokens = outputs[0][input_length:]
        response = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
        
        return response.strip()
    
    def rewrite_question(self, question: str, chat_history: List) -> str:
        """
        Rewrite follow-up question to be standalone using conversation history
        
        Args:
            question: Current question
            chat_history: List of previous messages
            
        Returns:
            Rewritten standalone question
        """
        if self.model is None:
            self.load_model()
        
        # If no history, return original question
        if not chat_history or len(chat_history) == 0:
            return question
        
        # Build history text from recent messages
        history_text = ""
        for msg in chat_history[-self.config.REWRITE_MAX_HISTORY:]:
            if hasattr(msg, 'type'):
                if msg.type == 'human':
                    history_text += f"Q: {msg.content[:100]}\n"
                elif msg.type == 'ai':
                    history_text += f"A: {msg.content[:100]}\n"
        
        # Prepare rewrite messages
        rewrite_messages = [
            {
                "role": "system",
                "content": self.config.REWRITE_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": f"""Context:
{history_text}
Current question: {question}

Rewritten standalone question:"""
            }
        ]
        
        # Apply chat template
        prompt = self.tokenizer.apply_chat_template(
            rewrite_messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        ).to(self.model.device)
        
        input_length = inputs["input_ids"].shape[1]
        
        # Generate with strict parameters
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.config.REWRITE_MAX_TOKENS,
                temperature=self.config.REWRITE_TEMPERATURE,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=[self.tokenizer.eos_token_id] + self.config.STOP_TOKEN_IDS
            )
        
        response_tokens = outputs[0][input_length:]
        rewritten = self.tokenizer.decode(response_tokens, skip_special_tokens=True).strip()
        
        # Take only first line
        rewritten = rewritten.split('\n')[0].strip()
        
        # Validate rewritten question
        if (len(rewritten) > 250 or
            len(rewritten) < 5 or
            "assistant" in rewritten.lower() or
            "context:" in rewritten.lower() or
            rewritten.count("?") > 2):
            print(f"⚠️ Rewrite validation failed, using original")
            return question
        
        print(f"🔄 Rewritten: {rewritten}")
        return rewritten
    
    def get_model_info(self) -> Dict:
        """
        Get information about loaded model
        
        Returns:
            Dictionary with model information
        """
        if self.model is None:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "model_name": self.config.LLM_MODEL,
            "device": str(self.model.device),
            "memory_footprint_gb": self.model.get_memory_footprint() / 1e9,
            "quantization": "8-bit" if self.config.USE_8BIT_QUANTIZATION else "None"
        }
