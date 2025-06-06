-- Step 1: Create Partitioned Table
DROP TABLE if exists augur_data.contributors_new; 
CREATE TABLE augur_data.contributors_new (
  cntrb_login varchar COLLATE "pg_catalog"."default",
  cntrb_email varchar COLLATE "pg_catalog"."default",
  cntrb_full_name varchar COLLATE "pg_catalog"."default",
  cntrb_company varchar COLLATE "pg_catalog"."default",
  cntrb_created_at timestamp(0),
  cntrb_type varchar COLLATE "pg_catalog"."default",
  cntrb_fake int2 DEFAULT 0,
  cntrb_deleted int2 DEFAULT 0,
  cntrb_long numeric(11,8) DEFAULT NULL::numeric,
  cntrb_lat numeric(10,8) DEFAULT NULL::numeric,
  cntrb_country_code char(3) COLLATE "pg_catalog"."default" DEFAULT NULL::bpchar,
  cntrb_state varchar COLLATE "pg_catalog"."default",
  cntrb_city varchar COLLATE "pg_catalog"."default",
  cntrb_location varchar COLLATE "pg_catalog"."default",
  cntrb_canonical varchar COLLATE "pg_catalog"."default",
  cntrb_last_used timestamptz(0) DEFAULT NULL::timestamp with time zone,
  gh_user_id int8,
  gh_login varchar COLLATE "pg_catalog"."default",
  gh_url varchar COLLATE "pg_catalog"."default",
  gh_html_url varchar COLLATE "pg_catalog"."default",
  gh_node_id varchar COLLATE "pg_catalog"."default",
  gh_avatar_url varchar COLLATE "pg_catalog"."default",
  gh_gravatar_id varchar COLLATE "pg_catalog"."default",
  gh_followers_url varchar COLLATE "pg_catalog"."default",
  gh_following_url varchar COLLATE "pg_catalog"."default",
  gh_gists_url varchar COLLATE "pg_catalog"."default",
  gh_starred_url varchar COLLATE "pg_catalog"."default",
  gh_subscriptions_url varchar COLLATE "pg_catalog"."default",
  gh_organizations_url varchar COLLATE "pg_catalog"."default",
  gh_repos_url varchar COLLATE "pg_catalog"."default",
  gh_events_url varchar COLLATE "pg_catalog"."default",
  gh_received_events_url varchar COLLATE "pg_catalog"."default",
  gh_type varchar COLLATE "pg_catalog"."default",
  gh_site_admin varchar COLLATE "pg_catalog"."default",
  gl_web_url varchar COLLATE "pg_catalog"."default",
  gl_avatar_url varchar COLLATE "pg_catalog"."default",
  gl_state varchar COLLATE "pg_catalog"."default",
  gl_username varchar COLLATE "pg_catalog"."default",
  gl_full_name varchar COLLATE "pg_catalog"."default",
  gl_id int8,
  tool_source varchar COLLATE "pg_catalog"."default",
  tool_version varchar COLLATE "pg_catalog"."default",
  data_source varchar COLLATE "pg_catalog"."default",
  data_collection_date timestamp(0) DEFAULT CURRENT_TIMESTAMP,
    cntrb_id uuid NOT NULL,
  PRIMARY KEY (cntrb_id)
) PARTITION BY HASH (cntrb_id)
TABLESPACE speed;

-- Step 2: Create Partitions (512)
DO $$
BEGIN
  FOR i IN 0..511 LOOP
    EXECUTE format('CREATE TABLE augur_data.contributors_new_p%s PARTITION OF augur_data.contributors_new FOR VALUES WITH (modulus 512, remainder %s) TABLESPACE speed;', i, i);
  END LOOP;
END $$;


-- This creates the unique index on each partition. Skipping for now due to GitLab issues
DO $$
DECLARE
  part RECORD;
BEGIN
  FOR part IN
    SELECT inhrelid::regclass AS partition_name
    FROM pg_inherits
    JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
    JOIN pg_namespace ns ON parent.relnamespace = ns.oid
    WHERE parent.relname = 'contributors_new'
      AND ns.nspname = 'augur_data'
  LOOP
    EXECUTE format('CREATE UNIQUE INDEX ON %s (gh_user_id) WHERE gh_user_id IS NOT NULL;', part.partition_name);
  END LOOP;
END $$;

/**
CREATE UNIQUE INDEX idx_gh_user_id ON contributors_new (gh_user_id) WHERE gh_user_id IS NOT NULL;
-- Step 3: Add Deferred Unique Constraints (Per Table)
-- NOTE: gh_user_id can be NULL, so partial unique index
CREATE UNIQUE INDEX contributors_new_gh_user_id_unique ON augur_data.contributors_new (gh_user_id) 
WHERE gh_user_id IS NOT NULL;
**/ 

/**
ALTER TABLE augur_data.contributors_new ADD CONSTRAINT gl_id_unique UNIQUE (gl_id) DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE augur_data.contributors_new ADD CONSTRAINT gl_username_unique UNIQUE (gl_username) DEFERRABLE INITIALLY DEFERRED;
**/ 
-- Step 4: Recreate Indexes

-- Hash Indexes (formerly)
CREATE INDEX cnt_fullname_new ON augur_data.contributors_new (cntrb_full_name COLLATE "pg_catalog"."default" "pg_catalog"."text_ops");
CREATE INDEX cntrb_theemail_new ON augur_data.contributors_new (cntrb_email COLLATE "pg_catalog"."default" "pg_catalog"."text_ops");

-- Btree Indexes
CREATE INDEX cntrb_canonical_idx_new ON augur_data.contributors_new USING btree (cntrb_canonical COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST);
CREATE INDEX cntrb_login_platform_index_new ON augur_data.contributors_new USING btree (cntrb_login COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST);
CREATE INDEX contributors_idx_cntrb_email3_new ON augur_data.contributors_new USING btree (cntrb_email COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST);
CREATE INDEX gh_login_new ON augur_data.contributors_new USING btree (gh_login COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS FIRST);
CREATE INDEX login_new ON augur_data.contributors_new USING btree (cntrb_login COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST);
CREATE INDEX login_contributor_idx_new ON augur_data.contributors_new USING btree (cntrb_login COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST);

-- BRIN Indexes
CREATE INDEX contributor_worker_email_finder_new ON augur_data.contributors_new USING brin (cntrb_email COLLATE "pg_catalog"."default" "pg_catalog"."text_minmax_ops");
CREATE INDEX contributor_worker_fullname_finder_new ON augur_data.contributors_new USING brin (cntrb_full_name COLLATE "pg_catalog"."default" "pg_catalog"."text_minmax_ops");

-- Step 5: Copy Data
INSERT INTO augur_data.contributors_new
SELECT * FROM augur_data.contributors;


-- Step 6: Swap Tables (if validated)
ALTER TABLE augur_data.contributors RENAME to contributors_old;
ALTER TABLE augur_data.contributors_new RENAME TO contributors;

-- Step 7: Keep an inventory of the foreign keys on the new `contributors_old` table, which is what contributors used to be prior to the hash partitioning. 

-- SHOULD STILL HAVE FOREIGN KEYS
SELECT *
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_schema = 'augur_data'
  AND ccu.table_name = 'contributors_old';

-- SHOULD NOT YET HAVE FOREIGN KEYS
SELECT *
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_schema = 'augur_data'
  AND ccu.table_name = 'contributors';

-- step 8: Rebuild and relocate foreign keys: 
-- MUST HAPPEN. Otherwise everything can be really messed up. :) 

BEGIN; 
DO $$
DECLARE
  fk RECORD;
BEGIN
  FOR fk IN
    SELECT
      tc.constraint_name,
      tc.table_schema,
      tc.table_name,
      kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu
      ON tc.constraint_name = ccu.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND ccu.table_schema = 'augur_data'
      AND ccu.table_name = 'contributors_old'
      AND ccu.column_name = 'cntrb_id'
  LOOP
    -- Log which FK is being relocated
    RAISE NOTICE 'Relocating FK % on %.% (%).', fk.constraint_name, fk.table_schema, fk.table_name, fk.column_name;

    -- Drop the old FK
    EXECUTE format(
      'ALTER TABLE %I.%I DROP CONSTRAINT %I',
      fk.table_schema, fk.table_name, fk.constraint_name
    );

    -- Recreate the FK pointing to contributors
    EXECUTE format(
      'ALTER TABLE %I.%I ADD CONSTRAINT %I FOREIGN KEY (%I) REFERENCES augur_data.contributors (cntrb_id)',
      fk.table_schema, fk.table_name, fk.constraint_name, fk.column_name
    );
  END LOOP;
END $$;

--Only run commit after checking that the old table is unchanged. Then hit commit. You just want to make 
--sure the relationships are moved correctly, and its easy to get these things wrong. 
--IF YOU DO NOT COMMIT AND CLOSE THE WINDOW, then the changes to foreign keys above will be rolled back. 


--COMMIT; 


-- STEP 9: 
-- Check that foreign keys are all removed from the old table
SELECT *
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_schema = 'augur_data'
  AND ccu.table_name = 'contributors_old';

-- Check that foreign keys now exist on the new version of contributors
SELECT *
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND ccu.table_schema = 'augur_data'
  AND ccu.table_name = 'contributors';