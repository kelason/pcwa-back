-- T2.6 image upload bucket (public read, writes go through the backend)
insert into storage.buckets (id, name, public)
values ('product-images', 'product-images', true)
on conflict (id) do nothing;
