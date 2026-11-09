ALTER TABLE kb.indexed_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb.indexed_documents FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON kb.indexed_documents
  USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
  WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

ALTER TABLE kb.sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb.sections FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON kb.sections
  USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
  WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

ALTER TABLE kb.chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb.chunks FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON kb.chunks
  USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
  WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);

ALTER TABLE kb.reply_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE kb.reply_runs FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON kb.reply_runs
  USING (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
  WITH CHECK (organization_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid);