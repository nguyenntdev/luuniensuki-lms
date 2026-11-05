"""Add rbpc_workshop_slots and rbpc_seat_reservations tables for availability inventory and calendar

Revision ID: 0082_rbpc_availability_inventory_calendar
Revises: 0081_rbpc_inquiry_notification_preferences
Create Date: 2026-11-06 08:00:00.000000

V5-T102 / W10-A02: Real availability inventory/calendar.
Manage limited workshop slots, seat capacity per time slot, reserve timeouts, provider confirmation, and no false checkouts.
Negative abuse: Two users cannot confirm the last remaining seat twice (concurrency race condition prevented).

Strictly additive:
- Creates rbpc_workshop_slots table with constraints and indexes
- Creates rbpc_seat_reservations table with constraints and indexes
- Adds slot_id and reservation_id columns to rbpc_inquiries with indexes
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0082_rbpc_availability_inventory_calendar"
down_revision: Union[str, Sequence[str], None] = "0081_rbpc_inquiry_notification_preferences"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        -- 1. Create rbpc_workshop_slots table
        CREATE TABLE IF NOT EXISTS rbpc_workshop_slots (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            experience_id UUID NOT NULL REFERENCES rbpc_experiences(id) ON DELETE CASCADE,
            start_time TIMESTAMPTZ NOT NULL,
            end_time TIMESTAMPTZ NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 10,
            reserved_seats INTEGER NOT NULL DEFAULT 0,
            confirmed_seats INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'open',
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_rbpc_slots_capacity_range CHECK (capacity >= 1 AND capacity <= 100),
            CONSTRAINT ck_rbpc_slots_reserved_nonneg CHECK (reserved_seats >= 0),
            CONSTRAINT ck_rbpc_slots_confirmed_nonneg CHECK (confirmed_seats >= 0),
            CONSTRAINT ck_rbpc_slots_capacity_bound CHECK (reserved_seats + confirmed_seats <= capacity),
            CONSTRAINT ck_rbpc_slots_time_valid CHECK (end_time > start_time),
            CONSTRAINT ck_rbpc_slots_status CHECK (status IN ('open','closed','cancelled'))
        );

        CREATE INDEX IF NOT EXISTS idx_rbpc_slots_exp ON rbpc_workshop_slots(experience_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_slots_time ON rbpc_workshop_slots(start_time, end_time);
        CREATE INDEX IF NOT EXISTS idx_rbpc_slots_status ON rbpc_workshop_slots(status);

        -- 2. Create rbpc_seat_reservations table
        CREATE TABLE IF NOT EXISTS rbpc_seat_reservations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            slot_id UUID NOT NULL REFERENCES rbpc_workshop_slots(id) ON DELETE CASCADE,
            inquiry_id UUID REFERENCES rbpc_inquiries(id) ON DELETE SET NULL,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            public_ref TEXT NOT NULL UNIQUE,
            seats INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'pending',
            hold_timeout_seconds INTEGER NOT NULL DEFAULT 900,
            expires_at TIMESTAMPTZ NOT NULL,
            confirmed_at TIMESTAMPTZ,
            confirmed_by UUID REFERENCES users(id) ON DELETE SET NULL,
            customer_name TEXT NOT NULL,
            customer_contact TEXT NOT NULL,
            idempotency_key TEXT UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ck_rbpc_reservations_seats_range CHECK (seats >= 1 AND seats <= 20),
            CONSTRAINT ck_rbpc_reservations_status CHECK (status IN ('pending','confirmed','expired','cancelled'))
        );

        CREATE INDEX IF NOT EXISTS idx_rbpc_reservations_slot ON rbpc_seat_reservations(slot_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_reservations_status ON rbpc_seat_reservations(status);
        CREATE INDEX IF NOT EXISTS idx_rbpc_reservations_expires ON rbpc_seat_reservations(expires_at);
        CREATE INDEX IF NOT EXISTS idx_rbpc_reservations_inquiry ON rbpc_seat_reservations(inquiry_id);

        -- 3. Add slot_id and reservation_id to rbpc_inquiries
        ALTER TABLE rbpc_inquiries ADD COLUMN IF NOT EXISTS slot_id UUID REFERENCES rbpc_workshop_slots(id) ON DELETE SET NULL;
        ALTER TABLE rbpc_inquiries ADD COLUMN IF NOT EXISTS reservation_id UUID REFERENCES rbpc_seat_reservations(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_rbpc_inquiries_slot ON rbpc_inquiries(slot_id);
        CREATE INDEX IF NOT EXISTS idx_rbpc_inquiries_reservation ON rbpc_inquiries(reservation_id);
        """
    )


def downgrade() -> None:
    pass
