"""
Conversation management with LangGraph for RAG chatbot
"""

import uuid
from typing import List, Dict, Tuple, Annotated, Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict # Use typing_extensions for TypedDict compatibility

# Assumed custom imports (kept as is)
from .config import RAGConfig
from .embeddings import EmbeddingManager
from .vector_store import VectorStore
from .llm_manager import LLMManager
from .retriever import Retriever
from .document_processor import DocumentProcessor

# --- 1. Define Graph State (The new "Memory" container) ---
class GraphState(TypedDict):
    """
    Represents the state of our graph.
    
    Attributes:
        messages: The chat history. 'add_messages' ensures updates are appended, not overwritten.
        context: The formatted context string retrieved from documents.
        retrieved_docs: List of documents retrieved (for source citation).
        question: The original user question.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    context: str
    retrieved_docs: List[Dict]
    question: str


class RAGChatbot:
    """Main RAG chatbot using LangGraph for conversation state and workflow."""
    
    def __init__(self, config: RAGConfig = None):
        self.config = config or RAGConfig()
        
        # Initialize components
        self.embedding_manager = EmbeddingManager(config=self.config)
        self.vector_store = VectorStore(config=self.config)
        self.llm_manager = LLMManager(config=self.config)
        self.retriever = Retriever(
            embedding_manager=self.embedding_manager,
            vector_store=self.vector_store,
            llm_manager=self.llm_manager,
            config=self.config
        )
        
        # Build the graph internally
        self._build_graph()
        self._initialized = False

    def _build_graph(self):
        """Builds the StateGraph defining the RAG workflow."""
        workflow = StateGraph(GraphState)

        # Add Nodes
        workflow.add_node("rewrite", self._rewrite_node)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("generate", self._generate_node)

        # Define Edges
        workflow.add_edge(START, "rewrite")
        workflow.add_edge("rewrite", "retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        # Initialize Memory (Persistence)
        self.checkpointer = MemorySaver()
        
        # Compile the graph
        self.app = workflow.compile(checkpointer=self.checkpointer)

    # --- 2. Node Definitions for the Graph ---

    def _rewrite_node(self, state: GraphState) -> Dict:
        """Node for query rewriting logic."""
        messages = state["messages"]
        question = messages[-1].content
        
        # Check if history exists (excluding the current HumanMessage)
        chat_history = messages[:-1]
        
        # We assume the Retriever has access to the LLMManager's rewrite method
        retrieval_question = question
        
        # Logic to rewrite: Check history length
        if len(chat_history) > 0:
            # Note: We assume self.retriever.rewrite_query calls the LLMManager internally.
            # We must pass BaseMessage objects as history now, as LLMManager's generate
            # method in the previous step handles the conversion from BaseMessage -> Dict.
            retrieval_question = self.retriever.rewrite_query(question, chat_history)

        return {
            "question": question, # Original question
            "retrieval_question": retrieval_question # Updated for retrieval
        }

    def _retrieve_node(self, state: GraphState) -> Dict:
        """Node to retrieve documents."""
        # Retrieve the question potentially modified by the rewrite node
        retrieval_question = state.get("retrieval_question", state["question"])
        
        # Retrieve relevant documents
        retrieved_docs, retrieved_metadata, similarities = self.retriever.retrieve(
            query=retrieval_question,
            n_results=getattr(self.config, 'RETRIEVAL_K', 4) 
        )

        # Check for empty results (Handling the original "if not retrieved_docs" logic)
        if not retrieved_docs:
            # If no docs found, pass a special message to the generate node
            return {
                "context": "",
                "retrieved_docs": [],
            }

        formatted_context = self.retriever.format_context(retrieved_docs, retrieved_metadata)
        
        # Prepare source data for final output
        docs_with_meta = self.retriever.prepare_sources(
            retrieved_docs,
            retrieved_metadata,
            similarities
        )
"""
Conversation management with LangGraph for RAG chatbot
"""

import uuid
from typing import List, Dict, Tuple, Annotated, Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict # Use typing_extensions for TypedDict compatibility

# Assumed custom imports (kept as is)
from .config import RAGConfig
from .embeddings import EmbeddingManager
from .vector_store import VectorStore
from .llm_manager import LLMManager
from .retriever import Retriever
from .document_processor import DocumentProcessor

# --- 1. Define Graph State (The new "Memory" container) ---
class GraphState(TypedDict):
    """
    Represents the state of our graph.
    
    Attributes:
        messages: The chat history. 'add_messages' ensures updates are appended, not overwritten.
        context: The formatted context string retrieved from documents.
        retrieved_docs: List of documents retrieved (for source citation).
        question: The original user question.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    context: str
    retrieved_docs: List[Dict]
    question: str


class RAGChatbot:
    """Main RAG chatbot using LangGraph for conversation state and workflow."""
    
    def __init__(self, config: RAGConfig = None):
        self.config = config or RAGConfig()
        
        # Initialize components
        self.embedding_manager = EmbeddingManager(config=self.config)
        self.vector_store = VectorStore(config=self.config)
        self.llm_manager = LLMManager(config=self.config)
        self.retriever = Retriever(
            embedding_manager=self.embedding_manager,
            vector_store=self.vector_store,
            llm_manager=self.llm_manager,
            config=self.config
        )
        
        # Build the graph internally
        self._build_graph()
        self._initialized = False

    def _build_graph(self):
        """Builds the StateGraph defining the RAG workflow."""
        workflow = StateGraph(GraphState)

        # Add Nodes
        workflow.add_node("rewrite", self._rewrite_node)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("generate", self._generate_node)

        # Define Edges
        workflow.add_edge(START, "rewrite")
        workflow.add_edge("rewrite", "retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        # Initialize Memory (Persistence)
        self.checkpointer = MemorySaver()
        
        # Compile the graph
        self.app = workflow.compile(checkpointer=self.checkpointer)

    # --- 2. Node Definitions for the Graph ---

    def _rewrite_node(self, state: GraphState) -> Dict:
        """Node for query rewriting logic."""
        messages = state["messages"]
        question = messages[-1].content
        
        # Check if history exists (excluding the current HumanMessage)
        chat_history = messages[:-1]
        
        # We assume the Retriever has access to the LLMManager's rewrite method
        retrieval_question = question
        
        # Logic to rewrite: Check history length
        if len(chat_history) > 0:
            # Note: We assume self.retriever.rewrite_query calls the LLMManager internally.
            # We must pass BaseMessage objects as history now, as LLMManager's generate
            # method in the previous step handles the conversion from BaseMessage -> Dict.
            retrieval_question = self.retriever.rewrite_query(question, chat_history)

        return {
            "question": question, # Original question
            "retrieval_question": retrieval_question # Updated for retrieval
        }

    def _retrieve_node(self, state: GraphState) -> Dict:
        """Node to retrieve documents."""
        # Retrieve the question potentially modified by the rewrite node
        retrieval_question = state.get("retrieval_question", state["question"])
        
        # Retrieve relevant documents
        retrieved_docs, retrieved_metadata, similarities = self.retriever.retrieve(
            query=retrieval_question,
            n_results=getattr(self.config, 'RETRIEVAL_K', 4) 
        )

        # Check for empty results (Handling the original "if not retrieved_docs" logic)
        if not retrieved_docs:
            # If no docs found, pass a special message to the generate node
            return {
                "context": "",
                "retrieved_docs": [],
            }

        formatted_context = self.retriever.format_context(retrieved_docs, retrieved_metadata)
        
        # Prepare source data for final output
        docs_with_meta = self.retriever.prepare_sources(
            retrieved_docs,
            retrieved_metadata,
            similarities
        )

        return {
            "context": formatted_context,
            "retrieved_docs": docs_with_meta,
        }

    def _generate_node(self, state: GraphState) -> Dict:
        """Node to generate the final answer."""
        context = state["context"]
        question = state["question"]
        
        if not context:
            no_context_answer = "I cannot find relevant information in the provided documents to answer this question. Please ask something related to the document content."
            # Return the no-context message as the final AI message
            return {"messages": [AIMessage(content=no_context_answer)]}

        # 1. System Prompt
        llm_messages: List[Dict] = [{"role": "system", "content": self.config.SYSTEM_PROMPT}]
        
        # 2. History (State already holds BaseMessage objects)
        history_messages = state["messages"][:-1]
        for msg in history_messages:
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            llm_messages.append({"role": role, "content": msg.content})
            
        # 3. Current input with Context
        llm_messages.append({
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}"
        })

        # Generate answer using the modernized LLMManager
        print("⏳ Generating answer...")
        answer = self.llm_manager.generate(llm_messages)
        
        # Return the final AI message, which is appended to the state history automatically
        return {"messages": [AIMessage(content=answer)]}

    # --- 3. Public Methods (Interface Remains Similar) ---

    def initialize(self, db_path: str = None, reset: bool = False):
        """Initializes components."""
        print("Initializing RAG Chatbot...")
        self.vector_store.initialize(db_path=db_path, reset=reset)
        self.embedding_manager.load_model()
        # The LLM is now lazily loaded by the LLMManager when called in the graph
        print("✅ RAG Chatbot initialized (Graph built, LLM will load on first query)")
        self._initialized = True

    def index_documents(self, documents: List, chunk_size: int = None,
                         chunk_overlap: int = None):
        """Indexes documents."""
        if not self._initialized:
            raise RuntimeError("Chatbot not initialized. Call initialize() first.")
        
        print(f"Indexing {len(documents)} documents...")
        
        # Initialize processor
        processor = DocumentProcessor(config=self.config)
        
        # Split documents
        chunks = processor.split_documents(documents)
        
        if not chunks:
            print("⚠️ No chunks created from documents.")
            return

        # Prepare for embedding
        texts, metadatas = processor.prepare_chunks_for_embedding(chunks)
        
        # Generate embeddings
        embeddings = self.embedding_manager.generate_embeddings(texts)
        
        # Add to vector store
        self.vector_store.add_documents(
            embeddings=embeddings.tolist(), # Convert to list for ChromaDB
            texts=texts,
            metadatas=metadatas
        )
        
        print(f"✅ Successfully indexed {len(chunks)} chunks.")

    def query(self, question: str, thread_id: str = "default_session") -> Tuple[str, List[Dict]]:
        """
        Query the RAG system by invoking the LangGraph.
        
        Args:
            question: User question
            thread_id: Unique ID for the conversation session (Crucial for memory)
            
        Returns:
            Tuple of (answer, sources)
        """
        if not self._initialized:
            raise RuntimeError("Chatbot not initialized. Call initialize() first.")

        # Configuration ties the execution to a specific conversation thread
        config = {"configurable": {"thread_id": thread_id}}
        
        # Input state: We only pass the new user message as a BaseMessage
        input_state = {"messages": [HumanMessage(content=question)]}
        
        # Run the graph and get the final state
        final_state = self.app.invoke(input_state, config=config)
        
        # Extract the final answer and sources
        final_response = final_state["messages"][-1].content
        sources = final_state.get("retrieved_docs", [])
        
        return final_response, sources

    def clear_memory(self, thread_id: str = "default_session"):
        """Clear conversation history for a specific thread."""
        config = {"configurable": {"thread_id": thread_id}}
        # LangGraph allows deletion of the checkpoint for a thread
        self.checkpointer.purge(config)
        print(f"🗑️ Conversation history cleared for thread: {thread_id}")
    
    def get_conversation_history(self, thread_id: str = "default_session") -> List[BaseMessage]:
        """Get current conversation history from the graph state."""
        config = {"configurable": {"thread_id": thread_id}}
        state_snapshot = self.app.get_state(config)
        return state_snapshot.values.get("messages", [])
    
    def get_system_info(self) -> Dict:
        """Get system information (Updated to reflect LangGraph turns)."""
        # The logic here remains mostly the same, fetching info from components
        return {
            "initialized": self._initialized,
            "llm_info": self.llm_manager.get_model_info(),
            "vector_store_count": self.vector_store.get_document_count(),
            # Note: conversation_turns calculation may need adjustment based on graph usage.
            "conversation_turns": len(self.get_conversation_history()) // 2
        }