-- Migration: add mistakes and improvement columns to interview_questions
-- Run once against the student_tracker database

ALTER TABLE interview_questions
    ADD COLUMN IF NOT EXISTS mistakes    JSONB  DEFAULT '[]',
    ADD COLUMN IF NOT EXISTS improvement TEXT   DEFAULT NULL;
