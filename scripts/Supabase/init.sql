-- Script de inicialización completo para Supabase
-- Ejecuta el schema base y luego carga los datos generados en data/out

\echo '>> Aplicando schema base de Supabase'
\ir schema.sql

\echo '>> Cargando datos generados para Supabase'
\ir ../../data/out/supabase_data.sql
