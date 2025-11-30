"""Move classworkskv fields from assignment to whiteboard

Revision ID: move_classworkskv_fields
Revises: previous_migration_id
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'move_classworkskv_fields'
down_revision = 'previous_migration_id'
branch_labels = None
depends_on = None


def upgrade():
    # 在 whiteboard 表中添加 ClassworksKV 相关字段
    op.add_column('whiteboard', sa.Column('use_classworkskv', sa.Boolean(), nullable=True, server_default='0'))
    op.add_column('whiteboard', sa.Column('classworkskv_namespace', sa.String(length=100), nullable=True))
    op.add_column('whiteboard', sa.Column('classworkskv_password', sa.String(length=100), nullable=True))
    op.add_column('whiteboard', sa.Column('classworkskv_token', sa.Text(), nullable=True))
    op.add_column('whiteboard', sa.Column('classworkskv_connected', sa.Boolean(), nullable=True, server_default='0'))
    op.add_column('whiteboard', sa.Column('classworkskv_last_sync', sa.DateTime(), nullable=True))
    
    # 如果 assignment 表中有 ClassworksKV 字段，需要迁移数据
    # 首先检查 assignment 表是否有这些字段
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    assignment_columns = [col['name'] for col in inspector.get_columns('assignment')]
    
    # 如果 assignment 表有 ClassworksKV 字段，迁移数据
    if 'is_classworkskv' in assignment_columns:
        # 创建临时表来存储迁移数据
        temp_table = op.create_table(
            'temp_classworkskv_migration',
            sa.Column('whiteboard_id', sa.Integer(), nullable=False),
            sa.Column('namespace', sa.String(100), nullable=True),
            sa.Column('password', sa.String(100), nullable=True),
            sa.Column('token', sa.Text(), nullable=True),
            sa.Column('has_classworkskv', sa.Boolean(), nullable=True)
        )
        
        # 从 assignment 表获取需要迁移的数据
        results = connection.execute("""
            SELECT DISTINCT a.whiteboard_id, 
                   a.classworkskv_namespace as namespace,
                   a.classworkskv_passpin as password,
                   a.classworkskv_token as token,
                   (a.is_classworkskv = 1) as has_classworkskv
            FROM assignment a
            WHERE a.is_classworkskv = 1
            AND a.classworkskv_namespace IS NOT NULL
        """).fetchall()
        
        # 插入到临时表
        for result in results:
            op.bulk_insert(temp_table, [{
                'whiteboard_id': result[0],
                'namespace': result[1],
                'password': result[2],
                'token': result[3],
                'has_classworkskv': result[4]
            }])
        
        # 更新 whiteboard 表
        connection.execute("""
            UPDATE whiteboard w
            JOIN temp_classworkskv_migration t ON w.id = t.whiteboard_id
            SET w.use_classworkskv = t.has_classworkskv,
                w.classworkskv_namespace = t.namespace,
                w.classworkskv_password = t.password,
                w.classworkskv_token = t.token,
                w.classworkskv_connected = 1,
                w.classworkskv_last_sync = NOW()
        """)
        
        # 删除临时表
        op.drop_table('temp_classworkskv_migration')
    
    if 'is_classworkskv' in assignment_columns:
        op.drop_column('assignment', 'is_classworkskv')
    if 'classworkskv_namespace' in assignment_columns:
        op.drop_column('assignment', 'classworkskv_namespace')
    if 'classworkskv_passpin' in assignment_columns:
        op.drop_column('assignment', 'classworkskv_passpin')
    if 'classworkskv_token' in assignment_columns:
        op.drop_column('assignment', 'classworkskv_token')


def downgrade():
    # 降级操作 - 将字段移回 assignment 表
    # 首先在 assignment 表中重新添加字段
    op.add_column('assignment', sa.Column('is_classworkskv', sa.Boolean(), nullable=True))
    op.add_column('assignment', sa.Column('classworkskv_namespace', sa.Text(), nullable=True))
    op.add_column('assignment', sa.Column('classworkskv_passpin', sa.Text(), nullable=True))
    op.add_column('assignment', sa.Column('classworkskv_token', sa.Text(), nullable=True))
    
    # 迁移数据回 assignment 表
    connection = op.get_bind()
    
    # 创建临时表存储要迁移的数据
    temp_table = op.create_table(
        'temp_classworkskv_downgrade',
        sa.Column('whiteboard_id', sa.Integer(), nullable=False),
        sa.Column('namespace', sa.String(100), nullable=True),
        sa.Column('password', sa.String(100), nullable=True),
        sa.Column('token', sa.Text(), nullable=True),
        sa.Column('use_classworkskv', sa.Boolean(), nullable=True)
    )
    
    # 从 whiteboard 表获取数据
    results = connection.execute("""
        SELECT id, classworkskv_namespace, classworkskv_password, classworkskv_token, use_classworkskv
        FROM whiteboard 
        WHERE use_classworkskv = 1
    """).fetchall()
    
    # 插入到临时表
    for result in results:
        op.bulk_insert(temp_table, [{
            'whiteboard_id': result[0],
            'namespace': result[1],
            'password': result[2],
            'token': result[3],
            'use_classworkskv': result[4]
        }])
    
    # 更新 assignment 表
    connection.execute("""
        UPDATE assignment a
        JOIN temp_classworkskv_downgrade t ON a.whiteboard_id = t.whiteboard_id
        SET a.is_classworkskv = t.use_classworkskv,
            a.classworkskv_namespace = t.namespace,
            a.classworkskv_passpin = t.password,
            a.classworkskv_token = t.token
    """)
    
    # 删除临时表
    op.drop_table('temp_classworkskv_downgrade')
    
    # 删除 whiteboard 表中的 ClassworksKV 字段
    op.drop_column('whiteboard', 'use_classworkskv')
    op.drop_column('whiteboard', 'classworkskv_namespace')
    op.drop_column('whiteboard', 'classworkskv_password')
    op.drop_column('whiteboard', 'classworkskv_token')
    op.drop_column('whiteboard', 'classworkskv_connected')
    op.drop_column('whiteboard', 'classworkskv_last_sync')