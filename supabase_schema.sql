-- =====================================================================
-- TABLA OFICIAL DE PERFILES Y PROGRESO PERSISTENTE GOPAES (SUPABASE)
-- Copia y pega este script en el "SQL Editor" de tu proyecto de Supabase
-- =====================================================================

CREATE TABLE IF NOT EXISTS gopaes_profiles (
    username TEXT PRIMARY KEY,
    password_hash TEXT,
    password_salt TEXT,
    created_at TEXT,
    last_activity_date TEXT,
    study_streak INTEGER DEFAULT 1,
    completed_exams INTEGER DEFAULT 0,
    diagnostic_completed BOOLEAN DEFAULT FALSE,
    axes_state JSONB DEFAULT '{}'::jsonb,
    micro_units_state JSONB DEFAULT '{}'::jsonb,
    logs JSONB DEFAULT '[]'::jsonb,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Habilitar Row Level Security (RLS)
ALTER TABLE gopaes_profiles ENABLE ROW LEVEL SECURITY;

-- Política de lectura y escritura para la aplicación GoPAES
CREATE POLICY "Permitir acceso completo a perfiles GoPAES"
ON gopaes_profiles
FOR ALL
USING (true)
WITH CHECK (true);
