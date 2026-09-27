"""Create creators, guides and comments.

Revision ID: 0001_core
"""

import sqlalchemy as sa

from alembic import op

revision = "0001_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "creators",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("platform_creator_id", sa.String(128), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("profile_url", sa.String(2048), nullable=True),
        sa.Column("avatar_url", sa.String(2048), nullable=True),
        sa.Column("followers", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("total_views", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_creators"),
        sa.UniqueConstraint(
            "platform", "platform_creator_id", name="uq_creators_platform_identity"
        ),
        sa.CheckConstraint("followers >= 0", name=op.f("ck_creators_followers_nonnegative")),
        sa.CheckConstraint("total_views >= 0", name=op.f("ck_creators_total_views_nonnegative")),
    )
    op.create_table(
        "guides",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("creator_id", sa.Uuid(), nullable=False),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("platform_content_id", sa.String(128), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("view_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("like_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("favorite_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("coin_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("comment_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("crawl_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("analysis_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_guides"),
        sa.UniqueConstraint("platform", "platform_content_id", name="uq_guides_platform_identity"),
        sa.CheckConstraint("view_count >= 0", name=op.f("ck_guides_view_count_nonnegative")),
        sa.CheckConstraint("like_count >= 0", name=op.f("ck_guides_like_count_nonnegative")),
        sa.CheckConstraint(
            "favorite_count >= 0", name=op.f("ck_guides_favorite_count_nonnegative")
        ),
        sa.CheckConstraint("coin_count >= 0", name=op.f("ck_guides_coin_count_nonnegative")),
        sa.CheckConstraint("comment_count >= 0", name=op.f("ck_guides_comment_count_nonnegative")),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["creators.id"],
            name="fk_guides_creator_id_creators",
            ondelete="RESTRICT",
        ),
    )
    op.create_index("ix_guides_creator_id", "guides", ["creator_id"])
    op.create_table(
        "comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("guide_id", sa.Uuid(), nullable=False),
        sa.Column("platform_comment_id", sa.String(128), nullable=False),
        sa.Column("parent_comment_id", sa.String(128), nullable=True),
        sa.Column("user_platform_id", sa.String(128), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("likes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("reply_count", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("crawled_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_comments"),
        sa.UniqueConstraint(
            "guide_id", "platform_comment_id", name="uq_comments_platform_identity"
        ),
        sa.CheckConstraint("likes >= 0", name=op.f("ck_comments_likes_nonnegative")),
        sa.CheckConstraint("reply_count >= 0", name=op.f("ck_comments_reply_count_nonnegative")),
        sa.ForeignKeyConstraint(
            ["guide_id"], ["guides.id"], name="fk_comments_guide_id_guides", ondelete="RESTRICT"
        ),
    )
    op.create_index("ix_comments_guide_id", "comments", ["guide_id"])


def downgrade():
    op.drop_table("comments")
    op.drop_table("guides")
    op.drop_table("creators")
