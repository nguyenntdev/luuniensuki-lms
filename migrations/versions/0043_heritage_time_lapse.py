"""heritage time-lapse

Adds three tables for the Heritage Time-Lapse feature:
- heritage_eras
- historical_events
- motif_eras

Plus seed data covering 3 eras (1802-1841, 1841-1883, 1883-1945) and 12+
historical events about the Cửu Đỉnh casting.

All additive — no existing tables modified. Reversible via downgrade.

Revision ID: 0043_heritage_time_lapse
Revises: 0042_streak_repair_economy
Create Date: 2026-05-20
"""
from __future__ import annotations

from alembic import op


revision = "0043_heritage_time_lapse"
down_revision = "0042_streak_repair_economy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # heritage_eras
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE heritage_eras (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            slug varchar(100) UNIQUE NOT NULL,
            name_vi varchar(200) NOT NULL,
            name_en varchar(200) NOT NULL,
            start_year integer NOT NULL,
            end_year integer NOT NULL,
            color_hex varchar(7) NOT NULL,
            sort_order integer NOT NULL DEFAULT 0,
            created_at timestamptz NOT NULL DEFAULT NOW(),
            CONSTRAINT heritage_eras_year_range CHECK (end_year >= start_year),
            CONSTRAINT heritage_eras_color_hex_format
                CHECK (color_hex ~ '^#[0-9A-Fa-f]{6}$')
        );
        CREATE INDEX idx_heritage_eras_sort_order ON heritage_eras(sort_order);
        """
    )

    # ------------------------------------------------------------------
    # historical_events
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE historical_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            era_id uuid NOT NULL REFERENCES heritage_eras(id) ON DELETE CASCADE,
            slug varchar(100) UNIQUE NOT NULL,
            name_vi varchar(300) NOT NULL,
            name_en varchar(300) NOT NULL,
            occurred_on date NOT NULL,
            description_vi text NOT NULL DEFAULT '',
            description_en text NOT NULL DEFAULT '',
            motif_id uuid REFERENCES motifs(id) ON DELETE SET NULL,
            urn_id uuid REFERENCES urns(id) ON DELETE SET NULL,
            importance integer NOT NULL DEFAULT 1,
            created_at timestamptz NOT NULL DEFAULT NOW(),
            CONSTRAINT historical_events_importance_range
                CHECK (importance BETWEEN 1 AND 5)
        );
        CREATE INDEX idx_historical_events_occurred_on ON historical_events(occurred_on);
        CREATE INDEX idx_historical_events_era ON historical_events(era_id);
        """
    )

    # ------------------------------------------------------------------
    # motif_eras
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE TABLE motif_eras (
            motif_id uuid NOT NULL REFERENCES motifs(id) ON DELETE CASCADE,
            era_id  uuid NOT NULL REFERENCES heritage_eras(id) ON DELETE CASCADE,
            PRIMARY KEY (motif_id, era_id)
        );
        CREATE INDEX idx_motif_eras_era ON motif_eras(era_id);
        """
    )

    # ------------------------------------------------------------------
    # Seed: 3 eras
    # ------------------------------------------------------------------
    op.execute(
        """
        INSERT INTO heritage_eras (slug, name_vi, name_en, start_year, end_year, color_hex, sort_order) VALUES
            ('gia-long-minh-mang',  'Gia Long - Minh Mạng',     'Gia Long - Minh Mang',     1802, 1841, '#D4AF37', 1),
            ('thieu-tri-tu-duc',    'Thiệu Trị - Tự Đức',       'Thieu Tri - Tu Duc',       1841, 1883, '#8B4513', 2),
            ('phap-thuoc-bao-dai',  'Pháp thuộc - Bảo Đại',     'French Colonial - Bao Dai', 1883, 1945, '#2F4F4F', 3)
        ON CONFLICT (slug) DO NOTHING;
        """
    )

    # ------------------------------------------------------------------
    # Seed: 12 historical events about the Cửu Đỉnh
    # ------------------------------------------------------------------
    op.execute(
        """
        INSERT INTO historical_events (era_id, slug, name_vi, name_en, occurred_on, description_vi, description_en, importance)
        SELECT id, slug_v, name_vi_v, name_en_v, occurred_on_v::date, desc_vi_v, desc_en_v, importance_v
        FROM heritage_eras,
             (VALUES
                ('gia-long-minh-mang', 'minh-mang-leu-1820',
                 'Vua Minh Mạng lên ngôi',
                 'Emperor Minh Mang ascends the throne',
                 '1820-02-14',
                 'Hoàng đế Minh Mạng kế vị Gia Long, mở đầu giai đoạn cải cách nhà Nguyễn.',
                 'Emperor Minh Mang succeeded Gia Long, beginning the Nguyen dynasty reform period.', 4),

                ('gia-long-minh-mang', 'cuu-dinh-decree-1835',
                 'Minh Mạng ra chiếu đúc Cửu Đỉnh',
                 'Minh Mang issues the decree to cast the Nine Dynastic Urns',
                 '1835-12-01',
                 'Vua Minh Mạng ban chiếu đúc 9 đỉnh đồng tượng trưng cho quyền lực và sự trường tồn của triều Nguyễn.',
                 'Emperor Minh Mang issued a decree to cast nine bronze urns symbolising the authority and longevity of the Nguyen dynasty.', 5),

                ('gia-long-minh-mang', 'cuu-dinh-foundry-1835',
                 'Khởi công đúc Cửu Đỉnh tại Huế',
                 'Casting of the Nine Urns begins in Hue',
                 '1835-12-15',
                 'Việc đúc 9 đỉnh được khởi công tại xưởng đúc đồng kinh thành Huế dưới sự giám sát của các quan thợ.',
                 'Casting of the nine urns commenced at the imperial foundry in Hue under the supervision of master craftsmen.', 4),

                ('gia-long-minh-mang', 'cao-dinh-completed-1836',
                 'Hoàn thành Cao Đỉnh',
                 'Cao Urn completed',
                 '1836-06-20',
                 'Cao Đỉnh, đỉnh đầu tiên đại diện cho vua Gia Long, được hoàn thành.',
                 'Cao Urn, the first dedicated to Emperor Gia Long, was completed.', 3),

                ('gia-long-minh-mang', 'nhan-dinh-completed-1836',
                 'Hoàn thành Nhân Đỉnh',
                 'Nhan Urn completed',
                 '1836-09-15',
                 'Nhân Đỉnh được đúc xong, dành cho vua Minh Mạng.',
                 'Nhan Urn, dedicated to Emperor Minh Mang, was completed.', 3),

                ('gia-long-minh-mang', 'cuu-dinh-completed-1837',
                 'Hoàn thành toàn bộ 9 đỉnh',
                 'All nine urns completed',
                 '1837-03-01',
                 'Toàn bộ 9 đỉnh được đúc xong và đặt tại Thế Miếu trong Đại Nội Huế.',
                 'All nine urns were completed and placed at The Mieu shrine inside the Hue Imperial City.', 5),

                ('gia-long-minh-mang', 'cuu-dinh-naming-1837',
                 'Đặt tên cho từng đỉnh',
                 'Naming ceremony for each urn',
                 '1837-03-15',
                 'Vua Minh Mạng chính thức đặt tên cho từng đỉnh: Cao, Nhân, Chương, Anh, Nghị, Thuần, Tuyên, Dũ, Huyền.',
                 'Emperor Minh Mang officially named each urn: Cao, Nhan, Chuong, Anh, Nghi, Thuan, Tuyen, Du, Huyen.', 5),

                ('thieu-tri-tu-duc', 'thieu-tri-coronation-1841',
                 'Vua Thiệu Trị lên ngôi',
                 'Emperor Thieu Tri ascends the throne',
                 '1841-02-11',
                 'Thiệu Trị kế vị Minh Mạng, tiếp tục bảo tồn các di sản của triều Nguyễn.',
                 'Thieu Tri succeeded Minh Mang, continuing to preserve the Nguyen dynasty heritage.', 3),

                ('thieu-tri-tu-duc', 'tu-duc-coronation-1847',
                 'Vua Tự Đức lên ngôi',
                 'Emperor Tu Duc ascends the throne',
                 '1847-11-10',
                 'Tự Đức trở thành hoàng đế thứ 4 của triều Nguyễn.',
                 'Tu Duc became the fourth emperor of the Nguyen dynasty.', 3),

                ('phap-thuoc-bao-dai', 'french-protectorate-1883',
                 'Hoà ước Patenôtre và bảo hộ Pháp',
                 'Patenotre Treaty and French Protectorate',
                 '1884-06-06',
                 'Việt Nam trở thành xứ bảo hộ của Pháp; di sản hoàng cung được giữ lại nhưng quyền lực bị giới hạn.',
                 'Vietnam became a French protectorate; imperial heritage was preserved but royal authority was curtailed.', 4),

                ('phap-thuoc-bao-dai', 'bao-dai-coronation-1926',
                 'Vua Bảo Đại lên ngôi',
                 'Emperor Bao Dai ascends the throne',
                 '1926-01-08',
                 'Bảo Đại trở thành hoàng đế cuối cùng của triều Nguyễn.',
                 'Bao Dai became the last emperor of the Nguyen dynasty.', 4),

                ('phap-thuoc-bao-dai', 'abdication-1945',
                 'Vua Bảo Đại thoái vị',
                 'Emperor Bao Dai abdicates',
                 '1945-08-30',
                 'Bảo Đại thoái vị, chấm dứt 143 năm trị vì của triều Nguyễn.',
                 'Bao Dai abdicated, ending the 143-year reign of the Nguyen dynasty.', 5)
             ) AS evt(era_slug, slug_v, name_vi_v, name_en_v, occurred_on_v, desc_vi_v, desc_en_v, importance_v)
        WHERE heritage_eras.slug = evt.era_slug
        ON CONFLICT (slug) DO NOTHING;
        """
    )

    # Backfill motif_eras: link every existing motif to gia-long-minh-mang
    # (the era of casting). Admins can refine via the admin endpoints.
    op.execute(
        """
        INSERT INTO motif_eras (motif_id, era_id)
        SELECT m.id, e.id
        FROM motifs m, heritage_eras e
        WHERE e.slug = 'gia-long-minh-mang'
        ON CONFLICT (motif_id, era_id) DO NOTHING;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS motif_eras CASCADE")
    op.execute("DROP TABLE IF EXISTS historical_events CASCADE")
    op.execute("DROP TABLE IF EXISTS heritage_eras CASCADE")
