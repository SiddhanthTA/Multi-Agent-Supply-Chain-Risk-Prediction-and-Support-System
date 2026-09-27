import json
import sys

from app.config.settings import settings


def _classify_choices(torch, model, tokenizer, prompt, choices, context_limit):
    if not choices:
        raise ValueError("classification_choices is required")
    prompt_ids = tokenizer(prompt, return_tensors="pt")["input_ids"][0]
    if prompt_ids.shape[0] >= context_limit:
        prompt_ids = prompt_ids[-(context_limit - 1):]
    scores = {}
    with torch.inference_mode():
        for choice in choices:
            choice_ids = tokenizer(choice, add_special_tokens=False)["input_ids"]
            input_ids = torch.cat([
                prompt_ids,
                torch.tensor(choice_ids, dtype=prompt_ids.dtype),
            ]).unsqueeze(0)
            logits = model(input_ids).logits[0]
            log_probs = torch.log_softmax(logits, dim=-1)
            token_scores = [
                log_probs[prompt_ids.shape[0] - 1 + index, token_id]
                for index, token_id in enumerate(choice_ids)
            ]
            scores[choice] = float(torch.stack(token_scores).mean())
    return max(scores, key=scores.get)


def main() -> None:
    try:
        request = json.load(sys.stdin)
        system_prompt = request["system_prompt"]
        user_prompt = request["user_prompt"]
        max_tokens = int(request["max_tokens"])
        assistant_prefix = str(request.get("assistant_prefix") or "")
        classification_choices = [
            str(choice) for choice in request.get("classification_choices") or []
        ]

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            settings.INVESTIGATION_MODEL_PATH,
            local_files_only=settings.INVESTIGATION_LOCAL_FILES_ONLY,
        )
        tokenizer.truncation_side = "left"
        load_kwargs = {
            "low_cpu_mem_usage": True,
            "local_files_only": settings.INVESTIGATION_LOCAL_FILES_ONLY,
        }
        load_kwargs["torch_dtype"] = (
            torch.float16 if torch.cuda.is_available() else torch.float32
        )
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
        ) + assistant_prefix
        raw_input_tokens = tokenizer(prompt, return_tensors="pt")["input_ids"].shape[1]
        diagnostics = {
            "prompt_chars": len(prompt),
            "raw_input_tokens": raw_input_tokens,
            "context_limit": settings.INVESTIGATION_CONTEXT_TOKENS,
        }

        if classification_choices:
            text = _classify_choices(
                torch,
                model,
                tokenizer,
                prompt,
                classification_choices,
                settings.INVESTIGATION_CONTEXT_TOKENS,
            )
            diagnostics.update({
                "mode": "constrained_classification",
                "choices": classification_choices,
            })
        else:
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
            diagnostics.update({
                "mode": "generation",
                "input_tokens": inputs["input_ids"].shape[1],
                "context_truncated": raw_input_tokens > inputs["input_ids"].shape[1],
                "output_tokens": generated.shape[0],
                "max_new_tokens": max_tokens,
                "ended_with_eos": bool(
                    generated.shape[0]
                    and tokenizer.eos_token_id is not None
                    and generated[-1].item() == tokenizer.eos_token_id
                ),
            })

        json.dump({"ok": True, "text": text, "diagnostics": diagnostics}, sys.stdout)
    except Exception:
        json.dump({"ok": False}, sys.stdout)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
