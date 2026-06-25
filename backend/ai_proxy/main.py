import json
import os
import re
from pathlib import Path
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api import ai_prompts


BASE_DIR = Path(__file__).resolve().parents[1]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip().lstrip('\ufeff'), value.strip().strip('"').strip("'"))


load_env_file(BASE_DIR / '.env')


GMS_BASE_URL = os.environ.get(
    'GMS_BASE_URL',
    'https://gms.ssafy.io/gmsapi/api.openai.com/v1',
).rstrip('/')
GMS_API_KEY = os.environ.get('GMS_API_KEY') or os.environ.get('OPENAI_API_KEY') or ''
GMS_MODEL = os.environ.get('GMS_MODEL') or os.environ.get('OPENAI_MODEL') or 'gpt-5-mini'
GMS_FALLBACK_MODEL = os.environ.get('GMS_FALLBACK_MODEL', 'gpt-5.4-mini')
GMS_TIMEOUT_SECONDS = int(os.environ.get('GMS_TIMEOUT_SECONDS', '45'))
GMS_MAX_OUTPUT_TOKENS = int(os.environ.get('GMS_MAX_OUTPUT_TOKENS', '3000'))


class GuardrailRequest(BaseModel):
    message: str = ''
    context: dict[str, Any] = Field(default_factory=dict)


class ChatProxyRequest(BaseModel):
    message: str = ''
    history: list[dict[str, Any]] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class JsonProxyRequest(BaseModel):
    task: str = 'generic'
    prompt: str = ''
    developerPrompt: str = ''


class ScoreRequest(BaseModel):
    question: str = ''
    answer: str = ''
    context: dict[str, Any] = Field(default_factory=dict)


app = FastAPI(
    title='CARCH AI Proxy',
    version='1.0.0',
    description='FastAPI model-serving proxy for Guardrail, LLM chat, and response scoring.',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://127.0.0.1:5173',
        'http://localhost:5173',
        'http://127.0.0.1:8000',
        'http://localhost:8000',
    ],
    allow_methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['Content-Type', 'Authorization'],
)


def configured() -> bool:
    return bool(GMS_API_KEY)


def extract_output_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get('output_text'), str):
        return payload['output_text']

    chunks: list[str] = []
    for item in payload.get('output', []):
        for content in item.get('content', []):
            if isinstance(content.get('text'), str):
                chunks.append(content['text'])
    if chunks:
        return ''.join(chunks)

    choices = payload.get('choices') or []
    if choices:
        message = choices[0].get('message') or {}
        content = message.get('content')
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and isinstance(item.get('text'), str):
                    chunks.append(item['text'])
            if chunks:
                return ''.join(chunks)

    return ''


def extract_json_object(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = re.sub(r'^```(?:json)?|```$', '', text.strip(), flags=re.IGNORECASE | re.MULTILINE).strip()
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start == -1 or end == -1 or end <= start:
            return None
        parsed = json.loads(cleaned[start : end + 1])
        return parsed if isinstance(parsed, dict) else None


def request_gms_json(prompt: str, developer_prompt: str) -> dict[str, Any]:
    if not configured():
        raise ValueError('GMS_API_KEY is not configured')

    url = f'{GMS_BASE_URL}/chat/completions'
    models = [GMS_MODEL]
    if GMS_FALLBACK_MODEL and GMS_FALLBACK_MODEL not in models:
        models.append(GMS_FALLBACK_MODEL)

    last_error: Exception | None = None
    for model in models:
        body: dict[str, Any] = {
            'model': model,
            'messages': [
                {'role': 'developer', 'content': developer_prompt},
                {'role': 'user', 'content': prompt},
            ],
            'response_format': {'type': 'json_object'},
        }
        if model.startswith('gpt-5') or model.startswith('o'):
            body['reasoning_effort'] = 'low'
            body['max_completion_tokens'] = GMS_MAX_OUTPUT_TOKENS
        else:
            body['max_tokens'] = GMS_MAX_OUTPUT_TOKENS

        try:
            response = requests.post(
                url,
                json=body,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {GMS_API_KEY}',
                },
                timeout=GMS_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
            if extract_output_text(payload).strip():
                return payload
            last_error = ValueError('Empty GMS output')
        except (requests.RequestException, ValueError) as error:
            last_error = error

    if last_error:
        raise last_error
    raise ValueError('No GMS model configured')


def guardrail_check(message: str) -> dict[str, Any]:
    text = str(message or '').strip()
    if not text:
        return {
            'allowed': False,
            'reason': '질문을 입력해야 합니다.',
            'categories': ['empty'],
        }

    blocked_terms = [
        '불법',
        '도박',
        '마약',
        '해킹',
        '폭력',
        '자해',
        '개인정보 유출',
        '카드번호 전체',
        '비밀번호',
    ]
    matched = [term for term in blocked_terms if term in text]
    if matched:
        return {
            'allowed': False,
            'reason': '금융 앱에서 처리하기 부적절한 요청입니다.',
            'categories': matched,
        }

    return {
        'allowed': True,
        'reason': 'CARCH 서비스 범위에서 처리 가능한 요청입니다.',
        'categories': ['card-spending'],
    }


def score_answer(question: str, answer: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    question_tokens = set(re.findall(r'[가-힣A-Za-z0-9]+', str(question).lower()))
    answer_tokens = set(re.findall(r'[가-힣A-Za-z0-9]+', str(answer).lower()))

    context_text = json.dumps(context or {}, ensure_ascii=False)
    route_bonus = 0.12 if any(route in str(answer) for route in ['/analytics', '/recommendations', '/plans']) else 0
    data_bonus = 0.12 if context else 0
    context_bonus = 0.0
    if answer and context_text:
        known_terms = set(re.findall(r'[가-힣A-Za-z0-9]+', context_text.lower()))
        context_overlap = len(answer_tokens & known_terms)
        context_bonus = min(0.18, context_overlap * 0.03)

    if not question_tokens or not answer_tokens:
        score = 0.52 + data_bonus + context_bonus
    else:
        overlap = len(question_tokens & answer_tokens) / max(len(question_tokens), 1)
        intent_terms = {'카드', '추천', '결제', '소비', '분석', '계획', '실적', '혜택'}
        intent_bonus = 0.08 if (question_tokens & intent_terms and answer_tokens & intent_terms) else 0
        score = 0.48 + overlap * 0.25 + route_bonus + data_bonus + context_bonus + intent_bonus
    score = min(1.0, round(score, 2))
    return {
        'score': score,
        'passed': score >= 0.6,
        'reason': '질문 키워드, 앱 데이터 사용 여부, 후속 화면 연결성을 기준으로 계산했습니다.',
    }


def infer_related_route(message: str) -> str | None:
    text = str(message or '')
    new_card_terms = ['새 카드', '신규 카드', '발급', '신청', '안 가진', '없는 카드', '비교 카드']
    usage_terms = ['보유', '가지고', '결제', '사용', '분배', '실적', '몰아', '채워', '어떤 카드', '어디에 쓸']
    analysis_terms = ['분석', '패턴', '소비 내역', '지출 내역', '얼마 썼']
    plan_terms = ['소비계획', '지출계획', '예정', '다음 달 계획', '계획 추가']

    if any(term in text for term in new_card_terms):
        return '/recommendations/new'
    if any(term in text for term in usage_terms):
        return '/recommendations/usage'
    if any(term in text for term in analysis_terms):
        return '/analytics'
    if any(term in text for term in plan_terms):
        return '/plans'
    return None


def normalize_proxy_chat_result(result: dict[str, Any], message: str) -> dict[str, Any]:
    if not isinstance(result, dict):
        return result

    inferred_route = infer_related_route(message)
    if inferred_route:
        result['relatedRoute'] = inferred_route
        if inferred_route in {'/recommendations/usage', '/recommendations/new'}:
            result['messageType'] = 'card-recommendation'
        elif inferred_route == '/analytics':
            result['messageType'] = 'spending-analysis'
        elif inferred_route in {'/plans', '/plans/new'}:
            result['messageType'] = 'purchase-plan'

    actions = result.get('actionButtons')
    if inferred_route and isinstance(actions, list):
        has_route = any(isinstance(action, dict) and action.get('route') == inferred_route for action in actions)
        if not has_route:
            label_by_route = {
                '/recommendations/usage': '보유 카드 사용 추천',
                '/recommendations/new': '새 카드 추천 보기',
                '/analytics': '소비 분석 보기',
                '/plans': '소비계획 보기',
                '/plans/new': '소비계획 추가',
            }
            actions.insert(0, {
                'label': label_by_route.get(inferred_route, '관련 화면 보기'),
                'route': inferred_route,
                'intent': 'open-related',
            })
            result['actionButtons'] = actions[:3]
    return result


@app.get('/health')
def health() -> dict[str, Any]:
    return {
        'ok': True,
        'service': 'carch-ai-proxy',
        'gmsConfigured': configured(),
        'model': GMS_MODEL,
        'fallbackModel': GMS_FALLBACK_MODEL,
    }


@app.get('/api/ai/status')
def ai_status() -> dict[str, Any]:
    return {
        'configured': configured(),
        'provider': 'gms-openai-compatible',
        'mode': 'fastapi-proxy',
        'model': GMS_MODEL,
        'fallbackModel': GMS_FALLBACK_MODEL,
        'baseUrl': GMS_BASE_URL,
    }


@app.post('/api/ai/guardrail')
def guardrail(payload: GuardrailRequest) -> dict[str, Any]:
    return guardrail_check(payload.message)


@app.post('/api/ai/score')
def score(payload: ScoreRequest) -> dict[str, Any]:
    return score_answer(payload.question, payload.answer, payload.context)


@app.post('/api/ai/proxy/chat')
def proxy_chat(payload: ChatProxyRequest) -> dict[str, Any]:
    guardrail_result = guardrail_check(payload.message)
    if not guardrail_result['allowed']:
        result = {
            'schemaVersion': 'chat-response-v2',
            'messageType': 'general',
            'reply': guardrail_result['reason'],
            'summaryChips': [{'label': 'Guardrail', 'value': '차단', 'tone': 'danger'}],
            'quickReplies': ['소비 분석 보기', '카드 추천 보기'],
            'actionButtons': [],
            'relatedRoute': '',
            'confidence': 0.9,
        }
        return {
            'schemaVersion': 'ai-proxy-chat-v1',
            'allowed': False,
            'guardrail': guardrail_result,
            'result': result,
            'score': score_answer(payload.message, result['reply'], payload.context),
            'aiMode': 'guardrail_blocked',
        }

    prompt = ai_prompts.build_chat_prompt(payload.message, payload.history, payload.context)
    response_payload = request_gms_json(prompt, ai_prompts.CHAT_DEVELOPER_PROMPT)
    parsed = extract_json_object(extract_output_text(response_payload))
    if not parsed:
        raise ValueError('GMS response did not contain valid JSON')

    parsed = normalize_proxy_chat_result(parsed, payload.message)
    score_result = score_answer(payload.message, parsed.get('reply') or '', payload.context)
    return {
        'schemaVersion': 'ai-proxy-chat-v1',
        'allowed': True,
        'guardrail': guardrail_result,
        'result': parsed,
        'score': score_result,
        'aiMode': 'gms_proxy',
    }


@app.post('/api/ai/proxy/json')
def proxy_json(payload: JsonProxyRequest) -> dict[str, Any]:
    prompt = str(payload.prompt or '').strip()
    developer_prompt = str(payload.developerPrompt or '').strip()
    if not prompt or not developer_prompt:
        raise HTTPException(status_code=400, detail='prompt and developerPrompt are required')

    response_payload = request_gms_json(prompt, developer_prompt)
    parsed = extract_json_object(extract_output_text(response_payload))
    if not parsed:
        raise HTTPException(status_code=502, detail='GMS response did not contain valid JSON')

    return {
        'schemaVersion': 'ai-proxy-json-v1',
        'task': str(payload.task or 'generic')[:80],
        'result': parsed,
        'aiMode': 'gms_proxy',
    }
