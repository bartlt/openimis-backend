from django.db import migrations


class AddFieldPostgres(migrations.AddField):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if schema_editor.connection.vendor == 'postgresql':
            super().database_backwards(app_label, schema_editor, from_state, to_state)

    def describe(self):
        # This is used to describe what the operation does in console output.
        return "Wrapper for AddField that works only for postgres database engine."
