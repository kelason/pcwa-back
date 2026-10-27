-- T1.1 richer product fields (run in the Supabase SQL editor)
alter table products
  add column if not exists description text,
  add column if not exists image_url text,
  add column if not exists sku text,
  add column if not exists stock integer not null default 0;

alter table products
  drop constraint if exists products_stock_non_negative;
alter table products
  add constraint products_stock_non_negative check (stock >= 0);
