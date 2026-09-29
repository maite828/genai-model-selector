"""Deterministic routing over an explicitly synthetic, versioned catalogue."""
import os
import re
from datetime import datetime, timezone
from typing import Literal, TypedDict
from uuid import uuid4

os.environ['LANGSMITH_TRACING'] = 'false'
os.environ['LANGCHAIN_TRACING_V2'] = 'false'

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, ConfigDict, Field, field_validator

VERSION = 'demo-2026-09-v1'
WEIGHTS = {
    'balanced': [0.34, 0.33, 0.33],
    'quality': [0.60, 0.20, 0.20],
    'cost': [0.20, 0.60, 0.20],
    'emissions': [0.20, 0.20, 0.60],
}
CATALOG = [
    {'id': 'local-small', 'name': 'Local compacto', 'location': 'local',
     'quality': {'knowledge': .70, 'reasoning': .59, 'code': .64, 'summary': .78, 'writing': .74},
     'eur_per_1k': .001, 'g_per_1k': .06},
    {'id': 'local-large', 'name': 'Local avanzado', 'location': 'local',
     'quality': {'knowledge': .85, 'reasoning': .82, 'code': .86, 'summary': .88, 'writing': .86},
     'eur_per_1k': .004, 'g_per_1k': .18},
    {'id': 'remote', 'name': 'Remoto de referencia', 'location': 'remote',
     'quality': {'knowledge': .94, 'reasoning': .94, 'code': .95, 'summary': .94, 'writing': .95},
     'eur_per_1k': .012, 'g_per_1k': .35},
]


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    prompt: str = Field(min_length=1, max_length=20000)
    task: Literal['knowledge', 'reasoning', 'code', 'summary', 'writing'] = 'summary'
    profile: Literal['balanced', 'quality', 'cost', 'emissions'] = 'balanced'
    privacy: Literal['public', 'internal', 'sensitive'] = 'internal'
    allow_remote: bool = False
    max_cost: float = Field(default=.02, ge=0, le=10)
    min_quality: float = Field(default=0, ge=0, le=1)
    output_tokens: int = Field(default=512, ge=32, le=2048)

    @field_validator('prompt')
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError('La solicitud no puede estar vacia.')
        return value.strip()


class State(TypedDict, total=False):
    request: dict
    analysis: dict
    candidates: list
    result: dict


def analyze(state):
    req = state['request']
    # Conservative heuristic only: user-declared sensitivity remains authoritative.
    signals = bool(re.search(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}|\b\d{8}[A-Za-z]\b|\b(?:paciente|diagn[oó]stico|contrase[nñ]a|historia cl[ií]nica)\b', req['prompt'], re.I))
    restricted = req['privacy'] != 'public' or signals or not req['allow_remote']
    return {'analysis': {'local_only': restricted, 'sensitive_signal': signals,
                         'input_tokens_estimated': max(1, (len(req['prompt']) + 3) // 4),
                         'task': req['task'], 'classifier': 'user-task + local-heuristic-v1'}}


def evaluate(state):
    req, analysis = state['request'], state['analysis']
    scale = (analysis['input_tokens_estimated'] + req['output_tokens']) / 1000
    candidates = []
    for model in CATALOG:
        quality = model['quality'][req['task']]
        cost = model['eur_per_1k'] * scale
        reasons = []
        if model['location'] == 'remote' and analysis['local_only']:
            reasons.append('Politica de privacidad: solo local')
        if cost > req['max_cost']:
            reasons.append('Supera el presupuesto estimado')
        if quality < req['min_quality']:
            reasons.append('Calidad de demostracion inferior al umbral')
        candidates.append({'id': model['id'], 'name': model['name'], 'location': model['location'],
                           'quality': quality, 'cost': cost, 'emissions': model['g_per_1k'] * scale,
                           'eligible': not reasons, 'reasons': reasons})
    return {'candidates': candidates}


def decide(state):
    req = state['request']
    candidates = state['candidates']
    weights = WEIGHTS[req['profile']]
    # Bounds use the full frozen catalogue, never just the admissible subset.
    bounds = {key: (min(c[key] for c in candidates), max(c[key] for c in candidates))
              for key in ('quality', 'cost', 'emissions')}
    for candidate in candidates:
        values = []
        for key in ('quality', 'cost', 'emissions'):
            low, high = bounds[key]
            value = (candidate[key] - low) / (high - low) if high > low else 1.0
            if key != 'quality' and high > low:
                value = 1 - value
            values.append(value)
        candidate['normalized'] = dict(zip(('quality', 'cost', 'emissions'), values))
        candidate['contributions'] = [v * w for v, w in zip(values, weights)]
        candidate['score'] = sum(candidate['contributions']) if candidate['eligible'] else None
    admissible = sorted((c for c in candidates if c['eligible']), key=lambda c: (-c['score'], c['cost'], c['id']))
    winner = admissible[0] if admissible else None
    return {'result': {'id': str(uuid4()), 'created_at': datetime.now(timezone.utc).isoformat(),
                      'catalog_version': VERSION, 'metric_source': 'synthetic-demonstration',
                      'status': 'selected' if winner else 'abstained', 'selected': winner,
                      'analysis': state['analysis'], 'weights': weights,
                      'constraints': {k: v for k, v in req.items() if k != 'prompt'},
                      'candidates': candidates, 'bounds': bounds,
                      'trace': ['Analisis local', 'Evaluacion de restricciones', 'Normalizacion del catalogo',
                                'Seleccion WSM' if winner else 'Abstencion: ningun candidato admisible'],
                      'execution': None}}


builder = StateGraph(State)
builder.add_node('analyze', analyze)
builder.add_node('evaluate', evaluate)
builder.add_node('decide', decide)
builder.add_edge(START, 'analyze')
builder.add_edge('analyze', 'evaluate')
builder.add_edge('evaluate', 'decide')
builder.add_edge('decide', END)
graph = builder.compile()


def route(request: RouteRequest):
    return graph.invoke({'request': request.model_dump()})['result']
