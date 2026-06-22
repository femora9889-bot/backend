"""category integer pk

Revision ID: 140994f09b73
Revises: 035b0009a53c
Create Date: 2026-06-20 14:54:23.562726

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '140994f09b73'
down_revision: Union[str, None] = '035b0009a53c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. مسح البيانات أولاً (قبل حذف الـ FK)
    op.execute("TRUNCATE TABLE store_categories")
    op.execute("UPDATE products SET category_id = NULL")

    # 2. حذف FK constraints
    op.execute("ALTER TABLE products DROP CONSTRAINT IF EXISTS products_category_id_fkey")
    op.execute("ALTER TABLE store_categories DROP CONSTRAINT IF EXISTS store_categories_category_id_fkey")

    # 3. حذف وإعادة بناء categories بـ integer PK
    op.drop_table('categories')
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('name_ar', sa.String(100), nullable=False),
    )

    # 4. تغيير نوع الأعمدة — products فاضية من قيم category_id، store_categories فاضية كلياً
    op.execute("ALTER TABLE products ALTER COLUMN category_id TYPE INTEGER USING NULL::INTEGER")
    op.execute("ALTER TABLE store_categories ALTER COLUMN category_id TYPE INTEGER USING category_id::integer")

    # 5. إعادة FK constraints
    op.create_foreign_key('products_category_id_fkey', 'products', 'categories', ['category_id'], ['id'])
    op.create_foreign_key('store_categories_category_id_fkey', 'store_categories', 'categories', ['category_id'], ['id'])


def downgrade() -> None:
    pass
