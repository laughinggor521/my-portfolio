"""Initial schema.
Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa
revision="0001_initial"
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("admins",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("username",sa.String(80),nullable=False),sa.Column("password_hash",sa.String(255),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_admins_username","admins",["username"],unique=True)
    op.create_table("posts",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("title",sa.String(180),nullable=False),sa.Column("slug",sa.String(200),nullable=False),sa.Column("summary",sa.String(500),nullable=False,server_default=""),sa.Column("body",sa.Text(),nullable=False,server_default=""),sa.Column("status",sa.String(20),nullable=False,server_default="draft"),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False),sa.Column("published_at",sa.DateTime(timezone=True),nullable=True))
    op.create_index("ix_posts_slug","posts",["slug"],unique=True)
    op.create_index("ix_posts_status","posts",["status"])
    op.create_table("projects",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("title",sa.String(180),nullable=False),sa.Column("description",sa.String(1000),nullable=False,server_default=""),sa.Column("url",sa.String(2048),nullable=False,server_default=""),sa.Column("image_path",sa.String(500),nullable=False,server_default=""),sa.Column("sort_order",sa.Integer(),nullable=False,server_default="0"),sa.Column("is_published",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("messages",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("nickname",sa.String(80),nullable=False),sa.Column("content",sa.String(2000),nullable=False),sa.Column("is_approved",sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_messages_is_approved","messages",["is_approved"])
def downgrade():
    op.drop_index("ix_messages_is_approved",table_name="messages");op.drop_table("messages")
    op.drop_table("projects")
    op.drop_index("ix_posts_status",table_name="posts");op.drop_index("ix_posts_slug",table_name="posts");op.drop_table("posts")
    op.drop_index("ix_admins_username",table_name="admins");op.drop_table("admins")
