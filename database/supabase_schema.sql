-- OTRADE Bot Database Schema for Supabase
-- Run this SQL in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create conversations table (matches the app's ConversationRecord schema)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create invoices table (matches the app's InvoiceRecord schema)
CREATE TABLE IF NOT EXISTS invoices (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT NOT NULL,
    invoice_number TEXT UNIQUE NOT NULL,
    pdf_url TEXT,
    order_data JSONB NOT NULL,
    total_amount DECIMAL(10,2),
    currency TEXT DEFAULT 'USD',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'paid', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create sessions table for tracking user sessions
CREATE TABLE IF NOT EXISTS sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id TEXT UNIQUE NOT NULL,
    phone_number TEXT,
    user_name TEXT,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_invoices_session_id ON invoices(session_id);
CREATE INDEX IF NOT EXISTS idx_invoices_created_at ON invoices(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_last_activity ON sessions(last_activity);

-- Enable Row Level Security (RLS)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for conversations
CREATE POLICY "Enable read access for all users" ON conversations
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for all users" ON conversations
    FOR INSERT WITH CHECK (true);

-- Create RLS policies for invoices
CREATE POLICY "Enable read access for all users" ON invoices
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for all users" ON invoices
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update for all users" ON invoices
    FOR UPDATE USING (true);

-- Create RLS policies for sessions
CREATE POLICY "Enable read access for all users" ON sessions
    FOR SELECT USING (true);

CREATE POLICY "Enable insert for all users" ON sessions
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable update for all users" ON sessions
    FOR UPDATE USING (true);

-- Create function for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for invoices updated_at
CREATE TRIGGER update_invoices_updated_at 
    BEFORE UPDATE ON invoices 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to clean old conversations (optional)
CREATE OR REPLACE FUNCTION clean_old_conversations(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM conversations 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE conversations IS 'Stores all chat conversations between users and the bot';
COMMENT ON TABLE invoices IS 'Stores generated invoices and order data';
COMMENT ON TABLE sessions IS 'Tracks user sessions and metadata';
