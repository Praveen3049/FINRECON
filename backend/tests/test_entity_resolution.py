import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.entity_resolution.models import (
    ConfidenceBucket,
    EntityResolutionQuery,
)
from app.services.entity_resolution.matcher import EntityMatcher
from app.services.entity_resolution.service import EntityResolutionService

client = TestClient(app)

SAMPLE_ENTITIES = [
    {
        "id": "ent-acme-1",
        "name": "Acme Corp",
        "legal_name": "Acme Corporation LLC",
        "entity_type": "CUSTOMER",
        "tax_id": "12-3456789",
        "email": "billing@acme.com",
        "phone": "+1-555-0192",
        "wallet_address": "0x71c8364437a9c47f65630c45159392c1a5641001",
        "bank_account_number": "9876543210",
    },
    {
        "id": "ent-starlight-2",
        "name": "Starlight Technologies",
        "legal_name": "Starlight Tech Systems Inc",
        "entity_type": "CUSTOMER",
        "tax_id": "98-7654321",
        "email": "finance@starlight.tech",
        "phone": "+1-555-0481",
        "wallet_address": "0x28c6c06298d514db089934071355e5743bf21d60",
    },
    {
        "id": "ent-cloudscale-3",
        "name": "CloudScale Hosting",
        "legal_name": "CloudScale Infrastructure Ltd",
        "entity_type": "VENDOR",
        "tax_id": "45-6789012",
        "email": "invoicing@cloudscale.net",
    },
    {
        "id": "ent-apex-4",
        "name": "Apex Capital",
        "legal_name": "Apex Capital Management LP",
        "entity_type": "PARTNER",
        "tax_id": "55-1234567",
        "email": "investor-relations@apexcap.com",
    },
]


@pytest.fixture(scope="module", autouse=True)
def setup_test_entities():
    from app.core.database import SessionLocal
    from app.models.entity import Entity
    db = SessionLocal()
    created_ids = []
    for ent in SAMPLE_ENTITIES:
        existing = db.query(Entity).filter(Entity.name == ent["name"]).first()
        if not existing:
            obj = Entity(
                id=ent["id"],
                name=ent["name"],
                legal_name=ent["legal_name"],
                entity_type=ent["entity_type"],
                tax_id=ent.get("tax_id"),
                email=ent.get("email"),
                phone=ent.get("phone"),
                wallet_address=ent.get("wallet_address"),
                bank_account_number=ent.get("bank_account_number"),
            )
            db.add(obj)
            created_ids.append(obj.id)
    db.commit()

    try:
        yield
    finally:
        if created_ids:
            db.query(Entity).filter(Entity.id.in_(created_ids)).delete(synchronize_session=False)
            db.commit()
        db.close()


class TestDeterministicEntityMatching:
    """Test deterministic exact matches on strong identifiers"""

    def test_exact_wallet_address_resolution(self):
        query = EntityResolutionQuery(
            wallet_address="0x71C8364437a9C47F65630C45159392C1a5641001"  # mixed case
        )
        res = EntityResolutionService.resolve_query(query, candidate_entities=SAMPLE_ENTITIES)
        assert res.resolved is True
        assert res.best_match is not None
        assert res.best_match.entity_id == "ent-acme-1"
        assert res.best_match.confidence_score == 1.0
        assert res.best_match.confidence_bucket == ConfidenceBucket.HIGH
        assert any(e.rule_name == "EXACT_WALLET_MATCH" for e in res.best_match.evidence)

    def test_exact_email_resolution(self):
        query = EntityResolutionQuery(email="BILLING@ACME.COM")
        res = EntityResolutionService.resolve_query(query, candidate_entities=SAMPLE_ENTITIES)
        assert res.resolved is True
        assert res.best_match is not None
        assert res.best_match.entity_id == "ent-acme-1"
        assert res.best_match.confidence_score == 0.95
        assert res.best_match.confidence_bucket == ConfidenceBucket.HIGH
        assert any(e.rule_name == "EXACT_EMAIL_MATCH" for e in res.best_match.evidence)

    def test_exact_tax_id_resolution(self):
        query = EntityResolutionQuery(tax_id="123456789")  # unformatted digits
        res = EntityResolutionService.resolve_query(query, candidate_entities=SAMPLE_ENTITIES)
        assert res.resolved is True
        assert res.best_match is not None
        assert res.best_match.entity_id == "ent-acme-1"
        assert res.best_match.confidence_score == 1.0
        assert any(e.rule_name == "EXACT_TAX_ID_MATCH" for e in res.best_match.evidence)

    def test_exact_phone_resolution(self):
        query = EntityResolutionQuery(phone="(555) 0192")
        res = EntityResolutionService.resolve_query(query, candidate_entities=SAMPLE_ENTITIES)
        assert res.resolved is True
        assert res.best_match is not None
        assert res.best_match.entity_id == "ent-acme-1"
        assert res.best_match.confidence_score == 0.90
        assert any(e.rule_name == "EXACT_PHONE_MATCH" for e in res.best_match.evidence)


class TestFuzzyNameEntityMatching:
    """Test RapidFuzz name and legal entity matching"""

    def test_acme_corp_fuzzy_match(self):
        query = EntityResolutionQuery(name="Acme Corporation")
        res = EntityResolutionService.resolve_query(query, candidate_entities=SAMPLE_ENTITIES)
        assert res.resolved is True
        assert res.best_match is not None
        assert res.best_match.entity_id == "ent-acme-1"
        assert res.best_match.confidence_bucket == ConfidenceBucket.HIGH
        assert res.best_match.confidence_score >= 0.85

    def test_starlight_tech_fuzzy_match(self):
        query = EntityResolutionQuery(name="Starlight Tech Systems")
        res = EntityResolutionService.resolve_query(query, candidate_entities=SAMPLE_ENTITIES)
        assert res.resolved is True
        assert res.best_match is not None
        assert res.best_match.entity_id == "ent-starlight-2"
        assert res.best_match.confidence_score >= 0.85

    def test_cloudscale_infrastructure_fuzzy_match(self):
        query = EntityResolutionQuery(name="Cloudscale Infrastructure")
        res = EntityResolutionService.resolve_query(query, candidate_entities=SAMPLE_ENTITIES)
        assert res.resolved is True
        assert res.best_match is not None
        assert res.best_match.entity_id == "ent-cloudscale-3"
        assert res.best_match.confidence_bucket == ConfidenceBucket.HIGH


class TestConfidenceBucketsAndAmbiguity:
    """Test confidence scoring thresholds, ambiguity flagging, and explainability"""

    def test_medium_confidence_bucket(self):
        # An abbreviated/loose match without secondary corroboration ("Infra" vs "Infrastructure")
        query = EntityResolutionQuery(name="Cloudscale Infra Ltd")
        res = EntityResolutionService.resolve_query(query, candidate_entities=SAMPLE_ENTITIES)
        assert res.best_match is not None
        assert res.best_match.confidence_bucket == ConfidenceBucket.MEDIUM
        assert res.requires_manual_review is True
        assert res.resolved is False

    def test_ambiguity_detection(self):
        ambiguous_entities = [
            {"id": "amb-1", "name": "Global Tech Ventures A", "entity_type": "CUSTOMER"},
            {"id": "amb-2", "name": "Global Tech Ventures B", "entity_type": "CUSTOMER"},
        ]
        query = EntityResolutionQuery(name="Global Tech Ventures")
        res = EntityResolutionService.resolve_query(query, candidate_entities=ambiguous_entities)
        assert res.requires_manual_review is True
        assert res.resolved is False
        assert "Ambiguous match" in res.resolution_notes

    def test_explainable_evidence_structure(self):
        query = EntityResolutionQuery(
            name="Acme Corp LLC",
            email="billing@acme.com",
            wallet_address="0x71c8364437a9c47f65630c45159392c1a5641001",
        )
        res = EntityResolutionService.resolve_query(query, candidate_entities=SAMPLE_ENTITIES)
        best = res.best_match
        assert best is not None
        assert len(best.evidence) >= 2
        for ev in best.evidence:
            assert ev.rule_name is not None
            assert ev.score_contribution > 0
            assert ev.explanation != ""


class TestEntityResolutionAPI:
    """Test REST API endpoints for entity resolution and management"""

    def test_api_resolve_endpoint(self):
        payload = {"name": "Acme Corp", "email": "billing@acme.com"}
        response = client.post("/api/v1/entities/resolve", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "resolved" in data
        assert "best_match" in data
        assert data["resolved"] is True
        assert data["best_match"]["name"] == "Acme Corp"
        assert len(data["best_match"]["evidence"]) > 0

    def test_api_list_entities(self):
        response = client.get("/api/v1/entities?limit=100")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 4  # From seed data
        names = [e["name"] for e in data]
        assert "Acme Corp" in names
        assert "Starlight Technologies" in names

    def test_api_create_and_get_entity(self):
        create_payload = {
            "name": "Nova Dynamics",
            "legal_name": "Nova Dynamics Corp",
            "entity_type": "PARTNER",
            "tax_id": "77-8899001",
            "email": "ops@novadynamics.io",
            "wallet_address": "0x55d398326f99059ff775485246999027b3197955",
        }
        create_resp = client.post("/api/v1/entities", json=create_payload)
        assert create_resp.status_code == 201
        created_data = create_resp.json()
        entity_id = created_data["id"]
        assert created_data["name"] == "Nova Dynamics"

        # Fetch detail
        detail_resp = client.get(f"/api/v1/entities/{entity_id}")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["id"] == entity_id
        assert detail_data["tax_id"] == "77-8899001"
        assert "transactions" in detail_data
