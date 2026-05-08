-- Migration: add follow_up column to interview_questions
ALTER TABLE interview_questions
    ADD COLUMN IF NOT EXISTS follow_up TEXT DEFAULT NULL;
