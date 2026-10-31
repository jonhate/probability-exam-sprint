from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class LLMError(RuntimeError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


@dataclass
class LLMResult:
    content: str
    usage: dict[str, Any]
    model: str


class LLMClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        timeout: int = 180,
    ):
        if not api_key:
            raise LLMError("尚未配置 API Key")
        self.api_key = api_key.strip()
        self.base_url = base_url.strip().rstrip("/") or "https://api.deepseek.com/v1"
        self.model = model.strip() or "deepseek-chat"
        self.timeout = timeout
        self.last_usage: dict[str, Any] = {}

    @property
    def endpoint(self) -> str:
        base = self.base_url
        if base.endswith("/chat/completions"):
            return base
        if base.endswith("/v1"):
            return base + "/chat/completions"
        return base + "/v1/chat/completions"

    def chat(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 8192,
        temperature: float = 0.2,
        json_mode: bool = True,
    ) -> LLMResult:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        last_err: Exception | None = None
        for attempt in range(3):
            try:
                return self._request(payload)
            except LLMError as exc:
                last_err = exc
                if exc.status == 400 and json_mode:
                    # Some OpenAI-compatible servers do not support response_format.
                    payload.pop("response_format", None)
                    json_mode = False
                    continue
                if exc.status in (401, 403, 404):
                    raise
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise
            except Exception as exc:
                last_err = exc
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue
        raise LLMError(str(last_err or "模型调用失败"))

    def _request(self, payload: dict[str, Any]) -> LLMResult:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "ExamSprint/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", "replace")[:800]
            except Exception:
                pass
            raise LLMError(f"API HTTP {exc.code}：模型服务请求失败，请检查连接、密钥和配额", status=exc.code) from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"无法连接模型服务：{exc.reason}") from exc
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMError("模型服务返回了非 JSON 响应") from exc
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("模型响应结构异常") from exc
        if isinstance(content, list):
            content = "".join(str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in content)
        usage = data.get("usage") or {}
        self.last_usage = usage if isinstance(usage, dict) else {}
        return LLMResult(str(content or ""), usage, str(data.get("model") or self.model))

    def complete_json(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 8192,
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        result = self.chat(system, user, max_tokens=max_tokens, temperature=temperature, json_mode=True)
        try:
            return parse_json_loose(result.content)
        except ValueError:
            repair = self.chat(
                "你是 JSON 修复器。只输出合法 JSON，不添加解释，不改变原有事实。",
                "把下面的内容修复为一个合法 JSON 对象，保持原有字段和内容：\n\n" + result.content[:40000],
                max_tokens=min(max_tokens, 8192),
                temperature=0,
                json_mode=True,
            )
            return parse_json_loose(repair.content)

    def test(self) -> dict[str, Any]:
        result = self.chat(
            "你是连通性测试助手。",
            '只输出 JSON：{"ok": true, "message": "pong"}',
            max_tokens=40,
            temperature=0,
            json_mode=True,
        )
        return {"ok": True, "model": result.model, "usage": result.usage, "reply": result.content[:200]}


def parse_json_loose(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    # Remove markdown fences.
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    candidates = [text]
    first, last = text.find("{"), text.rfind("}")
    if first >= 0 and last > first:
        candidates.append(text[first : last + 1])
    # Sometimes an array is returned; wrap it under items.
    first_a, last_a = text.find("["), text.rfind("]")
    if first_a >= 0 and last_a > first_a:
        candidates.append('{"items":' + text[first_a : last_a + 1] + "}")
    for c in candidates:
        try:
            data = json.loads(c)
            if isinstance(data, dict):
                return data
            if isinstance(data, list):
                return {"items": data}
        except json.JSONDecodeError:
            continue
    raise ValueError("模型没有返回可解析的 JSON")


def safe_int(value: Any, default: int, low: int | None = None, high: int | None = None) -> int:
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        n = default
    if low is not None:
        n = max(low, n)
    if high is not None:
        n = min(high, n)
    return n
