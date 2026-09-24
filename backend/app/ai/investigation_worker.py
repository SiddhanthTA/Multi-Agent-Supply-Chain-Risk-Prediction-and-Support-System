import json
import sys

from app.config.settings import settings


def main() -> None:
    try:
        request = json.load(sys.stdin)
        system_prompt = request["system_prompt"]
        user_prompt = request["user_prompt"]
        max_tokens = int(request["max_tokens"])

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            settings.INVESTIGATION_MODEL_PATH,
            local_files_only=settings.INVESTIGATION_LOCAL_FILES_ONLY,
        )

        load_kwargs = {
            "low_cpu_mem_usage": True,
            "local_files_only": settings.INVESTIGATION_LOCAL_FILES_ONLY,
        }
        if torch.cuda.is_available():
            load_kwargs["torch_dtype"] = torch.float16
        else:
            load_kwargs["torch_dtype"] = torch.float32

        model = AutoModelForCausalLM.from_pretrained(
            settings.INVESTIGATION_MODEL_PATH,
            **load_kwargs,
        )
        model.eval()

        prompt = tokenizer.apply_chat_template(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=settings.INVESTIGATION_CONTEXT_TOKENS,
        )
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated = output_ids[0][inputs["input_ids"].shape[1]:]
        text = tokenizer.decode(generated, skip_special_tokens=True).strip()
        json.dump({"ok": True, "text": text}, sys.stdout)
    except Exception:
        json.dump({"ok": False}, sys.stdout)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
