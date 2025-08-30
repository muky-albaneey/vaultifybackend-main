from django.db import migrations

SQL = r"""
CREATE TABLE IF NOT EXISTS api_alertattachment (
    id BIGSERIAL PRIMARY KEY,
    announcement_image varchar(100),
    alert_id bigint NOT NULL
        REFERENCES api_alert(id) ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED
);
CREATE INDEX IF NOT EXISTS api_alertattachment_alert_id_idx
    ON api_alertattachment(alert_id);
"""

class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_create_missing_provider_tables"),
    ]

    operations = [
        migrations.RunSQL(SQL, reverse_sql="""
            DROP TABLE IF EXISTS api_alertattachment CASCADE;
        """),
    ]
