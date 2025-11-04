# Self-Evolving Agent

Built a Self-Improving Agent (SEA) framework during Weights & Biases' WeaveHacks 2 (24-hour hackathon).  

SEA enhances itself through:  
1. Automatic prompt optimization  
2. Automatic tool creation  

Architecture:  
- **Evolve phase:** While solving tasks, auxiliary agents monitor traces and update system prompts and tools (passive learning; model parameters remain unchanged).  
- **Inference phase:** The evolved prompt and toolset are applied to new, unseen data.  

Tested SEA on the MATH 500 dataset using the Phi-4-3.8B model across four settings:  
1. Phi-4 baseline  
2. Phi-4 + basic tools  
3. SEA (evolve phase)  
4. SEA (inference phase)  

Results: SEA outperformed the first two baselines by over 13% in both evolve and inference phases.

