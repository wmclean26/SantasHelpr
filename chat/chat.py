from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch, re

# --- Config ---
MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# --- Load model ---
print("Loading model...")
try:
    bnb_config = BitsAndBytesConfig(load_in_4bit=True)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto"
    )
    print("4-bit model loaded successfully.\n")
except Exception as e:
    print("Falling back to float32 mode.")
    print(f"Reason: {e}\n")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,
        device_map=device
    )

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# --- Gift idea function ---
def get_similar_gift_ideas(gift_name: str, num_ideas: int = 5):
    """
    Returns short, thematically similar gift ideas.
    Example: 'Power Rangers' -> ['GI Joe', 'Transformers', 'He-Man', 'TMNT', 'Voltron']
    """
    prompt = f"List {num_ideas} toys or gifts similar to '{gift_name}', separated by commas. Only return names."

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=60,
        temperature=0.8,
        top_p=0.9,
        do_sample=True,
        pad_token_id=tokenizer.eos_token_id
    )

    # Skip the input tokens so the prompt itself isn't echoed
    generated = outputs[0][inputs["input_ids"].shape[-1]:]
    text = tokenizer.decode(generated, skip_special_tokens=True)

    # Remove unwanted labels or formatting artifacts
    text = re.sub(r"(?i)\b(solution|answer|response|output)\s*[:\-–]*", "", text)
    text = text.replace("**", "").strip()

    # Extract clean list
    ideas = re.split(r"[,;\n]+", text)
    ideas = [i.strip(" -*") for i in ideas if i.strip()]
    return ideas[:num_ideas] if ideas else ["(no ideas found)"]


# --- Chat loop ---
print("Gift matcher ready!")
print("Type a gift idea (e.g., 'Power Rangers') to see related gifts, or 'quit' to exit.\n")

while True:
    user_input = input("Gift idea: ").strip()
    if user_input.lower() in ["quit", "exit"]:
        print("Goodbye!")
        break

    ideas = get_similar_gift_ideas(user_input)
    print("\nHere are similar gift ideas:\n")
    for idea in ideas:
        print("-", idea)
    print("\n")
