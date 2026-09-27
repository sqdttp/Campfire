from app.crawlers.bilibili import BilibiliAPIError, extract_bvid, get_bilibili_client
from app.main import app


class FakeBilibiliClient:
    def __init__(self):
        self.title = "太刀新手攻略"
        self.comment_likes = 7
        self.comment_requests = 0

    def get_video(self, bvid):
        return {
            "aid": 123456,
            "bvid": bvid,
            "title": self.title,
            "desc": "从零开始学习太刀。",
            "pubdate": 1_725_633_600,
            "owner": {
                "mid": 778899,
                "name": "测试攻略作者",
                "face": "https://i.example/avatar.jpg",
            },
            "stat": {
                "view": 1000,
                "like": 100,
                "favorite": 50,
                "coin": 30,
                "reply": 2,
            },
        }

    def get_comments(self, aid, limit):
        assert aid == 123456
        assert limit == 20
        self.comment_requests += 1
        return [
            {
                "rpid": 9001,
                "root": 0,
                "parent": 0,
                "ctime": 1_725_633_700,
                "like": self.comment_likes,
                "rcount": 1,
                "member": {"mid": "2001"},
                "content": {"message": "很适合新手。"},
            },
            {
                "rpid": 9002,
                "root": 9001,
                "parent": 9001,
                "ctime": 1_725_633_800,
                "like": 2,
                "rcount": 0,
                "member": {"mid": "2002"},
                "content": {"message": "补充一个细节。"},
            },
        ][:limit]


def test_extract_bvid():
    assert extract_bvid("BV1Wz411B7Wn") == "BV1Wz411B7Wn"
    assert extract_bvid("https://www.bilibili.com/video/BV1Wz411B7Wn/?p=1") == "BV1Wz411B7Wn"


def test_import_bilibili_video_is_idempotent(client):
    fake = FakeBilibiliClient()
    app.dependency_overrides[get_bilibili_client] = lambda: fake
    try:
        payload = {
            "video": "https://www.bilibili.com/video/BV1Wz411B7Wn",
            "max_comments": 20,
        }
        first = client.post("/imports/bilibili/videos", json=payload)
        assert first.status_code == 200, first.text
        result = first.json()
        assert result["creator_created"] is True
        assert result["guide_created"] is True
        assert result["comments_fetched"] == 2
        assert result["comments_created"] == 2
        assert result["comments_updated"] == 0

        guide = client.get(f"/guides/{result['guide_id']}").json()
        assert guide["title"] == "太刀新手攻略"
        assert guide["view_count"] == 1000
        assert guide["crawl_status"] == "crawled"
        comments = client.get("/comments", params={"guide_id": result["guide_id"]}).json()
        assert len(comments) == 2
        assert comments[1]["parent_comment_id"] == "9001"

        fake.title = "太刀新手攻略（新版）"
        fake.comment_likes = 9
        second = client.post("/imports/bilibili/videos", json=payload)
        assert second.status_code == 200, second.text
        updated = second.json()
        assert updated["creator_id"] == result["creator_id"]
        assert updated["guide_id"] == result["guide_id"]
        assert updated["creator_created"] is False
        assert updated["guide_created"] is False
        assert updated["comments_created"] == 0
        assert updated["comments_updated"] == 2
        assert client.get(f"/guides/{result['guide_id']}").json()["title"].endswith("（新版）")
        comments = client.get("/comments", params={"guide_id": result["guide_id"]}).json()
        assert comments[0]["likes"] == 9
        assert fake.comment_requests == 2
    finally:
        app.dependency_overrides.pop(get_bilibili_client, None)


def test_import_can_skip_comments(client):
    fake = FakeBilibiliClient()
    app.dependency_overrides[get_bilibili_client] = lambda: fake
    try:
        response = client.post(
            "/imports/bilibili/videos",
            json={"video": "BV1Wz411B7Wn", "fetch_comments": False},
        )
        assert response.status_code == 200, response.text
        assert response.json()["comments_fetched"] == 0
        assert fake.comment_requests == 0
    finally:
        app.dependency_overrides.pop(get_bilibili_client, None)


def test_import_rejects_bad_video(client):
    response = client.post("/imports/bilibili/videos", json={"video": "not-a-video"})
    assert response.status_code == 422


def test_import_maps_upstream_errors(client):
    class BrokenClient:
        def get_video(self, _bvid):
            raise BilibiliAPIError("rate limited", 429)

    app.dependency_overrides[get_bilibili_client] = lambda: BrokenClient()
    try:
        response = client.post("/imports/bilibili/videos", json={"video": "BV1Wz411B7Wn"})
        assert response.status_code == 429
        assert response.json() == {"detail": "rate limited"}
    finally:
        app.dependency_overrides.pop(get_bilibili_client, None)
