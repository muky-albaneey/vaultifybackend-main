from django.db import migrations

SQL = r"""
-- Create api_provider if missing
CREATE TABLE IF NOT EXISTS api_provider (
    id BIGSERIAL PRIMARY KEY,
    first_name varchar(100) NOT NULL,
    last_name varchar(100) NOT NULL,
    phone varchar(20) NOT NULL,
    location varchar(150) NOT NULL,
    profile_picture varchar(100),
    availability varchar(100) NOT NULL DEFAULT 'offline',
    bio text NOT NULL DEFAULT '',
    skill varchar(120) NOT NULL DEFAULT '',
    service_id bigint NOT NULL
        REFERENCES api_service(id) DEFERRABLE INITIALLY DEFERRED,
    admin_id bigint NOT NULL
        REFERENCES api_admin(id) DEFERRABLE INITIALLY DEFERRED,
    created_at timestamp with time zone NOT NULL DEFAULT NOW(),
    updated_at timestamp with time zone NOT NULL DEFAULT NOW()
);

-- Create api_providerphoto if missing
CREATE TABLE IF NOT EXISTS api_providerphoto (
    id BIGSERIAL PRIMARY KEY,
    image varchar(100) NOT NULL,
    uploaded_at timestamp with time zone NOT NULL DEFAULT NOW(),
    provider_id bigint NOT NULL
        REFERENCES api_provider(id) ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED
);

-- Create api_providerreview if missing
CREATE TABLE IF NOT EXISTS api_providerreview (
    id BIGSERIAL PRIMARY KEY,
    reviewer_name varchar(120) NOT NULL,
    rating double precision NOT NULL,
    comment text NOT NULL DEFAULT '',
    created_at timestamp with time zone NOT NULL DEFAULT NOW(),
    provider_id bigint NOT NULL
        REFERENCES api_provider(id) ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED
);

-- Basic indexes (optional but nice)
CREATE INDEX IF NOT EXISTS api_provider_service_id_idx ON api_provider(service_id);
CREATE INDEX IF NOT EXISTS api_provider_admin_id_idx ON api_provider(admin_id);
CREATE INDEX IF NOT EXISTS api_providerphoto_provider_id_idx ON api_providerphoto(provider_id);
CREATE INDEX IF NOT EXISTS api_providerreview_provider_id_idx ON api_providerreview(provider_id);
"""

class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(SQL, reverse_sql="""
            DROP TABLE IF EXISTS api_providerreview CASCADE;
            DROP TABLE IF EXISTS api_providerphoto CASCADE;
            DROP TABLE IF EXISTS api_provider CASCADE;
        """),
    ]
