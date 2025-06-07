from src.local_model import LocalModel

# Initialize the model
model_path = "C:/Users/home/.lmstudio/models/lmstudio-community/Qwen2.5-7B-Instruct-1M-GGUF/Qwen2.5-7B-Instruct-1M-Q4_K_M.gguf"
model = LocalModel(model_path)

# Example conversation
messages = [
    {"role": "user", "content": "Hello, how are you?"}
]

# Generate response
response = model.generate_response(messages, temperature=0.7)
print("Model response:", response["choices"][0]["message"]["content"])

