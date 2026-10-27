-- T3.2 realtime: publish product/category changes to subscribed clients
alter publication supabase_realtime add table products;
alter publication supabase_realtime add table categories;
