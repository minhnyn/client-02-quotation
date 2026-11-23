"""Binding customer cases are read unchanged; expected values are not recalculated."""
import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as web
from quotation.calculator import COURSE_NOTICE, QuotationValidationError, calculate_quotation

CASES = json.loads((Path(__file__).resolve().parents[1] / 'data/HansePack_Referenzfaelle.json').read_text(encoding='utf-8'))
VALID = CASES['valid_cases']
INVALID = CASES['invalid_cases']


@pytest.fixture
def client():
    with TestClient(web.app) as instance:
        yield instance


def test_reference_case_coverage():
    assert {case['id'] for case in VALID} == {f'Q{i:02}' for i in range(1, 15)}
    assert {case['id'] for case in INVALID} == {f'E{i:02}' for i in range(1, 11)}


@pytest.mark.parametrize('case', VALID, ids=lambda case: case['id'])
def test_valid_reference(case):
    items = copy.deepcopy(case['input']['items'])
    result = calculate_quotation(items)
    assert result == {**case['expected']['HP-V1'], 'lines': case['expected_lines'], 'course_notice': COURSE_NOTICE}
    assert items == case['input']['items']
    for key in ('goods_net_cents', 'shipping_cents', 'total_cents'):
        assert type(result[key]) is int
    for line in result['lines']:
        for key, value in line.items():
            if key != 'sku':
                assert type(value) is int


@pytest.mark.parametrize('case', INVALID, ids=lambda case: case['id'])
def test_invalid_reference(case):
    with pytest.raises(QuotationValidationError) as caught:
        calculate_quotation(case['input']['items'])
    assert caught.value.reason == case['expected_reason']


@pytest.mark.parametrize('case', VALID, ids=lambda case: case['id'])
def test_api_display_and_export_match_calculation(client, case):
    display = client.post('/api/quotation', json=case['input'])
    export = client.post('/api/quotation/export', json=case['input'])
    assert display.status_code == export.status_code == 200
    assert display.content == export.content
    assert display.json() == calculate_quotation(case['input']['items'])
    assert export.headers['content-type'] == 'application/json'
    assert export.headers['content-disposition'] == 'attachment; filename="hansepack-quotation.json"'


@pytest.mark.parametrize('endpoint', ['/api/quotation', '/api/quotation/export'])
@pytest.mark.parametrize('case', INVALID, ids=lambda case: case['id'])
def test_invalid_api_reaches_business_validation(client, monkeypatch, endpoint, case):
    received = []
    def observed(items):
        received.append(items)
        return calculate_quotation(items)
    monkeypatch.setattr(web, 'calculate_quotation', observed)
    response = client.post(endpoint, json=case['input'])
    assert received == [case['input']['items']]
    assert response.status_code == 400
    assert response.json()['error']['reason'] == case['expected_reason']
    assert response.json()['error']['message']
    assert 'content-disposition' not in response.headers
    assert 'total_cents' not in response.json()


@pytest.mark.parametrize('quantity', ['', 'abc', '50', True, None, 1.0])
def test_no_silent_quantity_coercion(client, quantity):
    payload = {'items': [{'sku': 'HP-BOX', 'quantity': quantity}]}
    with pytest.raises(QuotationValidationError):
        calculate_quotation(payload['items'])
    assert client.post('/api/quotation', json=payload).status_code == 400


def test_three_lines_and_four_line_limit(client):
    items = [{'sku': sku, 'quantity': 1} for sku in ['HP-BOX', 'HP-TAPE', 'HP-FILM']]
    assert client.post('/api/quotation', json={'items': items}).json() == calculate_quotation(items)
    with pytest.raises(QuotationValidationError) as caught:
        calculate_quotation(items + [items[0]])
    assert caught.value.reason == 'too_many_lines'
    assert client.post('/api/quotation', json={'items': items + [items[0]]}).status_code == 400


@pytest.mark.parametrize('payload', [None, [], {}, {'items': None}, {'items': 'bad'}, {'items': [{}]}])
def test_malformed_structure(client, payload):
    response = client.post('/api/quotation', content=json.dumps(payload), headers={'Content-Type': 'application/json'})
    assert response.status_code == 400
    assert response.json()['error']['message']


def test_invalid_json(client):
    assert client.post('/api/quotation', content='{', headers={'Content-Type': 'application/json'}).status_code == 400


def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200
    assert COURSE_NOTICE in response.text
    assert '<html lang="de">' in response.text
    assert 'novalidate' in response.text
