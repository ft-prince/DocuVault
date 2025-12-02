"""
LLM management module
Handles loading and inference with quantized models using LangChain wrappers.
"""

import torch
from typing import List, Dict, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline
import os
from dotenv import load_dotenv
load_dotenv()

# Modern LangChain Imports
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from .config import RAGConfig

class LLMManager:
    """Manages LLM loading and inference using LangChain's modern ChatHuggingFace wrapper."""
    
    def __init__(self, config: RAGConfig = None):
        self.config = config or RAGConfig()
        self.model = None
        self.tokenizer = None
        self.llm: Optional[ChatOpenAI] = None  # The LangChain Runnable
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    def load_model(self):
        """Load the LLM model with 8-bit quantization and wrap it in LangChain."""
        if self.llm is not None:
            print("LLM model already loaded")
            return
        
        print(f"Loading LLM: {self.config.LLM_MODEL}")
        print("This may take a few minutes...")
        
        # # 1. Configure Quantization (Kept from your original logic)
        # bnb_config = BitsAndBytesConfig(
        #     load_in_8bit=self.config.USE_8BIT_QUANTIZATION,
        #     llm_int8_threshold=self.config.LLM_INT8_THRESHOLD,
        #     llm_int8_enable_fp32_cpu_offload=False
        # )
        
        # # 2. Load Tokenizer & Model
        # self.tokenizer = AutoTokenizer.from_pretrained(
        #     self.config.LLM_MODEL,
        #     trust_remote_code=True
        # )
        
        # self.model = AutoModelForCausalLM.from_pretrained(
        #     self.config.LLM_MODEL,
        #     quantization_config=bnb_config if self.config.USE_8BIT_QUANTIZATION else None,
        #     device_map="auto",
        #     trust_remote_code=True,
        #     torch_dtype=torch.float16
        # )
        
        # # Fix padding token if missing
        # if self.tokenizer.pad_token is None:
        #     self.tokenizer.pad_token = self.tokenizer.eos_token
        #     self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        
        # # 3. Create HuggingFace Pipeline
        # # We wrap the specific model/tokenizer in a standard pipeline
        # text_generation_pipeline = pipeline(
        #     "text-generation",
        #     model=self.model,
        #     tokenizer=self.tokenizer,
        #     max_new_tokens=self.config.MAX_NEW_TOKENS,
        #     temperature=self.config.TEMPERATURE,
        #     top_p=self.config.TOP_P,
        #     repetition_penalty=self.config.REPETITION_PENALTY,
        #     return_full_text=False,
        #     # Pass stop tokens here so pipeline handles them automatically
        #     eos_token_id=[self.tokenizer.eos_token_id] + getattr(self.config, 'STOP_TOKEN_IDS', []),
        #     do_sample=True
        # )

        # 4. Wrap in LangChain Classes
        # HuggingFacePipeline turns the HF pipeline into a standard LangChain LLM
        #hf_llm = HuggingFacePipeline(pipeline=text_generation_pipeline)
        
        # ChatHuggingFace applies the correct chat template automatically
        
        #self.llm = ChatHuggingFace(llm=hf_llm)
        
        self.llm = ChatGroq(
            model=self.config.LLM_MODEL,
            temperature=self.config.TEMPERATURE,
            max_tokens=self.config.MAX_NEW_TOKENS,
            # api_key=os.getenv("GROQ_API_KEY") # Optional if set in env
        )
        print(f"✅ Model loaded")
        #memory_footprint = self.model.get_memory_footprint() / 1e9
        #print(f"✅ Model loaded & wrapped! Memory footprint: {memory_footprint:.2f} GB")
    
    def generate(self, messages: List[Dict[str, str]], max_new_tokens: int = None,
                 temperature: float = None, do_sample: bool = True) -> str:
        """
        Generate text response.
        Adapts dictionary-based messages to LangChain BaseMessages and invokes the model.
        """
        if self.llm is None:
            self.load_model()
            
        # Convert Dicts to LangChain Message Objects
        # This bridges your legacy code with the modern LangChain object
        langchain_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            elif role == "system":
                langchain_messages.append(SystemMessage(content=content))

        # Runtime configuration overrides
        # We can pass these to the invoke method to override pipeline defaults
        invocation_params = {}
        if max_new_tokens:
            invocation_params["max_tokens"] = max_new_tokens
        if temperature:
            invocation_params["temperature"] = temperature
        # if not do_sample:
        #     invocation_params["do_sample"] = False

        # Invoke the modern Chat Model
        response = self.llm.invoke(langchain_messages, **invocation_params)
        
        return response.content.strip()

    def rewrite_question(self, question: str, chat_history: List) -> str:
        """
        Rewrite follow-up question to be standalone.
        Safely handles both LangChain Message objects and legacy dictionaries.
        """
        if self.llm is None:
            self.load_model()
            
        if not chat_history:
            return question
            
        # Format history string
        history_text = ""
        for msg in chat_history[-self.config.REWRITE_MAX_HISTORY:]:
            # 1. Handle LangChain Message Objects (Standard in LangGraph)
            if isinstance(msg, BaseMessage):
                content = msg.content
                role = "Q" if isinstance(msg, HumanMessage) else "A"
            
            # 2. Handle Legacy Dictionaries (Fallback)
            elif isinstance(msg, dict):
                content = msg.get('content', '')
                role_str = msg.get('role')
                role = "Q" if role_str == 'user' else "A"
            
            # 3. Skip unknown types
            else:
                continue

            history_text += f"{role}: {content[:100]}\n"

        # Create Prompt as Message Objects
        messages = [
            SystemMessage(content=self.config.REWRITE_SYSTEM_PROMPT),
            HumanMessage(content=f"Context:\n{history_text}\nCurrent question: {question}\n\nRewritten standalone question:")
        ]

        # Config for this specific strict task
        strict_params = {
            "max_tokens": self.config.REWRITE_MAX_TOKENS,
            "temperature": self.config.REWRITE_TEMPERATURE,
        }

        # Invoke
        rewritten = self.llm.invoke(messages, **strict_params).content.strip()
        
        # Cleanup
        rewritten = rewritten.split('\n')[0].strip()
        
        # Validation
        if (len(rewritten) > 250 or len(rewritten) < 5 or "assistant" in rewritten.lower()):
            print(f"⚠️ Rewrite validation failed, using original")
            return question
            
        print(f"🔄 Rewritten: {rewritten}")
        return rewritten

    def get_model_info(self) -> Dict:
        """Get information about loaded model"""
        if self.model is None and self.llm is None:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "model_name": self.config.LLM_MODEL,
            "device": str(self.model.device) if self.model else "cloud",
            "memory_footprint_gb": (self.model.get_memory_footprint() / 1e9) if self.model else 0,
            "quantization": "8-bit" if self.config.USE_8BIT_QUANTIZATION else "None",
            "backend": "LangChain ChatGroq"
        }