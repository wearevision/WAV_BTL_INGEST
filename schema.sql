-- Schema for WAV BTL Events
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT,
    year INTEGER,
    brand TEXT,
    cover_url TEXT,
    gallery_urls TEXT[], -- Array of strings
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

-- Policies
-- 1. Allow public read access (for website/Figma)
CREATE POLICY "Enable read access for all users" ON public.events
    FOR SELECT USING (true);

-- 2. Allow full access for service role (for migration script)
CREATE POLICY "Enable all access for service role" ON public.events
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Grant permissions to anon and authenticated roles
GRANT SELECT ON public.events TO anon;
GRANT SELECT ON public.events TO authenticated;
GRANT ALL ON public.events TO service_role;

-- Notify PostgREST to reload schema
NOTIFY pgrst, 'reload schema';
