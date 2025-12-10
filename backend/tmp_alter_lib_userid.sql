ALTER TABLE libraries DROP CONSTRAINT IF EXISTS libraries_user_id_key;
ALTER TABLE libraries ALTER COLUMN user_id TYPE uuid USING gen_random_uuid();
DROP INDEX IF EXISTS idx_libraries_user_id;
CREATE INDEX idx_libraries_user_id ON libraries(user_id);
