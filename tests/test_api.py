from uuid import uuid4

import pytest

CREATOR = {"platform": "bilibili", "platform_creator_id": "123456", "name": "攻略作者"}


def create_chain(client):
    creator = client.post("/creators", json=CREATOR)
    assert creator.status_code == 201, creator.text
    creator_id = creator.json()["id"]
    guide = client.post(
        "/guides",
        json={
            "creator_id": creator_id,
            "platform": "bilibili",
            "platform_content_id": "BV_TEST",
            "title": "太刀入门",
            "url": "https://www.bilibili.com/video/BV_TEST",
            "published_at": "2026-09-24T10:00:00+08:00",
        },
    )
    assert guide.status_code == 201, guide.text
    guide_id = guide.json()["id"]
    comment = client.post(
        "/comments",
        json={
            "guide_id": guide_id,
            "platform_comment_id": "100",
            "content": "适合新手",
            "likes": 3,
        },
    )
    assert comment.status_code == 201, comment.text
    return creator_id, guide_id, comment.json()["id"]


def test_crud_chain_and_delete_protection(client):
    creator_id, guide_id, comment_id = create_chain(client)
    assert client.get("/health/ready").status_code == 200
    for path, record_id, field, value in [
        ("creators", creator_id, "name", "新名字"),
        ("guides", guide_id, "title", "更新标题"),
        ("comments", comment_id, "content", "更新评论"),
    ]:
        response = client.get(f"/{path}/{record_id}")
        assert response.status_code == 200
        assert response.json()["created_at"]
        response = client.patch(f"/{path}/{record_id}", json={field: value})
        assert response.status_code == 200, response.text
        assert response.json()[field] == value
        assert client.get(f"/{path}/{record_id}").json()[field] == value
    assert client.get("/guides", params={"creator_id": creator_id}).json()[0]["id"] == guide_id
    assert client.get("/comments", params={"guide_id": guide_id}).json()[0]["id"] == comment_id
    assert client.get("/guides", params={"creator_id": str(uuid4())}).json() == []
    assert client.get("/creators?offset=1&limit=1").json() == []
    assert client.delete(f"/creators/{creator_id}").status_code == 409
    assert client.delete(f"/guides/{guide_id}").status_code == 409
    for path, record_id in [
        ("comments", comment_id),
        ("guides", guide_id),
        ("creators", creator_id),
    ]:
        assert client.delete(f"/{path}/{record_id}").status_code == 204
        assert client.get(f"/{path}/{record_id}").status_code == 404


def test_unique_identifiers_and_missing_references(client):
    creator_id, guide_id, comment_id = create_chain(client)
    assert client.post("/creators", json=CREATOR).status_code == 409
    guide = {
        "creator_id": creator_id,
        "platform": "bilibili",
        "platform_content_id": "BV_TEST",
        "title": "duplicate",
        "url": "https://example.com/guide",
    }
    assert client.post("/guides", json=guide).status_code == 409
    assert (
        client.post(
            "/comments",
            json={
                "guide_id": guide_id,
                "platform_comment_id": "100",
                "content": "duplicate",
            },
        ).status_code
        == 409
    )
    assert (
        client.patch(
            f"/guides/{guide_id}",
            json={
                "creator_id": str(uuid4()),
            },
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/comments",
            json={
                "guide_id": str(uuid4()),
                "platform_comment_id": "101",
                "content": "missing",
            },
        ).status_code
        == 409
    )
    # A failed transaction must not poison subsequent requests.
    assert client.get(f"/comments/{comment_id}").status_code == 200


def test_patch_null_and_omitted_fields(client):
    creator_id, guide_id, comment_id = create_chain(client)
    assert client.patch(f"/creators/{creator_id}", json={"name": None}).status_code == 422
    assert client.patch(f"/guides/{guide_id}", json={"view_count": None}).status_code == 422
    assert client.patch(f"/comments/{comment_id}", json={"content": None}).status_code == 422
    assert client.patch(f"/guides/{guide_id}", json={"description": "内容"}).status_code == 200
    assert (
        client.patch(f"/guides/{guide_id}", json={"description": None}).json()["description"]
        is None
    )
    response = client.patch(f"/guides/{guide_id}", json={})
    assert response.json()["title"] == "太刀入门"
    assert response.json()["creator_id"] == creator_id


@pytest.mark.parametrize("path", ["creators", "guides", "comments"])
def test_missing_records_and_pagination_validation(client, path):
    missing = str(uuid4())
    assert client.get(f"/{path}/{missing}").status_code == 404
    assert client.patch(f"/{path}/{missing}", json={}).status_code == 404
    assert client.delete(f"/{path}/{missing}").status_code == 404
    assert client.get(f"/{path}/invalid-uuid").status_code == 422
    assert client.get(f"/{path}?limit=101").status_code == 422
    assert client.get(f"/{path}?offset=-1").status_code == 422


def test_input_validation(client):
    assert client.post("/creators", json={**CREATOR, "followers": 2**63}).status_code == 422
    assert client.post("/creators", json={**CREATOR, "followers": -1}).status_code == 422
    assert client.post("/creators", json={**CREATOR, "name": " "}).status_code == 422
    assert client.post("/creators", json={**CREATOR, "unknown": True}).status_code == 422
    assert (
        client.post(
            "/creators",
            json={
                **CREATOR,
                "last_crawled_at": "2026-09-24T12:00:00",
            },
        ).status_code
        == 422
    )
