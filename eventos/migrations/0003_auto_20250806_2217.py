from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0002_evento_estado_evento_fecha_finalizacion_manual'),
    ]

    operations = [
        # Agregar índices para mejorar consultas del calendario (PostgreSQL compatible)
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS eventos_evento_fecha_evento_idx ON eventos_evento (fecha_evento);",
            reverse_sql="DROP INDEX IF EXISTS eventos_evento_fecha_evento_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS eventos_evento_fecha_estado_idx ON eventos_evento (fecha_evento, estado);",
            reverse_sql="DROP INDEX IF EXISTS eventos_evento_fecha_estado_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS eventos_evento_municipio_fecha_idx ON eventos_evento (municipio_id, fecha_evento);",
            reverse_sql="DROP INDEX IF EXISTS eventos_evento_municipio_fecha_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS eventos_evento_estado_idx ON eventos_evento (estado);",
            reverse_sql="DROP INDEX IF EXISTS eventos_evento_estado_idx;"
        ),
    ]