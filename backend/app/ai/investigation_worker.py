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
        raw_inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=False,
        )
        raw_input_tokens = raw_inputs["input_ids"].shape[1]
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=settings.INVESTIGATION_CONTEXT_TOKENS,
        )
        input_tokens = inputs["input_ids"].shape[1]
        context_truncated = raw_input_tokens > input_tokens
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        generated = output_ids[0][inputs["input_ids"].shape[1]:]
        text = tokenizer.decode(generated, skip_special_tokens=True).strip()
        output_tokens = generated.shape[0]
        ended_with_eos = bool(
            output_tokens
            and tokenizer.eos_token_id is not None
            and generated[-1].item() == tokenizer.eos_token_id
        )
        json.dump(
            {
                "ok": True,
                "text": text,
                "diagnostics": {
                    "prompt_chars": len(prompt),
                    "raw_input_tokens": raw_input_tokens,
                    "input_tokens": input_tokens,
                    "context_truncated": context_truncated,
                    "output_tokens": output_tokens,
                    "max_new_tokens": max_tokens,
                    "ended_with_eos": ended_with_eos,
                },
            },
            sys.stdout,
        )
    except Exception:
        json.dump({"ok": False}, sys.stdout)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
