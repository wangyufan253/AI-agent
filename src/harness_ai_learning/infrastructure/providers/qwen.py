import json
import time
from pathlib import Path

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from harness_ai_learning.domain import StudyOutput


class QwenStudyProvider:
    name = "qwen-doc"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: int = 90,
        parse_retries: int = 8,
        parse_retry_delay_seconds: int = 2,
        file_status_retries: int = 20,
        file_status_retry_delay_seconds: int = 2,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._parse_retries = parse_retries
        self._parse_retry_delay_seconds = parse_retry_delay_seconds
        self._file_status_retries = file_status_retries
        self._file_status_retry_delay_seconds = file_status_retry_delay_seconds
        self._client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout_seconds,
        )

    def generate(self, *, source_path: Path, source_type: str) -> StudyOutput:
        file_id = self._upload_file(source_path)
        self._wait_for_file_processed(file_id)
        payload = self._ask_model(file_id)
        return StudyOutput(
            source_path=source_path,
            source_type=source_type,
            extracted_text=f"模型直接读取文件: {source_path.name}",
            summary=payload["summary"],
            key_concepts=payload["key_concepts"],
            follow_up_questions=payload["follow_up_questions"],
            extension_ideas=payload["extension_ideas"],
        )

    def _upload_file(self, source_path: Path) -> str:
        try:
            with source_path.open("rb") as file_handle:
                response = self._client.files.create(file=file_handle, purpose="file-extract")
        except APIConnectionError as exc:
            raise RuntimeError(f"连接模型服务失败: {exc}") from exc
        except APITimeoutError as exc:
            raise RuntimeError("上传文件超时，请稍后重试。") from exc
        except APIStatusError as exc:
            raise RuntimeError(self._format_status_error(exc, prefix="上传文件失败")) from exc

        file_id = getattr(response, "id", None)
        if not file_id:
            raise RuntimeError("文件上传成功，但响应里缺少 file-id。")
        return file_id

    def _wait_for_file_processed(self, file_id: str) -> None:
        last_status = "unknown"
        status_details = None
        for _ in range(self._file_status_retries):
            try:
                file_info = self._client.files.retrieve(file_id=file_id)
            except APIConnectionError as exc:
                raise RuntimeError(f"查询文件解析状态失败: {exc}") from exc
            except APITimeoutError as exc:
                raise RuntimeError("查询文件解析状态超时，请稍后重试。") from exc
            except APIStatusError as exc:
                raise RuntimeError(self._format_status_error(exc, prefix="查询文件解析状态失败")) from exc

            last_status = getattr(file_info, "status", None) or "unknown"
            status_details = getattr(file_info, "status_details", None)
            if last_status == "processed":
                return
            if last_status in {"error", "failed"}:
                raise RuntimeError(f"文件解析失败，状态: {last_status}，详情: {status_details}")
            time.sleep(self._file_status_retry_delay_seconds)

        raise RuntimeError(f"文件长时间未完成解析，当前状态: {last_status}，详情: {status_details}")

    def _ask_model(self, file_id: str) -> dict:
        last_error: Exception | None = None
        for _ in range(self._parse_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个面向中文用户的学习助手。你必须严格基于提供的文件内容回答，禁止脱离文件内容泛化发挥。请严格返回 JSON，不要输出 JSON 之外的任何文本。",
                        },
                        {"role": "system", "content": f"fileid://{file_id}"},
                        {
                            "role": "user",
                            "content": (
                                "请阅读这份文件，并输出一个 JSON 对象。字段必须严格为："
                                "summary, key_concepts, follow_up_questions, extension_ideas。"
                                "其中 summary 是中文字符串；其余字段是中文字符串数组。"
                                "要求：1. 结论必须来自文件内容；2. 不要编造文件中没有的信息；"
                                "3. key_concepts 至少 5 个；4. 不要输出 markdown，不要输出代码块，不要额外解释。"
                            ),
                        },
                    ],
                    temperature=0.1,
                )
                content = response.choices[0].message.content or ""
                return self._parse_json(content)
            except APIStatusError as exc:
                message = self._extract_error_message(exc)
                if "File parsing in progress" in message:
                    last_error = exc
                    time.sleep(self._parse_retry_delay_seconds)
                    continue
                raise RuntimeError(self._format_status_error(exc, prefix="模型调用失败")) from exc
            except APIConnectionError as exc:
                raise RuntimeError(f"连接模型服务失败: {exc}") from exc
            except APITimeoutError as exc:
                raise RuntimeError("模型响应超时，请稍后重试。") from exc

        if last_error is not None:
            raise RuntimeError(self._format_status_error(last_error, prefix="模型调用失败")) from last_error
        raise RuntimeError("模型调用失败，未获取到有效响应。")

    def _parse_json(self, content: str) -> dict:
        content = content.strip()
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"模型没有返回合法 JSON。原始输出: {content[:200]}")
        payload = json.loads(content[start : end + 1])
        for field in ["summary", "key_concepts", "follow_up_questions", "extension_ideas"]:
            if field not in payload:
                raise ValueError(f"模型返回缺少字段: {field}")
        return payload

    def _extract_error_message(self, exc: APIStatusError) -> str:
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            if isinstance(body.get("message"), str):
                return body["message"]
            if isinstance(body.get("error"), dict) and isinstance(body["error"].get("message"), str):
                return body["error"]["message"]
        return str(exc)

    def _format_status_error(self, exc: APIStatusError, *, prefix: str) -> str:
        message = self._extract_error_message(exc)
        status_code = getattr(exc, "status_code", "unknown")
        return f"{prefix}，HTTP {status_code}: {message}"
