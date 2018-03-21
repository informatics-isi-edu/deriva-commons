-- begin transaction

BEGIN;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cv"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cv" 
	ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
	ADD COLUMN "RCB" public.ermrest_rcb,
	ADD COLUMN "RMB" public.ermrest_rmb,
	ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
	ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvterm"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvterm" 
	ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
	ADD COLUMN "RCB" public.ermrest_rcb,
	ADD COLUMN "RMB" public.ermrest_rmb,
	ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
	ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvterm_dbxref"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvterm_dbxref" 
	ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
	ADD COLUMN "RCB" public.ermrest_rcb,
	ADD COLUMN "RMB" public.ermrest_rmb,
	ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
	ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvterm_relationship"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvterm_relationship" 
	ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
	ADD COLUMN "RCB" public.ermrest_rcb,
	ADD COLUMN "RMB" public.ermrest_rmb,
	ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
	ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvtermpath"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvtermpath" 
	ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
	ADD COLUMN "RCB" public.ermrest_rcb,
	ADD COLUMN "RMB" public.ermrest_rmb,
	ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
	ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvtermprop"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvtermprop" 
	ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
	ADD COLUMN "RCB" public.ermrest_rcb,
	ADD COLUMN "RMB" public.ermrest_rmb,
	ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
	ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."cvtermsynonym"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."cvtermsynonym" 
	ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
	ADD COLUMN "RCB" public.ermrest_rcb,
	ADD COLUMN "RMB" public.ermrest_rmb,
	ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
	ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."db"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."db" 
	ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
	ADD COLUMN "RCB" public.ermrest_rcb,
	ADD COLUMN "RMB" public.ermrest_rmb,
	ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
	ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."dbxref"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."dbxref" 
	ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
	ADD COLUMN "RCB" public.ermrest_rcb,
	ADD COLUMN "RMB" public.ermrest_rmb,
	ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
	ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."domain_registry"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."domain_registry" 
	ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
	ADD COLUMN "RCB" public.ermrest_rcb,
	ADD COLUMN "RMB" public.ermrest_rmb,
	ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
	ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;

CREATE TRIGGER ermrest_syscols
BEFORE INSERT OR UPDATE ON "data_commons"."relationship_types"
FOR EACH ROW EXECUTE PROCEDURE _ermrest.maintain_row()
;

ALTER TABLE "data_commons"."relationship_types" 
	ADD COLUMN "RID" public.ermrest_rid UNIQUE DEFAULT nextval('_ermrest.rid_seq'::regclass) NOT NULL,
	ADD COLUMN "RCB" public.ermrest_rcb,
	ADD COLUMN "RMB" public.ermrest_rmb,
	ADD COLUMN "RCT" public.ermrest_rct DEFAULT now() NOT NULL,
	ADD COLUMN "RMT" public.ermrest_rmt DEFAULT now() NOT NULL
;


-- update ermrest
TRUNCATE _ermrest.data_version;
TRUNCATE _ermrest.model_version;
SELECT _ermrest.model_change_event();


COMMIT;

