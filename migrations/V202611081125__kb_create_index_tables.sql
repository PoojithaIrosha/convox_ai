SET search_path TO kb, public;

CREATE TABLE kb.indexed_documents (
  document_id      uuid PRIMARY KEY,          -- = knowledge_documents.id in convox-be
  organization_id  uuid NOT NULL,
  version          int NOT NULL,
  content_hash     bytea NOT NULL,            -- SHA-256 of the file
  title            text NOT NULL,
  embedding_model  varchar(100) NOT NULL,
  section_count    int NOT NULL,
  chunk_count      int NOT NULL,
  indexed_at       timestamptz NOT NULL
);

CREATE TABLE kb.sections (
  id               uuid PRIMARY KEY,
  organization_id  uuid NOT NULL,
  document_id      uuid NOT NULL REFERENCES kb.indexed_documents ON DELETE CASCADE,
  section_index    int NOT NULL,
  heading_path     text[] NOT NULL,
  kind             varchar(10) NOT NULL CHECK (kind IN ('TEXT', 'TABLE', 'IMAGE')),
  body             text NOT NULL,
  page_from        int,
  page_to          int,
  token_count      int NOT NULL,
  CONSTRAINT uq_sections_doc_index UNIQUE (document_id, section_index)
);

CREATE TABLE kb.chunks (
  id               uuid PRIMARY KEY,
  organization_id  uuid NOT NULL,
  document_id      uuid NOT NULL REFERENCES kb.indexed_documents ON DELETE CASCADE,
  section_id       uuid NOT NULL REFERENCES kb.sections ON DELETE CASCADE,
  chunk_index      int NOT NULL,
  text             text NOT NULL,
  search_text      text NOT NULL,
  context_prefix   text,
  embedding        vector(1024) NOT NULL,
  embedding_model  varchar(100) NOT NULL,
  tsv              tsvector GENERATED ALWAYS AS (to_tsvector('simple', search_text)) STORED,
  CONSTRAINT uq_chunks_section_index UNIQUE (section_id, chunk_index)
);

CREATE INDEX idx_chunks_embedding ON kb.chunks
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_chunks_tsv ON kb.chunks USING gin (tsv);
CREATE INDEX idx_chunks_org_doc ON kb.chunks (organization_id, document_id);
CREATE INDEX idx_sections_org_doc ON kb.sections (organization_id, document_id);

CREATE TABLE kb.reply_runs (
  run_id           uuid PRIMARY KEY,
  organization_id  uuid NOT NULL,
  status           varchar(12) NOT NULL CHECK (status IN ('PROCESSING', 'DONE', 'FAILED')),
  result           jsonb,
  created_at       timestamptz NOT NULL,
  updated_at       timestamptz NOT NULL
);