-- T3.3 soft delete + audit trail
alter table products add column if not exists deleted_at timestamptz;

create table if not exists product_audit (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null,
  actor text not null,
  action text not null,
  before jsonb,
  after jsonb,
  created_at timestamptz not null default now()
);

create index if not exists product_audit_product_id_idx
  on product_audit (product_id, created_at);
