# Memory

OmAgent implements two types of memory systems:

1. **Short-Term Memory (STM)**
   - Temporary storage for workflow-specific data
   - Implemented using Redis by default
   - Useful for storing session/workflow state
   - Data is volatile and workflow-instance specific

2. **Long-Term Memory (LTM)**
   - Persistent storage for long-term data
   - Implemented using vector database
   - Supports vector storage and similarity search
   - Data persists across different workflow instances

