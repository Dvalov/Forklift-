from django.db import migrations


class AddFieldIfMissing(migrations.AddField):
    """Support databases whose generated initial migration already included this column."""

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        model = to_state.apps.get_model(app_label, self.model_name)
        table = model._meta.db_table
        field = model._meta.get_field(self.name)
        with schema_editor.connection.cursor() as cursor:
            columns = schema_editor.connection.introspection.get_table_description(cursor, table)
        if any(column.name == field.column for column in columns):
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)
